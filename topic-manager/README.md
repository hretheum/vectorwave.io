# Topic Manager

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
