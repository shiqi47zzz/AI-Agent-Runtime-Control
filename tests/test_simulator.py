import httpx
import pytest

from agent_api_guard.simulator import SimulationConfig, run_simulation


@pytest.mark.asyncio
async def test_simulator_sends_agent_calls_and_retries_429() -> None:
    calls: list[httpx.Request] = []

    def guard(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200)

    attempts = await run_simulation(
        SimulationConfig(
            target_url="http://guard.test/v1/tools",
            requests=1,
            concurrency=1,
            retries=1,
            agent_id="test-agent",
        ),
        transport=httpx.MockTransport(guard),
    )

    assert [attempt.status_code for attempt in attempts] == [429, 200]
    assert len(calls) == 2
    assert calls[0].headers["X-Agent-ID"] == "test-agent"
