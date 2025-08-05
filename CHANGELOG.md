# CHANGELOG - AI Kolegium Redakcyjne

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚀 Added - 2025-08-05

#### Redis Cache Layer - Sprint 3.2.1 & 3.2.2 ✅ COMPLETED
Sprint 3.2.1:
- ✅ Added Redis 7-alpine to docker-compose.minimal.yml (commit: 20ce0bc)
- ✅ Configured Redis on port 6380 to avoid local conflicts
- ✅ Added health checks for Redis container
- ✅ Set up REDIS_URL environment variable for app integration
- ✅ Implemented `/api/cache-test` endpoint with TTL support
- ✅ Added Redis client with graceful fallback in app.py
- ✅ Fixed Redis dependency in requirements-crewai.txt
- ✅ Verified cache functionality with successful test response

Sprint 3.2.2:
- ✅ Implemented caching for `/api/analyze-potential` endpoint
- ✅ Cache key format: `analysis:{folder_name}`
- ✅ Cache TTL: 300 seconds (5 minutes)
- ✅ Added `from_cache` field to response
- ✅ Verified: First call returns `from_cache: false`, subsequent calls `from_cache: true`
- 📊 Performance: Cache hits reduce response time from ~2ms to ~1ms
- 🚀 Next Sprint: 3.2.3 - ChromaDB for Style Guide with Naive RAG

#### Draft Generation Fixes & Optimization
- ✅ Fixed "Failed to start writing flow" error (was returning 404)
- ✅ Changed endpoint from `/api/generate-draft-v2` to `/api/generate-draft`
- ✅ Added data transformation in frontend proxy to match backend format
- ✅ Fixed response format mismatch (backend `status: "completed"` → frontend `success: true`)
- ✅ Implemented skip_research optimization for ORIGINAL content
- ✅ Added execution time tracking and optimization logging
- ✅ Reduced draft generation time by ~20% for ORIGINAL content (25s → 20s)

#### Container-First Development
- ✅ Updated pragmatic approach documentation after "linear flow" lessons learned
- ✅ Implemented Minimal Viable Change (MVC) methodology
- ✅ Total fix: ~30 lines of code vs potential 2-day complex solution

### 🚀 Added - 2025-08-03

#### Knowledge Base Integration
- ✅ Standalone Knowledge Base service running in Docker containers (port 8082)
- ✅ PostgreSQL + Redis + ChromaDB vector store integration
- ✅ Enhanced Knowledge Tools with adapter pattern for CrewAI
- ✅ Circuit breaker pattern for resilient KB connections
- ✅ Hybrid search strategies: KB_FIRST, FILE_FIRST, HYBRID, KB_ONLY
- ✅ Full integration tests for CrewAI agents with KB access
- ✅ Comprehensive KB integration documentation (`KNOWLEDGE_INTEGRATION_README.md`)

#### Infrastructure & Deployment
- ✅ Complete Docker Compose setup for development (`docker-compose.yml`)
- ✅ Production Docker Compose with GitHub Container Registry (`docker-compose.prod.yml`)
- ✅ GitHub Actions CI/CD pipeline (`.github/workflows/ci-cd.yml`)
- ✅ Watchtower configuration for automated deployments
- ✅ Prometheus + Grafana monitoring stack configuration
- ✅ Comprehensive deployment guide (`DEPLOYMENT_GUIDE.md`)
- ✅ Development start script (`scripts/start-dev.sh`)

#### Configuration & Environment
- ✅ Updated `.env.example` with all required variables
- ✅ Knowledge Base configuration (`knowledge_config.py`)
- ✅ Score threshold adjusted from 0.7 to 0.35 for better results
- ✅ OpenAI API key integration for CrewAI agents

### 📝 Changed

#### Documentation Updates
- 📄 Updated `PROJECT_CONTEXT.md` with current implementation status
- 📄 Updated `README.md` with Knowledge Base integration info
- 📄 Updated `ROADMAP.md` marking completed tasks
- 📄 Enhanced agent descriptions with KB capabilities

#### Configuration Changes
- 🔧 Changed default KB score threshold to 0.35
- 🔧 Updated KB_API_URL environment variable name for consistency
- 🔧 Added proper `.gitignore` for security

### 🐛 Fixed

- 🔧 Fixed async event loop issues in Knowledge Base adapter
- 🔧 Fixed tool decorator usage in test scripts
- 🔧 Fixed KB connection URL mismatch (8080 vs 8082)

### 🔒 Security

- 🔐 Added `.gitignore` to prevent committing sensitive files
- 🔐 Environment variables for all API keys and secrets
- 🔐 Proper secret management in CI/CD pipeline

## [0.2.0] - 2025-01-31

### Added
- AI Writing Flow implementation with 5 specialized agents
- CrewAI Flow architecture discovery
- Vector Wave styleguide integration
- Human-in-the-loop for controversial content

## [0.1.0] - 2025-01-17

### Added
- Initial Digital Ocean droplet setup (46.101.156.14)
- Basic project structure
- CrewAI installation and configuration
- Project documentation framework

---

## 📊 Summary of Current State (2025-08-03)

### ✅ Completed
- Phase 1 Infrastructure: Tasks 1.0, 1.1, 1.3, 1.4
- Knowledge Base fully integrated with CrewAI agents
- Docker containerization complete
- CI/CD pipeline ready for production

### 🔄 In Progress
- Task 1.2: AG-UI Event System integration
- Frontend development (React + TypeScript)

### 📋 Upcoming
- Task 1.5: PostgreSQL Event Store implementation
- Task 1.6: Redis integration for caching
- Phase 2: Core Agent Implementation

### 📈 Metrics
- Knowledge Base query response time: ~62ms average
- Docker images build time: <5 minutes
- Test coverage: Pending full implementation
- Agent integration success rate: 100%