import sys, pathlib, uuid
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from main import app  # type: ignore


def test_novelty_check_requires_bearer_when_configured(monkeypatch):
    c = TestClient(app)
    # Ensure token required
    monkeypatch.setenv("TOPIC_MANAGER_TOKEN", "secret")
    r = c.post("/topics/novelty-check", json={"title": "AI", "summary": "AI"})
    assert r.status_code == 401
    assert r.json()["code"] == "unauthorized"

    # With wrong token
    r = c.post("/topics/novelty-check", json={"title": "AI", "summary": "AI"}, headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 401

    # With correct token
    r = c.post("/topics/novelty-check", json={"title": "AI", "summary": "AI"}, headers={"Authorization": "Bearer secret"})
    assert r.status_code == 200
    body = r.json()
    assert "decision" in body and body["decision"] in ("DUPLICATE", "NOVEL")


def test_suggestion_requires_idempotency_and_bearer(monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("TOPIC_MANAGER_TOKEN", "secret")

    payload = {
        "title": "AI Trends Weekly",
        "summary": "Roundup",
        "keywords": ["ai"],
        "content_type": "POST",
    }

    # Missing idempotency header
    r = c.post("/topics/suggestion", json=payload, headers={"Authorization": "Bearer secret"})
    assert r.status_code == 400
    assert r.json()["code"] == "missing_idempotency"

    # With header and valid token
    idem = str(uuid.uuid4())
    r = c.post(
        "/topics/suggestion",
        json=payload,
        headers={"Authorization": "Bearer secret", "Idempotency-Key": idem},
    )
    assert r.status_code == 200
    assert r.json()["status"] in ("created", "duplicate")

    # Repeat with same idempotency key -> duplicate
    r2 = c.post(
        "/topics/suggestion",
        json=payload,
        headers={"Authorization": "Bearer secret", "Idempotency-Key": idem},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"
