# Progress — devsecops-platform-lab

Current state of the project. Update at the end of every work session.

## Current Phase

**001-platform-info-api: COMPLETE (2026-09-17)**

All 3 user stories implemented, CI/CD pipeline live, deployed to local k3d cluster via ArgoCD, and fully validated end-to-end (T031). Next feature not yet started — see Backlog below for candidates.

## SDD Checklist

- [x] `specify init` — project scaffold created
- [x] `/speckit-constitution` — ratified v1.0.0 (2026-07-02)
- [x] `/speckit-specify` — Platform Info API spec (2026-07-03), all quality checklist items pass, no NEEDS CLARIFICATION
- [x] `/speckit-clarify` — surface assumptions (2026-07-05)
- [x] `/speckit-plan` — tech stack and architecture doc (2026-07-08)
- [x] `/speckit-tasks` — ordered task breakdown (2026-07-13)
- [x] `/speckit-implement` — build phase (2026-07-13 → 2026-09-17, including Phase 9 GitOps promotion fix and live cluster validation)

## What exists so far

| File | Status |
| --- | --- |
| `CLAUDE.md` | Done — technical project context, public-safe |
| `.specify/memory/constitution.md` | Done — 8 principles, v1.0.0 |
| `specs/001-platform-info-api/spec.md` | Done — user stories, FRs, success criteria |
| `specs/001-platform-info-api/plan.md` | Done — tech stack, architecture, project structure |
| `specs/001-platform-info-api/research.md` | Done — 4 key implementation decisions |
| `specs/001-platform-info-api/data-model.md` | Done — entities, metrics, network guard |
| `specs/001-platform-info-api/quickstart.md` | Done — validation guide for all 4 SCs |
| `specs/001-platform-info-api/contracts/api.yaml` | Done — OpenAPI 3.0 contract for all 4 endpoints |
| `specs/001-platform-info-api/tasks.md` | Done — 32 tasks across 8 phases |
| `specs/001-platform-info-api/checklists/requirements.md` | Done — all pass |
| `.gitignore` | Done |
| `PROGRESS.md` | Done (this file) |

## GitOps promotion gap (found 2026-09-17, closed same day)

While preparing T031 (live cluster validation), found that `k8s/overlays/local` pointed at `k3d-registry.localhost` with the image tag pinned to `:latest` — a merge to `main` pushed a new image to GHCR but produced no git diff, so ArgoCD's automated sync never actually redeployed it. Fixed by adding a CI job that commits the build's commit SHA as the image tag into `k8s/overlays/local/kustomization.yaml` after every GHCR push on `main`, using the default `GITHUB_TOKEN` (no retrigger). The overlay now targets GHCR directly; `k3d-registry.localhost` is kept only as a manual, non-committed fast-iteration path for pre-merge testing. Full decision and alternatives considered in `specs/001-platform-info-api/research.md`. New tasks T033–T036 added to `tasks.md` (Phase 9), all complete.

## Backlog (future phases — do not add to current build)

- Phase 2: Full observability stack — Prometheus (metrics) + Loki (logs) + Tempo (traces) + Grafana (visualization) + Alertmanager (alerts) — covers all 3 pillars: metrics, logs, traces. OpenTelemetry SDK instrumentation goes in the app at Phase 1 so traces are emitted when Tempo arrives.
- Phase 2: Harbor as self-hosted container registry (replacing GHCR)
- Phase 2: Dependency-Track to ingest the SBOM (`sbom.json`) generated per build — stores SBOMs across builds/time and continuously re-checks them against new CVE disclosures, closing the gap that CI-time Trivy scan and Trivy Operator (cluster-runtime) don't cover: CVEs disclosed after a build shipped. Raised 2026-07-27.
- Phase 2: Split into app repo + gitops repo (ArgoCD watches separate repo)
- Phase 3: Istio service mesh
- Phase 3: Backstage developer portal
- Phase 3: LocalStack / cloud simulator for AWS service integration tests
- Phase 4: Agentic AI security triage — an AI agent that consumes the artifacts the pipeline already produces (Trivy reports, SBOM, Semgrep findings) and summarizes/prioritizes them. Depends on Phase 1-3 being stable first (needs real pipeline output to read). Raised 2026-07-05.
