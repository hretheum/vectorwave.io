# 🎯 EXEC SUMMARY - PLAN NAPRAWY STYLEGUIDE + PUBLICATION TYPES

## ❌ ROZBIEŻNOŚCI WYKRYTE
- **Agentic RAG**: Udokumentowane ale nie zaimplementowane
- **180 reguł**: Są w docs, używane hardcoded listy
- **ChromaDB StyleGuide**: Zero integracji z validation flow
- **Publication Types**: Brak content planning rules w systemie
- **CrewAI Flows**: Docs vs Linear Flow w kodzie

## 📦 ARCHITEKTURA DOCELOWA
- **Shared Editorial Service**: Container-first dla DUAL WORKFLOW support
- **Dual Workflow Support**: 
  - **Kolegium** (Full AI): Comprehensive validation (wszystkie reguły)
  - **AI Writing Flow** (Human-assisted): Selective validation (krytyczne reguły w checkpoints)
- **Wykorzystanie**: Istniejący ChromaDB + flexible validation modes
- **Zachowanie**: Linear Flow pattern (nie CrewAI Flows)
- **Eliminacja**: Wszystkich hardcoded rules INCLUDING cache fallbacks i mock data
- **Gwarancja**: Cache i mocks populated WYŁĄCZNIE z ChromaDB responses
- **Rozszerzenie**: Content planning + publication type guidance + dual workflow optimization

## 🚀 PLAN W 6 BLOKACH (11.5h total, 16 zadań atomowych)

### **BLOK 0**: Architecture Foundation - Dual Workflow (1.5h)
- **NOWY BLOK**: Editorial Service z dual workflow support
- Shared ChromaDB collections (2 consolidated zamiast 8)
- Validation mode selection: comprehensive vs selective
- Circuit breaker pattern dla resilience

### **BLOK 1**: Editorial Service Implementation (3h)
- Docker service z FastAPI + ChromaDB client
- Migracja 355+ reguł do ChromaDB (2 consolidated collections)
- Multi-purpose query API z validation mode support
- Circuit breaker implementation z fallback cache

### **BLOK 2**: Dual Workflow Integration (2.25h)
- HTTP client dla Editorial Service z validation mode
- **KRYTYCZNE**: Usunięcie wszystkich hardcoded rules
- AI Writing Flow: selective validation (checkpoint-based) - 45min
- Kolegium: comprehensive validation (all rules) - 30min
- Workflow-specific refactoring split into focused tasks

### **BLOK 3**: Shared ChromaDB Collections (1.5h)
- **Collection 1**: style_editorial_rules (280+ rules)
- **Collection 2**: publication_platform_rules (75+ rules)
- Repository pattern z Strategy dla validation modes
- Query optimization dla dual workflow access

### **BLOK 4**: Workflow-Specific Features (2h)  
- AI Writing Flow: checkpoint validation (3 precise checkpoints)
- Kolegium: comprehensive validation (full rule coverage)
- Error handling & fallbacks (45min z realistic testing)
- Circuit breaker resilience patterns

### **BLOK 5**: Testing & Security (1.75h)
- AI Writing Flow E2E test (45min)
- Kolegium E2E test (45min) 
- Security implementation (45min z realistic JWT + rate limiting)
- Executable tests z concrete verification steps
- Zero tolerance dla hardcoded rules

## 📊 METRYKI SUKCESU - ULTRA-PRECYZYJNE

### **Data Integrity Metrics**
- **355+ rules** loaded: `curl http://localhost:8040/cache/stats | jq '.total_rules' >= 355`
- **0 hardcoded rules**: `grep -r "hardcoded|fallback_rules|default_rules" src/ cache/ mocks/ | wc -l == 0`
- **100% ChromaDB sourcing**: `curl http://localhost:8040/cache/dump | jq '[.[] | select(.chromadb_metadata == null)] | length' == 0`

### **Performance Metrics**
- **P95 <200ms**: Verified by 10,000 query benchmark showing P95 latency
- **P99 <500ms**: Verified by 10,000 query benchmark showing P99 latency
- **Auth overhead <50ms**: `(time_with_auth - time_without_auth) < 50ms`
- **Cache warmup <10s**: Service ready with 355+ rules within 10s of startup

### **Validation Depth Metrics**
- **Selective**: `curl .../validate/selective | jq '.rules | length' ∈ [3,4]`
- **Comprehensive**: `curl .../validate/comprehensive | jq '.rules | length' ∈ [8,12]`
- **Same input test**: Both modes process identical content differently

### **Resilience Metrics**
- **Circuit breaker**: Service returns 200 (not 503) during ChromaDB outage
- **Recovery time <30s**: Auto-reconnects when ChromaDB available
- **Fallback performance <500ms**: Cached responses maintain sub-500ms latency

## 🎯 KOŃCOWY STAN
- **Shared Editorial Service** w kontenerze na port 8040
- **Dual Workflow Support**:
  - AI Writing Flow: selective validation (human checkpoints)
  - Kolegium: comprehensive validation (full AI pipeline)
- **Consolidated ChromaDB**: 2 collections zamiast 8
- **Validation Modes**: comprehensive vs selective
- **Circuit Breaker**: fallback dla high availability
- **Repository Pattern**: clean separation of concerns
- **Zero dependency** na hardcoded data w obu workflows
- **Zero hardcoded fallbacks** w cache, mocks, lub emergency responses
- **ChromaDB-sourced cache** z explicit origin metadata dla każdej rule

---

## 📋 SZCZEGÓŁOWE ZADANIA ATOMOWE

### **BLOK 0: Architecture Foundation - Dual Workflow Support**

#### **Zadanie 0.1**: Dual Workflow Architecture Design ⏱️ 45min
**Cel**: Repository pattern z Strategy dla validation modes
**Deliverable**: Abstract interfaces dla ValidationStrategy (comprehensive vs selective)

**Konkretne kryteria sukcesu**:
✅ **Clean separation** = Each strategy in separate file, zero cross-dependencies
✅ **Interface compliance** = All 3 methods implemented: validate(), supports_request(), get_expected_rule_count_range()
✅ **Factory pattern** = Factory method returns correct strategy type in <10ms

**Executable testy**:
```bash
# Test 1: Factory returns correct strategy types
python -c "from validation import ValidationStrategyFactory as F; assert type(F.create('comprehensive')).__name__ == 'ComprehensiveStrategy'"
python -c "from validation import ValidationStrategyFactory as F; assert type(F.create('selective')).__name__ == 'SelectiveStrategy'"

# Test 2: Interface implementation verification
python -c "from validation import IValidationStrategy; assert hasattr(IValidationStrategy, 'validate')"
python -c "from validation import IValidationStrategy; assert hasattr(IValidationStrategy, 'supports_request')"
python -c "from validation import IValidationStrategy; assert hasattr(IValidationStrategy, 'get_expected_rule_count_range')"

# Test 3: Rule count verification
python -c "
from validation import ValidationStrategyFactory
strategy = ValidationStrategyFactory.create('comprehensive')
rules = strategy.validate({'content': 'test article'})
assert 8 <= len(rules) <= 12, f'Expected 8-12 rules, got {len(rules)}'
"

# Test 4: Performance verification
time python -c "from validation import ValidationStrategyFactory; [ValidationStrategyFactory.create('selective') for _ in range(1000)]"
# Expected: real time <0.010s (10ms for 1000 creations = <10μs per creation)
```

**Walidacja ChromaDB origin**:
```bash
# Verify no hardcoded rules in strategies
grep -r "forbidden_phrases\|leveraging\|paradigm" validation/ | wc -l
# Expected output: 0
```

#### **Zadanie 0.2**: Consolidated ChromaDB Collections ⏱️ 45min
**Cel**: Migracja z 8 collections do 2 consolidated
**Deliverable**: 
- style_editorial_rules (280+ rules)
- publication_platform_rules (75+ rules)

**Konkretne kryteria sukcesu**:
✅ **280+ rules** in style_editorial_rules collection (count verified)
✅ **75+ rules** in publication_platform_rules collection (count verified)
✅ **Query performance** = P95 latency <200ms across 1000 queries
✅ **Zero data loss** = All 355 rules migrated successfully

**Executable testy**:
```bash
# Test 1: Verify collection sizes
curl -X GET http://localhost:8000/collections/style_editorial_rules/count | jq '.count'
# Expected output: >=280

curl -X GET http://localhost:8000/collections/publication_platform_rules/count | jq '.count'
# Expected output: >=75

# Test 2: Query performance benchmark
python -c "
import time, requests, statistics
times = []
for _ in range(1000):
    start = time.perf_counter()
    requests.post('http://localhost:8000/query', json={'collection': 'style_editorial_rules', 'text': 'test'})
    times.append((time.perf_counter() - start) * 1000)
p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
assert p95 < 200, f'P95 latency {p95:.1f}ms exceeds 200ms limit'
print(f'✅ P95 latency: {p95:.1f}ms')
"

# Test 3: Verify both workflows can access
curl -X POST http://localhost:8040/validate/selective -d '{"content":"test"}' | jq '.rules | length'
# Expected: 3-4

curl -X POST http://localhost:8040/validate/comprehensive -d '{"content":"test"}' | jq '.rules | length'  
# Expected: 8-12

# Test 4: Data integrity check
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
style_rules = client.get_collection('style_editorial_rules')
platform_rules = client.get_collection('publication_platform_rules')
total = style_rules.count() + platform_rules.count()
assert total >= 355, f'Expected 355+ rules, found {total}'
print(f'✅ Total rules: {total}')
"
```

### **BLOK 1: Editorial Service Implementation**

#### **Zadanie 1.1a**: Editorial Service Foundation ⏱️ 45min
**Cel**: Docker service foundation z FastAPI basic setup
**Deliverable**: editorial-service/ z health endpoint i ChromaDB client

**Konkretne kryteria sukcesu**:
✅ **Container starts** = docker-compose up completes in <30s
✅ **Health endpoint** = Returns 200 OK with service metadata
✅ **ChromaDB connection** = Successfully connects to ChromaDB at startup
✅ **Startup time** = Service ready in <5s after container start

**Executable testy**:
```bash
# Test 1: Container startup
time docker-compose up -d editorial-service
# Expected: Completes in <30s

# Test 2: Health endpoint
curl -w "\n%{http_code} %{time_total}s\n" http://localhost:8040/health
# Expected output:
# {"status":"healthy","service":"editorial-service","version":"1.0.0","chromadb":"connected"}
# 200 0.050s

# Test 3: ChromaDB connection verification
docker logs editorial-service 2>&1 | grep "ChromaDB connected"
# Expected: "ChromaDB connected to localhost:8000"

# Test 4: Service readiness probe
for i in {1..10}; do curl -s http://localhost:8040/health > /dev/null && echo "Ready in ${i}s" && break || sleep 1; done
# Expected: "Ready in 1s" or max "Ready in 5s"
```

#### **Zadanie 1.1b**: Validation Mode Endpoints ⏱️ 30min
**Cel**: Implementation of dual validation mode endpoints
**Deliverable**: POST endpoints for comprehensive and selective validation

**Konkretne kryteria sukcesu**:
✅ **Comprehensive endpoint** = Returns 8-12 rules for test content
✅ **Selective endpoint** = Returns 3-4 rules for same test content
✅ **Response time** = Both endpoints respond in <200ms
✅ **Error handling** = Returns 400 for invalid JSON, 422 for missing fields

**Executable testy**:
```bash
# Test 1: Comprehensive validation
curl -X POST http://localhost:8040/validate/comprehensive \
  -H "Content-Type: application/json" \
  -d '{"content":"Test article about AI technology"}' \
  -w "\nRules: %{size_download} bytes in %{time_total}s\n" | jq '.rules | length'
# Expected: 8-12 (rule count), time <0.200s

# Test 2: Selective validation  
curl -X POST http://localhost:8040/validate/selective \
  -H "Content-Type: application/json" \
  -d '{"content":"Test article about AI technology"}' \
  -w "\nRules: %{size_download} bytes in %{time_total}s\n" | jq '.rules | length'
# Expected: 3-4 (rule count), time <0.200s

# Test 3: Error handling - Invalid JSON
curl -X POST http://localhost:8040/validate/comprehensive \
  -H "Content-Type: application/json" \
  -d 'invalid json' \
  -w "\nHTTP Status: %{http_code}\n"
# Expected: HTTP Status: 400

# Test 4: Error handling - Missing field
curl -X POST http://localhost:8040/validate/selective \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\nHTTP Status: %{http_code}\n"
# Expected: HTTP Status: 422
```

#### **Zadanie 1.2**: Circuit Breaker Implementation ⏱️ 60min
**Cel**: Resilience pattern dla high availability z ChromaDB-only cache
**Deliverable**: Circuit breaker z fallback cache popolowany WYŁĄCZNIE z ChromaDB
**Metryka sukcesu**: Service remains functional during ChromaDB outages using ONLY previously cached ChromaDB rules
**Test**: 
- System startup: ChromaDB populations cache from 355+ rules
- `docker stop chromadb-container` 
- `curl http://localhost:8040/validate/comprehensive` returns 200 (from ChromaDB-populated cache)
- Assert: Cache contains ONLY previously fetched ChromaDB rules
- Assert: `grep -r "hardcoded|fallback_rules" cache/` returns empty
- `docker start chromadb-container`
- Verify service recovers within 30s
**Walidacja**: Zero hardcoded fallbacks, cache sourced exclusively from ChromaDB

#### **Zadanie 1.3**: Validation Mode API ⏱️ 45min
**Cel**: REST API z dual workflow support
**Deliverable**: 
- POST /validate/comprehensive (Kolegium)
- POST /validate/selective (AI Writing Flow)
- POST /query/rules z mode parameter
**Metryka sukcesu**: Different modes return appropriate rule sets
**Test**: 
- `curl -X POST localhost:8040/validate/selective -d '{"content":"test"}'` returns 3-4 rules
- `curl -X POST localhost:8040/validate/comprehensive -d '{"content":"test"}'` returns 8-12 rules
- Response time <200ms dla both endpoints
**Walidacja ChromaDB**: Same collections, different query patterns

### **BLOK 2: Dual Workflow Integration** 

#### **Zadanie 2.1**: Dual Workflow Client ⏱️ 60min
**Cel**: HTTP client z validation mode support
**Deliverable**: 
- ai_writing_flow: selective validation client
- kolegium: comprehensive validation client
**Metryka sukcesu**: Both clients use same Editorial Service with different modes
**Test**: 
- `python -m ai_writing_flow.client.test_selective_validation`
- Verify: HTTP POST to `/validate/selective` with test content
- Assert: Response contains exactly 3-4 rules
- `python -m kolegium.client.test_comprehensive_validation`  
- Verify: HTTP POST to `/validate/comprehensive` with same content
- Assert: Response contains 8-12 rules
**Walidacja ChromaDB**: Same collections, different access patterns

#### **Zadanie 2.2**: Hardcoded Rules Elimination ⏱️ 45min
**Cel**: **KRYTYCZNE** - eliminacja hardcoded rules w obu workflows
**Deliverable**: 
- AI Writing Flow: refactored styleguide_loader.py
- Kolegium: updated multi-agent rule loading
**Metryka sukcesu**: Zero hardcoded rules w obu systemach
**Test**: `grep -r "forbidden_phrases|leveraging|paradigm" src/` returns empty
**Walidacja ChromaDB**: Both workflows use vector search exclusively

#### **Zadanie 2.3a**: AI Writing Flow Refactor ⏱️ 45min
**Cel**: Checkpoint-based validation dla human-assisted workflow
**Deliverable**: AI Writing Flow z selective validation (3-4 rules per checkpoint)
**Metryka sukcesu**: 3 checkpoints: pre-writing, mid-writing, post-writing
**Test**: 
- Input: test_article.md
- `python -m ai_writing_flow validate --checkpoint=pre-writing`
- Assert: Returns exactly 3-4 rules (publication_type, audience_match, structure_basic)
- Verify: No hardcoded rules in validation path
**Walidacja ChromaDB**: Checkpoint queries use selective strategy

#### **Zadanie 2.3b**: Kolegium Validation Refactor ⏱️ 30min  
**Cel**: Comprehensive validation dla AI-only workflow
**Deliverable**: Kolegium z comprehensive multi-agent validation (8-12 rules)
**Metryka sukcesu**: Full rule coverage w CrewAI flow
**Test**:
- Same input: test_article.md
- `python -m kolegium validate --comprehensive`
- Assert: Returns 8-12 rules covering all aspects
- Verify: All rules fetched from ChromaDB
**Walidacja ChromaDB**: Comprehensive strategy queries all relevant rules

### **BLOK 3: Shared ChromaDB Collections**

#### **Zadanie 3.1**: Repository Pattern Implementation ⏱️ 45min
**Cel**: Clean data access layer dla dual workflows z ChromaDB-sourced mocks
**Deliverable**: 
- IRuleRepository interface
- ChromaDBRuleRepository implementation
- ValidationStrategy abstractions
- **KRYTYCZNE**: Mock implementations using ONLY ChromaDB rule subsets
**Metryka sukcesu**: Clean separation between business logic i data access, zero hardcoded mocks
**Test**: 
- Repository pattern allows testing with ChromaDB-sourced mocks
- Mock data MUST be subset of actual ChromaDB collections
- Assert: `grep -r "hardcoded|test_rules" mocks/` returns empty
- Assert: All mock rules have ChromaDB collection origin metadata
**Walidacja**: Strategy pattern enables workflow-specific validation, mocks reflect real ChromaDB data

#### **Zadanie 3.2**: Query Optimization z ChromaDB-Only Cache ⏱️ 45min
**Cel**: Performance optimization dla dual access patterns z explicit cache strategy
**Deliverable**: 
- Indexed embeddings dla fast retrieval
- Query batching dla multi-rule validation
- **KRYTYCZNE**: Caching layer populated EXCLUSIVELY from ChromaDB responses
- Cache warmup strategy using real ChromaDB rules
- Zero hardcoded cache seeds

**Konkretne kryteria sukcesu**:
✅ **Query performance** = P95 <200ms, P99 <500ms across 10,000 queries
✅ **Cache source verification** = 100% rules have ChromaDB origin metadata
✅ **Cache warmup** = Populates 355+ rules from ChromaDB in <10s at startup
✅ **Zero hardcoded seeds** = grep returns 0 matches for hardcoded patterns

**Executable testy**:
```bash
# Test 1: Cache warmup from ChromaDB
docker-compose restart editorial-service
sleep 10
curl http://localhost:8040/cache/stats | jq '.'
# Expected output:
# {
#   "total_rules": 355,
#   "source": "chromadb",
#   "warmup_time_ms": 8500,
#   "all_have_origin": true
# }

# Test 2: Verify ChromaDB origin metadata
curl http://localhost:8040/cache/dump | jq '.[0]'
# Expected output (example):
# {
#   "rule_id": "style_001",
#   "content": "Avoid jargon...",
#   "chromadb_metadata": {
#     "collection": "style_editorial_rules",
#     "query_timestamp": "2024-01-15T10:30:00Z",
#     "similarity_score": 0.95,
#     "embedding_id": "emb_abc123"
#   }
# }

# Test 3: Zero hardcoded cache seeds
docker exec editorial-service sh -c "grep -r 'cache_seed\|default_rules\|fallback_rules\|hardcoded' /app/cache/" | wc -l
# Expected output: 0

# Test 4: Performance benchmark with cache
python -c "
import time, requests, statistics
# Warmup cache
for _ in range(100):
    requests.post('http://localhost:8040/validate/comprehensive', json={'content': 'test'})

# Measure performance
times = []
for _ in range(10000):
    start = time.perf_counter()
    requests.post('http://localhost:8040/validate/selective', json={'content': 'test article'})
    times.append((time.perf_counter() - start) * 1000)

p95 = statistics.quantiles(times, n=100)[94]
p99 = statistics.quantiles(times, n=100)[98]
assert p95 < 200, f'P95 {p95:.1f}ms exceeds 200ms'
assert p99 < 500, f'P99 {p99:.1f}ms exceeds 500ms'
print(f'✅ P95: {p95:.1f}ms, P99: {p99:.1f}ms')
"

# Test 5: Verify cache entries have timestamps
curl http://localhost:8040/cache/dump | jq '[.[] | select(.chromadb_metadata.query_timestamp == null)] | length'
# Expected output: 0
```

### **BLOK 4: Workflow-Specific Features**

#### **Zadanie 4.1**: AI Writing Flow Checkpoints ⏱️ 45min
**Cel**: Checkpoint-based validation dla human-assisted workflow
**Deliverable**: 
- Pre-writing: publication type validation
- Mid-writing: style consistency check
- Post-writing: final humanization review
**Metryka sukcesu**: 3 checkpoint validations z targeted rules
**Test**: 
- `curl -X POST /validate/selective -d '{"checkpoint":"pre-writing","content":"test"}'`
- Assert: Response contains exactly ["publication_type_match", "audience_targeting", "structure_basic"]
- `curl -X POST /validate/selective -d '{"checkpoint":"mid-writing","content":"test"}'`  
- Assert: Response contains exactly ["style_consistency", "tone_match", "flow_quality"]
- `curl -X POST /validate/selective -d '{"checkpoint":"post-writing","content":"test"}'`
- Assert: Response contains exactly ["humanization_check", "ai_detection_avoid", "final_polish"]
**Walidacja**: Selective validation maintains quality przy reduced overhead

#### **Zadanie 4.2**: Kolegium Comprehensive Validation ⏱️ 30min
**Cel**: Full rule coverage dla AI-only workflow
**Deliverable**: 
- Multi-agent rule selection
- Comprehensive style validation
- Platform optimization
- Publication structure compliance
**Metryka sukcesu**: 8-12 rules per validation, full coverage
**Test**: Kolegium validates all aspects: style, structure, platform, audience
**Walidacja**: Comprehensive validation catches all potential issues

#### **Zadanie 4.3**: Error Handling & ChromaDB-Only Fallbacks ⏱️ 45min
**Cel**: Resilience patterns dla production readiness z ChromaDB-sourced fallbacks
**Deliverable**: 
- Circuit breaker implementation
- **KRYTYCZNE**: Cached rule fallbacks sourced EXCLUSIVELY from ChromaDB
- Graceful degradation strategies without hardcoded rules
- Cache invalidation strategy ensuring freshness

**Konkretne kryteria sukcesu**:
✅ **Service availability** = Returns 200 (not 503) during ChromaDB outage
✅ **Fallback response time** = <500ms when using cached data
✅ **Recovery time** = Reconnects to ChromaDB within 30s of availability
✅ **Cache purity** = 0 hardcoded rules in fallback responses

**Executable testy**:
```bash
# Test 1: Populate cache from ChromaDB
docker-compose restart editorial-service
sleep 10
curl http://localhost:8040/cache/stats | jq '.total_rules'
# Expected output: 355 (or more)

# Test 2: Simulate ChromaDB outage
docker stop chromadb-container

# Test 3: Service remains available with cache
response=$(curl -s -w "\n%{http_code}" http://localhost:8040/validate/selective -d '{"content":"test"}')
echo "$response" | tail -1
# Expected output: 200 (not 503)

# Test 4: Verify cached response metadata
curl -s http://localhost:8040/validate/comprehensive -d '{"content":"test"}' | jq '.cache_metadata'
# Expected output:
# {
#   "source": "cache",
#   "cached_at": "2024-01-15T10:30:00Z",
#   "chromadb_origin": "style_editorial_rules",
#   "fallback_mode": true
# }

# Test 5: Response time during outage
time curl -s http://localhost:8040/validate/selective -d '{"content":"test"}' > /dev/null
# Expected: real time <0.500s

# Test 6: Verify no hardcoded rules in response
curl -s http://localhost:8040/validate/comprehensive -d '{"content":"test"}' | \
  jq '.rules[] | select(.chromadb_metadata == null)' | wc -l
# Expected output: 0

# Test 7: Restart ChromaDB
docker start chromadb-container

# Test 8: Verify automatic recovery
for i in {1..30}; do
  status=$(curl -s http://localhost:8040/health | jq -r '.chromadb_status')
  if [ "$status" = "connected" ]; then
    echo "✅ Recovered in ${i}s"
    break
  fi
  sleep 1
done
# Expected: "✅ Recovered in X" where X <= 30

# Test 9: Verify back to live ChromaDB queries
curl -s http://localhost:8040/validate/selective -d '{"content":"test"}' | jq '.cache_metadata.source'
# Expected output: "chromadb" (not "cache")
```

### **BLOK 5: Testing & Security**

#### **Zadanie 5.1a**: AI Writing Flow E2E Test ⏱️ 45min
**Cel**: End-to-end testing AI Writing Flow z human checkpoints
**Deliverable**: Complete AI Writing Flow workflow test
**Metryka sukcesu**: Full workflow passes with ChromaDB-only rules
**Test**: 
- `docker-compose up editorial-service`
- `python tests/e2e/test_ai_writing_flow.py`
- Assert: All 3 checkpoints pass with ChromaDB-only rules
- Assert: No hardcoded rules used (grep verification)
- Assert: Total execution time <5s
**Walidacja**: Zero fallback to hardcoded rules

#### **Zadanie 5.1b**: Kolegium E2E Test ⏱️ 45min
**Cel**: End-to-end testing Kolegium comprehensive workflow
**Deliverable**: Complete Kolegium validation pipeline test
**Metryka sukcesu**: Full validation pipeline completes successfully
**Test**: 
- `python tests/e2e/test_kolegium_comprehensive.py`
- Assert: Full validation pipeline completes
- Assert: 8-12 rules applied from ChromaDB
- Assert: No fallback to hardcoded rules
- Assert: All CrewAI agents use Editorial Service
**Walidacja**: Comprehensive validation covers all rule categories

#### **Zadanie 5.2**: Security Implementation ⏱️ 45min
**Cel**: Production-ready security measures
**Deliverable**: 
- API authentication (JWT tokens)
- Rate limiting dla endpoints
- Input validation i sanitization

**Konkretne kryteria sukcesu**:
✅ **JWT authentication** = Valid token required for all validation endpoints
✅ **Rate limiting** = 100 req/min per IP, returns 429 when exceeded
✅ **Performance overhead** = Authentication adds <50ms to response time
✅ **Input sanitization** = Prevents XSS/SQL injection attempts

**Executable testy**:
```bash
# Test 1: No auth returns 401
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8040/validate/comprehensive \
  -d '{"content":"test"}'
# Expected output: HTTP Status: 401

# Test 2: Invalid token returns 401
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer invalid_token_12345" \
  http://localhost:8040/validate/comprehensive \
  -d '{"content":"test"}'
# Expected output: HTTP Status: 401

# Test 3: Valid token returns 200
export JWT=$(python -c "
import jwt, datetime
secret = 'test_secret_key'
payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1), 'sub': 'test_user'}
token = jwt.encode(payload, secret, algorithm='HS256')
print(token)
")
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer $JWT" \
  http://localhost:8040/validate/selective \
  -d '{"content":"test"}'
# Expected output: HTTP Status: 200

# Test 4: Rate limiting enforcement
for i in {1..105}; do
  curl -s -H "Authorization: Bearer $JWT" \
    http://localhost:8040/validate/selective \
    -d '{"content":"test"}' \
    -w "%{http_code}\n" -o /dev/null
done | tail -5
# Expected output (last 5 responses):
# 200
# 200
# 429
# 429
# 429

# Test 5: Performance overhead measurement
# Without auth (baseline)
time curl -s http://localhost:8040/health > /dev/null
# Expected: real <0.050s

# With auth
time curl -s -H "Authorization: Bearer $JWT" \
  http://localhost:8040/validate/selective \
  -d '{"content":"test"}' > /dev/null
# Expected: real <0.250s (baseline + <50ms overhead)

# Test 6: Input sanitization - XSS attempt
curl -s -H "Authorization: Bearer $JWT" \
  http://localhost:8040/validate/selective \
  -d '{"content":"<script>alert(\"XSS\")</script>"}' | jq '.content'
# Expected output: "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;" (escaped)

# Test 7: Input validation - SQL injection attempt  
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer $JWT" \
  http://localhost:8040/validate/selective \
  -d '{"content":"test\" OR \"1\"=\"1"}' 
# Expected: HTTP Status: 200 (handled safely, no SQL execution)
```


## 🎯 DEPLOYMENT STRATEGY

### **Dual Workflow Architecture**:
- **Shared Editorial Service**: port 8040 (resolved conflict with Beehiiv Adapter)
- **AI Writing Flow**: selective validation client
- **Kolegium**: comprehensive validation client  
- **Health checks**: `/health` endpoint z dual workflow status
- **Consolidated ChromaDB**: 2 collections zamiast 8
- **Circuit breaker**: graceful fallback z cached rules
- **Port Allocation**: See `/Users/hretheum/dev/bezrobocie/vector-wave/PORT_ALLOCATION.md`

### **Success Metrics Summary**:
- **Rules Migration**: 355+ rules in ChromaDB w 2 consolidated collections (0 hardcoded)
- **Zero Hardcoded Fallbacks**: Cache, mocks, emergency responses sourced exclusively from ChromaDB
- **Cache Transparency**: All cached rules have ChromaDB origin metadata i timestamps
- **Dual Workflows**: AI Writing Flow (selective) + Kolegium (comprehensive) supported
- **Performance**: <200ms per query dla both validation modes
- **Validation Depth**: 3-4 rules (selective) vs 8-12 rules (comprehensive)
- **Circuit Breaker**: High availability z ChromaDB-sourced fallback
- **Repository Pattern**: Clean separation między workflows
- **Security**: JWT authentication + rate limiting
- **Container-First**: Shared service architecture

### **Consolidated ChromaDB Collections**:
1. **style_editorial_rules** (280+ rules) - Style, tone, publication structure, quality gates
2. **publication_platform_rules** (75+ rules) - Platform formatting, audience targeting, optimization

### **Dual Workflow Validation Patterns**:
- **AI Writing Flow (Selective)**: 3 checkpoints x 3-4 rules = 9-12 total queries
- **Kolegium (Comprehensive)**: Full pipeline x 8-12 rules = 40-60 total queries
- **Same ChromaDB collections**, different access patterns
- **Repository pattern** enables clean separation of validation logic

### **🚫 ZERO HARDCODED RULES GUARANTEE**:

#### **Cache Strategy - ChromaDB-Only**:
- **Warmup**: Cache populated during startup z ChromaDB queries
- **Source**: ALL cached rules MUST have ChromaDB origin metadata
- **Fallback**: Circuit breaker uses ONLY previously cached ChromaDB responses
- **Verification**: `grep -r "hardcoded|emergency_rules|fallback_data" cache/` MUST return empty
- **Timestamps**: Every cache entry includes ChromaDB query timestamp

#### **Mock Data Strategy - ChromaDB Subset**:
- **Source**: Test mocks use subset of actual ChromaDB collections
- **Generation**: Mocks generated from real ChromaDB queries
- **Verification**: `grep -r "test_rules|hardcoded" mocks/` MUST return empty
- **Metadata**: All mock rules include original ChromaDB collection reference

#### **Emergency Procedures - No Hardcoded Fallbacks**:
- **Outage**: Service fails gracefully when cache empty AND ChromaDB down
- **No Emergency Rules**: Zero hardcoded "emergency rule sets"
- **Degradation**: Service returns 503 Service Unavailable rather than fallback to hardcoded
- **Recovery**: Automatic ChromaDB reconnection repopulates cache from source