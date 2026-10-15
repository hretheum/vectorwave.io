# 🧪 Vibe Coding POC 2025 - Implementation Toolkit

## Real-World Evaluation of Conversational AI Coding

This toolkit implements the POC methodology for evaluating "vibe coding" (conversational AI) versus traditional assisted coding tools. Based on the industry methodology but adapted for **actual production codebases**.

---

## 🎯 What This Is

A **complete, ready-to-run POC** for testing whether conversational AI coding delivers the promised 15% improvement over traditional assisted tools.

**Not another blog post. Not theory. Actual experiments with actual code.**

## 📁 Repository Structure

```
vibe-coding-poc-2025/
├── 01-task-bank.md              # 3 concrete tasks (90 min each)
├── 02-participant-assignment.md  # Randomization matrix
├── 03-adr-template.md           # Architecture Decision Record template
├── 04-post-task-survey.md       # Experience measurement survey
├── 05-code-review-checklist.md  # Blind review scoring
├── 06-data-collection-sheet.md  # Metrics aggregation
├── 07-kickoff-guide.md          # Participant instructions
├── environment/                  # Docker environment
│   ├── docker-compose.yml       # 8-service architecture
│   └── services/                # Starting code for tasks
│       ├── recipe-service/      # Task A: Add rating system
│       └── agent-service/       # Task B: Refactor monolith
└── README.md                    # You are here
```

## 🚀 Quick Start

### 1. Setup Environment (5 minutes)
```bash
cd environment
docker-compose up -d
```

### 2. Recruit Participants (1 day)
- Need 6-8 developers
- Mix of experience levels
- 6-8 hours commitment each

### 3. Run Kickoff (30 minutes)
- Use `07-kickoff-guide.md`
- Assign tasks via `02-participant-assignment.md`
- Verify tool setups

### 4. Execute Tasks (1 week)
- Participants complete 2 tasks each
- One with assisted coding (Copilot/Cursor)
- One with vibe coding (Claude/ChatGPT)

### 5. Collect Data (ongoing)
- Use `06-data-collection-sheet.md`
- Surveys via `04-post-task-survey.md`
- Code reviews via `05-code-review-checklist.md`

### 6. Analyze Results (2 days)
- Statistical analysis
- Apply decision criteria
- Generate report

## 📊 Success Criteria

**We adopt vibe coding if:**
1. ≥15% median time improvement, AND
2. At least one additional edge case handled

**Current hypothesis**: Vibe coding excels at debugging/understanding, struggles with initial design.

## 🎮 The Three Tasks

### Task A: Onboarding Module
**Add Rating System to Recipe Service**
- Real microservice (FastAPI + PostgreSQL)
- Clear requirements (ratings 1-5)
- Tests + ADR required
- 90 minutes

### Task B: Code Refactoring  
**Extract Agent Coordination from 800-line Monolith**
- Actual messy production code
- Multiple responsibilities mixed
- Maintain functionality
- 90 minutes

### Task C: Technical Spike
**Evaluate Caching for Recipe Search**
- Performance optimization
- Redis implementation
- Benchmark & document
- 90 minutes

## 🛠️ Tools Being Tested

### Assisted Coding
- **GitHub Copilot**: Autocomplete only, no chat
- **Cursor**: Single-line suggestions
- **Windsurf**: Default config, no dialog

### Vibe Coding
- **Claude**: Full conversation, projects, artifacts
- **ChatGPT**: GPT-4/o1, code interpreter
- **Gemini**: 2.0 Flash, code execution

## 📈 Metrics Collected

### Quantitative
- Task completion time
- Test coverage %
- Code review score (120 points)
- Cyclomatic complexity
- Edge cases found

### Qualitative
- Confidence (1-5)
- Tool helpfulness (1-5)
- Cognitive load (1-5)
- Production readiness
- Would use again?

## 🔬 Why This Matters

**The Problem**: Every "vibe coding" evaluation uses toy problems. "Add field validation" isn't what we actually do.

**Our Approach**: Real production scenarios:
- Debugging 25-second response times
- Refactoring 800-line monoliths
- Optimizing O(n³) algorithms

**The Twist**: These tasks come from actual production crises where vibe coding both caused AND solved problems.

## 💡 Key Insights So Far

From pilot testing:

1. **Vibe coding shines in crisis debugging** (3 hours → 15 minutes)
2. **Fails at distributed system design** (wrong abstractions)
3. **No performance intuition** (generates beautiful, slow code)
4. **Excellent at pattern recognition** (spots anti-patterns instantly)

## 🚦 Getting Started

### For Researchers
1. Fork this repo
2. Adapt tasks to your codebase
3. Run with your team
4. Share results (please!)

### For Participants
1. Read `07-kickoff-guide.md`
2. Setup your environment
3. Complete assigned tasks
4. Fill surveys honestly

### For Skeptics
Look at `environment/services/agent-service/main.py`. That's actual production code that needs refactoring. Try it yourself with both approaches.

## 📝 Contributing

Found issues? Improvements? Better methodology?

Open an issue or PR. This is version 1.0 - let's make it better together.

## 🤝 Credits

Based on POC Methodology for Vibe Coding Beyond Assisted Coding.
Adapted with real production scenarios from Cookbook AI crisis (August 2025).

## ⚡ The Bottom Line

**Stop measuring whether AI helps write code faster.**
**Start measuring whether AI helps fix code smarter.**

Because in production, understanding failures is everything.

---

*Ready to run your own POC? Everything you need is here. No excuses.*