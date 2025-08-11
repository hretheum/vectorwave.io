import json
from fastapi.testclient import TestClient
from src.main import app, PlatformType, PlatformConfig

client = TestClient(app)

def test_end_to_end_schedule():
    payload = {
        "topic": {
            "title": "Test",
            "description": "Desc"
        },
        "platforms": {
            PlatformType.LINKEDIN.value: PlatformConfig(enabled=True, account_id="a").model_dump(),
            PlatformType.TWITTER.value: PlatformConfig(enabled=True, account_id="b").model_dump(),
        }
    }
    r = client.post("/publish", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("completed", "failed")
    assert isinstance(data["scheduled_jobs"], dict)
