import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.core import lifecycle
from src.core.config import settings
from src.core.metrics import (
    REGISTRY,
    http_request_duration_seconds,
    http_requests_errors_total,
    http_requests_total,
    process_uptime_seconds,
)
from src.core.network_guard import require_internal_network
from src.models.health import ServiceMetadata

app = FastAPI(docs_url=None, redoc_url=None)


@app.middleware("http")
async def _record_metrics(request: Request, call_next: object) -> object:
    start = time.perf_counter()
    response = await call_next(request)  # type: ignore[operator]
    duration = time.perf_counter() - start

    method = request.method
    path = request.url.path
    status = str(response.status_code)

    http_requests_total.labels(method=method, path=path, status=status).inc()
    http_request_duration_seconds.labels(method=method, path=path).observe(duration)
    if response.status_code >= 500:
        http_requests_errors_total.labels(method=method, path=path, status=status).inc()

    return response


@app.get("/info", response_model=ServiceMetadata, dependencies=[Depends(require_internal_network)])
async def info() -> ServiceMetadata:
    return ServiceMetadata(
        version=settings.version,
        environment=settings.environment.value,
        build_id=settings.build_id,
    )


@app.get("/metrics", dependencies=[Depends(require_internal_network)])
async def metrics() -> PlainTextResponse:
    uptime = (datetime.now(timezone.utc) - lifecycle.get_start_time()).total_seconds()
    process_uptime_seconds.set(uptime)
    return PlainTextResponse(
        content=generate_latest(REGISTRY).decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
