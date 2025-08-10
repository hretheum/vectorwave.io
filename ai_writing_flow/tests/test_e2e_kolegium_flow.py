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


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("CI") == "true", reason="requires local Editorial Service")
def test_e2e_partial_failure_quality(monkeypatch):
    if any(x is None for x in (WriterCrew, QualityCrew)):
        pytest.skip("crewai not available")
    writer = WriterCrew()
    quality = QualityCrew()

    # Produce a draft
    draft = writer.execute("SLOs", "LinkedIn", "technical", "research", 2, {"platform": "linkedin"})

    # Force Quality Crew to require human review via high controversy and poor value
    with patch.object(quality, 'check_controversy', return_value=0.9), \
         patch.object(quality, 'evaluate_value', return_value={
             "has_clear_takeaway": False,
             "provides_examples": False,
             "actionable_advice": False,
             "unique_perspective": False,
             "saves_reader_time": False,
         }), \
         patch.object(quality, 'assess_logical_flow', return_value={
             "structure_clear": False,
             "has_introduction": False,
             "has_conclusion": False,
             "logical_transitions": 0,
             "coherence_score": 0.3,
         }):
        assessment = quality.execute(draft.draft, [], {"platform": "linkedin", "content_type": "article"})
        assert assessment.is_approved is False
        assert assessment.requires_human_review is True
