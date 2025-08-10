import sys, pathlib
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from main import app


def test_list_endpoint_filters_and_pagination():
    c = TestClient(app)
    # Seed a couple topics
    for i in range(5):
        payload = {"title": f"AI case {i}", "description": "enterprise", "keywords": ["AI", "B2B"], "content_type": "POST"}
        c.post("/topics/manual", json=payload)
    # List first 2
    r = c.get("/topics?limit=2&offset=0&q=case&content_type=POST")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    assert data["total"] >= 2
    assert data["limit"] == 2 and data["offset"] == 0
    assert len(data["items"]) == 2
