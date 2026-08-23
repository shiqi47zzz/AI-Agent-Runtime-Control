import argparse
import asyncio
import statistics
import time
from collections import Counter
from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    target_url: str
    requests: int = 50
    concurrency: int = 10
    retries: int = 0
    timeout_seconds: float = 30.0
    agent_id: str = "simulated-agent"


@dataclass(frozen=True, slots=True)
class Attempt:
    request_id: int
    attempt: int
    status_code: int | None
    latency_ms: float
    error: str | None = None


async def run_simulation(
    config: SimulationConfig,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[Attempt]:
    """Send a bounded concurrent workload to the guard."""
    if config.requests < 1 or config.concurrency < 1 or config.retries < 0:
        raise ValueError("requests and concurrency must be positive; retries cannot be negative")

    semaphore = asyncio.Semaphore(config.concurrency)
    attempts: list[Attempt] = []

    async with httpx.AsyncClient(timeout=config.timeout_seconds, transport=transport) as client:

        async def send(request_id: int) -> None:
            for attempt_number in range(config.retries + 1):
                started = time.perf_counter()
                try:
                    async with semaphore:
                        response = await client.post(
                            config.target_url,
                            headers={"X-Agent-ID": config.agent_id},
                            json={
                                "agent_id": config.agent_id,
                                "request_id": request_id,
                                "tool": "simulated_backend_call",
                                "arguments": {"value": request_id},
                            },
                        )
                    attempts.append(
                        Attempt(
                            request_id=request_id,
                            attempt=attempt_number + 1,
                            status_code=response.status_code,
                            latency_ms=(time.perf_counter() - started) * 1000,
                        )
                    )
                    if response.status_code != 429 or attempt_number == config.retries:
                        return

                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.1 * (2**attempt_number)
                    await asyncio.sleep(min(delay, 5.0))
                except (httpx.HTTPError, ValueError) as error:
                    attempts.append(
                        Attempt(
                            request_id=request_id,
                            attempt=attempt_number + 1,
                            status_code=None,
                            latency_ms=(time.perf_counter() - started) * 1000,
                            error=str(error),
                        )
                    )
                    return

        await asyncio.gather(*(send(request_id) for request_id in range(1, config.requests + 1)))

    return attempts


def format_summary(config: SimulationConfig, attempts: list[Attempt], elapsed: float) -> str:
    statuses = Counter(
        str(attempt.status_code) if attempt.status_code is not None else "network_error"
        for attempt in attempts
    )
    latencies = [attempt.latency_ms for attempt in attempts]
    sorted_latencies = sorted(latencies)
    p95_index = max(0, round(0.95 * len(sorted_latencies)) - 1)
    attempt_rate = f"{len(attempts) / elapsed:.1f}/s" if elapsed else "n/a"

    lines = [
        "AI agent simulation complete",
        f"  Target:          {config.target_url}",
        f"  Logical calls:   {config.requests}",
        f"  HTTP attempts:   {len(attempts)}",
        f"  Concurrency:     {config.concurrency}",
        f"  Elapsed:         {elapsed:.2f}s",
        f"  Attempt rate:    {attempt_rate}",
        f"  Statuses:        {dict(sorted(statuses.items()))}",
        f"  Median latency:  {statistics.median(latencies):.1f}ms",
        f"  P95 latency:     {sorted_latencies[p95_index]:.1f}ms",
    ]
    return "\n".join(lines)


def parse_args() -> SimulationConfig:
    parser = argparse.ArgumentParser(description="Send simulated AI-agent calls to the guard")
    parser.add_argument("--url", required=True, help="Guard endpoint, e.g. http://localhost:8080/v1/tools")
    parser.add_argument("--requests", type=int, default=50, help="Number of logical agent calls")
    parser.add_argument("--concurrency", type=int, default=10, help="Maximum simultaneous calls")
    parser.add_argument("--retries", type=int, default=0, help="Retries per call after HTTP 429")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    parser.add_argument("--agent-id", default="simulated-agent", help="Value for X-Agent-ID")
    args = parser.parse_args()
    return SimulationConfig(
        target_url=args.url,
        requests=args.requests,
        concurrency=args.concurrency,
        retries=args.retries,
        timeout_seconds=args.timeout,
        agent_id=args.agent_id,
    )


def main() -> None:
    config = parse_args()
    started = time.perf_counter()
    attempts = asyncio.run(run_simulation(config))
    print(format_summary(config, attempts, time.perf_counter() - started))


if __name__ == "__main__":
    main()
