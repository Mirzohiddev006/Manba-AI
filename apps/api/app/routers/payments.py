"""To'lov webhook lari — imzo tekshiruvi + idempotentlik (TZ 11)."""

import hashlib
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_db
from ..models import Payment, User

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/webhook/click")
async def click_webhook(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    form = dict(await request.form())
    s = get_settings()
    sign_string = (
        f"{form.get('click_trans_id','')}{form.get('service_id','')}{s.click_secret_key}"
        f"{form.get('merchant_trans_id','')}{form.get('amount','')}{form.get('action','')}"
        f"{form.get('sign_time','')}"
    )
    if hashlib.md5(sign_string.encode()).hexdigest() != form.get("sign_string"):  # noqa: S324
        raise HTTPException(400, "Imzo noto'g'ri")
    external_id = f"click:{form.get('click_trans_id')}"
    existing = await db.execute(select(Payment).where(Payment.external_id == external_id))
    if existing.scalar_one_or_none():
        return {"error": 0, "error_note": "Allaqachon qabul qilingan"}  # idempotent
    user_id = int(str(form.get("merchant_trans_id", "0")))
    payment = Payment(
        user_id=user_id, plan="premium_month", amount=int(float(str(form.get("amount", 0))) * 100),
        provider="click", status="paid", external_id=external_id, paid_at=datetime.now(UTC),
    )
    db.add(payment)
    await _activate_premium(db, user_id)
    await db.commit()
    return {"error": 0, "error_note": "OK"}


@router.post("/webhook/payme")
async def payme_webhook(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    import base64

    auth = request.headers.get("Authorization", "")
    expected = base64.b64encode(f"Paycom:{get_settings().payme_secret_key}".encode()).decode()
    if auth != f"Basic {expected}":
        return {"error": {"code": -32504, "message": "Avtorizatsiya xato"}}
    body = await request.json()
    method = body.get("method", "")
    params = body.get("params", {})
    if method == "PerformTransaction":
        external_id = f"payme:{params.get('id')}"
        existing = await db.execute(select(Payment).where(Payment.external_id == external_id))
        if not existing.scalar_one_or_none():
            user_id = int(params.get("account", {}).get("user_id", 0))
            db.add(
                Payment(
                    user_id=user_id, plan="premium_month",
                    amount=int(params.get("amount", 0)), provider="payme",
                    status="paid", external_id=external_id, paid_at=datetime.now(UTC),
                )
            )
            await _activate_premium(db, user_id)
            await db.commit()
        return {"result": {"perform_time": int(datetime.now(UTC).timestamp() * 1000),
                           "transaction": params.get("id"), "state": 2}}
    return {"result": {"allow": True}}


@router.post("/webhook/stars")
async def stars_webhook(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    """Telegram Stars — bot successful_payment dan keyin chaqiradi (ichki)."""
    body = await request.json()
    if body.get("secret") != get_settings().webhook_secret_token:
        raise HTTPException(403, "Ruxsat yo'q")
    external_id = f"stars:{body['charge_id']}"
    existing = await db.execute(select(Payment).where(Payment.external_id == external_id))
    if existing.scalar_one_or_none():
        return {"ok": True}
    db.add(
        Payment(
            user_id=body["user_id"], plan=body.get("plan", "premium_month"),
            amount=body.get("amount", 0), provider="stars", status="paid",
            external_id=external_id, paid_at=datetime.now(UTC),
        )
    )
    await _activate_premium(db, body["user_id"])
    await db.commit()
    return {"ok": True}


async def _activate_premium(db: AsyncSession, user_id: int) -> None:
    from datetime import timedelta

    user = await db.get(User, user_id)
    if user:
        base = user.tariff_expires_at or datetime.now(UTC)
        if base < datetime.now(UTC):
            base = datetime.now(UTC)
        user.tariff = "premium"
        user.tariff_expires_at = base + timedelta(days=30)
