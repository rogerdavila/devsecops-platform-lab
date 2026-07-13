import pytest
from httpx import ASGITransport, AsyncClient

from src.apps.internal import app


@pytest.mark.asyncio
async def test_info_schema_matches_contract():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/info")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"version", "environment", "build_id"}
    assert isinstance(body["version"], str)
    assert isinstance(body["environment"], str)
    assert isinstance(body["build_id"], str)


@pytest.mark.asyncio
async def test_info_fields_are_non_empty():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/info")
    body = response.json()
    assert body["version"] != ""
    assert body["environment"] != ""
    assert body["build_id"] != ""


@pytest.mark.asyncio
async def test_info_rejected_when_not_internal(monkeypatch):
    import src.core.network_guard as ng

    monkeypatch.setattr(ng, "is_private_ip", lambda ip: False)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/info")

    assert response.status_code == 403
    assert response.json()["detail"] == "Access restricted to internal network"
