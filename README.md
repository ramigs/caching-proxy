# caching-proxy

A CLI tool that starts a caching proxy server. It forwards requests to a
configured origin server, caches the responses, and serves cached responses
on repeat requests instead of hitting the origin again.

Built as a solution to the [roadmap.sh caching proxy
project](https://roadmap.sh/projects/caching-server).

## How it works

- `GET` requests are looked up in the cache first. On a miss, the request is
  forwarded to the origin, the response is cached, and `X-Cache: MISS` is
  added to it. On a hit, the cached response is returned directly with
  `X-Cache: HIT`.
- Non-`GET` requests are forwarded to the origin transparently and are never
  cached.
- The cache is stored in Postgres and can be cleared on demand with
  `--clear-cache`.

## Caching strategy

This proxy implements **cache-aside** (a.k.a. lazy loading): the
application itself checks the cache first, and on a miss, fetches from the
origin and populates the cache — as opposed to *read-through*, where the
cache layer itself would be responsible for reaching the origin
transparently.

A few deliberate design decisions:

- **Cache key**: `path + query string` (e.g. `/products?limit=5`), so
  different query strings for the same path are cached independently.
  Only `GET` requests are cached — it's the only safe, idempotent method;
  caching a `POST`/`PUT`/`DELETE` response wouldn't make sense, since
  those requests are meant to actually reach the origin every time.
- **No TTL / expiration.** Entries never go stale on their own — the
  cache is invalidated only manually, via `--clear-cache`. This is also
  why the origin's own `Cache-Control` headers are deliberately ignored:
  this proxy exists specifically to cache more aggressively than the
  origin intends (e.g. `dummyjson.com` sends `Cache-Control: no-store`,
  which a spec-compliant HTTP cache would have to respect — but
  respecting it here would mean caching nothing at all).
- **Concurrent writes to the same key** (two simultaneous misses for the
  same URL) are resolved with an upsert (`INSERT ... ON CONFLICT DO
  UPDATE`) rather than treated as an error — the second write just
  overwrites the first with fresher data instead of failing.

## Prerequisites

- [Docker](https://www.docker.com/) (for Postgres + pgAdmin)
- [uv](https://docs.astral.sh/uv/) (Python package/dependency manager)

## Setup

1. Copy the example environment file and adjust if needed:

   ```sh
   cp .env.example .env
   ```

2. Start Postgres and pgAdmin:

   ```sh
   docker compose up -d
   ```

3. Install dependencies:

   ```sh
   uv sync
   ```

4. Apply database migrations:

   ```sh
   uv run alembic upgrade head
   ```

## Usage

Start the proxy:

```sh
uv run caching-proxy --port 3000 --origin https://dummyjson.com
```

Requests to `http://localhost:3000/...` are forwarded to
`https://dummyjson.com/...`.

```sh
curl -i http://localhost:3000/products/1   # X-Cache: MISS (fetched from origin, then cached)
curl -i http://localhost:3000/products/1   # X-Cache: HIT (served from cache)
```

Clear the cache:

```sh
uv run caching-proxy --clear-cache
```

This can be run independently of the running server — it connects to the
same Postgres database and empties the `cache` table directly.

## Development

### Running tests

Tests run against a separate `caching_proxy_test` database on the same
Postgres instance, so they never touch your dev data.

1. Create the test database once (via `psql` or pgAdmin):

   ```sql
   CREATE DATABASE caching_proxy_test;
   ```

2. Run the suite:

   ```sh
   uv run pytest
   ```

   Migrations are applied to the test database automatically at the start
   of the test session.

Tests hit the real `dummyjson.com` origin rather than mocking it, so they
require network access.

### Linting and type-checking

```sh
uv run ruff check .
uv run pyright
```

### pgAdmin

pgAdmin is available at [http://localhost:5050](http://localhost:5050)
(login from `.env`). Register a new server using host `db`, port `5432`,
and the Postgres credentials from `.env`.
