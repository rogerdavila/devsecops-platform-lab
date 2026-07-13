import pytest
from httpx import ASGITransport, AsyncClient

from src.apps.public import app
from src.core import lifecycle


@pytest.mark.asyncio
async def test_ready_503_before_startup():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False


@pytest.mark.asyncio
async def test_ready_200_after_startup():
    lifecycle.startup_complete()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


@pytest.mark.asyncio
async def test_ready_503_when_draining():
    lifecycle.startup_complete()
    lifecycle.begin_drain()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False


@pytest.mark.asyncio
async def test_ready_body_has_checked_at():
    lifecycle.startup_complete()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert "checked_at" in response.json()
