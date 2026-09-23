from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

from caching_proxy.db.engine import get_engine
from caching_proxy.db.queries import lookup, write


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.http_client.aclose()


app = FastAPI(lifespan=lifespan)

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "upgrade",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "date",
    "server",
}

# httpx transparently decompresses the response body, so these two headers
# from the origin no longer describe what we're actually sending back.
STALE_AFTER_DECOMPRESSION_HEADERS = {
    "content-length",
    "content-encoding",
}


async def forward_to_origin(request: Request, full_path: str) -> httpx.Response:
    headers = dict(request.headers)
    headers.pop("host", None)
    return await request.app.state.http_client.request(
        method=request.method,
        url=f"{request.app.state.origin}/{full_path}",
        params=request.query_params,
        headers=headers,
        content=await request.body(),
    )


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_handler(full_path: str, request: Request):
    if request.method == "GET":
        cache_key = f"{request.url.path}?{request.query_params}"
        engine = get_engine()
        async with engine.connect() as connection:
            cached = await lookup(connection, cache_key)
            if cached is not None:
                response_headers = {**cached.headers, "X-Cache": "HIT"}
                response = Response(
                    content=cached.body,
                    status_code=cached.status_code,
                    headers=response_headers,
                )
                return response
            else:
                response = await forward_to_origin(request=request, full_path=full_path)
                response_headers = {
                    key: value
                    for key, value in response.headers.items()
                    if key.lower() not in HOP_BY_HOP_HEADERS
                    and key.lower() not in STALE_AFTER_DECOMPRESSION_HEADERS
                }
                await write(
                    connection=connection,
                    cache_key=cache_key,
                    status_code=response.status_code,
                    headers=response_headers,
                    body=response.content,
                )
                response_headers["X-Cache"] = "MISS"
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response_headers,
                )
    else:
        response = await forward_to_origin(request=request, full_path=full_path)
        response_headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
            and key.lower() not in STALE_AFTER_DECOMPRESSION_HEADERS
        }
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
        )


def run_server(port: int, origin: str) -> None:
    app.state.origin = origin
    uvicorn.run(app, host="0.0.0.0", port=port)
