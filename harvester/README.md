# Trend Harvester Service

### Cel Serwisu
Automatyczne i cykliczne pozyskiwanie danych o trendach, nowościach i publikacjach z zewnętrznych źródeł API. Serwis działa jako zautomatyzowany "lejek", który pobiera surowe informacje, normalizuje je, a następnie wykonuje lekki selektywny triage (ocena dopasowania profilu + nowości) poprzez wywołania `Editorial Service` i `Topic Manager`. Tylko najbardziej wartościowe i dopasowane do profilu tematy są "promowane" jako sugestie do `Topic Manager`.

### Kluczowe Technologie
- **Framework**: FastAPI
- **Harmonogram**: APScheduler
- **Baza Danych**: ChromaDB (dla kolekcji `raw_trends`)
- **Główne Biblioteki**: `httpx`, `pydantic`

### Kluczowe Funkcjonalności
- **Scheduler-Driven Fetching**: Automatyczne uruchamianie procesu pobierania danych w zdefiniowanych interwałach.
- **Multi-Source Ingestion**: Równoległe pobieranie danych z wielu skonfigurowanych źródeł (Hacker News, ArXiv, GitHub itp.).
- **Data Normalization**: Standaryzacja pozyskanych danych do wspólnego formatu `RawTrendItem`.
- **Selective Triage**: Lekki triage za pomocą endpointów `Editorial Service` (ocena profilu) i `Topic Manager` (novelty check), bez użycia wewnętrznych agentów.
- **Automated Promotion**: Przekazywanie tylko przefiltrowanych i ocenionych tematów do `Topic Manager` API.

### Uruchomienie i Testowanie
Serwis jest w pełni skonteneryzowany i zostanie zintegrowany z głównym plikiem `docker-compose.yml`.

1.  **Uruchomienie serwisu (w ramach `docker-compose`):**
    ```bash
    docker compose --profile harvester up -d
    ```
2.  **Ręczne wyzwolenie procesu:**
    ```bash
    curl -X POST http://localhost:8043/harvest/trigger
    ```

---

## Uproszczona Architektura (2025-08-13)

Bez skomplikowanych agentów i scraperów. Minimalny, deterministyczny pipeline:

1) Fetch → 2) Normalize → 3) Save → 4) Selective Triage → 5) Promote

```mermaid
flowchart LR
  subgraph Sources
    HN[Hacker News]
    ARXIV[ArXiv]
    DEVTO[Dev.to]
    NEWSD[NewsData.io]
    PH[Product Hunt]
  end

  HN & ARXIV & DEVTO & NEWSD & PH --> F[FetcherEngine]
  F --> N[Normalizer (RawTrendItem)]
  N --> S[(ChromaDB: raw_trends)]
  S --> T[Selective Triage]
  T --> ES[Editorial Service /profile/score]
  T --> TM1[Topic Manager /topics/novelty-check]
  T -->|PROMOTE| TM2[Topic Manager /topics/suggestion]
```

### Źródła danych (aktywnie używane)
- Hacker News (top stories)
- ArXiv (cs.AI, cs.LG, cs.CV)
- Dev.to (tagi: ai, machinelearning, llm)
- NewsData.io (global news; wymaga `NEWS_DATA_API_KEY`)
- Product Hunt (GraphQL v2; wymaga `PRODUCT_HUNT_DEVELOPER_TOKEN`)

### Endpointy API
- `GET /health` – status serwisu i zależności (ChromaDB, Editorial, Topic Manager)
- `POST /harvest/trigger?limit=N` – ręczne wyzwolenie cyklu (równoległy fetch, zapis, triage, opcjonalna promocja)
- `GET /harvest/status` – snapshot ostatniego przebiegu i `next_run_at`
- `GET /metrics` – metryki Prometheus

### Konfiguracja (env)
```bash
# Połączenia
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000
CHROMADB_COLLECTION=raw_trends

# Integracje
EDITORIAL_SERVICE_URL=http://editorial-service:8040
TOPIC_MANAGER_URL=http://topic-manager:8041
TOPIC_MANAGER_TOKEN=your_s2s_bearer_token

# Klucze do źródeł
DEV_TO_API_KEY=
NEWS_DATA_API_KEY=
PRODUCT_HUNT_DEVELOPER_TOKEN=

# Harmonogram (cron lub */N minut)
HARVEST_SCHEDULE_CRON="0 */6 * * *"

# Progi triage
SELECTIVE_PROFILE_THRESHOLD=0.7
SELECTIVE_NOVELTY_THRESHOLD=0.8
```

### Model danych: `RawTrendItem`
Minimalne pola: `title`, `summary?`, `url?`, `source`, `keywords[]`, `author?`, `published_at?`.
Zapisywane do kolekcji `raw_trends` w ChromaDB wraz z metadanymi statusu (`promoted`/`rejected`).

### Kontrakty integracyjne (Selective Triage)
- Editorial: `POST /profile/score { content_summary } → { profile_fit_score }`
- Topic Manager: `POST /topics/novelty-check { title, summary } → { similarity_score }` (novelty = `1 - similarity`)
- Topic Manager: `POST /topics/suggestion` z nagłówkami `Authorization: Bearer <token>` i `Idempotency-Key`

### Przykładowe wywołania
```bash
# Health
curl -s http://localhost:8043/health | jq

# Trigger (limit 10)
curl -s -X POST "http://localhost:8043/harvest/trigger?limit=10" | jq

# Status
curl -s http://localhost:8043/harvest/status | jq

# Metryki
curl -s http://localhost:8043/metrics
```
