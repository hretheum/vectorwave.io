# Vector Wave - AI Content Generation Platform

AI-powered content generation platform with comprehensive automated auditing

## 🚀 Overview

Vector Wave is an advanced content generation platform that uses AI agents to automatically create, optimize, and publish content across multiple channels. The platform includes a comprehensive audit framework for continuous monitoring and quality assurance.

### 🎯 MAJOR MILESTONE ACHIEVED (2025-08-09): Phase 2/3 Migration Complete

**Vector Wave successfully completed 9 critical migration tasks**, transforming from hardcoded rules to a modern ChromaDB-centric architecture. This represents the largest architectural upgrade in the project's history.

#### ✅ Migration Achievements:
- **Zero Hardcoded Rules**: Eliminated 355+ scattered validation rules
- **Service-Oriented Architecture**: All CrewAI agents now communicate via HTTP
- **ChromaDB-Centric Validation**: Editorial Service provides unified rule management
- **Multi-Platform Orchestration**: Enhanced publishing system for LinkedIn, Twitter, newsletters
- **Future-Ready Analytics**: Extensible analytics interface for advanced insights
- **Circuit Breaker Resilience**: Fault-tolerant service integrations
- **Production-Ready Performance**: P95 latency < 200ms across all workflows

🚢 **Port Management**: All services use coordinated port allocation. See [PORT_ALLOCATION.md](./PORT_ALLOCATION.md) for current port assignments and conflict resolution.

### 🏆 Production-Ready AI Kolegium System (2025-08-06)

Vector Wave AI Kolegium has achieved **complete production readiness** with all phases implemented:

### 🎯 Core Production Features

#### ✅ LINEAR FLOW ARCHITECTURE (Phase 2-4 COMPLETED)
- **Zero infinite loops** - Complete elimination of @router/@listen patterns
- **Linear execution chain** - Sequential flow with comprehensive guards
- **Thread-safe operations** - RLock protection for concurrent access
- **Quality gates** - 5 automated validation rules
- **Performance optimized** - <30s execution, <100MB memory usage

#### ✅ ENTERPRISE MONITORING STACK (Phase 3 COMPLETED)
- **Real-time KPI tracking** - FlowMetrics with 698+ lines of monitoring code
- **Multi-channel alerting** - Console, webhook, email notifications
- **Dashboard API** - Time-series metrics aggregation
- **Comprehensive storage** - SQLite + file backends with retention
- **Observer pattern** - Real-time metrics feeding alerting system

#### ✅ AI ASSISTANT INTEGRATION (Phase 5 COMPLETED)
- **Natural language draft editing** - Chat with AI about your content
- **Conversation memory** - Maintains context across 20 messages
- **Streaming responses** - Real-time SSE for long operations
- **Intent recognition** - Understands when to use tools vs general chat
- **Comprehensive error handling** - User-friendly messages in Polish
- **Health monitoring** - `/api/chat/health` endpoint for diagnostics

#### ✅ TRUE AGENTIC RAG SYSTEM (Phase 6 COMPLETED)
- **Autonomous agent decisions** - Agent decides what and how to search
- **3-5 autonomous queries** per content generation
- **Unique results** - Same input produces different content each time
- **OpenAI Function Calling** - Native integration, no regex hacks
- **180 style guide rules** - Loaded from markdown with semantic search

#### ✅ CONTAINER-FIRST DEPLOYMENT (Phase 7 COMPLETED)
- **Zero local building** - Everything runs in Docker containers
- **One-command setup** - `make dev-setup` for new developers
- **Health monitoring** - Multi-component system status
- **Auto-scaling** - Resource-aware configuration
- **Production deployment** - Full CI/CD pipeline ready

## 📦 Project Structure

| Module | Repository | Description | Status | Production Ready |
|--------|------------|-------------|--------|-----------------|
| content | [content-library](https://github.com/hretheum/vector-wave-content) | Generated content storage and organization | 🟢 Active | ✅ Ready |
| ideas | [idea-bank](https://github.com/hretheum/vector-wave-ideas) | Content ideas and brainstorming storage | 🟡 In Development | 🔄 Planning |
| **kolegium** | [editorial-crew](https://github.com/hretheum/vector-wave-editorial-crew) | **AI Editorial System - PRODUCTION READY** | 🎯 **PRODUCTION** | ✅ **DEPLOYED** |
| linkedin | [linkedin-automation](https://github.com/hretheum/vector-wave-linkedin) 🔒 | LinkedIn post automation module | 🟡 In Development | 🔄 Planning |
| n8n | [workflow-automation](https://github.com/hretheum/vector-wave-n8n) 🔒 | n8n workflow automation | 🟢 Active | ✅ Ready |
| presenton | [presentation-generator](https://github.com/hretheum/vector-wave-presenton) 🔒 | AI-powered presentation generator | 🟢 Active | ✅ Ready |
| **publisher** | [multi-channel-publisher](https://github.com/hretheum/vector-wave-publisher) | **Multi-platform publishing automation** | 🎯 **PRODUCTION** | ✅ **READY** |

## 🛠️ Setup

### Clone with all submodules
```bash
git clone --recurse-submodules git@github.com:hretheum/vectorwave.io.git
cd vectorwave.io
```

### Update submodules
```bash
git submodule update --init --recursive
```

### Work with specific module
```bash
cd module-name
git checkout main
git pull origin main
# make changes...
git add .
git commit -m "Your changes"
git push origin main
```

### Update submodule reference in main repo
```bash
cd ..
git add module-name
git commit -m "Update module-name to latest version"
git push
```

## 🤖 Core System Features

### 🏆 Production Features
- **Linear Flow Architecture** - Zero infinite loops with comprehensive monitoring
- **Enterprise Monitoring** - Real-time KPIs, alerting, and quality gates
- **AI Assistant Integration** - Natural language draft editing with memory
- **TRUE Agentic RAG** - Autonomous style guide search with unique results
- **Container-First Deployment** - Full Docker containerization with health checks
- **FastAPI Integration** - Complete REST API with OpenAPI documentation

### 🚀 Content Generation
- **5 Core AI Agents** - Research, Audience, Writer, Style, Quality crews
- **Multi-Platform Support** - LinkedIn, Twitter, newsletters optimization
- **Style Guide Integration** - 180 rules with semantic search
- **Quality Gates** - Automated validation and human review integration
- **Performance Optimized** - <30s execution, <100MB memory usage

### 📋 Management & Monitoring
- **Comprehensive Auditing** - Multi-repo audit framework
- **Real-time Dashboards** - System health and performance metrics
- **Quality Assurance** - 277+ tests with 100% coverage
- **Developer Tools** - One-command setup and automated workflows

## 🔍 System Auditing

Vector Wave includes a comprehensive audit framework for continuous monitoring and quality assurance across all submodules.

### 🏆 Kolegium Production System (Recommended Start)

For the production-ready AI writing system:

```bash
# 1. Setup Kolegium AI system
cd kolegium
make dev-setup                    # <1 minute setup
source .venv/bin/activate
make dev                         # Start development environment

# 2. Access the system
# - API Documentation: http://localhost:8003/docs
# - Health Dashboard: http://localhost:8083
# - System Health: http://localhost:8003/health

# 3. Generate content (example)
curl -X POST "http://localhost:8003/generate-draft" \
  -H "Content-Type: application/json" \
  -d '{"content": {"title": "AI in Marketing", "platform": "LinkedIn"}}'
```

### 📋 System Audit (Complete Analysis)

For comprehensive system analysis across all modules:

```bash
# Install audit dependencies
pip install requests psutil docker safety bandit radon pytest-cov

# Run comprehensive audit suite (30-45 minutes total)
python audit/scripts/health_check.py          # System health validation
python audit/scripts/security_audit.py        # Security vulnerability scan
python audit/scripts/performance_audit.py     # Performance & resource analysis
python audit/scripts/code_quality_audit.py    # Code quality & standards
python audit/scripts/architecture_review.py   # Architecture compliance
bash audit/scripts/business_continuity.sh     # Backup & recovery testing

# Kolegium-specific validation
cd kolegium
make test                        # Run 277+ tests (100% coverage)
make validate-env                # Environment validation
make health                      # System health check
```

### Audit Results

All audit results are stored in structured reports:

```
audit/reports/
├── continuous/     # Health check results (every 5 min when automated)
├── daily/          # Security & performance audits
├── weekly/         # Code quality reports  
├── monthly/        # Architecture reviews
└── quarterly/      # Business continuity assessments
```

### Quality Gates

Each audit type has defined quality gates:

- **Health Check**: All services UP, response time <2s
- **Security**: 0 critical issues, ≤5 high-severity issues
- **Performance**: 0 critical issues, ≤3 high-severity issues  
- **Code Quality**: Score ≥60, ≤15 complexity issues
- **Architecture**: Score ≥80, 0 critical architecture issues
- **Business Continuity**: ≥90% success rate for backup/recovery tests

### Emergency Audit

If you suspect system issues, run immediate diagnostic:

```bash
# Emergency health check (30 seconds)
python audit/scripts/health_check.py

# If performance issues suspected
python audit/scripts/performance_audit.py

# Check for security incidents  
python audit/scripts/security_audit.py
```

**📖 Audit Documentation**:
- [Quick Start Guide](./AUDIT_QUICK_START.md) - Fast-track audit execution
- [Complete Audit Plan](./VECTOR_WAVE_AUDIT_PLAN.md) - Comprehensive framework documentation

## 📚 Documentation

### Core Documentation
- [Vector Wave Audit Plan](./VECTOR_WAVE_AUDIT_PLAN.md) - Comprehensive audit framework
- [Project Context](./PROJECT_CONTEXT.md) - Current project status and roadmap
- [Tech Blog Style Guide](./tech-blog-styleguide.md)
- [5 Tech Blog Influencers Analysis](./5-tech-blog-influencers-analysis.md)

### Module Documentation
- [AI Kolegium](./kolegium/PROJECT_CONTEXT.md) - AI agents and CrewAI flows
- [Knowledge Base](./knowledge-base/KB_INTEGRATION_GUIDE.md) - Knowledge management system
- [LinkedIn Automation](./linkedin/PROJECT_CONTEXT.md) - LinkedIn publishing automation
- [n8n Workflows](./n8n/PROJECT_CONTEXT.md) - Content automation pipelines

## 🔐 License

See individual repositories for license information.
