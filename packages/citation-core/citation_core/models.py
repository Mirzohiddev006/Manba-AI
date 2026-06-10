"""ManbaAI yadro modellari.

Arxitektura invarianti: `formatted_text` faqat shablon motori (`engine.render`)
tomonidan yaratiladi — LLM chiqishida bunday maydon yo'q.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    """TZ 2.3-jadvalidagi 9 manba turi."""

    BOOK = "book"  # kitob/monografiya, 1–3 muallif
    BOOK_MANY = "book_many"  # kitob, 4+ muallif
    JOURNAL_ARTICLE = "journal_article"  # jurnal maqolasi
    CONFERENCE = "conference"  # to'plam/konferensiya maqolasi
    DISSERTATION = "dissertation"  # dissertatsiya
    ABSTRACT = "abstract"  # avtoreferat
    LEGAL = "legal"  # normativ-huquqiy hujjat
    WEB = "web"  # internet resurs
    FOREIGN_ARTICLE = "foreign_article"  # xorijiy maqola


class Script(StrEnum):
    LATIN = "latin"
    CYRILLIC = "cyrillic"
    MIXED = "mixed"


class Person(BaseModel):
    """Muallif: «Karimov A.A.» ko'rinishida saqlanadi."""

    surname: str
    initials: str = ""  # «A.A.»

    def display(self) -> str:
        return f"{self.surname} {self.initials}".strip()

    def display_initials_first(self) -> str:
        """4+ mualliflik shaklda: «A.A.Karimov»."""
        return f"{self.initials}{self.surname}" if self.initials else self.surname


class SourceFields(BaseModel):
    """LLM va qoidaviy parser chiqaradigan YAGONA struktura.

    Diqqat: bu modelda formatlangan satr yo'q va bo'lmaydi (ADR-002).
    """

    authors: list[Person] = Field(default_factory=list)
    title: str = ""
    subtitle: str = ""  # «: Darslik» kabi izoh
    city: str = ""
    publisher: str = ""
    year: int | None = None
    pages_total: int | None = None  # – 350 b.
    pages_range: str = ""  # – B. 45–52.
    journal: str = ""
    collection: str = ""  # to'plam/konferensiya nomi
    volume: str = ""
    issue: str = ""
    url: str = ""
    accessed_date: str = ""  # 15.05.2026
    doi: str = ""
    isbn: str = ""
    doc_number: str = ""  # O'RQ-637-son
    doc_date: str = ""  # 23.09.2020
    degree: str = ""  # «Iqtisod. fan. bo'yicha falsafa dok. (PhD)»
    language: str = ""  # uz / ru / en ...


class ParsedSource(BaseModel):
    """Quvur natijasi."""

    raw_input: str
    source_type: SourceType
    fields: SourceFields
    confidence: float = 0.0  # umumiy 0–1
    field_confidence: dict[str, float] = Field(default_factory=dict)
    parse_method: str = "rules"  # rules | llm | rules+llm
    script: Script = Script.LATIN
    formatted_text: str = ""  # faqat engine.render() to'ldiradi
    warnings: list[str] = Field(default_factory=list)

    def low_confidence_fields(self, threshold: float = 0.6) -> list[str]:
        return [k for k, v in self.field_confidence.items() if v < threshold]


class SpellIssue(BaseModel):
    xato: str
    taklif: list[str]
    pozitsiya: int  # boshlanish indeksi


LLM_EXTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "source_type": {"type": "string", "enum": [t.value for t in SourceType]},
        "fields": {
            "type": "object",
            "properties": {
                "authors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "surname": {"type": "string"},
                            "initials": {"type": "string"},
                        },
                        "required": ["surname"],
                    },
                },
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "city": {"type": "string"},
                "publisher": {"type": "string"},
                "year": {"type": "integer"},
                "pages_total": {"type": "integer"},
                "pages_range": {"type": "string"},
                "journal": {"type": "string"},
                "collection": {"type": "string"},
                "volume": {"type": "string"},
                "issue": {"type": "string"},
                "url": {"type": "string"},
                "accessed_date": {"type": "string"},
                "doi": {"type": "string"},
                "isbn": {"type": "string"},
                "doc_number": {"type": "string"},
                "doc_date": {"type": "string"},
                "degree": {"type": "string"},
            },
        },
    },
    "required": ["source_type", "fields"],
}
"""LLM structured-output sxemasi — ataylab `formatted_text` siz (ADR-002)."""
