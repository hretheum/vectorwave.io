# CrewAI Flow Fix Plan - AI Writing Flow

## ROOT CAUSE ANALYSIS

### 1. Misuse of @router decorator
- We're using @router for looping, but it's NOT designed for that
- Known CrewAI issue: flows stop after first router iteration
- Our flow gets stuck and CrewAI tries to restart it (causing floods)

### 2. Circular dependencies
- await_human_feedback -> route_human_feedback -> validate_style -> await_human_feedback
- This creates an infinite loop that CrewAI can't handle

### 3. State management issues
- Not properly checking if stages were already completed
- Multiple flow executions overwriting state

## IMMEDIATE FIXES NEEDED

### 1. Remove @router for loops
```python
# WRONG (current):
@router(await_human_feedback)
def route_human_feedback(self):
    return "validate_style"  # This won't loop!

# CORRECT:
@listen("await_human_feedback")
def process_feedback(self):
    # Process and return next stage explicitly
    if self.state.needs_revision:
        return "generate_draft"
    return "validate_style"
```

### 2. Implement proper flow termination
- Each path must lead to "finalize_output"
- No circular returns
- Clear exit conditions

### 3. Add state guards
```python
# Check if stage already completed
if "validate_style" in self.state.completed_stages:
    return "quality_check"
```

### 4. Simplify flow for MVP
- Remove human feedback loop for now
- Linear flow: research -> audience -> draft -> style -> quality -> finalize
- Add human-in-the-loop later when stable

## PROPOSED FLOW STRUCTURE

```
@start() receive_topic
    |
    v
@listen() conduct_research (if EXTERNAL)
    |
    v
@listen() align_audience
    |
    v
@listen() generate_draft
    |
    v
@listen() validate_style
    |
    v
@listen() quality_check
    |
    v
@listen() finalize_output
```

## IMPLEMENTATION STEPS

1. **Backup current main.py**
2. **Remove all @router decorators**
3. **Simplify to linear flow**
4. **Add proper state guards**
5. **Test with single execution**
6. **Re-add complexity gradually**

## MONITORING

- Log each stage entry/exit
- Track execution count
- Monitor state changes
- Use timeouts for safety

## SUCCESS CRITERIA

- [ ] No infinite loops
- [ ] No flood logs
- [ ] Single flow execution
- [ ] Clean state progression
- [ ] Stable CPU usage