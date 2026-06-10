"""Komandalar: /start /new /list /export /spell /settings /premium /feedback /help."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..api_client import api
from ..i18n import t
from ..keyboards.common import export_kb, lang_keyboard, main_menu, nav_kb
from ..redis_store import set_user_lang
from ..states import FeedbackFlow

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, lang: str) -> None:
    # share_{token} deep-link (TZ 16.6)
    args = (message.text or "").split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("share_"):
        await message.answer(t(lang, "lists-title"))
        return
    await message.answer(t(lang, "choose-lang"), reply_markup=lang_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(cb: CallbackQuery) -> None:
    lang = cb.data.split(":")[1]
    await set_user_lang(cb.from_user.id, lang)
    await cb.message.edit_text(t(lang, "lang-set"))
    await cb.message.answer(
        t(lang, "start-welcome", name=cb.from_user.first_name or ""),
        reply_markup=main_menu(lang),
        parse_mode="HTML",
    )
    await cb.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t(lang, "help-text"), parse_mode="HTML")


@router.message(Command("new"))
async def cmd_new(message: Message, lang: str) -> None:
    await message.answer(t(lang, "menu-new") + "\n" + t(lang, "help-text"), parse_mode="HTML")


@router.message(Command("list"))
async def cmd_list(message: Message, lang: str) -> None:
    resp = await api.call(message.from_user.id, "GET", "/api/v1/lists")
    lists = resp.json() if resp.status_code == 200 else []
    if not lists:
        await message.answer(t(lang, "lists-empty"))
        return
    lines = [t(lang, "lists-title")] + [
        f"• {lst['title']} — {lst['items_count']}" for lst in lists
    ]
    await message.answer("\n".join(lines), reply_markup=nav_kb(lang))


@router.message(Command("export"))
async def cmd_export(message: Message, lang: str) -> None:
    await message.answer(t(lang, "export-choose"), reply_markup=export_kb(lang))


@router.callback_query(F.data.startswith("export:"))
async def do_export(cb: CallbackQuery, lang: str) -> None:
    grouping = cb.data.split(":")[1]
    resp = await api.call(cb.from_user.id, "GET", "/api/v1/lists")
    lists = resp.json() if resp.status_code == 200 else []
    if not lists:
        await cb.message.answer(t(lang, "lists-empty"))
        await cb.answer()
        return
    list_id = lists[0]["id"]  # oxirgi yangilangan
    resp = await api.call(
        cb.from_user.id, "POST", f"/api/v1/lists/{list_id}/export",
        json={"fmt": "docx", "script": "latin", "font_size": 14,
              "grouping": grouping},
    )
    if resp.status_code == 200:
        from aiogram.types import BufferedInputFile

        await cb.message.answer_document(
            BufferedInputFile(resp.content, filename="adabiyotlar_royxati.docx"),
            caption=t(lang, "export-ready"),
        )
    await cb.answer()


@router.message(Command("settings"))
async def cmd_settings(message: Message, lang: str) -> None:
    await message.answer(t(lang, "settings-title"), reply_markup=lang_keyboard())


@router.message(Command("premium"))
async def cmd_premium(message: Message, lang: str) -> None:
    await message.answer(t(lang, "premium-info"), parse_mode="HTML")


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, lang: str, state: FSMContext) -> None:
    await state.set_state(FeedbackFlow.writing)
    await message.answer(t(lang, "feedback-ask"))


@router.message(FeedbackFlow.writing)
async def feedback_text(message: Message, lang: str, state: FSMContext) -> None:
    await state.clear()
    # API ga yuborish (admin panel Feedback bo'limiga tushadi)
    await api.call(
        message.from_user.id, "POST", "/api/v1/feedback",
        json={"text": message.text or ""},
    )
    await message.answer(t(lang, "feedback-thanks"))


@router.callback_query(F.data == "nav:home")
async def nav_home(cb: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    await cb.message.answer(t(lang, "main-menu"), reply_markup=main_menu(lang))
    await cb.answer()
