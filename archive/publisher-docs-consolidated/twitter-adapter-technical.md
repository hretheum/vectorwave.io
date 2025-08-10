# Twitter Adapter - Dokumentacja Techniczna

## Przegląd
Twitter Adapter to mikrousługa do publikacji na Twitter/X przez Typefully API, część Multi-Channel Publisher.

## 🎯 Status: PRODUCTION READY (Tasks 2.1-2.5)

---

## Architektura

### Komponenty
- **FastAPI** - główna aplikacja
- **TypefullyClient** - klient API Typefully
- **Docker** - konteneryzacja
- **Nginx** - reverse proxy

### Porty
- **Aplikacja**: 8083:8082
- **Nginx**: 8081:80

---

## Endpointy API

### `GET /health`
```bash
curl http://localhost:8083/health
```
**Response:**
```json
{
  "status": "ok",
  "service": "twitter-adapter",
  "endpoints": {
    "health": "/health",
    "publish": "/publish", 
    "config": "/config",
    "status": "/status/{draft_id}",
    "docs": "/docs"
  }
}
```

### `GET /config`
```bash
curl http://localhost:8083/config
```
**Response:**
```json
{
  "typefully_api_configured": true,
  "typefully_base_url": "https://api.typefully.com/v1",
  "api_key_present": true,
  "api_key_prefix": "poOyVX2J...",
  "mode": "production",
  "api_test": "success",
  "recent_drafts_count": 0
}
```

### `POST /publish`
```bash
curl -X POST http://localhost:8083/publish \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello World! 🚀",
    "thread_mode": false,
    "schedule_time": "2025-01-08T15:30:00Z",
    "media_urls": ["https://example.com/image.jpg"]
  }'
```

**Request Model:**
```python
class PublishRequest(BaseModel):
    text: str                           # Treść tweeta/wątku
    thread_mode: bool = False           # Czy dzielić na wątek
    schedule_time: Optional[str] = None # ISO datetime lub "next-free-slot"
    media_urls: Optional[List[str]] = None # URLs obrazków (TODO: Task 2.6)
```

**Response Model:**
```python
class PublishResponse(BaseModel):
    accepted: bool                      # Czy żądanie zaakceptowane
    tweet_id: Optional[str] = None      # ID pojedynczego tweeta
    thread_ids: Optional[List[str]] = None # IDs wątku
    scheduled: bool = False             # Czy zaplanowane
    message: str                        # Status message
```

### `GET /status/{draft_id}`
```bash
curl http://localhost:8083/status/6401696
```
**Response:**
```json
{
  "found": true,
  "draft_id": "6401696",
  "status": "published",
  "scheduled_date": "2025-08-07T07:06:00Z",
  "published_on": "2025-08-07T07:06:01.157300Z",
  "twitter_url": "https://x.com/ErykO8529/status/1953351907545891240",
  "source": "published"
}
```

---

## 🔑 Kluczowe Odkrycie: Mechanizm Publikacji Typefully

### Sposób działania:
1. **Bez `schedule_time`** → Typefully tworzy draft ze statusem `"draft"`
   - ❌ **NIE publikuje automatycznie**
   - ⚠️ **Wymaga ręcznej publikacji w UI Typefully**

2. **Z `schedule_time` w przyszłości** → Typefully tworzy draft ze statusem `"scheduled"`
   - ✅ **Automatycznie publikuje** gdy nadejdzie czas!
   - 🎯 **To jest sposób na automatyczną publikację**

### Przykład auto-publikacji:
```bash
# Zaplanuj na za 2 minuty (CEST+2 = UTC)
curl -X POST http://localhost:8083/publish \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test auto-publikacji! 🚀",
    "schedule_time": "2025-01-08T13:17:00Z"
  }'

# Sprawdź status po czasie
curl http://localhost:8083/status/{draft_id}
```

**Rezultat:**
- `status: "scheduled"` → `status: "published"`
- `published_on: null` → `published_on: "2025-01-08T13:17:01.157Z"`
- `twitter_url: null` → `twitter_url: "https://x.com/..."`

---

## TypefullyClient

### Konfiguracja
```python
# Environment Variables
TYPEFULLY_API_KEY=poOyVX2J...    # Wymagane
TYPEFULLY_BASE_URL=https://api.typefully.com/v1  # Opcjonalne
```

### Headers
```python
{
    "X-API-KEY": f"Bearer {api_key}",  # ⚠️ UWAGA: X-API-KEY nie Authorization!
    "Content-Type": "application/json"
}
```

### Główne metody
```python
class TypefullyClient:
    def create_draft(self, text: str, media_urls: List[str] = None, 
                     schedule_time: str = None, thread_mode: bool = False):
        """Tworzy draft w Typefully"""
        
    def get_recent_drafts(self, filter_type: str = None):
        """Pobiera ostatnie zaplanowane drafty"""
        
    def get_published_drafts(self, filter_type: str = None):  
        """Pobiera ostatnie opublikowane drafty"""
```

### Payload dla create_draft
```python
# Pojedynczy tweet
{
    "content": "Hello World! 🚀"
}

# Wątek (thread_mode=True)
{
    "content": "Tweet 1\n\n\n\nTweet 2\n\n\n\nTweet 3",
    "threadify": True
}

# Zaplanowany
{
    "content": "Hello World! 🚀",
    "schedule-date": "2025-01-08T15:30:00Z"  # ISO format lub "next-free-slot"
}
```

---

## Obsługa wątków (Threads)

### Algorytm podziału tekstu
1. **Sprawdź długość** - jeśli ≤280 znaków, zostaw jako pojedynczy tweet
2. **Podziel na zdania** - użyj `. ` jako separatora
3. **Grupuj zdania** - dopóki zmieszczą się w 280 znakach
4. **Podziel na słowa** - jeśli zdanie za długie
5. **Połącz separatorem** - użyj `\n\n\n\n` między częściami wątku

### Przykład:
```bash
curl -X POST http://localhost:8083/publish \
  -H "Content-Type: application/json" \
  -d '{
    "text": "To jest bardzo długi tweet, który przekracza limit 280 znaków i powinien zostać automatycznie podzielony na wątek przez nasz Multi-Channel Publisher. System używa Typefully API do zarządzania publikacją na Twitter/X. Dzięki temu możemy publikować długie treści bez martwienia się o limity platform społecznościowych.",
    "thread_mode": true
  }'
```

**Rezultat:** Thread z `thread_ids: ["6401653"]`

---

## Docker & Deployment

### docker-compose.yml
```yaml
services:
  twitter-adapter:
    build:
      context: ./src/adapters/twitter
      dockerfile: Dockerfile
    container_name: publisher-twitter-adapter
    ports:
      - "8083:8082"
    env_file:
      - ./.env  # ⚠️ UWAGA: Root .env nie w src/adapters/twitter/
    environment:
      - HOST=0.0.0.0
      - PORT=8082
      - DEBUG=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Makefile Commands
```bash
make build        # Zbuduj kontenery
make up          # Uruchom usługi  
make restart     # Restart wszystkich usług
make logs-twitter # Pokaż logi Twitter Adapter
make test-health # Test healthcheck
```

---

## Testowanie

### Podstawowe testy
```bash
# 1. Health check
curl http://localhost:8083/health

# 2. Config check
curl http://localhost:8083/config

# 3. Pojedynczy tweet (draft)
curl -X POST http://localhost:8083/publish \
  -H "Content-Type: application/json" \
  -d '{"text": "Test pojedynczego tweeta"}'

# 4. Wątek
curl -X POST http://localhost:8083/publish \
  -H "Content-Type: application/json" \
  -d '{
    "text": "To jest bardzo długi tweet... [300+ znaków]",
    "thread_mode": true
  }'

# 5. Zaplanowany (auto-publikacja)
curl -X POST http://localhost:8083/publish \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Zaplanowany tweet! 🕒",
    "schedule_time": "2025-01-08T15:30:00Z"
  }'

# 6. Sprawdź status
curl http://localhost:8083/status/{draft_id}
```

### Oczekiwane rezultaty
- **Draft** → `"status": "draft"`, wymaga ręcznej publikacji
- **Scheduled** → `"status": "scheduled"` → po czasie `"status": "published"` + twitter_url
- **Thread** → `thread_ids: ["..."]` zamiast `tweet_id`

---

## Znane ograniczenia

### Task 2.6 (TODO)
- ❌ **Media URLs nie są jeszcze obsługiwane**
- ⚠️ Warning w logach: `"Media URLs nie są jeszcze obsługiwane - będzie w zadaniu 2.6"`

### Task 2.7 (TODO) 
- ❌ **Brak zaawansowanej walidacji błędów API**
- ⚠️ Podstawowe error handling jest zaimplementowane

### Inne
- ⚠️ **Strefa czasowa**: Typefully oczekuje UTC, ale trzeba pamiętać o konwersji z CEST (+2)
- ⚠️ **Rate limiting**: Nie zaimplementowane (może być potrzebne w produkcji)

---

## Logi i debugging

### Sprawdzanie logów
```bash
docker logs publisher-twitter-adapter --tail 20
```

### Typowe komunikaty
```
INFO:typefully_client:[Typefully] POST https://api.typefully.com/v1/drafts/
INFO:typefully_client:[Typefully] Response: {'id': 6401696, 'status': 'scheduled', ...}
INFO:main:[Twitter Adapter] Typefully publikacja zakończona: Tweet zaplanowany w Typefully (ID: 6401696)
```

### Error handling
```python
# 400 Bad Request
{"detail": "Schedule date must be in the future"}

# 403 Forbidden  
{"detail": "Błąd Typefully API: 403 Client Error: Forbidden"}

# API Key missing
{"detail": "TYPEFULLY_API_KEY jest wymagany"}
```

---

## Następne kroki

### Task 2.6: Media Support
- Implementacja obsługi `media_urls`
- Upload obrazków do Typefully
- Walidacja formatów i rozmiarów

### Task 2.7: Advanced Error Handling  
- Retry logic dla failed requests
- Rate limiting
- Detailed error responses
- Metrics and monitoring

### Przyszłe optymalizacje
- Pseudo-immediate publication (schedule +1 minute)
- Bulk operations
- Account switching
- Analytics integration