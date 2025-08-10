import sys, pathlib
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / 'src'))
from main import app
from matching import suggest_platforms


def test_end_to_end_crud_suggest_assign():
    c = TestClient(app)

    # Create
    payload = {"title": "AI for B2B", "description": "desc", "keywords": ["AI", "B2B"], "content_type": "POST"}
    r = c.post("/topics/manual", json=payload)
    assert r.status_code == 200
    tid = r.json()["topic_id"]

    # Read
    r = c.get(f"/topics/{tid}")
    assert r.status_code == 200
    topic = r.json()

    # Suggest
    r = c.get("/topics/suggestions?limit=2")
    assert r.status_code == 200

    # Assign
    platforms = suggest_platforms(topic)
    assert isinstance(platforms, list) and len(platforms) >= 1

    # Update
    payload["description"] = "updated"
    r = c.put(f"/topics/{tid}", json=payload)
    assert r.status_code == 200

    # Delete
    r = c.delete(f"/topics/{tid}")
    assert r.status_code == 200
