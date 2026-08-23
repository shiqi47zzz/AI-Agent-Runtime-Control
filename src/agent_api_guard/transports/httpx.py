from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

import httpx
from fastapi import Request, Response

from .base import UpstreamTransport, UpstreamUnavailable

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


class HttpxTransport(UpstreamTransport):
    """HTTP transport backed by one shared httpx connection pool."""

    def __init__(
        self,
        upstream_url: str,
        timeout_seconds: float,
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._upstream_url = upstream_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._http_transport = http_transport
        self._client: httpx.AsyncClient | None = None

    @asynccontextmanager
    async def lifecycle(self) -> AsyncIterator[None]:
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._http_transport,
        ) as client:
            self._client = client
            try:
                yield
            finally:
                self._client = None

    async def forward(self, request: Request) -> Response:
        if self._client is None:
            raise RuntimeError("transport is not running")

        path = request.path_params.get("path", "")
        try:
            upstream = await self._client.request(
                method=request.method,
                url=f"{self._upstream_url}/{path}",
                params=request.query_params,
                headers=_forwarded_headers(request.headers),
                content=await request.body(),
            )
        except httpx.HTTPError as error:
            raise UpstreamUnavailable from error

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=_forwarded_headers(upstream.headers),
        )


def _forwarded_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }
