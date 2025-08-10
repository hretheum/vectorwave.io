import sys, pathlib, asyncio
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from main import app


@pytest.mark.asyncio
async def test_crud_endpoints_async():
    # Fallback to sync client for compatibility in this env
    ac = TestClient(app)
    try:
        # Create
        payload = {"title": "Async", "description": "D", "keywords": ["ai"], "content_type": "POST"}
        r = ac.post("/topics/manual", json=payload)
        assert r.status_code == 200
        tid = r.json()["topic_id"]

        # Get
        r = ac.get(f"/topics/{tid}")
        assert r.status_code == 200
        assert r.json()["title"] == "Async"

        # Update
        upd = {**payload, "description": "Dx"}
        r = ac.put(f"/topics/{tid}", json=upd)
        assert r.status_code == 200
        assert r.json()["status"] == "updated"

        # Delete
        r = ac.delete(f"/topics/{tid}")
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

        # Not found
        r = ac.get(f"/topics/{tid}")
        assert r.status_code == 200
        assert r.json().get("error") == "not_found"
    finally:
        ac.close()


@pytest.mark.asyncio
async def test_suggestions_endpoint_async():
    ac = TestClient(app)
    try:
        r = ac.get("/topics/suggestions?limit=3")
        assert r.status_code == 200
        data = r.json()
        assert "suggestions" in data and len(data["suggestions"]) == 3
    finally:
        ac.close()
