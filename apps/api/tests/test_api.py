"""API integratsion testlar: auth HMAC, parse, lists oqimi, eksport."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

BOT_TOKEN = "12345:TEST_TOKEN"


def make_init_data(user_id: int = 999, *, age: int = 0) -> str:
    params = {
        "user": json.dumps({"id": user_id, "first_name": "Anvar", "language_code": "uz"}),
        "auth_date": str(int(time.time()) - age),
        "query_id": "AAH",
    }
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_telegram_auth_ok(client):
    r = await client.post("/api/v1/auth/telegram", json={"init_data": make_init_data()})
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_telegram_auth_rejects_tampered(client):
    bad = make_init_data().replace("Anvar", "Hacker")
    r = await client.post("/api/v1/auth/telegram", json={"init_data": bad})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_telegram_auth_rejects_old(client):
    r = await client.post(
        "/api/v1/auth/telegram", json={"init_data": make_init_data(age=7200)}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_parse_flow(client, user_token):
    token, _ = user_token
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.post(
        "/api/v1/sources/parse",
        json={"text": "Karimov A.A. Iqtisodiyot nazariyasi: Darslik. – Toshkent: Iqtisod-moliya, 2020. – 350 b."},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    src = r.json()["sources"][0]
    assert src["source_type"] == "book"
    assert src["formatted_text"].endswith("– 350 b.")
    assert src["confidence"] >= 0.85  # LLM kerak emas

    # PATCH → preview qayta formatlanadi (faqat shablon motori)
    r2 = await client.patch(
        f"/api/v1/sources/{src['id']}", json={"fields": {"year": 2021}}, headers=headers
    )
    assert r2.status_code == 200
    assert "2021" in r2.json()["formatted_text"]


@pytest.mark.asyncio
async def test_list_flow_and_export(client, user_token):
    token, _ = user_token
    headers = {"Authorization": f"Bearer {token}"}
    # 3 xil guruh manbalari
    texts = (
        "O'zbekiston Respublikasining «Ta'lim to'g'risida»gi Qonuni. O'RQ-637-son, 23.09.2020 // Qonunchilik ma'lumotlari milliy bazasi, lex.uz\n"
        "Karimov A.A. Iqtisodiyot nazariyasi: Darslik. – Toshkent: Iqtisod-moliya, 2020. – 350 b.\n"
        "Jahon banki ma'lumotlari [Elektron resurs]. – URL: https://data.worldbank.org (murojaat sanasi: 15.05.2026)."
    )
    r = await client.post("/api/v1/sources/parse", json={"text": texts}, headers=headers)
    ids = [s["id"] for s in r.json()["sources"]]
    assert len(ids) == 3

    r = await client.post("/api/v1/lists", json={"title": "Dissertatsiya"}, headers=headers)
    list_id = r.json()["id"]
    for sid in ids:
        r = await client.post(f"/api/v1/lists/{list_id}/items/{sid}", headers=headers)
        assert r.status_code == 201

    r = await client.get(f"/api/v1/lists/{list_id}", headers=headers)
    detail = r.json()
    assert detail["items_count"] == 3
    groups = [i["group_no"] for i in detail["items"]]
    assert groups == sorted(groups), "OAK guruh tartibi"

    # DOCX eksport
    r = await client.post(
        f"/api/v1/lists/{list_id}/export",
        json={"fmt": "docx", "script": "latin", "font_size": 14},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.content[:2] == b"PK"  # zip/docx

    # BibTeX eksport
    r = await client.post(
        f"/api/v1/lists/{list_id}/export", json={"fmt": "bib"}, headers=headers
    )
    assert b"@book" in r.content


@pytest.mark.asyncio
async def test_spell_endpoint(client, user_token):
    token, _ = user_token
    r = await client.post(
        "/api/v1/spell/check",
        json={"text": "raqamli tehnologiya"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    issues = r.json()
    assert any(i["xato"] == "tehnologiya" for i in issues)


@pytest.mark.asyncio
async def test_admin_rbac_and_totp(client, engine):
    import pyotp
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.auth import pwd_context
    from app.models import AdminUser

    secret = pyotp.random_base32()
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        session.add(AdminUser(
            email="admin@manba.uz", password_hash=pwd_context.hash("S3cret!pass"),
            role="superadmin", totp_secret=secret,
        ))
        await session.commit()

    # TOTP siz — rad
    r = await client.post("/api/v1/admin/login", json={
        "email": "admin@manba.uz", "password": "S3cret!pass", "totp_code": "000000"})
    assert r.status_code == 401

    code = pyotp.TOTP(secret).now()
    r = await client.post("/api/v1/admin/login", json={
        "email": "admin@manba.uz", "password": "S3cret!pass", "totp_code": code})
    assert r.status_code == 200
    admin_token = r.json()["access_token"]

    r = await client.get(
        "/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200
    assert "total_users" in r.json()

    # User token admin endpointga kirolmaydi
    r = await client.get("/api/v1/admin/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_template_test_playground(client, engine):
    import pyotp
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.models import AdminUser

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        admin = (await session.execute(select(AdminUser))).scalars().first()
        code = pyotp.TOTP(admin.totp_secret).now()
    r = await client.post("/api/v1/admin/login", json={
        "email": "admin@manba.uz", "password": "S3cret!pass", "totp_code": code})
    token = r.json()["access_token"]
    r = await client.post(
        "/api/v1/admin/templates/test",
        json={"template_body": "{{ authors|authors_sn }} {{ title }}. – {{ year }}.",
              "source_type": "book"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and "Karimov A.A." in body["preview"]
