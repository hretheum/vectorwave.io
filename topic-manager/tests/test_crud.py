import pytest
from fastapi.testclient import TestClient
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from main import app


client = TestClient(app)


def test_create_get_update_delete_topic_crud():
    # Create
    payload = {
        "title": "AI Agents",
        "description": "Trendy topic",
        "keywords": ["AI", "agents"],
        "content_type": "POST",
        "platform_assignment": {"linkedin": True},
    }
    r = client.post("/topics/manual", json=payload)
    assert r.status_code == 200
    tid = r.json()["topic_id"]

    # Read
    r = client.get(f"/topics/{tid}")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "AI Agents"

    # Update (PUT)
    update = {**payload, "description": "Updated desc"}
    r = client.put(f"/topics/{tid}", json=update)
    assert r.status_code == 200
    assert r.json()["status"] == "updated"

    # Verify update
    r = client.get(f"/topics/{tid}")
    assert r.status_code == 200
    assert r.json()["description"] == "Updated desc"

    # Delete
    r = client.delete(f"/topics/{tid}")
    assert r.status_code == 200
    assert r.json()["status"] == "deleted"

    # Verify deletion
    r = client.get(f"/topics/{tid}")
    assert r.status_code == 200
    assert r.json().get("error") == "not_found"
