"""ManbaAI Backend API — FastAPI ilovasi."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from starlette.requests import Request
from starlette.responses import Response

from .config import get_settings
from .routers import admin, auth, lists, misc, payments, sources

app = FastAPI(
    title="ManbaAI API",
    version="1.0.0",
    description="Bibliografik assistent — OAK/O'zDSt formatlash (TZ v2.0)",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if settings.env == "dev"
        else [settings.webapp_url, "https://admin.loyiha.uz"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUESTS = Counter("manba_requests_total", "HTTP so'rovlar", ["path", "method", "status"])


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):  # noqa: ANN001, ANN201
    response = await call_next(request)
    REQUESTS.labels(request.url.path, request.method, response.status_code).inc()
    return response


for r in (auth.router, sources.router, lists.router, misc.router, payments.router, admin.router):
    app.include_router(r)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.env}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
