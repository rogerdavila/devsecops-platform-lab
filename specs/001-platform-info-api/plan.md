# Implementation Plan: Platform Info API

**Branch**: `001-platform-info-api` | **Date**: 2026-07-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-platform-info-api/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

A FastAPI microservice exposing Kubernetes-standard liveness/readiness on a public port (8080) and service metadata/Prometheus metrics on an internal-only port (9090). The internal port is protected by defense-in-depth: a Kubernetes NetworkPolicy at the network layer, plus an application-level private-network check (clarified 2026-07-05). No external dependency exists yet — readiness reflects a minimal internal startup check, deliberately deferring real dependency wiring. The feature is complete only once it is built, containerized, scanned, and deployed to the local k3d cluster via ArgoCD (Constitution Principle III).

## Technical Context

**Language/Version**: Python 3.13 — latest stable CPython at time of writing; no legacy constraint exists in this greenfield project, so we take the current stable release.

**Primary Dependencies**: FastAPI (web framework, per CLAUDE.md), Uvicorn (ASGI server), `prometheus-client` (Prometheus exposition format for `/metrics`), Pydantic (response models, ships with FastAPI).

**Storage**: N/A — no persistence. Confirmed out of scope in `/speckit-clarify` (2026-07-05).

**Testing**: pytest + pytest-cov (per CLAUDE.md pipeline description), httpx (async test client for FastAPI).

**Target Platform**: Linux container (Docker), deployed to a local k3d-managed Kubernetes cluster.

**Project Type**: Single web-service microservice (two-port REST API).

**Performance Goals**: p95 < 100ms for `/health` and `/ready` (well inside the <1s ceiling in SC-001 — orchestrators poll frequently, so headroom matters); p95 < 500ms for `/metrics` scrape.

**Constraints**:

- Two-port design: 8080 public (health/ready), 9090 internal-only (info/metrics) — no shared access path (FR-007).
- FR-006 defense-in-depth: NetworkPolicy (network layer) AND an application-level check independently rejecting non-internal callers (application layer).
- No data persistence (out of scope).
- Graceful shutdown: SIGTERM flips readiness to not-ready immediately; liveness stays healthy through a brief drain window (clarified 2026-07-05).

**Scale/Scope**: Lab-scale — 1-2 replicas in a local k3d cluster, no production SLA. Readiness/liveness probes wired the standard way so the pattern is defensible at production scale even though throughput here is trivial (Constitution Principle VII — Real Patterns Only).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance |
| --- | --- |
| I. Security is a First-Class Citizen | PASS — SAST/SCA/image scan/SBOM are pipeline gates (built in later tasks); NetworkPolicy planned for the internal port from the start, not bolted on later. |
| II. Shift-Left on Everything | PASS — pre-commit → CI → cluster scanning gate order unchanged; nothing in this feature skips a gate. |
| III. Finish What You Start | PASS — scope is exactly the 3 user stories in spec.md plus the clarified out-of-scope list; no additions mid-plan. |
| IV. Everything is Code | PASS — Dockerfile, k8s manifests, and CI workflow all version-controlled; no manual cluster steps. |
| V. GitOps as the Deployment Model | PASS — ArgoCD reconciles `k8s/` from this repo; no ad-hoc `kubectl apply` planned. |
| VI. Understand Before You Use | PASS — every dependency choice has documented rationale in `research.md`. |
| VII. Real Patterns Only | PASS — two-port design, defense-in-depth, SBOM, NetworkPolicy are all production patterns, not lab shortcuts. |
| VIII. Documentation is Part of the Deliverable | PASS — this plan, research.md, data-model.md, and quickstart.md are all committed artifacts. |

No violations. Complexity Tracking table below is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-platform-info-api/
├── plan.md          # This file (/speckit-plan command output)
├── research.md       # Phase 0 output (/speckit-plan command)
├── data-model.md      # Phase 1 output (/speckit-plan command)
├── quickstart.md      # Phase 1 output (/speckit-plan command)
├── contracts/         # Phase 1 output (/speckit-plan command)
└── tasks.md           # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
app/
├── src/
│   ├── main.py               # Entrypoint: starts both ASGI servers (public + internal)
│   ├── apps/
│   │   ├── public.py          # FastAPI app for port 8080: /health, /ready
│   │   └── internal.py        # FastAPI app for port 9090: /info, /metrics
│   ├── core/
│   │   ├── config.py          # Env-driven settings: version, environment, build id
│   │   ├── network_guard.py   # App-level trusted-network check (defense-in-depth, FR-006)
│   │   └── lifecycle.py       # Startup check + SIGTERM-driven readiness flip
│   └── models/
│       └── health.py          # Pydantic response models (health, readiness, metadata)
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile
└── requirements.txt

k8s/
├── base/
│   ├── deployment.yaml         # readiness/liveness probes wired to :8080
│   ├── service.yaml            # two Services: public (8080) + internal (9090, ClusterIP)
│   ├── networkpolicy.yaml       # denies external ingress to port 9090
│   └── kustomization.yaml
└── overlays/
    └── local/                  # k3d-specific overlay

.github/workflows/
└── ci.yml                      # lint → SAST → SCA → tests → build → scan → SBOM → push
```

**Structure Decision**: Single microservice, two-port design implemented as two independent FastAPI apps (`apps/public.py`, `apps/internal.py`) served by two concurrent Uvicorn server instances from one process (see `research.md` for why this beats a single app with conditional routing). App code and Kubernetes manifests stay in the same monorepo per the current PROGRESS.md decision (splitting into app + gitops repos is an explicit Phase 2 backlog item, not now).

## Complexity Tracking

> Not applicable — Constitution Check above has no violations.
