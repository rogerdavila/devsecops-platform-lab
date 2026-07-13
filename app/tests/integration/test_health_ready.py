import pytest
from httpx import ASGITransport, AsyncClient

from src.apps.public import app
from src.core import lifecycle


@pytest.mark.asyncio
async def test_health_schema_matches_contract():
    lifecycle.startup_complete()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"alive", "checked_at"}
    assert isinstance(body["alive"], bool)
    assert isinstance(body["checked_at"], str)


@pytest.mark.asyncio
async def test_ready_schema_matches_contract():
    lifecycle.startup_complete()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"ready", "checked_at"}
    assert isinstance(body["ready"], bool)
    assert isinstance(body["checked_at"], str)


@pytest.mark.asyncio
async def test_ready_transitions_503_to_200():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        before = await client.get("/ready")
        assert before.status_code == 503

        lifecycle.startup_complete()

        after = await client.get("/ready")
        assert after.status_code == 200


@pytest.mark.asyncio
async def test_health_stays_200_while_draining():
    lifecycle.startup_complete()
    lifecycle.begin_drain()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        health_resp = await client.get("/health")
        ready_resp = await client.get("/ready")
    assert health_resp.status_code == 200
    assert ready_resp.status_code == 503
