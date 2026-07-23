# devsecops-platform-lab

A production-pattern DevSecOps platform built end-to-end — not a tutorial, not a toy.

This project implements a security-first CI/CD pipeline, a Python microservice with Kubernetes deployment via GitOps, and continuous cluster scanning. Every tool included is production-defensible and documented with its rationale.

> **Work in progress.** See [PROGRESS.md](PROGRESS.md) for current state.

## What this builds

A complete DevSecOps platform from scratch:

- **Python microservice** (FastAPI) with a two-port design following production security patterns
- **Security-gated CI/CD pipeline** (GitHub Actions) with SAST, SCA, image scanning, and SBOM generation
- **GitOps deployment** to a local Kubernetes cluster via ArgoCD
- **Continuous cluster scanning** with Trivy Operator

## Platform stack

| Layer | Tool | Role |
| --- | --- | --- |
| App | FastAPI (Python) | REST API microservice |
| CI/CD | GitHub Actions | Multi-gate security pipeline |
| Container registry | GHCR | Image storage (free for public repos) |
| Local Kubernetes | k3d | k3s in Docker — fast, lightweight |
| GitOps | ArgoCD | Cluster state reconciliation from Git |
| Cluster scanning | Trivy Operator | Continuous CVE and config audit reports |
| Code quality | black, ruff, bandit | Formatting, linting, SAST |
| Secret detection | detect-secrets | Prevents credential commits |
| Dependency audit | pip-audit | SCA — known vulnerable packages |
| Image scanning | Trivy | CVE scan + SBOM (CycloneDX) |
| SAST | Semgrep | Static analysis across the codebase |
| Dockerfile linting | hadolint | Dockerfile best practices |
| SDD workflow | spec-kit | Spec-Driven Development |
| Observability | Prometheus + Loki + Tempo + Grafana | Metrics, logs, traces, dashboards *(Phase 2)* |

## The app: Platform Info API

Two-port design separating public probes from internal observability endpoints:

| Endpoint | Port | Access | Purpose |
| --- | --- | --- | --- |
| `GET /health` | 8080 | Public | Kubernetes liveness probe |
| `GET /ready` | 8080 | Public | Kubernetes readiness probe |
| `GET /info` | 9090 | Internal only | Service metadata (version, env, build) |
| `GET /metrics` | 9090 | Internal only | Prometheus-format metrics |

Port 9090 is restricted by a Kubernetes `NetworkPolicy` — only Prometheus inside the cluster can reach it. This is the production pattern, not a shortcut.

## CI/CD pipeline

Every PR and push to `main` runs through:

```text
pre-commit hooks → lint → SAST → SCA → unit tests → docker build → trivy image scan → SBOM → integration tests → push to GHCR
```

**Security gates that block the pipeline:**

- Semgrep findings (SAST)
- pip-audit findings on CRITICAL/HIGH dependencies (SCA)
- Trivy CRITICAL CVEs in the built image
- Any failing integration test against the live container

**Pre-commit hooks** (run locally before every push): `black`, `ruff`, `bandit`, `detect-secrets`, `hadolint`

## Developer setup

**Prerequisites**: Python 3.13, pip, [hadolint](https://github.com/hadolint/hadolint) binary on PATH (Dockerfile lint hook), Docker (for local container testing).

```
# 1. Install pre-commit
pip install pre-commit

# 2. Register hooks in this repo (run once after cloning)
pre-commit install

# 3. Install Python dev dependencies
pip install -r app/requirements-dev.txt

# 4. Run all hooks manually to verify setup
pre-commit run --all-files

# 5. Run tests (from the app/ directory)
cd app
pytest
```

Note: on Windows, install hadolint via `winget install hadolint.hadolint` (or download the binary and add it to PATH) so the pre-commit hook can find it.

## Project principles

This project is governed by a [constitution](.specify/memory/constitution.md) with 8 non-negotiable principles, including:

- **Security is a first-class citizen** — controls at code, container, and cluster layers
- **Shift-left on everything** — catch issues as early as possible in the pipeline
- **Real patterns only** — every decision here is defensible in a production architecture review
- **Documentation is part of the deliverable** — the WHY behind decisions is captured, not just the HOW

## Development methodology

Built using [spec-kit](https://github.com/github/spec-kit) — a Spec-Driven Development workflow where specification and architecture are defined before any code is written.

```text
spec → clarify → plan → tasks → implement
```

## License

MIT
