# Beehiiv Adapter - Technical Documentation

## Overview
Beehiiv Adapter jest mikrousługą odpowiedzialną za publikację newsletterów na platformie Beehiiv. Obsługuje zarówno publikację przez API, jak i fallback przez browser automation.

## Architecture

### Tech Stack
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11
- **Container**: Docker + Docker Compose
- **Dependencies**: requests, pydantic, uvicorn

### Port & Endpoints
- **Port**: 8084
- **Base URL**: http://localhost:8084
- **Health Check**: `GET /health`
- **Configuration**: `GET /config`
- **Publish**: `POST /publish`
- **Documentation**: `GET /docs`

## API Endpoints

### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "beehiiv-adapter",
  "version": "1.0.0",
  "timestamp": "2025-08-07T08:26:24.031070"
}
```

### 2. Configuration
```http
GET /config
```

**Response:**
```json
{
  "beehiiv_api_configured": false,
  "beehiiv_base_url": "https://api.beehiiv.com/v2",
  "api_key_present": false,
  "api_key_prefix": null,
  "mode": "mock",
  "publication_id": null,
  "fallback_enabled": true
}
```

### 3. Publish Newsletter
```http
POST /publish
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Newsletter Title",
  "content": "Newsletter content (HTML or markdown)",
  "media_urls": ["https://example.com/image.jpg"],
  "schedule_time": "2025-08-07T15:00:00Z",
  "tags": ["tech", "newsletter"],
  "send_to_subscribers": true
}
```

**Response:**
```json
{
  "accepted": true,
  "newsletter_id": "mock_newsletter_123",
  "scheduled": false,
  "message": "Mock: Newsletter 'Newsletter Title' opublikowany pomyślnie",
  "send_count": 100
}
```

## Environment Variables

### Required
- `BEEHIIV_API_KEY` - API key z Beehiiv
- `BEEHIIV_PUBLICATION_ID` - ID publikacji w Beehiiv

### Optional
- `BEEHIIV_BASE_URL` - URL API (default: https://api.beehiiv.com/v2)
- `BEEHIIV_FALLBACK_ENABLED` - Włączenie fallback mode (default: true)
- `OPENAI_API_KEY` - Dla browser automation fallback
- `BROWSERBASE_API_KEY` - Cloud browser automation
- `BROWSERBASE_PROJECT_ID` - Browserbase project ID
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8084)
- `DEBUG` - Debug mode (default: false)

## Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8084
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8084/health || exit 1
CMD ["python", "main.py"]
```

### Docker Compose Service
```yaml
beehiiv-adapter:
  build:
    context: ./src/adapters/beehiiv
    dockerfile: Dockerfile
  container_name: publisher-beehiiv-adapter
  ports:
    - "8084:8084"
  env_file:
    - ./.env
  environment:
    - HOST=0.0.0.0
    - PORT=8084
    - DEBUG=true
  volumes:
    - ./src/adapters/beehiiv:/app
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8084/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

## Makefile Commands

```bash
# Build and run
make build
make up

# Test health check
make test-health

# Test publish endpoint
make test-beehiiv

# View logs
make logs-beehiiv

# Check status
make status
```

## Testing

### Basic Tests
```bash
# Health check
curl http://localhost:8084/health

# Configuration
curl http://localhost:8084/config

# Simple publish
curl -X POST http://localhost:8084/publish \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Test content"}'

# Scheduled publish
curl -X POST http://localhost:8084/publish \
  -H "Content-Type: application/json" \
  -d '{"title": "Scheduled", "content": "Content", "schedule_time": "2025-08-07T15:00:00Z"}'

# With media and tags
curl -X POST http://localhost:8084/publish \
  -H "Content-Type: application/json" \
  -d '{"title": "With Media", "content": "Content", "media_urls": ["https://example.com/image.jpg"], "tags": ["tech"]}'
```

## Current Status

### ✅ Task 3.1 COMPLETED
- **Szkielet usługi**: FastAPI application z wszystkimi podstawowymi endpointami
- **Kontener**: Docker + Docker Compose configuration
- **Health check**: Endpoint `/health` z proper response format
- **Testing**: Makefile commands dla testowania
- **Documentation**: API docs na `/docs`

### 🚧 Next Steps (Tasks 3.2-3.7)
- **Task 3.2**: Endpoint POST /publish już zaimplementowany (mock mode)
- **Task 3.3**: Integracja z prawdziwym Beehiiv API
- **Task 3.4**: Obsługa harmonogramu (logika już gotowa)
- **Task 3.5**: Obsługa mediów (walidacja URL już gotowa)
- **Task 3.6**: Browser automation fallback
- **Task 3.7**: Zaawansowane error handling

## File Structure

```
src/adapters/beehiiv/
├── main.py           # Main FastAPI application
├── requirements.txt  # Python dependencies
├── Dockerfile       # Container configuration
└── env.template     # Environment variables template
```