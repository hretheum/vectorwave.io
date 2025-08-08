# Vector Wave Developer Onboarding

## 🎯 Architecture Overview

Vector Wave uses ChromaDB-first architecture with CrewAI agents.  
**Primary reference**: target-version/

### Key Architecture Principles
- **Zero hardcoded rules** - all validation through Editorial Service
- **CrewAI Linear Flow** - sequential processing only  
- **ChromaDB integration** - all rules sourced from vector database
- **Container-first** - everything runs in Docker
- **Multi-platform publishing** - LinkedIn, Twitter, Substack, Ghost, Beehiiv

## 🚀 Quick Start

### 1. Understanding the System
Read these documents in order:
1. `target-version/README.md` - System overview
2. `target-version/VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md` - Complete architecture
3. `target-version/CREWAI_INTEGRATION_ARCHITECTURE.md` - Agent implementation
4. `target-version/VECTOR_WAVE_MIGRATION_ROADMAP.md` - Implementation roadmap

### 2. Development Setup
```bash
# Clone and setup
git clone [repository]
cd vector-wave

# Initialize submodules
git submodule update --init --recursive

# Start development environment
make dev-setup

# Verify all services
make health-check
```

### 3. Port Allocation
**IMPORTANT**: Always check `PORT_ALLOCATION.md` before creating new services.

Key services:
- **8040**: Editorial Service (ChromaDB validation)
- **8042**: CrewAI Orchestrator  
- **8000**: ChromaDB vector database
- **8003**: AI Writing Flow

## 🔧 Development Workflow

### Creating New Features

1. **Check Architecture Compatibility**
   ```bash
   # Ensure your feature aligns with target architecture
   cat target-version/VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md
   ```

2. **Port Allocation**
   ```bash
   # Check available ports
   cat PORT_ALLOCATION.md
   # Reserve your port by updating the document
   ```

3. **ChromaDB Integration**
   - **NO hardcoded rules** - everything goes through Editorial Service
   - Use ChromaDB collections for all validation logic
   - Implement proper error handling and fallbacks

4. **CrewAI Integration**  
   - Use **Linear Flow pattern only** - no @router/@listen
   - Implement proper circuit breakers
   - Follow container-first approach

### Code Standards

#### ✅ DO:
- Use Editorial Service for all validation (port 8040)
- Implement proper error handling with structured responses
- Add comprehensive logging and monitoring
- Write tests with >80% coverage
- Document API endpoints with OpenAPI
- Follow container-first architecture

#### ❌ DON'T:
- Hardcode validation rules or forbidden phrases
- Use CrewAI @router/@listen patterns (causes infinite loops)
- Skip port allocation documentation
- Implement without proper monitoring
- Create services without health checks

## 🏗️ System Components

### Core Services

#### 1. Editorial Service (Port 8040)
- **Purpose**: Centralized validation using ChromaDB rules
- **Integration**: HTTP API for all validation requests
- **Usage**: All agents must validate content through this service

#### 2. CrewAI Orchestrator (Port 8042)
- **Purpose**: Agent coordination and flow execution
- **Pattern**: Linear Flow (Process.sequential)
- **Agents**: Research, Audience, Writer, Style, Quality

#### 3. ChromaDB (Port 8000)
- **Purpose**: Vector database for all style rules
- **Collections**: 355+ rules from styleguides/*.md
- **Search**: Semantic search for relevant validation rules

#### 4. AI Writing Flow (Port 8003)  
- **Purpose**: Main content generation pipeline
- **Integration**: Uses all above services
- **Output**: Multi-platform content generation

### Platform Adapters
- **LinkedIn** (Port 8088): Production-ready automation
- **Twitter** (Port 8083): Typefully API integration  
- **Ghost** (Port 8086): CMS publishing
- **Substack** (Port TBD): Newsletter publishing
- **Beehiiv** (Port 8084): Email marketing

## 🧪 Testing Strategy

### Test Categories
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Service-to-service communication
3. **Container Tests**: Full Docker environment testing
4. **End-to-End Tests**: Complete workflow validation

### Running Tests
```bash
# Unit tests
make test-unit

# Integration tests  
make test-integration

# Full test suite
make test-all

# Specific service tests
make test-editorial-service
make test-crewai-flow
```

## 📊 Monitoring & Debugging

### Health Checks
```bash
# Check all services
curl http://localhost:8040/health  # Editorial Service
curl http://localhost:8042/health  # CrewAI Orchestrator
curl http://localhost:8000/health  # ChromaDB
curl http://localhost:8003/health  # AI Writing Flow
```

### Metrics & Logs
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Dashboards and visualization (port 3000)
- **Structured Logging**: All services use structured JSON logs

### Common Debugging Scenarios

#### 1. Validation Failures
```bash
# Check Editorial Service logs
docker logs vector-wave-editorial-service

# Test validation directly
curl -X POST http://localhost:8040/validate/comprehensive \
  -H "Content-Type: application/json" \
  -d '{"content": "test content", "platform": "linkedin"}'
```

#### 2. CrewAI Agent Issues
```bash
# Check orchestrator logs
docker logs vector-wave-crewai-orchestrator

# Verify linear flow execution
curl http://localhost:8042/diagnostics
```

#### 3. ChromaDB Connection Issues
```bash
# Check ChromaDB status
curl http://localhost:8000/api/v1/heartbeat

# List collections
curl http://localhost:8000/api/v1/collections
```

## 🔄 Integration Patterns

### Content Generation Flow
1. **Input Processing**: Normalize and validate input
2. **Research Agent**: Gather relevant information
3. **Audience Agent**: Analyze target audience  
4. **Writer Agent**: Generate initial draft
5. **Style Agent**: Apply platform-specific rules
6. **Quality Agent**: Final validation and polish
7. **Editorial Service**: Comprehensive rule validation
8. **Platform Publishing**: Multi-channel distribution

### Error Handling
- Use structured error responses with error codes
- Implement proper retry mechanisms with exponential backoff
- Provide clear error messages for debugging
- Log all errors with correlation IDs

### Performance Optimization
- Use caching for frequently accessed rules
- Implement connection pooling for database connections
- Use async/await patterns for I/O operations
- Monitor and optimize based on metrics

## 📚 Additional Resources

### Documentation
- `target-version/COMPLETE_API_SPECIFICATIONS.md` - API reference
- `target-version/CHROMADB_SCHEMA_SPECIFICATION.md` - Database schema
- `PORT_ALLOCATION.md` - Infrastructure coordination
- `styleguides/` - Source material for validation rules

### Production Systems
- `publisher/` - Multi-channel publisher (85% complete)
- `linkedin/` - LinkedIn automation (production ready)
- `kolegium/` - AI agent system

### Historical Context
- `docs/historical/` - Previous implementation approaches
- `docs/integration/` - System integration documentation

## 🚨 Common Pitfalls

### Architecture Violations
- **Hardcoding rules**: Always use Editorial Service
- **Circular dependencies**: Use proper dependency injection
- **Infinite loops**: Stick to Linear Flow pattern
- **Port conflicts**: Always check and update PORT_ALLOCATION.md

### Development Issues
- **Container setup**: Use make commands, not manual Docker
- **Environment variables**: Use .env files, never commit secrets
- **Testing**: Run full test suite before committing
- **Documentation**: Update docs with every architectural change

---

**Next Steps After Onboarding:**
1. Set up development environment with `make dev-setup`
2. Run through all health checks
3. Study target-version/ architecture documents
4. Pick a small feature to implement following all patterns
5. Review code with team focusing on architecture compliance

See target-version/ for complete specifications.