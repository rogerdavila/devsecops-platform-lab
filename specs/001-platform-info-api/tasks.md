# Tasks: Platform Info API

**Input**: Design documents from `/specs/001-platform-info-api/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml, quickstart.md

**Tests**: Included — required by CI pipeline gates (unit tests + integration tests are non-optional pipeline gates per constitution Quality Gates table and CLAUDE.md).

**Organization**: Tasks grouped by user story. US1 is independently deployable as MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to
- All file paths relative to repo root

---

## Phase 1: Setup

**Purpose**: Project directory structure, dependency manifest, developer tooling.

- [x] T001 Create app/ directory tree: `app/src/apps/`, `app/src/core/`, `app/src/models/`, `app/tests/unit/`, `app/tests/integration/` with `__init__.py` stubs
- [x] T002 Create `app/requirements.txt` with pinned versions: fastapi, uvicorn[standard], prometheus-client, pydantic-settings, httpx, pytest, pytest-cov, pytest-asyncio
- [x] T003 [P] Create `.pre-commit-config.yaml` with hooks: black (formatter), ruff (linter), bandit (SAST), detect-secrets (secret scanning), hadolint (Dockerfile linter)
- [x] T004 [P] Initialize detect-secrets baseline at `.secrets.baseline` via `detect-secrets scan > .secrets.baseline`

**Checkpoint**: Project skeleton ready. Pre-commit hooks installable via `pre-commit install`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on. No US work begins until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `app/src/core/config.py` — Pydantic `BaseSettings` reading `VERSION`, `ENVIRONMENT` (enum: dev/staging/prod), `BUILD_ID` from environment variables; defaults to dev/unknown for local runs
- [x] T006 Create `app/src/core/lifecycle.py` — in-memory startup state (`_started: bool`, `_draining: bool`); `startup_complete()` sets started; SIGTERM handler sets draining immediately (readiness flips to False, liveness unaffected) per clarified edge case (2026-07-05)
- [x] T007 Create `app/src/core/network_guard.py` — FastAPI dependency that reads client host from request, validates it falls within RFC1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), raises `HTTPException(403)` for any non-private source IP
- [x] T008 Create `app/src/models/health.py` — Pydantic response models matching `contracts/api.yaml`: `HealthStatus(alive: bool, checked_at: datetime)`, `ReadinessStatus(ready: bool, checked_at: datetime)`, `ServiceMetadata(version: str, environment: str, build_id: str)`
- [x] T009 Create `app/src/main.py` — entrypoint using `asyncio.gather` to run two concurrent `uvicorn.Server` instances: public app on `:8080`, internal app on `:9090`; wires SIGTERM to lifecycle handler
- [x] T010 Create `app/Dockerfile` — base `python:3.13-slim`, creates non-root user `appuser`, copies `requirements.txt` + `app/src/`, installs deps, `EXPOSE 8080 9090`, `USER appuser`, `CMD ["python", "src/main.py"]`

**Checkpoint**: Foundation complete. Core config, lifecycle, network guard, models, entrypoint, and container image build target all in place.

---

## Phase 3: User Story 1 — Orchestrator checks service health (Priority: P1) 🎯 MVP

**Goal**: Public port `:8080` serves `/health` (liveness) and `/ready` (readiness) with correct state transitions including SIGTERM drain behavior.

**Independent Test**: Start service locally, `curl http://localhost:8080/health` → 200 alive; `curl http://localhost:8080/ready` → 503 before startup completes, 200 after; `kill -TERM <pid>` → /ready immediately 503, /health still 200.

### Implementation for User Story 1

- [ ] T011 [US1] Create `app/src/apps/public.py` — FastAPI app with `GET /health` returning `HealthStatus(alive=True, checked_at=now)` always 200; `GET /ready` returning `ReadinessStatus` with 200 when lifecycle is started and not draining, 503 otherwise

### Tests for User Story 1

- [ ] T012 [P] [US1] Write unit tests for `/health` endpoint in `app/tests/unit/test_health.py` — always returns 200 with `alive=True` and `checked_at` in ISO 8601 format regardless of lifecycle state
- [ ] T013 [P] [US1] Write unit tests for `/ready` endpoint and lifecycle state in `app/tests/unit/test_ready.py` — 503 before startup, 200 after startup, 503 immediately on SIGTERM drain, 200 during drain on `/health`
- [ ] T014 [US1] Write integration tests for US1 in `app/tests/integration/test_health_ready.py` — starts service process, validates `/health` 200 JSON schema matches `contracts/api.yaml`, validates `/ready` 200/503 transitions (depends on T011, T012, T013)

**Checkpoint**: User Story 1 complete. Orchestrator can determine health/readiness. SC-001 verifiable (< 1s response).

---

## Phase 4: User Story 2 — Operator inspects service metadata (Priority: P2)

**Goal**: Internal port `:9090` serves `/info` returning version/environment/build_id; callers outside trusted network receive 403 (application-layer check, FR-006).

**Independent Test**: `curl http://localhost:9090/info` → 200 with version/environment/build_id fields; spoof non-RFC1918 source → 403 regardless of NetworkPolicy.

### Implementation for User Story 2

- [ ] T015 [US2] Create `app/src/apps/internal.py` — FastAPI app with `GET /info` using `network_guard` as FastAPI dependency, returns `ServiceMetadata` from `config`; applies `network_guard` at app middleware level so all routes on port 9090 are protected

### Tests for User Story 2

- [ ] T016 [P] [US2] Write unit tests for `network_guard.py` in `app/tests/unit/test_network_guard.py` — RFC1918 source IPs (10.x, 172.16.x, 192.168.x) are allowed; public IPs (1.2.3.4, 8.8.8.8) raise 403; edge cases: loopback 127.0.0.1 allowed
- [ ] T017 [P] [US2] Write unit tests for `/info` endpoint in `app/tests/unit/test_info.py` — returns 200 with correct `version`/`environment`/`build_id` from config; non-internal caller receives 403
- [ ] T018 [US2] Write integration tests for US2 in `app/tests/integration/test_info.py` — starts service, hits `/info` from localhost (RFC1918), validates all three `ServiceMetadata` fields present and non-empty, validates schema matches `contracts/api.yaml` (depends on T015, T016, T017)

**Checkpoint**: User Story 2 complete. Operators can identify running version/build. SC-002 and SC-004 verifiable.

---

## Phase 5: User Story 3 — Monitoring system collects metrics (Priority: P3)

**Goal**: Internal port `:9090` serves `/metrics` in Prometheus text exposition format with the four required metric families; callers outside trusted network receive 403.

**Independent Test**: `curl http://localhost:9090/metrics` → 200 text/plain containing `http_requests_total`, `http_request_duration_seconds`, `http_requests_errors_total`, `process_uptime_seconds`.

### Implementation for User Story 3

- [ ] T019 [US3] Add `GET /metrics` route and Prometheus instrumentation middleware to `app/src/apps/internal.py` — register four metric families per `data-model.md` (Counter `http_requests_total{method,path,status}`, Histogram `http_request_duration_seconds{method,path}`, Counter `http_requests_errors_total{method,path,status}`, Gauge `process_uptime_seconds`); serve `prometheus_client.generate_latest()` as `text/plain`; protected by existing `network_guard` middleware (depends on T015)

### Tests for User Story 3

- [ ] T020 [P] [US3] Write unit tests for metrics registration in `app/tests/unit/test_metrics.py` — all four metric family names present in registry; after a request, `http_requests_total` count increments; error requests increment `http_requests_errors_total`; `process_uptime_seconds` is non-negative
- [ ] T021 [US3] Write integration tests for US3 in `app/tests/integration/test_metrics.py` — starts service, scrapes `/metrics`, parses Prometheus text format, validates all four metric names present; sends a request first to ensure counters are non-zero; validates `/metrics` returns 403 when caller IP is non-RFC1918 (depends on T019, T020)

**Checkpoint**: All three user stories complete. Full feature functional and testable end-to-end.

---

## Phase 6: CI/CD Pipeline

**Purpose**: GitHub Actions pipeline enforcing all Quality Gates from the constitution before any image reaches the registry.

- [ ] T022 Create `.github/workflows/ci.yml` — sequential jobs: (1) lint-format: `black --check` + `ruff check`; (2) sast: Semgrep with `p/python`; (3) sca: `pip-audit` fail on HIGH+; (4) test: `pytest --cov=app/src --cov-fail-under=80`; (5) build: `docker build`; (6) scan: Trivy image scan fail on CRITICAL; (7) sbom: Trivy `--format cyclonedx` output to `sbom.json`; (8) integration: run container + hit `/health`, `/ready`, `/info`, `/metrics`; (9) push: GHCR push only on `main` branch after all gates pass
- [ ] T023 [P] Create `.hadolint.yaml` at repo root with project-specific ignore rules if needed (e.g., `DL3008` for apt pin — document rationale inline per Principle VI)

**Checkpoint**: CI pipeline enforces all constitution Quality Gates. No image reaches GHCR without passing every gate.

---

## Phase 7: Kubernetes & GitOps

**Purpose**: Kubernetes manifests enabling ArgoCD to deploy the service to the k3d cluster. Feature is not complete until deployed (Constitution Principle III).

- [ ] T024 Create `k8s/base/deployment.yaml` — Deployment with `livenessProbe` HTTP GET `/health` on `:8080` (initialDelaySeconds: 5, periodSeconds: 10), `readinessProbe` HTTP GET `/ready` on `:8080` (initialDelaySeconds: 5, periodSeconds: 5, failureThreshold: 3); `env` sourcing `VERSION`, `ENVIRONMENT`, `BUILD_ID` from ConfigMap or Deployment env block; image tag placeholder for Kustomize overlay
- [ ] T025 [P] Create `k8s/base/service.yaml` — two `ClusterIP` Services: `platform-info-public` on port 8080, `platform-info-internal` on port 9090 (internal ClusterIP only, no external exposure)
- [ ] T026 [P] Create `k8s/base/networkpolicy.yaml` — allow all ingress to `:8080`; allow ingress to `:9090` only from pods in `monitoring` namespace (Prometheus scrape); deny all other ingress to `:9090` (FR-006 network layer)
- [ ] T027 Create `k8s/base/kustomization.yaml` — lists resources: `deployment.yaml`, `service.yaml`, `networkpolicy.yaml`
- [ ] T028 Create `k8s/overlays/local/kustomization.yaml` — Kustomize overlay for k3d; sets image to local registry (`k3d-registry.localhost:5000/platform-info-api:latest`) and sets `ENVIRONMENT=dev`
- [ ] T029 Create `k8s/argocd/platform-info-app.yaml` — ArgoCD `Application` manifest pointing to `k8s/overlays/local/`, sync policy `automated` with `selfHeal: true`, targeting the local k3d cluster

**Checkpoint**: Cluster state managed by ArgoCD. Any commit to `k8s/` triggers reconciliation.

---

## Phase 8: Polish & Validation

**Purpose**: End-to-end validation that all success criteria are met, pre-commit passes cleanly, and PROGRESS.md reflects the final state.

- [ ] T030 [P] Run `pre-commit run --all-files` on the full repo and resolve any findings — ensures black/ruff/bandit/detect-secrets/hadolint all pass before PR
- [ ] T031 Execute the full `quickstart.md` validation end-to-end on a running k3d cluster: SC-001 (health < 1s), SC-002 (100% unauthorized internal requests refused), SC-003 (metrics collectible on every scrape), SC-004 (version/build identifiable from `/info` alone)
- [ ] T032 [P] Update `PROGRESS.md` — mark `001-platform-info-api` complete, advance SDD checklist to next phase, document any deferred items

**Checkpoint**: Feature complete. All pipeline gates green. All success criteria verified. Deployed via GitOps.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user story phases
- **Phase 3 (US1)**: Depends on Phase 2 — MVP deliverable, no dependency on US2/US3
- **Phase 4 (US2)**: Depends on Phase 2 — no dependency on US1 (shares `internal.py` file, so serialize after US1 in practice)
- **Phase 5 (US3)**: Depends on Phase 4 (T019 extends `internal.py` created in T015)
- **Phase 6 (CI/CD)**: Can be drafted in parallel with Phase 3; requires working tests to validate
- **Phase 7 (K8s)**: Can be drafted in parallel with Phase 3; requires built image to deploy
- **Phase 8 (Polish)**: Depends on all prior phases complete

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — no dependency on US2/US3
- **US2 (P2)**: Starts after Phase 2 — serialized with US1 due to shared `internal.py`
- **US3 (P3)**: Starts after US2 complete (T015 must exist before T019 can extend it)

### Within Each User Story

- Foundational models/core → App route implementation → Unit tests (can overlap) → Integration test (requires implementation complete)
- Tests marked [P] within a story can run in parallel (different files, no shared state)

### Parallel Opportunities

- T003 and T004 (Phase 1): both setup tasks, different files
- T012 and T013 (US1 tests): different test files, no shared state
- T016 and T017 (US2 tests): different test files
- T025 and T026 (K8s): different manifest files
- T023, T025, T026, T030, T032 all parallelizable within their phases

---

## Parallel Example: User Story 1

```bash
# After T011 (public.py) is complete, launch in parallel:
Task T012: unit tests for /health → app/tests/unit/test_health.py
Task T013: unit tests for /ready + lifecycle → app/tests/unit/test_ready.py
# Then sequentially:
Task T014: integration tests → app/tests/integration/test_health_ready.py
```

---

## Implementation Strategy

### MVP (User Story 1 only — T001–T014)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T010) — **blocks everything**
3. Complete Phase 3: US1 (T011–T014)
4. **STOP and VALIDATE**: `/health` and `/ready` work, tests pass, CI runs clean
5. Ship US1 as a verified, independently deployable increment

### Incremental Delivery

1. Phases 1–2 → Foundation ready
2. Phase 3 (US1) → MVP: orchestrator health checks working → validate → deploy
3. Phase 4 (US2) → Operator metadata working → validate → deploy
4. Phase 5 (US3) → Monitoring metrics working → validate → deploy
5. Phases 6–7 → Pipeline + cluster wired → GitOps live
6. Phase 8 → End-to-end validation, done

---

## Notes

- [P] tasks = different files, no incomplete shared dependencies — safe to run concurrently
- [Story] label traces each task to the user story it delivers value for
- Each user story is independently completable and testable as a vertical slice
- Commit after each task or logical group; commit messages must reference task ID (e.g., `feat(T011): add public FastAPI app with /health and /ready`)
- Stop at each **Checkpoint** to validate the story independently before moving forward
- The feature is not complete until T031 (quickstart.md validation) passes on the live cluster — per Constitution Principle III
