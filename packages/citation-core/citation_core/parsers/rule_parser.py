"""Qoidaviy parser: tur aniqlash + maydon ajratish + per-field confidence."""

from __future__ import annotations

import re

from ..models import ParsedSource, Person, SourceFields, SourceType
from ..preprocess import detect_script
from . import patterns as P


def detect_type(text: str) -> tuple[SourceType, float]:
    """Manba turini evristik aniqlaydi. Qaytaradi: (tur, ishonch)."""
    if P.AVTOREF.search(text):
        return SourceType.ABSTRACT, 0.95
    if P.DISS.search(text):
        return SourceType.DISSERTATION, 0.95
    if P.LEGAL_HINT.search(text) and (P.DOC_NUMBER.search(text) or "lex.uz" in text.lower()):
        return SourceType.LEGAL, 0.92
    if P.ELEKTRON.search(text) or (
        P.URL.search(text) and not re.search(r"//\s*[A-ZА-ЯЁЎҚҒҲ«]", text)
    ):
        return SourceType.WEB, 0.85
    if P.MANY_AUTHORS.search(text):
        return SourceType.BOOK_MANY, 0.9
    if "//" in text:
        after = text.split("//", 1)[1]
        is_latin = not re.search(r"[а-яёўқғҳА-ЯЁЎҚҒҲ]", text)
        if is_latin and (P.VOLUME.search(after) or re.search(r"\bP\.\s*\d", after)):
            return SourceType.FOREIGN_ARTICLE, 0.85
        if re.search(r"konferensiya|konferentsiya|конференция|to['ʻ’]plam|тўплам|materiallari|материаллари|anjuman", after, re.IGNORECASE):
            return SourceType.CONFERENCE, 0.88
        if (m := P.PAGES_RANGE.search(after)) and not P.CITY_PUB_YEAR.search(after):
            # Sahifa yorlig'i hal qiluvchi: «P.» — xorijiy, «B./Б./С.» — mahalliy
            if m.group(1).upper() == "P" and is_latin:
                return SourceType.FOREIGN_ARTICLE, 0.85
            return SourceType.JOURNAL_ARTICLE, 0.85
        return SourceType.JOURNAL_ARTICLE, 0.7
    if P.CITY_PUB_YEAR.search(text) and P.PAGES_TOTAL.search(text):
        return SourceType.BOOK, 0.85
    if P.URL.search(text):
        return SourceType.WEB, 0.7
    return SourceType.BOOK, 0.4


def _authors_leading(text: str) -> tuple[list[Person], str, float]:
    """Matn boshidagi mualliflarni oladi; qolgan matn va ishonchni qaytaradi."""
    authors: list[Person] = []
    rest = text
    conf = 0.0
    while True:
        m = P.AUTHOR.match(rest.lstrip(", "))
        if not m:
            break
        authors.append(
            Person(surname=m.group("surname"), initials=m.group("initials").replace(" ", ""))
        )
        rest = rest.lstrip(", ")[m.end():]
        conf = 0.95
        if not rest.startswith(","):
            break
    return authors, rest.lstrip(". ").strip(), conf


def parse_rule_based(text: str) -> ParsedSource:
    from ..preprocess import clean_line

    text = clean_line(text)
    stype, type_conf = detect_type(text)
    f = SourceFields()
    fc: dict[str, float] = {}
    script = detect_script(text)
    work = text

    # --- umumiy maydonlar ---
    if m := P.URL.search(work):
        f.url = m.group(0).rstrip(".,;")
        fc["url"] = 1.0
    if m := P.DOI.search(work):
        f.doi = m.group(0).rstrip(".,;")
        fc["doi"] = 1.0
    if m := P.ACCESSED.search(work):
        f.accessed_date = m.group(1)
        fc["accessed_date"] = 1.0
    if m := P.PAGES_RANGE.search(work):
        f.pages_range = f"{m.group(2)}–{m.group(3)}"
        fc["pages_range"] = 0.95
        f.language = _lang_from_label(m.group(1))
    elif m := P.PAGES_TOTAL.search(work):
        f.pages_total = int(m.group(1))
        fc["pages_total"] = 0.95
        f.language = _lang_from_label(m.group(2))
    if m := P.VOLUME.search(work):
        f.volume = m.group(1)
        fc["volume"] = 0.9
    if m := P.ISSUE.search(work):
        f.issue = m.group(1)
        fc["issue"] = 0.9

    # --- turga xos ajratish ---
    if stype == SourceType.LEGAL:
        _extract_legal(work, f, fc)
    elif stype == SourceType.WEB:
        _extract_web(work, f, fc)
    elif stype == SourceType.BOOK_MANY:
        _extract_book_many(work, f, fc)
    elif stype in (SourceType.JOURNAL_ARTICLE, SourceType.CONFERENCE, SourceType.FOREIGN_ARTICLE):
        _extract_article(work, f, fc, stype)
    elif stype in (SourceType.DISSERTATION, SourceType.ABSTRACT):
        _extract_dissertation(work, f, fc)
    else:
        _extract_book(work, f, fc)

    if f.year is None and (m := P.YEAR.search(work)):
        f.year = int(m.group(0))
        fc.setdefault("year", 0.7)

    weights = {"title": 3.0, "authors": 2.0, "year": 1.5}
    total = sum(fc.get(k, 0.0) * weights.get(k, 1.0) for k in fc)
    denom = sum(weights.get(k, 1.0) for k in _expected_fields(stype))
    field_score = min(1.0, (total / denom) if denom else 0.0)
    # Tur ishonchi yarim vaznda: maydonlar to'liq bo'lsa, tipik manba LLM siz o'tadi
    overall = field_score * (0.5 + 0.5 * type_conf)

    return ParsedSource(
        raw_input=text,
        source_type=stype,
        fields=f,
        confidence=round(overall, 3),
        field_confidence=fc,
        parse_method="rules",
        script=script,
    )


def _lang_from_label(label: str) -> str:
    """Sahifa yorlig'idan tilni aniqlaydi: b→uz, б→uz(kirill), с→ru, p→en."""
    return {"b": "uz", "б": "uz", "с": "ru", "p": "en"}.get(label.lower(), "")


def _expected_fields(stype: SourceType) -> list[str]:
    base = {
        SourceType.BOOK: ["authors", "title", "city", "publisher", "year", "pages_total"],
        SourceType.BOOK_MANY: ["authors", "title", "city", "publisher", "year", "pages_total"],
        SourceType.JOURNAL_ARTICLE: ["authors", "title", "journal", "year", "issue", "pages_range"],
        SourceType.CONFERENCE: ["authors", "title", "collection", "city", "year", "pages_range"],
        SourceType.DISSERTATION: ["authors", "title", "degree", "city", "year", "pages_total"],
        SourceType.ABSTRACT: ["authors", "title", "degree", "city", "year", "pages_total"],
        SourceType.LEGAL: ["title", "doc_number", "doc_date"],
        SourceType.WEB: ["title", "url", "accessed_date"],
        SourceType.FOREIGN_ARTICLE: ["authors", "title", "journal", "year", "volume", "pages_range"],
    }
    return base[stype]


def _split_title(raw: str, f: SourceFields, fc: dict[str, float]) -> None:
    """«Sarlavha: Izoh» ni ajratadi."""
    raw = raw.strip(" .–-")
    if ":" in raw:
        t, sub = raw.split(":", 1)
        f.title, f.subtitle = t.strip(), sub.strip()
    else:
        f.title = raw
    fc["title"] = 0.9 if f.title else 0.0


def _extract_book(text: str, f: SourceFields, fc: dict[str, float]) -> None:
    authors, rest, aconf = _authors_leading(text)
    f.authors = authors
    fc["authors"] = aconf
    if m := P.CITY_PUB_YEAR.search(text):
        f.city, f.publisher, f.year = m.group("city"), m.group("pub").strip(), int(m.group("year"))
        fc.update(city=0.9, publisher=0.9, year=0.95)
        title_part = re.split(r"\s*[-–]\s*[A-ZА-ЯЁЎҚҒҲ][\w'ʻ’.-]*\s*:", rest, maxsplit=1)[0]
        _split_title(title_part, f, fc)
    else:
        _split_title(re.split(r"\s*[-–]\s", rest, maxsplit=1)[0], f, fc)


def _extract_book_many(text: str, f: SourceFields, fc: dict[str, float]) -> None:
    if m := P.MANY_AUTHORS.search(text):
        for am in P.AUTHOR_INV.finditer(m.group("authors")):
            f.authors.append(
                Person(surname=am.group("surname"), initials=am.group("initials").replace(" ", ""))
            )
        fc["authors"] = 0.95 if f.authors else 0.3
        _split_title(text[: m.start()], f, fc)
    if m := P.CITY_PUB_YEAR.search(text):
        f.city, f.publisher, f.year = m.group("city"), m.group("pub").strip(), int(m.group("year"))
        fc.update(city=0.9, publisher=0.9, year=0.95)


def _extract_article(
    text: str, f: SourceFields, fc: dict[str, float], stype: SourceType
) -> None:
    head, _, tail = text.partition("//")
    authors, rest, aconf = _authors_leading(head)
    f.authors = authors
    fc["authors"] = aconf
    _split_title(rest, f, fc)
    tail = tail.strip()
    # jurnal/to'plam nomi — birinchi « – » gacha
    container = re.split(r"\s*[-–]\s", tail, maxsplit=1)[0].strip(" .,")
    if stype == SourceType.CONFERENCE:
        f.collection = container
        fc["collection"] = 0.85 if container else 0.0
        if m := P.CITY_YEAR.search(tail):
            f.city, f.year = m.group("city"), int(m.group("year"))
            fc.update(city=0.85, year=0.95)
    else:
        f.journal = container
        fc["journal"] = 0.85 if container else 0.0
        if m := P.CITY_PUB_YEAR.search(tail):
            f.city, f.year = m.group("city"), int(m.group("year"))
            fc.update(city=0.85, year=0.95)
        elif m := P.CITY_YEAR.search(tail):
            f.city, f.year = m.group("city"), int(m.group("year"))
            fc.update(city=0.85, year=0.95)
        elif m := P.YEAR.search(tail):
            f.year = int(m.group(0))
            fc["year"] = 0.9


def _extract_dissertation(text: str, f: SourceFields, fc: dict[str, float]) -> None:
    authors, rest, aconf = _authors_leading(text)
    f.authors = authors
    fc["authors"] = aconf
    if dm := P.DEGREE_DISS.match(rest):
        f.title = dm.group("title").strip(" .–-")
        f.degree = dm.group("degree").strip(" .:")
        fc["title"] = 0.9 if f.title else 0.0
        fc["degree"] = 0.9
    else:
        _split_title(re.split(r"\s*[-–]\s", rest, maxsplit=1)[0], f, fc)
    if m2 := P.CITY_YEAR.search(text):
        f.city, f.year = m2.group("city"), int(m2.group("year"))
        fc.update(city=0.9, year=0.95)


def _extract_legal(text: str, f: SourceFields, fc: dict[str, float]) -> None:
    if m := P.DOC_NUMBER.search(text):
        f.doc_number = m.group(1)
        fc["doc_number"] = 0.95
    if m := P.DOC_DATE.search(text):
        f.doc_date = m.group(1)
        fc["doc_date"] = 0.95
    title = text.split("//")[0]
    if f.doc_number:
        title = title.split(f.doc_number)[0]
    f.title = title.strip(" .,–-")
    fc["title"] = 0.85 if f.title else 0.0
    if "lex.uz" in text.lower():
        f.url = "lex.uz"
        fc["url"] = 0.9


def _extract_web(text: str, f: SourceFields, fc: dict[str, float]) -> None:
    title = P.ELEKTRON.sub("", text.split("URL")[0])
    title = P.URL.sub("", title)
    f.title = title.strip(" .,\u2013-[]")
    fc["title"] = 0.9 if f.title else 0.0
