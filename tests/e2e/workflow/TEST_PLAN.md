# E2E User Workflow Test Plan

## Scope

Covers both workflows: AI Writing Flow (selective validation) and Kolegium (comprehensive validation). Exercises UI → Orchestrator → Editorial Service → Topic Manager interactions.

## Scenarios

1. Topic discovery and selection
- Precondition: Topic Manager running with /topics/search
- Steps: Search topics → pick one with highest score → assign platforms (LI, TW)
- Expected: Selection payload is built with topic metadata

2. Draft generation and validation (AI Writing Flow)
- Pre: Editorial Service up
- Steps: Generate initial draft → run selective validation at pre/mid/post → apply suggestions
- Expected: At least one validation response with rules_applied > 0

3. Publishing orchestration (multi-platform)
- Pre: Orchestrator up
- Steps: POST /publish with LI+TW → (optional) Presentor invoked for long/technical content
- Expected: publication_id generated, scheduled_jobs per platform

4. Manual upload package (LinkedIn)
- Pre: Orchestrator up; Presentor optional
- Steps: Read publication response for `linkedin_manual_upload`
- Expected: Checklist provided; assets present when presentation generated

5. Analytics & preferences
- Steps: POST /analytics/track; PUT/GET /preferences/{user}
- Expected: Track returns status=tracked; Preferences persist in memory

## Data
- Topic query: "AI"
- Platforms: linkedin, twitter
- Content seed: "AI agents transform development workflows by..."

## Teardown
- In-memory stores; no teardown required

## Idempotency
- Publication requests are independent; test may re-run without conflicts
