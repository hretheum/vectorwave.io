# Kolegium — AI Writing Flow

ChromaDB‑centric writing workflow with agent crews and an HTTP client for the Editorial Service. No hardcoded editorial rules — all validations are sourced from Editorial Service.

## Components

- ai_writing_flow/clients/editorial_client.py
  - Async HTTP client with retries (exponential backoff + jitter), circuit breaker, per‑endpoint timeouts
  - Normalizes comprehensive responses (`rules`, `violations`, `suggestions`)
  - Env: `EDITORIAL_SERVICE_URL` (default `http://editorial-service:8040`)
- ai_writing_flow/clients/editorial_utils.py
  - `aggregate_rules(validation_result)` → `{rule_count, critical_count, score}`
- ai_writing_flow/crews/style_crew.py
  - Style Crew Replacement — ChromaDB‑only validation (comprehensive), `rule_summary`, parametric compliance threshold
- ai_writing_flow/crews/audience_crew.py, writer_crew.py, quality_crew.py
  - Integrations with Editorial Service (selective/comprehensive) and rule aggregation

## Editorial Service

- Health: `http://localhost:8040/health`
- Selective: `POST /validate/selective` (top‑level `checkpoint`)
- Comprehensive: `POST /validate/comprehensive`
- Cache: `GET /cache/stats`, `GET /cache/dump`, `POST /cache/refresh`

Set URL via env:

```bash
export EDITORIAL_SERVICE_URL=http://localhost:8040
```

## Running tests

Most tests are lightweight and do not require live services. Some tests (crews) skip automatically if `crewai` is not installed.

```bash
# From repository root
PYTHONPATH=kolegium/ai_writing_flow/src \
pytest -q kolegium/ai_writing_flow/tests
```

Run a focused test:

```bash
PYTHONPATH=kolegium/ai_writing_flow/src \
pytest -q kolegium/ai_writing_flow/tests/test_style_crew_replacement.py
```

## Notes

- Style Crew replacement uses only Editorial Service rules (ChromaDB). No hardcoded rule lists.
- Client supports optional `Authorization: Bearer <token>` and automatic `x-request-id` for observability.
- Circuit breaker prevents cascading failures; retries use exponential backoff with jitter.

## Playbooks (usage examples)

### Style Crew — comprehensive validation

```python
from ai_writing_flow.crews.style_crew import StyleCrew

crew = StyleCrew(editorial_service_url="http://localhost:8040", min_compliance_score=75)

draft = """Your draft content here..."""
styleguide = {"platform": "linkedin"}

result = crew.execute(draft, styleguide)
print(result.is_compliant, result.compliance_score)
for v in result.violations:
    print("-", v)
```

### Audience Crew — platform optimization

```python
from ai_writing_flow.crews.audience_crew import AudienceCrew

crew = AudienceCrew(editorial_service_url="http://localhost:8040")

topic = "AI agents for enterprise onboarding"
platform = "linkedin"
research_summary = "Key stats and insights..."
editorial_recs = "Be specific, avoid jargon..."

alignment = crew.execute(topic, platform, research_summary, editorial_recs)
print(alignment.recommended_depth, alignment.tone_calibration)
print(alignment.key_messages.get("technical_founder"))
```

### Writer Crew — selective validation with checkpoints

```python
from ai_writing_flow.crews.writer_crew import WriterCrew

crew = WriterCrew(editorial_service_url="http://localhost:8040")

topic = "Observability SLOs"
platform = "LinkedIn"
audience_insights = "technical, ROI"
research_summary = "collected sources..."
depth = 2
style_ctx = {"platform": "linkedin"}

draft = crew.execute(topic, platform, audience_insights, research_summary, depth, style_ctx)
print(draft.structure_type, draft.word_count)
```

### Quality Crew — comprehensive final check

```python
from ai_writing_flow.crews.quality_crew import QualityCrew

crew = QualityCrew(editorial_service_url="http://localhost:8040")

sources = [{"title": "Study 2024"}]
style_ctx = {"platform": "linkedin", "content_type": "article"}

assessment = crew.execute("final draft text", sources, style_ctx)
print(assessment.quality_score, assessment.is_approved)
for s in assessment.improvement_suggestions:
    print("-", s)
```
