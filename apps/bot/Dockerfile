FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /repo
COPY pyproject.toml uv.lock* ./
COPY packages/citation-core packages/citation-core
COPY apps/bot/pyproject.toml apps/bot/
RUN uv sync --frozen --no-dev --package manba-bot || uv sync --no-dev --package manba-bot
COPY apps/bot apps/bot
WORKDIR /repo/apps/bot
ENV PATH="/repo/.venv/bin:$PATH"
CMD ["python", "-m", "bot.main"]
