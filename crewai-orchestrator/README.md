# CrewAI Orchestrator

This service exposes orchestration endpoints for the Vector Wave platform.

## Key endpoints

- `GET /health` – healthcheck (fields: `status`, `service`, `version`, `uptime_seconds`, `registered_agents`, `sequence_ready`)
- `POST /checkpoints/create` – utworzenie checkpointu (pre_writing|mid_writing|post_writing)
- `GET /checkpoints/status/{id}` – status pojedynczego checkpointu
- `POST /checkpoints/{id}/intervene` – interwencja użytkownika i rewalidacja
- `GET /checkpoints/history/{id}` – historia zdarzeń checkpointu (persisted w Redis)
- `POST /checkpoints/sequence/start` – uruchamia sekwencję pre→mid→post dla podanego contentu
- `GET /checkpoints/sequence/status/{flow_id}` – status sekwencji i lista checkpointów
- `POST /flows/execute` – uruchamia pełny przepływ research→audience→writer→style→quality (in‑memory)
- `GET /flows/status/{flow_id}` – status przepływu (progress, current_agent, chromadb_sourced, result)
- `GET /flows/active` – lista aktywnych przepływów w formie skróconej
- `POST /triage/seed` and `POST /api/triage/seed` – batch pre-screening and promotion of topics using triage policy
- `GET /triage/policy` and `GET /api/triage/policy` – get current applied policy (from `TRIAGE_POLICY_PATH`)
- `POST /triage/policy` and `POST /api/triage/policy` – update policy (validated if `TRIAGE_POLICY_SCHEMA_PATH` is available)

## Configuration

The orchestrator reads its triage policy from a YAML file. Paths are configurable via environment variables.

- `TRIAGE_POLICY_PATH` (default `/app/config/triage_policy.yaml`) – YAML policy file
- `TRIAGE_POLICY_SCHEMA_PATH` (optional, default `/app/config/triage_policy.schema.json`) – JSON Schema to validate incoming `POST /triage/policy`
- `EDITORIAL_SERVICE_URL` – internal URL to Editorial Service
- `HARVESTER_URL` – internal URL to Harvester service (used by triage seeder)
- `REDIS_URL` – opcjonalny URL do Redis; jeśli ustawiony, stany checkpointów i historia są persystowane. Health zawiera `sequence_ready` (true jeśli połączenie z Redis OK).
## Examples

Start sequence and poll status:

```bash
curl -s -X POST http://localhost:8042/checkpoints/sequence/start \
  -H 'Content-Type: application/json' \
  -d '{"content":"Your content","platform":"linkedin"}'

curl -s http://localhost:8042/checkpoints/sequence/status/<flow_id> | jq .
```

Execute full flow and check progress:

```bash
curl -s -X POST http://localhost:8042/flows/execute \
  -H 'Content-Type: application/json' \
  -d '{"content":"Your content","platform":"linkedin"}'

curl -s http://localhost:8042/flows/status/<flow_id> | jq .
```

Common errors:

- 422 Unprocessable Entity – brak `content` lub `platform`
- 404 Not Found – nieznany `flow_id` lub `checkpoint_id`
- 501 Not Implemented – funkcja niedostępna w danym buildzie


These are already set in the root `docker-compose.yml`.

## Example: modifying the triage policy

1. Fetch current policy (alias under `/api` also works):

```bash
curl -s http://localhost:8042/api/triage/policy | yq -P
```

2. Update policy (validated against `config/triage_policy.schema.json` if present):

```bash
curl -s -X POST http://localhost:8042/api/triage/policy \
  -H 'Content-Type: application/json' \
  -d '{
    "version": 1,
    "lookback_hours": 48,
    "limits": {"max_total": 50, "max_per_source": {"hacker-news": 30}},
    "thresholds": {"profile_fit": 0.7, "novelty_sim_jaccard": 0.3, "title_min_len": 10},
    "promote": {"top_k": 20}
  }'
```

3. Run seeding with the currently stored policy (or override inline):

```bash
curl -s -X POST http://localhost:8042/api/triage/seed -H 'Content-Type: application/json' -d '{}'
```

or with overrides:

```bash
curl -s -X POST http://localhost:8042/api/triage/seed \
  -H 'Content-Type: application/json' \
  -d '{
    "policy_overrides": {"thresholds": {"profile_fit": 0.8}}
  }'
```

## Notes

- If `TRIAGE_POLICY_SCHEMA_PATH` is missing in the container, policy validation will be skipped.
- The service uses direct HTTP to ChromaDB to fetch raw trends (via Harvester selection flow).
- Compose injects: `EDITORIAL_SERVICE_URL`, `HARVESTER_URL`, `TRIAGE_POLICY_PATH`, `TRIAGE_POLICY_SCHEMA_PATH`.

## Smoke: sequence API

With the stack up (redis, editorial-service, orchestrator):

```bash
bash scripts/smoke_sequence.sh
# or customize:
ORCH_URL=http://localhost:8042 CONTENT="Your content" PLATFORM=linkedin bash scripts/smoke_sequence.sh
```
