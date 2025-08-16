import asyncio
import os
import pytest

from crewai_orchestrator.src.agent_clients import AgentHTTPClient


@pytest.mark.asyncio
async def test_with_retries_transient_timeout(monkeypatch):
    client = AgentHTTPClient("research", editorial_service_url="http://localhost:8040")

    attempts = {"n": 0}

    class DummyTimeout(Exception):
        pass

    async def flaky():
        attempts["n"] += 1
        if attempts["n"] < 2:
            # First call fails
            raise DummyTimeout()
        return {"ok": True}

    # Monkeypatch httpx timeout class detection by mapping DummyTimeout to httpx.TimeoutException
    import crewai_orchestrator.src.agent_clients as ac

    original_check = ac.httpx.TimeoutException
    try:
        ac.httpx.TimeoutException = DummyTimeout  # type: ignore
        res = await client._with_retries(flaky)
        assert res == {"ok": True}
        assert attempts["n"] == 2
    finally:
        ac.httpx.TimeoutException = original_check  # type: ignore


