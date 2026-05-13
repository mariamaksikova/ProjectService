import pytest


@pytest.mark.asyncio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Project Service API"
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_projects_crud_and_tasks(client):
    r = await client.post(
        "/projects",
        json={"name": "P1", "description": "d", "status": "active"},
    )
    assert r.status_code == 201
    pid = r.json()["id"]

    r = await client.get("/projects")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "P1"

    r = await client.get(f"/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["tasks"] == []

    r = await client.get("/projects/999999")
    assert r.status_code == 404

    r = await client.post(
        f"/projects/{pid}/tasks",
        json={"name": "T1", "description": None, "status": "todo"},
    )
    assert r.status_code == 201
    tid = r.json()["id"]
    assert r.json()["project_id"] == pid

    r = await client.get(f"/tasks/{tid}")
    assert r.status_code == 200

    r = await client.put(
        f"/tasks/{tid}",
        json={"status": "done"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "done"

    r = await client.get("/stats")
    assert r.status_code == 200
    st = r.json()
    assert st["total_projects"] == 1
    assert st["total_tasks"] == 1
    assert st["tasks_by_status"]["done"] == 1

    r = await client.delete(f"/tasks/{tid}")
    assert r.status_code == 200

    r = await client.delete(f"/projects/{pid}")
    assert r.status_code == 200

    r = await client.get("/projects")
    assert r.json() == []
