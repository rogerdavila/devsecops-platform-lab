# Progress — devsecops-platform-lab

Current state of the project. Update at the end of every work session.

## Current Phase

**SDD Workflow — Step 2: `/speckit-specify`**

Constitution is ratified (v1.0.0). Next: define the Platform Info API feature spec.

## SDD Checklist

- [x] `specify init` — project scaffold created
- [x] `/speckit-constitution` — ratified v1.0.0 (2026-07-02)
- [ ] `/speckit-specify` — Platform Info API spec ← **YOU ARE HERE**
- [ ] `/speckit-clarify` — surface assumptions
- [ ] `/speckit-plan` — tech stack and architecture doc
- [ ] `/speckit-tasks` — ordered task breakdown
- [ ] `/speckit-implement` — build phase

## What exists so far

| File | Status |
| --- | --- |
| `CLAUDE.md` | Done — technical project context, public-safe |
| `.specify/memory/constitution.md` | Done — 8 principles, v1.0.0 |
| `.gitignore` | Done |
| `PROGRESS.md` | Done (this file) |

## Backlog (future phases — do not add to current build)

- Phase 2: Harbor as self-hosted container registry (replacing GHCR)
- Phase 2: Split into app repo + gitops repo (ArgoCD watches separate repo)
- Phase 3: Istio service mesh
- Phase 3: Backstage developer portal
- Phase 3: LocalStack / cloud simulator for AWS service integration tests
