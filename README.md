# Vector Wave

Vector Wave to zaawansowany, wieloplatformowy system do tworzenia i publikacji treści oparty na AI. Wykorzystuje architekturę mikroserwisów i wyspecjalizowane ekipy agentów AI do researchu, pisania, walidacji i dystrybucji treści.

## 🚀 Architektura Systemu

Architektura projektu jest w pełni opisana w folderze `target-version`, który stanowi jedyne źródło prawdy o docelowej implementacji.

**➡️ [Zobacz Pełną Architekturę Systemu](./target-version/VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md)**

## ⚡ Quick Start

Projekt jest w pełni skonteneryzowany. Do uruchomienia całego środowiska deweloperskiego użyj Docker Compose.

1.  **Uruchomienie rdzenia systemu:**
    ```bash
    docker compose up --build -d
    ```
    Ta komenda uruchomi kluczowe serwisy: `chromadb`, `redis`, `editorial-service`, `topic-manager` i `crewai-orchestrator`.

2.  **Uruchomienie serwisów opcjonalnych (z profilami):**
    ```bash
    # Uruchomienie serwisu do publikacji
    docker compose --profile publishing up -d

    # Uruchomienie serwisu analitycznego
    docker compose --profile analytics up -d
    ```

3.  **Weryfikacja:**
    Sprawdź, czy kluczowe serwisy działają poprawnie:
    ```bash
    curl -s http://localhost:8000/api/v1/heartbeat && echo ""
    curl -s http://localhost:8040/health | jq .status
    curl -s http://localhost:8042/health | jq .status
    curl -s http://localhost:8041/health | jq '{embeddings_ready,chromadb}'
    ```

## 🏗️ Struktura Serwisów

Projekt składa się z kilku kluczowych mikroserwisów i submodułów Git. Każdy z nich posiada własne `README.md` z szczegółową dokumentacją.

| Serwis / Submoduł | Opis |
| :--- | :--- |
| **[`kolegium/`](./kolegium/README.md)** | Główny submoduł zawierający logikę **AI Writing Flow** oraz interfejs użytkownika **Vector Wave UI**. |
| **[`editorial-service/`](./editorial-service/README.md)** | Scentralizowany serwis do walidacji treści, w pełni zintegrowany z ChromaDB. |
| **[`publisher/`](./publisher/README.md)** | Submoduł odpowiedzialny za orkiestrację i publikację treści na wielu platformach. |
| **[`knowledge-base/`](./knowledge-base/README.md)** | Baza wiedzy dla agentów AI, zapewniająca długoterminową pamięć i kontekst. |
| **[`linkedin/`](./linkedin/README.md)** | Submoduł ze specjalizowaną logiką dla platformy LinkedIn. |
| **[`topic-manager/`](./topic-manager/README.md)** | Serwis do zarządzania i odkrywania nowych tematów na treści. |
| **[`analytics-service/`](./kolegium/analytics-service/README.md)** | (W budowie) Serwis do śledzenia wydajności publikacji i uczenia się preferencji. |