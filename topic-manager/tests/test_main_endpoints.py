import sys
import pathlib
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

# Ensure src in path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from main import app as fastapi_app  # type: ignore

def _seed_topic(client: TestClient, title: str = "AI Test") -> None:
    payload: Dict[str, Any] = {
        "title": title,
        "description": "Desc",
        "keywords": ["ai"],
        "content_type": "POST",
    }
    client.post("/topics/manual", json=payload)

@pytest.fixture(autouse=True)
def clear_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests do not require auth token."""
    monkeypatch.delenv("TOPIC_MANAGER_TOKEN", raising=False)

def test_list_topics_returns_items() -> None:
    client = TestClient(fastapi_app)
    _seed_topic(client, title="First topic")
    resp = client.get("/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data and data["count"] >= 1

def test_novelty_check_basic() -> None:
    client = TestClient(fastapi_app)
    _seed_topic(client, title="Novelty Seed")
    resp = client.post("/topics/novelty-check", json={"title": "Novelty Seed"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(["decision", "similarity_score", "nearest", "threshold"]).issubset(body)
