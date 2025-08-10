import os, sys
import pytest

# allow running from repo root
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from fastapi.testclient import TestClient
    from main import app
except Exception:
    app = None


@pytest.mark.skipif(app is None, reason="fastapi not available")
def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "topic-manager"


@pytest.mark.skipif(app is None, reason="fastapi not available")
def test_add_and_get_topic():
    client = TestClient(app)
    payload = {"title": "Test", "description": "Desc", "keywords": ["ai"], "content_type": "POST"}
    r = client.post("/topics/manual", json=payload)
    assert r.status_code == 200
    tid = r.json()["topic_id"]

    r2 = client.get(f"/topics/{tid}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["title"] == "Test"
