# Multi-Agent API Contract

This document defines the HTTP surface of the CrewAI Orchestrator and its
interaction with the Editorial Service and internal agent clients.

- Contract version: v0.2 (additive update)
- Target architecture alignment: see `target-version/COMPLETE_API_SPECIFICATIONS.md`
  and `target-version/VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md`

## 1. Agents

- research
- audience
- writer
- style
- quality

## 2. Validation Needs Declaration

Agents must declare:
- mode: `selective` | `comprehensive`
- platform: string (e.g., `linkedin`)
- content_type: string (e.g., `article`, `thread`)
- checkpoint (selective only): `pre-writing` | `mid-writing` | `post-writing`

## 3. Editorial Service Endpoints

- POST /validate/selective
  - payload: `{ content, platform, checkpoint, mode: "selective", context? }`
  - response: `{ mode: "selective", checkpoint, rules_applied: Rule[], rule_count, suggestions?, processing_time_ms, metadata }`

- POST /validate/comprehensive
  - payload: `{ content, platform, content_type, context? }`
  - response: `{ mode: "comprehensive", rules_applied: Rule[], rule_count, suggestions?, processing_time_ms, metadata }`

- GET /cache/stats
- GET /cache/dump
- POST /cache/refresh

## 4. Orchestrator Checkpoint API

- POST /checkpoints/create
  - payload: `{ content, platform, checkpoint: "pre_writing"|"mid_writing"|"post_writing", user_notes? }`
  - response: `{ checkpoint_id, status }`

- GET /checkpoints/status/{id}
  - response: `{ checkpoint_id, checkpoint, status, result?, created_at, updated_at, error_message? }`

- POST /checkpoints/{id}/intervene
  - payload: `{ user_input, finalize: boolean }`
  - response: `{ status, checkpoint_id }`

- POST /checkpoints/sequence/start
  - payload: `{ content, platform }`
  - response: `{ flow_id, status: "running" }`
- GET /checkpoints/sequence/status/{flow_id}
  - response: `{ flow_id, status: "running"|"completed"|"failed:...", current_step: string|null, checkpoints: string[] }`

Notes:
- Sequence tracking uses Redis when available (`REDIS_URL`).
  - `GET /health` exposes `sequence_ready: boolean` to indicate Redis connectivity.
  - Without Redis, sequence can start, but status metadata may be `unknown` and checkpoint list empty.

- GET /checkpoints/sequence/status/{flow_id}
  - response: `{ flow_id, status: "running"|"completed"|"failed:...", current_step: string|null, checkpoints: string[] }`

## 5. Flow Execution API

High-level, in-memory execution of the entire research→audience→writer→style→quality flow.

- POST /flows/execute
  - payload: `{ content: string, platform: string }`
  - response: `{ flow_id: string, state: "running" }`
- GET /flows/status/{flow_id}
  - response example:
    `{ flow_id, status: "running"|"completed"|"failed", current_agent: string|null, progress: number, chromadb_sourced: boolean, result?: object }`
- GET /flows/active
  - response: map of active flows to compact status

## 6. Response Envelope Standard

All service responses SHOULD include:
- `mode`: selective|comprehensive
- `rule_count`: number
- `rules_applied`: Rule[] (alias: `rules`)
- `suggestions`: string[] (optional)
- `processing_time_ms`: number (optional)
- `metadata`: object (optional)

For internal use, clients may normalize `rules_applied` to `rules` for convenience.

## 7. Headers

- `Authorization: Bearer <token>` (optional)
- `x-request-id: uuid` (recommended)

## 8. Error Handling

- 4xx/5xx errors returned as JSON with `detail` where possible.
- Clients should raise `EditorialServiceError` with actionable messages.
- Circuit breaker and retries (with jitter) recommended on client side.

Typical errors and status codes:
- 400: invalid payload shapes (non-JSON, wrong types)
- 401/403: missing/invalid auth where enforced
- 404: unknown `flow_id` or `checkpoint_id`
- 422: validation errors on required fields (e.g., missing `content` or `platform`)
- 500/502: upstream Editorial Service errors or internal exceptions
- 501: not implemented (legacy endpoints that may appear in docs but are not available)

## 9. Health and Environment

Environment variables:
- `EDITORIAL_SERVICE_URL`: base URL for Editorial Service (default `http://localhost:8040`)
- `REDIS_URL`: Redis connection string for checkpoint/sequence state (enables history and sequence metadata)
- `TRIAGE_POLICY_PATH`, `TRIAGE_POLICY_SCHEMA_PATH`: triage management endpoints

Health:
- `GET /health` returns
  `{ status, service, version, uptime_seconds, registered_agents, sequence_ready }`
  where `sequence_ready=true` indicates Redis connectivity.

## 10. Monitoring

- GET `/monitoring/agents/performance`
  - Returns performance metrics aggregated from internal agent clients

## 11. Examples

Start a sequence and poll status:

```bash
curl -s -X POST http://localhost:8042/checkpoints/sequence/start \
  -H 'Content-Type: application/json' \
  -d '{"content":"Test content","platform":"linkedin"}'

curl -s http://localhost:8042/checkpoints/sequence/status/<flow_id>
```

Create a single checkpoint and fetch status:

```bash
curl -s -X POST http://localhost:8042/checkpoints/create \
  -H 'Content-Type: application/json' \
  -d '{"content":"Test content","platform":"linkedin","checkpoint":"pre_writing"}'

curl -s http://localhost:8042/checkpoints/status/<checkpoint_id>
```

Execute full flow and check progress:

```bash
curl -s -X POST http://localhost:8042/flows/execute \
  -H 'Content-Type: application/json' \
  -d '{"content":"Test content","platform":"linkedin"}'

curl -s http://localhost:8042/flows/status/<flow_id>
```

## 12. Versioning

- This contract is v0.2 and may evolve. Additive changes only within minor.
