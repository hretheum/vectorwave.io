# Trend Harvester Service

### Cel Serwisu
Automatyczne i cykliczne pozyskiwanie danych o trendach, nowościach i publikacjach z zewnętrznych źródeł API. Serwis działa jako zautomatyzowany "lejek", który pobiera surowe informacje, normalizuje je, a następnie wykorzystuje wyspecjalizowaną załogę agentów AI (`Triage Crew`) do wstępnej selekcji i oceny. Tylko najbardziej wartościowe i dopasowane do profilu tematy są "promowane" jako sugestie do serwisu `Topic Manager`.

### Kluczowe Technologie
- **Framework**: FastAPI
- **Harmonogram**: APScheduler
- **Baza Danych**: ChromaDB (dla kolekcji `raw_trends`)
- **Główne Biblioteki**: `httpx`, `pydantic`, `crewai`

### Kluczowe Funkcjonalności
- **Scheduler-Driven Fetching**: Automatyczne uruchamianie procesu pobierania danych w zdefiniowanych interwałach.
- **Multi-Source Ingestion**: Równoległe pobieranie danych z wielu skonfigurowanych źródeł (Hacker News, ArXiv, GitHub itp.).
- **Data Normalization**: Standaryzacja pozyskanych danych do wspólnego formatu `RawTrendItem`.
- **AI-Powered Triage**: Wykorzystanie załogi agentów (`Triage Crew`) do inteligentnej oceny dopasowania do profilu (`Editorial Service`) i nowości (`Topic Manager`).
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
