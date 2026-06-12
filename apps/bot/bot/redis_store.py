"""Bot darajasidagi Redis: til, oxirgi ro'yxat, spell sessiyalari."""

from __future__ import annotations

import json

from typing import Any

from .config import get_settings

_redis: Any = None


def get_redis() -> Any:
    global _redis
    if _redis is None:
        url = get_settings().redis_url
        if url.startswith("fakeredis"):
            import fakeredis.aioredis

            _redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        else:
            import redis.asyncio as aioredis

            _redis = aioredis.from_url(url, decode_responses=True)
    return _redis


async def get_user_lang(tg_id: int) -> str:
    return await get_redis().get(f"lang:{tg_id}") or "uz"


async def set_user_lang(tg_id: int, lang: str) -> None:
    await get_redis().set(f"lang:{tg_id}", lang)


async def set_spell_session(tg_id: int, text: str, issues: list[dict]) -> None:
    await get_redis().set(
        f"spell:{tg_id}", json.dumps({"text": text, "issues": issues}), ex=3600
    )


async def get_spell_session(tg_id: int) -> dict | None:
    raw = await get_redis().get(f"spell:{tg_id}")
    return json.loads(raw) if raw else None


async def get_user_script(tg_id: int) -> str:
    return await get_redis().get(f"script:{tg_id}") or "latin"


async def set_user_script(tg_id: int, script: str) -> None:
    await get_redis().set(f"script:{tg_id}", script)
