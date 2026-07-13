from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class HealthStatus(BaseModel):
    alive: bool
    checked_at: datetime = Field(default_factory=_now)


class ReadinessStatus(BaseModel):
    ready: bool
    checked_at: datetime = Field(default_factory=_now)


class ServiceMetadata(BaseModel):
    version: str
    environment: str
    build_id: str
