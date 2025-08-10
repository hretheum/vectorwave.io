import sys, pathlib, os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

# Lazy import to avoid crewai hard dependency
try:
    from ai_writing_flow.crews.writer_crew import WriterCrew
    from ai_writing_flow.crews.style_crew import StyleCrew
    from ai_writing_flow.crews.audience_crew import AudienceCrew
    from ai_writing_flow.crews.quality_crew import QualityCrew
except Exception:
    WriterCrew = StyleCrew = AudienceCrew = QualityCrew = None


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires local Editorial Service")
def test_e2e_kolegium_happy_path(monkeypatch):
    if any(x is None for x in (WriterCrew, StyleCrew, AudienceCrew, QualityCrew)):
        pytest.skip("crewai not available")
    # Setup crews
    audience = AudienceCrew()
    writer = WriterCrew()
    style = StyleCrew()
    quality = QualityCrew()

    topic = "AI agents for enterprise onboarding"
    platform = "linkedin"
    research_summary = "Relevant stats and insights..."
    editorial_recs = "Avoid jargon. Be specific."

    # Audience alignment
    align = audience.execute(topic, platform, research_summary, editorial_recs)
    assert 0.0 <= align.technical_founder_score <= 1.0

    # Write
    draft = writer.execute(topic, platform.capitalize(), "technical, ROI", research_summary, align.recommended_depth, {"platform": platform})
    assert isinstance(draft.draft, str) and len(draft.draft) > 0

    # Style validation (will call Editorial Service if available)
    # Monkeypatch health if needed
    with patch.object(style, 'check_service_health', return_value={"available": True, "total_rules": 300}):
        style_result = style.execute(draft.draft, {"platform": platform})
        assert isinstance(style_result.compliance_score, (int, float))

    # Quality (final)
    quality_result = quality.execute(draft.draft, [], {"platform": platform, "content_type": "article"})
    assert isinstance(quality_result.quality_score, (int, float))


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires local Editorial Service")
def test_e2e_kolegium_dependency_unavailable(monkeypatch):
    if StyleCrew is None:
        pytest.skip("crewai not available")
    style = StyleCrew()
    with patch.object(style, 'check_service_health', return_value={"available": False, "error": "unreachable"}):
        result = style.execute("text", {"platform": "linkedin"})
        assert result.is_compliant is False
        assert any(v["type"] == "service_error" for v in result.violations)
