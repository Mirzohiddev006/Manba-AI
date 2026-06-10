"""Tahlil servisi: citation-core quvuri + LLM (xarajat jurnali bilan)."""

from __future__ import annotations

import time

from citation_core import ParsedSource, Pipeline, SourceFields, SourceType, TemplateEngine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import LlmUsage, Source, Template

# Narxlar taxminiy (USD / 1M token) — admin sozlamasida o'zgartiriladi
_PRICE_IN, _PRICE_OUT = 3.0, 15.0


class _LoggedLLM:
    """AnthropicExtractor o'rami — llm_usage jadvaliga yozadi."""

    def __init__(self) -> None:
        from citation_core.llm import AnthropicExtractor

        s = get_settings()
        self._inner = AnthropicExtractor(api_key=s.anthropic_api_key, model=s.llm_model)
        self.last_record: dict | None = None

    def extract(self, raw_text: str) -> tuple[SourceType, SourceFields, dict[str, float]]:
        t0 = time.monotonic()
        result = self._inner.extract(raw_text)
        usage = self._inner.last_usage
        self.last_record = {
            "model": get_settings().llm_model,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost_usd": usage.get("input_tokens", 0) / 1e6 * _PRICE_IN
            + usage.get("output_tokens", 0) / 1e6 * _PRICE_OUT,
            "latency_ms": int((time.monotonic() - t0) * 1000),
        }
        return result


async def load_template_overrides(db: AsyncSession) -> dict[SourceType, str]:
    res = await db.execute(select(Template).where(Template.is_active))
    return {SourceType(t.source_type.value): t.template_body for t in res.scalars()}


async def build_pipeline(db: AsyncSession) -> Pipeline:
    overrides = await load_template_overrides(db)
    engine = TemplateEngine(overrides=overrides or None)
    llm = None
    if get_settings().anthropic_api_key:
        llm = _LoggedLLM()
    return Pipeline(engine=engine, llm=llm)


async def parse_and_store(
    db: AsyncSession, user_id: int, text: str
) -> list[tuple[Source, ParsedSource]]:
    pipe = await build_pipeline(db)
    out: list[tuple[Source, ParsedSource]] = []
    for parsed in pipe.parse_many(text):
        row = Source(
            user_id=user_id,
            raw_input=parsed.raw_input,
            source_type=parsed.source_type.value,
            fields=parsed.fields.model_dump(),
            formatted_text=parsed.formatted_text,
            confidence=parsed.confidence,
            parse_method=parsed.parse_method,
        )
        db.add(row)
        if isinstance(pipe.llm, _LoggedLLM) and pipe.llm.last_record:
            db.add(LlmUsage(user_id=user_id, **pipe.llm.last_record))
            pipe.llm.last_record = None
        out.append((row, parsed))
    await db.commit()
    for row, _ in out:
        await db.refresh(row)
    return out


def reformat(db_source: Source, engine: TemplateEngine) -> str:
    """Maydon tahriridan keyin qayta formatlash (preview)."""
    from citation_core import Script, detect_script

    fields = SourceFields.model_validate(db_source.fields)
    script = detect_script(db_source.raw_input) if db_source.raw_input else Script.LATIN
    return engine.render(SourceType(db_source.source_type.value), fields, script)
