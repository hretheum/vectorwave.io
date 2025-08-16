# AI Writing Flow Service

FastAPI service exposing legacy and enhanced endpoints for multi‑platform content generation.

## Run (compose)

The root docker‑compose defines the service as `ai-writing-flow-service` on port 8044:

```bash
docker compose up -d ai-writing-flow-service
curl -s http://localhost:8044/health | jq .
```

## Endpoints

- `GET /health` – overall service health (legacy + enhanced components)
- `GET /` – root info with links
- Enhanced API (mounted under `/v2`):
  - `POST /v2/generate/multi-platform` – generate content for multiple platforms
  - `POST /v2/generate/linkedin-prompt` – prepare LinkedIn carousel prompt
  - `GET /v2/metrics` – runtime metrics
  - `GET /v2/platforms` – supported platforms and configs
  - `GET /v2/docs` – Swagger UI for enhanced API

## Quick smoke

```bash
curl -s -X POST http://localhost:8044/v2/generate/multi-platform \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": {"title": "AIWF smoke", "description": "desc", "keywords": ["ai"], "target_audience": "engineers"},
    "platforms": {"linkedin": {"enabled": true, "direct_content": true}},
    "priority": 5
  }' | jq .
```

Expected: 200 with `platform_content.linkedin.*`.

## Configuration

No required envs for local compose. The container listens on 0.0.0.0:8044.

## Notes

- The legacy endpoint `POST /generate` remains for backward compatibility.
- The service aggregates metrics across requests (`/health` and `/v2/metrics`).
# AI Writing Flow

### Cel Serwisu
Główny silnik orkiestracji agentów AI w systemie Vector Wave. Implementuje liniowy, niezawodny przepływ generowania treści, od researchu po finalną walidację jakości. Integruje się z `editorial-service` w celu walidacji i `knowledge-base` w celu pozyskiwania wiedzy.

### Kluczowe Komponenty
- **`ai_writing_flow_v2.py`**: Główna klasa orkiestrująca, integrująca monitoring, alerty i bramki jakości.
- **`linear_flow.py`**: Implementacja liniowego przepływu, eliminująca pętle i zapewniająca przewidywalność.
- **`*_linear.py`**: Dedykowane exekutory dla każdego etapu (Research, Audience, Draft, Style, Quality).
- **`crews/`**: Definicje agentów CrewAI i ich zadań.

### Uruchomienie i Testowanie
Serwis jest częścią submodułu `kolegium` i jest uruchamiany przez główny plik `docker-compose.yml`.

**Uruchomienie testów jednostkowych i integracyjnych:**
```bash
# Z głównego katalogu repozytorium
PYTHONPATH=kolegium/ai_writing_flow/src pytest -q kolegium/ai_writing_flow/tests
```

---
### Istniejąca Dokumentacja (Zachowana)

# AI Writing Flow - V2 Production Readme

## 🚀 Status: **PRODUCTION READY** (Phase 4.5.3 COMPLETED)

### ✅ Kluczowe Osiągnięcia
- **Linear Flow Pattern**: Zero infinite loops, stabilne i przewidywalne wykonanie.
- **Pełny Monitoring**: FlowMetrics, AlertManager, DashboardAPI - pełna obserwowalność.
- **Quality Gates**: 5 zautomatyzowanych reguł walidacji.
- **Knowledge Base Integration**: Adapter i `enhanced_knowledge_tools` w produkcji.
- **Container-First**: Pełna konteneryzacja z health checks.
- **AI Assistant & Agentic RAG**: Zintegrowany asystent do edycji i autonomiczny RAG.

### 🏗️ Architektura
- **`ai_writing_flow_v2.py`**: Główna klasa orkiestrująca.
- **`linear_flow.py`**: Implementacja liniowego przepływu.
- **`*_linear.py`**: Dedykowane exekutory dla każdego etapu (Research, Audience, Draft, Style, Quality).
- **`monitoring/`**: Kompletny stack monitoringu.
- **`validation/`**: Implementacja Quality Gates.
- **`tools/`**: Narzędzia CrewAI, w tym integracja z Knowledge Base.

### ⚡ Quick Start
```bash
# Uruchom cały system (w tym AI Writing Flow)
docker compose up -d

# Wykonaj przykładowy flow przez API
curl -X POST http://localhost:8001/v2/generate/multi-platform \
  -H "Content-Type: application/json" \
  -d 
    {
      "topic": { "title": "Test" },
      "platforms": { "linkedin": { "enabled": true } }
    }
```

### 🧪 Testowanie
```bash
# Uruchom wszystkie testy
PYTHONPATH=./src pytest

# Uruchom testy integracyjne z KB
pytest tests/test_knowledge_integration.py
```

---
### Skonsolidowana Dokumentacja

---
# AI Writing Flow - API Documentation

## V2 Enhanced API (`/v2`)

### 1. Multi-Platform Content Generation
- **Endpoint**: `/v2/generate/multi-platform`
- **Method**: `POST`
- **Description**: Generuje zoptymalizowane treści dla wielu platform jednocześnie.
- **Request Body**: `MultiPlatformRequest`
- **Response**: `MultiPlatformResponse`

### 2. LinkedIn Prompt-Based Generation
- **Endpoint**: `/v2/generate/linkedin-prompt`
- **Method**: `POST`
- **Description**: Generuje treść na LinkedIn na podstawie prostego promptu.
- **Request Body**: `LinkedInPromptRequest`
- **Response**: `LinkedInPromptResponse`

### 3. Monitoring & Health
- **Endpoint**: `/v2/metrics`
- **Method**: `GET`
- **Description**: Zwraca metryki wydajności i status alertów.

- **Endpoint**: `/v2/platforms`
- **Method**: `GET`
- **Description**: Zwraca listę wspieranych platform i ich konfigurację.

## Legacy API

### 1. Generate Content (Legacy)
- **Endpoint**: `/generate`
- **Method**: `POST`
- **Description**: Utrzymywany dla kompatybilności wstecznej.
---
# Project Status: AI Writing Flow

## 🎯 Current Focus: **Production Hardening & Optimization**

### ✅ Recently Completed
- **Phase 4.5.3**: Pełna integracja z Publisher Orchestrator.
- **Linear Flow**: Całkowite wyeliminowanie pętli router/listen.
- **Monitoring**: Wdrożenie `FlowMetrics` i `AlertManager`.
- **Quality Gates**: Zintegrowanie 5 reguł walidacyjnych.
- **Knowledge Base**: Pełna integracja z `enhanced_knowledge_tools`.

### 🚧 In Progress
- **Performance Tuning**: Optymalizacja zapytań do ChromaDB i redukcja zużycia pamięci.
- **Error Handling**: Rozbudowa katalogu błędów i scenariuszy odzyskiwania.
- **UI Bridge V2**: Udoskonalenie komunikacji z frontendem, przesyłanie bardziej szczegółowych statusów.

### ⏳ Next Steps
- **Advanced Caching**: Implementacja bardziej zaawansowanych strategii cache'owania dla wyników agentów.
- **Security Hardening**: Wprowadzenie uwierzytelniania między serwisami.
- **Documentation Cleanup**: Ujednolicenie i aktualizacja całej dokumentacji.
