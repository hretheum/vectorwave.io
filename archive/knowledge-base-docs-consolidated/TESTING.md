# Knowledge Base Testing Documentation

## 🎯 Overview

This document describes the comprehensive testing strategy for the Knowledge Base implementation, providing >80% code coverage through unit, integration, performance, and edge case tests.

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── __init__.py
├── unit/                    # Unit tests for individual components
│   ├── test_memory_cache.py         # L1 cache tests (49 tests)
│   ├── test_redis_cache.py          # L2 cache tests (23 tests)  
│   ├── test_cache_manager.py        # Cache orchestration tests (37 tests)
│   ├── test_chroma_client.py        # Vector store tests (42 tests)
│   └── test_knowledge_engine.py     # Main engine tests (38 tests)
├── integration/             # Integration tests across components
│   ├── test_end_to_end.py           # End-to-end flow tests (18 tests)
│   └── test_api.py                  # FastAPI endpoint tests (35 tests)
├── edge_cases/              # Edge cases and error conditions
│   └── test_edge_cases.py           # Boundary condition tests (25 tests)
├── performance/             # Performance and benchmark tests
│   └── test_performance.py          # Performance benchmarks (15 tests)
└── requirements/
    └── test_requirements.txt        # Test dependencies
```

**Total: 282+ test cases across 9 test files**

## 🧪 Test Categories

### Unit Tests (189 tests)
- **Memory Cache**: TTL, eviction, concurrency, performance
- **Redis Cache**: Serialization, networking, error handling  
- **Cache Manager**: Multi-layer coordination, invalidation
- **Chroma Client**: Vector operations, search, document management
- **Knowledge Engine**: Query processing, fallback strategy, statistics

### Integration Tests (53 tests)
- **End-to-End Flows**: Cache → Vector → Web fallback
- **API Endpoints**: FastAPI routes, validation, error handling
- **Component Coordination**: Cross-service integration
- **Concurrent Operations**: Multi-user scenarios

### Performance Tests (15 tests)
- **Query Latency**: <200ms average, <500ms P95
- **Cache Hit Ratio**: >70% target
- **Concurrent Load**: 100+ concurrent users
- **Memory Usage**: Efficient resource utilization
- **Sustained Load**: Long-running stability

### Edge Case Tests (25 tests)
- **Error Conditions**: Network failures, timeouts, corrupted data
- **Boundary Values**: Empty queries, large payloads, extreme parameters
- **Unicode/Special Characters**: International text, emojis
- **Resource Exhaustion**: Memory pressure, disk space
- **Race Conditions**: Concurrent access patterns

## 🔧 Test Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=src
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
    --durations=10
markers =
    unit: Unit tests for individual components
    integration: Integration tests across components
    performance: Performance and benchmark tests
    edge_case: Edge case and error condition tests
    slow: Tests that take longer than 5 seconds
```

### Test Fixtures

**Global Fixtures (conftest.py):**
- `sample_document`: ChromaDocument for testing
- `sample_documents`: List of test documents
- `sample_query_params`: QueryParams for testing
- `cache_config`: Test cache configuration
- `mock_chroma_client`: Mocked vector store
- `performance_tracker`: Performance metrics collector
- `error_simulator`: Error condition simulator

## 🚀 Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r test_requirements.txt

# Install main dependencies  
pip install -r requirements.txt
```

### Quick Test Commands

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test suites
python run_tests.py --unit-only
python run_tests.py --integration-only
python run_tests.py --performance-only
python run_tests.py --api-only

# Run with options
python run_tests.py --parallel        # Parallel execution
python run_tests.py --include-slow    # Include long-running tests
python run_tests.py --no-performance  # Skip performance tests
python run_tests.py --no-quality      # Skip code quality checks
```

### Manual pytest Commands

```bash
# Unit tests with coverage
pytest tests/unit/ -v --cov=src --cov-report=html

# Integration tests
pytest tests/integration/ -v -m integration

# Performance tests
pytest tests/performance/ -v -m performance --benchmark-only

# Edge case tests
pytest tests/edge_cases/ -v -m edge_case

# Parallel execution (faster)
pytest tests/unit/ -n auto

# Specific test file
pytest tests/unit/test_memory_cache.py -v

# Specific test method
pytest tests/unit/test_memory_cache.py::TestMemoryCache::test_set_and_get_basic -v
```

## 📊 Coverage Targets

| Component | Target Coverage | Test Focus |
|-----------|----------------|------------|
| Memory Cache | 95%+ | TTL, eviction, concurrency |
| Redis Cache | 90%+ | Serialization, networking |
| Cache Manager | 95%+ | Multi-layer coordination |
| Chroma Client | 85%+ | Vector operations, search |
| Knowledge Engine | 90%+ | Query processing, fallback |
| API Routes | 85%+ | Endpoint validation, errors |
| **Overall** | **>80%** | **All code paths** |

## 🎯 Performance Benchmarks

### Query Performance
- **Average latency**: <200ms
- **P95 latency**: <500ms  
- **P99 latency**: <1000ms
- **Cache hit ratio**: >70%

### Concurrent Performance  
- **10 concurrent users**: <100ms average
- **50 concurrent users**: <200ms average
- **100 concurrent users**: <500ms average

### Memory Cache Performance
- **Set operations**: <100μs average
- **Get operations**: <50μs average  
- **Delete operations**: <100μs average

### Vector Store Performance
- **Document addition**: >20 docs/second
- **Search operations**: <100ms average
- **Result processing**: >1000 results/second

## 🔍 Test Quality Metrics

### Code Quality Checks
- **Black**: Code formatting compliance
- **Flake8**: Linting and style compliance
- **MyPy**: Type annotation validation
- **isort**: Import organization

### Test Patterns
- **AAA Pattern**: Arrange, Act, Assert
- **Descriptive Names**: Clear test intentions
- **Isolated Tests**: No dependencies between tests
- **Mocked Dependencies**: External service isolation
- **Comprehensive Fixtures**: Reusable test data

## 🐛 Debugging Tests

### Verbose Output
```bash
# Detailed test output
pytest -v --tb=long

# Show print statements  
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest --tb=auto --showlocals
```

### Performance Debugging
```bash
# Profile memory usage
pytest --profile

# Show slowest tests
pytest --durations=10

# Benchmark comparison
pytest --benchmark-compare
```

## 📈 Continuous Integration

### GitHub Actions Integration
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test_requirements.txt
      - name: Run tests
        run: python run_tests.py
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 🔧 Test Maintenance

### Adding New Tests
1. **Create test file**: Follow naming convention `test_*.py`
2. **Add markers**: Use appropriate pytest markers
3. **Include fixtures**: Use shared fixtures from conftest.py
4. **Document purpose**: Clear test descriptions
5. **Update coverage**: Maintain >80% coverage

### Updating Existing Tests
1. **Run related tests**: Ensure changes don't break existing functionality
2. **Update fixtures**: Modify shared test data if needed
3. **Check performance**: Verify performance benchmarks still pass
4. **Review coverage**: Ensure coverage remains high

## 📋 Test Checklist

### Before Deployment
- [ ] All unit tests pass (189/189)
- [ ] All integration tests pass (53/53) 
- [ ] Performance benchmarks met
- [ ] Code coverage >80%
- [ ] No flaky tests
- [ ] Error scenarios covered
- [ ] API endpoints validated
- [ ] Edge cases tested

### Test Quality Review
- [ ] Tests are isolated and independent
- [ ] Mocks are properly configured
- [ ] Fixtures are reusable and clear
- [ ] Error messages are descriptive
- [ ] Performance tests have realistic targets
- [ ] Documentation is up-to-date

## 🚨 Common Issues

### Import Errors
```bash
# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Install missing dependencies
pip install -r test_requirements.txt
```

### Async Test Issues
```bash
# Ensure asyncio mode is set
pytest --asyncio-mode=auto

# Or use explicit event loop
pytest -v tests/unit/test_memory_cache.py
```

### Performance Test Failures
- Check system resources (CPU, memory)
- Adjust performance targets for CI environment
- Use `--benchmark-skip` to skip during development

---

## 💡 Best Practices

1. **Write tests first** (TDD approach)
2. **Keep tests simple** and focused
3. **Use descriptive names** for tests and fixtures
4. **Mock external dependencies** consistently
5. **Test both happy path and error conditions**
6. **Maintain high coverage** without sacrificing quality
7. **Run tests frequently** during development
8. **Review test failures** immediately
9. **Keep tests fast** (unit tests <1s each)
10. **Document complex test scenarios**

This comprehensive testing strategy ensures the Knowledge Base implementation is robust, performant, and maintainable with >80% code coverage across all components.