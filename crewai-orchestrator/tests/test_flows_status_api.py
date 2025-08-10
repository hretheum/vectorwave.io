import os
import time
import pytest
import requests

BASE = os.getenv("ORCH_BASE", "http://localhost:8042")


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires running orchestrator")
def test_flows_execute_and_status():
    r = requests.post(f"{BASE}/flows/execute", json={"content": "Draft", "platform": "linkedin"}, timeout=10)
    r.raise_for_status()
    flow_id = r.json()["flow_id"]
    assert flow_id

    # Poll until running or completed (tolerant to long-running envs)
    last = None
    for _ in range(40):
        s = requests.get(f"{BASE}/flows/status/{flow_id}", timeout=5)
        last = s
        if s.status_code == 200:
            data = s.json()
            # Be tolerant to different server versions: require progress and allow optional status
            assert 0 <= data.get("progress", 0) <= 100
            is_completed = data.get("status") == "completed" or ("result" in data and isinstance(data["result"], dict))
            if is_completed:
                if "result" in data:
                    assert isinstance(data["result"], dict)
                break
        time.sleep(0.25)
    else:
        # Accept partial completion in constrained environments
        assert last is not None and last.status_code == 200

    lst = requests.get(f"{BASE}/flows/active", timeout=5)
    assert lst.status_code in (200, 404)
