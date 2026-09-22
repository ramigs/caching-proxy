from functools import cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from caching_proxy.db.config import get_database_url


@cache
def get_engine() -> AsyncEngine:
    return create_async_engine(get_database_url())
