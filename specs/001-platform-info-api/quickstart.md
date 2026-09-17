# Quickstart: Platform Info API

Validation guide for the feature once implemented. Not implementation instructions — see `tasks.md` (created by `/speckit-tasks`) for that. This proves the contract in `contracts/api.yaml` actually holds.

## Prerequisites

- Python 3.13 and the dependencies in `app/requirements.txt` installed, OR the built Docker image.
- For the NetworkPolicy portion: a running k3d cluster with ArgoCD installed — see [Local Kubernetes cluster](../../README.md#local-kubernetes-cluster) in the root README for one-time setup.

## Deploy this feature to the cluster

Once the cluster + ArgoCD exist ([root README](../../README.md#local-kubernetes-cluster)), register the Application once:

```bash
kubectl apply -f k8s/argocd/platform-info-app.yaml
kubectl -n default get pods -w
```

### The real flow: GitOps-managed deploy

`k8s/overlays/local/kustomization.yaml` points at `ghcr.io/rogerdavila/platform-info-api`. Every push to `main` runs the full CI pipeline (lint → SAST → SCA → tests → build → scan → SBOM → integration tests → push to GHCR), then a final job commits the build's commit SHA as the image tag into that overlay file directly. ArgoCD (`automated` sync, `selfHeal: true`, `prune: true`) picks up that git diff and redeploys the exact image the pipeline just scanned and published — no manual `docker push` or `kubectl apply` needed after the one-time Application registration above. See `research.md` ("CI commits the image tag bump") for why this is necessary — ArgoCD reacts to git diffs, not registry pushes.

### Fast local iteration (before merging, skips CI)

To test a change against the cluster before it reaches `main` — e.g. verifying a NetworkPolicy tweak — push a throwaway build to the local k3d registry and point the running Deployment at it manually. This is a temporary, non-committed override, not a deployment path:

```bash
docker build -t k3d-registry.localhost:5050/platform-info-api:dev app/
docker push k3d-registry.localhost:5050/platform-info-api:dev
kubectl -n default set image deployment/platform-info-api api=k3d-registry.localhost:5050/platform-info-api:dev
```

ArgoCD's `selfHeal: true` will revert this back to the git-declared GHCR image on its next reconcile — that's expected, not a bug.

Once pods are `Running` (either path), port-forward to reach the service:

```bash
kubectl port-forward svc/platform-info-public 18080:8080
```

Use a local port other than `8080` (e.g. `18080` above) — `k3d cluster create` already binds host port `8080` to the cluster's Traefik load balancer (`-p "8080:80@loadbalancer"`). Curling `localhost:8080` hits Traefik, not this Service, and returns Traefik's own `404 page not found` (no `Ingress` is defined for this app) — easy to mistake for the app itself being broken.

Now the endpoints below are reachable at `localhost:8080` for the public port. For the internal port (`9090`), port-forward the internal Service instead and treat it as originating from inside the cluster.

## Run locally (no cluster)

```bash
cd app
python -m venv .venv          # create isolated environment (first time only)
source .venv/bin/activate     # activate it (use .venv\Scripts\activate on Windows)
pip install -r requirements.txt
python -m src.main
```

> **Tip**: always use a virtual environment (`venv`) to avoid polluting your system Python with project dependencies. The `.venv/` directory is gitignored.

The entrypoint starts both ASGI servers (public :8080, internal :9090) in one process — see `research.md` for why. Run from `app/` so that `src.*` imports resolve correctly.

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
