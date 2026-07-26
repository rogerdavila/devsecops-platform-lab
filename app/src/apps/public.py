import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status

from src.core import lifecycle
from src.core.metrics import (
    http_request_duration_seconds,
    http_requests_errors_total,
    http_requests_total,
)
from src.models.health import HealthStatus, ReadinessStatus


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    lifecycle.startup_complete()
    yield
    lifecycle.begin_drain()


app = FastAPI(lifespan=_lifespan, docs_url=None, redoc_url=None)


@app.middleware("http")
async def _record_metrics(request: Request, call_next: object) -> object:
    start = time.perf_counter()
    response = await call_next(request)  # type: ignore[operator]
    duration = time.perf_counter() - start

    method = request.method
    path = request.url.path
    status_code = str(response.status_code)

    http_requests_total.labels(method=method, path=path, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, path=path).observe(duration)
    if response.status_code >= 500:
        http_requests_errors_total.labels(
            method=method, path=path, status=status_code
        ).inc()

    return response


@app.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    return HealthStatus(alive=True)


@app.get("/ready", response_model=ReadinessStatus)
async def ready(response: Response) -> ReadinessStatus:
    ready_state = lifecycle.is_ready()
    if not ready_state:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessStatus(ready=ready_state)
