# Topic Manager

## Cel
Aktywny serwis pomocniczy utrzymujący indeks tematów oraz integrujący się z Harvester i innymi usługami. Ocenia nowość tematów oraz przyjmuje sugestie z procesów zewnętrznych (np. Harvester). Nie posiada wbudowanych scraperów; pozyskiwanie danych realizuje Harvester. Domyślny port: 8041.

## Endpointy

### Lista
- `GET /health` — sprawdzenie stanu serwisu i połączenia z ChromaDB.
- `POST /topics/manual` — utworzenie tematu.
- `GET /topics` — lista tematów.
- `GET /topics/{topic_id}` — szczegóły tematu.
- `PUT /topics/{topic_id}` — aktualizacja tematu.
- `DELETE /topics/{topic_id}` — usunięcie tematu.
- `POST /topics/novelty-check` — ocena nowości tematu względem indeksu.
- `POST /topics/suggestion` — przyjęcie propozycji tematu (idempotentnie).
- `GET /topics/index/info` — diagnostyka wektorowego indeksu.
- `POST /topics/index/reindex` — ponowne indeksowanie tematów.
- `POST /topics/index/verify` — weryfikacja obecności ID w Chroma.
- `GET /topics/search` — wyszukiwanie wektorowe z filtrami.

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

### Vector Index (ChromaDB) – examples

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

# Vector search with title substring filter
curl -s 'http://localhost:8041/topics/search?q=AI&title_contains=OpenAI&limit=5' | jq .
```

## Konfiguracja

| Zmienna                    | Opis                                                    |
|---------------------------|---------------------------------------------------------|
| `SERVICE_PORT`            | Port HTTP (domyślnie 8041)                              |
| `TOPIC_DB` / `TOPIC_MANAGER_DB` | Lokalizacja bazy / indeksu                     |
| `AUTH_TOKEN` (opcjonalnie) | Token weryfikowany dla żądań przychodzących            |
| `CHROMADB_HOST`           | Host bazy Chroma (domyślnie `chromadb`)                  |
| `CHROMADB_PORT`           | Port Chroma (domyślnie `8000`)                           |
| `EMBEDDINGS_PROVIDER`     | Dostawca embeddingów (np. `openai`)                     |
| `OPENAI_API_KEY`          | Klucz API używany przy realnych embeddingach            |
| `OPENAI_EMBEDDING_MODEL`  | Model embeddingów (np. `text-embedding-3-small`)        |
| `INDEX_REINDEX_CRON`      | Harmonogram ponownego indeksowania (`*/10 * * * *`)     |

Docker Compose dostarcza domyślne wartości, które można nadpisać zmiennymi środowiskowymi.

## Testy

```bash
# Unit/integration
pytest -q

# Smoke test lokalnie
curl -f http://localhost:8041/health
curl -s -X POST -H "Content-Type: application/json" \
  http://localhost:8041/topics/novelty-check \
  -d '{"title":"Test topic", "summary":"Short"}' | jq .
KEY=$(uuidgen)
curl -s -X POST -H "Content-Type: application/json" -H "Idempotency-Key: $KEY" \
  http://localhost:8041/topics/suggestion \
  -d '{"title":"Test topic","source":"harvester"}' | jq .
```

Opcjonalny smoke test z prawdziwym OpenAI:

```bash
RUN_OPENAI_SMOKE=1 OPENAI_API_KEY=sk-... pytest -q tests/test_embeddings_smoke.py
```

## FAQ

- „Czy TM ma własne scrapowanie?” → Nie. Pozyskiwanie danych realizuje `Harvester`.
- „Jak uniknąć duplikatów?” → Używaj `Idempotency-Key` w `POST /topics/suggestion`.
- „Jak chronić endpointy?” → Włącz nagłówek `Authorization` i weryfikację tokena po stronie TM.

