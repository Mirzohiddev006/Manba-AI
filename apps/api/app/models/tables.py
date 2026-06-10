"""DB sxemasi — TZ 7-bo'lim + 16.10 jadvallar."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class SourceTypeEnum(str, enum.Enum):
    book = "book"
    book_many = "book_many"
    journal_article = "journal_article"
    conference = "conference"
    dissertation = "dissertation"
    abstract = "abstract"
    legal = "legal"
    web = "web"
    foreign_article = "foreign_article"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    lang: Mapped[str] = mapped_column(String(8), default="uz")
    script: Mapped[str] = mapped_column(String(12), default="latin")
    tariff: Mapped[str] = mapped_column(String(16), default="free")
    tariff_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    daily_used: Mapped[int] = mapped_column(Integer, default=0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lists: Mapped[list[ReferenceList]] = relationship(back_populates="user")


class ReferenceList(Base):
    __tablename__ = "reference_lists"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="Yangi ro'yxat")
    grouping_mode: Mapped[str] = mapped_column(String(16), default="oak")  # oak | flat
    sort_mode: Mapped[str] = mapped_column(String(16), default="auto")  # auto | manual
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="lists")
    items: Mapped[list[ListItem]] = relationship(
        back_populates="ref_list", cascade="all, delete-orphan", order_by="ListItem.position"
    )


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    raw_input: Mapped[str] = mapped_column(Text)
    source_type: Mapped[SourceTypeEnum] = mapped_column(Enum(SourceTypeEnum, name="source_type"))
    fields: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    formatted_text: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    parse_method: Mapped[str] = mapped_column(String(16), default="rules")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_sources_fields", "fields", postgresql_using="gin"),)


class ListItem(Base):
    __tablename__ = "list_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("reference_lists.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    group_no: Mapped[int] = mapped_column(Integer, default=2)

    ref_list: Mapped[ReferenceList] = relationship(back_populates="items")
    source: Mapped[Source] = relationship()


class Template(Base):
    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[SourceTypeEnum] = mapped_column(Enum(SourceTypeEnum, name="source_type"))
    lang: Mapped[str] = mapped_column(String(8), default="uz")
    template_body: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"))


class DictionaryWord(Base):
    __tablename__ = "dictionary_words"
    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(128), index=True)
    script: Mapped[str] = mapped_column(String(12), default="latin")
    category: Mapped[str] = mapped_column(String(24), default="atama")  # atama | atoqli_ot
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | pending
    added_by: Mapped[int | None] = mapped_column(BigInteger)  # tg_id yoki admin id


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(32))
    amount: Mapped[int] = mapped_column(Integer)  # tiyin / stars
    provider: Mapped[str] = mapped_column(String(16))  # click | payme | stars
    status: Mapped[str] = mapped_column(String(16), default="pending")
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True)  # idempotentlik
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminUser(Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(256), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(24), default="moderator")  # superadmin|moderator|content
    totp_secret: Mapped[str] = mapped_column(String(64))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"))
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LlmUsage(Base):
    __tablename__ = "llm_usage"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Broadcast(Base):
    __tablename__ = "broadcasts"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id"))
    segment: Mapped[str] = mapped_column(String(32))  # all | premium | inactive_30
    message: Mapped[str] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="draft")


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new")  # new|in_progress|closed
    admin_reply: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PdfTask(Base):
    __tablename__ = "pdf_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    s3_key: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued|processing|done|error
    result: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# === V2 (TZ 16.10) ===

class LexDocument(Base):
    __tablename__ = "lex_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, index=True)
    doc_type: Mapped[str] = mapped_column(String(32))  # qonun|farmon|qaror
    doc_number: Mapped[str] = mapped_column(String(64))
    adopted_date: Mapped[str] = mapped_column(String(16))
    last_edition_date: Mapped[str | None] = mapped_column(String(16))
    url: Mapped[str] = mapped_column(String(512))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OakJournal(Base):
    __tablename__ = "oak_journals"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    specialty_code: Mapped[str | None] = mapped_column(String(32))
    lang: Mapped[str | None] = mapped_column(String(8))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ListShare(Base):
    __tablename__ = "list_shares"
    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("reference_lists.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    permission: Mapped[str] = mapped_column(String(8), default="view")  # view | edit
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ItemComment(Base):
    __tablename__ = "item_comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    list_item_id: Mapped[int] = mapped_column(ForeignKey("list_items.id", ondelete="CASCADE"))
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OcrTask(Base):
    __tablename__ = "ocr_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    pdf_task_id: Mapped[int] = mapped_column(ForeignKey("pdf_tasks.id", ondelete="CASCADE"))
    engine: Mapped[str] = mapped_column(String(16), default="tesseract")  # tesseract|textract
    pages: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="queued")
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
