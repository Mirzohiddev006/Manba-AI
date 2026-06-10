"""Gibrid quvur: preprocess → rule parser → (confidence < eshik → LLM) → validate → render.

LLM dependency-injection orqali beriladi (Protocol) — citation-core hech qanday
tarmoq kutubxonasiga bog'lanmaydi; Anthropic implementatsiyasi `llm.py` da.
"""

from __future__ import annotations

from typing import Protocol

from .models import ParsedSource, Person, SourceFields, SourceType
from .parsers.rule_parser import parse_rule_based
from .preprocess import split_sources
from .templates.engine import TemplateEngine
from .validators import validate

CONFIDENCE_THRESHOLD = 0.85


class LLMExtractor(Protocol):
    """Faqat maydon ajratadi. Formatlangan satr qaytarish IMKONSIZ (sxema cheklovi)."""

    def extract(self, raw_text: str) -> tuple[SourceType, SourceFields, dict[str, float]]: ...


class Pipeline:
    def __init__(
        self,
        engine: TemplateEngine | None = None,
        llm: LLMExtractor | None = None,
        threshold: float = CONFIDENCE_THRESHOLD,
    ) -> None:
        self.engine = engine or TemplateEngine()
        self.llm = llm
        self.threshold = threshold

    def parse_one(self, text: str) -> ParsedSource:
        src = parse_rule_based(text)
        if src.confidence < self.threshold and self.llm is not None:
            try:
                stype, fields, fconf = self.llm.extract(text)
                src = self._merge(src, stype, fields, fconf)
                src.parse_method = "rules+llm"
            except Exception as exc:  # LLM xatosi — qoidaviy natija bilan davom
                src.warnings.append(f"LLM xatosi, qoidaviy natija ishlatildi: {exc}")
        src = validate(src)
        return self.engine.render_source(src)

    def parse_many(self, text: str) -> list[ParsedSource]:
        return [self.parse_one(line) for line in split_sources(text)]

    @staticmethod
    def _merge(
        rule_src: ParsedSource,
        llm_type: SourceType,
        llm_fields: SourceFields,
        llm_conf: dict[str, float],
    ) -> ParsedSource:
        """LLM natijasini qoidaviy natija ustiga qo'yadi: qoidaviy yuqori-confidence
        maydonlar saqlanadi, bo'sh/past maydonlar LLM dan to'ldiriladi."""
        merged = rule_src.model_copy(deep=True)
        merged.source_type = llm_type
        for name in SourceFields.model_fields:
            rule_conf = rule_src.field_confidence.get(name, 0.0)
            llm_c = llm_conf.get(name, 0.75)
            llm_val = getattr(llm_fields, name)
            empty = not getattr(rule_src.fields, name) or (
                name == "year" and rule_src.fields.year is None
            )
            if (empty or rule_conf < 0.6) and llm_val:
                setattr(merged.fields, name, llm_val)
                merged.field_confidence[name] = llm_c
        vals = merged.field_confidence.values()
        merged.confidence = round(sum(vals) / max(len(list(vals)), 1), 3) if vals else 0.5
        return merged


def make_sample_fields(stype: SourceType) -> SourceFields:
    """Admin sinov maydonchasi uchun namunaviy maydonlar."""
    return SourceFields(
        authors=[Person(surname="Karimov", initials="A.A.")],
        title="Iqtisodiyot nazariyasi",
        subtitle="Darslik",
        city="Toshkent",
        publisher="Iqtisod-moliya",
        year=2020,
        pages_total=350,
        pages_range="45–52",
        journal="Iqtisodiyot va ta'lim",
        collection="«Raqamli transformatsiya» konferensiyasi materiallari",
        volume="37",
        issue="3",
        url="https://data.worldbank.org",
        accessed_date="15.05.2026",
        doc_number="O'RQ-637-son",
        doc_date="23.09.2020",
        degree="Iqtisod. fan. bo'yicha falsafa dok. (PhD)",
    )
