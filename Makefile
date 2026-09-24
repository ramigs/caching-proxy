# Name of the app service in the Railway project. Passed explicitly so a
# deploy can never land on the Postgres service by accident.
SERVICE ?= caching-proxy

.PHONY: deploy stop clear-cache-prod test lint

deploy:
	railway up --service $(SERVICE)

stop:
	railway down --service $(SERVICE)

clear-cache-prod:
	railway ssh --service $(SERVICE) -- caching-proxy --clear-cache

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright
