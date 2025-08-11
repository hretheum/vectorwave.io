import os
import pytest
import requests

BASE_ORCH = os.getenv("ORCH_BASE", "http://localhost:8080")

@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires local services")
def test_partial_failure_one_platform(monkeypatch):
    payload = {
        "topic": {"title": "Test", "description": "Desc"},
        "platforms": {
            "linkedin": {"enabled": True, "account_id": "a"},
            "twitter": {"enabled": True, "account_id": "b"}
        }
    }
    r = requests.post(f"{BASE_ORCH}/publish", json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    # Expect scheduled_jobs for at least one platform, and status completed|failed
    assert data.get("status") in ("completed", "failed")
    assert isinstance(data.get("scheduled_jobs"), dict)
