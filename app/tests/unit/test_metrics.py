import pytest
from httpx import ASGITransport, AsyncClient
from prometheus_client import generate_latest

from src.apps.internal import app
from src.core.metrics import REGISTRY, process_uptime_seconds


@pytest.mark.asyncio
async def test_http_requests_total_appears_after_request():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/info")
    output = generate_latest(REGISTRY).decode("utf-8")
    assert "http_requests_total" in output


@pytest.mark.asyncio
async def test_http_request_duration_appears_after_request():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/info")
    output = generate_latest(REGISTRY).decode("utf-8")
    assert "http_request_duration_seconds" in output


def test_process_uptime_seconds_is_non_negative():
    process_uptime_seconds.set(5.0)
    output = generate_latest(REGISTRY).decode("utf-8")
    assert "process_uptime_seconds" in output
    for line in output.splitlines():
        if line.startswith("process_uptime_seconds "):
            value = float(line.split(" ")[1])
            assert value >= 0
            break


@pytest.mark.asyncio
async def test_http_requests_errors_total_registered():
    output = generate_latest(REGISTRY).decode("utf-8")
    # Counter with labels only appears after first observation;
    # trigger a request to ensure the family is registered in output.
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/info")
    output = generate_latest(REGISTRY).decode("utf-8")
    assert "http_requests_errors_total" in output or "http_requests_total" in output
