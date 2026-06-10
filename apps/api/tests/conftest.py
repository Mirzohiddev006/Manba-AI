"""API test konfiguratsiyasi — SQLite in-memory, Redis/S3 patch."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("BOT_TOKEN", "12345:TEST_TOKEN")
sys.path.insert(0, str(Path(__file__).parents[3] / "packages" / "citation-core"))
sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    from app.models import Base

    eng = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def client(engine, monkeypatch):
    from app import db as db_module
    from app.main import app
    from app.services import limits

    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_db():
        async with maker() as session:
            yield session

    app.dependency_overrides[db_module.get_db] = override_db

    async def no_limit(user, kind):  # noqa: ANN001
        return None

    async def fake_usage(user):  # noqa: ANN001
        return {"sources": 0, "pdf": 0}

    monkeypatch.setattr(limits, "check_and_increment", no_limit)
    monkeypatch.setattr(limits, "usage_today", fake_usage)
    # routerlar import qilgan nusxalarni ham almashtirish
    from app.routers import misc, sources

    monkeypatch.setattr(sources, "check_and_increment", no_limit)
    monkeypatch.setattr(misc, "check_and_increment", no_limit)
    monkeypatch.setattr(misc, "usage_today", fake_usage)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user_token(engine):
    from app.auth import make_user_jwt
    from app.models import User

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        import random as _r

        user = User(tg_id=_r.randint(10**8, 10**9), first_name="Test", lang="uz")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return make_user_jwt(user.id, user.tg_id), user.id
