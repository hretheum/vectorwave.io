# Service README Template

Use this template to standardize documentation across all Vector Wave services.

## 1) Overview
- One-paragraph description of the service (purpose, scope)
- Current status (e.g., prototype, MVP, production-ready)
- Ownership (team/owner)

## 2) Architecture
- Core components and their responsibilities
- Dependencies (internal services, external APIs)
- Ports and processes
- Diagram (optional)

## 3) Quick Start
- Prerequisites
- Local run (Docker and direct)
- Health check command
- Links to API docs (/docs)

## 4) Configuration
- Environment variables (table with name, required, description, example)
- Profiles/feature flags (e.g., GAMMA_ENABLED)
- Secrets handling guidelines

## 5) API Endpoints
- Summary list with method/path and short description
- Example requests/responses for the main endpoints
- Error model and common status codes

## 6) Health, Monitoring, Metrics
- /health response format and dependency checks
- Observability (logs, metrics, dashboards)
- Rate limits/session health (if applicable)

## 7) Data and Storage
- Databases/collections/buckets used
- Data retention and privacy notes

## 8) Testing
- Unit/integration/E2E commands
- Minimal manual validation steps

## 9) Troubleshooting
- Common issues and fixes
- Playbooks for degraded modes/circuit breakers

## 10) KPIs and Validation
- Service-specific KPIs and acceptance criteria
- Validation checklist (copy from VW-37 once available)

## 11) Roadmap and Status
- Current limitations
- Next steps / backlog links

## 12) References
- Links to related docs (CONTEXT, plans, specs)
