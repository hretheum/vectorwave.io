# QA Test Instructions for Knowledge Base

You are acting as a QA Test Engineer with expertise in:
- pytest, pytest-cov, pytest-asyncio, pytest-mock, pytest-benchmark
- Unit testing, integration testing, e2e testing, performance testing
- Code coverage analysis, test planning, bug reporting

## Your Task

Test the Knowledge Base implementation comprehensively.

## Test Scope

### 1. Unit Tests (Target: >80% coverage)
- Cache layer (L1 in-memory, L2 Redis)
- Vector store operations (Chroma)
- Query engine logic
- Update mechanism
- API endpoints

### 2. Integration Tests
- End-to-end query flow
- Cache → Vector → Markdown → Web fallback
- Concurrent query handling
- Update while querying

### 3. Performance Tests
- Query latency benchmarks (<200ms average)
- Cache hit ratio (>70%)
- Memory usage under load (<500MB)
- Concurrent user simulation (100 users)

### 4. Edge Cases
- Empty results handling
- Network failures
- Cache overflow
- Invalid queries
- Rate limiting

## Deliverables

1. **Test Suite** in `/knowledge-base/tests/`
   - `test_unit_*.py` - Unit tests
   - `test_integration_*.py` - Integration tests
   - `test_performance_*.py` - Performance tests
   - `conftest.py` - Shared fixtures
   - `pytest.ini` - Test configuration

2. **Coverage Report**
   - HTML report in `htmlcov/`
   - Terminal output summary
   - Coverage badge

3. **Performance Report**
   - Latency benchmarks
   - Throughput metrics
   - Resource usage stats

4. **Bug Report** (if any found)
   - Severity classification
   - Reproduction steps
   - Suggested fixes

5. **Test Execution Plan**
   - How to run tests
   - CI/CD integration
   - Maintenance guidelines

## Test Implementation Guidelines

### Unit Test Example
```python
@pytest.mark.asyncio
async def test_cache_hit(knowledge_base):
    # Arrange
    query = "CrewAI installation"
    expected = {"result": "pip install crewai"}
    
    # Act - First query (cache miss)
    result1 = await knowledge_base.query(query)
    # Act - Second query (cache hit)
    result2 = await knowledge_base.query(query)
    
    # Assert
    assert result1 == result2
    assert knowledge_base.cache.hit_ratio > 0
```

### Performance Test Example
```python
@pytest.mark.benchmark
def test_query_latency(benchmark, knowledge_base):
    result = benchmark(knowledge_base.query, "CrewAI flows")
    assert benchmark.stats["mean"] < 0.2  # 200ms
```

## Success Criteria
- ✅ Code coverage >80%
- ✅ All tests passing
- ✅ Query latency <200ms (avg)
- ✅ No critical bugs
- ✅ Clear test documentation

Start by examining the codebase structure, then implement comprehensive tests!