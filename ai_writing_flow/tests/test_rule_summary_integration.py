import json
import pytest
import pytest_asyncio

# Import crew modules lazily to avoid hard dependency on crewai in CI profile



@pytest.fixture
def sample_validation_result():
    return {
        "rules_applied": [
            {"id": "r1", "severity": "warning"},
            {"id": "r2", "severity": "critical"},
            {"id": "r3", "severity": "info"},
        ],
        "violations": [
            {"id": "v1", "severity": "critical", "description": "Critical issue"},
            {"id": "v2", "severity": "warning", "description": "Minor issue"},
        ],
        "suggestions": ["Do X", "Do Y"],
        "rule_count": 3,
        "mode": "comprehensive",
    }


@pytest.mark.asyncio
async def test_style_crew_adds_rule_summary(monkeypatch, sample_validation_result):
    try:
        from ai_writing_flow.crews.style_crew import StyleCrew
    except Exception:
        pytest.skip("crewai dependency not available")
    crew = StyleCrew()

    async def mock_validate_comprehensive(*args, **kwargs):
        return dict(sample_validation_result)

    monkeypatch.setattr(crew.editorial_client, "validate_comprehensive", mock_validate_comprehensive)

    result = crew.validate_style_comprehensive("text", platform="general")
    assert isinstance(result, dict)
    assert "rule_summary" in result
    assert result["rule_summary"]["rule_count"] == 3
    assert result["rule_summary"]["critical_count"] == 1


@pytest.mark.asyncio
async def test_quality_crew_adds_rule_summary(monkeypatch, sample_validation_result):
    try:
        from ai_writing_flow.crews.quality_crew import QualityCrew
    except Exception:
        pytest.skip("crewai dependency not available")
    crew = QualityCrew()

    async def mock_validate_comprehensive(*args, **kwargs):
        return dict(sample_validation_result)

    monkeypatch.setattr(crew.editorial_client, "validate_comprehensive", mock_validate_comprehensive)

    result_json = crew.validate_comprehensive_quality("text", platform="general")
    result = json.loads(result_json)
    assert "rule_summary" in result
    assert result["rule_summary"]["rule_count"] == 3


@pytest.mark.asyncio
async def test_audience_crew_adds_rule_summary(monkeypatch, sample_validation_result):
    try:
        from ai_writing_flow.crews.audience_crew import AudienceCrew
    except Exception:
        pytest.skip("crewai dependency not available")
    crew = AudienceCrew()

    async def mock_validate_comprehensive(*args, **kwargs):
        return dict(sample_validation_result)

    monkeypatch.setattr(crew.editorial_client, "validate_comprehensive", mock_validate_comprehensive)

    result_json = crew.validate_platform_optimization("text", platform="linkedin", target_audience="technical_founder")
    result = json.loads(result_json)
    assert "rule_summary" in result
    assert result["rule_summary"]["critical_count"] == 1


@pytest.mark.asyncio
async def test_writer_crew_adds_rule_summary(monkeypatch):
    try:
        from ai_writing_flow.crews.writer_crew import WriterCrew
    except Exception:
        pytest.skip("crewai dependency not available")
    crew = WriterCrew()

    async def mock_validate_selective(*args, **kwargs):
        return {
            "rules_applied": [{"id": "r1", "severity": "warning"}, {"id": "r2", "severity": "warning"}],
            "violations": [{"id": "v1", "severity": "warning"}],
            "rule_count": 2,
            "mode": "selective",
        }

    monkeypatch.setattr(crew.editorial_client, "validate_selective", mock_validate_selective)

    result_json = crew.validate_selective("text", platform="linkedin", checkpoint="mid-writing")
    result = json.loads(result_json)
    assert "rule_summary" in result
    assert result["rule_summary"]["rule_count"] == 2
