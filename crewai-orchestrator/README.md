# CrewAI Orchestrator

This service exposes orchestration endpoints for the Vector Wave platform.

## Key endpoints

- `GET /health` – healthcheck
- `POST /triage/seed` – batch pre-screening and promotion of topics using triage policy
- `GET /triage/policy` – get current applied policy (from `TRIAGE_POLICY_PATH`)
- `POST /triage/policy` – update policy (validated if `TRIAGE_POLICY_SCHEMA_PATH` is available)

## Configuration

The orchestrator reads its triage policy from a YAML file. Paths are configurable via environment variables.

- `TRIAGE_POLICY_PATH` (default `/app/config/triage_policy.yaml`) – YAML policy file
- `TRIAGE_POLICY_SCHEMA_PATH` (optional, default `/app/config/triage_policy.schema.json`) – JSON Schema to validate incoming `POST /triage/policy`
- `EDITORIAL_SERVICE_URL` – internal URL to Editorial Service
- `HARVESTER_URL` – internal URL to Harvester service (used by triage seeder)

These are already set in the root `docker-compose.yml`.

## Example: modifying the triage policy

1. Fetch current policy:

```bash
curl -s http://localhost:8042/triage/policy | yq -P
```

2. Update policy (validated against `config/triage_policy.schema.json` if present):

```bash
curl -s -X POST http://localhost:8042/triage/policy \
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
curl -s -X POST http://localhost:8042/triage/seed -H 'Content-Type: application/json' -d '{}'
```

or with overrides:

```bash
curl -s -X POST http://localhost:8042/triage/seed \
  -H 'Content-Type: application/json' \
  -d '{
    "policy_overrides": {"thresholds": {"profile_fit": 0.8}}
  }'
```

## Notes

- If `TRIAGE_POLICY_SCHEMA_PATH` is missing in the container, policy validation will be skipped.
- The service uses direct HTTP to ChromaDB to fetch raw trends.
