# Quickstart: Platform Info API

Validation guide for the feature once implemented. Not implementation instructions — see `tasks.md` (created by `/speckit-tasks`) for that. This proves the contract in `contracts/api.yaml` actually holds.

## Prerequisites

- Python 3.13 and the dependencies in `app/requirements.txt` installed, OR the built Docker image.
- For the NetworkPolicy portion: a running k3d cluster with the service deployed per `k8s/base/`.

## Run locally (no cluster)

```bash
uvicorn app.src.main:app --host 0.0.0.0
```

The entrypoint starts both ASGI servers (public :8080, internal :9090) in one process — see `research.md` for why.

## Validate the public port (User Story 1)

```bash
curl -i http://localhost:8080/health
curl -i http://localhost:8080/ready
```

Expected: `200` with `{"alive": true, ...}` from `/health` immediately after startup. `/ready` returns `503` until the internal startup check completes, then `200`.

## Validate the internal port from an allowed caller (User Story 2 & 3)

```bash
curl -i http://localhost:9090/info
curl -i http://localhost:9090/metrics
```

Expected: `200` with version/environment/build_id from `/info`; `200` with Prometheus text format from `/metrics`, containing at minimum `http_requests_total`, `http_request_duration_seconds`, `http_requests_errors_total`, `process_uptime_seconds`.

## Validate defense-in-depth rejection (FR-006)

Two independent checks must both hold once deployed to the cluster:

1. **Network layer**: from outside the cluster, port 9090 must be unreachable (connection refused/timeout — the NetworkPolicy drops the packet before it reaches the app).
2. **Application layer**: from inside the cluster but simulating a non-private source IP (e.g., a unit/integration test that forges the source), the app itself must return `403`, independent of the NetworkPolicy.

## Validate graceful shutdown (SIGTERM edge case)

```bash
kill -TERM <pid>
curl -i http://localhost:8080/ready   # expect 503 immediately
curl -i http://localhost:8080/health  # expect 200 until the drain window ends
```

## Success criteria mapping

- SC-001 (health check < 1s): time the `/health` and `/ready` calls above; both should be well under the 1s ceiling (target p95 < 100ms per `plan.md`).
- SC-002 (100% of unauthorized internal-port requests refused): both the NetworkPolicy and application-layer checks above must independently reject.
- SC-003 (metrics collectible on every scrape while healthy): repeat the `/metrics` curl multiple times while the service is ready; every call must succeed.
- SC-004 (identify version/build without pipeline access): confirm `/info` alone is sufficient to answer "what build is this."
