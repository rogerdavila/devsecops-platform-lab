# Phase 1 Data Model: Platform Info API

Derived from the Key Entities section of `spec.md`, resolved with the Clarifications from 2026-07-05. Nothing here is persisted — all state is in-process, per the "no data persistence" out-of-scope decision.

## Service Health State

Represents current liveness and readiness of the running instance.

| Field | Type | Notes |
| --- | --- | --- |
| `alive` | bool | Always `true` once the process has started; liveness never depends on dependency checks (FR-001). |
| `ready` | bool | `true` only when the internal startup check has completed AND the instance is not in a SIGTERM drain window (FR-002, FR-003). |
| `checked_at` | ISO 8601 timestamp | When the state was last evaluated. |

**Lifecycle / state transitions**:

```text
starting → ready (startup check passes)
ready → draining (SIGTERM received: ready flips to false immediately, alive stays true)
draining → terminated (process exits after in-flight requests complete or grace period expires)
```

There is no path back from `draining` to `ready` — shutdown is one-directional, matching the clarified edge case.

## Service Metadata

Represents identifying information about the running instance (FR-004).

| Field | Type | Notes |
| --- | --- | --- |
| `version` | string | Semver, e.g. `0.1.0`. Sourced from a build-time env var, not hardcoded. |
| `environment` | string (enum) | One of `dev`, `staging`, `prod`. |
| `build_id` | string | CI build identifier (e.g. commit SHA or run number) — enables SC-004 (identify exact build without pipeline access). |

## Operational Metrics

Represents quantitative runtime measurements (FR-005, resolved in Clarifications to four specific metrics).

| Metric name | Prometheus type | Labels | Notes |
| --- | --- | --- | --- |
| `http_requests_total` | Counter | `method`, `path`, `status` | Request count. |
| `http_request_duration_seconds` | Histogram | `method`, `path` | Request latency. |
| `http_requests_errors_total` | Counter | `method`, `path`, `status` | Subset of `http_requests_total` where `status >= 500`; kept separate for direct alerting on error rate. |
| `process_uptime_seconds` | Gauge | none | Seconds since process start. |

## Trusted Network Check (defense-in-depth, FR-006)

Not a persisted entity, but a request-scoped evaluation:

| Input | Rule |
| --- | --- |
| Request source IP | Must fall within an RFC1918 private range (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`). Anything else is rejected before reaching route handlers on the internal app. |
