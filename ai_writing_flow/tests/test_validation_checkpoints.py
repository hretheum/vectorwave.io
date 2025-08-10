import pytest
import pytest_asyncio

from ai_writing_flow.validation_checkpoints import ValidationCheckpoints
from ai_writing_flow.clients.editorial_client import EditorialServiceClient


@pytest.mark.asyncio
async def test_validation_checkpoints_calls_selective_with_top_level_checkpoint(monkeypatch):
    called = []

    async def fake_validate_selective(self, content, platform, checkpoint="general", context=None):
        called.append({"content": content, "platform": platform, "checkpoint": checkpoint})
        # Simulate Editorial Service response
        return {"rule_count": 3, "passed": True, "rules_applied": [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]}

    monkeypatch.setattr(EditorialServiceClient, "validate_selective", fake_validate_selective, raising=False)

    vc = ValidationCheckpoints(base_url="http://localhost:8040")
    results = await vc.validate_all("Draft", "linkedin")

    checkpoints = [c["checkpoint"] for c in called]
    assert checkpoints == ["pre-writing", "mid-writing", "post-writing"]
    assert all(r["passed"] for r in results)
    assert all(r["rule_count"] == 3 for r in results)
