# syntax=docker/dockerfile:1

# --- Build: install the project and its runtime dependencies into a venv ---
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /bin/uv

# Byte-compile for faster startup, copy files out of uv's cache instead of
# hardlinking (the cache doesn't exist in the final image), and use the
# image's own Python rather than letting uv download one.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, in their own layer, so code-only changes don't reinstall
# them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then the project itself. --no-editable installs it into the venv's
# site-packages, so the runtime stage only needs the venv, not src/.
# README.md is read by the build backend (pyproject.toml's `readme`).
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# --- Runtime: just the venv plus what Alembic needs, run as non-root ---
FROM python:3.12-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
# Needed by the pre-deploy `alembic upgrade head`, run from this directory.
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations

USER app

# PORT (set by Railway) and ORIGIN are read from the environment by the CLI,
# so no shell is needed to expand them, and shutdown signals reach the app
# directly.
CMD ["caching-proxy"]
