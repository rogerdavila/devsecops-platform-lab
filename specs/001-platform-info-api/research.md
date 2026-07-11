# Phase 0 Research: Platform Info API

No `NEEDS CLARIFICATION` markers remained in the Technical Context after drafting — the stack was already largely fixed by `CLAUDE.md`. This document resolves the implementation-level decisions that were genuinely open, so Phase 1 design has a solid foundation.

## Decision: Two ASGI apps, two concurrent Uvicorn servers, one process

**Rationale**: FastAPI/Starlette does not natively bind a single app to two ports with different route sets and different network exposure. The three realistic options were evaluated below. Running two independent FastAPI apps (`public.py`, `internal.py`) inside one process via `asyncio.gather` on two `uvicorn.Server` instances keeps the deployment as a single container/process (simplest Kubernetes Deployment, one process to health-check and one image to scan) while still giving each port its own route table, so `/health`/`/ready` and `/info`/`/metrics` never share code paths (FR-007 requires them not to share an access path).

**Alternatives considered**:

- *Single FastAPI app, single port, path-based access control* — rejected: violates FR-007 (metadata/metrics would share an access path with health checks) and makes the NetworkPolicy port-based block impossible, since there'd be only one port to allow or deny.
- *Two separate containers/processes in the same Pod* — rejected as unnecessary complexity for this scale; two ports from one process is a well-established pattern (e.g., how many Go services expose `:8080` app traffic and `:9090` metrics) and avoids a second container image, a second set of resource limits, and inter-container coordination for shared config (version/build id).

## Decision: `prometheus-client` for `/metrics`

**Rationale**: CLAUDE.md already commits to "Prometheus-format metrics." `prometheus-client` is the reference Python implementation of the Prometheus exposition format, actively maintained, and integrates cleanly as a plain ASGI/WSGI-mountable endpoint without pulling in a full auto-instrumentation framework we don't need yet (OpenTelemetry is explicitly Phase 2 per `PROGRESS.md`).

**Alternatives considered**: `prometheus-fastapi-instrumentator` (auto-instruments all routes) — rejected for now because it would auto-expose metrics for the public app too, which is out of scope; we want the four specific metrics from the clarified FR-005 (request count, latency, error rate, uptime), not a wall of auto-generated ones.

## Decision: App-level "trusted internal network" check = RFC1918 private-range source IP allowlist

**Rationale**: The Clarification session fixed defense-in-depth: NetworkPolicy (network layer) *and* an app-level check (application layer). NetworkPolicy already guarantees only in-cluster traffic reaches port 9090, so the app-level check does not need to reproduce that guarantee — it needs to be a cheap, dependency-free second layer that fails closed if NetworkPolicy is ever misconfigured or bypassed (e.g., an accidental `LoadBalancer` Service). Checking that the request's source IP falls within RFC1918 private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) — which covers k3d's default pod/service CIDRs — is a standard, low-maintenance "belt" to NetworkPolicy's "suspenders." It requires no shared secret, no extra infrastructure, and no cluster-specific hardcoded CIDR.

**Alternatives considered**:

- *Shared-secret header injected by a trusted proxy* — rejected: adds a secret to manage and rotate for a lab-scale defense-in-depth check; disproportionate to the risk being mitigated.
- *Hardcoding the exact k3d pod CIDR* — rejected: couples the app to one cluster's specific network config, breaking Principle VII (real, portable patterns) the moment the cluster CIDR changes.

## Decision: Graceful shutdown via Uvicorn's SIGTERM handling + FastAPI lifespan shutdown hook

**Rationale**: Uvicorn already installs a SIGTERM handler that stops accepting new connections and lets in-flight requests finish (`timeout_graceful_shutdown`). Wiring a FastAPI lifespan `shutdown` event to flip an in-memory `ready = False` flag the instant SIGTERM arrives gives the exact behavior clarified: readiness flips immediately, liveness stays healthy through the drain window, and Kubernetes' own termination grace period (default 30s) governs how long the drain is allowed to run.

**Alternatives considered**: A custom signal handler bypassing Uvicorn's — rejected as reinventing something Uvicorn already does correctly and safely.

## Decision: `python:3.13-slim` base image

**Rationale**: Smaller attack surface and fewer packages for Trivy to flag than the full `python:3.13` image, without the added toolchain complexity of a fully distroless image (no shell at all) at this stage of the project. Consistent with Constitution Principle I (security at every layer) balanced against Principle VI (understand before you use) — a fully distroless build can be a documented Phase 2/3 hardening step once the team is comfortable debugging it.

**Alternatives considered**: `python:3.13` (full) — rejected, larger surface with no benefit. Distroless — deferred, not rejected outright; worth revisiting once the base pipeline is stable.
