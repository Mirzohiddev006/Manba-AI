"""Redis ulanish (limitlar, kesh). `fakeredis://` — Docker siz lokal rejim."""

from typing import Any

from .config import get_settings

_pool: Any = None


def get_redis() -> Any:
    global _pool
    if _pool is None:
        url = get_settings().redis_url
        if url.startswith("fakeredis"):
            import fakeredis.aioredis

            _pool = fakeredis.aioredis.FakeRedis(decode_responses=True)
        else:
            import redis.asyncio as aioredis

            _pool = aioredis.from_url(url, decode_responses=True)
    return _pool
