"""Maydonma-maydon tahrirlash FSM (TZ 4.2) — holatlar Redis da."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..api_client import api
from ..i18n import t
from ..keyboards.common import edit_fields_kb, source_card_kb
from ..states import EditSource

router = Router()


@router.callback_query(F.data.startswith("src:edit:"))
async def start_edit(cb: CallbackQuery, lang: str, state: FSMContext) -> None:
    source_id = int(cb.data.split(":")[2])
    await state.set_state(EditSource.choosing_field)
    await state.update_data(source_id=source_id)
    await cb.message.answer(
        t(lang, "edit-choose-field"), reply_markup=edit_fields_kb(lang, source_id)
    )
    await cb.answer()


@router.callback_query(EditSource.choosing_field, F.data.startswith("edit:"))
async def choose_field(cb: CallbackQuery, lang: str, state: FSMContext) -> None:
    _, source_id, field = cb.data.split(":")
    await state.set_state(EditSource.entering_value)
    await state.update_data(source_id=int(source_id), field=field)
    await cb.message.answer(t(lang, "edit-enter-value", field=field))
    await cb.answer()


@router.message(EditSource.entering_value, F.text)
async def enter_value(message: Message, lang: str, state: FSMContext) -> None:
    data = await state.get_data()
    source_id, field = data["source_id"], data["field"]
    value: object = message.text
    if field in ("year", "pages_total"):
        try:
            value = int(message.text)
        except ValueError:
            await message.answer(t(lang, "edit-enter-value", field=field))
            return
    if field == "authors":
        # «Karimov A.A., Saidov B.B.» ko'rinishini maydonga aylantirish
        authors = []
        for part in message.text.split(","):
            bits = part.strip().rsplit(" ", 1)
            if len(bits) == 2:
                authors.append({"surname": bits[0], "initials": bits[1]})
        value = authors
    resp = await api.call(
        message.from_user.id, "PATCH", f"/api/v1/sources/{source_id}",
        json={"fields": {field: value}},
    )
    await state.clear()
    if resp.status_code == 200:
        src = resp.json()
        await message.answer(
            t(lang, "edit-updated") + f"\n\n<code>{html.escape(src['formatted_text'])}</code>",
            reply_markup=source_card_kb(lang, source_id),
            parse_mode="HTML",
        )
