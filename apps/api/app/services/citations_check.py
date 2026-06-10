"""Matn ichi havolalar tekshiruvi (TZ 16.3): [1], [2, 5], [12–15] ↔ ro'yxat."""

from __future__ import annotations

import io
import re

_REF = re.compile(r"\[(\d+(?:\s*[-–,]\s*\d+)*)\]")


def extract_citation_numbers(docx_bytes: bytes) -> set[int]:
    from docx import Document

    doc = Document(io.BytesIO(docx_bytes))
    nums: set[int] = set()
    for para in doc.paragraphs:
        for m in _REF.finditer(para.text):
            for part in re.split(r",", m.group(1)):
                part = part.strip()
                if "–" in part or "-" in part:
                    a, b = re.split(r"[-–]", part)
                    nums.update(range(int(a), int(b) + 1))
                elif part.isdigit():
                    nums.add(int(part))
    return nums


def check(docx_bytes: bytes, list_size: int) -> dict:
    used = extract_citation_numbers(docx_bytes)
    all_nums = set(range(1, list_size + 1))
    unused = sorted(all_nums - used)  # ro'yxatda bor, matnda yo'q — OAK buzilishi
    missing = sorted(n for n in used if n > list_size)  # matnda bor, ro'yxatda yo'q
    return {
        "used_count": len(used & all_nums),
        "unused_in_text": unused,
        "missing_in_list": missing,
        "ok": not unused and not missing,
        "warning": (
            "OAK talabi: ishlatilmagan manba ro'yxatga kiritilishi mumkin emas"
            if unused else ""
        ),
    }
