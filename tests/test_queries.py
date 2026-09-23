import pytest
from sqlalchemy.exc import IntegrityError

from caching_proxy.db.queries import clear, lookup, write


async def test_lookup_returns_none_when_key_not_cached(connection):
    result = await lookup(connection, "/nonexistent?")

    assert result is None


async def test_lookup_returns_cached_row_on_hit(connection):
    await write(
        connection,
        cache_key="/products/1?",
        status_code=200,
        headers={"content-type": "application/json"},
        body=b'{"id": 1}',
    )

    result = await lookup(connection, "/products/1?")

    assert result is not None
    assert result.status_code == 200
    assert result.headers == {"content-type": "application/json"}
    assert result.body == b'{"id": 1}'


async def test_write_overwrites_existing_entry_on_conflict(connection):
    await write(
        connection,
        cache_key="/products/1?",
        status_code=200,
        headers={"content-type": "application/json"},
        body=b'{"id": 1}',
    )
    await write(
        connection,
        cache_key="/products/1?",
        status_code=404,
        headers={"content-type": "text/plain"},
        body=b"not found",
    )

    result = await lookup(connection, "/products/1?")

    assert result is not None
    assert result.status_code == 404
    assert result.headers == {"content-type": "text/plain"}
    assert result.body == b"not found"


async def test_write_rejects_out_of_range_status_code(connection):
    with pytest.raises(IntegrityError):
        await write(
            connection,
            cache_key="/products/1?",
            status_code=999,
            headers={},
            body=b"",
        )


async def test_clear_removes_all_entries(connection):
    await write(
        connection,
        cache_key="/products/1?",
        status_code=200,
        headers={},
        body=b"{}",
    )

    await clear(connection)

    result = await lookup(connection, "/products/1?")

    assert result is None
