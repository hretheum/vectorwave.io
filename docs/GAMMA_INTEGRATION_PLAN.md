# Gamma Integration Plan

Date: 2025-08-13
Scope: Define minimal, actionable plan to integrate Gamma.app with Publisher.

## Status
- Plan drafted and aligned with current architecture
- Service `gamma-ppt-generator` docs available and up to date
- Ready for implementation behind Publisher toggle with fallback

## Objectives
- MVP service endpoints in `gamma-ppt-generator`:
  - GET /health (200 when ready)
  - POST /generate (payload: topic, slides_count, theme; returns { job_id or file })
- Publisher toggle + fallback:
  - When `GAMMA_ENABLED=true`, Publisher uses Gamma client for presentation generation
  - Else fallback to Presenton
- Contract tests and configuration notes

## Service (gamma-ppt-generator)
- Port: 8003
- Env:
  - `GAMMA_API_KEY` (opt. for real mode)
  - `SERVICE_PORT=8003`
- Endpoints:
  - `GET /health` → `{ status: healthy }`
  - `POST /generate` → `{ id, status }` or direct file link
- Demo mode: allow run without API key with mocked responses

## Requirements
- Environment
  - `GAMMA_API_KEY` set for production mode (keep secret, do not commit)
  - `SERVICE_PORT=8003`
  - `HOST=0.0.0.0`
- Contracts
  - Health returns 200 with JSON including `status`, `version`, `port`
  - Generate accepts: `topic{title,description,keywords,target_audience}`, `slides_count`, `theme`, `output_formats`
  - Cost/rate constraints respected (beta limit ~50/month)
- Security
  - Bearer token placeholder; JWT to be added later
- Observability
  - Health includes circuit breaker and usage where applicable

## Publisher changes
- Add env: `GAMMA_ENABLED=true|false` (default: false)
- Add GammaClient (base URL from compose or env): `GAMMA_URL=http://gamma-ppt-generator:8003`
- In presentation generation path, branch by `GAMMA_ENABLED`:
  - true → call `POST {GAMMA_URL}/generate`
  - false → use Presenton as today

## Test plan
- docker compose --profile gamma up -d
- curl http://localhost:8003/health (expect 200)
- curl -X POST http://localhost:8003/generate (sample payload)
- Publisher dry-run with `GAMMA_ENABLED=true` and verify calling Gamma
- Publisher dry-run with `GAMMA_ENABLED=false` and verify fallback to Presenton

## References
- kolegium/gamma-ppt-generator/README.md (service docs)
- publisher/README.md (toggle & fallback section to add)
  
