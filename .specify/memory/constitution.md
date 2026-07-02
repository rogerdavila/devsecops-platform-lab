<!--
SYNC IMPACT REPORT
Version change: none → 1.0.0 (initial ratification)
Modified principles: N/A — initial creation from template
Added sections:
  - Core Principles (8 principles, expanded from 5-slot template)
  - Quality Gates (new section — not in template)
  - Development Workflow (new section — not in template)
  - Governance
Templates checked:
  ✅ .specify/templates/plan-template.md — "Constitution Check" placeholder is filled
     dynamically at /speckit-plan time; Quality Gates table in this constitution
     will inform that section. No template changes needed.
  ✅ .specify/templates/spec-template.md — requirements structure and scope
     constraints compatible with all 8 principles. No changes needed.
  ✅ .specify/templates/tasks-template.md — "Security hardening" in Polish phase
     aligns with Principles I and II. No changes needed.
Deferred TODOs: none — all placeholders resolved.
-->

# devsecops-platform-lab Constitution

## Core Principles

### I. Security is a First-Class Citizen

Security controls MUST exist at every layer: code (SAST, pre-commit bandit/semgrep),
container (Trivy image scan, SBOM), and cluster (Trivy Operator, NetworkPolicies).
Security MUST NOT be bolted on at the end of a feature — it is a gate at every stage.

- Every PR MUST pass SAST, SCA, and image scanning before merge.
- NetworkPolicies MUST be defined for every workload.
- Secrets MUST never be committed; `detect-secrets` enforces this in pre-commit.
- An SBOM MUST be generated for every image pushed to the registry.

### II. Shift-Left on Everything

Issues (security vulnerabilities, code quality, bugs) MUST be caught as early as possible.
The gate order is: local pre-commit → CI pipeline → cluster scanning. Each layer is
complementary to the others, not redundant.

- Pre-commit hooks (black, ruff, bandit, detect-secrets, hadolint) MUST run before every push.
- CI MUST block merges on any CRITICAL vulnerability or failed security gate.
- Trivy Operator MUST continuously scan running workloads for CVEs discovered post-deployment.

### III. Finish What You Start

Scope is fixed per phase. No feature additions mid-build. If a new idea arises during
implementation, it MUST be logged in `PROGRESS.md` as a future phase and deferred.
The current task MUST be completed and verified before moving to anything new.

- A feature is complete only when it passes all pipeline gates AND is deployed to the cluster.
- `PROGRESS.md` is the backlog. Ideas go there, not into the current implementation.

### IV. Everything is Code

All infrastructure, configuration, pipelines, Kubernetes manifests, and documentation MUST
live in the repository. Manual steps that cannot be reproduced from the repo are prohibited.
If a step requires human action, it MUST be documented as a runbook in the repo.

- Kubernetes manifests MUST be version-controlled under `k8s/`.
- Pipeline configuration MUST live in `.github/workflows/`.
- No `kubectl apply` from a local machine outside of documented bootstrap procedures.

### V. GitOps as the Deployment Model

The repository is the single source of truth for cluster state. ArgoCD MUST reconcile the
cluster to match the repo. Direct cluster mutations (ad-hoc `kubectl apply`, manual Helm
releases outside of GitOps flow) are prohibited in normal operations.

- All deployment changes flow through Git commits → ArgoCD sync.
- Cluster state drift MUST be detected and reconciled by ArgoCD, not manually corrected.
- ArgoCD sync status is the authoritative definition of "what is running."

### VI. Understand Before You Use

Every tool in this project MUST be understood before it is added. The bar: can you explain
what problem it solves, why it was chosen over alternatives, and what it does at runtime?
No black boxes. No cargo-culted tooling.

- Each tool MUST have documented rationale in `CLAUDE.md` or the relevant spec.
- "Everyone else uses it" is not a sufficient rationale.

### VII. Real Patterns Only

Everything built here MUST be defensible in a production architecture conversation. No toy
shortcuts that would need to be unlearned. The two-port design (8080 public / 9090 internal),
NetworkPolicies, SBOM generation, and GitOps flow are all production patterns — not
lab inventions.

- If a shortcut is taken, it MUST be explicitly documented with the production equivalent noted.
- Patterns that would be wrong in production are prohibited without written justification.

### VIII. Documentation is Part of the Deliverable

A feature is not done until its WHY is documented. Architecture decisions, tool choices,
security tradeoffs, and design rationale MUST be captured — not just the implementation.
Future readers (including the author) MUST be able to understand decisions without reading
git history.

- `CLAUDE.md` captures project-level context and architecture decisions.
- Specs in `specs/` capture the feature-level WHY before any HOW is written.
- Commit messages MUST be meaningful and reference the task or principle they serve.

## Quality Gates

These gates MUST pass before any artifact is considered complete:

| Gate | Stage | Failure Action |
| --- | --- | --- |
| Pre-commit: black, ruff, bandit, detect-secrets, hadolint | Local | Block commit |
| SAST — Semgrep | CI | Block merge |
| SCA — pip-audit | CI | Block merge on CRITICAL/HIGH |
| Unit tests — pytest with coverage | CI | Block merge |
| Docker image build | CI | Block merge |
| Image scan — Trivy (CRITICAL CVEs) | CI | Block push to registry |
| SBOM generation (CycloneDX via Trivy) | CI | Block push to registry |
| Integration tests (live container) | CI | Block push to registry |
| ArgoCD sync healthy | Cluster | Alert |
| Trivy Operator reports | Cluster | Alert + track in PROGRESS.md |

## Development Workflow

All work MUST follow the Spec-Driven Development (SDD) flow via spec-kit:

1. All work starts with a spec (`/speckit-specify` → `specs/<feature>/spec.md`).
2. Assumptions are surfaced before planning (`/speckit-clarify`).
3. Architecture and tech decisions are documented before any code is written (`/speckit-plan`).
4. Tasks are broken down with explicit dependencies (`/speckit-tasks` → `tasks.md`).
5. Implementation follows the task list (`/speckit-implement`), one task at a time.
6. No code is written before a spec exists for the feature it belongs to.
7. `PROGRESS.md` MUST be updated at the end of every work session.

## Governance

This constitution supersedes all other practices for this project. Any deviation MUST be
justified in writing in the relevant spec or commit message.

**Amendment procedure:**

- MAJOR bump: removing or redefining a principle in a backward-incompatible way. Requires
  explicit documentation of why the old principle no longer applies.
- MINOR bump: adding a new principle or materially expanding an existing one.
- PATCH bump: clarifications, wording improvements, typo fixes.

**Compliance review:** Constitution Check is performed at the start of every `/speckit-plan`
execution. The plan MUST explicitly confirm compliance or document justified exceptions.

**Precedence:** In any conflict between convenience and a principle in this document,
the principle wins. Exceptions require written justification and a PATCH version bump.

**Version**: 1.0.0 | **Ratified**: 2026-07-02 | **Last Amended**: 2026-07-02
