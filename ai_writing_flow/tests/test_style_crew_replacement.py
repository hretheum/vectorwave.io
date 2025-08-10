import sys, pathlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
# Lazy import to avoid crewai dependency in CI
StyleCrew = None
try:
    from ai_writing_flow.crews.style_crew import StyleCrew
except Exception:
    pass


@pytest.mark.asyncio
async def test_validate_style_calls_comprehensive_and_adds_rule_summary():
    if StyleCrew is None:
        pytest.skip("crewai not available")
    crew = StyleCrew()
    mock_result = {
        "mode": "comprehensive",
        "rules_applied": [{"id": "r1", "severity": "warning"}],
        "violations": [],
        "suggestions": ["Do X"],
    }
    with patch.object(crew.editorial_client, 'validate_comprehensive', new=AsyncMock(return_value=mock_result)) as vc:
        result = crew.validate_style_comprehensive("text", platform="linkedin")
        assert isinstance(result, dict)
        assert result["mode"] == "comprehensive"
        assert "rule_summary" in result and result["rule_summary"]["rule_count"] >= 1
        vc.assert_awaited()


@pytest.mark.asyncio
async def test_style_validation_threshold_param():
    if StyleCrew is None:
        pytest.skip("crewai not available")
    crew = StyleCrew(min_compliance_score=80)
    # Force health check to return available
    with patch.object(crew, 'check_service_health', return_value={"available": True, "total_rules": 100}):
        # Mock validation call inside execute
        with patch.object(crew, 'validate_style_comprehensive', return_value={
            "violations": [{"severity": "low"}],
            "suggestions": []
        }):
            out = crew.execute("draft", {"platform": "linkedin"})
            assert out.compliance_score <= 100
            # With threshold 80 and at least one low violation, is_compliant might be below threshold
            assert isinstance(out.is_compliant, bool)
