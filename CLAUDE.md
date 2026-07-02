<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->

# Project Context — devsecops-platform-lab

This file is the single source of truth for any Claude instance working on this project. Read it fully before doing anything else. Also read `PROGRESS.md` to know the current state.

## Why this project exists

A complete DevSecOps platform built end-to-end. The goal is to ship something real that demonstrates production-grade patterns: secure Python microservice, multi-gate CI/CD pipeline with SAST/SCA/image scanning, GitOps deployment to Kubernetes, continuous cluster scanning.

**The most important rule:** finish it. Scope is fixed. No pivoting mid-build. New ideas go to `PROGRESS.md` as future phases.

## What we are building

A **DevSecOps platform lab** — a monorepo containing a real Python microservice deployed to a local Kubernetes cluster via GitOps, with a full security-first CI/CD pipeline.

### The app: Platform Info API (FastAPI / Python)

A production-pattern REST API with two-port design:

| Endpoint | Port | Access | Purpose |
| --- | --- | --- | --- |
| `GET /health` | 8080 | Public | Liveness probe for Kubernetes |
| `GET /ready` | 8080 | Public | Readiness probe (checks dependencies) |
| `GET /info` | 9090 | Internal only | Service metadata (version, env, build) |
| `GET /metrics` | 9090 | Internal only | Prometheus-format metrics |

Why two ports: `/info` and `/metrics` expose sensitive data (version, internals). A NetworkPolicy blocks external access to port 9090 — only Prometheus inside the cluster can reach it. This is the real production pattern, not a shortcut.

### The CI/CD pipeline (GitHub Actions)

**Pre-commit hooks (local, runs before every git push):**

- `black` — Python code formatter
- `ruff` — linter (faster than flake8)
- `bandit` — SAST for Python (catches security issues in code)
- `detect-secrets` — prevents secrets from being committed
- `hadolint` — Dockerfile linter

**GitHub Actions pipeline (runs on every PR and push to main):**

1. Lint & format check (black --check, ruff)
2. SAST — Semgrep (broader than bandit alone)
3. SCA — pip-audit (vulnerability scan of Python dependencies)
4. Unit tests — pytest with coverage
5. Docker build
6. Image scan — Trivy (CVEs in the built image) → pipeline fails on CRITICAL
7. SBOM generation — Trivy generates Software Bill of Materials (CycloneDX format)
8. Integration tests — spins up the container, hits real endpoints, validates responses
9. Push to GHCR — only if all gates pass, only on main branch

Trivy in CI **and** Trivy Operator in the cluster: CI (shift-left) blocks bad images before they deploy. Trivy Operator catches new CVEs discovered after deployment and scans running workloads continuously.

### The platform stack

| Tool | Role | Why chosen |
| --- | --- | --- |
| **k3d** | Local Kubernetes | Runs k3s in Docker — faster and lighter than Minikube |
| **ArgoCD** | GitOps / CD | The repo IS the source of truth; ArgoCD reconciles cluster state |
| **Trivy Operator** | Continuous cluster scanning | Scans everything running, generates K8s-native reports |
| **GHCR** | Container registry | Free for public repos; phase 2 consider Harbor (CNCF) |
| **FastAPI** | Python web framework | Modern, fast, built-in OpenAPI, easy to test |
| **spec-kit** | SDD workflow | Spec-Driven Development: spec → plan → tasks → implement |

### Repo structure (monorepo)

```text
devsecops-platform-lab/
├── CLAUDE.md                        ← you are here
├── PROGRESS.md                      ← current state and next steps
├── .specify/memory/constitution.md  ← project principles (spec-kit)
├── specs/
│   └── platform-info-api/
│       ├── spec.md                  ← what and why (no tech details)
│       ├── plan.md                  ← tech stack and architecture
│       └── tasks.md                 ← ordered, executable tasks
├── app/
│   ├── src/
│   ├── tests/unit/
│   ├── tests/integration/
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/
│   ├── base/                        ← Kubernetes manifests (ArgoCD reads these)
│   └── overlays/
├── .github/workflows/ci.yml
└── .pre-commit-config.yaml
```

## How we work (SDD workflow)

We follow spec-kit's Spec-Driven Development flow. Check `PROGRESS.md` for the current step.

1. `/speckit-constitution` — establish project principles (done when constitution.md is filled)
2. `/speckit-specify` — define Platform Info API requirements (what/why, no tech)
3. `/speckit-clarify` — surface assumptions before planning
4. `/speckit-plan` — tech stack and architecture decisions
5. `/speckit-tasks` — ordered task breakdown with dependencies
6. `/speckit-implement` — build task by task
