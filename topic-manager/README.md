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
- POST /topics/scrape — stub auto-scraping

### Vector Index (ChromaDB)

- GET /topics/index/info — returns collection name, readiness, total indexed, chromadb status
- POST /topics/index/reindex — reindex topics into `topics_index` (uses real embeddings if configured)
- GET /topics/search?q=...&limit=5 — vector search over topics index

## Configuration

Environment variables:

- CHROMADB_HOST (default: chromadb)
- CHROMADB_PORT (default: 8000)
- EMBEDDINGS_PROVIDER=openai
- OPENAI_API_KEY=... (required for real embeddings)
- OPENAI_EMBEDDING_MODEL=text-embedding-3-small

Docker Compose sets these for you; override via shell env if needed.

## Development

- Run tests: `pytest -q`
- Optional smoke test against real OpenAI (skipped by default):
  - `RUN_OPENAI_SMOKE=1 OPENAI_API_KEY=sk-... pytest -q tests/test_embeddings_smoke.py`
