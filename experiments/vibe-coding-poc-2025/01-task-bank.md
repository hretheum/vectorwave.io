# 📋 POC Vibe Coding - Task Bank
## Vector Wave / Cookbook AI Context

---

## TASK A: Onboarding Module 
**"Add Recipe Rating System to Cookbook AI"**

### Context
The Cookbook AI system currently generates recipes but lacks user feedback mechanism. We need to add a rating system that allows users to rate recipes and stores ratings for future recommendations.

### Your Task
Extend the existing system with:
1. Rating endpoint in recipe-service (POST /recipes/{id}/rating)
2. Database schema for storing ratings (PostgreSQL)
3. Aggregation logic for average ratings
4. Integration with the API gateway
5. Error handling for invalid ratings (422 responses)

### Acceptance Criteria
- [ ] Rating values 1-5 with half-star precision
- [ ] User can update their existing rating
- [ ] Anonymous ratings supported with session tracking
- [ ] Average rating calculation with minimum 3 ratings threshold
- [ ] Comprehensive test suite (>90% coverage)
- [ ] Architecture Decision Record (ADR) documenting approach

### Provided Resources
- Docker Compose setup with all services
- Existing recipe-service codebase
- Database connection configured
- OpenTelemetry tracing enabled

### Time Budget: 90 minutes

---

## TASK B: Code Refactoring
**"Extract Agent Coordination from Monolithic Service"**

### Context  
The agent-service currently combines CrewAI agent initialization, coordination logic, and tool execution in a single 800-line module. This creates maintenance bottlenecks and makes testing difficult.

### Your Task
Refactor the code to:
1. Extract agent coordination into separate module
2. Create clean interfaces between components
3. Implement dependency injection for tools
4. Add contract tests at module boundaries
5. Maintain existing functionality

### Current Code Structure
```
agent_service.py (800 lines)
├── Agent initialization (lines 1-200)
├── Tool definitions (lines 201-400)  
├── Coordination logic (lines 401-600)
└── API endpoints (lines 601-800)
```

### Acceptance Criteria
- [ ] Clear separation of concerns (3+ modules)
- [ ] No regression in functionality
- [ ] Contract tests for interfaces
- [ ] Test coverage ≥90% on new modules
- [ ] Cyclomatic complexity < 10 per function
- [ ] Clean, atomic git commits
- [ ] ADR explaining refactoring decisions

### Time Budget: 90 minutes

---

## TASK C: Technical Spike
**"Evaluate Caching Strategies for Recipe Search"**

### Context
Recipe search currently hits the vector database (Qdrant) for every query, causing 200-300ms latency. We need to evaluate caching strategies to reduce this to <50ms for common queries.

### Your Task
Research and prototype:
1. Identify top 20% most common queries (Pareto principle)
2. Implement Redis caching with TTL strategy
3. Compare LRU vs LFU eviction policies
4. Benchmark performance improvements
5. Document memory usage implications

### Acceptance Criteria
- [ ] Working proof of concept with Redis
- [ ] Benchmark data showing latency improvements
- [ ] Memory usage analysis for 10K cached queries
- [ ] Cache invalidation strategy documented
- [ ] ADR with recommendations and trade-offs
- [ ] Demo-able implementation

### Performance Targets
- P50 latency: <50ms (from 200ms)
- P99 latency: <150ms (from 500ms)
- Cache hit rate: >60% for common queries

### Time Budget: 90 minutes