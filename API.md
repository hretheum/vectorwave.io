# API Reference - Kolegium AI Writing Flow

## 🚀 Quick Start

Base URL: `http://localhost:8003/api`

## 🔥 Core Endpoints

### 1. Generate Draft with TRUE Agentic RAG
```bash
POST /generate-draft
{
  "content": {
    "title": "Your topic here",
    "platform": "LinkedIn",
    "content_type": "THOUGHT_LEADERSHIP",
    "content_ownership": "ORIGINAL"
  }
}
```
- Uses iterative style guide search (3-5 autonomous queries)
- Each generation is unique even for same input
- Response time: 20-50s

### 2. Analyze Custom Ideas (Batch)
```bash
POST /analyze-custom-ideas
{
  "ideas": ["idea 1", "idea 2", "idea 3"]
}
```
- Analyzes multiple ideas in parallel
- Returns scores, recommendations, best idea

### 3. Stream Batch Analysis (SSE)
```bash
POST /analyze-custom-ideas-stream
{
  "ideas": ["idea 1", "idea 2", "idea 3"]
}
```
- Real-time progress updates
- Event types: start, progress, result, error, complete

### 4. Iterative Style Guide Analysis
```bash
POST /style-guide/analyze-iterative
{
  "content": "Your content to analyze",
  "platform": "LinkedIn",
  "max_iterations": 5
}
```
- Agent autonomously searches style guide
- Returns search log, discovered rules, analysis

### 5. Chat with AI Assistant
```bash
POST /chat
{
  "message": "Make the draft more engaging",
  "context": {
    "draft_content": "current draft...",
    "topic_title": "AI in Marketing"
  }
}
```
- Natural language draft editing
- Intent recognition
- Context-aware responses

## 📊 Style Guide Endpoints

### Seed Style Guide (180 rules)
```bash
POST /style-guide/seed
```

### Check Style Guide
```bash
POST /style-guide/check
{
  "content": "Your content",
  "platform": "LinkedIn"
}
```

## 🔍 Diagnostic Endpoints

### Health Check
```bash
GET /health
```

### OpenAPI Docs
```bash
GET /docs
```

## 🎯 Key Features

1. **TRUE Agentic RAG**
   - Agent decides what to search
   - 3-5 autonomous queries per generation
   - No hardcoded rules or patterns

2. **Unique Results**
   - Same input → Different queries
   - Different queries → Different content
   - Zero predetermined outcomes

3. **Real-time Streaming**
   - SSE for batch analysis
   - Progress tracking (0-100%)
   - Instant feedback

4. **Smart Caching**
   - Redis cache for analysis results
   - 5-minute TTL
   - Preload on startup

## 🚨 Important Notes

- OpenAI API key required (`OPENAI_API_KEY`)
- ChromaDB must be running (port 8001)
- Redis must be running (port 6380)
- All times are estimates based on OpenAI response times