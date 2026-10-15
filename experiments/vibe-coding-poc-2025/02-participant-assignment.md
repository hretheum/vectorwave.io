# 🎲 Participant Assignment & Randomization

## Cross-Over Design Matrix

| Participant ID | Name | Experience | Task 1 | Tool 1 | Task 2 | Tool 2 | Order |
|---------------|------|------------|--------|--------|--------|--------|-------|
| P001 | _________ | Senior/Mid/Junior | A: Onboarding | Vibe Coding | B: Refactoring | Assisted | Random |
| P002 | _________ | Senior/Mid/Junior | B: Refactoring | Assisted | C: Spike | Vibe Coding | Random |
| P003 | _________ | Senior/Mid/Junior | C: Spike | Vibe Coding | A: Onboarding | Assisted | Random |
| P004 | _________ | Senior/Mid/Junior | A: Onboarding | Assisted | C: Spike | Vibe Coding | Random |
| P005 | _________ | Senior/Mid/Junior | B: Refactoring | Vibe Coding | A: Onboarding | Assisted | Random |
| P006 | _________ | Senior/Mid/Junior | C: Spike | Assisted | B: Refactoring | Vibe Coding | Random |

## Randomization Protocol

### Step 1: Task Assignment
```python
import random

tasks = ['A: Onboarding', 'B: Refactoring', 'C: Spike']
participants = ['P001', 'P002', 'P003', 'P004', 'P005', 'P006']

# Ensure balanced design
task_combinations = [
    ('A', 'B'), ('B', 'C'), ('C', 'A'),
    ('A', 'C'), ('B', 'A'), ('C', 'B')
]

random.shuffle(task_combinations)
```

### Step 2: Tool Assignment
- Each participant uses BOTH tools (one per task)
- Randomize which tool is used first
- Balance: 50% start with Vibe, 50% with Assisted

### Step 3: Order Randomization
- Week 1: First task (3 participants Monday, 3 Tuesday)
- Week 1: Second task (3 participants Thursday, 3 Friday)
- Allow flexibility for participant schedules

## Baseline Configuration

### Assisted Coding Tools
**GitHub Copilot**
- Version: Latest stable (document specific version on start)
- Settings: Default autocomplete enabled
- Context window: 50 lines
- Tab completion: ON
- Inline chat: OFF (baseline only)

**Cursor**
- Version: Latest stable
- Autocomplete: Enabled
- Completion depth: Single-line
- Chat features: DISABLED for baseline
- Copilot++: OFF

**Windsurf**
- Version: Cascade environment
- Default configuration
- Suggestion depth: Standard
- Context: File-only
- Dialog features: DISABLED

### Vibe Coding Tools
**Claude (Projects)**
- Model: Claude Opus 4.1
- Project context: Full codebase uploaded
- Artifacts: Enabled
- File access: Read/write via desktop commander
- System prompt: Standardized (see prompt-template.md)

**ChatGPT**
- Model: GPT-4o or o1-preview
- Custom instructions: Disabled
- Code interpreter: Enabled if needed
- Context: Full file uploads allowed

**Gemini**
- Model: Gemini 2.0 Flash
- Code execution: Enabled
- Context window: Maximum
- Google Colab integration: Optional

## Participant Preparation Checklist

### Pre-POC (per participant)
- [ ] Development environment verified
- [ ] All tools installed and configured
- [ ] Access to repository confirmed
- [ ] Randomization completed
- [ ] Schedule confirmed
- [ ] Baseline survey completed

### Day of Task
- [ ] Record exact tool versions
- [ ] Start screen recording (optional)
- [ ] Note start time
- [ ] Confirm task understanding
- [ ] No external help/documentation beyond assigned tool

## Privacy & Ethics

- All code stays in participant's local environment
- No performance data linked to individual names
- Results reported in aggregate only
- Participation is voluntary
- Can withdraw at any time
- No impact on performance reviews