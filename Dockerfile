# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
ARG TAILWIND_VERSION=v3.4.17

# --- base: runtime interpreter and OS packages shared by every stage -----------
FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/venv/bin:$PATH" \
    # django-admin, celery and gunicorn do not all add the workdir themselves.
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=config.settings
# gettext provides msgfmt for compilemessages; curl is used by healthchecks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# --- tailwind: standalone CLI binary, no Node.js anywhere in the image ---------
FROM base AS tailwind
ARG TAILWIND_VERSION
ARG TARGETARCH=amd64
RUN set -eu; \
    case "$TARGETARCH" in \
    amd64) arch=x64 ;; \
    arm64) arch=arm64 ;; \
    *) echo "unsupported arch: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /usr/local/bin/tailwindcss \
    "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-${arch}"; \
    chmod +x /usr/local/bin/tailwindcss

# --- deps: python dependencies into a self-contained virtualenv ---------------
FROM base AS deps
RUN python -m venv /venv
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

FROM deps AS deps-dev
RUN pip install --no-cache-dir ".[dev]"

# --- dev: source is bind-mounted by compose, tooling included -----------------
FROM base AS dev
COPY --from=deps-dev /venv /venv
COPY --from=tailwind /usr/local/bin/tailwindcss /usr/local/bin/tailwindcss
RUN useradd --system --create-home --uid 10001 app \
    && mkdir -p /app/media/public /app/media/private /app/staticfiles \
    && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- runtime: production image, no dev tooling --------------------------------
FROM base AS runtime
COPY --from=deps /venv /venv
COPY --from=tailwind /usr/local/bin/tailwindcss /usr/local/bin/tailwindcss
RUN useradd --system --create-home --uid 10001 app
COPY --chown=app:app . /app
# Empty DJANGO_SETTINGS_MODULE keeps compilemessages from loading settings: the
# real environment does not exist at build time.
#
# collectstatic does need settings, so it gets throwaway ones. They are only
# ever seen by this one command inside the build: nothing is connected to, and
# the image carries no trace of them.
RUN set -eu; \
    tailwindcss -i static/css/input.css -o static/css/app.css --minify; \
    DJANGO_SETTINGS_MODULE= django-admin compilemessages; \
    mkdir -p /app/media/public /app/media/private /app/staticfiles; \
    SECRET_KEY=build-only \
    SITE_URL=http://build.invalid \
    DATABASE_URL=postgresql://build:build@127.0.0.1:5432/build \
    REDIS_URL=redis://127.0.0.1:6379/0 \
    CELERY_BROKER_URL=redis://127.0.0.1:6379/1 \
    CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2 \
    IP_HASH_SALT=build-only \
    python manage.py collectstatic --noinput --clear; \
    chown -R app:app /app/media /app/staticfiles /app/static
USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
