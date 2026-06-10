"""Umumiy regex naqshlar — barcha manba turlari uchun."""

from __future__ import annotations

import re

# «Karimov A.A.» yoki «Karimov A.» — familiya + initsiallar
AUTHOR = re.compile(
    r"(?P<surname>[A-ZА-ЯЁЎҚҒҲ][a-zа-яёўқғҳ'ʻ’-]+)\s+"
    r"(?P<initials>(?:[A-ZА-ЯЁЎҚҒҲ]\.\s?){1,3})"
)
# «A.A.Karimov» — initsiallar oldin (4+ mualliflik shakl)
AUTHOR_INV = re.compile(
    r"(?P<initials>(?:[A-ZА-ЯЁЎҚҒҲ]\.\s?){1,3})\s*"
    r"(?P<surname>[A-ZА-ЯЁЎҚҒҲ][a-zа-яёўқғҳ'ʻ’-]+)"
)
YEAR = re.compile(r"\b(1[4-9]\d{2}|20\d{2}|2100)\b")
PAGES_TOTAL = re.compile(r"[-–]\s*(\d{1,4})\s*(b|б|с|p)\.", re.IGNORECASE)
PAGES_RANGE = re.compile(r"[-–]\s*(B|Б|С|P)\.\s*(\d{1,4})\s*[-–]\s*(\d{1,4})", re.IGNORECASE)
DEGREE_DISS = re.compile(
    r"^(?P<title>.+?):\s*(?P<degree>[^:]+?)\s*\.\.\.\s*(?:diss|дисс)", re.IGNORECASE
)
VOLUME = re.compile(r"\b(?:Vol|Т|T|Jild)\.?\s*(\d{1,3})", re.IGNORECASE)
ISSUE = re.compile(r"[№N#]\s*(\d{1,3})")
URL = re.compile(r"https?://[^\s)»]+")
DOI = re.compile(r"\b10\.\d{4,9}/[^\s»)]+")
ISBN = re.compile(r"\b(?:ISBN[:\s]*)?((?:97[89][- ]?)?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?[\dXx])\b")
ACCESSED = re.compile(
    r"(?:murojaat sanasi|мурожаат санаси|дата обращения)[:\s]*(\d{2}\.\d{2}\.\d{4})",
    re.IGNORECASE,
)
# – Toshkent: Fan, 2019 — shahar: nashriyot, yil
CITY_PUB_YEAR = re.compile(
    r"[-–]\s*(?P<city>[A-ZА-ЯЁЎҚҒҲ][\w'ʻ’.-]+(?:\s[A-ZА-ЯЁЎҚҒҲ][\w'ʻ’.-]+)?)\s*:\s*"
    r"(?P<pub>[^,]+?),\s*(?P<year>\d{4})"
)
# – Samarqand, 2022 — shahar, yil (nashriyotsiz)
CITY_YEAR = re.compile(
    r"[-–]\s*(?P<city>[A-ZА-ЯЁЎҚҒҲ][\w'ʻ’.-]+(?:\s[A-ZА-ЯЁЎҚҒҲ][\w'ʻ’.-]+)?)\s*,\s*(?P<year>\d{4})"
)
DOC_NUMBER = re.compile(
    r"\b((?:O['ʻ’]RQ|ЎРҚ|PF|ПФ|PQ|ПҚ|VM|ВМ)[-–]\d+(?:[-–]son|[-–]сон)?)", re.IGNORECASE
)
DOC_DATE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")
DEGREE = re.compile(
    r"(?P<degree>[A-ZА-ЯЁЎҚҒҲ][^:]*?(?:fan|фан)[^.]*?\b"
    r"(?:dok|док|nomzod|номзод)[^.]*?(?:\((?:PhD|DSc)\))?)\s*\.{0,3}\s*"
    r"(?:\.\.\.\s*)?(?:diss|дисс)",
    re.IGNORECASE,
)
DISS = re.compile(r"\b(?:diss|дисс)\b", re.IGNORECASE)
AVTOREF = re.compile(r"\b(?:avtoref|автореф)", re.IGNORECASE)
MANY_AUTHORS = re.compile(r"/\s*(?P<authors>[^/]+?)\s*\[(?:va boshq|ва бошқ|и др)\.?\]", re.IGNORECASE)
LEGAL_HINT = re.compile(
    r"(?:Qonun|Қонун|закон|Farmon|Фармон|указ|Qaror|Қарор|постановлен|lex\.uz|"
    r"O['ʻ’]zbekiston Respublikasi|Ўзбекистон Республикаси)",
    re.IGNORECASE,
)
ELEKTRON = re.compile(r"\[(?:Elektron resurs|Электрон ресурс|Электронный ресурс)\]", re.IGNORECASE)
LATIN_TEXT = re.compile(r"^[\x00-\x7F«»–—'’ʻÀ-ɏ]+$")
