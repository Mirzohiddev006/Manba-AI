"""POST /api/v1/auth/telegram — initData → JWT."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_or_create_user, make_user_jwt, verify_init_data
from ..config import get_settings
from ..db import get_db
from ..schemas.api import TelegramAuthIn, TokenOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/telegram", response_model=TokenOut)
async def telegram_auth(
    body: TelegramAuthIn, db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenOut:
    try:
        parsed = verify_init_data(body.init_data, get_settings().bot_token)
    except ValueError as e:
        raise HTTPException(401, f"initData yaroqsiz: {e}") from e
    tg_user = json.loads(parsed.get("user", "{}"))
    if not tg_user.get("id"):
        raise HTTPException(401, "user maydoni yo'q")
    user = await get_or_create_user(db, tg_user)
    return TokenOut(access_token=make_user_jwt(user.id, user.tg_id))
