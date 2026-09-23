import os

import httpx
import pytest
from alembic import command
from alembic.config import Config

from caching_proxy.db.engine import get_engine
from caching_proxy.db.queries import clear
from caching_proxy.server import app


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    os.environ["POSTGRES_DB"] = "caching_proxy_test"
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@pytest.fixture
async def connection():
    engine = get_engine()
    async with engine.connect() as connection:
        await clear(connection)
        yield connection


@pytest.fixture
async def client():
    engine = get_engine()
    async with engine.connect() as connection:
        await clear(connection)

    app.state.origin = "https://dummyjson.com"
    async with httpx.AsyncClient() as origin_client:
        app.state.http_client = origin_client
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as test_client:
            yield test_client
