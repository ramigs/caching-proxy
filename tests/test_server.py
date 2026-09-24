from caching_proxy.server import HOP_BY_HOP_HEADERS


async def test_health_check_is_answered_directly_not_proxied(client):
    response = await client.get("/__health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "x-cache" not in response.headers


async def test_get_request_is_a_cache_miss_the_first_time(client):
    response = await client.get("/products/1")

    assert response.status_code == 200
    assert response.headers["x-cache"] == "MISS"


async def test_get_request_is_a_cache_hit_the_second_time(client):
    await client.get("/products/1")

    response = await client.get("/products/1")

    assert response.status_code == 200
    assert response.headers["x-cache"] == "HIT"


async def test_query_string_is_part_of_the_cache_key(client):
    response_a = await client.get("/products", params={"limit": "1"})
    response_b = await client.get("/products", params={"limit": "2"})
    response_a_again = await client.get("/products", params={"limit": "1"})

    assert response_a.headers["x-cache"] == "MISS"
    assert response_b.headers["x-cache"] == "MISS"
    assert response_a_again.headers["x-cache"] == "HIT"


async def test_non_get_request_is_forwarded_without_caching(client):
    response = await client.post(
        "/products/add",
        json={"title": "test product"},
    )

    assert response.status_code == 201
    assert "x-cache" not in response.headers


async def test_response_excludes_hop_by_hop_and_content_encoding_headers(client):
    response = await client.get("/products/1")

    for header in HOP_BY_HOP_HEADERS | {"content-encoding"}:
        assert header not in response.headers


async def test_response_content_length_matches_actual_body_size(client):
    response = await client.get("/products/1")

    assert int(response.headers["content-length"]) == len(response.content)
