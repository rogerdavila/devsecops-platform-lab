import pytest
from httpx import ASGITransport, AsyncClient

from src.apps.internal import app


@pytest.mark.asyncio
async def test_metrics_returns_200():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_content_type_is_prometheus():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_metrics_contains_all_four_metric_families():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/info")
        response = await client.get("/metrics")
    body = response.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "process_uptime_seconds" in body


@pytest.mark.asyncio
async def test_metrics_process_uptime_is_non_negative():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/metrics")
    for line in response.text.splitlines():
        if line.startswith("process_uptime_seconds ") and not line.startswith("#"):
            assert float(line.split(" ")[1]) >= 0
            break


@pytest.mark.asyncio
async def test_metrics_rejected_when_not_internal(monkeypatch):
    import src.core.network_guard as ng

    monkeypatch.setattr(ng, "is_private_ip", lambda ip: False)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/metrics")

    assert response.status_code == 403
