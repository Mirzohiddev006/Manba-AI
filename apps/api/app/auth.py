"""Auth: Telegram initData HMAC-SHA256 → JWT; admin email+parol+TOTP → JWT; RBAC."""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_db
from .models import AdminUser, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

INITDATA_MAX_AGE = 3600  # TZ 11: auth_date ≤ 1 soat


def verify_init_data(init_data: str, bot_token: str) -> dict[str, Any]:
    """Telegram Web App initData ni HMAC-SHA256 bilan tekshiradi."""
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", "")
    if not received_hash:
        raise ValueError("hash yo'q")
    auth_date = int(parsed.get("auth_date", "0"))
    if time.time() - auth_date > INITDATA_MAX_AGE:
        raise ValueError("initData eskirgan (auth_date > 1 soat)")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise ValueError("HMAC mos emas")
    return parsed


def make_user_jwt(user_id: int, tg_id: int) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "tg_id": tg_id,
        "kind": "user",
        "exp": datetime.now(UTC) + timedelta(minutes=s.jwt_ttl_minutes),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def make_admin_jwt(admin_id: int, role: str, refresh: bool = False) -> str:
    s = get_settings()
    ttl = (
        timedelta(days=s.admin_refresh_ttl_days)
        if refresh
        else timedelta(minutes=s.admin_access_ttl_minutes)
    )
    payload = {
        "sub": str(admin_id),
        "role": role,
        "kind": "admin_refresh" if refresh else "admin",
        "exp": datetime.now(UTC) + ttl,
    }
    return jwt.encode(payload, s.admin_jwt_secret, algorithm="HS256")


async def current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token yo'q")
    try:
        payload = jwt.decode(creds.credentials, get_settings().jwt_secret, algorithms=["HS256"])
        if payload.get("kind") != "user":
            raise JWTError("kind")
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token yaroqsiz") from e
    user = await db.get(User, int(payload["sub"]))
    if user is None or user.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Foydalanuvchi bloklangan yoki topilmadi")
    return user


async def current_admin(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUser:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token yo'q")
    try:
        payload = jwt.decode(
            creds.credentials, get_settings().admin_jwt_secret, algorithms=["HS256"]
        )
        if payload.get("kind") != "admin":
            raise JWTError("kind")
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin token yaroqsiz") from e
    admin = await db.get(AdminUser, int(payload["sub"]))
    if admin is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin topilmadi")
    return admin


ROLE_LEVELS = {"superadmin": 3, "moderator": 2, "content": 1}


def require_role(min_role: str):
    """RBAC depends: superadmin > moderator > content."""

    async def checker(admin: Annotated[AdminUser, Depends(current_admin)]) -> AdminUser:
        if ROLE_LEVELS.get(admin.role, 0) < ROLE_LEVELS[min_role]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yetarli emas")
        return admin

    return checker


async def get_or_create_user(db: AsyncSession, tg: dict[str, Any]) -> User:
    res = await db.execute(select(User).where(User.tg_id == int(tg["id"])))
    user = res.scalar_one_or_none()
    if user is None:
        user = User(
            tg_id=int(tg["id"]),
            username=tg.get("username"),
            first_name=tg.get("first_name"),
            lang=tg.get("language_code", "uz")[:8],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
