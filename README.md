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
  proxy.py           upstream reverse proxy
  controls/
    base.py          plugin contract
    concurrency.py   initial capacity policy
tests/               policy and endpoint tests
```

This is a single-instance foundation. A production follow-up should define agent
identity/tenant keys, trusted authentication headers, distributed state, metrics,
and retry/circuit-breaker semantics.
