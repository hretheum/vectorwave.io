# Example: Troubleshooting Router Loops

This example demonstrates how to use the Knowledge Base to troubleshoot CrewAI router loop issues.

## Problem: Router Loop Detection

Router loops are a known issue in CrewAI where `@router` decorators can create infinite cycles.

### Using Troubleshooting Tools

```python
from ai_writing_flow.tools.enhanced_knowledge_tools import (
    troubleshoot_crewai,
    search_crewai_knowledge
)

# Get general troubleshooting help
router_help = troubleshoot_crewai("performance")
print(router_help)
```

**Expected Output:**
```
# 🔧 Troubleshooting: Performance and optimization issues

## 📚 Knowledge Base Results

### 1. Router Loop Problem Resolution
*Relevance: 0.94*

**Issue**: @router doesn't support loops (GitHub #1579)
**Symptoms**: CPU spikes, infinite execution, memory growth

**Solution**: Use @listen with explicit state checks instead:

```python
# DON'T DO THIS - Creates infinite loop
@router(some_method)
def route_back(self):
    return "some_method"  # Infinite cycle

# DO THIS - Use @listen with state guards
@listen(some_method)
def next_step(self):
    if self.state.needs_retry and self.state.retry_count < 3:
        self.state.retry_count += 1
        return "some_method"
    return "final_step"
```

### 2. Performance Monitoring
*Relevance: 0.87*

Monitor these indicators for router loops:
- CPU usage above 90%
- Memory growth pattern
- Log flooding
- Stuck execution states
```

## Specific Router Loop Search

```python
# Search for router loop solutions
router_solution = search_crewai_knowledge(
    "CrewAI router loop infinite cycle @router decorator solution",
    strategy="HYBRID",
    score_threshold=0.8
)

print(router_solution)
```

**Expected Response:**
```
# Knowledge Search Results
**Query:** CrewAI router loop infinite cycle @router decorator solution
**Strategy used:** HYBRID
**Response time:** 189ms

## 📚 Knowledge Base Results

### 1. Router Loop Solution Pattern
*Relevance: 0.95*

Replace @router with @listen and state management:

```python
from crewai import Flow, listen, start
from pydantic import BaseModel

class FlowState(BaseModel):
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    retry_count: int = 0
    max_retries: int = 3
    current_stage: str = "initialized"
    
class SafeFlow(Flow[FlowState]):
    @start()
    def begin(self):
        self.state.current_stage = "processing"
        return "process_data"
    
    @listen("begin")
    def process_data(self):
        try:
            # Main processing logic
            result = self.do_processing()
            if result.success:
                return "complete"
            else:
                return "handle_retry"
        except Exception:
            return "handle_error"
    
    @listen("process_data")
    def handle_retry(self):
        if self.state.retry_count < self.state.max_retries:
            self.state.retry_count += 1
            return "process_data"  # Controlled retry
        return "max_retries_exceeded"
    
    @listen("handle_retry")
    def max_retries_exceeded(self):
        # Final fallback
        return "complete"
```

### 2. Linear Flow Design Pattern
*Relevance: 0.91*

Best practice: Design flows as linear progressions:

```
@start() → @listen() → @listen() → @listen() → end
```

Avoid circular dependencies entirely.
```

## Advanced Debugging

```python
# Search for debugging techniques
debug_help = search_crewai_knowledge(
    "CrewAI flow debugging state inspection execution tracing",
    strategy="KB_FIRST",
    limit=5
)

# Get specific debugging patterns
debug_patterns = get_flow_examples("error_handling")
```

## Complete Router Loop Fix Example

```python
from crewai import Flow, listen, start
from pydantic import BaseModel, Field
import uuid
import logging

logger = logging.getLogger(__name__)

class LoopSafeState(BaseModel):
    """State with built-in loop protection"""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    completed_stages: list[str] = Field(default_factory=list)
    current_stage: str = "initialized"
    retry_count: int = 0
    max_retries: int = 3
    error_count: int = 0
    
    def mark_completed(self, stage: str):
        """Mark stage as completed"""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
            logger.info(f"Stage completed: {stage}")
    
    def can_retry(self) -> bool:
        """Check if retry is allowed"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry counter safely"""
        self.retry_count += 1
        logger.warning(f"Retry attempt {self.retry_count}/{self.max_retries}")

class LoopSafeFlow(Flow[LoopSafeState]):
    """Flow with comprehensive loop protection"""
    
    @start()
    def initialize(self):
        """Start the flow safely"""
        self.state.current_stage = "initializing"
        logger.info(f"Flow started: {self.state.execution_id}")
        return "validate_input"
    
    @listen("initialize")
    def validate_input(self):
        """Validate input data"""
        self.state.current_stage = "validating"
        
        try:
            # Validation logic here
            validation_result = self.perform_validation()
            
            if validation_result.is_valid:
                self.state.mark_completed("validation")
                return "process_main"
            else:
                return "handle_validation_error"
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return "handle_error"
    
    @listen("validate_input")
    def process_main(self):
        """Main processing logic"""
        self.state.current_stage = "processing"
        
        try:
            # Main business logic
            result = self.main_processing()
            
            if result.success:
                self.state.mark_completed("main_processing")
                return "finalize"
            elif result.retryable and self.state.can_retry():
                return "retry_processing"
            else:
                return "handle_processing_error"
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.state.error_count += 1
            return "handle_error"
    
    @listen("process_main")
    def retry_processing(self):
        """Handle retries safely"""
        if not self.state.can_retry():
            logger.error("Max retries exceeded")
            return "max_retries_exceeded"
        
        self.state.increment_retry()
        return "process_main"  # Controlled retry
    
    @listen("retry_processing", "process_main")
    def finalize(self):
        """Finalize processing"""
        self.state.current_stage = "finalizing"
        self.state.mark_completed("finalization")
        logger.info(f"Flow completed successfully: {self.state.execution_id}")
        return "complete"
    
    @listen("validate_input", "process_main", "retry_processing")
    def handle_error(self):
        """Central error handling"""
        self.state.current_stage = "error_handling"
        logger.error(f"Flow error in stage: {self.state.current_stage}")
        
        # Error recovery logic
        if self.state.error_count < 3:
            return "error_recovery"
        else:
            return "error_final"
    
    @listen("handle_error")
    def error_recovery(self):
        """Attempt error recovery"""
        # Recovery logic here
        return "validate_input"  # Restart from validation
    
    @listen("handle_error", "retry_processing")
    def error_final(self):
        """Final error state"""
        self.state.current_stage = "failed"
        logger.error(f"Flow failed: {self.state.execution_id}")
        return "complete"
    
    @listen("retry_processing")
    def max_retries_exceeded(self):
        """Handle max retries exceeded"""
        self.state.current_stage = "max_retries_exceeded"
        logger.error(f"Max retries exceeded: {self.state.execution_id}")
        return "complete"

# Usage example
def run_safe_flow():
    """Run the loop-safe flow"""
    flow = LoopSafeFlow()
    
    try:
        result = flow.kickoff()
        logger.info(f"Flow result: {result}")
        return result
    except Exception as e:
        logger.error(f"Flow execution failed: {e}")
        raise
```

## Prevention Strategies

### 1. Flow Design Checklist

```python
# Use this checklist to prevent router loops

def validate_flow_design(flow_class):
    """Validate flow design against loop patterns"""
    
    checks = {
        "has_start_decorator": False,
        "has_linear_progression": True,
        "has_state_guards": False,
        "has_termination_conditions": False,
        "uses_router_decorator": False
    }
    
    # Analysis logic would go here
    return checks

# Before implementing flows
flow_validation = validate_flow_design(MyFlow)
if flow_validation["uses_router_decorator"]:
    print("⚠️ WARNING: Flow uses @router - potential loop risk")
```

### 2. State Management Best Practices

```python
class RobustFlowState(BaseModel):
    """Template for robust flow state"""
    
    # Required fields
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Stage tracking
    current_stage: str = "initialized"
    completed_stages: list[str] = Field(default_factory=list)
    stage_history: list[dict] = Field(default_factory=list)
    
    # Loop prevention
    retry_count: int = 0
    max_retries: int = 3
    execution_time_limit: int = 300  # 5 minutes
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    
    def is_loop_detected(self) -> bool:
        """Detect potential loops in execution"""
        if len(self.stage_history) < 3:
            return False
        
        recent_stages = [h["stage"] for h in self.stage_history[-3:]]
        return len(set(recent_stages)) == 1  # Same stage repeated
    
    def add_stage_transition(self, from_stage: str, to_stage: str):
        """Track stage transitions"""
        self.stage_history.append({
            "from": from_stage,
            "to": to_stage,
            "timestamp": datetime.now(),
            "retry_count": self.retry_count
        })
```

## Monitoring and Alerting

```python
import time
from contextlib import contextmanager

@contextmanager
def flow_monitoring(flow_name: str):
    """Monitor flow execution for loops"""
    start_time = time.time()
    
    try:
        yield
    except Exception as e:
        execution_time = time.time() - start_time
        if execution_time > 300:  # 5 minutes
            logger.critical(f"Flow {flow_name} timeout - possible loop")
        raise
    finally:
        execution_time = time.time() - start_time
        logger.info(f"Flow {flow_name} executed in {execution_time:.2f}s")

# Usage
def run_monitored_flow():
    with flow_monitoring("ContentGenerationFlow"):
        flow = ContentFlow()
        return flow.kickoff()
```

## Testing for Router Loops

```python
import pytest
import threading
import time

def test_flow_no_infinite_loop():
    """Test that flow completes within reasonable time"""
    
    def run_flow():
        flow = MyFlow()
        return flow.kickoff()
    
    # Run flow in separate thread with timeout
    thread = threading.Thread(target=run_flow)
    thread.daemon = True
    thread.start()
    
    # Wait maximum 60 seconds
    thread.join(timeout=60)
    
    if thread.is_alive():
        pytest.fail("Flow did not complete within 60 seconds - possible infinite loop")

def test_state_progression():
    """Test that flow state progresses correctly"""
    
    flow = MyFlow()
    
    # Mock the flow execution to track state changes
    state_changes = []
    
    original_kickoff = flow.kickoff
    def tracked_kickoff(*args, **kwargs):
        # Track state changes during execution
        return original_kickoff(*args, **kwargs)
    
    flow.kickoff = tracked_kickoff
    
    result = flow.kickoff()
    
    # Verify state progression
    assert len(set(state_changes)) > 1, "Flow state did not progress"
    assert "complete" in state_changes, "Flow did not reach completion"
```

## Emergency Recovery

```python
def emergency_flow_recovery(flow_instance):
    """Emergency procedure for stuck flows"""
    
    try:
        # Force state reset
        if hasattr(flow_instance, 'state'):
            flow_instance.state.current_stage = "emergency_recovery"
            flow_instance.state.retry_count = 0
        
        # Log current state for debugging
        logger.critical(f"Emergency recovery initiated for {flow_instance}")
        
        # Attempt graceful shutdown
        if hasattr(flow_instance, 'shutdown'):
            flow_instance.shutdown()
        
        return True
    except Exception as e:
        logger.critical(f"Emergency recovery failed: {e}")
        return False
```

This comprehensive example shows how to use the Knowledge Base to troubleshoot and prevent router loops in CrewAI flows. The key is replacing `@router` decorators with `@listen` decorators and implementing proper state management with loop detection.