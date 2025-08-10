# API Specifications: Trend Harvester Service

## 1. Wprowadzenie

API serwisu `Trend-Harvester` jest celowo minimalistyczne. Jego głównym zadaniem jest praca w tle według harmonogramu. Udostępnione endpointy służą głównie do celów administracyjnych, diagnostycznych i ręcznego wyzwalania procesów.

-   **Base URL:** `http://localhost:8043`
-   **Authentication:** Brak (serwis działa w wewnętrznej sieci Docker)

---

## 2. Endpoints

### `POST /harvest/trigger`

-   **Opis:** Ręcznie wyzwala pełny cykl pobierania, normalizacji i oceny trendów. Endpoint natychmiast zwraca odpowiedź, a proces jest wykonywany w tle.
-   **Request Body:** Brak
-   **Response `202 Accepted`:**
    ```json
    {
      "status": "Harvesting process triggered successfully.",
      "timestamp": "2025-08-10T12:05:00Z"
    }
    ```
-   **Response `409 Conflict`:**
    ```json
    {
      "status": "Harvesting process is already running.",
      "started_at": "2025-08-10T12:00:00Z"
    }
    ```

### `GET /harvest/status`

-   **Opis:** Zwraca status ostatniego cyklu pobierania danych.
-   **Request Parameters:** Brak
-   **Response `200 OK`:**
    ```json
    {
      "last_run": {
        "status": "completed", // "running", "failed", "completed"
        "started_at": "2025-08-10T12:00:00Z",
        "finished_at": "2025-08-10T12:15:00Z",
        "duration_seconds": 900,
        "sources_processed": [
          "hacker-news",
          "arxiv",
          "github"
        ],
        "items_fetched": 152,
        "items_promoted": 12,
        "error": null
      },
      "next_run_scheduled_at": "2025-08-10T18:00:00Z"
    }
    ```

### `GET /health`

-   **Opis:** Standardowy endpoint zdrowia, zgodny z resztą mikroserwisów.
-   **Request Parameters:** Brak
-   **Response `200 OK`:**
    ```json
    {
      "status": "healthy",
      "timestamp": "2025-08-10T12:20:00Z",
      "dependencies": {
        "chromadb": "connected",
        "editorial_service": "connected",
        "topic_manager": "connected"
      }
    }
    ```
