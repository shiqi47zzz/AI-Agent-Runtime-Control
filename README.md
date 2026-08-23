# Agent API Guard

A minimal Python control layer that protects backend APIs from bursty and highly
parallel AI-agent traffic. It can run in front of an API gateway upstream or as
a standalone sidecar/microservice.

The first control is deliberately small: excess concurrent requests are rejected
with HTTP `429` before they consume backend capacity. The control is behind a
plugin interface so rate limits, cost budgets, circuit breakers, and distributed
coordination can be added without changing the proxy.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
make install
UPSTREAM_URL=http://localhost:9000 MAX_IN_FLIGHT=20 make run
```

Send protected traffic to `http://localhost:8080`. Operational endpoints are
`GET /healthz` and `GET /readyz`.

## Simulate AI-agent traffic

With the guard and a backend running, send 100 tool-style calls with up to 25
calls in flight:

```bash
agent-simulator \
  --url http://localhost:8080/v1/tools \
  --requests 100 \
  --concurrency 25
```

To model an agent that retries rejected calls, add `--retries 2`. The simulator
honors the guard's `Retry-After` header, caps each wait at five seconds, and
prints status counts and latency statistics. Use only against systems you own or
are authorized to test.

## Configuration

| Environment variable | Default | Description |
|---|---:|---|
| `UPSTREAM_URL` | `http://localhost:9000` | Absolute HTTP(S) backend URL |
| `MAX_IN_FLIGHT` | `20` | Maximum concurrent upstream calls per instance |
| `UPSTREAM_TIMEOUT_SECONDS` | `30` | Upstream request timeout |

## Structure

```text
src/agent_api_guard/
  app.py             FastAPI lifecycle and routes
  config.py          environment configuration
  simulator.py       bounded AI-agent traffic simulator
  controls/
    base.py          plugin contract
    concurrency.py   initial capacity policy
  transports/
    base.py          upstream transport plugin contract
    httpx.py         shared HTTP client and reverse-proxy transport
tests/               policy and endpoint tests
```

This is a single-instance foundation. A production follow-up should define agent
identity/tenant keys, trusted authentication headers, distributed state, metrics,
and retry/circuit-breaker semantics.
