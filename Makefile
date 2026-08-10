COMPOSE ?= docker compose
RUN = $(COMPOSE) run --rm web

.PHONY: up down build logs migrate makemigrations seed test lint fmt shell css

up:
	$(COMPOSE) up

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f web celery celery-beat

migrate:
	$(RUN) python manage.py migrate

makemigrations:
	$(RUN) python manage.py makemigrations

seed:
	$(RUN) python scripts/seed.py

test:
	$(RUN) pytest

lint:
	$(RUN) ruff check .
	$(RUN) ruff format --check .
	$(RUN) mypy .

fmt:
	$(RUN) ruff format .
	$(RUN) ruff check --fix .

shell:
	$(RUN) python manage.py shell

css:
	$(RUN) tailwindcss -i static/css/input.css -o static/css/app.css --minify
