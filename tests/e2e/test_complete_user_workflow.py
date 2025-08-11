import asyncio
import os
import time
import pytest
import httpx

EDITORIAL_URL = os.getenv("EDITORIAL_URL", "http://localhost:8040")
TOPIC_MANAGER_URL = os.getenv("TOPIC_MANAGER_URL", "http://localhost:8041")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8042")
HARVESTER_URL = os.getenv("HARVESTER_URL", "http://localhost:8043")


async def _is_up(url: str, path: str = "/health", timeout: float = 2.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{url}{path}")
            return r.status_code == 200
    except Exception:
        return False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_user_workflow_sanity():
    # 1) Check core services up (skip if not running locally)
    editorial_up, tm_up, harvester_up = await asyncio.gather(
        _is_up(EDITORIAL_URL), _is_up(TOPIC_MANAGER_URL), _is_up(HARVESTER_URL)
    )
    if not (editorial_up and tm_up and harvester_up):
        pytest.skip("Required services not running locally (editorial/topic-manager/harvester)")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 2) Editorial Service profile score
        summary = "AI trend about vector embeddings and agents"
        r1 = await client.post(f"{EDITORIAL_URL}/profile/score", json={"content_summary": summary})
        assert r1.status_code == 200
        prof_score = float(r1.json().get("profile_fit_score") or 0.0)
        assert 0.0 <= prof_score <= 1.0

        # 3) Topic Manager novelty check
        r2 = await client.post(
            f"{TOPIC_MANAGER_URL}/topics/novelty-check",
            json={"title": summary, "summary": summary},
        )
        assert r2.status_code == 200
        novelty_sim = float(r2.json().get("similarity_score") or 0.0)
        assert 0.0 <= novelty_sim <= 1.0

        # 4) Harvester selective triage (will promote if thresholds met)
        r3 = await client.post(
            f"{HARVESTER_URL}/triage/selective",
            params={"summary": summary, "content_type": "POST"},
        )
        assert r3.status_code == 200
        data3 = r3.json()
        assert "decision" in data3
        assert data3["decision"] in ["PROMOTE", "REJECT"]

        # 5) Reindex topics vector index (best-effort) and search
        await client.post(f"{TOPIC_MANAGER_URL}/topics/index/reindex", params={"limit": 50})
        r4 = await client.get(f"{TOPIC_MANAGER_URL}/topics/search", params={"q": "AI", "limit": 3})
        assert r4.status_code == 200
        assert "items" in r4.json()

        # 6) Check harvester status includes next_run_at
        r5 = await client.get(f"{HARVESTER_URL}/harvest/status")
        assert r5.status_code == 200
        assert "next_run_at" in r5.json()

        # 7) Check health reports dependencies and schedule
        r6 = await client.get(f"{HARVESTER_URL}/health")
        assert r6.status_code == 200
        h = r6.json()
        assert "dependencies" in h and "schedule" in h
