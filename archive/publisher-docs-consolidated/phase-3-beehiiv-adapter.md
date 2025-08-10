# Faza 3: Beehiiv Adapter

## Cel fazy
Zbudowanie adaptera do publikacji newsletterów na Beehiiv przez API (lub browserbase fallback), z obsługą harmonogramu i mediów.

---

### Zadanie 3.1: Szkielet usługi Beehiiv Adapter (kontener, healthcheck) ✅
- **Wartość**: Usługa uruchamia się w kontenerze, odpowiada na healthcheck (`/health`).
- **Test**: `curl http://localhost:8084/health` zwraca `{ "status": "ok" }`.
- **Implementacja**: ✅ FastAPI + Docker + health endpoint + API documentation
- **Porty**: 8084:8084 (Beehiiv), 8083:8082 (Twitter), 8081:80 (Nginx)
- **Endpoints**: `/health`, `/config`, `/publish`, `/docs`
- **Testing**: `make test-health`, `make test-beehiiv`, `make logs-beehiiv`

### Zadanie 3.2: Endpoint POST /publish (przyjmuje dane publikacji) ✅
- **Wartość**: Usługa przyjmuje żądanie publikacji (tytuł, treść, media, data publikacji).
- **Test**: `curl -X POST http://localhost:8084/publish -d '{ "title": "T", "content": "C" }' -H 'Content-Type: application/json'` zwraca `{ "accepted": true, ... }`.
- **Implementacja**: ✅ FastAPI endpoint z Pydantic walidacją, obsługa wszystkich pól
- **Walidacja**: 
  - `title`: wymagane, min 1 znak, max 200 znaków
  - `content`: wymagane, min 1 znak
  - `media_urls`: opcjonalne, lista URL-i
  - `schedule_time`: opcjonalne, ISO format
  - `tags`: opcjonalne, lista stringów
  - `send_to_subscribers`: opcjonalne, boolean (default: true)
- **Response format**: `{"accepted": bool, "newsletter_id": str, "scheduled": bool, "message": str, "send_count": int|null}`
- **Test suite**: `./scripts/test-beehiiv-publish.sh` - 12/12 testów przeszło ✅

### Zadanie 3.3: Integracja z Beehiiv API – publikacja newslettera ✅
- **Wartość**: Usługa publikuje newsletter przez Beehiiv API.
- **Test**: Po wysłaniu żądania POST, newsletter pojawia się na koncie Beehiiv.
- **Implementacja**: ✅ Pełna integracja z BeehiivClient
- **API Client**:
  - Autentykacja Bearer token
  - Automatyczne wykrywanie dostępności API
  - Graceful fallback na mock responses
  - Error handling dla wszystkich błędów API
  - Connection test z diagnostyką
- **Features**:
  - Publikacja draft postów
  - Harmonogramowanie (schedule_time)
  - HTML content support
  - Tags support
  - Publication ID validation
  - Environment variables configuration
- **Error Handling**: Wyraźne błędy API zamiast ukrywania za mock responses
- **Testing**: API connection tests + prawdziwe error handling verification ✅
- **Status Codes**: 503 (API disabled), 401 (invalid key), 400 (bad request), 422 (validation)

### Zadanie 3.4: Obsługa harmonogramu publikacji
- **Wartość**: Możliwość zaplanowania newslettera na określoną datę/godzinę.
- **Test**: Po wysłaniu żądania z polem `schedule_time`, newsletter pojawia się o zadanej godzinie.

### Zadanie 3.5: Obsługa mediów (obrazki, PDF)
- **Wartość**: Możliwość dołączenia pliku do newslettera.
- **Test**: Po wysłaniu żądania z polem `media_url`, plik pojawia się w newsletterze.

### Zadanie 3.6: Fallback na browserbase/stagehand (jeśli API zawiedzie)
- **Wartość**: Usługa próbuje browserbase, jeśli API nie działa.
- **Test**: Po symulacji błędu API, newsletter pojawia się przez browserbase.

### Zadanie 3.7: Walidacja błędów i odpowiedzi API
- **Wartość**: Usługa zwraca czytelne błędy (np. błąd autoryzacji, błąd publikacji).
- **Test**: Wysłanie niepoprawnego żądania zwraca `{ "error": "opis błędu" }`.