"""Bot birlik testlari: i18n to'liqligi, kartochka render, klaviaturalar."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from bot.i18n import LANGS, t  # noqa: E402


def test_i18n_all_langs_have_keys():
    keys = ["start-welcome", "analyzing", "btn-edit", "btn-copy", "btn-add-to-list",
            "limit-reached", "type-book", "type-legal", "export-ready", "help-text"]
    for lang in LANGS:
        for key in keys:
            val = t(lang, key, name="X", cap=10, count=1, list="L",
                    emoji="📕", type_name="K", confidence=90, wrong="a", correct="b",
                    field="f")
            assert val and val != key, f"{lang}:{key} tarjima yo'q"


def test_i18n_langs_differ():
    assert t("uz", "btn-edit") != t("ru", "btn-edit")
    assert t("uz", "type-book") != t("uz_cyrl", "type-book")


def test_render_card_marks_low_confidence():
    from bot.handlers.parse_flow import render_card

    src = {
        "source_type": "book", "confidence": 0.62,
        "formatted_text": "Karimov A.A. Kitob. – Toshkent: Fan, 2020. – 100 b.",
        "field_confidence": {"title": 0.9, "publisher": 0.3},
    }
    card = render_card("uz", src)
    assert "publisher" in card and "62%" in card
    assert "▰" in card and "<blockquote>" in card  # vizual shkala + premium kartochka


def test_main_menu_max_six_buttons():
    from bot.keyboards.common import main_menu

    kb = main_menu("uz")
    total = sum(len(row) for row in kb.keyboard)
    assert total <= 6  # TZ 4.6
