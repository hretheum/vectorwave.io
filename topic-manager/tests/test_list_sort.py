import sys, pathlib
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from main import app


def test_list_sorting_by_title_desc():
    c = TestClient(app)
    titles = ["CaseB", "CaseA", "CaseG"]
    for t in titles:
        payload = {"title": t, "description": "d", "keywords": ["k"], "content_type": "POST"}
        c.post("/topics/manual", json=payload)
    r = c.get("/topics?limit=3&sort_by=title&order=desc&q=case")
    assert r.status_code == 200
    data = r.json()
    got = [item["title"] for item in data["items"]]
    assert got == sorted(titles, reverse=True)
