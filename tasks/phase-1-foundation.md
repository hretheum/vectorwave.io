# PHASE 1: Foundation & Infrastructure

## 📋 Bloki Zadań Atomowych

### Blok 0: Infrastructure Setup ✅ [WYKONANY]
**Czas**: 2h | **Agent**: deployment-specialist | **Status**: COMPLETED 2025-01-17

**Task 1.0**: Setup Digital Ocean droplet infrastructure

#### Execution Summary:
Droplet został już skonfigurowany i działa:
- **Droplet ID**: 511009535
- **IP**: 46.101.156.14
- **Użytkownik**: editorial-ai (dostęp SSH: `ssh crew`)
- **System**: Ubuntu 22.04 (4 vCPU, 8GB RAM, 160GB SSD)
- **Docker**: Zainstalowany i skonfigurowany
- **Python venv**: /home/editorial-ai/venv z crewai 0.152.0, fastapi, redis, celery
- **Firewall**: Porty otwarte: SSH, HTTP, HTTPS, 8000-8010
- **docker-compose.yml**: Utworzony w /home/editorial-ai/

**Success Criteria** ✅:
- [x] SSH access as editorial-ai user works
- [x] Docker runs without sudo for editorial-ai user
- [x] Firewall rules active
- [x] Basic monitoring tools installed
- [x] Python environment setup complete

---

### Blok 1: Clean Architecture Foundation  
**Czas**: 3h | **Agent**: project-coder | **Dependencies**: Blok 0

**Task 1.1**: Implementacja Clean Architecture structure

#### Execution Steps:
1. **Work in local repository** (pracujemy LOKALNIE, nie na droplecie!)
   ```bash
   # W lokalnym środowisku deweloperskim
   cd /Users/hretheum/dev/bezrobocie/vector-wave/kolegium
   # Cały kod będzie budowany w GitHub Actions i deployowany jako kontenery
   ```

2. **Setup directory structure**
   ```bash
   mkdir -p src/{domains/{content,analytics,editorial,quality,orchestration},shared,interfaces}
   mkdir -p src/domains/content/{domain/{entities,value_objects,repositories,services},application/{use_cases,handlers,dto},infrastructure/{repositories,services,agents}}
   mkdir -p src/shared/{domain/{events,exceptions,value_objects},infrastructure/{agui,database,cache,monitoring,security},application/{events,services}}
   mkdir -p src/interfaces/{api/{controllers,websockets,dto},events/handlers,jobs/schedulers}
   mkdir -p tests/{unit,integration,e2e}
   mkdir -p docs/{api,user-guides,operations}
   ```

3. **Create basic domain entities**
   ```python
   # src/domains/content/domain/entities/topic.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import List, Optional
   from uuid import UUID, uuid4
   
   @dataclass
   class Topic:
       id: UUID
       title: str
       description: str
       url: str
       source: str
       discovered_at: datetime
       keywords: List[str]
       initial_score: float
       category: str
       sentiment: Optional[float] = None
       
       @classmethod
       def create(cls, title: str, description: str, url: str, source: str, 
                  keywords: List[str], category: str) -> 'Topic':
           return cls(
               id=uuid4(),
               title=title,
               description=description,
               url=url,
               source=source,
               discovered_at=datetime.utcnow(),
               keywords=keywords,
               initial_score=0.0,
               category=category
           )
   ```

4. **Create repository interfaces**
   ```python
   # src/domains/content/domain/repositories/topic_repository.py
   from abc import ABC, abstractmethod
   from typing import List, Optional
   from uuid import UUID
   
   from ..entities.topic import Topic
   
   class ITopicRepository(ABC):
       @abstractmethod
       async def save(self, topic: Topic) -> None:
           pass
           
       @abstractmethod
       async def find_by_id(self, topic_id: UUID) -> Optional[Topic]:
           pass
           
       @abstractmethod
       async def find_by_url(self, url: str) -> Optional[Topic]:
           pass
           
       @abstractmethod
       async def find_recent(self, limit: int = 50) -> List[Topic]:
           pass
   ```

5. **Setup dependency injection and requirements**
   ```python
   # requirements.txt
   fastapi==0.109.0
   uvicorn[standard]==0.27.0
   pydantic==2.5.3
   dependency-injector==4.41.0
   sqlalchemy==2.0.25
   alembic==1.13.1
   asyncpg==0.29.0
   redis==5.0.1
   python-multipart==0.0.6
   python-jose[cryptography]==3.3.0
   passlib[bcrypt]==1.7.4
   prometheus-client==0.19.0
   opentelemetry-api==1.22.0
   opentelemetry-sdk==1.22.0
   opentelemetry-instrumentation-fastapi==0.43b0
   pytest==7.4.4
   pytest-asyncio==0.23.3
   pytest-cov==4.1.0
   ```
   
   ```python
   # src/shared/infrastructure/container.py
   from dependency_injector import containers, providers
   from dependency_injector.wiring import Provide, inject
   
   class Container(containers.DeclarativeContainer):
       # Configuration
       config = providers.Configuration()
       
       # Database
       database = providers.Singleton(
           # Will be implemented in next task
       )
       
       # Repositories
       topic_repository = providers.Factory(
           # Will be implemented in task 1.5
       )
   ```

**Success Criteria**:
- [ ] Clean folder structure created
- [ ] Basic domain entities defined with proper typing
- [ ] Repository interfaces following DIP
- [ ] Dependency injection container setup

---

### Blok 2: AG-UI Event System Core
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 1

**Task 1.2**: AG-UI Event System podstawowy

#### Execution Steps:
1. **Define AG-UI event types**
   ```python
   # src/shared/domain/events/agui_events.py
   from enum import Enum
   from pydantic import BaseModel, Field
   from typing import Any, Dict, Optional
   from datetime import datetime
   from uuid import UUID, uuid4
   
   class AGUIEventType(Enum):
       # Core messaging
       MESSAGE = "message"
       MESSAGE_DELTA = "message_delta"
       
       # State management
       STATE_SYNC = "state_sync"
       STATE_UPDATE = "state_update"
       
       # Tool interaction
       TOOL_CALL = "tool_call"
       TOOL_RESULT = "tool_result"
       
       # UI generation
       UI_COMPONENT = "ui_component"
       UI_UPDATE = "ui_update"
       
       # Human interaction
       HUMAN_INPUT_REQUEST = "human_input_request"
       HUMAN_FEEDBACK = "human_feedback"
       
       # Progress tracking
       PROGRESS_UPDATE = "progress_update"
       TASK_COMPLETE = "task_complete"
       
       # Editorial specific
       TOPIC_DISCOVERED = "topic_discovered"
       EDITORIAL_DECISION = "editorial_decision"
       CONTENT_ANALYSIS = "content_analysis"
       QUALITY_ASSESSMENT = "quality_assessment"
   
   class AGUIEvent(BaseModel):
       id: UUID = Field(default_factory=uuid4)
       type: AGUIEventType
       data: Dict[str, Any]
       agent_id: Optional[str] = None
       timestamp: datetime = Field(default_factory=datetime.utcnow)
       session_id: Optional[str] = None
       correlation_id: Optional[str] = None
       user_id: Optional[str] = None
   ```

2. **Create event emitter**
   ```python
   # src/shared/infrastructure/agui/event_emitter.py
   import asyncio
   import json
   from typing import Set, List, Callable, Dict
   from fastapi import WebSocket
   import redis.asyncio as redis
   
   from src.shared.domain.events.agui_events import AGUIEvent
   
   class AGUIEventEmitter:
       def __init__(self, redis_client: redis.Redis):
           self.redis = redis_client
           self.connections: Set[WebSocket] = set()
           self.event_handlers: Dict[str, List[Callable]] = {}
           
       async def emit(self, event: AGUIEvent) -> None:
           """Emit event to all connected clients and Redis streams"""
           event_json = event.model_dump_json()
           
           # Store in Redis Stream for persistence
           await self.redis.xadd(
               "agui_events", 
               {"event": event_json},
               maxlen=10000  # Keep last 10k events
           )
           
           # Broadcast to WebSocket connections
           if self.connections:
               dead_connections = set()
               for connection in self.connections:
                   try:
                       await connection.send_text(event_json)
                   except Exception:
                       dead_connections.add(connection)
               
               self.connections -= dead_connections
               
           # Trigger local handlers
           handlers = self.event_handlers.get(event.type.value, [])
           for handler in handlers:
               try:
                   await handler(event)
               except Exception as e:
                   print(f"Event handler error: {e}")
       
       async def subscribe(self, event_type: str, handler: Callable) -> None:
           """Subscribe to specific event types"""
           if event_type not in self.event_handlers:
               self.event_handlers[event_type] = []
           self.event_handlers[event_type].append(handler)
       
       async def add_connection(self, websocket: WebSocket) -> None:
           """Add WebSocket connection"""
           await websocket.accept()
           self.connections.add(websocket)
           
       async def remove_connection(self, websocket: WebSocket) -> None:
           """Remove WebSocket connection"""
           self.connections.discard(websocket)
   ```

3. **WebSocket endpoint handler**
   ```python
   # src/interfaces/api/websockets/agui_websocket.py
   from fastapi import APIRouter, WebSocket, WebSocketDisconnect
   from dependency_injector.wiring import inject, Provide
   
   from src.shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   from src.shared.infrastructure.container import Container
   
   router = APIRouter()
   
   @router.websocket("/ws/agui")
   @inject
   async def agui_websocket(
       websocket: WebSocket,
       emitter: AGUIEventEmitter = Provide[Container.agui_emitter]
   ):
       await emitter.add_connection(websocket)
       try:
           while True:
               # Keep connection alive and handle client messages
               data = await websocket.receive_text()
               # Process client events if needed
               print(f"Received client message: {data}")
       except WebSocketDisconnect:
           await emitter.remove_connection(websocket)
   ```

4. **SSE endpoint for alternative transport**
   ```python
   # src/interfaces/api/controllers/sse_controller.py
   from fastapi import APIRouter
   from fastapi.responses import StreamingResponse
   from dependency_injector.wiring import inject, Provide
   import asyncio
   import json
   
   router = APIRouter()
   
   @router.get("/events/stream")
   @inject
   async def event_stream():
       """Server-Sent Events stream for AG-UI events"""
       async def generate():
           # This will be enhanced with Redis stream reading
           yield "data: {\"type\": \"connection_established\"}\n\n"
           
           while True:
               # Placeholder - will connect to Redis streams
               await asyncio.sleep(1)
               yield "data: {\"type\": \"heartbeat\", \"timestamp\": \"" + str(datetime.utcnow()) + "\"}\n\n"
       
       return StreamingResponse(
           generate(), 
           media_type="text/plain",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "X-Accel-Buffering": "no"
           }
       )
   ```

**Success Criteria**:
- [ ] AGUIEvent classes with full typing
- [ ] Event emitter with Redis persistence
- [ ] WebSocket handler functional
- [ ] SSE endpoint available
- [ ] Event subscription system working

---

### Blok 3: Docker Infrastructure
**Czas**: 3h | **Agent**: deployment-specialist | **Dependencies**: Blok 2

**Task 1.3**: Docker containers setup

#### Execution Steps:
1. **Create development docker-compose**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   
   services:
     api-gateway:
       build:
         context: ./services/api-gateway
         target: development
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://kolegium:dev_password@postgres:5432/kolegium
         - REDIS_URL=redis://redis:6379
         - PYTHONPATH=/app
         - RELOAD=true
       volumes:
         - ./src:/app/src
         - ./tests:/app/tests
       depends_on:
         - postgres
         - redis
       command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   
     postgres:
       image: postgres:15-alpine
       environment:
         - POSTGRES_DB=kolegium
         - POSTGRES_USER=kolegium
         - POSTGRES_PASSWORD=dev_password
       ports:
         - "5432:5432"
       volumes:
         - postgres_dev_data:/var/lib/postgresql/data
         - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
   
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_dev_data:/data
       command: redis-server --appendonly yes
   
     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
   
     grafana:
       image: grafana/grafana:latest
       ports:
         - "3001:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin
       volumes:
         - grafana_dev_data:/var/lib/grafana
   
   volumes:
     postgres_dev_data:
     redis_dev_data:
     grafana_dev_data:
   ```

2. **Create production docker-compose**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   
   services:
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx/nginx.conf:/etc/nginx/nginx.conf
         - /etc/letsencrypt:/etc/letsencrypt
       depends_on:
         - api-gateway
       restart: unless-stopped
   
     api-gateway:
       image: ghcr.io/username/kolegium-api-gateway:latest
       environment:
         - DATABASE_URL=postgresql://kolegium:${DB_PASSWORD}@postgres:5432/kolegium
         - REDIS_URL=redis://redis:6379
         - JWT_SECRET=${JWT_SECRET}
       depends_on:
         - postgres
         - redis
       restart: unless-stopped
       labels:
         - "com.centurylinklabs.watchtower.enable=true"
   
     postgres:
       image: postgres:15-alpine
       environment:
         - POSTGRES_DB=kolegium
         - POSTGRES_USER=kolegium
         - POSTGRES_PASSWORD=${DB_PASSWORD}
       volumes:
         - postgres_prod_data:/var/lib/postgresql/data
       restart: unless-stopped
   
     redis:
       image: redis:7-alpine
       volumes:
         - redis_prod_data:/data
       command: redis-server --appendonly yes
       restart: unless-stopped
   
     watchtower:
       image: containrrr/watchtower:latest
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
       environment:
         - WATCHTOWER_POLL_INTERVAL=60
         - WATCHTOWER_CLEANUP=true
         - WATCHTOWER_LABEL_ENABLE=true
       command: --interval 60 --cleanup --label-enable
       restart: unless-stopped
   
   volumes:
     postgres_prod_data:
     redis_prod_data:
   ```

3. **Create API Gateway Dockerfile**
   ```dockerfile
   # services/api-gateway/Dockerfile
   FROM python:3.11-slim as base
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc g++ python3-dev libpq-dev curl \
       && rm -rf /var/lib/apt/lists/*
   
   # Create user
   RUN useradd -m -u 1000 app && chown -R app:app /app
   USER app
   
   # Install Python dependencies
   COPY --chown=app:app requirements.txt .
   RUN pip install --no-cache-dir --user -r requirements.txt
   
   ENV PATH="/home/app/.local/bin:${PATH}"
   
   # Development stage
   FROM base as development
   RUN pip install --no-cache-dir --user pytest pytest-cov pytest-asyncio
   COPY --chown=app:app . .
   CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
   
   # Production stage
   FROM base as production
   COPY --chown=app:app . .
   
   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:8000/health || exit 1
   
   EXPOSE 8000
   CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

4. **Create basic FastAPI application**
   ```python
   # services/api-gateway/src/main.py
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   import redis.asyncio as redis
   
   from src.shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   from src.interfaces.api.websockets.agui_websocket import router as ws_router
   from src.interfaces.api.controllers.sse_controller import router as sse_router
   
   app = FastAPI(title="AI Kolegium Redakcyjne", version="0.1.0")
   
   # CORS
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   
   # Global state
   redis_client = None
   agui_emitter = None
   
   @app.on_event("startup")
   async def startup():
       global redis_client, agui_emitter
       redis_client = redis.from_url("redis://redis:6379")
       agui_emitter = AGUIEventEmitter(redis_client)
   
   @app.on_event("shutdown")
   async def shutdown():
       if redis_client:
           await redis_client.close()
   
   @app.get("/health")
   async def health():
       return {"status": "healthy", "service": "api-gateway"}
   
   # Include routers
   app.include_router(ws_router, prefix="/ws")
   app.include_router(sse_router, prefix="/api")
   ```

**Success Criteria**:
- [ ] Development docker-compose działa lokalnie
- [ ] Production docker-compose configured
- [ ] Multi-stage Dockerfiles dla optimization
- [ ] Health checks dla wszystkich services
- [ ] Basic FastAPI app responding

---

### Blok 4: CI/CD Foundation
**Czas**: 4h | **Agent**: deployment-specialist | **Dependencies**: Blok 3

**Task 1.4**: GitHub Actions CI/CD pipeline

#### Execution Steps:
1. **Create basic CI workflow**
   ```yaml
   # .github/workflows/ci.yml
   name: CI Pipeline
   
   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main ]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       
       services:
         postgres:
           image: postgres:15-alpine
           env:
             POSTGRES_DB: test_kolegium
             POSTGRES_USER: test_user
             POSTGRES_PASSWORD: test_pass
           options: >-
             --health-cmd pg_isready
             --health-interval 10s
             --health-timeout 5s
             --health-retries 5
         
         redis:
           image: redis:7-alpine
           options: >-
             --health-cmd "redis-cli ping"
             --health-interval 10s
             --health-timeout 5s
             --health-retries 5
       
       steps:
       - uses: actions/checkout@v4
       
       - name: Set up Python 3.11
         uses: actions/setup-python@v4
         with:
           python-version: '3.11'
           
       - name: Cache dependencies
         uses: actions/cache@v3
         with:
           path: ~/.cache/pip
           key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
           
       - name: Install dependencies
         run: |
           cd services/api-gateway
           python -m venv .venv
           source .venv/bin/activate
           python -m pip install --upgrade pip
           pip install -r requirements.txt
           pip install pytest pytest-cov pytest-asyncio
           
       - name: Run tests
         run: |
           cd services/api-gateway
           python -m pytest tests/ --cov=src --cov-report=xml --cov-report=term-missing
           
       - name: Upload coverage to Codecov
         uses: codecov/codecov-action@v3
         with:
           file: ./services/api-gateway/coverage.xml
           flags: unittests
           name: codecov-umbrella
   ```

2. **Create deployment workflow**
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy to Production
   
   on:
     push:
       branches: [ main ]
   
   env:
     REGISTRY: ghcr.io
     IMAGE_NAME: ${{ github.repository }}
   
   jobs:
     build-and-deploy:
       runs-on: ubuntu-latest
       if: github.ref == 'refs/heads/main'
       
       steps:
       - uses: actions/checkout@v4
       
       - name: Log in to Container Registry
         uses: docker/login-action@v2
         with:
           registry: ${{ env.REGISTRY }}
           username: ${{ github.actor }}
           password: ${{ secrets.GITHUB_TOKEN }}
           
       - name: Extract metadata
         id: meta
         uses: docker/metadata-action@v4
         with:
           images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-api-gateway
           tags: |
             type=ref,event=branch
             type=sha,prefix={{branch}}-
             type=raw,value=latest,enable={{is_default_branch}}
             
       - name: Build and push Docker image
         uses: docker/build-push-action@v4
         with:
           context: ./services/api-gateway
           target: production
           push: true
           tags: ${{ steps.meta.outputs.tags }}
           labels: ${{ steps.meta.outputs.labels }}
           cache-from: type=gha
           cache-to: type=gha,mode=max
           
       - name: Deploy to Digital Ocean
         uses: appleboy/ssh-action@v0.1.5
         with:
           host: 46.101.156.14
           username: editorial-ai
           key: ${{ secrets.DO_SSH_KEY }}
           script: |
             cd /home/editorial-ai
             # NO git operations on droplet! Only pulling Docker images
             docker-compose -f docker-compose.prod.yml pull api-gateway
             docker-compose -f docker-compose.prod.yml up -d api-gateway
             
             # Health check
             sleep 10
             curl -f http://localhost:8000/health || exit 1
             
       - name: Notify deployment
         if: always()
         run: |
           echo "Deployment completed with status: ${{ job.status }}"
   ```

3. **Setup GitHub repository secrets**
   ```bash
   # These need to be set in GitHub repository settings -> Secrets
   # DO_SSH_KEY: Private SSH key for Digital Ocean droplet
   # DB_PASSWORD: Production database password
   # JWT_SECRET: JWT signing secret
   ```

4. **Create docker-compose.prod.yml on droplet**
   ```bash
   # This file needs to be manually placed on droplet ONCE
   # at /home/editorial-ai/docker-compose.prod.yml
   # It will reference images from ghcr.io
   ```

5. **Create deployment verification script**
   ```bash
   #!/bin/bash
   # scripts/verify-deployment.sh
   
   set -e
   
   echo "🚀 Starting deployment..."
   
   # NO code pulling! Only Docker images from ghcr.io
   # All code is built in GitHub Actions and deployed as containers
   
   # Pull latest Docker images
   docker-compose -f docker-compose.prod.yml pull
   
   # Recreate services with new images
   docker-compose -f docker-compose.prod.yml up -d
   
   # Health check
   echo "⏳ Waiting for services to be healthy..."
   sleep 30
   
   # Check API Gateway
   if curl -f http://localhost:8000/health; then
       echo "✅ API Gateway is healthy"
   else
       echo "❌ API Gateway health check failed"
       exit 1
   fi
   
   # Check database connection
   if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U kolegium; then
       echo "✅ Database is healthy"
   else
       echo "❌ Database health check failed"
       exit 1
   fi
   
   echo "🎉 Deployment successful!"
   ```

**Success Criteria**:
- [ ] CI pipeline runs on PR/push
- [ ] Tests execute with >80% coverage
- [ ] Docker images build and push to ghcr.io
- [ ] Deploy script works on droplet
- [ ] Health checks verify deployment

**Deploy Test**: Po ukończeniu tego bloku, uruchom pierwszy deploy na droplet