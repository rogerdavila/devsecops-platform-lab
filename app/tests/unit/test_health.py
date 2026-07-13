import pytest
from httpx import ASGITransport, AsyncClient

from src.apps.public import app
from src.core import lifecycle


@pytest.mark.asyncio
async def test_health_always_200():
    lifecycle.startup_complete()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_body_alive_true():
    lifecycle.startup_complete()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    body = response.json()
    assert body["alive"] is True


@pytest.mark.asyncio
async def test_health_body_has_checked_at():
    lifecycle.startup_complete()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    body = response.json()
    assert "checked_at" in body
    assert body["checked_at"] is not None


@pytest.mark.asyncio
async def test_health_returns_200_when_draining():
    lifecycle.startup_complete()
    lifecycle.begin_drain()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["alive"] is True
