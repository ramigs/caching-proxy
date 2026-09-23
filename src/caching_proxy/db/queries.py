from sqlalchemy import Row, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from caching_proxy.db.schema import cache_table


async def lookup(
    connection: AsyncConnection,
    cache_key: str,
) -> Row | None:
    stmt = select(cache_table).where(cache_table.c.cache_key == cache_key)
    result = await connection.execute(stmt)
    return result.first()


async def write(
    connection: AsyncConnection,
    cache_key: str,
    status_code: int,
    headers: dict,
    body: bytes,
) -> None:
    stmt = pg_insert(cache_table).values(
        cache_key=cache_key,
        status_code=status_code,
        headers=headers,
        body=body,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["cache_key"],
        set_={
            "status_code": stmt.excluded.status_code,
            "headers": stmt.excluded.headers,
            "body": stmt.excluded.body,
            "created_at": stmt.excluded.created_at,
        },
    )
    await connection.execute(stmt)
    await connection.commit()


async def clear(connection: AsyncConnection) -> None:
    await connection.execute(text(f"TRUNCATE TABLE {cache_table.name}"))
    await connection.commit()
