import os
import time
import pytest
import requests

BASE = os.getenv("ORCH_BASE", "http://localhost:8042")


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires orchestrator + redis + editorial service")
def test_checkpoint_history_and_sequence_flow():
    # 1) Create a checkpoint and wait for status to contain a result
    payload = {
        "content": "Draft content for history",
        "platform": "linkedin",
        "checkpoint": "pre_writing",
    }
    r = requests.post(f"{BASE}/checkpoints/create", json=payload, timeout=10)
    r.raise_for_status()
    cid = r.json()["checkpoint_id"]

    # Poll for status
    for _ in range(40):
        s = requests.get(f"{BASE}/checkpoints/status/{cid}", timeout=5)
        if s.status_code == 200:
            data = s.json()
            res = data.get("result")
            if isinstance(res, dict) and (isinstance(res.get("rule_count"), int) or isinstance(res.get("rules_applied"), list)):
                break
        time.sleep(0.25)
    else:
        pytest.fail("checkpoint status never contained result")

    # Fetch history and assert it contains at least 'created' and 'validated'
    h = requests.get(f"{BASE}/checkpoints/history/{cid}", timeout=5)
    h.raise_for_status()
    hist = h.json()
    assert isinstance(hist, list) and len(hist) >= 2
    types = {e.get("type") for e in hist if isinstance(e, dict)}
    assert "created" in types and ("validated" in types or "failed" in types)

    # 2) Start a sequence and poll for status until at least first checkpoint is created
    seq_req = {
        "content": "Sequence content",
        "platform": "linkedin",
    }
    s = requests.post(f"{BASE}/checkpoints/sequence/start", json=seq_req, timeout=10)
    s.raise_for_status()
    fid = s.json()["flow_id"]

    for _ in range(60):
        st = requests.get(f"{BASE}/checkpoints/sequence/status/{fid}", timeout=5)
        if st.status_code == 200:
            body = st.json()
            cps = body.get("checkpoints", [])
            if isinstance(cps, list) and len(cps) >= 1:
                assert body.get("status") in ("running", "completed")
                break
        time.sleep(0.5)
    else:
        pytest.fail("sequence status did not report any checkpoints")
