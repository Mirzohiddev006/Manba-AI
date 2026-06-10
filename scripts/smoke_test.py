#!/usr/bin/env python3
"""Smoke-test: docker-compose up dan keyin to'liq oqim — parse → list → export.

Ishlatish: python scripts/smoke_test.py [API_BASE]
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
from urllib.parse import urlencode

import httpx

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
BOT_TOKEN = "12345:TEST_TOKEN"  # .env dagi BOT_TOKEN bilan mos bo'lsin


def make_init_data() -> str:
    params = {
        "user": json.dumps({"id": 555001, "first_name": "Smoke", "language_code": "uz"}),
        "auth_date": str(int(time.time())),
        "query_id": "smoke",
    }
    check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


def main() -> int:
    c = httpx.Client(base_url=API, timeout=30)

    print("1) /health…", end=" ")
    r = c.get("/health")
    assert r.status_code == 200, r.text
    print("OK")

    print("2) auth…", end=" ")
    r = c.post("/api/v1/auth/telegram", json={"init_data": make_init_data()})
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    print("OK")

    print("3) parse…", end=" ")
    r = c.post("/api/v1/sources/parse", headers=headers, json={"text": (
        "Karimov A.A. Iqtisodiyot nazariyasi: Darslik. – Toshkent: Iqtisod-moliya, 2020. – 350 b.\n"
        "Jahon banki ma'lumotlari [Elektron resurs]. – URL: https://data.worldbank.org "
        "(murojaat sanasi: 15.05.2026)."
    )})
    assert r.status_code == 200, r.text
    sources = r.json()["sources"]
    assert len(sources) == 2 and sources[0]["source_type"] == "book"
    print(f"OK ({len(sources)} manba)")

    print("4) list…", end=" ")
    r = c.post("/api/v1/lists", headers=headers, json={"title": "Smoke ro'yxat"})
    list_id = r.json()["id"]
    for s in sources:
        r = c.post(f"/api/v1/lists/{list_id}/items/{s['id']}", headers=headers)
        assert r.status_code == 201, r.text
    print("OK")

    print("5) export…", end=" ")
    r = c.post(f"/api/v1/lists/{list_id}/export", headers=headers,
               json={"fmt": "docx", "script": "latin", "font_size": 14})
    assert r.status_code == 200 and r.content[:2] == b"PK", "DOCX emas"
    print(f"OK ({len(r.content)} bayt)")

    print("\n✅ Smoke-test o'tdi: parse → list → export")
    return 0


if __name__ == "__main__":
    sys.exit(main())
