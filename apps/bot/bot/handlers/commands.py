"""Komandalar va inline menyular — hamma amal bir bosishda ishlaydi."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from ..api_client import api
from ..i18n import t
from ..keyboards.common import (
    lang_keyboard,
    list_view_kb,
    lists_kb,
    main_menu,
    new_source_kb,
    settings_kb,
)
from ..redis_store import get_user_script, set_user_lang, set_user_script
from ..states import FeedbackFlow

router = Router()

SAMPLE_TEXT = (
    "Karimov A.A. Iqtisodiyot nazariyasi: Darslik. – Toshkent: Iqtisod-moliya, 2020. – 350 b."
)


# ============ /start va til ============

@router.message(CommandStart())
async def cmd_start(message: Message, lang: str) -> None:
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


# ============ Yangi manba ============

@router.message(Command("new"))
async def cmd_new(message: Message, lang: str) -> None:
    await message.answer(t(lang, "new-hint"), reply_markup=new_source_kb(lang))


@router.callback_query(F.data == "demo:parse")
async def demo_parse(cb: CallbackQuery, lang: str) -> None:
    """Namuna manba — bir bosishda kartochka."""
    from .parse_flow import render_card, source_card_kb

    await cb.answer("🧪")
    try:
        resp = await api.call(
            cb.from_user.id, "POST", "/api/v1/sources/parse", json={"text": SAMPLE_TEXT}
        )
        resp.raise_for_status()
        src = resp.json()["sources"][0]
    except Exception:
        await cb.message.answer(t(lang, "parse-error"))
        return
    await cb.message.answer(
        render_card(lang, src),
        reply_markup=source_card_kb(lang, src["id"]),
        parse_mode="HTML",
    )


# ============ Ro'yxatlar (hamma amal inline) ============

async def _show_lists(message: Message, lang: str, title_key: str = "lists-title") -> None:
    resp = await api.call(message.chat.id, "GET", "/api/v1/lists")
    lists = resp.json() if resp.status_code == 200 else []
    if not lists:
        resp = await api.call(
            message.chat.id, "POST", "/api/v1/lists", json={"title": "Mening ro'yxatim"}
        )
        lists = [resp.json()]
    await message.answer(t(lang, title_key), reply_markup=lists_kb(lang, lists))


@router.message(Command("list"))
async def cmd_list(message: Message, lang: str) -> None:
    await _show_lists(message, lang)


@router.message(Command("export"))
async def cmd_export(message: Message, lang: str) -> None:
    await _show_lists(message, lang, title_key="choose-list")


@router.callback_query(F.data == "list:new")
async def list_new(cb: CallbackQuery, lang: str) -> None:
    await api.call(cb.from_user.id, "POST", "/api/v1/lists", json={"title": "Yangi ro'yxat"})
    await cb.answer("➕")
    await _refresh_lists(cb, lang)


@router.callback_query(F.data == "list:back")
async def list_back(cb: CallbackQuery, lang: str) -> None:
    await cb.answer()
    await _refresh_lists(cb, lang)


async def _refresh_lists(cb: CallbackQuery, lang: str) -> None:
    resp = await api.call(cb.from_user.id, "GET", "/api/v1/lists")
    lists = resp.json() if resp.status_code == 200 else []
    try:
        await cb.message.edit_text(t(lang, "lists-title"), reply_markup=lists_kb(lang, lists))
    except Exception:
        await cb.message.answer(t(lang, "lists-title"), reply_markup=lists_kb(lang, lists))


@router.callback_query(F.data.startswith("list:open:"))
async def list_open(cb: CallbackQuery, lang: str) -> None:
    list_id = int(cb.data.split(":")[2])
    resp = await api.call(cb.from_user.id, "GET", f"/api/v1/lists/{list_id}")
    if resp.status_code != 200:
        await cb.answer("❌")
        return
    detail = resp.json()
    header = "📚 <b>" + html.escape(detail["title"]) + "</b>  •  " + str(
        detail["items_count"]
    ) + " " + t(lang, "unit-source")
    lines = [header]
    current_group = 0
    n = 0
    for item in detail["items"][:15]:
        if item["group_no"] != current_group:
            current_group = item["group_no"]
            lines.append("\n<b>" + t(lang, f"group-{current_group}") + "</b>")
        n += 1
        lines.append(f"{n}. {html.escape(item['source']['formatted_text'])}")
    if detail["items_count"] > 15:
        lines.append("…")
    if not detail["items"]:
        lines.append("\n" + t(lang, "list-empty-add"))
    text = "\n".join(lines)[:4000]
    try:
        await cb.message.edit_text(
            text, reply_markup=list_view_kb(lang, list_id), parse_mode="HTML"
        )
    except Exception:
        await cb.message.answer(
            text, reply_markup=list_view_kb(lang, list_id), parse_mode="HTML"
        )
    await cb.answer()


@router.callback_query(F.data.startswith("list:word:") | F.data.startswith("list:text:"))
async def list_export(cb: CallbackQuery, lang: str) -> None:
    _, fmt, list_id = cb.data.split(":")
    script = await get_user_script(cb.from_user.id)
    await cb.answer("⏳")
    try:
        resp = await api.call(
            cb.from_user.id, "POST", f"/api/v1/lists/{list_id}/export",
            json={"fmt": "docx" if fmt == "word" else "text",
                  "script": script, "font_size": 14},
        )
        resp.raise_for_status()
    except Exception:
        await cb.message.answer(t(lang, "parse-error"))
        return
    if fmt == "word":
        await cb.message.answer_document(
            BufferedInputFile(resp.content, filename="adabiyotlar_royxati.docx"),
            caption=t(lang, "export-ready"),
        )
    else:
        body = html.escape(resp.content.decode("utf-8", errors="replace"))[:4000]
        await cb.message.answer(f"<code>{body}</code>", parse_mode="HTML")


@router.callback_query(F.data.startswith("list:del:"))
async def list_delete(cb: CallbackQuery, lang: str) -> None:
    list_id = int(cb.data.split(":")[2])
    await api.call(cb.from_user.id, "DELETE", f"/api/v1/lists/{list_id}")
    await cb.answer(t(lang, "list-deleted"))
    await _refresh_lists(cb, lang)


# ============ Sozlamalar (inline, bir bosishda) ============

@router.message(Command("settings"))
async def cmd_settings(message: Message, lang: str) -> None:
    script = await get_user_script(message.chat.id)
    await message.answer(t(lang, "settings-menu"), reply_markup=settings_kb(lang, script))


@router.callback_query(F.data == "set:lang")
async def settings_lang(cb: CallbackQuery, lang: str) -> None:
    await cb.message.edit_text(t(lang, "choose-lang"), reply_markup=lang_keyboard())
    await cb.answer()


@router.callback_query(F.data == "set:script")
async def settings_script(cb: CallbackQuery, lang: str) -> None:
    current = await get_user_script(cb.from_user.id)
    new = "cyrillic" if current == "latin" else "latin"
    await set_user_script(cb.from_user.id, new)
    name = t(lang, "script-latin" if new == "latin" else "script-cyr")
    await cb.answer(t(lang, "script-set", script=name))
    await cb.message.edit_text(
        t(lang, "settings-menu"), reply_markup=settings_kb(lang, new)
    )


# ============ Premium / Feedback / Help / Navigatsiya ============

@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t(lang, "help-text"), parse_mode="HTML")


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
    await api.call(
        message.from_user.id, "POST", "/api/v1/feedback", json={"text": message.text or ""}
    )
    await message.answer(t(lang, "feedback-thanks"))


@router.callback_query(F.data == "nav:home")
async def nav_home(cb: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    await cb.message.answer(t(lang, "main-menu"), reply_markup=main_menu(lang))
    await cb.answer()


@router.callback_query(F.data == "nav:back")
async def nav_back(cb: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    await cb.message.answer(t(lang, "main-menu"), reply_markup=main_menu(lang))
    await cb.answer()
