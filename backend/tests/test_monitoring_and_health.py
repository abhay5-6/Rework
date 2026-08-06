import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_endpoint_diagnostics(client: AsyncClient):
    """Verifies GET /health returns structured diagnostics, services status, and system metrics."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "worker_queue" in data["services"]
    assert "system" in data
    assert "disk_free_gb" in data["system"]
    assert isinstance(data["system"]["disk_free_gb"], (int, float))


async def test_root_endpoint_responsiveness(client: AsyncClient):
    """Verifies GET / root route returns 200 OK greeting."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


async def test_middleware_request_id_and_security_headers(client: AsyncClient):
    """Verifies request_context_middleware attaches X-Request-ID and security headers."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
