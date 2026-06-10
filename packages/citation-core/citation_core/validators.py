"""Post-validatsiya: maydon qiymatlarini tekshiradi, ogohlantirishlar qo'shadi."""

from __future__ import annotations

import re

from .models import ParsedSource

_URL_RE = re.compile(r"^(https?://)?[\w.-]+\.[a-z]{2,}(/.*)?$", re.IGNORECASE)
_PAGES_RANGE_RE = re.compile(r"^\d{1,4}–\d{1,4}$")
_DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")


def validate(src: ParsedSource) -> ParsedSource:
    f = src.fields
    if f.year is not None and not (1400 <= f.year <= 2100):
        src.warnings.append(f"Yil shubhali: {f.year}")
        src.field_confidence["year"] = 0.2
    if f.pages_range and not _PAGES_RANGE_RE.match(f.pages_range):
        src.warnings.append(f"Sahifa oralig'i formati noto'g'ri: {f.pages_range}")
        src.field_confidence["pages_range"] = 0.3
    if f.pages_range:
        a, b = (int(x) for x in f.pages_range.split("–"))
        if a >= b:
            src.warnings.append("Sahifa oralig'i teskari")
            src.field_confidence["pages_range"] = 0.3
    if f.url and f.url != "lex.uz" and not _URL_RE.match(f.url):
        src.warnings.append(f"URL shubhali: {f.url}")
        src.field_confidence["url"] = 0.3
    if f.accessed_date and not _DATE_RE.match(f.accessed_date):
        src.warnings.append("Murojaat sanasi formati: DD.MM.YYYY bo'lishi kerak")
    if f.doc_date and not _DATE_RE.match(f.doc_date):
        src.warnings.append("Hujjat sanasi formati: DD.MM.YYYY bo'lishi kerak")
    for a in f.authors:
        if a.initials and not re.match(r"^(?:[A-ZА-ЯЁЎҚҒҲ]\.){1,3}$", a.initials):
            src.warnings.append(f"Initsiallar shakli: {a.initials}")
    return src
