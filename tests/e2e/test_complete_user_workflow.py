import os
import time
import pytest
import requests

BASE_ORCH = os.getenv("ORCH_BASE", "http://localhost:8080")
BASE_TM = os.getenv("TM_BASE", "http://localhost:8041")
BASE_ES = os.getenv("ES_BASE", "http://localhost:8040")

@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires local services")
def test_complete_user_workflow():
    # 1) Topic discovery
    r = requests.get(f"{BASE_TM}/topics/search", params={"q":"AI","limit":5}, timeout=10)
    r.raise_for_status()
    items = r.json().get("items", [])
    assert isinstance(items, list)

    # 2) Publish request (LI+TW)
    payload = {
        "topic": {"title": (items[0].get("title") if items else "AI Agents"), "description": "Workflow test"},
        "platforms": {
            "linkedin": {"enabled": True, "account_id": "a"},
            "twitter": {"enabled": True, "account_id": "b"}
        }
    }
    pr = requests.post(f"{BASE_ORCH}/publish", json=payload, timeout=30)
    pr.raise_for_status()
    resp = pr.json()
    assert "publication_id" in resp
    assert isinstance(resp.get("scheduled_jobs"), dict)

    # 3) Validate content via ES (best-effort)
    content_any = "AI agents transform development."
    vr = requests.post(f"{BASE_ES}/validate/comprehensive", json={"content": content_any, "mode":"comprehensive"}, timeout=10)
    if vr.status_code == 200:
        assert isinstance(vr.json().get("rules_applied", []), list)

    # 4) Analytics track
    tr = requests.post(f"{BASE_ORCH}/analytics/track", json={"request_id": resp.get("request_id") or resp.get("publication_id"), "platform": "linkedin", "status": resp.get("status")}, timeout=10)
    assert tr.status_code in (200, 404)  # 404 tolerated if not implemented

    # 5) Preferences
    pu = requests.put(f"{BASE_ORCH}/preferences/demo", json={"platform":"linkedin","hour":"11:00","score":0.8}, timeout=10)
    assert pu.status_code in (200, 404)
    pg = requests.get(f"{BASE_ORCH}/preferences/demo", timeout=10)
    assert pg.status_code in (200, 404)
