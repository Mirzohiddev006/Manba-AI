FROM python:3.12-slim AS base
# Tesseract OCR (uzb, uzb_cyrl, rus, eng) — PDF worker uchun
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-uzb tesseract-ocr-uzb-cyrl tesseract-ocr-rus tesseract-ocr-eng \
    libpq5 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /repo
COPY pyproject.toml uv.lock* ./
COPY packages/citation-core packages/citation-core
COPY apps/api/pyproject.toml apps/api/
RUN uv sync --frozen --no-dev --package manba-api || uv sync --no-dev --package manba-api
COPY apps/api apps/api
WORKDIR /repo/apps/api
ENV PATH="/repo/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
