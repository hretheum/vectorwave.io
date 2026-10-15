# 🚀 POC Kickoff Guide - Vibe Coding Evaluation

## Welcome!

Thank you for participating in our Vibe Coding POC. This experiment will help us determine whether conversational AI coding delivers measurable value beyond traditional assisted coding tools.

**Your participation is:**
- Voluntary
- Anonymous in results
- Not linked to performance reviews
- Valuable for our team's tooling decisions

---

## What We're Testing

**Hypothesis**: Conversational AI coding (Claude, ChatGPT) provides ≥15% time improvement over assisted coding (Copilot, Cursor) while maintaining or improving code quality.

**Your Role**: Complete 2 development tasks, one with each approach, helping us gather real-world data.

---

## Schedule & Time Commitment

### Today: Kickoff (30 minutes)
- Overview of methodology
- Tool setup verification
- Task assignment
- Q&A

### This Week: Task Execution (3 hours)
- **Task A**: 90 minutes + 15 min survey
- **Task B**: 90 minutes + 15 min survey
- Complete at your convenience

### Next Week: Review (Optional, 1 hour)
- Architecture Jam session
- Share experiences
- Review findings

**Total time**: 4-5 hours over 2 weeks

---

## Your Assigned Tasks

**Participant ID**: _____

### Task 1: _______________
**Tool**: _______________
**Scheduled**: _______________

### Task 2: _______________
**Tool**: _______________
**Scheduled**: _______________

---

## Tool Setup Instructions

### For Assisted Coding Tasks

#### GitHub Copilot
1. Ensure Copilot is enabled in your IDE
2. Verify autocomplete is working
3. **IMPORTANT**: Disable chat features for this task
4. Record version: `GitHub Copilot vX.X.X`

#### Cursor
1. Open Cursor IDE
2. Enable autocomplete
3. **IMPORTANT**: Disable AI chat for this task
4. Set to single-line completions only
5. Record version: `Cursor vX.X.X`

#### Windsurf
1. Launch Windsurf Cascade
2. Use default configuration
3. **IMPORTANT**: Disable dialog features
4. Record version: `Windsurf vX.X.X`

### For Vibe Coding Tasks

#### Claude (Recommended)
1. Open claude.ai
2. Create new project: "POC Task [A/B/C]"
3. Upload provided codebase files
4. Use this system prompt:
```
You are an expert software developer helping me complete a coding task.
We're working on a FastAPI microservices application.
Please help me implement the requirements step by step.
Ask clarifying questions when needed.
Provide complete, production-ready code.
```

#### ChatGPT
1. Open chat.openai.com
2. Start new chat
3. Upload codebase context
4. No custom instructions

#### Gemini
1. Open gemini.google.com
2. Enable code execution if needed
3. Upload context files

---

## Environment Setup

### Prerequisites
- Docker Desktop running
- Python 3.11+ installed
- Git configured
- PostgreSQL client (optional)

### Quick Start
```bash
# Clone the POC repository
git clone [repo-url]
cd vibe-coding-poc-2025/environment

# Start services
docker-compose up -d

# Verify services
curl http://localhost:8001/health  # Recipe service
curl http://localhost:8004/health  # Agent service
curl http://localhost:8080/health  # API Gateway

# View traces (optional)
open http://localhost:16686  # Jaeger UI
```

---

## Task Execution Process

### Before You Start
1. **Record start time**
2. **Confirm task understanding** (read acceptance criteria)
3. **Open only assigned tool** (no mixing!)
4. **No external resources** beyond assigned tool

### During the Task
1. **Work naturally** - don't try to game the system
2. **Complete acceptance criteria** in order
3. **Write tests** as you normally would
4. **Document in ADR** using provided template
5. **Commit regularly** with meaningful messages

### After Completion
1. **Record end time**
2. **Run tests** and record coverage
3. **Complete survey** immediately (while fresh)
4. **Submit code** via PR to your branch

---

## Important Rules

### DO ✅
- Use your assigned tool exclusively
- Work at your normal pace
- Write production-quality code
- Ask tool for help as needed
- Take breaks if needed (pause timer)

### DON'T ❌
- Use multiple AI tools together
- Look up solutions on StackOverflow
- Copy code from previous projects
- Collaborate with others
- Optimize for speed over quality

---

## Data We're Collecting

### Quantitative
- Task completion time
- Test coverage percentage
- Code review scores
- Cyclomatic complexity
- Number of edge cases handled

### Qualitative
- Your confidence level
- Tool helpfulness rating
- Cognitive load assessment
- Would you use this in production?

**Privacy**: All data is anonymized. We only report aggregate results.

---

## Support & Questions

### During Tasks
If you encounter blockers:
1. Note the issue in your survey
2. Make reasonable assumptions
3. Continue if possible
4. Contact support only for environment issues

### Slack Channel
`#vibe-coding-poc`

### Technical Issues
- Environment problems: [contact]
- Tool access issues: [contact]
- Task clarification: Make your best judgment

---

## Deliverables Checklist

For each task, submit:
- [ ] Completed code (PR to your branch)
- [ ] All tests passing
- [ ] Test coverage report
- [ ] Architecture Decision Record
- [ ] Post-task survey
- [ ] Time tracking (start/end)

---

## What Happens Next?

### Week 2
- Code review by blind reviewers
- Aggregate data analysis
- Team discussion session

### Results
- Shared with all participants
- Aggregate only (no individual data)
- Decision on tool adoption
- Methodology published for reuse

---

## Tips for Success

1. **Read acceptance criteria carefully** - they define "done"
2. **Use the ADR template** - it's part of evaluation
3. **Don't rush** - quality matters more than speed
4. **Be honest in surveys** - your experience matters
5. **Trust the tool** - let it help you naturally

---

## Remember

This POC is about finding what works best for our team. There's no "right" answer - we're learning together.

Your honest participation helps us make better tooling decisions that affect everyone's daily work.

**Thank you for contributing to this important evaluation!**

---

*Questions? Reach out in #vibe-coding-poc or attend office hours.*