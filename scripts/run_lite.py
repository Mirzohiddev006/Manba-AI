#!/usr/bin/env python3
"""Yengil rejim: Docker SIZ — SQLite + fakeredis + bot polling.

Ishlatish: BOT_TOKEN=... python scripts/run_lite.py
API :8000 da, bot polling rejimida — bitta protsess.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "apps" / "bot"))
sys.path.insert(0, str(ROOT / "packages" / "citation-core"))

os.environ.setdefault("ENV", "lite")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{ROOT}/manba_lite.db")
os.environ.setdefault("REDIS_URL", "fakeredis://")
os.environ.setdefault("API_BASE_URL", "http://127.0.0.1:8000")
os.environ.setdefault("BOT_MODE", "polling")

if not os.environ.get("BOT_TOKEN"):
    print("❌ BOT_TOKEN berilmagan. Ishlatish: BOT_TOKEN=123:ABC python scripts/run_lite.py")
    sys.exit(1)


async def main() -> None:
    import uvicorn

    from app.db import engine
    from app.main import app
    from app.models import Base

    # Jadvallar (SQLite — alembic siz)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Baza tayyor (SQLite)")

    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.1)
    print("✅ API ishlamoqda: http://127.0.0.1:8000")

    from bot.main import run_polling

    print("✅ Bot polling rejimida ishga tushmoqda… (to'xtatish: Ctrl+C)")
    try:
        await run_polling()
    finally:
        server.should_exit = True
        await api_task


if __name__ == "__main__":
    asyncio.run(main())
