import os
import pytest
import requests

BASE_ORCH = os.getenv("ORCH_BASE", "http://localhost:8080")
BASE_TM = os.getenv("TM_BASE", "http://localhost:8041")

@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires local services")
def test_malformed_publish_payload():
    r = requests.post(f"{BASE_ORCH}/publish", json={}, timeout=10)
    assert r.status_code in (400, 422)

@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires local services")
def test_novelty_check_unauthorized_when_token_enabled(monkeypatch):
    # If token is enabled in env, expect 401; otherwise allow skipping
    r = requests.post(f"{BASE_TM}/topics/novelty-check", json={"title":"x","summary":"y"}, timeout=10)
    if os.getenv("TOPIC_MANAGER_TOKEN"):
        assert r.status_code == 401
    else:
        assert r.status_code in (200, 401, 403)
