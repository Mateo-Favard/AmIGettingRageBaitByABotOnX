import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    # Without real DB, we expect 503 (degraded) since DB check fails
    # But the endpoint itself should respond
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_has_security_headers(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Request-ID") is not None


@pytest.mark.asyncio
async def test_health_has_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 36  # UUID format
