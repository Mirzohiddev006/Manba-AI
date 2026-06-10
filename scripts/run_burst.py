#!/usr/bin/env python3
"""Qisqa polling sessiyasi (sandbox uchun): N soniya ishlab, toza to'xtaydi."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
for p in ("apps/api", "apps/bot", "packages/citation-core"):
    sys.path.insert(0, str(ROOT / p))

DURATION = int(os.environ.get("BURST_SECONDS", "35"))


async def main() -> None:
    import uvicorn
    from aiogram import Bot, Dispatcher  # noqa: F401
    from aiogram.client.default import DefaultBotProperties

    from app.db import engine
    from app.main import app
    from app.models import Base
    from bot.config import get_settings
    from bot.main import build_dispatcher

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)

    s = get_settings()
    bot = Bot(s.bot_token, default=DefaultBotProperties(parse_mode=None))
    dp = build_dispatcher()
    await bot.delete_webhook(drop_pending_updates=False)
    print(f"⏱ {DURATION} soniyalik sessiya boshlandi…", flush=True)
    poll = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    try:
        await asyncio.wait_for(asyncio.shield(poll), timeout=DURATION)
    except TimeoutError:
        await dp.stop_polling()
        try:
            await asyncio.wait_for(poll, timeout=5)
        except (TimeoutError, asyncio.CancelledError):
            poll.cancel()
    finally:
        await bot.session.close()
        server.should_exit = True
        await api_task
    print("✅ Sessiya tugadi (xabarlar saqlandi, keyingisida davom etadi)", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
