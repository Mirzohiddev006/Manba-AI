"""Preprocessing: tozalash, yozuvni aniqlash, ko'p manbali matnni ajratish."""

from __future__ import annotations

import re

from .models import Script

_CYR = re.compile(r"[а-яёўқғҳА-ЯЁЎҚҒҲ]")
_LAT = re.compile(r"[a-zA-Z]")

# Boshidagi raqamlash: «1. », «12) », «[3] », «– » va h.k.
_LEADING_NUM = re.compile(r"^\s*(?:\[\d{1,3}\]\s*|\d{1,3}[.)]\s+|[-–—•]\s+)")

_WS = re.compile(r"[ \t  ]+")

_URL_LIKE = re.compile(r"https?://\S+|www\.\S+|\b10\.\d{4,9}/\S+|\(PhD\)|\(DSc\)|URL")


def detect_script(text: str) -> Script:
    text = _URL_LIKE.sub("", text)  # URL/DOI/daraja qisqartmalari hisobga olinmaydi
    cyr = len(_CYR.findall(text))
    lat = len(_LAT.findall(text))
    if cyr == 0 and lat == 0:
        return Script.LATIN
    if cyr and lat and min(cyr, lat) / max(cyr, lat) > 0.35:
        return Script.MIXED
    return Script.CYRILLIC if cyr > lat else Script.LATIN


def clean_line(line: str) -> str:
    """Bitta satrni tozalash: raqamlash va ortiqcha bo'shliqlar olib tashlanadi.

    Diqqat: tire turlari (– va —) normallashtirilmaydi — rasmiy hujjat
    nomlarida em-tire saqlanishi shart («Raqamli O'zbekiston — 2030»).
    """
    line = _LEADING_NUM.sub("", line.strip())
    line = _WS.sub(" ", line)
    return line.strip()


def split_sources(text: str) -> list[str]:
    """Ko'p manbali matnni alohida yozuvlarga ajratadi.

    Qoida: har yangi satr — yangi manba nomzodi; lekin kichik harf bilan
    boshlangan yoki juda qisqa davom satrlar oldingisiga qo'shiladi
    (Word dan ko'chirilgan o'ralgan satrlar holati).
    """
    lines = [ln for ln in (clean_line(x) for x in text.splitlines()) if ln]
    out: list[str] = []
    for ln in lines:
        starts_new = bool(re.match(r"^[A-ZА-ЯЁЎҚҒҲO'«\d]", ln))
        if out and (not starts_new or len(ln) < 25 and not _ends_complete(out[-1])):
            out[-1] = f"{out[-1]} {ln}"
        else:
            out.append(ln)
    # takrorlarni olib tashlash (tartib saqlanadi)
    seen: set[str] = set()
    uniq = []
    for s in out:
        key = re.sub(r"\W+", "", s.lower())
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    return uniq


def _ends_complete(s: str) -> bool:
    return s.rstrip().endswith((".", ".)", "»"))
