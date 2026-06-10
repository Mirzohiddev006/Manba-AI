"""Imlo oqimi (TZ 4.4): diff ko'rinish, ✅/❌ har xato, «hammasini qabul»."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..api_client import api
from ..i18n import t
from ..keyboards.common import spell_kb
from ..redis_store import get_spell_session, set_spell_session
from ..states import SpellFlow

router = Router()


async def _do_spell(message: Message, lang: str, text: str) -> None:
    try:
        resp = await api.call(
            message.from_user.id, "POST", "/api/v1/spell/check", json={"text": text}
        )
        issues = resp.json() if resp.status_code == 200 else []
    except Exception:
        await message.answer(t(lang, "parse-error"))
        return
    if not issues:
        await message.answer(t(lang, "spell-none"))
        return
    await set_spell_session(message.from_user.id, text, issues)
    lines = [t(lang, "spell-found")] + [
        f"{i + 1}. " + t(lang, "spell-diff", wrong=iss["xato"], correct=iss["taklif"][0])
        for i, iss in enumerate(issues[:8])
    ]
    await message.answer("\n".join(lines), reply_markup=spell_kb(lang, len(issues)))


@router.message(Command("spell"))
async def cmd_spell(message: Message, lang: str, state: FSMContext) -> None:
    text = (message.text or "").removeprefix("/spell").strip()
    if not text:
        await state.set_state(SpellFlow.reviewing)
        await message.answer(t(lang, "spell-ask"))
        return
    await _do_spell(message, lang, text)


@router.message(SpellFlow.reviewing, F.text)
async def spell_awaited_text(message: Message, lang: str, state: FSMContext) -> None:
    await state.clear()
    await _do_spell(message, lang, message.text or "")


@router.callback_query(F.data == "spell:all")
async def accept_all(cb: CallbackQuery, lang: str) -> None:
    session = await get_spell_session(cb.from_user.id)
    if session:
        text = session["text"]
        for iss in sorted(session["issues"], key=lambda i: i["pozitsiya"], reverse=True):
            if iss["taklif"]:
                text = (
                    text[: iss["pozitsiya"]]
                    + iss["taklif"][0]
                    + text[iss["pozitsiya"] + len(iss["xato"]):]
                )
        await cb.message.answer(f"<code>{html.escape(text)}</code>", parse_mode="HTML")
    await cb.answer("✅")


@router.callback_query(F.data.startswith("spell:ok:") | F.data.startswith("spell:no:"))
async def toggle_issue(cb: CallbackQuery, lang: str) -> None:
    await cb.answer("✅" if ":ok:" in cb.data else "❌")
