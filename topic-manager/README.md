# Topic Manager

Status: aktywny serwis pomocniczy (bez wbudowanych scraperów) – integruje się z Harvester i innymi usługami poprzez proste endpointy HTTP. Port domyślny: 8041.

## Cel
- Utrzymywanie indeksu tematów oraz obsługa kontroli nowości i przyjmowania sugestii tematów z zewnętrznych procesów (np. `Harvester`).

## Najważniejsze fakty
- Brak endpointu `/topics/scrape` – pozyskiwanie źródeł realizuje `Harvester`.
- Zapewnione są dwa kluczowe endpointy:
  - `POST /topics/novelty-check` – ocena „nowości” tematu w kontekście istniejącego indeksu.
  - `POST /topics/suggestion` – przyjęcie propozycji tematu (idempotentnie) do indeksu.
- Integracja z `ChromaDB`/wektorowym indeksem – szczegóły implementacyjne zależne od wersji.

## Endpointy

### POST /topics/novelty-check
Żądanie (przykład):

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  ${TOPIC_MANAGER_URL:-http://localhost:8041}/topics/novelty-check \
  -d '{
    "title": "Vector database observability",
    "summary": "Observability patterns for vector DBs in production"
  }'
```

Odpowiedź (przykład):

```json
{
  "noveltyScore": 0.83,
  "similarItems": [
    { "id": "t_123", "title": "Vector DB metrics 101", "similarity": 0.78 }
  ]
}
```

Zastosowanie: używane przez `Harvester` do selektywnego triage (profil dopasowania + nowość) przed „promocją” tematu.

### POST /topics/suggestion
Żądanie (przykład z idempotency):

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  ${TOPIC_MANAGER_URL:-http://localhost:8041}/topics/suggestion \
  -d '{
    "title": "Vector database observability",
    "source": "harvester",
    "metadata": {"seed": "trends:2025-08-13"}
  }'
```

Odpowiedź (przykład):

```json
{
  "accepted": true,
  "id": "t_456",
  "status": "queued"
}
```

Uwagi:
- Jeżeli nagłówek `Idempotency-Key` jest dostarczony, ponowne wysłanie tego samego żądania nie powinno tworzyć duplikatów.
- Jeśli serwis jest skonfigurowany na przyjmowanie tylko autoryzowanych żądań, dodaj `Authorization: Bearer <token>`.

## Integracja z Harvester

Typowy przepływ:
1. `Harvester` pobiera kandydatów tematów z zewnętrznych źródeł.
2. Dla każdego kandydata:
   - wywołuje `Editorial Service` (ocena profilu/strategii),
   - wywołuje `Topic Manager /topics/novelty-check` (ocena nowości),
   - jeśli spełnione kryteria – wysyła `POST /topics/suggestion` z `Idempotency-Key`.

## Zdrowie i porty

- Health: `GET /health` (jeśli włączony) powinien zwracać 200.
- Port: 8041 (spójny z `docs/integration/PORT_ALLOCATION.md`).

## Konfiguracja (przykładowo)

Zmienna | Opis
---|---
`SERVICE_PORT` | Port HTTP (domyślnie 8041)
`TOPIC_DB` lub `INDEX` | Lokalizacja bazy / indeksu
`AUTH_TOKEN` (opcjonalnie) | Token weryfikowany dla żądań przychodzących

## Test dymny (lokalnie)

```bash
# 1) Health
curl -f http://localhost:8041/health

# 2) Novelty check
curl -s -X POST -H "Content-Type: application/json" \
  http://localhost:8041/topics/novelty-check \
  -d '{"title":"Test topic", "summary":"Short"}' | jq .

# 3) Suggestion (idempotent)
KEY=$(uuidgen)
curl -s -X POST -H "Content-Type: application/json" -H "Idempotency-Key: $KEY" \
  http://localhost:8041/topics/suggestion \
  -d '{"title":"Test topic","source":"harvester"}' | jq .
```

## FAQ

- „Czy TM ma własne scrapowanie?” → Nie. Pozyskiwanie danych realizuje `Harvester`.
- „Jak uniknąć duplikatów?” → Używaj `Idempotency-Key` w `POST /topics/suggestion`.
- „Jak chronić endpointy?” → Włącz nagłówek `Authorization` i weryfikację tokena po stronie TM.


Service for topic management, discovery, and vector search.

## Endpoints

- GET /health — includes embeddings readiness/provider and Chroma heartbeat
- POST /topics/manual — create a topic
- GET /topics — list topics
- GET /topics/{topic_id} — get topic
- PUT /topics/{topic_id} — update topic
- DELETE /topics/{topic_id} — delete topic
- POST /topics/suggestion — idempotent ingestion (requires Bearer + Idempotency-Key)
- POST /topics/novelty-check — S2S duplicate check (requires Bearer)

### Vector Index (ChromaDB)

- GET /topics/index/info — returns readiness and diagnostics (total_topics, last_indexed, index_coverage, chroma_reported_count)
- POST /topics/index/reindex — reindex topics into `topics_index` (uses real embeddings if configured)
- POST /topics/index/verify — verify presence of a sample of topic IDs in Chroma
- GET /topics/search?q=...&limit=5[&content_type=POST][&title_contains=AI] — vector search with optional filters

#### Examples

```bash
# Info and diagnostics
curl -s http://localhost:8041/topics/index/info | jq .

# Reindex 200 topics (no reset)
curl -s -X POST 'http://localhost:8041/topics/index/reindex?limit=200' | jq .

# Reset and reindex from scratch
curl -s -X POST 'http://localhost:8041/topics/index/reindex?limit=200&reset=true' | jq .

# Verify presence of a sample of topic IDs in Chroma (sample of 10)
curl -s -X POST 'http://localhost:8041/topics/index/verify?sample_size=10' | jq .

# Vector search (top 5)
curl -s 'http://localhost:8041/topics/search?q=AI&limit=5' | jq .

# Vector search filtered by content_type
curl -s 'http://localhost:8041/topics/search?q=AI&content_type=POST&limit=5' | jq .

# Vector search with title substring filter (post-filter)
curl -s 'http://localhost:8041/topics/search?q=AI&title_contains=OpenAI&limit=5' | jq .
```

## Configuration

Environment variables:

- CHROMADB_HOST (default: chromadb)
- CHROMADB_PORT (default: 8000)
- EMBEDDINGS_PROVIDER=openai
- OPENAI_API_KEY=... (required for real embeddings)
- OPENAI_EMBEDDING_MODEL=text-embedding-3-small
- TOPIC_MANAGER_DB=/data/topics.db (when running in Docker)
- INDEX_REINDEX_CRON="*/10 * * * *" (background reindex interval in minutes; format */N)

Docker Compose sets these for you; override via shell env if needed.

### Persistence & Background reindex

- Docker volume `topic_manager_data` is mounted to `/data` in the container to persist the SQLite database.
- On startup, a background task triggers reindex every N minutes (default 10). You can override via `INDEX_REINDEX_CRON`.

## Development

- Run tests: `pytest -q`
- Optional smoke test against real OpenAI (skipped by default):
  - `RUN_OPENAI_SMOKE=1 OPENAI_API_KEY=sk-... pytest -q tests/test_embeddings_smoke.py`
