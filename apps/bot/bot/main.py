"""Bot kirish nuqtasi: webhook (prod) yoki polling (lokal docker-compose)."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from .config import get_settings
from .handlers import commands, edit_flow, parse_flow, spell_flow
from .middlewares.user_context import UserContextMiddleware

log = logging.getLogger("bot")


def build_dispatcher() -> Dispatcher:
    s = get_settings()
    if s.redis_url.startswith("fakeredis"):
        from aiogram.fsm.storage.memory import MemoryStorage

        storage: object = MemoryStorage()  # yengil lokal rejim (Docker siz)
    else:
        storage = RedisStorage.from_url(s.redis_url)  # FSM Redis da (TZ 4.6)
    dp = Dispatcher(storage=storage)
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    # Tartib muhim: komandalar va FSM oqimlari erkin matndan oldin
    dp.include_router(commands.router)
    dp.include_router(edit_flow.router)
    dp.include_router(spell_flow.router)
    dp.include_router(parse_flow.router)
    return dp


async def run_polling() -> None:
    s = get_settings()
    bot = Bot(s.bot_token, default=DefaultBotProperties(parse_mode=None))
    dp = build_dispatcher()
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Polling rejimida ishga tushdi (lokal test)")
    await dp.start_polling(bot)


async def run_webhook() -> None:
    """Webhook: maxfiy path + X-Telegram-Bot-Api-Secret-Token (TZ 11)."""
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    s = get_settings()
    bot = Bot(s.bot_token, default=DefaultBotProperties(parse_mode=None))
    dp = build_dispatcher()
    path = f"/webhook/{s.webhook_secret_path}"
    await bot.set_webhook(
        f"{s.webhook_base}{path}",
        secret_token=s.webhook_secret_token,
        drop_pending_updates=False,
    )
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=s.webhook_secret_token).register(
        app, path=path
    )
    setup_application(app, dp, bot=bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)  # noqa: S104
    log.info("Webhook rejimida 8080 portda")
    await site.start()
    await asyncio.Event().wait()


def main() -> None:
    logging.basicConfig(level="INFO")
    s = get_settings()
    asyncio.run(run_polling() if s.bot_mode == "polling" else run_webhook())


if __name__ == "__main__":
    main()
