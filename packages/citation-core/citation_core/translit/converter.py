"""Kirill ↔ lotin transliteratsiya — 2021-yilgi lotin imlo qoidalari (V2, TZ 16.4).

Kontekst qoidalari:
  ц → "s" so'z boshida/undoshdan keyin, "ts" unlidan keyin;
  е → "ye" so'z boshida va unli/ъ/ь dan keyin, aks holda "e".
Istisnolar lug'ati (xorijiy nomlar, brendlar, URL) konvertatsiya qilinmaydi.
"""

from __future__ import annotations

import re

_VOWELS_CYR = set("аеёиоуэюяўАЕЁИОУЭЮЯЎ")

_CYR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x",
    "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'", "ь": "", "э": "e",
    "ю": "yu", "я": "ya", "ё": "yo", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}

# Lotin → kirill: digraflar avval
_LAT2CYR_DIGRAPHS = [
    ("o'", "ў"), ("oʻ", "ў"), ("o’", "ў"), ("g'", "ғ"), ("gʻ", "ғ"), ("g’", "ғ"),
    ("sh", "ш"), ("ch", "ч"), ("yo", "ё"), ("yu", "ю"), ("ya", "я"), ("ye", "е"),
    ("ts", "ц"),
]
_LAT2CYR = {
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ",
    "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
    "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
    "x": "х", "y": "й", "z": "з", "'": "ъ",
}

_PROTECTED = re.compile(r"https?://\S+|www\.\S+|\S+@\S+|\b10\.\d{4,9}/\S+")


class Transliterator:
    def __init__(self, exceptions: set[str] | None = None) -> None:
        self._exceptions = {e.lower() for e in (exceptions or set())}

    def _is_exception(self, word: str) -> bool:
        return word.lower() in self._exceptions

    def cyr_to_lat(self, text: str) -> str:
        return self._convert(text, self._cyr_word_to_lat)

    def lat_to_cyr(self, text: str) -> str:
        return self._convert(text, self._lat_word_to_cyr)

    def _convert(self, text: str, fn) -> str:  # type: ignore[no-untyped-def]
        # URL/DOI/email himoyalanadi
        protected: list[str] = []

        def stash(m: re.Match[str]) -> str:
            protected.append(m.group(0))
            return f"\x00{len(protected) - 1}\x00"

        text = _PROTECTED.sub(stash, text)
        out = []
        # Apostrof (' ʻ ’) so'z belgisi hisoblanadi — digraflar buzilmasin
        for token in re.split(r"([^\w'ʻ’]+)", text):
            if not token or not token[0].isalpha() or self._is_exception(token):
                out.append(token)
            else:
                out.append(fn(token))
        result = "".join(out)
        for i, p in enumerate(protected):
            result = result.replace(f"\x00{i}\x00", p)
        return result

    @staticmethod
    def _cyr_word_to_lat(word: str) -> str:
        out: list[str] = []
        for i, ch in enumerate(word):
            low = ch.lower()
            if low == "е":
                soft = _VOWELS_CYR | {"ъ", "ь", "Ъ", "Ь"}
                rep = "ye" if i == 0 or word[i - 1] in soft else "e"
            elif low == "ц":
                prev_vowel = i > 0 and word[i - 1] in _VOWELS_CYR
                rep = "ts" if prev_vowel else "s"
            else:
                rep = _CYR2LAT.get(low, ch)
            if ch.isupper() and rep:
                rep = rep[0].upper() + rep[1:]
            out.append(rep)
        return "".join(out)

    @staticmethod
    def _lat_word_to_cyr(word: str) -> str:
        s = word
        result = ""
        i = 0
        while i < len(s):
            matched = False
            for dg, cyr in _LAT2CYR_DIGRAPHS:
                chunk = s[i : i + len(dg)]
                if chunk.lower() == dg:
                    result += cyr.upper() if chunk[0].isupper() else cyr
                    i += len(dg)
                    matched = True
                    break
            if matched:
                continue
            ch = s[i]
            rep = _LAT2CYR.get(ch.lower(), ch)
            result += rep.upper() if ch.isupper() else rep
            i += 1
        return result
