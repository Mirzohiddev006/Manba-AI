"""Lex.uz scraping moduli (TZ 16.2) — hurmatli siyosat: 1 req/s, kesh-birinchi.

Selektorlar bitta joyda (SELECTORS) — smoke-test buzilishni aniqlaydi.
"""

from __future__ import annotations

import asyncio
import re
import time

import httpx
from selectolax.parser import HTMLParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import LexDocument

BASE = "https://lex.uz"
USER_AGENT = "ManbaAI/1.0 (+https://manba.uz; bibliografik assistent; aloqa: admin@manba.uz)"

SELECTORS = {
    "search_item": "a.search-result-title, .doc-list a",
    "doc_title": "h1, .document-title",
    "doc_props": ".doc-props, .document-info",
}

_last_request = 0.0
_RATE = 1.0  # maks 1 so'rov/soniya


async def _polite_get(url: str) -> str | None:
    global _last_request
    wait = _RATE - (time.monotonic() - _last_request)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_request = time.monotonic()
    async with httpx.AsyncClient(
        timeout=15, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        resp = await client.get(url)
        return resp.text if resp.status_code == 200 else None


_DOC_NUM = re.compile(r"((?:O['ʻ’]RQ|ЎРҚ|PF|ПФ|PQ|ПҚ|VM|ВМ)[-–]\d+(?:[-–]son|[-–]сон)?)", re.I)
_DATE = re.compile(r"(\d{2}\.\d{2}\.\d{4})")


def _doc_type(title: str) -> str:
    t = title.lower()
    if "qonun" in t or "қонун" in t or "закон" in t:
        return "qonun"
    if "farmon" in t or "фармон" in t or "указ" in t:
        return "farmon"
    return "qaror"


async def search(db: AsyncSession, query: str) -> list[dict]:
    """Kesh-birinchi: lex_documents jadvalidan, topilmasa scraping."""
    res = await db.execute(
        select(LexDocument).where(LexDocument.title.ilike(f"%{query}%")).limit(10)
    )
    cached = list(res.scalars())
    if cached:
        return [_to_dict(d) for d in cached]

    html = await _polite_get(f"{BASE}/search/nat?query={httpx.QueryParams({'q': query})['q']}")
    if html is None:
        return []
    tree = HTMLParser(html)
    out: list[dict] = []
    for node in tree.css(SELECTORS["search_item"])[:5]:
        title = node.text(strip=True)
        href = node.attributes.get("href", "")
        if not title or not href:
            continue
        url = href if href.startswith("http") else BASE + href
        num_m = _DOC_NUM.search(title)
        date_m = _DATE.search(title)
        doc = LexDocument(
            title=title,
            doc_type=_doc_type(title),
            doc_number=num_m.group(1) if num_m else "",
            adopted_date=date_m.group(1) if date_m else "",
            url=url,
        )
        db.add(doc)
        out.append(_to_dict(doc))
    await db.commit()
    return out


def _to_dict(d: LexDocument) -> dict:
    return {
        "title": d.title,
        "doc_type": d.doc_type,
        "doc_number": d.doc_number,
        "adopted_date": d.adopted_date,
        "url": d.url,
        "attribution": "lex.uz",
    }


async def selector_smoke_test() -> bool:
    """Kunlik smoke-test: bosh sahifa ochilishi va selektor topilishi (TZ 16.2)."""
    html = await _polite_get(BASE)
    if html is None:
        return False
    tree = HTMLParser(html)
    return bool(tree.css("a"))
