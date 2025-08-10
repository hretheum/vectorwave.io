# Multi-Agent API Contract (Draft)

This document defines the HTTP surface between CrewAI Orchestrator and Editorial/Topic services, and the internal agent clients. Version: v0.1.

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

## 5. Response Envelope Standard

All service responses SHOULD include:
- `mode`: selective|comprehensive
- `rule_count`: number
- `rules_applied`: Rule[] (alias: `rules`)
- `suggestions`: string[] (optional)
- `processing_time_ms`: number (optional)
- `metadata`: object (optional)

For internal use, clients may normalize `rules_applied` to `rules` for convenience.

## 6. Headers

- `Authorization: Bearer <token>` (optional)
- `x-request-id: uuid` (recommended)

## 7. Error Handling

- 4xx/5xx errors returned as JSON with `detail` where possible.
- Clients should raise `EditorialServiceError` with actionable messages.
- Circuit breaker and retries (with jitter) recommended on client side.

## 8. Versioning

- This contract is v0.1 and may evolve. Additive changes only within minor.
