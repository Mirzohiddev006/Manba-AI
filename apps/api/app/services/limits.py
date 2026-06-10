"""Kunlik limitlar — Redis hisoblagichlar (TZ 4.6)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException

from ..config import get_settings
from ..models import User
from ..redis_client import get_redis


def _key(kind: str, tg_id: int) -> str:
    today = datetime.now(UTC).strftime("%Y%m%d")
    return f"limit:{kind}:{tg_id}:{today}"


async def check_and_increment(user: User, kind: str) -> None:
    """kind: 'source' yoki 'pdf'. Premium — cheksiz."""
    if user.tariff != "free":
        return
    s = get_settings()
    cap = s.free_daily_sources if kind == "source" else s.free_daily_pdf
    r = get_redis()
    key = _key(kind, user.tg_id)
    current = await r.incr(key)
    if current == 1:
        await r.expire(key, 90000)  # ~25 soat
    if current > cap:
        raise HTTPException(
            429,
            detail={
                "code": "limit_exceeded",
                "kind": kind,
                "cap": cap,
                "message": "Kunlik limit tugadi. Premium: /premium",
            },
        )


async def usage_today(user: User) -> dict[str, int]:
    r = get_redis()
    src = await r.get(_key("source", user.tg_id))
    pdf = await r.get(_key("pdf", user.tg_id))
    return {"sources": int(src or 0), "pdf": int(pdf or 0)}
