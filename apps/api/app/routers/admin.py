"""/api/v1/admin/* — RBAC bilan boshqaruv (TZ 6.1)."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin, make_admin_jwt, pwd_context, require_role
from ..db import get_db
from ..models import (
    AdminUser, AuditLog, Broadcast, DictionaryWord, Feedback,
    LlmUsage, Payment, Source, Template, User,
)
from ..schemas.api import AdminLoginIn, TemplateIn, TemplateTestIn, TokenOut

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def _audit(db: AsyncSession, admin: AdminUser, action: str, entity: str,
                 payload: dict | None = None, ip: str | None = None) -> None:
    db.add(AuditLog(admin_id=admin.id, action=action, entity=entity,
                    payload=payload or {}, ip=ip))


async def _login_rate_limit(request: Request) -> None:
    """IP bo'yicha: 10 urinish / 15 daqiqa (TZ 11)."""
    from ..redis_client import get_redis

    ip = request.client.host if request.client else "unknown"
    key = f"admin_login:{ip}"
    r = get_redis()
    try:
        n = await r.incr(key)
        if n == 1:
            await r.expire(key, 900)
        if n > 10:
            raise HTTPException(429, "Juda ko'p urinish. 15 daqiqadan keyin qayta urinib ko'ring.")
    except HTTPException:
        raise
    except Exception:  # Redis yo'q (test) — o'tkazib yuboriladi
        return


@router.post("/login", response_model=TokenOut)
async def login(
    body: AdminLoginIn, request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenOut:
    await _login_rate_limit(request)
    res = await db.execute(select(AdminUser).where(AdminUser.email == body.email))
    admin = res.scalar_one_or_none()
    if admin is None or not pwd_context.verify(body.password, admin.password_hash):
        raise HTTPException(401, "Email yoki parol noto'g'ri")
    if not pyotp.TOTP(admin.totp_secret).verify(body.totp_code, valid_window=1):
        raise HTTPException(401, "TOTP kod noto'g'ri")
    admin.last_login = datetime.now(UTC)
    await _audit(db, admin, "login", "admin", ip=request.client.host if request.client else None)
    await db.commit()
    return TokenOut(access_token=make_admin_jwt(admin.id, admin.role))


@router.get("/dashboard")
async def dashboard(
    admin: Annotated[AdminUser, Depends(current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    now = datetime.now(UTC)
    day, week, month = now - timedelta(days=1), now - timedelta(days=7), now - timedelta(days=30)

    async def count(q):  # noqa: ANN001
        return (await db.execute(q)).scalar() or 0

    by_type = await db.execute(
        select(Source.source_type, func.count()).group_by(Source.source_type)
    )
    llm_today = await db.execute(
        select(func.coalesce(func.sum(LlmUsage.cost_usd), 0.0)).where(LlmUsage.created_at >= day)
    )
    revenue = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "paid", Payment.paid_at >= month
        )
    )
    parse_methods = await db.execute(
        select(Source.parse_method, func.count()).group_by(Source.parse_method)
    )
    return {
        "dau": await count(select(func.count()).select_from(User).where(User.created_at >= day)),
        "wau": await count(select(func.count()).select_from(User).where(User.created_at >= week)),
        "mau": await count(select(func.count()).select_from(User).where(User.created_at >= month)),
        "total_users": await count(select(func.count()).select_from(User)),
        "sources_by_type": {str(k.value): v for k, v in by_type.all()},
        "parse_methods": {str(k): v for k, v in parse_methods.all()},
        "llm_cost_today_usd": float(llm_today.scalar() or 0),
        "revenue_month": int(revenue.scalar() or 0),
    }


@router.get("/users")
async def users_list(
    admin: Annotated[AdminUser, Depends(require_role("moderator"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = "", tariff: str = "", page: int = 1,
) -> dict:
    query = select(User)
    if q:
        query = query.where(User.username.ilike(f"%{q}%") | User.first_name.ilike(f"%{q}%"))
    if tariff:
        query = query.where(User.tariff == tariff)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    res = await db.execute(query.order_by(User.created_at.desc()).offset((page - 1) * 50).limit(50))
    return {
        "total": total,
        "items": [
            {
                "id": u.id, "tg_id": u.tg_id, "username": u.username,
                "first_name": u.first_name, "lang": u.lang, "tariff": u.tariff,
                "is_blocked": u.is_blocked, "created_at": u.created_at,
            }
            for u in res.scalars()
        ],
    }


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    blocked: bool,
    admin: Annotated[AdminUser, Depends(require_role("moderator"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Topilmadi")
    user.is_blocked = blocked
    await _audit(db, admin, "block" if blocked else "unblock", "user", {"user_id": user_id})
    await db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/grant-premium")
async def grant_premium(
    user_id: int,
    days: int,
    admin: Annotated[AdminUser, Depends(require_role("moderator"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Topilmadi")
    base = max(user.tariff_expires_at or datetime.now(UTC), datetime.now(UTC))
    user.tariff = "premium"
    user.tariff_expires_at = base + timedelta(days=days)
    await _audit(db, admin, "grant_premium", "user", {"user_id": user_id, "days": days})
    await db.commit()
    return {"ok": True, "expires_at": str(user.tariff_expires_at)}


# --- Format shablonlari (Jinja2 tahrirlovchi + sinov maydonchasi) ---

@router.get("/templates")
async def templates_list(
    admin: Annotated[AdminUser, Depends(require_role("content"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    res = await db.execute(select(Template).order_by(Template.source_type, Template.version.desc()))
    return [
        {
            "id": t.id, "source_type": t.source_type.value, "lang": t.lang,
            "template_body": t.template_body, "version": t.version, "is_active": t.is_active,
        }
        for t in res.scalars()
    ]


@router.post("/templates", status_code=201)
async def template_create(
    body: TemplateIn,
    admin: Annotated[AdminUser, Depends(require_role("content"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    last = await db.execute(
        select(func.max(Template.version)).where(Template.source_type == body.source_type)
    )
    version = (last.scalar() or 0) + 1
    tpl = Template(
        source_type=body.source_type, lang=body.lang,
        template_body=body.template_body, version=version, updated_by=admin.id,
    )
    db.add(tpl)
    await _audit(db, admin, "create", "template", {"source_type": body.source_type, "v": version})
    await db.commit()
    return {"id": tpl.id, "version": version}


@router.post("/templates/test")
async def template_test(
    body: TemplateTestIn,
    admin: Annotated[AdminUser, Depends(require_role("content"))],
) -> dict:
    """Sinov maydonchasi: shablonni namunaviy maydonlarda sinash."""
    from citation_core import SourceType, TemplateEngine
    from citation_core.pipeline import make_sample_fields

    try:
        stype = SourceType(body.source_type)
        result = TemplateEngine().validate_template(
            body.template_body, make_sample_fields(stype), stype
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "preview": result}


# --- Lug'at ---

@router.get("/dictionary")
async def dictionary_list(
    admin: Annotated[AdminUser, Depends(require_role("content"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str = "",
) -> list[dict]:
    q = select(DictionaryWord)
    if status:
        q = q.where(DictionaryWord.status == status)
    res = await db.execute(q.limit(500))
    return [
        {"id": w.id, "word": w.word, "script": w.script, "category": w.category,
         "status": w.status}
        for w in res.scalars()
    ]


@router.post("/dictionary", status_code=201)
async def dictionary_add(
    word: str, category: str,
    admin: Annotated[AdminUser, Depends(require_role("content"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    w = DictionaryWord(word=word, category=category, status="active", added_by=admin.id)
    db.add(w)
    await _audit(db, admin, "create", "dictionary", {"word": word})
    await db.commit()
    return {"id": w.id}


@router.post("/dictionary/{word_id}/moderate")
async def dictionary_moderate(
    word_id: int, approve: bool,
    admin: Annotated[AdminUser, Depends(require_role("content"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    w = await db.get(DictionaryWord, word_id)
    if w is None:
        raise HTTPException(404, "Topilmadi")
    if approve:
        w.status = "active"
    else:
        await db.delete(w)
    await db.commit()
    return {"ok": True}


# --- AI monitoring ---

@router.get("/ai-monitoring")
async def ai_monitoring(
    admin: Annotated[AdminUser, Depends(current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    recent = await db.execute(
        select(LlmUsage).order_by(LlmUsage.created_at.desc()).limit(100)
    )
    low_conf = await db.execute(
        select(Source).where(Source.confidence < 0.6).order_by(Source.created_at.desc()).limit(50)
    )
    return {
        "recent_calls": [
            {"model": u.model, "in": u.input_tokens, "out": u.output_tokens,
             "cost_usd": u.cost_usd, "latency_ms": u.latency_ms, "at": str(u.created_at)}
            for u in recent.scalars()
        ],
        "low_confidence": [
            {"id": s.id, "raw": s.raw_input[:120], "confidence": s.confidence,
             "type": s.source_type.value}
            for s in low_conf.scalars()
        ],
    }


# --- Broadcast / Feedback / Audit ---

@router.post("/broadcasts", status_code=201)
async def broadcast_create(
    segment: str, message: str,
    admin: Annotated[AdminUser, Depends(require_role("moderator"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    b = Broadcast(admin_id=admin.id, segment=segment, message=message, status="queued")
    db.add(b)
    await _audit(db, admin, "create", "broadcast", {"segment": segment})
    await db.commit()
    return {"id": b.id}


@router.get("/feedback")
async def feedback_list(
    admin: Annotated[AdminUser, Depends(require_role("moderator"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str = "",
) -> list[dict]:
    q = select(Feedback).order_by(Feedback.created_at.desc())
    if status:
        q = q.where(Feedback.status == status)
    res = await db.execute(q.limit(200))
    return [
        {"id": f.id, "user_id": f.user_id, "text": f.text, "status": f.status,
         "admin_reply": f.admin_reply, "created_at": str(f.created_at)}
        for f in res.scalars()
    ]


@router.post("/feedback/{fb_id}/reply")
async def feedback_reply(
    fb_id: int, reply: str,
    admin: Annotated[AdminUser, Depends(require_role("moderator"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    fb = await db.get(Feedback, fb_id)
    if fb is None:
        raise HTTPException(404, "Topilmadi")
    fb.admin_reply = reply
    fb.status = "closed"
    await _audit(db, admin, "reply", "feedback", {"id": fb_id})
    await db.commit()
    return {"ok": True}


@router.get("/audit")
async def audit_list(
    admin: Annotated[AdminUser, Depends(require_role("superadmin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    res = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500))
    return [
        {"id": a.id, "admin_id": a.admin_id, "action": a.action, "entity": a.entity,
         "payload": a.payload, "ip": a.ip, "at": str(a.created_at)}
        for a in res.scalars()
    ]
