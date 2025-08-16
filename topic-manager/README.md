# Topic Manager

## Cel
Aktywny serwis pomocniczy do zarządzania indeksem tematów oraz oceny ich nowości. Integruje się z `Harvester` i innymi usługami poprzez proste endpointy HTTP. Domyślny port: **8041**.

Najważniejsze fakty:
- Brak endpointu `/topics/scrape` – pozyskiwanie źródeł realizuje `Harvester`.
- Zapewnione są dwa kluczowe endpointy:
  - `POST /topics/novelty-check` – ocena „nowości” tematu w kontekście istniejącego indeksu.
  - `POST /topics/suggestion` – idempotentne przyjęcie propozycji tematu do indeksu.
- Integracja z `ChromaDB`/wektorowym indeksem.

### Integracja z Harvester
1. `Harvester` pobiera kandydatów tematów z zewnętrznych źródeł.
2. Dla każdego kandydata:
   - wywołuje `Editorial Service` (ocena profilu/strategii),
   - wywołuje `Topic Manager /topics/novelty-check` (ocena nowości),
   - przy spełnieniu kryteriów wysyła `POST /topics/suggestion` z nagłówkiem `Idempotency-Key`.

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
- Z nagłówkiem `Idempotency-Key` ponowne wysłanie tego samego żądania nie tworzy duplikatów.
- Jeśli serwis jest skonfigurowany na przyjmowanie tylko autoryzowanych żądań, dodaj `Authorization: Bearer <token>`.

## Konfiguracja

- Health: `GET /health` powinien zwracać 200.
- Port: 8041 (zgodny z `docs/integration/PORT_ALLOCATION.md`).

Zmienna | Opis
---|---
`SERVICE_PORT` | Port HTTP (domyślnie 8041)
`TOPIC_DB` lub `INDEX` | Lokalizacja bazy / indeksu
`AUTH_TOKEN` (opcjonalnie) | Token weryfikowany dla żądań przychodzących

## Testy
- Uruchom testy jednostkowe: `pytest -q`.
- Test dymny (lokalnie):
```bash
# 1) Health
curl -f http://localhost:8041/health

# 2) Novelty check
docker compose exec topic-manager curl -s -X POST -H "Content-Type: application/json" \
  http://localhost:8041/topics/novelty-check \
  -d '{"title":"Test topic", "summary":"Short"}' | jq .

# 3) Suggestion (idempotent)
KEY=$(uuidgen)
docker compose exec topic-manager curl -s -X POST -H "Content-Type: application/json" -H "Idempotency-Key: $KEY" \
  http://localhost:8041/topics/suggestion \
  -d '{"title":"Test topic","source":"harvester"}' | jq .
```

## FAQ
- „Czy TM ma własne scrapowanie?” → Nie. Pozyskiwanie danych realizuje `Harvester`.
- „Jak uniknąć duplikatów?” → Używaj `Idempotency-Key` w `POST /topics/suggestion`.
- „Jak chronić endpointy?” → Włącz nagłówek `Authorization` i weryfikację tokena po stronie TM.
