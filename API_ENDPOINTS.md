# API Endpoints Documentation - AI Kolegium Redakcyjne

## Overview
**Base URL:** `http://localhost:8003`  
**Last Updated:** 2025-08-05 (commit: `58cbf76`)

## 🎯 Core Endpoints

### 1. Health Check
```bash
GET /health
```
Returns basic health status.

**Response:**
```json
{
  "status": "healthy",
  "container": "running"
}
```

### 2. Analyze Content Potential ⚡
```bash
POST /api/analyze-potential
```
Ultra-fast content analysis (1ms response time).

**Request:**
```json
{
  "folder": "2025-07-31-adhd-ideas-overflow",
  "use_flow": false
}
```

**Response:**
```json
{
  "folder": "2025-07-31-adhd-ideas-overflow",
  "filesCount": 5,
  "contentType": "GENERAL",
  "contentOwnership": "ORIGINAL",
  "valueScore": 7.5,
  "viral_score": 0.75,
  "topTopics": [
    {
      "title": "5 Lessons from ADHD Ideas Overflow Implementation",
      "platform": "LinkedIn",
      "viralScore": 8
    }
  ],
  "recommendation": "🔥 High viral potential!",
  "processing_time_ms": 1
}
```

### 3. Generate Draft 🚀
```bash
POST /api/generate-draft
```
Generates content draft using CrewAI Writer Agent.

**Request:**
```json
{
  "content": {
    "title": "5 AI Automation Mistakes",
    "content_type": "STANDARD",
    "platform": "LinkedIn",
    "content_ownership": "ORIGINAL"
  },
  "skip_research": true  // Automatic for ORIGINAL content
}
```

**Response:**
```json
{
  "status": "completed",
  "draft": {
    "title": "5 AI Automation Mistakes",
    "content": "Full draft content...",
    "platform": "LinkedIn",
    "word_count": 458,
    "optimized_for": "LinkedIn"
  },
  "metadata": {
    "generated_at": "2025-08-05T20:04:39.350855",
    "content_type": "STANDARD",
    "used_research": false,
    "execution_time_seconds": 20.5,
    "optimization_applied": true
  }
}
```

### 4. Execute Research
```bash
POST /api/research
```
Performs deep research on a topic.

**Request:**
```json
{
  "topic": "AI Automation Trends",
  "depth": "standard",  // quick, standard, deep
  "skip_research": false
}
```

**Response:**
```json
{
  "status": "completed",
  "topic": "AI Automation Trends",
  "findings": {
    "summary": "Research findings...",
    "key_points": ["Point 1", "Point 2"],
    "word_count": 350
  },
  "execution_time_ms": 2500
}
```

### 5. Execute Complete Flow
```bash
POST /api/execute-flow
```
Runs the complete flow: routing → research → writing.

**Request:**
```json
{
  "title": "Building AI Agents",
  "content_type": "TECHNICAL",
  "platform": "Blog",
  "content_ownership": "EXTERNAL"
}
```

### 6. Execute Flow with Tracking
```bash
POST /api/execute-flow-tracked
```
Complete flow with detailed diagnostics and step tracking.

**Response includes:**
- Flow ID for tracking
- Step-by-step execution details
- Agent decisions
- Content loss metrics
- Timing information

### 7. Flow Diagnostics
```bash
GET /api/flow-diagnostics/{flow_id}
```
Get detailed diagnostics for a specific flow execution.

```bash
GET /api/flow-diagnostics?limit=10
```
List recent flow executions.

### 8. List Content Folders
```bash
GET /api/list-content-folders
```
Lists available content folders from the raw content directory.

**Response:**
```json
{
  "status": "ok",
  "folders": [
    {
      "name": "2025-07-31-adhd-ideas-overflow",
      "path": "/path/to/folder",
      "type": "raw_content"
    }
  ],
  "total": 15
}
```

### 9. Verify OpenAI Integration
```bash
GET /api/verify-openai
```
Verifies that the system is using real OpenAI API.

**Response:**
```json
{
  "status": "verified",
  "api_type": "OpenAI GPT-4",
  "response": "Generated message with timestamp",
  "execution_time_seconds": 1.2,
  "model": "gpt-4"
}
```

## 🔧 Frontend Proxy Endpoints

### Generate Draft (Frontend Proxy)
```bash
POST /api/generate-draft  # Port 3000
```
Frontend proxy that transforms data between UI and backend formats.

**Key Transformations:**
- `topic_title` → `content.title`
- Adds default values for missing fields
- Transforms response format (`status: "completed"` → `success: true`)
- Automatically sets `skip_research: true` for ORIGINAL content

## 📊 Performance Metrics

| Endpoint | Average Response Time | Notes |
|----------|---------------------|-------|
| `/api/analyze-potential` | 1ms | No AI calls |
| `/api/generate-draft` (ORIGINAL) | ~20s | Skip research |
| `/api/generate-draft` (EXTERNAL) | ~25s | With research |
| `/api/execute-research` | 2-3s | Deep research |
| `/api/execute-flow` | 25-50s | Full flow |

## 🚀 Optimizations

### Skip Research for ORIGINAL Content
When `content_ownership = "ORIGINAL"`:
- Research phase is automatically skipped
- Special context provided to AI agent
- ~20% faster draft generation (25s → 20s)

### Response Caching
- Simple in-memory caching available
- Cache key: `{title}:{platform}`
- Useful for repeated requests

## 🔍 Error Handling

All endpoints return consistent error format:
```json
{
  "status": "error",
  "error": "Error message",
  "detail": "Additional context if available"
}
```

Common HTTP status codes:
- `200`: Success
- `404`: Endpoint not found (check URL)
- `422`: Validation error (check request format)
- `500`: Server error

## 🧪 Testing

### Quick Test Commands

```bash
# Test health
curl http://localhost:8003/health

# Test analyze (fastest)
curl -X POST http://localhost:8003/api/analyze-potential \
  -H "Content-Type: application/json" \
  -d '{"folder": "test-folder"}'

# Test draft generation
curl -X POST http://localhost:8003/api/generate-draft \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "title": "Test Draft",
      "platform": "LinkedIn",
      "content_ownership": "ORIGINAL"
    },
    "skip_research": true
  }'
```

## 📝 Notes

1. **Port Configuration**: Backend runs on port 8003, frontend on 3000
2. **CORS**: Enabled for frontend integration
3. **Authentication**: Currently no auth required (development mode)
4. **Rate Limiting**: Not implemented yet
5. **Logging**: Optimization logs visible in console