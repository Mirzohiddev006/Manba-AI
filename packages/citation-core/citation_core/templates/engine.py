"""Jinja2 shablon motori — yakuniy bibliografik satrning YAGONA manbasi.

ADR-002 invarianti: bu modul chetlab o'tilmaydi. LLM hech qachon satr yozmaydi.
Shablonlar DB da (templates jadvali) versiyalanadi; bu yerda standart
(default) to'plam saqlanadi — DB bo'sh bo'lsa yoki testlarda ishlatiladi.
"""

from __future__ import annotations

from jinja2 import BaseLoader, Environment, StrictUndefined

from ..models import ParsedSource, Script, SourceFields, SourceType

# Etalon: TZ 2.3-jadval. Tinish belgilariga tegmang — ular standartning o'zi.
DEFAULT_TEMPLATES: dict[SourceType, str] = {
    SourceType.BOOK: (
        "{{ authors|authors_sn }} {{ title }}{% if subtitle %}: {{ subtitle }}{% endif %}."
        " – {{ city }}: {{ publisher }}, {{ year }}."
        "{% if pages_total %} – {{ pages_total }} {{ p_label }}.{% endif %}"
    ),
    SourceType.BOOK_MANY: (
        "{{ title }}{% if subtitle %}: {{ subtitle }}{% endif %}"
        " / {{ authors|authors_inv }} [{{ etal_label }}.]."
        " – {{ city }}: {{ publisher }}, {{ year }}."
        "{% if pages_total %} – {{ pages_total }} {{ p_label }}.{% endif %}"
    ),
    SourceType.JOURNAL_ARTICLE: (
        "{{ authors|authors_sn }} {{ title }} // {{ journal }}."
        "{% if city %} – {{ city }}, {{ year }}.{% else %} – {{ year }}.{% endif %}"
        "{% if issue %} – №{{ issue }}.{% endif %}"
        "{% if pages_range %} – {{ pr_label }}. {{ pages_range }}.{% endif %}"
    ),
    SourceType.CONFERENCE: (
        "{{ authors|authors_sn }} {{ title }} // {{ collection }}."
        " – {{ city }}, {{ year }}."
        "{% if pages_range %} – {{ pr_label }}. {{ pages_range }}.{% endif %}"
    ),
    SourceType.DISSERTATION: (
        "{{ authors|authors_sn }} {{ title }}: {{ degree }} ... {{ diss_label }}."
        " – {{ city }}, {{ year }}."
        "{% if pages_total %} – {{ pages_total }} {{ p_label }}.{% endif %}"
    ),
    SourceType.ABSTRACT: (
        "{{ authors|authors_sn }} {{ title }}: {{ degree }} ... {{ diss_label }}. {{ avtoref_label }}."
        " – {{ city }}, {{ year }}."
        "{% if pages_total %} – {{ pages_total }} {{ p_label }}.{% endif %}"
    ),
    SourceType.LEGAL: (
        "{{ title }}. {{ doc_number }}, {{ doc_date }} // {{ legal_base_label }}"
    ),
    SourceType.WEB: (
        "{{ title }} [{{ elektron_label }}]. – URL: {{ url }}"
        "{% if accessed_date %} ({{ accessed_label }}: {{ accessed_date }}){% endif %}."
    ),
    SourceType.FOREIGN_ARTICLE: (
        "{{ authors|authors_sn }} {{ title }} // {{ journal }}. – {{ year }}."
        "{% if volume %} – Vol. {{ volume }}{% if issue %}, №{{ issue }}{% endif %}.{% endif %}"
        "{% if pages_range %} – P. {{ pages_range }}.{% endif %}"
    ),
}


def _authors_sn(authors: list) -> str:
    """«Karimov A.A., Saidov B.B.» — familiya oldin."""
    return ", ".join(a.display() for a in authors)


def _authors_inv(authors: list) -> str:
    """«A.A.Karimov, B.B.Saidov» — initsiallar oldin (4+ shakl)."""
    return ", ".join(a.display_initials_first() for a in authors)


_LABELS = {
    "uz_latin": {
        "p_label": "b", "pr_label": "B", "etal_label": "va boshq",
        "elektron_label": "Elektron resurs", "accessed_label": "murojaat sanasi",
        "diss_label": "diss", "avtoref_label": "avtoref",
        "legal_base_label": "Qonunchilik ma'lumotlari milliy bazasi, lex.uz",
    },
    "uz_cyrillic": {
        "p_label": "б", "pr_label": "Б", "etal_label": "ва бошқ",
        "elektron_label": "Электрон ресурс", "accessed_label": "мурожаат санаси",
        "diss_label": "дисс", "avtoref_label": "автореф",
        "legal_base_label": "Қонунчилик маълумотлари миллий базаси, lex.uz",
    },
    "ru": {
        "p_label": "с", "pr_label": "С", "etal_label": "и др",
        "elektron_label": "Электронный ресурс", "accessed_label": "дата обращения",
        "diss_label": "дисс", "avtoref_label": "автореф",
        "legal_base_label": "Национальная база данных законодательства, lex.uz",
    },
    "en": {
        "p_label": "p", "pr_label": "P", "etal_label": "et al",
        "elektron_label": "Electronic resource", "accessed_label": "accessed",
        "diss_label": "diss", "avtoref_label": "avtoref",
        "legal_base_label": "Qonunchilik ma'lumotlari milliy bazasi, lex.uz",
    },
}


def _labels(script: Script, stype: SourceType, language: str = "") -> dict[str, str]:
    if stype == SourceType.FOREIGN_ARTICLE or language == "en":
        return _LABELS["en"]
    if language == "ru":
        return _LABELS["ru"]
    if script == Script.CYRILLIC:
        return _LABELS["uz_cyrillic"]
    return _LABELS["uz_latin"]


class TemplateEngine:
    def __init__(self, overrides: dict[SourceType, str] | None = None) -> None:
        self._env = Environment(
            loader=BaseLoader(), undefined=StrictUndefined, autoescape=False
        )
        self._env.filters["authors_sn"] = _authors_sn
        self._env.filters["authors_inv"] = _authors_inv
        self._templates = {**DEFAULT_TEMPLATES, **(overrides or {})}

    def render(self, stype: SourceType, fields: SourceFields, script: Script = Script.LATIN) -> str:
        tpl = self._env.from_string(self._templates[stype])
        ctx = fields.model_dump()
        ctx["authors"] = fields.authors
        ctx.update(_labels(script, stype, fields.language))
        out = tpl.render(**ctx)
        return " ".join(out.split())  # qo'sh bo'shliqlarni yig'ish

    def render_source(self, src: ParsedSource) -> ParsedSource:
        src.formatted_text = self.render(src.source_type, src.fields, src.script)
        return src

    def validate_template(self, body: str, sample: SourceFields, stype: SourceType) -> str:
        """Admin paneldagi sinov maydonchasi uchun: shablonni sinab ko'rish."""
        tpl = self._env.from_string(body)
        ctx = sample.model_dump()
        ctx["authors"] = sample.authors
        ctx.update(_labels(Script.LATIN, stype))
        return tpl.render(**ctx)
