# CrewAI Flow Architecture - Dekompozycja Atomowych Zadań

## 🎯 Przegląd Projektu

**Cel**: Implementacja stabilnej architektury CrewAI Flow eliminującej infinite loops i zapewniającej pełną kontrolę nad wykonaniem.

**Success Criteria**: 
- Zero infinite loops
- CPU usage <30%
- Memory usage <500MB
- Execution time <5 minut
- >95% completion rate

**Timeline**: 3 tygodnie

**Risk Level**: Medium → Low (po implementacji)

## 🚨 KRYTYCZNA INSTRUKCJA: Code Review Co 150 Wierszy

### ⚠️ OBOWIĄZKOWY PROCES CODE REVIEW

**KAŻDY AGENT IMPLEMENTUJĄCY KOD MUSI**:
1. **Zatrzymać się po napisaniu 150 wierszy kodu**
2. **Uruchomić agenta code-reviewer**: `/agent code-reviewer`
3. **Wprowadzić sugerowane poprawki PRZED kontynuacją**
4. **Dopiero potem przejść do następnych 150 wierszy**

### 📏 Metryki Code Review

- **Maksimum**: 150 wierszy kodu przed review
- **Wyjątek**: Tylko pliki konfiguracyjne mogą przekroczyć limit
- **Enforcement**: Automatyczne zatrzymanie flow po 150 liniach

### 🔄 Proces Review w Atomic Tasks

Dla każdego atomic task z implementacją kodu:
```
1. Implementuj do 150 linii → STOP
2. /agent code-reviewer → Review
3. Wprowadź poprawki → Commit
4. Kontynuuj następne 150 linii
```

### ❌ Konsekwencje Pominięcia Review

- **Odrzucenie PR**: Kod bez review nie przejdzie do main
- **Rollback**: Automatyczny rollback zmian bez review
- **Alert**: Notyfikacja do team lead o naruszeniu procesu

### ✅ Przykład Prawidłowego Flow

```bash
# Agent implementuje FlowControlState (200 linii)
/nakurwiaj 1  # Pierwsze 150 linii
# AUTOMATYCZNE ZATRZYMANIE PO 150 LINIACH
/agent code-reviewer  # Review pierwszej części
# Wprowadzenie poprawek
git commit -m "feat: FlowControlState part 1 (reviewed)"
# Kontynuacja pozostałych 50 linii
/agent code-reviewer  # Review drugiej części
git commit -m "feat: FlowControlState part 2 (reviewed)"
```

## 🏗️ Architektura Overview

Obecna implementacja zawiera krytyczne błędy:
- Circular dependencies w @router
- Brak proper state management
- CPU 97.9% z powodu infinite loops

Nowa architektura:
```
Linear Flow: START → VALIDATE → RESEARCH → AUDIENCE → DRAFT → HUMAN_REVIEW → STYLE → QUALITY → FINALIZE → END
Guards: Circuit Breaker + Stage Manager + Retry Manager + Loop Prevention
```

---

## 📈 Fazy Implementacji

### Phase 1: Core Architecture (Week 1)

#### Task 1.1: Implement FlowControlState and stage management (4h)

##### Blok 0: Analiza i przygotowanie (1h)
**Agent Chain**: architecture-advisor → project-architect

- [ ] **Atomic Task 0.1**: Analiza obecnego stanu FlowControlState
  - **Agent**: architecture-advisor
  - **Time**: 20min
  - **Deliverable**: Dokument analizy obecnego kodu
  - **Success**: Wszystkie problemy zidentyfikowane
  - **Validation**: `find . -name "*.py" | xargs grep -l "FlowControlState"`

- [ ] **Atomic Task 0.2**: Design nowej architektury state management
  - **Agent**: project-architect → architecture-advisor
  - **Time**: 25min
  - **Deliverable**: Diagram architektury state management
  - **Success**: UML diagram z lifecycle stages
  - **Validation**: Architecture review approved

- [ ] **Atomic Task 0.3**: Przygotowanie struktury plików
  - **Agent**: project-coder
  - **Time**: 15min
  - **Deliverable**: Struktura folderów i base files
  - **Success**: Wszystkie pliki utworzone zgodnie ze strukturą
  - **Validation**: `ls -la src/ai_writing_flow/models/` sprawdzi strukturę

##### Blok 1: FlowStage i podstawowe modele (1.5h)
**Agent Chain**: project-coder → code-reviewer
**⚠️ CODE REVIEW**: Obowiązkowy po każdych 150 liniach kodu!

- [ ] **Atomic Task 1.1**: Implement FlowStage enum
  - **Agent**: project-coder
  - **Time**: 30min
  - **Deliverable**: `/src/ai_writing_flow/models/flow_stage.py`
  - **Success**: Wszystkie stany flow zdefiniowane, proper typing
  - **Validation**: `python -c "from models.flow_stage import FlowStage; print(list(FlowStage))"`
  - **Code Review**: Mandatory before proceeding to 1.2

- [ ] **Atomic Task 1.2**: Create FlowControlState model
  - **Agent**: project-coder → code-reviewer
  - **Time**: 45min
  - **Deliverable**: `/src/ai_writing_flow/models/flow_control_state.py`
  - **Success**: Pydantic model z retry tracking i history
  - **Validation**: `pytest tests/test_flow_control_state.py::test_serialization -v`

- [ ] **Atomic Task 1.3**: Add state transition validation
  - **Agent**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: State transition matrix i validation logic
  - **Success**: Invalid transitions raise exceptions
  - **Validation**: `pytest tests/test_flow_control_state.py::test_transitions -v`

##### Blok 2: StageManager implementation (1h)
**Agent Chain**: project-coder → code-reviewer → architecture-advisor

- [ ] **Atomic Task 2.1**: Create StageManager class
  - **Agent**: project-coder → architecture-advisor
  - **Time**: 30min
  - **Deliverable**: `/src/ai_writing_flow/managers/stage_manager.py`
  - **Success**: Stage completion tracking working
  - **Validation**: `pytest tests/test_stage_manager.py::test_completion_tracking -v`

- [ ] **Atomic Task 2.2**: Add stage result storage
  - **Agent**: project-coder → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Result caching per stage
  - **Success**: Results properly typed i accessible
  - **Validation**: `pytest tests/test_stage_manager.py::test_result_storage -v`

- [ ] **Atomic Task 2.3**: Implement stage reset functionality
  - **Agent**: project-coder → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Reset mechanism for retries
  - **Success**: Reset clears completion i results
  - **Validation**: `pytest tests/test_stage_manager.py::test_reset -v`

##### Blok 3: Testing i validation (30min)
**Agent Chain**: qa-test-engineer → code-reviewer

- [ ] **Atomic Task 3.1**: Create comprehensive tests
  - **Agent**: qa-test-engineer
  - **Time**: 20min
  - **Deliverable**: Complete test suite dla FlowControlState
  - **Success**: >95% coverage, all edge cases
  - **Validation**: `pytest --cov=models.flow_control_state --cov-report=term-missing`

- [ ] **Atomic Task 3.2**: Performance testing
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Performance benchmarks
  - **Success**: State operations <1ms each
  - **Validation**: Performance tests pass

#### Task 1.2: Create CircuitBreaker and retry mechanisms (3h)

##### Blok 4: Circuit Breaker Pattern (1.5h)
**Agent Chain**: project-coder → code-reviewer → debugger
**⚠️ CODE REVIEW**: Ten blok będzie ~200-300 linii - WYMAGANE 2 review sessions!

- [ ] **Atomic Task 4.1**: Implement CircuitBreaker class
  - **Agent**: project-coder → debugger
  - **Time**: 45min
  - **Deliverable**: `/src/ai_writing_flow/utils/circuit_breaker.py`
  - **Success**: CLOSED/OPEN/HALF_OPEN states working
  - **Validation**: `pytest tests/test_circuit_breaker.py::test_state_transitions -v`
  - **Code Review Points**:
    1. Po implementacji base class i states (150 lines) → code-reviewer
    2. Po dodaniu failure logic i recovery (next 150 lines) → code-reviewer

- [ ] **Atomic Task 4.2**: Add failure threshold logic
  - **Agent**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Configurable failure detection
  - **Success**: Circuit opens after N failures
  - **Validation**: `pytest tests/test_circuit_breaker.py::test_threshold -v`

- [ ] **Atomic Task 4.3**: Implement recovery timeout
  - **Agent**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Time-based recovery mechanism
  - **Success**: Auto-recovery after timeout
  - **Validation**: `pytest tests/test_circuit_breaker.py::test_recovery -v`

##### Blok 5: RetryManager implementation (1h)
**Agent Chain**: project-coder → code-reviewer

- [ ] **Atomic Task 5.1**: Create RetryManager class
  - **Agent**: project-coder
  - **Time**: 30min
  - **Deliverable**: `/src/ai_writing_flow/utils/retry_manager.py`
  - **Success**: Per-operation retry tracking
  - **Validation**: `pytest tests/test_retry_manager.py::test_tracking -v`

- [ ] **Atomic Task 5.2**: Add exponential backoff
  - **Agent**: project-coder → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Exponential backoff calculation
  - **Success**: Delays increase exponentially with max cap
  - **Validation**: `pytest tests/test_retry_manager.py::test_backoff -v`

- [ ] **Atomic Task 5.3**: Integrate with CircuitBreaker
  - **Agent**: project-coder → architecture-advisor
  - **Time**: 10min
  - **Deliverable**: Combined failure handling
  - **Success**: Circuit breaker + retry work together
  - **Validation**: `pytest tests/test_integration.py::test_circuit_retry -v`

##### Blok 6: Testing comprehensive (30min)
**Agent Chain**: qa-test-engineer → code-reviewer

- [ ] **Atomic Task 6.1**: Test circuit breaker scenarios
  - **Agent**: qa-test-engineer
  - **Time**: 20min
  - **Deliverable**: Comprehensive test suite
  - **Success**: All state transitions tested
  - **Validation**: 100% coverage na circuit breaker logic

- [ ] **Atomic Task 6.2**: Test retry behavior under load
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Load testing dla retry mechanisms
  - **Success**: No infinite loops under any conditions
  - **Validation**: Stress tests pass

#### Task 1.3: Build StageManager and RetryManager (3h)

##### Blok 7: Advanced StageManager features (1.5h)
**Agent Chain**: project-coder → code-reviewer → architecture-advisor

- [ ] **Atomic Task 7.1**: Add execution history tracking
  - **Agent**: project-coder → architecture-advisor
  - **Time**: 45min
  - **Deliverable**: Timestamped execution log
  - **Success**: All stage transitions logged z metadata
  - **Validation**: `pytest tests/test_stage_manager.py::test_history -v`

- [ ] **Atomic Task 7.2**: Implement history analysis methods
  - **Agent**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: History query i analysis functions
  - **Success**: Can detect loops i timing patterns
  - **Validation**: `pytest tests/test_stage_manager.py::test_analysis -v`

- [ ] **Atomic Task 7.3**: Add history cleanup
  - **Agent**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: History size limits i cleanup
  - **Success**: Memory usage stays bounded
  - **Validation**: `pytest tests/test_stage_manager.py::test_cleanup -v`

##### Blok 8: Loop Prevention System (1h)
**Agent Chain**: project-coder → debugger → code-reviewer

- [ ] **Atomic Task 8.1**: Create LoopPreventionSystem
  - **Agent**: project-coder → debugger
  - **Time**: 30min
  - **Deliverable**: `/src/ai_writing_flow/utils/loop_prevention.py`
  - **Success**: Execution counting i limits enforced
  - **Validation**: `pytest tests/test_loop_prevention.py::test_limits -v`

- [ ] **Atomic Task 8.2**: Add method execution tracking
  - **Agent**: project-coder → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Per-method execution counters
  - **Success**: All method calls tracked
  - **Validation**: `pytest tests/test_loop_prevention.py::test_tracking -v`

- [ ] **Atomic Task 8.3**: Implement timeout guards
  - **Agent**: project-coder → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Total flow timeout enforcement
  - **Success**: Flow stops after max time
  - **Validation**: `pytest tests/test_loop_prevention.py::test_timeout -v`

##### Blok 9: Integration testing (30min)
**Agent Chain**: qa-test-engineer → architecture-advisor

- [ ] **Atomic Task 9.1**: Test integrated components
  - **Agent**: qa-test-engineer
  - **Time**: 20min
  - **Deliverable**: Integration test suite
  - **Success**: All components work together
  - **Validation**: `pytest tests/test_integration.py -v`

- [ ] **Atomic Task 9.2**: Validate architecture consistency
  - **Agent**: architecture-advisor
  - **Time**: 10min
  - **Deliverable**: Architecture validation report
  - **Success**: No architectural violations
  - **Validation**: Architecture review passed

---

### Phase 2: Linear Flow Implementation (Week 1-2)

⚠️ **CRITICAL FOR PHASE 2**: Ta faza zawiera przepisywanie całego flow (~1000+ linii kodu).
**OBOWIĄZKOWO**: Code review co 150 linii! Każdy blok w tej fazie będzie wymagał 2-3 review sessions.

#### Task 2.1: Rewrite flow methods without @router (6h)

##### Blok 10: Analysis i design (1h)
**Agent Chain**: crewai-flow-specialist → architecture-advisor

- [ ] **Atomic Task 10.1**: Map current @router dependencies
  - **Agent**: crewai-flow-specialist
  - **Time**: 30min
  - **Deliverable**: Current flow dependency graph
  - **Success**: All router usages documented
  - **Validation**: Dependency analysis complete

- [ ] **Atomic Task 10.2**: Design linear flow replacement
  - **Agent**: architecture-advisor → crewai-flow-specialist
  - **Time**: 30min
  - **Deliverable**: New linear flow design
  - **Success**: No circular dependencies possible
  - **Validation**: Architecture review approved

##### Blok 11: Initialize Flow Method rewrite (1.5h)
**Agent Chain**: crewai-flow-specialist → code-reviewer

- [ ] **Atomic Task 11.1**: Replace @start with linear initialization
  - **Agent**: crewai-flow-specialist
  - **Time**: 45min
  - **Deliverable**: New `initialize_flow()` method w main.py
  - **Success**: Proper input validation i flow setup
  - **Validation**: `pytest tests/test_flow_methods.py::test_initialize -v`

- [ ] **Atomic Task 11.2**: Add flow path configuration
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Dynamic flow path determination
  - **Success**: Skip logic works based on content type
  - **Validation**: `pytest tests/test_flow_methods.py::test_path_config -v`

- [ ] **Atomic Task 11.3**: Implement early validation
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Input validation z early failure
  - **Success**: Invalid inputs fail fast
  - **Validation**: `pytest tests/test_flow_methods.py::test_validation -v`

##### Blok 12: Research Method rewrite (1.5h)
**Agent Chain**: crewai-flow-specialist → code-reviewer

- [ ] **Atomic Task 12.1**: Convert @router to @listen pattern
  - **Agent**: crewai-flow-specialist
  - **Time**: 45min
  - **Deliverable**: New `execute_research()` method
  - **Success**: Linear execution, no loops
  - **Validation**: `pytest tests/test_flow_methods.py::test_research -v`

- [ ] **Atomic Task 12.2**: Add stage completion checks
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Skip logic dla completed research
  - **Success**: Research not re-executed if complete
  - **Validation**: `pytest tests/test_flow_methods.py::test_research_skip -v`

- [ ] **Atomic Task 12.3**: Integrate circuit breaker
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Circuit breaker wrapped execution
  - **Success**: Research fails safely under errors
  - **Validation**: `pytest tests/test_flow_methods.py::test_research_circuit -v`

##### Blok 13: Audience Alignment Method rewrite (1h)
**Agent Chain**: crewai-flow-specialist → code-reviewer

- [ ] **Atomic Task 13.1**: Convert to linear @listen pattern
  - **Agent**: crewai-flow-specialist
  - **Time**: 30min
  - **Deliverable**: New `execute_audience_alignment()` method
  - **Success**: Always executes, no circular calls
  - **Validation**: `pytest tests/test_flow_methods.py::test_audience -v`

- [ ] **Atomic Task 13.2**: Add error handling with fallback
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Graceful failure handling
  - **Success**: Audience failures don't stop flow
  - **Validation**: `pytest tests/test_flow_methods.py::test_audience_errors -v`

- [ ] **Atomic Task 13.3**: Integrate state updates
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Proper state mutation
  - **Success**: Audience data properly stored
  - **Validation**: `pytest tests/test_flow_methods.py::test_audience_state -v`

##### Blok 14: Draft Generation Method rewrite (1h)
**Agent Chain**: crewai-flow-specialist → code-reviewer

- [ ] **Atomic Task 14.1**: Convert to linear execution
  - **Agent**: crewai-flow-specialist
  - **Time**: 30min
  - **Deliverable**: New `execute_draft_generation()` method
  - **Success**: No loops, clean retry logic
  - **Validation**: `pytest tests/test_flow_methods.py::test_draft -v`

- [ ] **Atomic Task 14.2**: Add human review checkpoint
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Human review decision point
  - **Success**: Review process doesn't create loops
  - **Validation**: `pytest tests/test_flow_methods.py::test_human_review -v`

- [ ] **Atomic Task 14.3**: Implement draft versioning
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Version tracking dla drafts
  - **Success**: All draft iterations tracked
  - **Validation**: `pytest tests/test_flow_methods.py::test_versioning -v`

#### Task 2.2: Implement proper @listen chain (4h)

##### Blok 15: Listen Chain Design (1h)
**Agent Chain**: architecture-advisor → crewai-flow-specialist

- [ ] **Atomic Task 15.1**: Map complete linear execution flow
  - **Agent**: architecture-advisor
  - **Time**: 30min
  - **Deliverable**: Complete @listen chain diagram
  - **Success**: Clear start-to-end execution path
  - **Validation**: Flow diagram review approved

- [ ] **Atomic Task 15.2**: Define method return values
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Standardized return value patterns
  - **Success**: All methods return next step consistently
  - **Validation**: `pytest tests/test_flow_chain.py::test_returns -v`

- [ ] **Atomic Task 15.3**: Add conditional routing logic
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 10min
  - **Deliverable**: State-based routing decisions
  - **Success**: Routing based on state, not loops
  - **Validation**: `pytest tests/test_flow_chain.py::test_routing -v`

##### Blok 16: Style Validation Chain (1.5h)
**Agent Chain**: crewai-flow-specialist → code-reviewer

- [ ] **Atomic Task 16.1**: Create execute_style_validation method
  - **Agent**: crewai-flow-specialist
  - **Time**: 45min
  - **Deliverable**: Style validation z retry limits
  - **Success**: Limited retries, escalation path
  - **Validation**: `pytest tests/test_flow_chain.py::test_style -v`

- [ ] **Atomic Task 16.2**: Add style retry logic
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Retry counter i max limit enforcement
  - **Success**: Style retries don't exceed limits
  - **Validation**: `pytest tests/test_flow_chain.py::test_style_retries -v`

- [ ] **Atomic Task 16.3**: Implement escalation pathway
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Human escalation dla style issues
  - **Success**: Clear escalation after max retries
  - **Validation**: `pytest tests/test_flow_chain.py::test_style_escalation -v`

##### Blok 17: Quality Assessment Chain (1.5h)
**Agent Chain**: crewai-flow-specialist → code-reviewer

- [ ] **Atomic Task 17.1**: Create execute_quality_assessment method
  - **Agent**: crewai-flow-specialist
  - **Time**: 45min
  - **Deliverable**: Final quality check z approval logic
  - **Success**: Quality gates properly enforced
  - **Validation**: `pytest tests/test_flow_chain.py::test_quality -v`

- [ ] **Atomic Task 17.2**: Add quality retry mechanism
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Quality-based retry logic
  - **Success**: Poor quality triggers appropriate action
  - **Validation**: `pytest tests/test_flow_chain.py::test_quality_retries -v`

- [ ] **Atomic Task 17.3**: Implement final output path
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Clean finalization logic
  - **Success**: Approved content goes to finalization
  - **Validation**: `pytest tests/test_flow_chain.py::test_finalization -v`

#### Task 2.3: Add execution guards and limits (3h)

##### Blok 18: Guards Implementation (1.5h)
**Agent Chain**: project-coder → code-reviewer → debugger

- [ ] **Atomic Task 18.1**: Integrate guards with all flow methods
  - **Agent**: project-coder → debugger
  - **Time**: 45min
  - **Deliverable**: Guard integration w wszystkich flow methods
  - **Success**: All methods protected by guards
  - **Validation**: `pytest tests/test_guards.py::test_integration -v`

- [ ] **Atomic Task 18.2**: Add resource monitoring guards
  - **Agent**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: CPU i memory monitoring guards
  - **Success**: Flow stops when resources exceeded
  - **Validation**: `pytest tests/test_guards.py::test_resources -v`

- [ ] **Atomic Task 18.3**: Implement execution time limits
  - **Agent**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Configurable timeout guards
  - **Success**: Flow stops after max execution time
  - **Validation**: `pytest tests/test_guards.py::test_timeouts -v`

##### Blok 19: Guard Testing (1h)
**Agent Chain**: qa-test-engineer → debugger

- [ ] **Atomic Task 19.1**: Test guard effectiveness
  - **Agent**: qa-test-engineer → debugger
  - **Time**: 30min
  - **Deliverable**: Guard effectiveness test suite
  - **Success**: Guards prevent all infinite loop scenarios
  - **Validation**: `pytest tests/test_guards.py --timeout=30 -v`

- [ ] **Atomic Task 19.2**: Load test with guards
  - **Agent**: qa-test-engineer → debugger
  - **Time**: 20min
  - **Deliverable**: Load testing z guard protection
  - **Success**: System stable under stress with guards
  - **Validation**: Load tests pass with guard protection

- [ ] **Atomic Task 19.3**: Validate guard configuration
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Configuration validation tests
  - **Success**: All guard configs work correctly
  - **Validation**: Configuration tests comprehensive

##### Blok 20: Final Integration (30min)
**Agent Chain**: crewai-flow-specialist → code-reviewer → architecture-advisor

- [ ] **Atomic Task 20.1**: Complete flow integration test
  - **Agent**: crewai-flow-specialist → architecture-advisor
  - **Time**: 20min
  - **Deliverable**: End-to-end flow test z guards
  - **Success**: Complete flow works bez loops
  - **Validation**: `pytest tests/test_complete_flow.py -v`

- [ ] **Atomic Task 20.2**: Performance validation
  - **Agent**: crewai-flow-specialist → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Performance metrics validation
  - **Success**: All performance targets met
  - **Validation**: Performance benchmarks pass

---

### Phase 3: Testing & Validation (Week 2)

#### Task 3.1: Create comprehensive test suite (8h)

##### Blok 21: Unit Tests Core Components (3h)
**Agent Chain**: qa-test-engineer → code-reviewer

- [ ] **Atomic Task 21.1**: Complete FlowControlState tests
  - **Agent**: qa-test-engineer
  - **Time**: 45min
  - **Deliverable**: `/tests/test_flow_control_state.py`
  - **Success**: 100% coverage, all edge cases
  - **Validation**: `pytest tests/test_flow_control_state.py --cov=100%`

- [ ] **Atomic Task 21.2**: Complete CircuitBreaker tests
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: `/tests/test_circuit_breaker.py`
  - **Success**: All state transitions tested
  - **Validation**: `pytest tests/test_circuit_breaker.py --cov=100%`

- [ ] **Atomic Task 21.3**: Complete StageManager tests
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: `/tests/test_stage_manager.py`
  - **Success**: All stage operations tested
  - **Validation**: `pytest tests/test_stage_manager.py --cov=100%`

- [ ] **Atomic Task 21.4**: Complete RetryManager tests
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: `/tests/test_retry_manager.py`
  - **Success**: All retry scenarios covered
  - **Validation**: `pytest tests/test_retry_manager.py --cov=100%`

##### Blok 22: Integration Tests (3h)
**Agent Chain**: qa-test-engineer → crewai-flow-specialist → code-reviewer

- [ ] **Atomic Task 22.1**: Complete linear flow execution tests
  - **Agent**: qa-test-engineer → crewai-flow-specialist
  - **Time**: 1h
  - **Deliverable**: `/tests/test_flow_integration.py`
  - **Success**: Full flow executes bez loops
  - **Validation**: `pytest tests/test_flow_integration.py --timeout=300 -v`

- [ ] **Atomic Task 22.2**: All error scenario tests
  - **Agent**: qa-test-engineer → debugger
  - **Time**: 1h
  - **Deliverable**: `/tests/test_error_scenarios.py`
  - **Success**: All error paths tested
  - **Validation**: `pytest tests/test_error_scenarios.py -v`

- [ ] **Atomic Task 22.3**: Retry and escalation path tests
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 1h
  - **Deliverable**: `/tests/test_retry_escalation.py`
  - **Success**: All retry scenarios work correctly
  - **Validation**: `pytest tests/test_retry_escalation.py -v`

##### Blok 23: Load and Stress Tests (2h)
**Agent Chain**: performance-tester → qa-test-engineer → code-reviewer

- [ ] **Atomic Task 23.1**: Concurrent execution tests
  - **Agent**: performance-tester
  - **Time**: 1h
  - **Deliverable**: `/tests/test_concurrent_flows.py`
  - **Success**: Multiple flows run simultaneously
  - **Validation**: `pytest tests/test_concurrent_flows.py --workers=10 -v`

- [ ] **Atomic Task 23.2**: Resource usage under load tests
  - **Agent**: performance-tester → debugger
  - **Time**: 1h
  - **Deliverable**: `/tests/test_resource_usage.py`
  - **Success**: Resources stay within limits under load
  - **Validation**: `pytest tests/test_resource_usage.py --monitor-resources -v`

#### Task 3.2: Implement performance monitoring (4h)

##### Blok 24: FlowMetrics System (2h)
**Agent Chain**: project-coder → code-reviewer

- [ ] **Atomic Task 24.1**: Implement FlowMetrics class
  - **Agent**: project-coder
  - **Time**: 1h
  - **Deliverable**: `/src/ai_writing_flow/monitoring/flow_metrics.py`
  - **Success**: All KPIs tracked w real-time
  - **Validation**: `pytest tests/test_flow_metrics.py::test_kpi_collection -v`

- [ ] **Atomic Task 24.2**: Add performance KPI calculations
  - **Agent**: project-coder → performance-tester
  - **Time**: 45min
  - **Deliverable**: KPI calculation methods
  - **Success**: All target metrics calculated correctly
  - **Validation**: `pytest tests/test_flow_metrics.py::test_kpi_calculations -v`

- [ ] **Atomic Task 24.3**: Implement metrics export
  - **Agent**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Metrics export to JSON/Prometheus
  - **Success**: Metrics accessible dla monitoring
  - **Validation**: `curl http://localhost:8000/metrics` returns data

##### Blok 25: Real-time Monitoring (1.5h)
**Agent Chain**: project-coder → code-reviewer

- [ ] **Atomic Task 25.1**: Create monitoring dashboard data
  - **Agent**: project-coder
  - **Time**: 45min
  - **Deliverable**: Dashboard API endpoints
  - **Success**: Real-time metrics available via API
  - **Validation**: `pytest tests/test_monitoring_api.py -v`

- [ ] **Atomic Task 25.2**: Implement alerting system
  - **Agent**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Threshold-based alerting
  - **Success**: Alerts trigger on threshold breaches
  - **Validation**: `pytest tests/test_alerting.py -v`

- [ ] **Atomic Task 25.3**: Add historical metrics storage
  - **Agent**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Metrics persistence layer
  - **Success**: Historical data preserved
  - **Validation**: `pytest tests/test_metrics_storage.py -v`

##### Blok 26: Monitoring Testing (30min)
**Agent Chain**: qa-test-engineer → performance-tester

- [ ] **Atomic Task 26.1**: Test metrics accuracy
  - **Agent**: qa-test-engineer → performance-tester
  - **Time**: 20min
  - **Deliverable**: `/tests/test_metrics_accuracy.py`
  - **Success**: All metrics match expected values
  - **Validation**: Accuracy tests pass within 5% margin

- [ ] **Atomic Task 26.2**: Test alerting reliability
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 10min
  - **Deliverable**: `/tests/test_alerting_reliability.py`
  - **Success**: Alerts fire correctly and timely
  - **Validation**: All alert scenarios tested

#### Task 3.3: Add quality gates and validation (4h)

##### Blok 27: QualityGate System (2h)
**Agent Chain**: qa-test-engineer → architecture-advisor → code-reviewer

- [ ] **Atomic Task 27.1**: Implement QualityGate class
  - **Agent**: qa-test-engineer → architecture-advisor
  - **Time**: 1h
  - **Deliverable**: `/src/ai_writing_flow/validation/quality_gate.py`
  - **Success**: All validation rules implemented
  - **Validation**: `pytest tests/test_quality_gate.py -v`

- [ ] **Atomic Task 27.2**: Add static analysis validation
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Static code analysis integration
  - **Success**: Circular dependencies detected
  - **Validation**: `python -m quality_gate.static_analysis`

- [ ] **Atomic Task 27.3**: Add runtime validation
  - **Agent**: qa-test-engineer → debugger
  - **Time**: 15min
  - **Deliverable**: Runtime behavior validation
  - **Success**: Loop detection during execution
  - **Validation**: Runtime validation catches loops

##### Blok 28: Validation Rules (1.5h)
**Agent Chain**: qa-test-engineer → debugger

- [ ] **Atomic Task 28.1**: Create loop detection rules
  - **Agent**: qa-test-engineer → debugger
  - **Time**: 45min
  - **Deliverable**: Loop detection algorithms
  - **Success**: All possible loops detected
  - **Validation**: `pytest tests/test_loop_detection.py -v`

- [ ] **Atomic Task 28.2**: Add resource limit validation
  - **Agent**: qa-test-engineer → performance-tester
  - **Time**: 30min
  - **Deliverable**: Resource usage validation rules
  - **Success**: Resource violations caught early
  - **Validation**: `pytest tests/test_resource_validation.py -v`

- [ ] **Atomic Task 28.3**: Create state consistency validation
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 15min
  - **Deliverable**: State validation rules
  - **Success**: Invalid states caught
  - **Validation**: `pytest tests/test_state_validation.py -v`

##### Blok 29: Quality Gate Testing (30min)
**Agent Chain**: qa-test-engineer → architecture-advisor

- [ ] **Atomic Task 29.1**: Test all validation rules
  - **Agent**: qa-test-engineer
  - **Time**: 20min
  - **Deliverable**: `/tests/test_validation_rules.py`
  - **Success**: All rules tested z edge cases
  - **Validation**: All validation rule tests pass

- [ ] **Atomic Task 29.2**: Test quality gate integration
  - **Agent**: qa-test-engineer → architecture-advisor
  - **Time**: 10min
  - **Deliverable**: `/tests/test_quality_gate_integration.py`
  - **Success**: Quality gates block bad code
  - **Validation**: Integration tests verified

---

### Phase 4: Integration & Deployment (Week 3)

#### Task 4.1: Integrate with existing Kolegium system (6h)

##### Blok 30: Kolegium Integration Update (3h)
**Agent Chain**: project-coder → code-reviewer

- [ ] **Atomic Task 30.1**: Update flow registration
  - **Agent**: project-coder
  - **Time**: 1h
  - **Deliverable**: New flow class registration w Kolegium
  - **Success**: AIWritingFlowV2 properly registered
  - **Validation**: `python -c "from ai_writing_flow.main import AIWritingFlowV2; print('OK')"`

- [ ] **Atomic Task 30.2**: Update UI bridge integration
  - **Agent**: project-coder → code-reviewer
  - **Time**: 1h
  - **Deliverable**: UI bridge compatibility z new flow
  - **Success**: Human review integration works
  - **Validation**: `pytest tests/test_ui_bridge_integration.py -v`

- [ ] **Atomic Task 30.3**: Update API endpoints
  - **Agent**: project-coder → code-reviewer
  - **Time**: 1h
  - **Deliverable**: API compatibility updates
  - **Success**: All endpoints work z new flow
  - **Validation**: `pytest tests/test_api_endpoints.py -v`

##### Blok 31: System Integration Testing (2h)
**Agent Chain**: qa-test-engineer → project-coder → code-reviewer

- [ ] **Atomic Task 31.1**: End-to-end user flow tests
  - **Agent**: qa-test-engineer → project-coder
  - **Time**: 1h
  - **Deliverable**: `/tests/test_e2e_user_flows.py`
  - **Success**: Complete user workflows tested
  - **Validation**: E2E tests pass consistently

- [ ] **Atomic Task 31.2**: API backwards compatibility tests
  - **Agent**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: `/tests/test_api_compatibility.py`
  - **Success**: Existing API clients work
  - **Validation**: Backwards compatibility verified

- [ ] **Atomic Task 31.3**: Data migration tests
  - **Agent**: qa-test-engineer → deployment-specialist
  - **Time**: 15min
  - **Deliverable**: `/tests/test_data_migration.py`
  - **Success**: Old states migrate cleanly
  - **Validation**: Migration tests pass

##### Blok 32: Performance Integration Testing (1h)
**Agent Chain**: performance-tester → qa-test-engineer

- [ ] **Atomic Task 32.1**: Integrated system performance tests
  - **Agent**: performance-tester
  - **Time**: 45min
  - **Deliverable**: `/tests/test_integrated_performance.py`
  - **Success**: Performance targets met w integrated system
  - **Validation**: Performance benchmarks pass

- [ ] **Atomic Task 32.2**: Production environment resource tests
  - **Agent**: performance-tester → deployment-specialist
  - **Time**: 15min
  - **Deliverable**: Production resource usage tests
  - **Success**: Resources within production limits
  - **Validation**: Resource tests verified

#### Task 4.2: Load testing and optimization (4h)

##### Blok 33: Concurrent Flow Testing (2h)
**Agent Chain**: performance-tester → debugger

- [ ] **Atomic Task 33.1**: 10 concurrent flows test
  - **Agent**: performance-tester
  - **Time**: 1h
  - **Deliverable**: `/tests/test_10_concurrent_flows.py`
  - **Success**: All flows complete successfully
  - **Validation**: `pytest tests/test_10_concurrent_flows.py --workers=10 -v`

- [ ] **Atomic Task 33.2**: Resource contention tests
  - **Agent**: performance-tester → debugger
  - **Time**: 45min
  - **Deliverable**: `/tests/test_resource_contention.py`
  - **Success**: No resource conflicts detected
  - **Validation**: Contention tests pass

- [ ] **Atomic Task 33.3**: Scaling behavior tests
  - **Agent**: performance-tester → deployment-specialist
  - **Time**: 15min
  - **Deliverable**: `/tests/test_scaling_behavior.py`
  - **Success**: Linear scaling observed
  - **Validation**: Scaling characteristics verified

##### Blok 34: Performance Optimization (1.5h)
**Agent Chain**: performance-tester → project-coder

- [ ] **Atomic Task 34.1**: Profile flow execution
  - **Agent**: performance-tester
  - **Time**: 45min
  - **Deliverable**: Performance profiling results
  - **Success**: Bottlenecks identified
  - **Validation**: Profiling data analyzed

- [ ] **Atomic Task 34.2**: Optimize critical paths
  - **Agent**: project-coder → performance-tester → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Optimized critical sections
  - **Success**: Performance improvements measured
  - **Validation**: Optimization gains verified

##### Blok 35: Stress Testing (30min)
**Agent Chain**: performance-tester → debugger

- [ ] **Atomic Task 35.1**: Heavy load stress test
  - **Agent**: performance-tester → debugger
  - **Time**: 20min
  - **Deliverable**: `/tests/test_heavy_load.py`
  - **Success**: System stable under stress
  - **Validation**: Stress tests pass

- [ ] **Atomic Task 35.2**: Failure recovery under load test
  - **Agent**: performance-tester → debugger
  - **Time**: 10min
  - **Deliverable**: `/tests/test_failure_recovery_load.py`
  - **Success**: Graceful degradation verified
  - **Validation**: Recovery tests pass

#### Task 4.3: Production deployment and monitoring (4h)

##### Blok 36: Deployment Preparation (2h)
**Agent Chain**: deployment-specialist → code-reviewer

- [ ] **Atomic Task 36.1**: Create deployment scripts
  - **Agent**: deployment-specialist
  - **Time**: 1h
  - **Deliverable**: `/deployment/deploy_flow_v2.sh`
  - **Success**: Zero-downtime deployment possible
  - **Validation**: Deployment scripts tested w staging

- [ ] **Atomic Task 36.2**: Setup production monitoring
  - **Agent**: deployment-specialist → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Production monitoring infrastructure
  - **Success**: All metrics visible w production
  - **Validation**: Monitoring stack verified

- [ ] **Atomic Task 36.3**: Create rollback procedures
  - **Agent**: deployment-specialist → emergency-system-controller
  - **Time**: 15min
  - **Deliverable**: `/deployment/rollback_flow_v2.sh`
  - **Success**: Fast rollback possible
  - **Validation**: Rollback procedures tested

##### Blok 37: Production Deployment (1.5h)
**Agent Chain**: deployment-specialist → emergency-system-controller

- [ ] **Atomic Task 37.1**: Execute staged deployment
  - **Agent**: deployment-specialist → emergency-system-controller
  - **Time**: 1h
  - **Deliverable**: Production deployment completed
  - **Success**: New flow active w production
  - **Validation**: Deployment health checks pass

- [ ] **Atomic Task 37.2**: Verify production metrics
  - **Agent**: deployment-specialist → performance-tester
  - **Time**: 30min
  - **Deliverable**: Production metrics validation
  - **Success**: All KPIs within target ranges
  - **Validation**: Production metrics green

##### Blok 38: Post-Deployment Monitoring (30min)
**Agent Chain**: deployment-specialist → performance-tester

- [ ] **Atomic Task 38.1**: Monitor initial production load
  - **Agent**: deployment-specialist → performance-tester
  - **Time**: 20min
  - **Deliverable**: Initial load monitoring results
  - **Success**: System stable under real load
  - **Validation**: Load monitoring verified

- [ ] **Atomic Task 38.2**: Validate alerting system
  - **Agent**: deployment-specialist → emergency-system-controller
  - **Time**: 10min
  - **Deliverable**: Alert system validation w production
  - **Success**: Alerts working w production
  - **Validation**: Alert system verified

---

## 🔧 Tools & Resources

### Required Tools
- **pytest**: Testing framework
- **coverage.py**: Code coverage
- **psutil**: System monitoring
- **asyncio**: Async execution
- **pydantic**: Data validation
- **crewai**: Flow framework

### External Dependencies
- **OpenAI API**: LLM services
- **Redis**: Caching layer
- **PostgreSQL**: State persistence
- **Prometheus**: Metrics collection

### Team Skills Needed
- CrewAI Flow expertise
- Circuit breaker patterns
- Performance testing
- Production deployment

## 📊 Success Metrics

### Phase-by-phase KPIs
- **Phase 1**: Core components implemented, tested
- **Phase 2**: Linear flow working, no loops
- **Phase 3**: Comprehensive testing passed
- **Phase 4**: Production deployment successful

### Overall Project KPIs
- **Zero Infinite Loops**: Static + runtime verification
- **Performance**: CPU <30%, Memory <500MB, Time <5min
- **Reliability**: >95% success rate, <5% retry rate
- **Quality**: >80% test coverage, all quality gates pass

### Quality Indicators
- All tests pass consistently
- Performance benchmarks met
- No security vulnerabilities
- Clean architecture validated

## ⚠️ Risk Management

### Identified Risks
1. **Complex Migration**: Mitigated by gradual rollout
2. **Performance Regression**: Mitigated by extensive testing
3. **Integration Issues**: Mitigated by comprehensive E2E tests

### Rollback Plans
- **Phase 1**: Revert to models backup
- **Phase 2**: Switch back to old flow implementation
- **Phase 3**: Disable new components
- **Phase 4**: Full system rollback procedures

### Escalation Paths
- **Technical Issues**: architecture-advisor → emergency-system-controller
- **Performance Issues**: performance-tester → deployment-specialist
- **Production Issues**: deployment-specialist → emergency-system-controller

## 🚀 Quick Start

### First 3 Steps to Begin
1. **Setup Environment**: `cd ai_writing_flow && python -m venv venv && source venv/bin/activate`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Run Validation**: `pytest tests/ -v`

### Commands to Run
```bash
# Start development
/nakurwiaj 0

# Execute specific block
/nakurwiaj 15

# Run tests
pytest tests/test_flow_control_state.py -v

# Check performance
python -m monitoring.flow_metrics
```

### How to Verify Setup
1. All imports work: `python -c "from models.flow_stage import FlowStage"`
2. Tests pass: `pytest tests/ --tb=short`
3. Performance baseline: `python benchmark.py`

---

## 📝 Code Review Summary

### Total Expected Code Reviews
- **Phase 1**: ~15 review sessions (2,250 lines total)
- **Phase 2**: ~25 review sessions (3,750 lines total)
- **Phase 3**: ~10 review sessions (1,500 lines testing)
- **Phase 4**: ~5 review sessions (750 lines integration)

### Review Checkpoint Formula
```
Total Lines Written ÷ 150 = Number of Required Reviews
```

### Code Review Tracking
Each atomic task MUST track:
1. Lines of code written
2. Number of review sessions completed
3. Issues found and fixed
4. Final approval status

## 💡 Emergency Procedures

### If Infinite Loop Detected
1. **Immediate**: `/agent emergency-system-controller`
2. **Stop Flow**: `killall python` lub circuit breaker trigger
3. **Rollback**: Use rollback scripts
4. **Investigate**: Check execution history w StageManager

### If Performance Degraded
1. **Monitor**: Check FlowMetrics dashboard
2. **Scale Down**: Reduce concurrent flows
3. **Optimize**: Profile i fix bottlenecks
4. **Alert**: Notify performance team

### If Tests Failing
1. **Stop Deployment**: Hold production rollout
2. **Debug**: Use debugger agent for analysis
3. **Fix**: Address failing tests
4. **Verify**: Full test suite pass before continue

---

*Atomic task decomposition created: 2025-08-03*  
*Total estimated time: 50 hours over 3 weeks*  
*Risk level: Medium → Low after implementation*  
*Agent chains optimized for /nakurwiaj compatibility*