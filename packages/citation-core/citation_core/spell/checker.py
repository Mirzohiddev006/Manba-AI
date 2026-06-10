"""Imlo moduli: hunspell (spylls) → maxsus lug'at → LLM (ixtiyoriy, DI).

Qatlamlar:
  1. uz-hunspell lug'ati (github.com/u2b3k/uz-hunspell) — spylls orqali, sof Python;
  2. maxsus atamalar/atoqli otlar lug'ati (DB dan keladi) — xato deb belgilanmaydi;
  3. past ishonchli holatlarda LLM kontekst tekshiruvi (callback, ixtiyoriy).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from ..models import SpellIssue

_WORD = re.compile(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ'ʻ’]{2,}")

# Tez-tez uchraydigan xatolar jadvali — hunspell topa olmaydigan tipik holatlar
_COMMON_FIXES: dict[str, str] = {
    "tehnologiya": "texnologiya",
    "tahlil qilish": "tahlil qilish",
    "innovatsion": "innovatsion",
    "iqtisodiy": "iqtisodiy",
    "universitet": "universitet",
}


class SpellChecker:
    def __init__(
        self,
        dictionary_path: str | Path | None = None,
        custom_words: set[str] | None = None,
        llm_check: Callable[[str, str], list[str]] | None = None,
    ) -> None:
        """dictionary_path — uz-hunspell .dic/.aff joylashgan papka."""
        self._custom = {w.lower() for w in (custom_words or set())}
        self._llm_check = llm_check
        self._hunspell = None
        if dictionary_path:
            try:
                from spylls.hunspell import Dictionary

                self._hunspell = Dictionary.from_files(str(dictionary_path))
            except Exception:
                self._hunspell = None  # lug'at yo'q — faqat jadval+custom rejim

    def add_custom_words(self, words: set[str]) -> None:
        self._custom |= {w.lower() for w in words}

    def check(self, text: str) -> list[SpellIssue]:
        issues: list[SpellIssue] = []
        for m in _WORD.finditer(text):
            word = m.group(0)
            lw = word.lower().replace("ʻ", "'").replace("’", "'")
            if lw in self._custom:
                continue
            if word[0].isupper() and m.start() > 0:
                # Atoqli ot bo'lishi ehtimoli yuqori — faqat lug'atda aniq xato bo'lsa
                continue
            if lw in _COMMON_FIXES and _COMMON_FIXES[lw] != lw:
                issues.append(
                    SpellIssue(xato=word, taklif=[_COMMON_FIXES[lw]], pozitsiya=m.start())
                )
                continue
            if self._hunspell is not None and not self._hunspell.lookup(word):
                suggestions = list(self._hunspell.suggest(word))[:3]
                if self._llm_check is not None and not suggestions:
                    suggestions = self._llm_check(word, text)[:3]
                if suggestions:
                    issues.append(
                        SpellIssue(xato=word, taklif=suggestions, pozitsiya=m.start())
                    )
        return issues

    @staticmethod
    def apply(text: str, issues: list[SpellIssue], accepted: list[int] | None = None) -> str:
        """Qabul qilingan tuzatishlarni qo'llaydi (indekslar bo'yicha, oxiridan boshlab)."""
        chosen = issues if accepted is None else [issues[i] for i in accepted]
        for issue in sorted(chosen, key=lambda i: i.pozitsiya, reverse=True):
            if issue.taklif:
                text = (
                    text[: issue.pozitsiya]
                    + issue.taklif[0]
                    + text[issue.pozitsiya + len(issue.xato):]
                )
        return text
