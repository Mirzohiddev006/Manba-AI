"""OAK 3-guruh saralash + kirill-lotin aralash collation.

Guruhlar (TZ 2.2):
  1 — normativ-huquqiy hujjatlar (kiritilgan tartibda, muhimlik bo'yicha)
  2 — asosiy adabiyotlar: avval o'zbek/rus (kirill yoki lotin), alifbo bo'yicha;
      so'ng xorijiy tillardagi manbalar
  3 — internet resurslar
"""

from __future__ import annotations

import re

from .models import ParsedSource, SourceType

GROUP_LEGAL, GROUP_MAIN, GROUP_WEB = 1, 2, 3

# O'zbek lotin alifbosi tartibi (1995/2021): ... z, o', g', sh, ch, ng
_UZ_LATIN = "abdefghijklmnopqrstuvxyz"  # asosiy harflar
# Maxsus collation: har belgiga tartib raqami. Kirill va lotin BIRGA saralanadi —
# kirill harfi lotin ekvivalenti pozitsiyasiga xaritalanadi (aralash ro'yxat talabi).
_CYR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "s", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
    "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'",
    "ҳ": "h",
}
# Digraf va maxsus harflar tartibi (z dan keyin): o' g' sh ch ng
_ORDER = {ch: i for i, ch in enumerate(_UZ_LATIN)}
_ORDER.update({"o'": 24, "g'": 25, "sh": 26, "ch": 27, "ng": 28, "'": 29})


def collation_key(text: str) -> tuple[int, ...]:
    """Aralash kirill-lotin matn uchun saralash kaliti."""
    s = text.lower().replace("ʻ", "'").replace("’", "'").replace("`", "'")
    out: list[int] = []
    i = 0
    while i < len(s):
        ch = s[i]
        ch2 = s[i : i + 2]
        if ch in _CYR2LAT:
            for c in _CYR2LAT[ch]:
                pair = _CYR2LAT[ch]
                if pair in _ORDER and len(pair) == 2:
                    out.append(100 + _ORDER[pair])
                    break
                out.append(100 + _ORDER.get(c, 99))
            i += 1
            continue
        if ch2 in ("o'", "g'", "sh", "ch", "ng") and ch2 in _ORDER:
            out.append(100 + _ORDER[ch2])
            i += 2
            continue
        if ch in _ORDER:
            out.append(100 + _ORDER[ch])
            i += 1
            continue
        if ch.isdigit():
            out.append(50 + int(ch))
            i += 1
            continue
        i += 1  # tinish belgilari e'tiborsiz
    return tuple(out)


_FOREIGN_RE = re.compile(r"^[\x00-\x7F\s«»–—'’.,;:()\[\]/№-]+$")


def is_foreign(src: ParsedSource) -> bool:
    if src.source_type == SourceType.FOREIGN_ARTICLE:
        return True
    probe = (src.fields.authors[0].surname if src.fields.authors else src.fields.title) or ""
    # Faqat ASCII bo'lsa-yu, o'zbekcha so'z belgilarisiz — xorijiy deb hisoblanadi
    return bool(_FOREIGN_RE.match(probe)) and not re.search(
        r"o'|g'|sh|ch|q[aeiou]", probe.lower()
    ) and src.fields.language in ("en", "de", "fr")


def group_of(src: ParsedSource) -> int:
    if src.source_type == SourceType.LEGAL:
        return GROUP_LEGAL
    if src.source_type == SourceType.WEB:
        return GROUP_WEB
    return GROUP_MAIN


def sort_sources(sources: list[ParsedSource], oak_groups: bool = True) -> list[ParsedSource]:
    """OAK tartibida saralaydi. oak_groups=False — yagona alifbo."""

    def main_key(s: ParsedSource) -> tuple:
        head = s.fields.authors[0].surname if s.fields.authors else s.fields.title
        return (1 if is_foreign(s) else 0, collation_key(head), collation_key(s.fields.title))

    if not oak_groups:
        return sorted(sources, key=main_key)

    legal = [s for s in sources if group_of(s) == GROUP_LEGAL]  # kiritilgan tartib saqlanadi
    main = sorted((s for s in sources if group_of(s) == GROUP_MAIN), key=main_key)
    web = sorted((s for s in sources if group_of(s) == GROUP_WEB), key=lambda s: collation_key(s.fields.title))
    return legal + main + web


GROUP_TITLES = {
    "latin": {
        GROUP_LEGAL: "I. Normativ-huquqiy hujjatlar",
        GROUP_MAIN: "II. Asosiy adabiyotlar",
        GROUP_WEB: "III. Internet manbalar",
    },
    "cyrillic": {
        GROUP_LEGAL: "I. Норматив-ҳуқуқий ҳужжатлар",
        GROUP_MAIN: "II. Асосий адабиётлар",
        GROUP_WEB: "III. Интернет манбалар",
    },
}
