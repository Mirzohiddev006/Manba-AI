"""i18n — barcha matnlar locales/ dagi fluent fayllarda, kodda hardcode YO'Q."""

from __future__ import annotations

from pathlib import Path

from fluent.runtime import FluentLocalization, FluentResourceLoader

LOCALES_DIR = Path(__file__).parent / "locales"
LANGS = ("uz", "uz_cyrl", "ru")

_loader = FluentResourceLoader(str(LOCALES_DIR) + "/{locale}")
_l10n: dict[str, FluentLocalization] = {
    lang: FluentLocalization([lang, "uz"], ["messages.ftl"], _loader) for lang in LANGS
}


def t(lang: str, key: str, **kwargs) -> str:
    loc = _l10n.get(lang, _l10n["uz"])
    return loc.format_value(key, kwargs or None) or key
