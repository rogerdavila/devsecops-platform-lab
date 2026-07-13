from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Response, status

from src.core import lifecycle
from src.models.health import HealthStatus, ReadinessStatus


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    lifecycle.startup_complete()
    yield
    lifecycle.begin_drain()


app = FastAPI(lifespan=_lifespan, docs_url=None, redoc_url=None)


@app.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    return HealthStatus(alive=True)


@app.get("/ready", response_model=ReadinessStatus)
async def ready(response: Response) -> ReadinessStatus:
    ready_state = lifecycle.is_ready()
    if not ready_state:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessStatus(ready=ready_state)
