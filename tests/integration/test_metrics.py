import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    r = await client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "project_service_projects_total" in body
    assert "project_service_tasks_total" in body
    assert "http_requests_total" in body or "http_request" in body


@pytest.mark.asyncio
async def test_business_metrics_update_on_crud(client):
    r = await client.get("/metrics")
    assert r.status_code == 200

    await client.post(
        "/projects",
        json={"name": "MetricsP", "description": "d", "status": "active"},
    )
    r = await client.get("/metrics")
    body = r.text
    assert "project_service_projects_created_total" in body
    assert "project_service_projects_total" in body
