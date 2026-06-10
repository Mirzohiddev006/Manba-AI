"""API sxemalari (Pydantic v2) — OpenAPI orqali shared-types ga generatsiya qilinadi."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TelegramAuthIn(BaseModel):
    init_data: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ParseIn(BaseModel):
    text: str = Field(min_length=3, max_length=20000)


class SourceOut(BaseModel):
    id: int | None = None
    raw_input: str
    source_type: str
    fields: dict[str, Any]
    formatted_text: str
    confidence: float
    field_confidence: dict[str, float] = {}
    parse_method: str
    warnings: list[str] = []


class ParseOut(BaseModel):
    sources: list[SourceOut]


class SourcePatch(BaseModel):
    source_type: str | None = None
    fields: dict[str, Any] | None = None


class ListCreate(BaseModel):
    title: str = "Yangi ro'yxat"
    grouping_mode: str = "oak"


class ListOut(BaseModel):
    id: int
    title: str
    grouping_mode: str
    sort_mode: str
    items_count: int = 0
    updated_at: datetime | None = None


class ListItemOut(BaseModel):
    id: int
    position: int
    group_no: int
    source: SourceOut


class ListDetailOut(ListOut):
    items: list[ListItemOut] = []


class ReorderIn(BaseModel):
    item_ids: list[int]


class ExportIn(BaseModel):
    grouping: str = "oak"  # oak | flat
    font_size: int = 14
    numbering: str = "arabic"
    script: str = "latin"
    fmt: str = "docx"  # docx | text | bib | ris


class SpellIn(BaseModel):
    text: str = Field(min_length=1, max_length=50000)


class SpellIssueOut(BaseModel):
    xato: str
    taklif: list[str]
    pozitsiya: int


class AdminLoginIn(BaseModel):
    email: str
    password: str
    totp_code: str


class ShareIn(BaseModel):
    permission: str = "view"
    expires_days: int | None = 30


class CommentIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class TemplateIn(BaseModel):
    source_type: str
    lang: str = "uz"
    template_body: str


class TemplateTestIn(BaseModel):
    template_body: str
    source_type: str
