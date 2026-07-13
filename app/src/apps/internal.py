from fastapi import Depends, FastAPI

from src.core.config import settings
from src.core.network_guard import require_internal_network
from src.models.health import ServiceMetadata

app = FastAPI(docs_url=None, redoc_url=None)


@app.get("/info", response_model=ServiceMetadata, dependencies=[Depends(require_internal_network)])
async def info() -> ServiceMetadata:
    return ServiceMetadata(
        version=settings.version,
        environment=settings.environment.value,
        build_id=settings.build_id,
    )
