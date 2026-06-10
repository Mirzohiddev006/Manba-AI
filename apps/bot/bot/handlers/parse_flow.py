"""Asosiy oqim: manba kiritish → kartochka → inline amallar (TZ 4.2)."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ..api_client import api
from ..i18n import t
from ..keyboards.common import TYPE_EMOJI, source_card_kb
from ..redis_store import get_redis

router = Router()


def render_card(lang: str, src: dict) -> str:
    type_name = t(lang, f"type-{src['source_type']}")
    emoji = TYPE_EMOJI.get(src["source_type"], "📄")
    conf = int(src["confidence"] * 100)
    title = t(lang, "parse-result-title", emoji=emoji, type_name=type_name, confidence=conf)
    text = html.escape(src["formatted_text"])
    low = [k for k, v in (src.get("field_confidence") or {}).items() if v < 0.6]
    note = ("\n\n" + t(lang, "low-confidence-note") + ": " + ", ".join(f"❓{f}" for f in low)) if low else ""
    return f"{title}\n\n{text}{note}"


@router.message(F.document & F.document.mime_type == "application/pdf")
async def handle_pdf(message: Message, lang: str) -> None:
    """PDF oqimi (TZ 4.3): yuklash → SQS → push."""
    file = await message.bot.get_file(message.document.file_id)
    data = await message.bot.download_file(file.file_path)
    resp = await api.call(
        message.from_user.id, "POST", "/api/v1/pdf/upload",
        files={"file": (message.document.file_name or "doc.pdf", data.read(), "application/pdf")},
    )
    if resp.status_code == 429:
        cap = resp.json().get("detail", {}).get("cap", "")
        await message.answer(t(lang, "limit-reached", cap=cap))
        return
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    await get_redis().set(f"pdftask:{task_id}", message.chat.id, ex=7200)
    await message.answer(t(lang, "pdf-received"))


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, lang: str) -> None:
    """Matn / URL / DOI / ISBN — hammasi parse quvuriga."""
    # Menyu tugmalari — tegishli komanda to'g'ridan-to'g'ri bajariladi
    from .commands import cmd_export, cmd_list, cmd_new, cmd_premium, cmd_settings

    menu_handlers = {
        "menu-new": cmd_new,
        "menu-lists": cmd_list,
        "menu-export": cmd_export,
        "menu-settings": cmd_settings,
        "menu-premium": cmd_premium,
    }
    for key, handler in menu_handlers.items():
        if message.text == t(lang, key):
            await handler(message, lang)
            return
    if len((message.text or "").strip()) < 5:
        await message.answer(t(lang, "unknown"))
        return
    progress = await message.answer(t(lang, "analyzing"))
    try:
        resp = await api.call(
            message.from_user.id, "POST", "/api/v1/sources/parse", json={"text": message.text}
        )
        if resp.status_code == 429:
            cap = resp.json().get("detail", {}).get("cap", "")
            await progress.edit_text(t(lang, "limit-reached", cap=cap))
            return
        resp.raise_for_status()
        sources = resp.json()["sources"]
    except Exception:
        await progress.edit_text(t(lang, "parse-error"))
        return
    await progress.delete()
    for src in sources[:10]:
        await message.answer(
            render_card(lang, src),
            reply_markup=source_card_kb(lang, src["id"]),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("src:copy:"))
async def copy_source(cb: CallbackQuery, lang: str) -> None:
    """Monospace alohida xabar — bir bosishda nusxalanadi (TZ 4.2)."""
    source_id = int(cb.data.split(":")[2])
    resp = await api.call(cb.from_user.id, "GET", f"/api/v1/sources/{source_id}")
    if resp.status_code == 200:
        text = html.escape(resp.json()["formatted_text"])
        await cb.message.answer(t(lang, "copy-hint"))
        await cb.message.answer(f"<code>{text}</code>", parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data.startswith("src:add:"))
async def add_to_list(cb: CallbackQuery, lang: str) -> None:
    source_id = int(cb.data.split(":")[2])
    resp = await api.call(cb.from_user.id, "GET", "/api/v1/lists")
    lists = resp.json() if resp.status_code == 200 else []
    if not lists:
        resp = await api.call(
            cb.from_user.id, "POST", "/api/v1/lists", json={"title": "Mening ro'yxatim"}
        )
        lists = [resp.json()]
    target = lists[0]
    resp = await api.call(
        cb.from_user.id, "POST", f"/api/v1/lists/{target['id']}/items/{source_id}"
    )
    if resp.status_code == 201:
        detail = await api.call(cb.from_user.id, "GET", f"/api/v1/lists/{target['id']}")
        count = detail.json().get("items_count", "?")
        await cb.message.answer(t(lang, "added-to-list", list=target["title"], count=count))
    await cb.answer()


@router.callback_query(F.data.startswith("src:reparse:"))
async def reparse(cb: CallbackQuery, lang: str) -> None:
    source_id = int(cb.data.split(":")[2])
    resp = await api.call(cb.from_user.id, "GET", f"/api/v1/sources/{source_id}")
    if resp.status_code == 200:
        raw = resp.json()["raw_input"]
        await api.call(cb.from_user.id, "DELETE", f"/api/v1/sources/{source_id}")
        new = await api.call(cb.from_user.id, "POST", "/api/v1/sources/parse", json={"text": raw})
        src = new.json()["sources"][0]
        await cb.message.edit_text(
            render_card(lang, src),
            reply_markup=source_card_kb(lang, src["id"]),
            parse_mode="HTML",
        )
    await cb.answer()


@router.callback_query(F.data.startswith("src:del:"))
async def delete_source(cb: CallbackQuery, lang: str) -> None:
    source_id = int(cb.data.split(":")[2])
    await api.call(cb.from_user.id, "DELETE", f"/api/v1/sources/{source_id}")
    await cb.message.delete()
    await cb.answer("🗑")
