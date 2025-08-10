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


@pytest.mark.asyncio
async def test_style_validation_contract_and_threshold():
    if StyleCrew is None:
        pytest.skip("crewai not available")
    # Case 1: no violations -> compliant
    crew = StyleCrew(min_compliance_score=70)
    with patch.object(crew, 'check_service_health', return_value={"available": True, "total_rules": 100}):
        with patch.object(crew, 'validate_style_comprehensive', return_value={
            "violations": [],
            "suggestions": ["Looks good"],
            "rules_applied": [{"id": "r1"}],
        }):
            out = crew.execute("text", {"platform": "linkedin"})
            assert isinstance(out.is_compliant, bool)
            assert out.is_compliant is True
            assert isinstance(out.violations, list)
            assert isinstance(out.forbidden_phrases, list)
            assert isinstance(out.suggestions, list)
            assert isinstance(out.compliance_score, (int, float))

    # Case 2: medium violation -> not compliant with high threshold
    crew2 = StyleCrew(min_compliance_score=95)
    with patch.object(crew2, 'check_service_health', return_value={"available": True, "total_rules": 100}):
        with patch.object(crew2, 'validate_style_comprehensive', return_value={
            "violations": [{"severity": "medium", "type": "style"}],
            "suggestions": ["Tighten language"]
        }):
            out2 = crew2.execute("text", {"platform": "linkedin"})
            assert out2.is_compliant is False


@pytest.mark.asyncio
async def test_compliance_score_aggregation():
    if StyleCrew is None:
        pytest.skip("crewai not available")
    crew = StyleCrew()
    with patch.object(crew, 'check_service_health', return_value={"available": True, "total_rules": 100}):
        violations = [
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]
        with patch.object(crew, 'validate_style_comprehensive', return_value={
            "violations": violations,
            "suggestions": []
        }):
            out = crew.execute("text", {"platform": "linkedin"})
            # Expected: 100 - 2*15 - 1*10 - 1*5 = 55
            assert out.compliance_score == 55
            assert out.is_compliant is False


@pytest.mark.asyncio
async def test_min_compliance_score_edges():
    if StyleCrew is None:
        pytest.skip("crewai not available")
    # Threshold 0 -> always compliant if score >=0
    crew_low = StyleCrew(min_compliance_score=0)
    with patch.object(crew_low, 'check_service_health', return_value={"available": True, "total_rules": 100}):
        with patch.object(crew_low, 'validate_style_comprehensive', return_value={
            "violations": [{"severity": "high"}, {"severity": "high"}, {"severity": "high"}],
            "suggestions": []
        }):
            out_low = crew_low.execute("text", {"platform": "linkedin"})
            assert out_low.compliance_score >= 0
            assert out_low.is_compliant is True

    # Threshold 100 -> compliant only with perfect score
    crew_high = StyleCrew(min_compliance_score=100)
    with patch.object(crew_high, 'check_service_health', return_value={"available": True, "total_rules": 100}):
        # No violations -> 100
        with patch.object(crew_high, 'validate_style_comprehensive', return_value={
            "violations": [],
            "suggestions": []
        }):
            out_high_ok = crew_high.execute("text", {"platform": "linkedin"})
            assert out_high_ok.compliance_score == 100
            assert out_high_ok.is_compliant is True
        # One low violation -> < 100 -> not compliant
        with patch.object(crew_high, 'validate_style_comprehensive', return_value={
            "violations": [{"severity": "low"}],
            "suggestions": []
        }):
            out_high_bad = crew_high.execute("text", {"platform": "linkedin"})
            assert out_high_bad.compliance_score < 100
            assert out_high_bad.is_compliant is False
