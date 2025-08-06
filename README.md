# Vector Wave - AI Content Generation Platform

AI-powered content generation platform with comprehensive automated auditing

## 🚀 Overview

Vector Wave is an advanced content generation platform that uses AI agents to automatically create, optimize, and publish content across multiple channels. The platform includes a comprehensive audit framework for continuous monitoring and quality assurance.

### 🎯 Latest Achievement: TRUE Agentic RAG in Kolegium

The Kolegium module now features **TRUE Agentic RAG** where AI agents autonomously decide what to search for in the style guide:
- **Zero hardcoded rules** - agent makes all decisions
- **3-5 autonomous queries** per content generation
- **Unique results** - same input produces different content each time
- **OpenAI Function Calling** - native integration, no regex hacks
- **180 style guide rules** loaded from markdown files

## 📦 Project Structure

| Module | Repository | Description | Status |
|--------|------------|-------------|--------|
| content | [content-library](https://github.com/hretheum/vector-wave-content) | Generated content storage and organization | 🟢 Active |
| ideas | [idea-bank](https://github.com/hretheum/vector-wave-ideas) | Content ideas and brainstorming storage | 🟡 In Development |
| kolegium | [editorial-crew](https://github.com/hretheum/vector-wave-editorial-crew) | AI Editorial System with TRUE Agentic RAG | 🟢 Active |
| linkedin | [linkedin-automation](https://github.com/hretheum/vector-wave-linkedin) 🔒 | LinkedIn post automation module | 🟡 In Development |
| n8n | [workflow-automation](https://github.com/hretheum/vector-wave-n8n) 🔒 | n8n workflow automation | 🟢 Active |
| presenton | [presentation-generator](https://github.com/hretheum/vector-wave-presenton) 🔒 | AI-powered presentation generator | 🟢 Active |

## 🛠️ Setup

### Clone with all submodules
```bash
git clone --recurse-submodules git@github.com:hretheum/vectorwave.io.git
cd vectorwave.io
```

### Update submodules
```bash
git submodule update --init --recursive
```

### Work with specific module
```bash
cd module-name
git checkout main
git pull origin main
# make changes...
git add .
git commit -m "Your changes"
git push origin main
```

### Update submodule reference in main repo
```bash
cd ..
git add module-name
git commit -m "Update module-name to latest version"
git push
```

## 🤖 Features

- **AI Agents** - Autonomous agents for content research and generation
- **Content Pipeline** - Automated workflow from idea to publication
- **Multi-Channel Publishing** - Support for various social media platforms
- **Visual Generation** - Integration with design tools
- **Analytics** - Performance tracking and optimization
- **Automated Auditing** - Comprehensive multi-repo audit framework
- **Quality Assurance** - Continuous monitoring and quality gates

## 🔍 System Auditing

Vector Wave includes a comprehensive audit framework for continuous monitoring and quality assurance across all submodules.

### Quick Start Audit (Recommended First Run)

For immediate system assessment, run these essential audits:

```bash
# 1. Install audit dependencies
pip install requests psutil docker safety bandit

# 2. Create audit directories
mkdir -p audit/reports/{daily,weekly,monthly,quarterly,continuous}

# 3. Run essential audits (15-20 minutes total)
python audit/scripts/health_check.py          # 2 min  - System health
python audit/scripts/security_audit.py        # 10 min - Security scan  
python audit/scripts/performance_audit.py     # 5 min  - Performance baseline
```

### Comprehensive One-Time Audit

For complete system analysis, run all audit types:

```bash
# Install all audit tools
pip install requests psutil docker safety bandit radon pytest-cov

# Run complete audit suite (45-60 minutes total)
python audit/scripts/health_check.py          # System health validation
python audit/scripts/security_audit.py        # Security vulnerability scan
python audit/scripts/performance_audit.py     # Performance & resource analysis
python audit/scripts/code_quality_audit.py    # Code quality & standards
python audit/scripts/architecture_review.py   # Architecture compliance
bash audit/scripts/business_continuity.sh     # Backup & recovery testing
```

### Audit Results

All audit results are stored in structured reports:

```
audit/reports/
├── continuous/     # Health check results (every 5 min when automated)
├── daily/          # Security & performance audits
├── weekly/         # Code quality reports  
├── monthly/        # Architecture reviews
└── quarterly/      # Business continuity assessments
```

### Quality Gates

Each audit type has defined quality gates:

- **Health Check**: All services UP, response time <2s
- **Security**: 0 critical issues, ≤5 high-severity issues
- **Performance**: 0 critical issues, ≤3 high-severity issues  
- **Code Quality**: Score ≥60, ≤15 complexity issues
- **Architecture**: Score ≥80, 0 critical architecture issues
- **Business Continuity**: ≥90% success rate for backup/recovery tests

### Emergency Audit

If you suspect system issues, run immediate diagnostic:

```bash
# Emergency health check (30 seconds)
python audit/scripts/health_check.py

# If performance issues suspected
python audit/scripts/performance_audit.py

# Check for security incidents  
python audit/scripts/security_audit.py
```

**📖 Audit Documentation**:
- [Quick Start Guide](./AUDIT_QUICK_START.md) - Fast-track audit execution
- [Complete Audit Plan](./VECTOR_WAVE_AUDIT_PLAN.md) - Comprehensive framework documentation

## 📚 Documentation

### Core Documentation
- [Vector Wave Audit Plan](./VECTOR_WAVE_AUDIT_PLAN.md) - Comprehensive audit framework
- [Project Context](./PROJECT_CONTEXT.md) - Current project status and roadmap
- [Tech Blog Style Guide](./tech-blog-styleguide.md)
- [5 Tech Blog Influencers Analysis](./5-tech-blog-influencers-analysis.md)

### Module Documentation
- [AI Kolegium](./kolegium/PROJECT_CONTEXT.md) - AI agents and CrewAI flows
- [Knowledge Base](./knowledge-base/KB_INTEGRATION_GUIDE.md) - Knowledge management system
- [LinkedIn Automation](./linkedin/PROJECT_CONTEXT.md) - LinkedIn publishing automation
- [n8n Workflows](./n8n/PROJECT_CONTEXT.md) - Content automation pipelines

## 🔐 License

See individual repositories for license information.
