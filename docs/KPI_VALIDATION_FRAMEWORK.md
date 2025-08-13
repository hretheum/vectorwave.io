# KPI & Validation Framework

Data: 2025-08-13
Scope: Standard KPIs and validation checklists for Vector Wave services.

## Purpose
- Align service-level goals and success metrics
- Provide a common validation checklist for docs and releases
- Reduce drift across service READMEs

## Global KPIs
- Health endpoints: 200 status; P95 latency targets defined per service
- Startup time: < 30s (services with external deps may vary)
- Error budgets: < 1% 5xx rate in dev; < 0.1% in prod-like
- Observability: logs structured; basic metrics exposed when applicable

## Service Categories

### Editorial/Validation Services (e.g., editorial-service)
- Validation performance: < 200ms per request (typical)
- Rule sourcing: 100% from ChromaDB (no hardcoded fallbacks)
- Health: P95 < 50ms
- Checklist additions: smoke for selective/comprehensive endpoints

### Topic/Index Services (e.g., topic-manager)
- Novelty/suggestion API: avg < 150ms
- Reindex: < 60s for 10k topics (local baseline)
- Health: P95 < 50ms

### Publishing/Orchestration (publisher)
- Health: P95 < 100ms
- Publish happy-path returns publication_id; status endpoint reflects progress
- Alert test endpoint produces a dev notification

### Content Generation (presenton, gamma)
- Health: P95 < 80ms
- Generation: typical 5–10 slides < 15s (local baseline)
- Quota/circuit breaker signals exposed in health where applicable

### Analytics (analytics-service)
- Health: P95 < 80ms
- ChromaDB: no error; required collections present
- Insights endpoint returns data_quality_score in [0, 1]

## Common Validation Checklist
- [ ] README includes: Overview, Quick Start, KPIs i Walidacja, References
- [ ] Health endpoint documented with example curl
- [ ] Port matches docs/integration/PORT_ALLOCATION.md
- [ ] Minimal smoke test commands provided
- [ ] Error handling and limitations documented or linked
- [ ] Links are relative and valid

## Release Checklist (Docs)
- [ ] Linter (scripts/docs_lint_readme.py) passes for all services
- [ ] Updated links to central KPIs framework where relevant
- [ ] Archived outdated documents and added references
