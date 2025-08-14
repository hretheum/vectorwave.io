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

## 🔗 Mapa zależności i porty

- **Mapa zależności usług**: [docs/DEPENDENCIES_MAP.md](docs/DEPENDENCIES_MAP.md)
- **Rejestr portów**: [docs/integration/PORT_ALLOCATION.md](docs/integration/PORT_ALLOCATION.md)

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

## 🧭 Ważne uwagi dot. Editorial Crew (kolegium)

- Właściwy submoduł Editorial Crew znajduje się pod ścieżką `kolegium/`.
- Historyczny folder `vector-wave-editorial-crew/` został usunięty jako „sierota”. Wszystkie prace nad AI Writing Flow prowadź w `kolegium/ai_writing_flow`.

### Uruchamianie testów AI Writing Flow (kolegium) w trybie CI-Light

- Szybki runner Dockera jest w `kolegium/docker-compose.test.yml`.
- Domyślnie włączony jest `CI_LIGHT=1` (deterministyczne odpowiedzi bez zewnętrznych zależności).

Przykłady:

```bash
# Wszystkie testy (working dir kontenera: kolegium/ai_writing_flow)
docker compose -f kolegium/docker-compose.test.yml run --rm test-python-3.11

# Wybrane testy integracyjne
CI_LIGHT=1 TESTARGS="-q tests/test_flow_integration.py tests/test_integration_phase1.py" \
  docker compose -f kolegium/docker-compose.test.yml run --rm test-python-3.11
```

W testach dostępne są helpery do CI-Light:

```python
from ai_writing_flow.tests.helpers.ci_light import enable_ci_light, disable_ci_light, kb_unavailable
```