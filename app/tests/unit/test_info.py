import pytest
from httpx import ASGITransport, AsyncClient

from src.apps.internal import app
from src.core.config import Settings, Environment


@pytest.mark.asyncio
async def test_info_returns_200_from_internal_caller():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/info")
    # ASGITransport sets client host to testclient (127.0.0.1 → private → allowed)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_info_body_has_required_fields():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/info")
    body = response.json()
    assert "version" in body
    assert "environment" in body
    assert "build_id" in body


@pytest.mark.asyncio
async def test_info_environment_is_valid_enum_value():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/info")
    env = response.json()["environment"]
    assert env in ("dev", "staging", "prod")


@pytest.mark.asyncio
async def test_info_returns_403_for_public_ip(monkeypatch):
    import src.core.network_guard as ng

    original = ng.is_private_ip

    def always_false(ip: str) -> bool:
        return False

    monkeypatch.setattr(ng, "is_private_ip", always_false)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/info")

    monkeypatch.setattr(ng, "is_private_ip", original)
    assert response.status_code == 403
