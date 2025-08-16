# AI Writing Flow Service

## Overview
AI Writing Flow is a human-assisted content generation service that integrates with CrewAI agents and Editorial Service to produce high-quality content with checkpoint-based validation.

## Features
- **Selective Validation**: Uses 3-4 critical rules at each checkpoint (pre-writing, mid-writing, post-writing)
- **Comprehensive Validation**: Full rule set validation for final content
- **Platform Adaptation**: Generates content variants for different platforms (LinkedIn, Twitter, Medium)
- **Editorial Integration**: Seamless integration with Editorial Service for ChromaDB-based validation
- **Circuit Breaker**: Resilient error handling with automatic fallback

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Orchestrator  │────▶│ AI Writing Flow  │────▶│Editorial Service │
└─────────────────┘     └──────────────────┘     └──────────────────┘
         │                       │                         │
         │                       │                         │
    direct_content=false    checkpoints              ChromaDB rules
         │                  validation                     │
         ▼                       ▼                         ▼
   ┌──────────┐          ┌──────────────┐        ┌──────────────┐
   │ /publish │          │   /generate   │        │  /validate/* │
   └──────────┘          └──────────────┘        └──────────────┘
```

## API Endpoints

### GET /health
Health check endpoint with dependency status.

**Response:**
```json
{
  "status": "healthy|degraded",
  "service": "ai-writing-flow",
  "version": "1.0.0",
  "environment": "development",
  "uptime_seconds": 123.456,
  "dependencies": {
    "editorial_service": {
      "status": "healthy",
      "details": {...}
    }
  },
  "timestamp": "2025-01-15T12:00:00"
}
```

### POST /generate
Generate content with AI Writing Flow checkpoints.

**Request:**
```json
{
  "topic": {
    "title": "The Future of AI",
    "description": "Exploring emerging AI technologies",
    "viral_score": 0.8,
    "content_type": "STANDALONE",
    "content_ownership": "ORIGINAL",
    "editorial_recommendations": ["focus on practical applications"]
  },
  "platform": "linkedin",
  "mode": "selective",
  "checkpoints_enabled": true,
  "skip_research": false,
  "user_id": "user123"
}
```

**Response:**
```json
{
  "content_id": "aiwf_1234567890_The_Future",
  "status": "completed",
  "content": "# The Future of AI\n\n...",
  "checkpoints_passed": {
    "pre-writing": true,
    "mid-writing": true,
    "post-writing": true
  },
  "validation_results": {
    "pre-writing": {...},
    "mid-writing": {...},
    "post-writing": {...}
  },
  "platform_variants": {
    "linkedin": "...",
    "twitter": "...",
    "medium": "..."
  },
  "metadata": {
    "topic": {...},
    "mode": "selective",
    "user_id": "user123"
  },
  "processing_time_ms": 2345.67,
  "timestamp": "2025-01-15T12:00:00"
}
```

### GET /metrics
Prometheus metrics endpoint.

## Integration with Orchestrator

The Orchestrator integrates with AI Writing Flow through the `direct_content` parameter:

- `direct_content=true` (default): Traditional agent flow
- `direct_content=false`: AI Writing Flow with checkpoints

### Example Orchestrator Request:
```bash
curl -X POST http://localhost:8042/flows/execute \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Artificial Intelligence Trends",
    "platform": "linkedin",
    "direct_content": false
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_PORT` | Service port | `8003` |
| `EDITORIAL_SERVICE_URL` | Editorial Service URL | `http://editorial-service:8040` |
| `OPENAI_API_KEY` | OpenAI API key for content generation | (required for full functionality) |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Log level | `info` |
| `CORS_ORIGINS` | CORS allowed origins | `*` |

## Docker Deployment

### Build
```bash
docker build -t ai-writing-flow ./ai-writing-flow
```

### Run Standalone
```bash
docker run -p 8003:8003 \
  -e EDITORIAL_SERVICE_URL=http://editorial-service:8040 \
  -e OPENAI_API_KEY=your-key \
  ai-writing-flow
```

### Docker Compose
The service is integrated in the main `docker-compose.yml`:
```bash
docker compose up ai-writing-flow editorial-service redis chromadb
```

## Testing

### Smoke Test
```bash
# Run smoke test
./ai-writing-flow/test_smoke.sh

# With custom hosts
AIWF_HOST=localhost AIWF_PORT=8003 \
ORCHESTRATOR_HOST=localhost ORCHESTRATOR_PORT=8042 \
./ai-writing-flow/test_smoke.sh
```

### E2E Test with Orchestrator
```bash
# Test with AI Writing Flow enabled
curl -X POST http://localhost:8042/flows/execute \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test content for AI generation",
    "platform": "linkedin",
    "direct_content": false
  }'

# Check flow status
curl http://localhost:8042/flows/status/{flow_id}
```

## Monitoring

### Health Monitoring
- `/health` endpoint provides service and dependency status
- Circuit breaker state for Editorial Service connection
- Degraded mode operation when Editorial Service unavailable

### Metrics
Prometheus metrics available at `/metrics`:
- `aiwf_requests_total` - Total requests by endpoint
- `aiwf_request_duration_seconds` - Request duration histogram
- `aiwf_generation_total` - Content generations by checkpoint
- `aiwf_editorial_validation_duration_seconds` - Editorial Service call duration

## Checkpoints and Validation

### Checkpoint Flow
1. **Pre-writing**: Initial content planning validation
2. **Mid-writing**: Draft content validation
3. **Post-writing**: Final content quality check

### Validation Modes
- **Selective**: 3-4 critical rules per checkpoint (human-assisted workflow)
- **Comprehensive**: Full rule set validation (automated workflow)

## Error Handling

### Circuit Breaker
- Automatic circuit breaker for Editorial Service calls
- Fallback to degraded mode when dependencies unavailable
- Configurable failure threshold and recovery timeout

### Graceful Degradation
- Service continues to function without Editorial Service
- Content generation proceeds without validation in degraded mode
- Health endpoint reports degraded status

## Development

### Requirements
- Python 3.11+
- FastAPI
- CrewAI
- httpx for async HTTP
- Prometheus client

### Local Development
```bash
cd ai-writing-flow
pip install -r requirements.txt
python -m src.main
```

### API Documentation
When running locally, interactive API docs available at:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## Troubleshooting

### Common Issues

1. **Editorial Service Unavailable**
   - Service runs in degraded mode
   - Check Editorial Service health: `curl http://editorial-service:8040/health`
   - Verify network connectivity between services

2. **Content Generation Fails**
   - Check OPENAI_API_KEY is set (if using OpenAI)
   - Verify topic data format
   - Check logs for detailed error messages

3. **Checkpoints Not Validating**
   - Ensure Editorial Service is healthy
   - Verify ChromaDB has validation rules
   - Check circuit breaker status in metrics

## Future Enhancements
- [ ] Real CrewAI agent integration
- [ ] OpenAI/LLM content generation
- [ ] Caching layer for validation results
- [ ] WebSocket support for real-time updates
- [ ] Multi-language content generation
- [ ] A/B testing framework for content variants