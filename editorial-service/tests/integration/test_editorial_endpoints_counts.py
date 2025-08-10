import os
import pytest
import httpx

BASE_URL = os.getenv("EDITORIAL_BASE_URL", "http://localhost:8040")

@pytest.mark.asyncio
async def test_selective_returns_3_to_4_rules():
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "content": "Plan audience and structure before writing",
            "mode": "selective",
            "checkpoint": "pre-writing",
            "platform": "linkedin",
        }
        resp = await client.post(f"{BASE_URL}/validate/selective", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("mode") == "selective"
        assert data.get("checkpoint") == "pre-writing"
        rules_count = len(data.get("rules_applied", []))
        assert 3 <= rules_count <= 4, f"expected 3-4 rules, got {rules_count}"

@pytest.mark.asyncio
async def test_comprehensive_returns_8_to_12_rules():
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "content": "Plan audience and structure before writing",
            "mode": "comprehensive",
            "platform": "linkedin",
        }
        resp = await client.post(f"{BASE_URL}/validate/comprehensive", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("mode") == "comprehensive"
        rules_count = len(data.get("rules_applied", []))
        assert 8 <= rules_count <= 12, f"expected 8-12 rules, got {rules_count}"
