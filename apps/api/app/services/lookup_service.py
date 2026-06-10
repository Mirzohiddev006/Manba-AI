"""DOI/ISBN lookup — CrossRef + OpenLibrary, Redis kesh 30 kun (TZ 16.1)."""

from __future__ import annotations

import json

import httpx

from ..config import get_settings
from ..redis_client import get_redis

CACHE_TTL = 30 * 86400


async def _cached_get(url: str, cache_key: str) -> dict | None:
    r = get_redis()
    hit = await r.get(cache_key)
    if hit:
        return json.loads(hit)
    headers = {"User-Agent": f"ManbaAI/1.0 (mailto:{get_settings().crossref_mailto})"}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
    await r.set(cache_key, json.dumps(data), ex=CACHE_TTL)
    return data


async def lookup_doi(doi: str) -> dict | None:
    """CrossRef polite pool (mailto so'rovda)."""
    mailto = get_settings().crossref_mailto
    data = await _cached_get(
        f"https://api.crossref.org/works/{doi}?mailto={mailto}", f"doi:{doi}"
    )
    if not data:
        return None
    msg = data.get("message", {})
    authors = [
        {"surname": a.get("family", ""), "initials": _initials(a.get("given", ""))}
        for a in msg.get("author", [])
    ]
    issued = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {
        "source_type": "foreign_article",
        "fields": {
            "authors": authors,
            "title": (msg.get("title") or [""])[0],
            "journal": (msg.get("container-title") or [""])[0],
            "year": issued,
            "volume": msg.get("volume", ""),
            "issue": msg.get("issue", ""),
            "pages_range": (msg.get("page") or "").replace("-", "–"),
            "doi": doi,
        },
    }


async def lookup_isbn(isbn: str) -> dict | None:
    """OpenLibrary; topilmasa Google Books zaxira."""
    clean = isbn.replace("-", "").replace(" ", "")
    data = await _cached_get(f"https://openlibrary.org/isbn/{clean}.json", f"isbn:{clean}")
    if data:
        year = "".join(ch for ch in data.get("publish_date", "") if ch.isdigit())[-4:]
        return {
            "source_type": "book",
            "fields": {
                "title": data.get("title", ""),
                "publisher": (data.get("publishers") or [""])[0],
                "year": int(year) if year else None,
                "pages_total": data.get("number_of_pages"),
                "isbn": clean,
            },
        }
    g = await _cached_get(
        f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean}", f"gbooks:{clean}"
    )
    if g and g.get("items"):
        info = g["items"][0]["volumeInfo"]
        return {
            "source_type": "book",
            "fields": {
                "title": info.get("title", ""),
                "authors": [
                    {"surname": a.split()[-1], "initials": _initials(" ".join(a.split()[:-1]))}
                    for a in info.get("authors", [])
                ],
                "publisher": info.get("publisher", ""),
                "year": int(info.get("publishedDate", "0")[:4] or 0) or None,
                "pages_total": info.get("pageCount"),
                "isbn": clean,
            },
        }
    return None


def _initials(given: str) -> str:
    return "".join(f"{p[0]}." for p in given.replace(".", " ").split() if p)
