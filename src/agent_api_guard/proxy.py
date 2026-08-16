from collections.abc import Mapping

import httpx
from fastapi import Request, Response

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def forwarded_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }


async def forward(request: Request, client: httpx.AsyncClient, upstream_url: str) -> Response:
    path = request.path_params.get("path", "")
    url = f"{upstream_url}/{path}"
    upstream = await client.request(
        method=request.method,
        url=url,
        params=request.query_params,
        headers=forwarded_headers(request.headers),
        content=await request.body(),
    )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=forwarded_headers(upstream.headers),
    )
