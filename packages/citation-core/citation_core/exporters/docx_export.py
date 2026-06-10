"""DOCX eksport — OAK 3-ilova ko'rinishi.

Times New Roman 14pt, 1.5 interval, osma xat (hanging indent 0.5"),
avtomatik raqamlash (butun ro'yxat bo'ylab uzluksiz), guruh sarlavhalari.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Inches, Pt

from ..models import ParsedSource
from ..sorting import GROUP_TITLES, group_of, sort_sources

FONT = "Times New Roman"


def _style_paragraph(p, hanging: bool = True) -> None:  # type: ignore[no-untyped-def]
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(0)
    if hanging:
        pf.left_indent = Inches(0.5)
        pf.first_line_indent = Inches(-0.5)


def _run(p, text: str, bold: bool = False, size: int = 14):  # type: ignore[no-untyped-def]
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.bold = bold
    return r


def export_docx(
    sources: list[ParsedSource],
    *,
    title: str = "FOYDALANILGAN ADABIYOTLAR RO'YXATI",
    oak_groups: bool = True,
    script: str = "latin",
    font_size: int = 14,
) -> bytes:
    doc = Document()
    # Sahifa: standart A4, normal field python-docx default ga yaqin
    h = doc.add_paragraph()
    h.alignment = 1  # markaz
    _run(h, title, bold=True, size=font_size)
    _style_paragraph(h, hanging=False)

    ordered = sort_sources(sources, oak_groups=oak_groups)
    titles = GROUP_TITLES.get(script, GROUP_TITLES["latin"])

    n = 0
    current_group = 0
    for src in ordered:
        g = group_of(src)
        if oak_groups and g != current_group:
            current_group = g
            gp = doc.add_paragraph()
            _run(gp, titles[g], bold=True, size=font_size)
            _style_paragraph(gp, hanging=False)
        n += 1
        p = doc.add_paragraph()
        _run(p, f"{n}. {src.formatted_text}", size=font_size)
        _style_paragraph(p)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def export_docx_file(sources: list[ParsedSource], path: str | Path, **kw) -> Path:  # type: ignore[no-untyped-def]
    out = Path(path)
    out.write_bytes(export_docx(sources, **kw))
    return out


def export_text(sources: list[ParsedSource], oak_groups: bool = True, script: str = "latin") -> str:
    """Clipboard uchun matn varianti."""
    ordered = sort_sources(sources, oak_groups=oak_groups)
    titles = GROUP_TITLES.get(script, GROUP_TITLES["latin"])
    lines: list[str] = []
    n = 0
    current_group = 0
    for src in ordered:
        g = group_of(src)
        if oak_groups and g != current_group:
            current_group = g
            lines.append(f"\n{titles[g]}\n")
        n += 1
        lines.append(f"{n}. {src.formatted_text}")
    return "\n".join(lines).strip()
