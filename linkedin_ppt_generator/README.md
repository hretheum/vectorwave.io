# LinkedIn PPT Generator Service

LinkedIn-optimized presentation generator service for Vector Wave platform. Acts as a wrapper for Presenton service with LinkedIn-specific enhancements.

## 📋 Overview

**Task 3.2.1: LinkedIn PPT Generator Service** - Provides LinkedIn-optimized presentation generation by proxying requests to the Presenton service with enhanced prompts and LinkedIn-specific optimizations.

### ✨ Features

- **LinkedIn Optimization**: Prompts enhanced for LinkedIn audience and sharing
- **Presenton Integration**: Seamless proxy to existing Presenton service (port 8089)
- **Circuit Breaker Pattern**: Resilient HTTP client with automatic recovery
- **Professional Templates**: Business-focused presentation templates
- **Call-to-Action**: Automatic LinkedIn engagement prompts
- **RESTful API**: FastAPI with automatic documentation

## 🚀 Quick Start

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up -d linkedin-ppt-generator

# Check service health
curl http://localhost:8002/health
```

### API Usage
```python
import requests

# Generate LinkedIn presentation
response = requests.post("http://localhost:8002/generate-linkedin-ppt", json={
    "topic_title": "AI Content Creation Revolution",
    "topic_description": "How AI transforms marketing workflows with practical insights",
    "slides_count": 6,
    "template": "business",
    "linkedin_format": True,
    "include_call_to_action": True,
    "target_audience": "marketing professionals",
    "keywords": ["AI", "content", "automation"]
})

result = response.json()
print(f"Generated: {result['pdf_url']}")
```

## 🏗️ Architecture

### Service Structure
```
linkedin_ppt_generator/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   └── presenton_client.py     # Presenton HTTP client
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Service orchestration
├── requirements.txt            # Python dependencies
├── test_linkedin_ppt_generator.py # Test suite
└── README.md                   # This file
```

### Integration Flow
```
Publishing Orchestrator (8050) 
    ↓ HTTP request
LinkedIn PPT Generator (8002)
    ↓ Enhanced prompt
Presenton Service (8089)
    ↓ Generated files
Shared Volume (/tmp/publisher_images)
```

## 🔧 API Endpoints

### Core Endpoints
- `POST /generate-linkedin-ppt` - Generate LinkedIn-optimized presentation
- `GET /health` - Service health check with Presenton status
- `GET /` - Service information and circuit breaker status

### LinkedIn PPT Generation
```bash
curl -X POST http://localhost:8002/generate-linkedin-ppt \
  -H "Content-Type: application/json" \
  -d '{
    "topic_title": "AI Marketing Revolution",
    "topic_description": "Transforming marketing workflows with AI automation",
    "slides_count": 5,
    "template": "business",
    "linkedin_format": true,
    "include_call_to_action": true,
    "target_audience": "marketers",
    "keywords": ["AI", "automation", "ROI"]
  }'
```

## 📊 Configuration

### Environment Variables
```bash
# Service configuration
HOST=0.0.0.0
PORT=8002

# Presenton integration
PRESENTON_SERVICE_URL=http://presenton:8089
PRESENTON_TIMEOUT=60.0

# Optional
DEBUG=false
```

### LinkedIn Optimizations
- **Professional Tone**: Business-appropriate language for LinkedIn audience
- **Value Proposition**: Clear value statement on first slide
- **Actionable Insights**: Data-driven takeaways in every presentation
- **Social Media Ready**: Visual hierarchy optimized for sharing
- **Engagement Prompts**: Built-in discussion starters for comments
- **Call-to-Action**: Dedicated CTA slide encouraging LinkedIn engagement

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8002/health
```

### Full Test Suite
```bash
python test_linkedin_ppt_generator.py
```

### Manual Testing
```bash
# Generate test presentation
curl -X POST http://localhost:8002/generate-linkedin-ppt \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

## 🐳 Docker Integration

### Dependencies
- **Presenton Service**: Core presentation generation (port 8089)
- **Vector Wave Network**: Shared network for service communication
- **Publisher Images Volume**: Shared storage with other services

### Circuit Breaker
- **Failure Threshold**: 5 consecutive failures
- **Recovery Timeout**: 60 seconds
- **Automatic Retry**: 3 attempts with exponential backoff
- **Status Monitoring**: Real-time circuit breaker status

## 🔍 Monitoring

### Health Status
The service provides comprehensive monitoring:
- Presenton service availability check
- Circuit breaker status monitoring
- Request/response time tracking
- Error rate monitoring

### Circuit Breaker Status
```json
{
  "circuit_open": false,
  "failure_count": 0,
  "failure_threshold": 5,
  "recovery_timeout": 60
}
```

## 🚨 Error Handling

### Common Scenarios
1. **Presenton Service Down**: Circuit breaker opens, 503 responses
2. **Invalid Request**: 422 validation errors with detailed messages
3. **Timeout**: Automatic retry with exponential backoff
4. **Circuit Open**: 503 with retry-after header

### Fallback Strategy
- Circuit breaker prevents cascade failures
- Graceful degradation with meaningful error messages
- Automatic recovery when Presenton becomes available
- Detailed logging for troubleshooting

## 🔄 Integration

### Publishing Orchestrator Integration
```python
# Publishing Orchestrator expects this endpoint
linkedin_response = await client.post(
    "http://linkedin-ppt-generator:8002/generate-linkedin-ppt",
    json={
        "topic_title": topic["title"],
        "topic_description": topic["description"], 
        "slides_count": 5,
        "template": "business"
    }
)
```

### Response Format
```json
{
  "presentation_id": "uuid-string",
  "pptx_url": "http://presenton:8089/download/file.pptx",
  "pdf_url": "http://presenton:8089/download/file.pdf",
  "pdf_path": "/tmp/publisher_images/file.pdf",
  "slide_count": 5,
  "generation_time": 12.34,
  "template_used": "business",
  "topic_title": "Final Title",
  "linkedin_optimized": true,
  "ready_for_linkedin": true
}
```

## 📈 Performance

### Typical Generation Times
- 3-5 slides: ~8-15 seconds (including LinkedIn optimization)
- 6-10 slides: ~15-25 seconds
- Network overhead: ~1-2 seconds (proxy layer)

### LinkedIn Enhancement Features
- Prompt optimization: ~200ms additional processing
- Business tone adaptation
- Engagement element injection
- CTA slide generation

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PRESENTON_SERVICE_URL=http://localhost:8089
export PORT=8002

# Run service
python src/main.py
```

### Testing
```bash
# Health check
curl http://localhost:8002/health

# Full test suite
python test_linkedin_ppt_generator.py

# API documentation
open http://localhost:8002/docs
```

---

**Status**: ✅ Task 3.2.1 Completed - LinkedIn PPT Generator Service Implemented  
**Integration**: Ready for Publishing Orchestrator (port 8050)  
**Presenton Proxy**: Optimized LinkedIn presentation generation via Presenton (port 8089)  
**Circuit Breaker**: Resilient HTTP client with automatic failure recovery