import httpx
import pytest

from agent_api_guard.app import create_app
from agent_api_guard.config import Settings


@pytest.mark.asyncio
async def test_health_and_proxy() -> None:
    def upstream(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"path": request.url.path})

    app = create_app(
        Settings("http://backend.test", max_in_flight=1),
        transport=httpx.MockTransport(upstream),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://guard.test"
        ) as client:
            assert (await client.get("/healthz")).json() == {"status": "ok"}
            response = await client.post("/v1/tools?agent=demo", json={"hello": "world"})

    assert response.status_code == 200
    assert response.json() == {"path": "/v1/tools"}
