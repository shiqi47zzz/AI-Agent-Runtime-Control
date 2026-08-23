from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from .config import Settings
from .controls import AdmissionControl, CapacityRejected, ConcurrencyLimit
from .transports import HttpxTransport, UpstreamTransport, UpstreamUnavailable


def create_app(
    settings: Settings | None = None,
    control: AdmissionControl | None = None,
    transport: UpstreamTransport | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    resolved_control = control or ConcurrencyLimit(resolved_settings.max_in_flight)
    resolved_transport = transport or HttpxTransport(
        upstream_url=resolved_settings.upstream_url,
        timeout_seconds=resolved_settings.upstream_timeout_seconds,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        async with resolved_transport.lifecycle():
            yield

    application = FastAPI(title="Agent API Guard", version="0.1.0", lifespan=lifespan)

    @application.get("/healthz", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/readyz", include_in_schema=False)
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @application.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def proxy(request: Request) -> Response:
        try:
            async with resolved_control.admission(request):
                return await resolved_transport.forward(request)
        except CapacityRejected:
            return JSONResponse(
                status_code=429,
                content={"error": "upstream capacity limit reached"},
                headers={"Retry-After": "1"},
            )
        except UpstreamUnavailable:
            return JSONResponse(status_code=502, content={"error": "upstream unavailable"})

    return application


app = create_app()
