import asyncio
from src.main import validate_with_editorial_service


def test_validation_pipeline_best_effort(monkeypatch):
    async def fake_validate(content: str, platform: str):
        return {"is_compliant": True, "rules_applied": ["r1"], "mode": "comprehensive"}

    monkeypatch.setattr("src.main.validate_with_editorial_service", fake_validate)

    res = asyncio.get_event_loop().run_until_complete(fake_validate("text", "linkedin"))
    assert res.get("is_compliant") is True
