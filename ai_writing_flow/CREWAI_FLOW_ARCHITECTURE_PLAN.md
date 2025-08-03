# CrewAI Flow Architecture Plan - AI Writing Flow
## Kompleksowy plan architektury rozwiązujący problemy infinite loops

---

## 🎯 Executive Summary

Obecny AI Writing Flow zawiera krytyczne błędy architektury powodujące infinite loops i zawiesanie systemu. Ten plan przedstawia kompletną przeprojektowaną architekturę opartą na best practices CrewAI, która rozwiązuje wszystkie zidentyfikowane problemy.

### Główne problemy do rozwiązania:
1. **Circular Dependencies**: Router powoduje pętle między metodami
2. **Misuse of @router**: Używanie @router do loops zamiast branching
3. **State Management**: Brak proper state isolation
4. **Flow Control**: Niepoprawne routing patterns
5. **Resource Leaks**: CPU 97.9% z powodu infinite execution

---

## 🏗️ Nowa Architektura Flow

### 1. Linear Flow Pattern (No Loops)

Zamiast circular flow z routerami, implementujemy **linear pipeline** z conditional skips:

```
START → INPUT_VALIDATION → RESEARCH → AUDIENCE → DRAFT → STYLE → QUALITY → FINALIZE → END
         ↓                   ↓         ↓        ↓       ↓       ↓
         ├─ SKIP_RESEARCH ────┘         │        │       │       │
         ├─ SKIP_AUDIENCE ──────────────┘        │       │       │
         ├─ HUMAN_FEEDBACK_LOOP ─────────────────┘       │       │
         ├─ STYLE_RETRY_LIMIT ───────────────────────────┘       │
         └─ QUALITY_ESCALATION ──────────────────────────────────┘
```

### 2. State-Based Stage Management

```python
class FlowStage(str, Enum):
    INPUT_VALIDATION = "input_validation"
    RESEARCH_PHASE = "research_phase"
    AUDIENCE_ALIGNMENT = "audience_alignment"
    DRAFT_GENERATION = "draft_generation"
    HUMAN_REVIEW = "human_review"
    STYLE_VALIDATION = "style_validation"
    QUALITY_ASSESSMENT = "quality_assessment"
    OUTPUT_FINALIZATION = "output_finalization"
    COMPLETED = "completed"
    FAILED = "failed"

class FlowControlState(BaseModel):
    current_stage: FlowStage = FlowStage.INPUT_VALIDATION
    next_stage: Optional[FlowStage] = None
    can_proceed: bool = True
    retry_count: Dict[str, int] = Field(default_factory=dict)
    max_retries: Dict[str, int] = Field(default_factory=lambda: {
        "draft_generation": 3,
        "style_validation": 2,
        "quality_assessment": 2
    })
    skip_stages: Set[FlowStage] = Field(default_factory=set)
    execution_history: List[Tuple[FlowStage, datetime, str]] = Field(default_factory=list)
```

---

## 🔄 Flow Method Architecture

### Core Pattern: Sequential Execution with Guards

```python
class AIWritingFlowV2(Flow[WritingFlowState]):
    """Redesigned flow without circular dependencies"""
    
    def __init__(self):
        super().__init__(verbose=False)
        self.crew = WritingCrew()
        self.flow_control = FlowControlState()
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=Exception
        )
    
    @start()
    def initialize_flow(self) -> str:
        """Entry point - validate input and set up flow"""
        self.flow_control.current_stage = FlowStage.INPUT_VALIDATION
        self._log_stage_execution("initialize_flow", "started")
        
        # Validate required inputs
        if not self._validate_inputs():
            return "failed_validation"
        
        # Determine flow path based on content ownership
        self._configure_flow_path()
        
        return "execute_research" if self._should_execute_research() else "execute_audience_alignment"
    
    @listen("execute_research")
    def execute_research(self) -> str:
        """Research phase - only if needed"""
        with self._circuit_breaker:
            self.flow_control.current_stage = FlowStage.RESEARCH_PHASE
            
            if self._is_stage_completed(FlowStage.RESEARCH_PHASE):
                return "execute_audience_alignment"
            
            try:
                result = self._execute_research_crew()
                self._update_state_with_research(result)
                self._mark_stage_completed(FlowStage.RESEARCH_PHASE)
                return "execute_audience_alignment"
                
            except Exception as e:
                return self._handle_stage_failure("research", e)
    
    @listen("execute_audience_alignment")
    def execute_audience_alignment(self) -> str:
        """Audience alignment - always required"""
        with self._circuit_breaker:
            self.flow_control.current_stage = FlowStage.AUDIENCE_ALIGNMENT
            
            if self._is_stage_completed(FlowStage.AUDIENCE_ALIGNMENT):
                return "execute_draft_generation"
            
            try:
                result = self._execute_audience_crew()
                self._update_state_with_audience_data(result)
                self._mark_stage_completed(FlowStage.AUDIENCE_ALIGNMENT)
                return "execute_draft_generation"
                
            except Exception as e:
                return self._handle_stage_failure("audience", e)
    
    @listen("execute_draft_generation")
    def execute_draft_generation(self) -> str:
        """Draft generation with retry logic"""
        with self._circuit_breaker:
            self.flow_control.current_stage = FlowStage.DRAFT_GENERATION
            
            try:
                result = self._execute_writer_crew()
                self._update_state_with_draft(result)
                self._mark_stage_completed(FlowStage.DRAFT_GENERATION)
                
                # Check if human review is needed
                if self._requires_human_review():
                    return "await_human_review"
                
                return "execute_style_validation"
                
            except Exception as e:
                return self._handle_stage_failure("draft_generation", e)
    
    @listen("await_human_review")
    def await_human_review(self) -> str:
        """Human review checkpoint - NO LOOPS"""
        self.flow_control.current_stage = FlowStage.HUMAN_REVIEW
        
        # Send to UI and wait for response (timeout after 5 minutes)
        feedback = self._request_human_feedback_with_timeout()
        
        if feedback:
            self._process_human_feedback(feedback)
            
            # Based on feedback type, determine next action
            if feedback.feedback_type == "minor":
                return "execute_style_validation"
            elif feedback.feedback_type == "major":
                # Reset draft stage but keep other work
                self._reset_stage(FlowStage.DRAFT_GENERATION)
                return "execute_draft_generation"
            elif feedback.feedback_type == "pivot":
                # Reset all content stages but keep research
                self._reset_content_stages()
                return "execute_audience_alignment"
        
        # No feedback = proceed
        return "execute_style_validation"
    
    @listen("execute_style_validation")
    def execute_style_validation(self) -> str:
        """Style validation with limited retries"""
        with self._circuit_breaker:
            self.flow_control.current_stage = FlowStage.STYLE_VALIDATION
            
            try:
                result = self._execute_style_crew()
                self._update_state_with_style_results(result)
                
                if result.is_compliant:
                    self._mark_stage_completed(FlowStage.STYLE_VALIDATION)
                    return "execute_quality_assessment"
                
                # Style issues found
                retry_count = self._increment_retry_count("style_validation")
                if retry_count > self.flow_control.max_retries["style_validation"]:
                    return "escalate_to_human"
                
                # Reset draft for regeneration with style feedback
                self._reset_stage(FlowStage.DRAFT_GENERATION)
                return "execute_draft_generation"
                
            except Exception as e:
                return self._handle_stage_failure("style_validation", e)
    
    @listen("execute_quality_assessment")
    def execute_quality_assessment(self) -> str:
        """Final quality check"""
        with self._circuit_breaker:
            self.flow_control.current_stage = FlowStage.QUALITY_ASSESSMENT
            
            try:
                result = self._execute_quality_crew()
                self._update_state_with_quality_results(result)
                
                if result.is_approved and not result.requires_human_review:
                    self._mark_stage_completed(FlowStage.QUALITY_ASSESSMENT)
                    return "finalize_output"
                
                # Quality issues
                if result.requires_human_review:
                    return "escalate_to_human"
                
                retry_count = self._increment_retry_count("quality_assessment")
                if retry_count > self.flow_control.max_retries["quality_assessment"]:
                    return "escalate_to_human"
                
                return "execute_draft_generation"
                
            except Exception as e:
                return self._handle_stage_failure("quality_assessment", e)
    
    @listen("escalate_to_human")
    def escalate_to_human(self) -> str:
        """Human escalation endpoint"""
        self._log_escalation()
        self.ui_bridge.escalate_to_human(self.state, self.flow_control)
        return "finalize_output"  # Always end after escalation
    
    @listen("failed_validation")
    def failed_validation(self) -> str:
        """Validation failure endpoint"""
        self.flow_control.current_stage = FlowStage.FAILED
        self._log_validation_failure()
        return self.state  # End flow
    
    @listen("finalize_output")
    def finalize_output(self) -> WritingFlowState:
        """Final output preparation"""
        self.flow_control.current_stage = FlowStage.OUTPUT_FINALIZATION
        
        self._prepare_final_output()
        self._calculate_performance_metrics()
        self._cleanup_resources()
        
        self.flow_control.current_stage = FlowStage.COMPLETED
        return self.state
```

---

## 🔧 Supporting Architecture Components

### 1. Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Prevent cascade failures and infinite loops"""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __enter__(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._on_success()
        else:
            self._on_failure()
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

### 2. Stage Management System

```python
class StageManager:
    """Manage flow stage transitions and state"""
    
    def __init__(self, flow_control: FlowControlState):
        self.flow_control = flow_control
        self.completed_stages = set()
        self.stage_results = {}
    
    def mark_stage_completed(self, stage: FlowStage, result: Any = None):
        """Mark stage as completed and store result"""
        self.completed_stages.add(stage)
        self.stage_results[stage] = result
        self.flow_control.execution_history.append(
            (stage, datetime.now(), "completed")
        )
    
    def is_stage_completed(self, stage: FlowStage) -> bool:
        """Check if stage was already completed"""
        return stage in self.completed_stages
    
    def reset_stage(self, stage: FlowStage):
        """Reset stage for retry"""
        self.completed_stages.discard(stage)
        self.stage_results.pop(stage, None)
        self.flow_control.execution_history.append(
            (stage, datetime.now(), "reset")
        )
    
    def reset_content_stages(self):
        """Reset all content-related stages for pivot"""
        content_stages = {
            FlowStage.AUDIENCE_ALIGNMENT,
            FlowStage.DRAFT_GENERATION,
            FlowStage.STYLE_VALIDATION,
            FlowStage.QUALITY_ASSESSMENT
        }
        for stage in content_stages:
            self.reset_stage(stage)
```

### 3. Retry Management

```python
class RetryManager:
    """Manage retries with exponential backoff"""
    
    def __init__(self, max_retries: Dict[str, int]):
        self.max_retries = max_retries
        self.retry_counts = defaultdict(int)
        self.last_retry_time = defaultdict(float)
    
    def can_retry(self, operation: str) -> bool:
        """Check if operation can be retried"""
        return self.retry_counts[operation] < self.max_retries.get(operation, 0)
    
    def increment_retry(self, operation: str) -> int:
        """Increment retry count and return current count"""
        self.retry_counts[operation] += 1
        self.last_retry_time[operation] = time.time()
        return self.retry_counts[operation]
    
    def get_backoff_delay(self, operation: str) -> float:
        """Calculate exponential backoff delay"""
        retry_count = self.retry_counts[operation]
        return min(2 ** retry_count, 30)  # Max 30 seconds
```

---

## 📊 Metryki Sukcesu i KPIs

### Performance Metrics

```python
class FlowMetrics:
    """Track flow performance and health"""
    
    def __init__(self):
        self.start_time = time.time()
        self.stage_durations = {}
        self.retry_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.memory_usage = []
        self.cpu_usage = []
    
    def calculate_kpis(self) -> Dict[str, Any]:
        """Calculate key performance indicators"""
        total_duration = time.time() - self.start_time
        
        return {
            "total_execution_time": total_duration,
            "average_stage_duration": np.mean(list(self.stage_durations.values())),
            "total_retries": sum(self.retry_counts.values()),
            "error_rate": sum(self.error_counts.values()) / len(self.stage_durations),
            "stages_completed": len(self.stage_durations),
            "max_memory_usage": max(self.memory_usage) if self.memory_usage else 0,
            "avg_cpu_usage": np.mean(self.cpu_usage) if self.cpu_usage else 0,
            "completion_rate": self._calculate_completion_rate(),
            "quality_score": self._calculate_quality_score()
        }
```

### Success Criteria

| Metric | Target | Critical |
|--------|--------|----------|
| **Execution Time** | < 5 minutes | < 10 minutes |
| **CPU Usage** | < 30% | < 50% |
| **Memory Usage** | < 500MB | < 1GB |
| **Error Rate** | < 5% | < 15% |
| **Completion Rate** | > 95% | > 85% |
| **Quality Score** | > 80 | > 70 |
| **Retry Rate** | < 10% | < 25% |

---

## 🧪 Plan Testów

### 1. Unit Tests (Coverage > 80%)

```python
class TestFlowArchitecture:
    """Comprehensive test suite for new architecture"""
    
    def test_linear_flow_execution(self):
        """Test that flow executes linearly without loops"""
        flow = AIWritingFlowV2()
        execution_path = []
        
        # Mock all crew executions
        with patch.object(flow, '_execute_research_crew') as mock_research:
            mock_research.return_value = ResearchResult(...)
            
            result = flow.kickoff(test_state)
            
            # Verify linear execution
            assert "execute_research" in execution_path
            assert "execute_audience_alignment" in execution_path
            assert "execute_draft_generation" in execution_path
            # No stage should appear twice
            assert len(execution_path) == len(set(execution_path))
    
    def test_circuit_breaker_prevents_loops(self):
        """Test circuit breaker stops execution on repeated failures"""
        flow = AIWritingFlowV2()
        
        # Simulate repeated failures
        with patch.object(flow, '_execute_writer_crew') as mock_writer:
            mock_writer.side_effect = Exception("Test failure")
            
            with pytest.raises(CircuitBreakerOpenException):
                for _ in range(5):  # Should fail before 5th attempt
                    flow.execute_draft_generation()
    
    def test_stage_completion_tracking(self):
        """Test that completed stages are not re-executed"""
        flow = AIWritingFlowV2()
        flow.stage_manager.mark_stage_completed(FlowStage.RESEARCH_PHASE)
        
        with patch.object(flow, '_execute_research_crew') as mock_research:
            result = flow.execute_research()
            
            # Should skip research since it's marked complete
            mock_research.assert_not_called()
            assert result == "execute_audience_alignment"
    
    def test_retry_limits_respected(self):
        """Test that retry limits prevent infinite loops"""
        flow = AIWritingFlowV2()
        
        # Set low retry limit for testing
        flow.flow_control.max_retries["draft_generation"] = 2
        
        with patch.object(flow, '_execute_writer_crew') as mock_writer:
            mock_writer.return_value = DraftContent(...)
            
            # Simulate style failures
            with patch.object(flow, '_execute_style_crew') as mock_style:
                mock_style.return_value = StyleValidation(is_compliant=False, ...)
                
                # Should escalate after max retries
                for _ in range(3):
                    result = flow.execute_style_validation()
                
                assert result == "escalate_to_human"
```

### 2. Integration Tests

```python
class TestFlowIntegration:
    """Integration tests for complete flow scenarios"""
    
    def test_full_flow_original_content(self):
        """Test complete flow for ORIGINAL content"""
        initial_state = WritingFlowState(
            content_ownership="ORIGINAL",
            topic_title="Test Topic",
            platform="LinkedIn"
        )
        
        flow = AIWritingFlowV2()
        result = flow.kickoff(initial_state.model_dump())
        
        assert result.current_stage == "completed"
        assert "research_agent" not in result.agents_executed  # Should skip research
        assert result.final_draft is not None
        assert result.total_processing_time < 300  # 5 minutes max
    
    def test_human_feedback_integration(self):
        """Test human feedback loop without infinite cycles"""
        flow = AIWritingFlowV2()
        
        # Simulate human feedback
        with patch.object(flow.ui_bridge, 'request_human_feedback') as mock_feedback:
            mock_feedback.return_value = HumanFeedbackDecision(
                feedback_type="major",
                feedback_text="Need more technical depth"
            )
            
            result = flow.await_human_review()
            
            # Should return to draft generation, not create loop
            assert result == "execute_draft_generation"
            assert flow.flow_control.retry_count["human_feedback"] == 1
```

### 3. Load Tests

```python
class TestFlowPerformance:
    """Performance and load testing"""
    
    def test_concurrent_flow_execution(self):
        """Test multiple flows running concurrently"""
        flows = [AIWritingFlowV2() for _ in range(5)]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(flow.kickoff, test_state)
                for flow in flows
            ]
            
            results = [future.result(timeout=600) for future in futures]
            
            # All should complete successfully
            assert all(r.current_stage == "completed" for r in results)
            
            # No resource conflicts
            assert all(r.total_processing_time < 300 for r in results)
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during flow execution"""
        initial_memory = psutil.Process().memory_info().rss
        
        for i in range(10):
            flow = AIWritingFlowV2()
            flow.kickoff(test_state)
            
            current_memory = psutil.Process().memory_info().rss
            memory_growth = current_memory - initial_memory
            
            # Memory growth should be minimal
            assert memory_growth < 100 * 1024 * 1024  # 100MB max
```

---

## 🚨 Risk Mitigation

### 1. Infinite Loop Prevention

**Mechanisms:**
- **Circuit Breaker**: Automatic failure detection and prevention
- **Execution Counters**: Track method invocations
- **Stage Completion Tracking**: Prevent duplicate executions
- **Timeout Guards**: Maximum execution time limits
- **Linear Flow Design**: No routing loops

**Implementation:**
```python
class LoopPreventionSystem:
    def __init__(self):
        self.execution_counts = defaultdict(int)
        self.max_executions = {
            "execute_draft_generation": 5,
            "execute_style_validation": 3,
            "execute_quality_assessment": 3
        }
        self.start_time = time.time()
        self.max_total_time = 600  # 10 minutes
    
    def check_execution_limits(self, method_name: str):
        """Check if method execution should be allowed"""
        self.execution_counts[method_name] += 1
        
        # Check per-method limits
        if self.execution_counts[method_name] > self.max_executions.get(method_name, 10):
            raise MaxExecutionLimitExceeded(f"{method_name} exceeded limit")
        
        # Check total time limit
        if time.time() - self.start_time > self.max_total_time:
            raise TotalTimeoutExceeded("Flow exceeded maximum execution time")
```

### 2. Resource Management

**Memory Management:**
```python
class ResourceManager:
    def __init__(self):
        self.memory_threshold = 1024 * 1024 * 1024  # 1GB
        self.cpu_threshold = 80  # 80%
    
    def monitor_resources(self):
        """Monitor system resources and take action if needed"""
        memory_usage = psutil.Process().memory_info().rss
        cpu_usage = psutil.cpu_percent(interval=1)
        
        if memory_usage > self.memory_threshold:
            self._trigger_memory_cleanup()
        
        if cpu_usage > self.cpu_threshold:
            self._throttle_execution()
    
    def _trigger_memory_cleanup(self):
        """Force garbage collection and cleanup"""
        import gc
        gc.collect()
        
        # Clear large objects from state
        if hasattr(self, 'state'):
            self.state.draft_versions = self.state.draft_versions[-3:]  # Keep only last 3
```

### 3. Error Recovery

**Graceful Degradation:**
```python
class ErrorRecoverySystem:
    def __init__(self):
        self.fallback_strategies = {
            "research_failure": self._skip_research,
            "audience_failure": self._use_default_audience,
            "draft_failure": self._use_template_draft,
            "style_failure": self._bypass_style_check,
            "quality_failure": self._manual_review_required
        }
    
    def handle_stage_failure(self, stage: str, error: Exception) -> str:
        """Handle stage failure with appropriate recovery strategy"""
        logger.error(f"Stage {stage} failed: {error}")
        
        strategy = self.fallback_strategies.get(f"{stage}_failure")
        if strategy:
            return strategy(error)
        
        # Default: escalate to human
        return "escalate_to_human"
```

---

## 🔍 Metody Walidacji

### 1. Architecture Validation

**Static Analysis:**
```python
def validate_flow_architecture():
    """Static analysis of flow architecture"""
    flow_class = AIWritingFlowV2
    
    # Check for circular dependencies
    method_calls = extract_method_calls(flow_class)
    call_graph = build_call_graph(method_calls)
    
    cycles = detect_cycles(call_graph)
    assert len(cycles) == 0, f"Circular dependencies detected: {cycles}"
    
    # Check for proper @listen/@start usage
    decorators = extract_decorators(flow_class)
    assert "@router" not in decorators, "Router decorators should be removed"
    
    # Verify linear flow pattern
    flow_path = trace_execution_path(flow_class)
    assert is_linear_path(flow_path), "Flow path is not linear"
```

**Runtime Validation:**
```python
def validate_runtime_behavior():
    """Validate runtime behavior of flow"""
    flow = AIWritingFlowV2()
    
    # Monitor execution path
    execution_tracer = ExecutionTracer()
    flow.add_tracer(execution_tracer)
    
    result = flow.kickoff(test_state)
    
    # Validate no loops occurred
    execution_path = execution_tracer.get_execution_path()
    assert has_no_loops(execution_path), "Execution loops detected"
    
    # Validate resource usage
    assert execution_tracer.max_cpu_usage < 50, "CPU usage too high"
    assert execution_tracer.max_memory_usage < 1024**3, "Memory usage too high"
```

### 2. Quality Gates

**Pre-deployment Validation:**
```python
class QualityGate:
    def __init__(self):
        self.validators = [
            self.validate_no_infinite_loops,
            self.validate_resource_limits,
            self.validate_error_handling,
            self.validate_state_consistency,
            self.validate_performance_metrics
        ]
    
    def run_all_validations(self) -> bool:
        """Run all quality gates"""
        for validator in self.validators:
            if not validator():
                return False
        return True
    
    def validate_no_infinite_loops(self) -> bool:
        """Ensure no infinite loops possible"""
        # Static analysis + runtime testing
        return self._static_loop_detection() and self._runtime_loop_testing()
    
    def validate_resource_limits(self) -> bool:
        """Ensure resource usage is within limits"""
        metrics = self._run_performance_test()
        return (
            metrics.max_cpu_usage < 50 and
            metrics.max_memory_usage < 1024**3 and
            metrics.execution_time < 300
        )
```

---

## 📈 Implementation Roadmap - Atomic Task Decomposition

### Phase 1: Core Architecture (Week 1)

#### **Task 1.1**: Implement FlowControlState and stage management
**Primary Agent**: project-coder | **Review Agent**: code-reviewer | **Validation**: architecture-advisor

##### Blok 1.1.1: Create FlowStage Enum (1h)
- [ ] **Atomic Task 1.1.1.1**: Define FlowStage enum with all stages
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: `models/flow_stage.py` with complete enum
  - **Success**: All required stages defined, enum properly typed
  - **Validation**: `pytest tests/test_flow_stage.py -v`

- [ ] **Atomic Task 1.1.1.2**: Add stage transition validation
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Stage transition matrix and validation logic
  - **Success**: Invalid transitions raise exceptions
  - **Validation**: All transition tests pass

##### Blok 1.1.2: Create FlowControlState Model (1.5h)
- [ ] **Atomic Task 1.1.2.1**: Implement FlowControlState BaseModel
  - **Agent Chain**: project-coder → code-reviewer → architecture-advisor
  - **Time**: 45min
  - **Deliverable**: `models/flow_control_state.py` with Pydantic model
  - **Success**: All fields properly typed, defaults set
  - **Validation**: Model serialization/deserialization works

- [ ] **Atomic Task 1.1.2.2**: Add retry count management
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Retry tracking with max limits
  - **Success**: Retry limits enforced per operation
  - **Validation**: Retry overflow raises exception

- [ ] **Atomic Task 1.1.2.3**: Implement execution history tracking
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Timestamped execution log
  - **Success**: All stage transitions logged
  - **Validation**: History persists through flow execution

##### Blok 1.1.3: Test FlowControlState (1.5h)
- [ ] **Atomic Task 1.1.3.1**: Create unit tests for state model
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: `tests/test_flow_control_state.py`
  - **Success**: >95% coverage, all edge cases tested
  - **Validation**: `pytest --cov=models.flow_control_state --cov-report=term-missing`

- [ ] **Atomic Task 1.1.3.2**: Test state persistence and serialization
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Serialization/deserialization tests
  - **Success**: State survives JSON round-trip
  - **Validation**: All serialization tests pass

- [ ] **Atomic Task 1.1.3.3**: Performance test state operations
  - **Agent Chain**: performance-tester → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Performance benchmarks
  - **Success**: State operations <1ms each
  - **Validation**: Benchmark tests pass

#### **Task 1.2**: Create CircuitBreaker and retry mechanisms
**Primary Agent**: project-coder | **Review Agent**: code-reviewer | **Validation**: debugger

##### Blok 1.2.1: Implement Circuit Breaker Pattern (1.5h)
- [ ] **Atomic Task 1.2.1.1**: Create CircuitBreaker class
  - **Agent Chain**: project-coder → code-reviewer → debugger
  - **Time**: 45min
  - **Deliverable**: `utils/circuit_breaker.py` with full implementation
  - **Success**: CLOSED/OPEN/HALF_OPEN states working
  - **Validation**: State transitions behave correctly

- [ ] **Atomic Task 1.2.1.2**: Add failure threshold logic
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Configurable failure detection
  - **Success**: Circuit opens after N failures
  - **Validation**: Threshold tests pass

- [ ] **Atomic Task 1.2.1.3**: Implement recovery timeout
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Time-based recovery mechanism
  - **Success**: Circuit auto-recovers after timeout
  - **Validation**: Recovery timing tests pass

##### Blok 1.2.2: Create RetryManager (1h)
- [ ] **Atomic Task 1.2.2.1**: Implement RetryManager class
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: `utils/retry_manager.py`
  - **Success**: Per-operation retry tracking
  - **Validation**: Retry limits enforced

- [ ] **Atomic Task 1.2.2.2**: Add exponential backoff
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Exponential backoff calculation
  - **Success**: Delays increase exponentially with max cap
  - **Validation**: Backoff timing tests pass

- [ ] **Atomic Task 1.2.2.3**: Integrate with CircuitBreaker
  - **Agent Chain**: project-coder → code-reviewer → architecture-advisor
  - **Time**: 10min
  - **Deliverable**: Combined failure handling
  - **Success**: Circuit breaker + retry work together
  - **Validation**: Integration tests pass

##### Blok 1.2.3: Test Circuit Breaking and Retries (30min)
- [ ] **Atomic Task 1.2.3.1**: Test circuit breaker scenarios
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Comprehensive circuit breaker tests
  - **Success**: All state transitions tested
  - **Validation**: 100% coverage on circuit breaker logic

- [ ] **Atomic Task 1.2.3.2**: Test retry behavior under load
  - **Agent Chain**: performance-tester → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Load testing for retry mechanisms
  - **Success**: No infinite loops under any conditions
  - **Validation**: Stress tests pass

#### **Task 1.3**: Build StageManager and RetryManager
**Primary Agent**: project-coder | **Review Agent**: code-reviewer | **Validation**: architecture-advisor

##### Blok 1.3.1: Implement StageManager (1.5h)
- [ ] **Atomic Task 1.3.1.1**: Create StageManager class
  - **Agent Chain**: project-coder → code-reviewer → architecture-advisor
  - **Time**: 45min
  - **Deliverable**: `managers/stage_manager.py`
  - **Success**: Stage completion tracking works
  - **Validation**: Completion states persist correctly

- [ ] **Atomic Task 1.3.1.2**: Add stage result storage
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Result caching per stage
  - **Success**: Stage results accessible and typed
  - **Validation**: Result storage tests pass

- [ ] **Atomic Task 1.3.1.3**: Implement stage reset functionality
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Stage reset for retries
  - **Success**: Reset clears completion and results
  - **Validation**: Reset behavior verified

##### Blok 1.3.2: Add Execution History Tracking (1h)
- [ ] **Atomic Task 1.3.2.1**: Create execution history model
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Timestamped execution log model
  - **Success**: All events tracked with metadata
  - **Validation**: History serializes correctly

- [ ] **Atomic Task 1.3.2.2**: Add history analysis methods
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 20min
  - **Deliverable**: History query and analysis functions
  - **Success**: Can detect loops and timing patterns
  - **Validation**: Analysis methods tested

- [ ] **Atomic Task 1.3.2.3**: Implement history cleanup
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 10min
  - **Deliverable**: History size limits and cleanup
  - **Success**: Memory usage stays bounded
  - **Validation**: Cleanup tests pass

##### Blok 1.3.3: Test Stage Management (30min)
- [ ] **Atomic Task 1.3.3.1**: Test stage lifecycle
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Complete stage lifecycle tests
  - **Success**: All stage operations tested
  - **Validation**: Full lifecycle tests pass

- [ ] **Atomic Task 1.3.3.2**: Test concurrent stage access
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Thread safety tests
  - **Success**: No race conditions in stage management
  - **Validation**: Concurrent tests pass

### Phase 2: Linear Flow Implementation (Week 1-2)

#### **Task 2.1**: Rewrite flow methods without @router
**Primary Agent**: crewai-flow-specialist | **Review Agent**: code-reviewer | **Validation**: architecture-advisor

##### Blok 2.1.1: Analyze Existing Router Usage (1h)
- [ ] **Atomic Task 2.1.1.1**: Map current @router dependencies
  - **Agent Chain**: crewai-flow-specialist → architecture-advisor
  - **Time**: 30min
  - **Deliverable**: Current flow dependency graph
  - **Success**: All router usages documented
  - **Validation**: Dependency analysis complete

- [ ] **Atomic Task 2.1.1.2**: Design linear flow replacement
  - **Agent Chain**: architecture-advisor → crewai-flow-specialist
  - **Time**: 30min
  - **Deliverable**: New linear flow design
  - **Success**: No circular dependencies possible
  - **Validation**: Architecture review approved

##### Blok 2.1.2: Rewrite Initialize Flow Method (1.5h)
- [ ] **Atomic Task 2.1.2.1**: Replace @start with linear initialization
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 45min
  - **Deliverable**: New `initialize_flow()` method
  - **Success**: Proper input validation and flow setup
  - **Validation**: Initialization tests pass

- [ ] **Atomic Task 2.1.2.2**: Add flow path configuration
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Dynamic flow path determination
  - **Success**: Skip logic works based on content type
  - **Validation**: Path configuration tests pass

- [ ] **Atomic Task 2.1.2.3**: Implement early validation
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Input validation with early failure
  - **Success**: Invalid inputs fail fast
  - **Validation**: Validation tests comprehensive

##### Blok 2.1.3: Rewrite Research Method (1.5h)
- [ ] **Atomic Task 2.1.3.1**: Convert @router to @listen pattern
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 45min
  - **Deliverable**: New `execute_research()` method
  - **Success**: Linear execution, no loops
  - **Validation**: Method follows linear pattern

- [ ] **Atomic Task 2.1.3.2**: Add stage completion checks
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Skip logic for completed research
  - **Success**: Research not re-executed if complete
  - **Validation**: Completion check tests pass

- [ ] **Atomic Task 2.1.3.3**: Implement circuit breaker integration
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Circuit breaker wrapped execution
  - **Success**: Research fails safely under errors
  - **Validation**: Circuit breaker tests pass

##### Blok 2.1.4: Rewrite Audience Alignment Method (1h)
- [ ] **Atomic Task 2.1.4.1**: Convert to linear @listen pattern
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: New `execute_audience_alignment()` method
  - **Success**: Always executes, no circular calls
  - **Validation**: Method execution verified

- [ ] **Atomic Task 2.1.4.2**: Add error handling with fallback
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Graceful failure handling
  - **Success**: Audience failures don't stop flow
  - **Validation**: Error handling tests pass

- [ ] **Atomic Task 2.1.4.3**: Integrate state updates
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Proper state mutation
  - **Success**: Audience data properly stored
  - **Validation**: State update tests pass

##### Blok 2.1.5: Rewrite Draft Generation Method (1.5h)
- [ ] **Atomic Task 2.1.5.1**: Convert to linear execution
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 45min
  - **Deliverable**: New `execute_draft_generation()` method
  - **Success**: No loops, clean retry logic
  - **Validation**: Draft generation tested

- [ ] **Atomic Task 2.1.5.2**: Add human review checkpoint
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Human review decision point
  - **Success**: Review process doesn't create loops
  - **Validation**: Human review integration tested

- [ ] **Atomic Task 2.1.5.3**: Implement draft versioning
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Version tracking for drafts
  - **Success**: All draft iterations tracked
  - **Validation**: Versioning tests pass

##### Blok 2.1.6: Rewrite Human Review Method (30min)
- [ ] **Atomic Task 2.1.6.1**: Create timeout-based review
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: `await_human_review()` with timeout
  - **Success**: No infinite waiting, clear decisions
  - **Validation**: Timeout behavior verified

- [ ] **Atomic Task 2.1.6.2**: Add feedback processing logic
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Feedback type-based routing
  - **Success**: Different feedback types route correctly
  - **Validation**: Feedback routing tests pass

#### **Task 2.2**: Implement proper @listen chain
**Primary Agent**: crewai-flow-specialist | **Review Agent**: code-reviewer | **Validation**: debugger

##### Blok 2.2.1: Design Complete Listen Chain (1h)
- [ ] **Atomic Task 2.2.1.1**: Map linear execution flow
  - **Agent Chain**: architecture-advisor → crewai-flow-specialist
  - **Time**: 30min
  - **Deliverable**: Complete @listen chain diagram
  - **Success**: Clear start-to-end execution path
  - **Validation**: Flow diagram review approved

- [ ] **Atomic Task 2.2.1.2**: Define method return values
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Standardized return value patterns
  - **Success**: All methods return next step consistently
  - **Validation**: Return value tests comprehensive

- [ ] **Atomic Task 2.2.1.3**: Add conditional routing logic
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 10min
  - **Deliverable**: State-based routing decisions
  - **Success**: Routing based on state, not loops
  - **Validation**: Routing logic tested

##### Blok 2.2.2: Implement Style Validation Chain (1.5h)
- [ ] **Atomic Task 2.2.2.1**: Create execute_style_validation method
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Style validation with retry limits
  - **Success**: Limited retries, escalation path
  - **Validation**: Style validation tests pass

- [ ] **Atomic Task 2.2.2.2**: Add style retry logic
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Retry counter and max limit enforcement
  - **Success**: Style retries don't exceed limits
  - **Validation**: Retry limit tests pass

- [ ] **Atomic Task 2.2.2.3**: Implement escalation pathway
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Human escalation for style issues
  - **Success**: Clear escalation after max retries
  - **Validation**: Escalation tests verified

##### Blok 2.2.3: Implement Quality Assessment Chain (1.5h)
- [ ] **Atomic Task 2.2.3.1**: Create execute_quality_assessment method
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Final quality check with approval logic
  - **Success**: Quality gates properly enforced
  - **Validation**: Quality assessment tested

- [ ] **Atomic Task 2.2.3.2**: Add quality retry mechanism
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Quality-based retry logic
  - **Success**: Poor quality triggers appropriate action
  - **Validation**: Quality retry tests pass

- [ ] **Atomic Task 2.2.3.3**: Implement final output path
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Clean finalization logic
  - **Success**: Approved content goes to finalization
  - **Validation**: Output path verified

##### Blok 2.2.4: Create End-State Methods (1h)
- [ ] **Atomic Task 2.2.4.1**: Implement escalate_to_human method
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Human escalation endpoint
  - **Success**: Clear escalation with context
  - **Validation**: Escalation tests pass

- [ ] **Atomic Task 2.2.4.2**: Implement failed_validation method
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Validation failure endpoint
  - **Success**: Clear failure state with logging
  - **Validation**: Failure handling verified

- [ ] **Atomic Task 2.2.4.3**: Implement finalize_output method
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Final output preparation
  - **Success**: Complete state preparation and cleanup
  - **Validation**: Finalization tests pass

#### **Task 2.3**: Add execution guards and limits
**Primary Agent**: project-coder | **Review Agent**: code-reviewer | **Validation**: debugger

##### Blok 2.3.1: Implement Loop Prevention System (1.5h)
- [ ] **Atomic Task 2.3.1.1**: Create LoopPreventionSystem class
  - **Agent Chain**: project-coder → code-reviewer → debugger
  - **Time**: 45min
  - **Deliverable**: `utils/loop_prevention.py`
  - **Success**: Execution counting and limits enforced
  - **Validation**: Loop prevention tests comprehensive

- [ ] **Atomic Task 2.3.1.2**: Add method execution tracking
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Per-method execution counters
  - **Success**: All method calls tracked
  - **Validation**: Execution tracking verified

- [ ] **Atomic Task 2.3.1.3**: Implement timeout guards
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Total flow timeout enforcement
  - **Success**: Flow stops after max time
  - **Validation**: Timeout tests pass

##### Blok 2.3.2: Add Resource Monitoring (1h)
- [ ] **Atomic Task 2.3.2.1**: Create ResourceManager class
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: `utils/resource_manager.py`
  - **Success**: CPU and memory monitoring active
  - **Validation**: Resource monitoring tests pass

- [ ] **Atomic Task 2.3.2.2**: Implement resource thresholds
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Configurable resource limits
  - **Success**: Flow stops when resources exceeded
  - **Validation**: Threshold enforcement verified

- [ ] **Atomic Task 2.3.2.3**: Add cleanup mechanisms
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Memory cleanup and garbage collection
  - **Success**: Memory usage stays bounded
  - **Validation**: Cleanup effectiveness verified

##### Blok 2.3.3: Integrate Guards with Flow (30min)
- [ ] **Atomic Task 2.3.3.1**: Add guards to all flow methods
  - **Agent Chain**: crewai-flow-specialist → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Guard integration in all methods
  - **Success**: All methods protected by guards
  - **Validation**: Guard integration tested

- [ ] **Atomic Task 2.3.3.2**: Test guard effectiveness
  - **Agent Chain**: qa-test-engineer → debugger
  - **Time**: 10min
  - **Deliverable**: Guard effectiveness test suite
  - **Success**: Guards prevent all infinite loop scenarios
  - **Validation**: All guard tests pass

### Phase 3: Testing & Validation (Week 2)

#### **Task 3.1**: Create comprehensive test suite
**Primary Agent**: qa-test-engineer | **Review Agent**: code-reviewer | **Validation**: debugger

##### Blok 3.1.1: Unit Tests for Core Components (3h)
- [ ] **Atomic Task 3.1.1.1**: Test FlowControlState thoroughly
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Complete state model tests
  - **Success**: 100% coverage, all edge cases
  - **Validation**: `pytest tests/test_flow_control_state.py --cov=100%`

- [ ] **Atomic Task 3.1.1.2**: Test CircuitBreaker all scenarios
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Circuit breaker test suite
  - **Success**: All state transitions tested
  - **Validation**: Circuit breaker tests comprehensive

- [ ] **Atomic Task 3.1.1.3**: Test StageManager lifecycle
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Stage management tests
  - **Success**: All stage operations tested
  - **Validation**: Stage manager tests complete

- [ ] **Atomic Task 3.1.1.4**: Test RetryManager behavior
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Retry mechanism tests
  - **Success**: All retry scenarios covered
  - **Validation**: Retry tests comprehensive

##### Blok 3.1.2: Integration Tests for Flow (3h)
- [ ] **Atomic Task 3.1.2.1**: Test complete linear flow execution
  - **Agent Chain**: qa-test-engineer → crewai-flow-specialist → code-reviewer
  - **Time**: 1h
  - **Deliverable**: End-to-end flow tests
  - **Success**: Full flow executes without loops
  - **Validation**: E2E tests pass consistently

- [ ] **Atomic Task 3.1.2.2**: Test all error scenarios
  - **Agent Chain**: qa-test-engineer → debugger → code-reviewer
  - **Time**: 1h
  - **Deliverable**: Error scenario test suite
  - **Success**: All error paths tested
  - **Validation**: Error handling tests comprehensive

- [ ] **Atomic Task 3.1.2.3**: Test retry and escalation paths
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 1h
  - **Deliverable**: Retry and escalation tests
  - **Success**: All retry scenarios work correctly
  - **Validation**: Retry tests pass

##### Blok 3.1.3: Load and Stress Tests (2h)
- [ ] **Atomic Task 3.1.3.1**: Create concurrent execution tests
  - **Agent Chain**: performance-tester → qa-test-engineer → code-reviewer
  - **Time**: 1h
  - **Deliverable**: Concurrent flow test suite
  - **Success**: Multiple flows run simultaneously
  - **Validation**: Concurrent tests stable

- [ ] **Atomic Task 3.1.3.2**: Test resource usage under load
  - **Agent Chain**: performance-tester → debugger → code-reviewer
  - **Time**: 1h
  - **Deliverable**: Resource usage tests
  - **Success**: Resources stay within limits under load
  - **Validation**: Resource tests pass

#### **Task 3.2**: Implement performance monitoring
**Primary Agent**: project-coder | **Review Agent**: code-reviewer | **Validation**: performance-tester

##### Blok 3.2.1: Create FlowMetrics System (2h)
- [ ] **Atomic Task 3.2.1.1**: Implement FlowMetrics class
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 1h
  - **Deliverable**: `monitoring/flow_metrics.py`
  - **Success**: All KPIs tracked in real-time
  - **Validation**: Metrics collection verified

- [ ] **Atomic Task 3.2.1.2**: Add performance KPI calculations
  - **Agent Chain**: project-coder → performance-tester → code-reviewer
  - **Time**: 45min
  - **Deliverable**: KPI calculation methods
  - **Success**: All target metrics calculated correctly
  - **Validation**: KPI calculations tested

- [ ] **Atomic Task 3.2.1.3**: Implement metrics export
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Metrics export to JSON/Prometheus
  - **Success**: Metrics accessible for monitoring
  - **Validation**: Export formats verified

##### Blok 3.2.2: Add Real-time Monitoring (1.5h)
- [ ] **Atomic Task 3.2.2.1**: Create monitoring dashboard data
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Dashboard API endpoints
  - **Success**: Real-time metrics available via API
  - **Validation**: API endpoints tested

- [ ] **Atomic Task 3.2.2.2**: Implement alerting system
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 30min
  - **Deliverable**: Threshold-based alerting
  - **Success**: Alerts trigger on threshold breaches
  - **Validation**: Alert system tested

- [ ] **Atomic Task 3.2.2.3**: Add historical metrics storage
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Metrics persistence layer
  - **Success**: Historical data preserved
  - **Validation**: Storage layer verified

##### Blok 3.2.3: Test Monitoring System (30min)
- [ ] **Atomic Task 3.2.3.1**: Test metrics accuracy
  - **Agent Chain**: qa-test-engineer → performance-tester
  - **Time**: 20min
  - **Deliverable**: Metrics accuracy test suite
  - **Success**: All metrics match expected values
  - **Validation**: Accuracy tests pass

- [ ] **Atomic Task 3.2.3.2**: Test alerting reliability
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 10min
  - **Deliverable**: Alert system tests
  - **Success**: Alerts fire correctly and timely
  - **Validation**: Alert tests comprehensive

#### **Task 3.3**: Add quality gates and validation
**Primary Agent**: qa-test-engineer | **Review Agent**: code-reviewer | **Validation**: architecture-advisor

##### Blok 3.3.1: Create QualityGate System (2h)
- [ ] **Atomic Task 3.3.1.1**: Implement QualityGate class
  - **Agent Chain**: qa-test-engineer → architecture-advisor → code-reviewer
  - **Time**: 1h
  - **Deliverable**: `validation/quality_gate.py`
  - **Success**: All validation rules implemented
  - **Validation**: Quality gate tests comprehensive

- [ ] **Atomic Task 3.3.1.2**: Add static analysis validation
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Static code analysis integration
  - **Success**: Circular dependencies detected
  - **Validation**: Static analysis tests pass

- [ ] **Atomic Task 3.3.1.3**: Add runtime validation
  - **Agent Chain**: qa-test-engineer → debugger → code-reviewer
  - **Time**: 15min
  - **Deliverable**: Runtime behavior validation
  - **Success**: Loop detection during execution
  - **Validation**: Runtime validation verified

##### Blok 3.3.2: Implement Validation Rules (1.5h)
- [ ] **Atomic Task 3.3.2.1**: Create loop detection rules
  - **Agent Chain**: qa-test-engineer → debugger
  - **Time**: 45min
  - **Deliverable**: Loop detection algorithms
  - **Success**: All possible loops detected
  - **Validation**: Loop detection tests comprehensive

- [ ] **Atomic Task 3.3.2.2**: Add resource limit validation
  - **Agent Chain**: qa-test-engineer → performance-tester
  - **Time**: 30min
  - **Deliverable**: Resource usage validation rules
  - **Success**: Resource violations caught early
  - **Validation**: Resource validation tested

- [ ] **Atomic Task 3.3.2.3**: Create state consistency validation
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 15min
  - **Deliverable**: State validation rules
  - **Success**: Invalid states caught
  - **Validation**: State validation verified

##### Blok 3.3.3: Test Quality Gates (30min)
- [ ] **Atomic Task 3.3.3.1**: Test all validation rules
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 20min
  - **Deliverable**: Comprehensive validation tests
  - **Success**: All rules tested with edge cases
  - **Validation**: Validation rule tests pass

- [ ] **Atomic Task 3.3.3.2**: Test quality gate integration
  - **Agent Chain**: qa-test-engineer → architecture-advisor
  - **Time**: 10min
  - **Deliverable**: Quality gate integration tests
  - **Success**: Quality gates block bad code
  - **Validation**: Integration tests verified

### Phase 4: Integration & Deployment (Week 3)

#### **Task 4.1**: Integrate with existing Kolegium system
**Primary Agent**: project-coder | **Review Agent**: code-reviewer | **Validation**: deployment-specialist

##### Blok 4.1.1: Update Kolegium Integration (3h)
- [ ] **Atomic Task 4.1.1.1**: Update flow registration
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 1h
  - **Deliverable**: New flow class registration
  - **Success**: AIWritingFlowV2 properly registered
  - **Validation**: Registration tests pass

- [ ] **Atomic Task 4.1.1.2**: Update UI bridge integration
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 1h
  - **Deliverable**: UI bridge compatibility
  - **Success**: Human review integration works
  - **Validation**: UI integration tested

- [ ] **Atomic Task 4.1.1.3**: Update API endpoints
  - **Agent Chain**: project-coder → code-reviewer
  - **Time**: 1h
  - **Deliverable**: API compatibility updates
  - **Success**: All endpoints work with new flow
  - **Validation**: API tests comprehensive

##### Blok 4.1.2: Test System Integration (2h)
- [ ] **Atomic Task 4.1.2.1**: Test end-to-end user flows
  - **Agent Chain**: qa-test-engineer → project-coder → code-reviewer
  - **Time**: 1h
  - **Deliverable**: E2E user journey tests
  - **Success**: Complete user workflows tested
  - **Validation**: E2E tests pass

- [ ] **Atomic Task 4.1.2.2**: Test API backwards compatibility
  - **Agent Chain**: qa-test-engineer → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Backwards compatibility tests
  - **Success**: Existing API clients work
  - **Validation**: Compatibility verified

- [ ] **Atomic Task 4.1.2.3**: Test data migration
  - **Agent Chain**: qa-test-engineer → deployment-specialist
  - **Time**: 15min
  - **Deliverable**: State migration tests
  - **Success**: Old states migrate cleanly
  - **Validation**: Migration tests pass

##### Blok 4.1.3: Performance Integration Testing (1h)
- [ ] **Atomic Task 4.1.3.1**: Test integrated system performance
  - **Agent Chain**: performance-tester → qa-test-engineer
  - **Time**: 45min
  - **Deliverable**: Integrated performance tests
  - **Success**: Performance targets met
  - **Validation**: Performance benchmarks pass

- [ ] **Atomic Task 4.1.3.2**: Test resource usage in production environment
  - **Agent Chain**: performance-tester → deployment-specialist
  - **Time**: 15min
  - **Deliverable**: Production resource tests
  - **Success**: Resources within production limits
  - **Validation**: Resource tests verified

#### **Task 4.2**: Load testing and optimization
**Primary Agent**: performance-tester | **Review Agent**: code-reviewer | **Validation**: deployment-specialist

##### Blok 4.2.1: Concurrent Flow Testing (2h)
- [ ] **Atomic Task 4.2.1.1**: Test 10 concurrent flows
  - **Agent Chain**: performance-tester → debugger
  - **Time**: 1h
  - **Deliverable**: 10 concurrent flow test suite
  - **Success**: All flows complete successfully
  - **Validation**: Concurrent flow tests stable

- [ ] **Atomic Task 4.2.1.2**: Test resource contention
  - **Agent Chain**: performance-tester → debugger
  - **Time**: 45min
  - **Deliverable**: Resource contention tests
  - **Success**: No resource conflicts detected
  - **Validation**: Contention tests pass

- [ ] **Atomic Task 4.2.1.3**: Test scaling behavior
  - **Agent Chain**: performance-tester → deployment-specialist
  - **Time**: 15min
  - **Deliverable**: Scaling characteristic tests
  - **Success**: Linear scaling observed
  - **Validation**: Scaling tests verified

##### Blok 4.2.2: Performance Optimization (1.5h)
- [ ] **Atomic Task 4.2.2.1**: Profile flow execution
  - **Agent Chain**: performance-tester → project-coder
  - **Time**: 45min
  - **Deliverable**: Performance profiling results
  - **Success**: Bottlenecks identified
  - **Validation**: Profiling data analyzed

- [ ] **Atomic Task 4.2.2.2**: Optimize critical paths
  - **Agent Chain**: project-coder → performance-tester → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Optimized critical sections
  - **Success**: Performance improvements measured
  - **Validation**: Optimization verified

##### Blok 4.2.3: Stress Testing (30min)
- [ ] **Atomic Task 4.2.3.1**: Test system under heavy load
  - **Agent Chain**: performance-tester → debugger
  - **Time**: 20min
  - **Deliverable**: Heavy load test results
  - **Success**: System stable under stress
  - **Validation**: Stress tests pass

- [ ] **Atomic Task 4.2.3.2**: Test failure recovery under load
  - **Agent Chain**: performance-tester → debugger
  - **Time**: 10min
  - **Deliverable**: Failure recovery tests
  - **Success**: Graceful degradation verified
  - **Validation**: Recovery tests pass

#### **Task 4.3**: Production deployment and monitoring
**Primary Agent**: deployment-specialist | **Review Agent**: code-reviewer | **Validation**: emergency-system-controller

##### Blok 4.3.1: Deployment Preparation (2h)
- [ ] **Atomic Task 4.3.1.1**: Create deployment scripts
  - **Agent Chain**: deployment-specialist → code-reviewer
  - **Time**: 1h
  - **Deliverable**: Automated deployment scripts
  - **Success**: Zero-downtime deployment possible
  - **Validation**: Deployment scripts tested

- [ ] **Atomic Task 4.3.1.2**: Setup monitoring infrastructure
  - **Agent Chain**: deployment-specialist → code-reviewer
  - **Time**: 45min
  - **Deliverable**: Production monitoring setup
  - **Success**: All metrics visible in production
  - **Validation**: Monitoring verified

- [ ] **Atomic Task 4.3.1.3**: Create rollback procedures
  - **Agent Chain**: deployment-specialist → emergency-system-controller
  - **Time**: 15min
  - **Deliverable**: Emergency rollback scripts
  - **Success**: Fast rollback possible
  - **Validation**: Rollback procedures tested

##### Blok 4.3.2: Production Deployment (1.5h)
- [ ] **Atomic Task 4.3.2.1**: Execute staged deployment
  - **Agent Chain**: deployment-specialist → emergency-system-controller
  - **Time**: 1h
  - **Deliverable**: Production deployment
  - **Success**: New flow active in production
  - **Validation**: Deployment health checks pass

- [ ] **Atomic Task 4.3.2.2**: Verify production metrics
  - **Agent Chain**: deployment-specialist → performance-tester
  - **Time**: 30min
  - **Deliverable**: Production metrics validation
  - **Success**: All KPIs within target ranges
  - **Validation**: Production metrics green

##### Blok 4.3.3: Post-Deployment Monitoring (30min)
- [ ] **Atomic Task 4.3.3.1**: Monitor initial production load
  - **Agent Chain**: deployment-specialist → performance-tester
  - **Time**: 20min
  - **Deliverable**: Initial load monitoring
  - **Success**: System stable under real load
  - **Validation**: Load monitoring verified

- [ ] **Atomic Task 4.3.3.2**: Validate alerting system
  - **Agent Chain**: deployment-specialist → emergency-system-controller
  - **Time**: 10min
  - **Deliverable**: Alert system validation
  - **Success**: Alerts working in production
  - **Validation**: Alert system verified

---

## 📋 Success Checklist

### Technical Validation
- [ ] **No Infinite Loops**: Static analysis confirms no circular paths
- [ ] **Resource Limits**: CPU <30%, Memory <500MB, Time <5min
- [ ] **Error Recovery**: All failure scenarios have graceful handling
- [ ] **State Consistency**: State remains valid throughout execution
- [ ] **Performance**: 95% success rate, <5% retry rate

### Functional Validation
- [ ] **All Features Work**: Research, audience, draft, style, quality
- [ ] **Human-in-Loop**: Feedback integration without loops
- [ ] **Content Quality**: Generated content meets style guidelines
- [ ] **Platform Support**: Works for all target platforms
- [ ] **Monitoring**: Full observability of flow execution

### Production Readiness
- [ ] **High Availability**: 99.9% uptime target
- [ ] **Scalability**: Handles multiple concurrent flows
- [ ] **Maintainability**: Clear architecture and documentation
- [ ] **Security**: No sensitive data leaks or security issues
- [ ] **Compliance**: Meets all regulatory requirements

---

## 🎯 Conclusion

Ta nowa architektura rozwiązuje wszystkie zidentyfikowane problemy z obecnym AI Writing Flow:

1. **Eliminuje Infinite Loops**: Linear flow pattern bez circular dependencies
2. **Kontroluje Zasoby**: Circuit breakers i resource monitoring
3. **Zachowuje Funkcjonalności**: Wszystkie features działają bez loops
4. **Dodaje Observability**: Pełne monitorowanie i metryki
5. **Zapewnia Jakość**: Comprehensive testing i quality gates

Implementacja tego planu zapewni stabilny, wydajny i skalowalny system generacji treści z pełną kontrolą nad wykonaniem i zero-risk infinite loops.

**Next Steps:**
1. Review tego planu z zespołem
2. Rozpoczęcie implementacji od Phase 1

---

## 🧠 Knowledge Base Implementation Plan

### Architecture: Hybrid Approach

```
vector-wave/
├── knowledge-base/
│   ├── crewai/
│   │   ├── cache/              # Cached query responses
│   │   ├── docs/               # Offline markdown documentation
│   │   │   ├── core/           # Core concepts (flows, agents, crews)
│   │   │   ├── patterns/       # Best practices and patterns
│   │   │   ├── issues/         # Known issues and solutions
│   │   │   └── examples/       # Code examples
│   │   ├── embeddings/         # Pre-computed vector embeddings
│   │   ├── chroma_db/          # Persisted vector store
│   │   └── updater.py          # Sync and update script
│   └── config.yaml             # Configuration
```

### Components

1. **Offline Markdown Store** 
   - Git-versioned documentation
   - Structured for easy navigation
   - Full-text searchable

2. **Chroma Vector Store**
   - Semantic search capabilities
   - Pre-computed embeddings
   - Fast similarity search

3. **Redis/In-Memory Cache**
   - Frequently asked queries
   - Performance optimization
   - TTL-based invalidation

4. **Web API Fallback**
   - Always up-to-date information
   - Direct docs.crewai.com access
   - GitHub issues integration

### 📋 Atomic Tasks with Agent Chains

#### Phase 1: Knowledge Base Infrastructure (Day 1-2)

**Agent Chain**: project-architect → project-coder → qa-test-engineer

**Task 1.1: Design KB Architecture** (2h)
- Agent: project-architect
- Deliverables: Detailed architecture diagram, API design
- Success Metrics:
  - Query latency <100ms (cached)
  - Query latency <500ms (uncached)
  - 99% availability

**Task 1.2: Setup Vector Store** (3h)
- Agent: project-coder
- Actions:
  ```bash
  pip install chromadb langchain openai tiktoken
  mkdir -p knowledge-base/crewai/{cache,docs,embeddings,chroma_db}
  ```
- Success Metrics:
  - Chroma DB initialized
  - Test embeddings created
  - Basic CRUD operations working

**Task 1.3: Implement Query Engine** (4h)
- Agent: project-coder
- Components:
  ```python
  class CrewAIKnowledgeBase:
      def __init__(self):
          self.cache = CacheLayer()
          self.vector_store = ChromaVectorStore()
          self.markdown_store = MarkdownStore()
          self.web_fallback = WebAPIFallback()
      
      async def query(self, question: str):
          # Multi-layer query resolution
  ```
- Success Metrics:
  - 4-layer fallback working
  - <200ms average response time
  - 95% query success rate

**Task 1.4: Create Update Mechanism** (2h)
- Agent: project-coder
- Features:
  - Weekly sync cron job
  - Incremental updates
  - Diff detection
- Success Metrics:
  - Full sync <5 minutes
  - Incremental sync <30 seconds
  - Zero data loss

#### Phase 2: Content Population (Day 2-3)

**Agent Chain**: crewai-flow-specialist → documentation-keeper → qa-test-engineer

**Task 2.1: Download & Structure Docs** (3h)
- Agent: crewai-flow-specialist
- Actions:
  - Scrape all CrewAI documentation
  - Organize by topic
  - Create navigation index
- Success Metrics:
  - 100% documentation coverage
  - Proper categorization
  - Valid markdown format

**Task 2.2: Extract Known Issues** (2h)
- Agent: crewai-flow-specialist
- Sources:
  - GitHub issues (especially #1579 - router loops)
  - Stack Overflow questions
  - Discord community FAQs
- Success Metrics:
  - Top 50 issues documented
  - Solutions provided
  - Categorized by severity

**Task 2.3: Create Embeddings** (2h)
- Agent: project-coder
- Process:
  - Chunk documents (max 1000 tokens)
  - Generate embeddings
  - Store in Chroma
- Success Metrics:
  - All docs embedded
  - <5s query time
  - 90% semantic accuracy

#### Phase 3: Integration with Flow (Day 3-4)

**Agent Chain**: crewai-flow-specialist → project-coder → qa-test-engineer

**Task 3.1: Create KB Tools** (3h)
- Agent: project-coder
- Tools:
  ```python
  @tool("query_crewai_knowledge")
  def query_knowledge(query: str) -> str:
      """Query CrewAI knowledge base"""
      
  @tool("debug_flow_issue")
  def debug_issue(error: str) -> str:
      """Get debugging help for flow issues"""
  ```
- Success Metrics:
  - Tools integrated with crews
  - <500ms response time
  - Helpful responses

**Task 3.2: Integrate with AI Writing Flow** (4h)
- Agent: project-coder
- Integration points:
  - Error handling lookups
  - Best practice validation
  - Pattern recommendations
- Success Metrics:
  - Automatic error resolution
  - Reduced debugging time by 50%
  - Zero false positives

### 🎯 Validation Methods

#### 1. Query Accuracy Testing
```python
# Test suite with ground truth
test_cases = [
    {
        "query": "How to fix @router infinite loops?",
        "expected": "Use @listen with state checks instead"
    },
    {
        "query": "CrewAI flow best practices",
        "expected": ["Linear flow", "State guards", "No circular deps"]
    }
]

accuracy = run_accuracy_tests(kb, test_cases)
assert accuracy > 0.9  # 90% accuracy required
```

#### 2. Performance Benchmarking
```python
# Latency requirements
benchmarks = {
    "cached_query": 10,      # ms
    "vector_search": 200,    # ms
    "markdown_grep": 500,    # ms
    "web_fallback": 2000     # ms
}

results = run_performance_tests(kb, n=1000)
assert all(results[k] < v for k, v in benchmarks.items())
```

#### 3. Coverage Validation
```bash
# Ensure all docs are indexed
coverage_report = validate_coverage()
assert coverage_report['official_docs'] == 100
assert coverage_report['github_issues'] >= 50
assert coverage_report['examples'] >= 20
```

### 📊 Success Metrics

1. **Knowledge Base Metrics**
   - Query success rate: >95%
   - Average response time: <200ms
   - Documentation coverage: 100%
   - Update frequency: Weekly
   - Cache hit rate: >70%

2. **Integration Metrics**
   - Flow debugging time: -50%
   - Error resolution rate: >80%
   - False positive rate: <5%
   - User satisfaction: >4.5/5

3. **Operational Metrics**
   - Uptime: 99.9%
   - Storage used: <1GB
   - Memory usage: <500MB
   - CPU usage: <10%

### 🚀 Implementation Timeline

**Week 1 Enhanced:**
- Day 1: KB infrastructure setup
- Day 2: Content population
- Day 3: KB integration with flow
- Day 4: Linear flow implementation
- Day 5: Testing & optimization

**Week 2:**
- Comprehensive testing with KB
- Performance optimization
- Documentation

**Week 3:**
- Production deployment
- Monitoring setup
- Training & handover
3. Continuous testing podczas development
4. Staged rollout z monitoring

---

*Plan stworzony: 2025-01-30*  
*Estimated Implementation Time: 3 weeks*  
*Risk Level: Low (proven patterns)*