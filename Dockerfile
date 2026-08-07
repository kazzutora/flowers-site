# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12-slim-bookworm

# ---------- base: system deps shared by every later stage ----------
FROM python:${PYTHON_VERSION} AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# libpq5: psycopg at runtime. ffmpeg: the `media` queue worker (tech.md
# §2 — snapshots/renditions, ffmpeg only runs in that container, but all
# workers share this one image for simplicity). curl: healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------- builder: compiles wheels (needs a real build toolchain) --
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip wheel --wheel-dir /wheels -r requirements/prod.txt \
    && pip wheel --wheel-dir /wheels -r requirements/dev.txt

# ---------- css: Tailwind v3 standalone CLI, no Node in the image ----
FROM base AS css
RUN curl -fsSL -o /usr/local/bin/tailwindcss \
        https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 \
    && chmod +x /usr/local/bin/tailwindcss
COPY tailwind.config.js .
COPY templates/ templates/
COPY static/css/input.css static/css/input.css
RUN tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify

# ---------- dev: full dev+prod deps; source is bind-mounted by compose
FROM base AS dev
COPY --from=builder /wheels /wheels
COPY requirements/ requirements/
RUN pip install --no-index --find-links=/wheels -r requirements/dev.txt \
    && rm -rf /wheels
COPY . .
COPY --from=css /app/static/css/tailwind.css static/css/tailwind.css
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--reload"]

# ---------- prod: minimal runtime, non-root, no compiler toolchain ----
FROM base AS prod
RUN groupadd --system app && useradd --system --gid app --home-dir /app --no-create-home app

COPY --from=builder /wheels /wheels
COPY requirements/ requirements/
RUN pip install --no-index --find-links=/wheels -r requirements/prod.txt \
    && rm -rf /wheels requirements

COPY . .
COPY --from=css /app/static/css/tailwind.css static/css/tailwind.css

# Build-time-only placeholders: collectstatic touches WhiteNoise's
# staticfiles storage, never the database or a real secret, but
# config/settings/env.py still requires these two fields to be set for
# Django to import at all (tech.md §6.1).
RUN SECRET_KEY=build-time-placeholder POSTGRES_PASSWORD=build-time-placeholder \
    python manage.py collectstatic --noinput --settings=config.settings.prod

RUN chown -R app:app /app
USER app

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
