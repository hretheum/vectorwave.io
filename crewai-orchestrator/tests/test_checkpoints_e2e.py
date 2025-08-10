import os
import time
import pytest
import requests

BASE = os.getenv("ORCH_BASE", "http://localhost:8042")


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires running orchestrator + editorial service")
def test_checkpoint_create_status_intervene_e2e():
    # Create
    payload = {
        "content": "Draft content for checkpoint e2e",
        "platform": "linkedin",
        "checkpoint": "pre_writing",
        "user_notes": "initial run"
    }
    r = requests.post(f"{BASE}/checkpoints/create", json=payload, timeout=10)
    r.raise_for_status()
    cid = r.json()["checkpoint_id"]
    assert cid

    # Poll status
    for _ in range(20):
        s = requests.get(f"{BASE}/checkpoints/status/{cid}", timeout=5)
        if s.status_code == 200:
            data = s.json()
            assert data["checkpoint"] in ("pre_writing", "mid_writing", "post_writing")
            # result shape comes from Editorial Service; ensure it's present and has counts
            res = data.get("result")
            if not isinstance(res, dict):
                time.sleep(0.25)
                continue
            # Accept either explicit rule_count or list of rules_applied
            assert (isinstance(res.get("rule_count"), int) and res.get("rule_count") >= 1) or (
                isinstance(res.get("rules_applied"), list) and len(res.get("rules_applied")) >= 1
            )
            break
        time.sleep(0.2)
    else:
        pytest.fail("status polling failed")

    # Intervene (no-op) and check status again
    iv = requests.post(f"{BASE}/checkpoints/{cid}/intervene", json={"user_input": "noop", "finalize": False}, timeout=10)
    iv.raise_for_status()
    s2 = requests.get(f"{BASE}/checkpoints/status/{cid}", timeout=5)
    s2.raise_for_status()
    assert s2.json()["checkpoint_id"] == cid
