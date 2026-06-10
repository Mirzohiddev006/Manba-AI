"""Eksport: ro'yxat → DOCX/matn/BibTeX/RIS; S3 presigned URL."""

from __future__ import annotations

import uuid

import boto3
from citation_core import ParsedSource, SourceFields, SourceType
from citation_core.exporters import export_docx, export_text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import ReferenceList


def _s3():
    s = get_settings()
    return boto3.client("s3", region_name=s.aws_region, endpoint_url=s.aws_endpoint_url)


def to_parsed(items) -> list[ParsedSource]:
    out = []
    for item in items:
        src = item.source
        from citation_core import detect_script

        out.append(
            ParsedSource(
                raw_input=src.raw_input,
                source_type=SourceType(src.source_type.value),
                fields=SourceFields.model_validate(src.fields),
                formatted_text=src.formatted_text,
                script=detect_script(src.raw_input or ""),
            )
        )
    return out


async def export_list(
    db: AsyncSession, ref_list: ReferenceList, fmt: str, *, script: str, font_size: int
) -> tuple[bytes | str, str, str]:
    """Qaytaradi: (kontent, fayl nomi, content_type)."""
    sources = to_parsed(ref_list.items)
    oak = ref_list.grouping_mode == "oak"
    if fmt == "text":
        return export_text(sources, oak_groups=oak, script=script), "royxat.txt", "text/plain"
    if fmt == "bib":
        return _to_bibtex(sources), "royxat.bib", "text/plain"
    if fmt == "ris":
        return _to_ris(sources), "royxat.ris", "text/plain"
    data = export_docx(sources, oak_groups=oak, script=script, font_size=font_size)
    return data, "adabiyotlar_royxati.docx", (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


def upload_and_presign(data: bytes, filename: str, content_type: str) -> str:
    s = get_settings()
    key = f"exports/{uuid.uuid4()}/{filename}"
    _s3().put_object(Bucket=s.s3_bucket_export, Key=key, Body=data, ContentType=content_type)
    return _s3().generate_presigned_url(
        "get_object", Params={"Bucket": s.s3_bucket_export, "Key": key}, ExpiresIn=3600
    )


_BIB_TYPES = {
    "book": "book", "book_many": "book", "journal_article": "article",
    "conference": "inproceedings", "dissertation": "phdthesis", "abstract": "phdthesis",
    "legal": "misc", "web": "online", "foreign_article": "article",
}


def _to_bibtex(sources: list[ParsedSource]) -> str:
    entries = []
    for i, s in enumerate(sources, 1):
        f = s.fields
        authors = " and ".join(f"{a.surname}, {a.initials}" for a in f.authors)
        fields = {
            "author": authors, "title": f.title, "year": f.year or "",
            "publisher": f.publisher, "address": f.city, "journal": f.journal,
            "volume": f.volume, "number": f.issue, "pages": f.pages_range,
            "url": f.url, "doi": f.doi, "isbn": f.isbn,
        }
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items() if v)
        entries.append(f"@{_BIB_TYPES[s.source_type.value]}{{manba{i},\n{body}\n}}")
    return "\n\n".join(entries)


_RIS_TYPES = {
    "book": "BOOK", "book_many": "BOOK", "journal_article": "JOUR",
    "conference": "CPAPER", "dissertation": "THES", "abstract": "THES",
    "legal": "STAT", "web": "ELEC", "foreign_article": "JOUR",
}


def _to_ris(sources: list[ParsedSource]) -> str:
    out = []
    for s in sources:
        f = s.fields
        lines = [f"TY  - {_RIS_TYPES[s.source_type.value]}"]
        lines += [f"AU  - {a.surname}, {a.initials}" for a in f.authors]
        if f.title:
            lines.append(f"TI  - {f.title}")
        if f.journal:
            lines.append(f"JO  - {f.journal}")
        if f.year:
            lines.append(f"PY  - {f.year}")
        if f.city:
            lines.append(f"CY  - {f.city}")
        if f.publisher:
            lines.append(f"PB  - {f.publisher}")
        if f.url:
            lines.append(f"UR  - {f.url}")
        if f.doi:
            lines.append(f"DO  - {f.doi}")
        if f.pages_range and "–" in f.pages_range:
            a, b = f.pages_range.split("–")
            lines += [f"SP  - {a}", f"EP  - {b}"]
        lines.append("ER  - ")
        out.append("\n".join(lines))
    return "\n".join(out)
