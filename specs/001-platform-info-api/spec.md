# Feature Specification: Platform Info API

**Feature Branch**: `001-platform-info-api`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Platform Info API — a production-pattern service exposing health/readiness on a public port and service metadata/metrics on an internal-only port."
Lee CLAUDE.md y PROGRESS.md para contexto del proyecto. Estamos en el paso 2 del flujo SDD. Ejecuta /speckit-specify para el Platform Info API.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Orchestrator checks service health (Priority: P1)

A Kubernetes orchestrator needs to know if the service instance is alive and ready to receive traffic, so it can route traffic correctly and restart unhealthy instances.

**Why this priority**: Without health/readiness signals, the orchestrator cannot safely manage the workload — this is the minimum viable slice; nothing else works without it.

**Independent Test**: Can be fully tested by starting the service and querying the liveness and readiness endpoints, and confirming they report accurate state (including when a dependency is unavailable).

**Acceptance Scenarios**:

1. **Given** the service has started successfully, **When** the orchestrator queries the liveness check, **Then** it receives confirmation the process is alive.
2. **Given** the service's dependencies are healthy, **When** the orchestrator queries the readiness check, **Then** it receives confirmation the service can accept traffic.
3. **Given** a required dependency is unavailable, **When** the orchestrator queries the readiness check, **Then** it receives a not-ready signal so traffic is withheld.

---

### User Story 2 - Operator inspects service metadata (Priority: P2)

An internal operator or automated tool needs to know which version and build of the service is running, and in which environment, to support troubleshooting and audits.

**Why this priority**: Valuable for operations but not required for the service to function — the platform can run without it, unlike health checks.

**Independent Test**: Can be fully tested by querying the metadata endpoint from within the trusted internal network and confirming it returns version, environment, and build information.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** a caller on the internal network requests service metadata, **Then** it receives the current version, environment, and build identifiers.
2. **Given** a caller outside the trusted internal network attempts to request service metadata, **When** the request reaches the service, **Then** it is refused.

---

### User Story 3 - Monitoring system collects metrics (Priority: P3)

A monitoring system needs to continuously collect operational metrics from the service to support dashboards and alerting.

**Why this priority**: Enhances observability but is not required for core service operation or for the P1/P2 stories to deliver value on their own.

**Independent Test**: Can be fully tested by having a monitoring collector on the internal network scrape the metrics endpoint and confirming it receives a well-formed, parseable metrics payload.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** the monitoring system scrapes metrics from the internal network, **Then** it receives current operational metrics in a standard, parseable format.
2. **Given** a caller outside the trusted internal network attempts to scrape metrics, **When** the request reaches the service, **Then** it is refused.

---

### Edge Cases

- What happens when a dependency check times out rather than cleanly failing? Readiness MUST report not-ready rather than hang indefinitely.
- How does the system handle a request to the internal-only endpoints from outside the trusted network? Request MUST be refused, not silently allowed.
- What happens when the service is mid-shutdown? Liveness/readiness MUST reflect that the instance should no longer receive new traffic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a liveness signal indicating whether the running process is alive, reachable on the public-facing port.
- **FR-002**: System MUST expose a readiness signal indicating whether the service can currently accept traffic, reachable on the public-facing port.
- **FR-003**: Readiness MUST reflect the health of the service's dependencies, not just process liveness.
- **FR-004**: System MUST expose service metadata (at minimum: version, environment, build identifier) on an internal-only port.
- **FR-005**: System MUST expose operational metrics in a standard, parseable format on an internal-only port.
- **FR-006**: System MUST restrict access to the metadata and metrics capabilities to callers within the trusted internal network only.
- **FR-007**: System MUST NOT expose metadata or metrics on the same access path as the public health/readiness checks.
- **FR-008**: System MUST respond to health/readiness checks quickly enough for automated orchestration to act on them without unnecessary delay.

### Key Entities

- **Service Health State**: Represents current liveness and readiness of the running instance; derived from process state and dependency checks.
- **Service Metadata**: Represents identifying information about the running instance — version, environment, build identifier.
- **Operational Metrics**: Represents quantitative runtime measurements of the service, exposed for collection by a monitoring system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An orchestrator can determine service health status in under 1 second per check.
- **SC-002**: 100% of requests to internal-only capabilities from outside the trusted network are refused.
- **SC-003**: A monitoring system can successfully collect metrics on every scrape attempt when the service is healthy.
- **SC-004**: An operator can identify the exact running version and build of any service instance without needing direct access to the deployment pipeline or source control.

## Assumptions

- "Trusted internal network" means the cluster-internal network reachable only from within the platform (e.g., other in-cluster workloads such as a monitoring collector), not the public internet.
- The service has at least one dependency whose health affects readiness (even if minimal at first release).
- Consumers of health/readiness are automated systems (orchestrator), not human end users.
- Consumers of metadata/metrics are internal operators and automated monitoring tooling, not external customers.