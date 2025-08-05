# 🐳 Container-First Transformation Plan - AI Writing Flow

## 🎯 Filozofia: Container-First Development

**Zamiast**: Budować skomplikowany system i potem go konteneryzować  
**Robimy**: Każdy krok rozwoju działa od razu w kontenerze z testowalnym API

### Główne zasady:
1. **Każde zadanie = nowy endpoint API** który można przetestować curl'em
2. **Progresywny rozwój** - kontener rośnie z każdym zadaniem
3. **Zero setup** - `docker compose up` i wszystko działa
4. **Instant feedback** - każda zmiana widoczna przez API

---

## 📋 Faza 0: Minimal Container Foundation (2 godziny)

### Zadanie 0.1: Minimalny kontener FastAPI (45 min)

**Cel**: Najprostszy możliwy kontener z endpointem testującym routing

**Pliki do stworzenia**:

```dockerfile
# Dockerfile.minimal
FROM python:3.11-slim
WORKDIR /app
COPY requirements.minimal.txt .
RUN pip install -r requirements.minimal.txt
COPY app.py .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```python
# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="AI Writing Flow - Container First")

class ContentRequest(BaseModel):
    title: str
    content_type: str = "STANDARD"  # STANDARD, TECHNICAL, VIRAL
    platform: str = "LinkedIn"
    content_ownership: str = "EXTERNAL"  # EXTERNAL, ORIGINAL

@app.get("/")
def root():
    return {"status": "ok", "service": "ai-writing-flow"}

@app.get("/health")
def health():
    return {"status": "healthy", "container": "running"}

@app.post("/api/test-routing")
def test_routing(content: ContentRequest):
    """Test endpoint pokazujący że routing działa"""
    # Podstawowa logika routingu
    if content.content_ownership == "ORIGINAL":
        route = "skip_research_flow"
    elif content.content_type == "TECHNICAL":
        route = "technical_deep_dive_flow"
    elif content.content_type == "VIRAL":
        route = "viral_engagement_flow"
    else:
        route = "standard_editorial_flow"
    
    return {
        "status": "routed",
        "input": content.dict(),
        "route_decision": route,
        "skip_research": content.content_ownership == "ORIGINAL",
        "container_id": "ai-writing-flow-v1"
    }
```

```txt
# requirements.minimal.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

**Test**:
```bash
# Build i uruchom
docker build -f Dockerfile.minimal -t ai-writing-flow:minimal .
docker run -p 8000:8000 ai-writing-flow:minimal

# Testuj routing
curl -X POST http://localhost:8000/api/test-routing \
  -H "Content-Type: application/json" \
  -d '{"title": "AI Article", "content_ownership": "ORIGINAL"}'

# Oczekiwany wynik:
{
  "status": "routed",
  "route_decision": "skip_research_flow",
  "skip_research": true
}
```

**Success Criteria**:
- ✅ Kontener buduje się < 2 min
- ✅ Endpoint /api/test-routing poprawnie routuje ORIGINAL vs EXTERNAL
- ✅ Health check działa

---

### Zadanie 0.2: Docker Compose Foundation (30 min)

**Cel**: Docker Compose który będzie rósł z każdym zadaniem

```yaml
# docker-compose.yml
version: '3.8'

services:
  ai-writing-flow:
    build:
      context: .
      dockerfile: Dockerfile.minimal
    ports:
      - "8000:8000"
    environment:
      - ENV=development
      - LOG_LEVEL=debug
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - ./app.py:/app/app.py  # Hot reload dla development
```

**Test**:
```bash
docker compose up -d
docker compose ps  # Sprawdź że kontener jest healthy
curl http://localhost:8000/health
docker compose logs -f  # Zobacz logi
```

---

### Zadanie 0.3: Automated Container Tests (45 min)

**Cel**: Framework do testowania każdego nowego endpointu

```python
# tests/test_container_api.py
import requests
import pytest
import time

BASE_URL = "http://localhost:8000"

def wait_for_api(timeout=30):
    """Czekaj aż API będzie dostępne"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def test_container_health():
    """Test że kontener odpowiada"""
    assert wait_for_api(), "API nie odpowiada po 30 sekundach"
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_routing_original_content():
    """Test że ORIGINAL content pomija research"""
    payload = {
        "title": "My Personal AI Journey",
        "content_ownership": "ORIGINAL",
        "content_type": "STANDARD"
    }
    
    response = requests.post(f"{BASE_URL}/api/test-routing", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["route_decision"] == "skip_research_flow"
    assert data["skip_research"] == True

def test_routing_external_technical():
    """Test że EXTERNAL TECHNICAL idzie przez deep research"""
    payload = {
        "title": "Kubernetes Architecture Deep Dive",
        "content_ownership": "EXTERNAL",
        "content_type": "TECHNICAL"
    }
    
    response = requests.post(f"{BASE_URL}/api/test-routing", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["route_decision"] == "technical_deep_dive_flow"
    assert data["skip_research"] == False
```

```makefile
# Makefile
.PHONY: test

test:
	docker compose up -d
	@echo "Czekam na start kontenera..."
	@sleep 5
	pytest tests/test_container_api.py -v
	
clean:
	docker compose down

full-test: clean test
	@echo "✅ Wszystkie testy przeszły!"
```

**Test**:
```bash
make full-test
```

---

## 📋 Faza 1: CrewAI Integration Container (1 dzień)

### Zadanie 1.1: Research Agent Endpoint (2h)

**Cel**: Dodaj endpoint który wykonuje research przez CrewAI

```python
# app.py - rozszerzenie
from crewai import Agent, Task, Crew
import os

# Dodaj do istniejącego app.py

class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"  # quick, standard, deep
    skip_research: bool = False

@app.post("/api/research")
async def execute_research(request: ResearchRequest):
    """Wykonuje research używając CrewAI Agent"""
    
    if request.skip_research:
        return {
            "status": "skipped",
            "reason": "skip_research flag is True",
            "topic": request.topic,
            "findings": []
        }
    
    # Stwórz Research Agent
    researcher = Agent(
        role="Senior Research Analyst",
        goal=f"Research comprehensive information about {request.topic}",
        backstory="Expert researcher with access to vast knowledge",
        verbose=True
    )
    
    # Stwórz task
    research_task = Task(
        description=f"""
        Research the topic: {request.topic}
        Depth level: {request.depth}
        
        Provide:
        1. Key concepts and definitions
        2. Current trends and developments
        3. Best practices
        4. Common challenges
        """,
        agent=researcher,
        expected_output="Comprehensive research findings"
    )
    
    # Wykonaj research
    crew = Crew(
        agents=[researcher],
        tasks=[research_task],
        verbose=True
    )
    
    try:
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "topic": request.topic,
            "depth": request.depth,
            "findings": {
                "summary": str(result),
                "key_points": extract_key_points(str(result)),
                "word_count": len(str(result).split())
            },
            "execution_time_ms": 2500  # W prawdziwej implementacji zmierz czas
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "topic": request.topic
        }

def extract_key_points(text: str) -> list:
    """Wyciągnij kluczowe punkty z tekstu"""
    # Prosta heurystyka - w produkcji użyj NLP
    lines = text.split('\n')
    key_points = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20][:5]
    return key_points
```

**Update Dockerfile**:
```dockerfile
# Dockerfile - dodaj CrewAI
FROM python:3.11-slim
WORKDIR /app

# System dependencies dla CrewAI
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

```txt
# requirements.txt - rozszerzone
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
crewai==0.1.0
langchain==0.1.0
openai==1.0.0
```

**Test**:
```bash
# Test research endpoint
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "Container-First Development", "depth": "standard"}'

# Test skip research
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "My Story", "skip_research": true}'
```

---

### Zadanie 1.2: Writer Agent Endpoint (2h)

**Cel**: Dodaj endpoint który generuje content przez WriterAgent

```python
@app.post("/api/generate-draft")
async def generate_draft(content: ContentRequest, research_data: dict = None):
    """Generuje draft używając CrewAI Writer Agent"""
    
    # Writer Agent
    writer = Agent(
        role=f"{content.platform} Content Writer",
        goal=f"Write engaging {content.platform} content about {content.title}",
        backstory=f"Expert {content.platform} content creator",
        verbose=True
    )
    
    # Context z research (jeśli jest)
    context = ""
    if research_data and research_data.get("findings"):
        context = f"Research findings: {research_data['findings']['summary']}"
    
    # Writing task
    writing_task = Task(
        description=f"""
        Write {content.platform} content about: {content.title}
        Content type: {content.content_type}
        
        {context}
        
        Requirements:
        - Optimize for {content.platform} best practices
        - Target length: {"280 chars" if content.platform == "Twitter" else "500-1000 words"}
        - Include engaging hook
        - Add call to action
        """,
        agent=writer,
        expected_output=f"Complete {content.platform} post"
    )
    
    crew = Crew(agents=[writer], tasks=[writing_task])
    
    try:
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "draft": {
                "title": content.title,
                "content": str(result),
                "platform": content.platform,
                "word_count": len(str(result).split()),
                "optimized_for": content.platform
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "content_type": content.content_type,
                "used_research": research_data is not None
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

---

### Zadanie 1.3: Complete Flow Endpoint (2h)

**Cel**: Połącz routing + research + writing w jeden flow

```python
@app.post("/api/execute-flow")
async def execute_complete_flow(content: ContentRequest):
    """Wykonuje kompletny flow: routing → research → writing"""
    
    execution_log = []
    start_time = datetime.now()
    
    # Step 1: Routing
    routing_result = test_routing(content)
    execution_log.append({
        "step": "routing",
        "result": routing_result,
        "duration_ms": 50
    })
    
    # Step 2: Research (jeśli potrzebny)
    research_result = None
    if not routing_result["skip_research"]:
        research_request = ResearchRequest(
            topic=content.title,
            depth="deep" if content.content_type == "TECHNICAL" else "standard"
        )
        research_result = await execute_research(research_request)
        execution_log.append({
            "step": "research",
            "result": research_result,
            "duration_ms": 2500
        })
    
    # Step 3: Generate Draft
    draft_result = await generate_draft(content, research_result)
    execution_log.append({
        "step": "draft_generation",
        "result": draft_result,
        "duration_ms": 3000
    })
    
    total_duration = (datetime.now() - start_time).total_seconds() * 1000
    
    return {
        "flow_id": f"flow_{int(time.time())}",
        "status": "completed",
        "routing_decision": routing_result["route_decision"],
        "execution_log": execution_log,
        "final_draft": draft_result.get("draft"),
        "total_duration_ms": total_duration
    }
```

**Test kompletnego flow**:
```bash
# Test ORIGINAL content (skip research)
curl -X POST http://localhost:8000/api/execute-flow \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My AI Journey",
    "content_ownership": "ORIGINAL",
    "platform": "LinkedIn"
  }'

# Test EXTERNAL TECHNICAL (with research)
curl -X POST http://localhost:8000/api/execute-flow \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Kubernetes Best Practices",
    "content_ownership": "EXTERNAL",
    "content_type": "TECHNICAL",
    "platform": "Blog"
  }'
```

---

## 📋 Faza 2: Human Review Integration (1 dzień)

### Zadanie 2.1: Review Queue Endpoint (2h)

**Cel**: System kolejkowania dla human review

```python
# Dodaj do app.py
from enum import Enum
from uuid import uuid4

class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

# In-memory review queue (w produkcji użyj Redis)
review_queue = {}

@app.post("/api/request-review")
async def request_human_review(draft: dict, review_type: str = "editorial"):
    """Dodaje draft do kolejki review"""
    
    review_id = str(uuid4())
    review_item = {
        "review_id": review_id,
        "draft": draft,
        "review_type": review_type,
        "status": ReviewStatus.PENDING,
        "created_at": datetime.now().isoformat(),
        "reviewer": None,
        "feedback": None
    }
    
    review_queue[review_id] = review_item
    
    return {
        "review_id": review_id,
        "status": ReviewStatus.PENDING,
        "position_in_queue": len(review_queue),
        "review_url": f"/review/{review_id}",
        "estimated_wait_time": "5-10 minutes"
    }

@app.get("/api/review-queue")
async def get_review_queue(status: ReviewStatus = None):
    """Pobiera kolejkę review z opcjonalnym filtrem"""
    
    items = list(review_queue.values())
    
    if status:
        items = [item for item in items if item["status"] == status]
    
    return {
        "total_items": len(items),
        "items": items,
        "stats": {
            "pending": sum(1 for item in review_queue.values() if item["status"] == ReviewStatus.PENDING),
            "in_review": sum(1 for item in review_queue.values() if item["status"] == ReviewStatus.IN_REVIEW),
            "completed": sum(1 for item in review_queue.values() if item["status"] in [ReviewStatus.APPROVED, ReviewStatus.REJECTED])
        }
    }

@app.post("/api/submit-review/{review_id}")
async def submit_review(review_id: str, decision: str, feedback: str = "", reviewer: str = "anonymous"):
    """Submit human review decision"""
    
    if review_id not in review_queue:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review_item = review_queue[review_id]
    review_item.update({
        "status": decision,
        "feedback": feedback,
        "reviewer": reviewer,
        "reviewed_at": datetime.now().isoformat()
    })
    
    return {
        "review_id": review_id,
        "status": "review_submitted",
        "decision": decision
    }
```

---

### Zadanie 2.2: Review UI Endpoint (1h)

**Cel**: Prosty HTML interface dla reviewerów

```python
from fastapi.responses import HTMLResponse

@app.get("/review/{review_id}", response_class=HTMLResponse)
async def review_interface(review_id: str):
    """HTML interface dla human review"""
    
    if review_id not in review_queue:
        return "<h1>Review not found</h1>"
    
    item = review_queue[review_id]
    draft = item["draft"]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Review: {draft.get('title', 'Untitled')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .draft {{ background: #f0f0f0; padding: 20px; margin: 20px 0; }}
            .buttons {{ margin: 20px 0; }}
            button {{ padding: 10px 20px; margin: 0 10px; cursor: pointer; }}
            .approve {{ background: #28a745; color: white; }}
            .reject {{ background: #dc3545; color: white; }}
            .revise {{ background: #ffc107; }}
            textarea {{ width: 100%; min-height: 100px; }}
        </style>
    </head>
    <body>
        <h1>Content Review</h1>
        <p>Review ID: {review_id}</p>
        <p>Platform: {draft.get('platform', 'Unknown')}</p>
        
        <div class="draft">
            <h2>{draft.get('title', 'Untitled')}</h2>
            <p>{draft.get('content', 'No content')}</p>
            <p><small>Word count: {draft.get('word_count', 0)}</small></p>
        </div>
        
        <h3>Your Review</h3>
        <textarea id="feedback" placeholder="Add your feedback here..."></textarea>
        
        <div class="buttons">
            <button class="approve" onclick="submitReview('approved')">✅ Approve</button>
            <button class="revise" onclick="submitReview('needs_revision')">✏️ Request Revision</button>
            <button class="reject" onclick="submitReview('rejected')">❌ Reject</button>
        </div>
        
        <script>
            async function submitReview(decision) {{
                const feedback = document.getElementById('feedback').value;
                
                const response = await fetch('/api/submit-review/{review_id}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        decision: decision,
                        feedback: feedback,
                        reviewer: 'web_reviewer'
                    }})
                }});
                
                if (response.ok) {{
                    alert('Review submitted!');
                    window.location.href = '/api/review-queue';
                }} else {{
                    alert('Error submitting review');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return html
```

---

### Zadanie 2.3: Flow z Human Review (2h)

**Cel**: Rozszerz complete flow o human review checkpoint

```python
@app.post("/api/execute-flow-with-review")
async def execute_flow_with_human_review(content: ContentRequest, require_review: bool = True):
    """Complete flow z opcjonalnym human review"""
    
    # Wykonaj podstawowy flow
    flow_result = await execute_complete_flow(content)
    
    if not require_review:
        return flow_result
    
    # Dodaj do review queue
    if flow_result["status"] == "completed" and flow_result["final_draft"]:
        review_request = await request_human_review(
            draft=flow_result["final_draft"],
            review_type="editorial"
        )
        
        flow_result["human_review"] = {
            "required": True,
            "review_id": review_request["review_id"],
            "status": "pending",
            "review_url": review_request["review_url"]
        }
    
    return flow_result

@app.get("/api/flow-status/{flow_id}")
async def get_flow_status(flow_id: str):
    """Sprawdź status flow włącznie z review"""
    # W prawdziwej implementacji pobierz z bazy
    # Na razie zwróć mock
    return {
        "flow_id": flow_id,
        "status": "waiting_for_review",
        "stages_completed": ["routing", "research", "draft_generation"],
        "current_stage": "human_review",
        "review_status": "pending"
    }
```

---

## 📋 Faza 3: Production Container (1 dzień)

### Zadanie 3.1: Multi-stage Dockerfile (1h)

**Cel**: Produkcyjny Dockerfile z optymalizacją

```dockerfile
# Dockerfile.production
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser templates templates/
COPY --chown=appuser:appuser static static/

USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

### Zadanie 3.2: Redis + Knowledge Base Integration (2h)

**Cel**: Pełny stack z Redis i Knowledge Base

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  ai-writing-flow:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - KNOWLEDGE_BASE_URL=http://knowledge-base:8082
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      redis:
        condition: service_healthy
      knowledge-base:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  knowledge-base:
    image: chromadb/chroma:latest
    ports:
      - "8082:8000"
    environment:
      - ANONYMIZED_TELEMETRY=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - ai-writing-flow
    restart: unless-stopped

networks:
  default:
    driver: bridge

volumes:
  redis-data:
  chroma-data:
```

```python
# app.py - dodaj Redis support
import redis
from typing import Optional

# Redis connection
redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        redis_client.ping()
        print("✅ Redis connected")
    except:
        print("⚠️ Redis not available - using in-memory storage")

# Update review queue to use Redis
async def request_human_review(draft: dict, review_type: str = "editorial"):
    """Dodaje draft do kolejki review (Redis-backed)"""
    
    review_id = str(uuid4())
    review_item = {
        "review_id": review_id,
        "draft": json.dumps(draft),  # Redis wymaga string
        "review_type": review_type,
        "status": ReviewStatus.PENDING,
        "created_at": datetime.now().isoformat()
    }
    
    # Save to Redis
    try:
        redis_client.hset(f"review:{review_id}", mapping=review_item)
        redis_client.zadd("review_queue", {review_id: time.time()})
    except:
        # Fallback to in-memory
        review_queue[review_id] = review_item
    
    return {"review_id": review_id, "status": ReviewStatus.PENDING}
```

---

### Zadanie 3.3: Monitoring Dashboard (2h)

**Cel**: Dashboard z metrykami systemu

```python
@app.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard():
    """Live monitoring dashboard"""
    
    # Gather metrics
    try:
        redis_info = redis_client.info()
        redis_status = "connected"
    except:
        redis_info = {}
        redis_status = "disconnected"
    
    # System metrics
    import psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Business metrics
    total_flows = redis_client.get("metrics:total_flows") or 0
    total_reviews = redis_client.zcard("review_queue") or len(review_queue)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Writing Flow - Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #f5f5f5; 
            }}
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
            }}
            .metrics {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin: 20px 0; 
            }}
            .metric {{ 
                background: white; 
                padding: 20px; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            }}
            .metric h3 {{ 
                margin: 0 0 10px 0; 
                color: #333; 
            }}
            .metric .value {{ 
                font-size: 2em; 
                font-weight: bold; 
                color: #2196F3; 
            }}
            .status {{ 
                padding: 5px 10px; 
                border-radius: 4px; 
                display: inline-block; 
            }}
            .status.connected {{ 
                background: #4CAF50; 
                color: white; 
            }}
            .status.disconnected {{ 
                background: #f44336; 
                color: white; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 AI Writing Flow - Live Dashboard</h1>
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="metrics">
                <div class="metric">
                    <h3>System Status</h3>
                    <div class="value">Healthy</div>
                    <p>CPU: {cpu_percent}%</p>
                    <p>Memory: {memory.percent}%</p>
                </div>
                
                <div class="metric">
                    <h3>Redis Status</h3>
                    <div class="status {redis_status}">{redis_status.upper()}</div>
                    <p>Keys: {redis_info.get('db0', {}).get('keys', 0)}</p>
                </div>
                
                <div class="metric">
                    <h3>Total Flows</h3>
                    <div class="value">{total_flows}</div>
                    <p>Processed today</p>
                </div>
                
                <div class="metric">
                    <h3>Review Queue</h3>
                    <div class="value">{total_reviews}</div>
                    <p>Pending reviews</p>
                </div>
            </div>
            
            <h2>Recent Activity</h2>
            <div id="activity">
                <p>Loading recent activity...</p>
            </div>
            
            <script>
                // Auto-refresh activity feed
                async function loadActivity() {{
                    try {{
                        const response = await fetch('/api/recent-activity');
                        const data = await response.json();
                        
                        const activityHtml = data.activities
                            .map(a => `<p>$ {{a.timestamp}} - $ {{a.action}} - $ {{a.details}}</p>`)
                            .join('');
                            
                        document.getElementById('activity').innerHTML = activityHtml || '<p>No recent activity</p>';
                    }} catch (e) {{
                        console.error('Failed to load activity:', e);
                    }}
                }}
                
                loadActivity();
                setInterval(loadActivity, 5000);
            </script>
        </div>
    </body>
    </html>
    """
    
    return html

@app.get("/api/recent-activity")
async def get_recent_activity():
    """Get recent system activity"""
    # Mock data - w produkcji pobierz z Redis
    activities = [
        {
            "timestamp": datetime.now().isoformat(),
            "action": "flow_executed",
            "details": "Technical content flow completed"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "action": "review_submitted",
            "details": "Content approved by senior_editor"
        }
    ]
    
    return {"activities": activities}
```

---

## 🎯 Finalne Testy E2E

### Test Script
```bash
#!/bin/bash
# test-e2e.sh

echo "🧪 AI Writing Flow - E2E Container Tests"

# 1. Start services
echo "1️⃣ Starting services..."
docker compose -f docker-compose.production.yml up -d

# 2. Wait for health
echo "2️⃣ Waiting for services..."
sleep 30

# 3. Test routing
echo "3️⃣ Testing routing..."
curl -s -X POST http://localhost:8000/api/test-routing \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content_ownership": "ORIGINAL"}' \
  | jq .route_decision

# 4. Test complete flow
echo "4️⃣ Testing complete flow..."
FLOW_RESPONSE=$(curl -s -X POST http://localhost:8000/api/execute-flow \
  -H "Content-Type: application/json" \
  -d '{"title": "Container Best Practices", "content_type": "TECHNICAL"}')

echo "$FLOW_RESPONSE" | jq .status

# 5. Test with review
echo "5️⃣ Testing flow with review..."
REVIEW_RESPONSE=$(curl -s -X POST http://localhost:8000/api/execute-flow-with-review \
  -H "Content-Type: application/json" \
  -d '{"title": "AI Future", "platform": "LinkedIn"}')

REVIEW_ID=$(echo "$REVIEW_RESPONSE" | jq -r .human_review.review_id)
echo "Review ID: $REVIEW_ID"

# 6. Check dashboard
echo "6️⃣ Checking dashboard..."
curl -s http://localhost/dashboard | grep -q "AI Writing Flow" && echo "✅ Dashboard OK"

# 7. Submit review
echo "7️⃣ Submitting review..."
curl -s -X POST http://localhost:8000/api/submit-review/$REVIEW_ID \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "feedback": "Great content!"}' \
  | jq .status

# 8. Check metrics
echo "8️⃣ Final metrics..."
curl -s http://localhost:8000/api/system-metrics | jq .

echo "✅ All tests completed!"
```

---

## 📊 Podsumowanie Container-First Approach

### Co osiągnęliśmy:

1. **Zero Setup Time**
   - `docker compose up` - wszystko działa
   - Nie trzeba instalować Python, dependencies, etc.

2. **Testowalne API od pierwszego dnia**
   - Każde zadanie = nowy endpoint
   - Curl/httpie do testowania każdej funkcji

3. **Progresywny rozwój**
   - Zaczynamy od 50 linii kodu
   - Każde zadanie dodaje nową funkcjonalność
   - Zawsze mamy działający system

4. **Production Ready**
   - Health checks
   - Monitoring dashboard
   - Redis dla persistence
   - Nginx load balancer

5. **Human-in-the-Loop**
   - Web UI dla reviewerów
   - API dla integracji
   - Queue management

### Kluczowe różnice vs tradycyjne podejście:

| Tradycyjne | Container-First |
|------------|-----------------|
| Najpierw cały kod, potem testy | Każda linia kodu od razu testowalna |
| Konteneryzacja na końcu | Kontener od pierwszego dnia |
| Skomplikowany setup | docker compose up |
| Trudne debugowanie | curl do każdego endpointu |
| Deployment jako afterthought | Production-ready od początku |

### Next Steps:

1. **Kubernetes deployment** - Helm charts
2. **CI/CD pipeline** - GitHub Actions
3. **Observability** - Prometheus + Grafana
4. **API Gateway** - Kong/Traefik
5. **Message Queue** - RabbitMQ/Kafka dla async

Ten plan transformuje AI Writing Flow w nowoczesny, container-first system gdzie każdy krok jest testowalny i produkcyjny od pierwszego dnia.