"""Inline klaviaturalar — barcha matnlar i18n orqali."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from ..config import get_settings
from ..i18n import t

TYPE_EMOJI = {
    "book": "📕", "book_many": "📗", "journal_article": "📄", "conference": "📑",
    "dissertation": "🎓", "abstract": "📜", "legal": "🏛", "web": "🌐",
    "foreign_article": "🌍",
}

EDITABLE_FIELDS = [
    "title", "authors", "city", "publisher", "year", "pages_total",
    "pages_range", "journal", "collection", "issue", "volume", "url",
]


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'zbek (lotin)", callback_data="lang:uz")],
        [InlineKeyboardButton(text="Ўзбек (кирилл)", callback_data="lang:uz_cyrl")],
        [InlineKeyboardButton(text="Русский", callback_data="lang:ru")],
    ])


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    """Reply keyboard faqat bosh menyuda, ≤ 6 tugma (TZ 4.6)."""
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text=t(lang, "menu-new")), KeyboardButton(text=t(lang, "menu-lists"))],
            [KeyboardButton(text=t(lang, "menu-export")),
             KeyboardButton(text=t(lang, "menu-settings"))],
            [KeyboardButton(text=t(lang, "menu-premium")),
             KeyboardButton(
                 text=t(lang, "menu-webapp"),
                 web_app=WebAppInfo(url=get_settings().webapp_url),
             )],
        ],
    )


def source_card_kb(lang: str, source_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "btn-edit"), callback_data=f"src:edit:{source_id}"),
            InlineKeyboardButton(text=t(lang, "btn-copy"), callback_data=f"src:copy:{source_id}"),
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "btn-add-to-list"), callback_data=f"src:add:{source_id}"
            ),
            InlineKeyboardButton(
                text=t(lang, "btn-reparse"), callback_data=f"src:reparse:{source_id}"
            ),
            InlineKeyboardButton(text=t(lang, "btn-cancel"), callback_data=f"src:del:{source_id}"),
        ],
    ])


def edit_fields_kb(lang: str, source_id: int) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(EDITABLE_FIELDS), 3):
        rows.append([
            InlineKeyboardButton(text=f, callback_data=f"edit:{source_id}:{f}")
            for f in EDITABLE_FIELDS[i:i + 3]
        ])
    rows.append([
        InlineKeyboardButton(text=t(lang, "btn-back"), callback_data="nav:home"),
        InlineKeyboardButton(
            text=t(lang, "menu-webapp"),
            web_app=WebAppInfo(url=get_settings().webapp_url),
        ),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def nav_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "btn-back"), callback_data="nav:back"),
        InlineKeyboardButton(text=t(lang, "btn-home"), callback_data="nav:home"),
    ]])


def spell_kb(lang: str, issue_count: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=f"✅ {i + 1}", callback_data=f"spell:ok:{i}"),
            InlineKeyboardButton(text=f"❌ {i + 1}", callback_data=f"spell:no:{i}"),
        ]
        for i in range(min(issue_count, 8))
    ]
    rows.append([
        InlineKeyboardButton(text=t(lang, "btn-accept-all"), callback_data="spell:all")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def export_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t(lang, "export-grouping-oak"), callback_data="export:oak"
            ),
            InlineKeyboardButton(
                text=t(lang, "export-grouping-flat"), callback_data="export:flat"
            ),
        ],
        [InlineKeyboardButton(text=t(lang, "btn-home"), callback_data="nav:home")],
    ])


def settings_kb(lang: str, script: str) -> InlineKeyboardMarkup:
    script_name = t(lang, "script-latin" if script == "latin" else "script-cyr")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn-lang"), callback_data="set:lang")],
        [InlineKeyboardButton(
            text=t(lang, "btn-script", script=script_name), callback_data="set:script"
        )],
        [InlineKeyboardButton(text=t(lang, "btn-home"), callback_data="nav:home")],
    ])


def lists_kb(lang: str, lists: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"📚 {lst['title']} ({lst['items_count']})",
            callback_data=f"list:open:{lst['id']}",
        )]
        for lst in lists[:8]
    ]
    rows.append([
        InlineKeyboardButton(text=t(lang, "list-create"), callback_data="list:new"),
        InlineKeyboardButton(text=t(lang, "btn-home"), callback_data="nav:home"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def list_view_kb(lang: str, list_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t(lang, "btn-export-word"), callback_data=f"list:word:{list_id}"
            ),
            InlineKeyboardButton(
                text=t(lang, "btn-export-text"), callback_data=f"list:text:{list_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "btn-delete-list"), callback_data=f"list:del:{list_id}"
            ),
            InlineKeyboardButton(text=t(lang, "btn-back"), callback_data="list:back"),
        ],
    ])


def new_source_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn-try-sample"), callback_data="demo:parse")],
    ])
