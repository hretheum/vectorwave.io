import os, uuid
from fastapi.testclient import TestClient
from harvester.src.main import app


def test_selective_triage_promote_flow(monkeypatch):
    # Configure token so novelty/suggestion flow accepts auth
    monkeypatch.setenv("TOPIC_MANAGER_TOKEN", "testtoken")
    client = TestClient(app)

    # Make thresholds easy to pass in local run
    monkeypatch.setenv("SELECTIVE_PROFILE_THRESHOLD", "0.0")
    monkeypatch.setenv("SELECTIVE_NOVELTY_THRESHOLD", "0.0")

    r = client.post("/triage/selective", params={"summary": "AI trend about vector db embeddings", "content_type": "POST"})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] in ("PROMOTE", "REJECT")
    # With zero thresholds we should promote
    assert body["decision"] == "PROMOTE"
    assert "suggestion_result" in body or "suggestion_error" in body
