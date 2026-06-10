"""Backend API mijozi — bot biznes-mantiqni API ga delegatsiya qiladi."""

from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings


class ApiClient:
    """Har foydalanuvchi uchun qisqa muddatli JWT bilan ishlaydi.

    Bot server-server rejimida: o'z servis tokenini emas, foydalanuvchining
    tg_id sini API ga `X-Bot-User` orqali beradi (ichki tarmoq, ALB siz ochiq emas).
    Soddalik uchun bot initData o'rniga maxsus bot endpointidan JWT oladi.
    """

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.api_base_url
        self._client = httpx.AsyncClient(base_url=self._base, timeout=30)
        self._tokens: dict[int, str] = {}

    async def _token(self, tg_id: int, first_name: str = "", lang: str = "uz") -> str:
        if tg_id in self._tokens:
            return self._tokens[tg_id]
        import hashlib
        import hmac
        import json
        import time
        from urllib.parse import urlencode

        s = get_settings()
        params = {
            "user": json.dumps({"id": tg_id, "first_name": first_name, "language_code": lang}),
            "auth_date": str(int(time.time())),
            "query_id": "bot",
        }
        check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        secret = hmac.new(b"WebAppData", s.bot_token.encode(), hashlib.sha256).digest()
        params["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        resp = await self._client.post(
            "/api/v1/auth/telegram", json={"init_data": urlencode(params)}
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self._tokens[tg_id] = token
        return token

    async def call(
        self, tg_id: int, method: str, path: str, *, retry: bool = True, **kw
    ) -> httpx.Response:
        token = await self._token(tg_id)
        resp = await self._client.request(
            method, path, headers={"Authorization": f"Bearer {token}"}, **kw
        )
        if resp.status_code == 401 and retry:  # token eskirgan — yangilash
            self._tokens.pop(tg_id, None)
            return await self.call(tg_id, method, path, retry=False, **kw)
        return resp

    async def parse(self, tg_id: int, text: str) -> dict[str, Any]:
        resp = await self.call(tg_id, "POST", "/api/v1/sources/parse", json={"text": text})
        resp.raise_for_status()
        return resp.json()


api = ApiClient()
