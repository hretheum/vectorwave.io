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
