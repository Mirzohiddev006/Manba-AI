"""Anthropic LLM ekstraktor — structured output (tool use) bilan.

Sxema (`LLM_EXTRACT_SCHEMA`) da `formatted_text` YO'Q — LLM faqat maydon ajratadi.
"""

from __future__ import annotations

from typing import Any

from .models import LLM_EXTRACT_SCHEMA, Person, SourceFields, SourceType

_SYSTEM = """Sen bibliografik yozuvlardan maydon ajratuvchi yordamchisan.
Berilgan matndan manba turini va maydonlarni aniqla. O'zbek (lotin/kirill),
rus va ingliz tillarini qo'llab-quvvatla. Hech narsani formatlamaysan,
faqat maydonlarni ajratasan. Noma'lum maydonlarni bo'sh qoldir, taxmin qilma."""


class AnthropicExtractor:
    """`Pipeline(llm=AnthropicExtractor(...))` orqali ulanadi."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        import anthropic  # ixtiyoriy bog'liqlik

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self.last_usage: dict[str, Any] = {}

    def extract(self, raw_text: str) -> tuple[SourceType, SourceFields, dict[str, float]]:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_SYSTEM,
            messages=[{"role": "user", "content": raw_text}],
            tools=[
                {
                    "name": "submit_fields",
                    "description": "Ajratilgan bibliografik maydonlarni topshirish",
                    "input_schema": LLM_EXTRACT_SCHEMA,
                }
            ],
            tool_choice={"type": "tool", "name": "submit_fields"},
        )
        self.last_usage = {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }
        block = next(b for b in resp.content if b.type == "tool_use")
        data: dict[str, Any] = block.input  # type: ignore[assignment]
        stype = SourceType(data["source_type"])
        raw_fields = dict(data.get("fields", {}))
        raw_fields["authors"] = [
            Person(surname=a.get("surname", ""), initials=a.get("initials", ""))
            for a in raw_fields.get("authors", [])
        ]
        fields = SourceFields.model_validate(raw_fields)
        conf = {k: 0.8 for k, v in raw_fields.items() if v}
        return stype, fields, conf
