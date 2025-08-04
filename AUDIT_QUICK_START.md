# 🚀 Vector Wave Audit - Quick Start Guide

**Fast-track guide for running on-demand audits**

## 📋 TL;DR - Essential Commands

```bash
# 1. Quick setup (30 seconds)
pip install requests psutil docker safety bandit
mkdir -p audit/reports/{daily,weekly,monthly,quarterly,continuous}

# 2. Essential audit (15-20 minutes)
python audit/scripts/health_check.py          # 2 min
python audit/scripts/security_audit.py        # 10 min  
python audit/scripts/performance_audit.py     # 5 min

# 3. Check results
ls -la audit/reports/*/*.json
```

---

## 🎯 Audit Options

### Option 1: Essential Audit (Recommended First Run)
**Time**: 15-20 minutes  
**Purpose**: Critical issues detection + baseline establishment

```bash
# Dependencies
pip install requests psutil docker safety bandit

# Core audits
python audit/scripts/health_check.py          # System availability
python audit/scripts/security_audit.py        # Critical vulnerabilities
python audit/scripts/performance_audit.py     # Resource utilization
```

**What it checks**:
- ✅ Service health and response times
- 🔒 Security vulnerabilities in dependencies
- ⚡ CPU/memory usage and potential infinite loops
- 🐳 Docker configuration security

### Option 2: Comprehensive Audit (Complete Analysis)
**Time**: 45-60 minutes  
**Purpose**: Full system assessment

```bash
# All dependencies
pip install requests psutil docker safety bandit radon pytest-cov

# Full audit suite
python audit/scripts/health_check.py          # Health check
python audit/scripts/security_audit.py        # Security scan
python audit/scripts/performance_audit.py     # Performance analysis
python audit/scripts/code_quality_audit.py    # Code quality
python audit/scripts/architecture_review.py   # Architecture compliance
bash audit/scripts/business_continuity.sh     # Backup/recovery testing
```

**What it adds**:
- 📊 Code complexity and test coverage analysis
- 🏗️ Architecture patterns and dependency coupling
- 📋 Business continuity and disaster recovery validation
- 📈 Comprehensive quality scoring

### Option 3: Emergency Diagnostic (Incident Response)
**Time**: 2-5 minutes  
**Purpose**: Quick system diagnostic when issues suspected

```bash
# Minimal diagnostic
python audit/scripts/health_check.py          # 30 sec
python audit/scripts/performance_audit.py     # 3 min

# Security incident check (if needed)
python audit/scripts/security_audit.py        # 10 min
```

---

## 📊 Understanding Results

### Quality Gate Status

| Symbol | Status | Meaning | Action |
|--------|--------|---------|--------|
| ✅ | PASS | All criteria met | Continue operation |
| ⚠️ | WARN | Minor issues | Plan fixes, not urgent |
| ❌ | FAIL | Critical issues | **Immediate attention required** |

### Result Files Location

```
audit/reports/
├── continuous/     # Health check results
├── daily/          # Security & performance  
├── weekly/         # Code quality
├── monthly/        # Architecture reviews
└── quarterly/      # Business continuity
```

### Quick Results Check

```bash
# Check for any failures
grep -r "FAIL\|CRITICAL\|critical" audit/reports/

# View latest results summary
ls -t audit/reports/*/*.json | head -3

# Get audit status overview
python -c "
import json, glob
for f in glob.glob('audit/reports/*/*.json'):
    with open(f) as file:
        data = json.load(file)
        print(f'{f}: {data.get(\"status\", \"unknown\")}')
"
```

---

## 🚨 Common Issues & Solutions

### Issue: Scripts Not Found
```bash
# Ensure you're in the correct directory
cd /Users/hretheum/dev/bezrobocie/vector-wave

# Scripts should exist in audit/scripts/
ls audit/scripts/
```

### Issue: Permission Denied
```bash
# Make scripts executable
chmod +x audit/scripts/*.py
chmod +x audit/scripts/*.sh
```

### Issue: Docker Access Denied
```bash
# Check Docker daemon
docker ps

# If permission denied, add user to docker group (requires restart)
sudo usermod -aG docker $USER
```

### Issue: Python Module Not Found
```bash
# Install missing dependencies
pip install requests psutil docker safety bandit radon pytest-cov

# Or use requirements file if available
pip install -r requirements.txt
```

### Issue: Services Not Responding
```bash
# Check which services are expected to be running
cat audit/scripts/health_check.py | grep "endpoints"

# Start missing services manually
docker-compose up -d  # If using Docker Compose
```

---

## 📈 Expected First-Run Results

### Health Check
**Likely Result**: Mixed (some services UP, others DOWN)  
**Normal Findings**:
- n8n service: Usually UP (external)
- Local services: May be DOWN if not started
- Response times: Varies based on system load

**Action Items**:
- Start missing Docker services
- Check network connectivity
- Verify service configurations

### Security Audit  
**Likely Result**: WARN (5-10 findings)  
**Common Findings**:
- Dependency vulnerabilities (medium severity)
- Docker running as root user
- Missing .dockerignore files

**Critical Watch**: .env files tracked in git (immediate fix required)

### Performance Audit
**Likely Result**: PASS or WARN  
**Watch For**:
- CPU >80% (indicates CrewAI infinite loops - CRITICAL)
- Memory >85% (potential memory leaks)
- Slow response times >2s

**Baseline**: First run establishes performance baseline for future comparisons

---

## 🔄 Next Steps After First Audit

### If All PASS ✅
1. Review detailed reports for optimization opportunities
2. Consider setting up automated cykliczne audyts
3. Document baseline metrics for future comparison

### If WARN Found ⚠️
1. Prioritize fixing high-severity security issues
2. Address performance bottlenecks >70% utilization
3. Plan architecture improvements for next iteration

### If FAIL Found ❌
1. **STOP** - Address critical issues immediately
2. Focus on security vulnerabilities first
3. Fix infinite loops or system instability
4. Re-run audit after fixes

---

## 🎯 Pro Tips

### Performance Optimization
- Run audits during low-activity periods
- Use `--json` flags where available for faster parsing
- Skip business continuity audit in development environments

### Troubleshooting
- Check `audit/reports/` for detailed error messages
- Use `python -v audit/scripts/script_name.py` for verbose output
- Ensure all git submodules are up to date

### Automation Preparation
- Document any custom configurations needed
- Test all scripts manually before setting up automation
- Create backup of current system state before major fixes

---

## 📞 Emergency Contacts

**System Down**: Run emergency diagnostic immediately
**Security Incident**: Focus on security audit + immediate containment
**Performance Issues**: Performance audit + process monitoring
**Data Issues**: Business continuity audit (if services running)

---

*For comprehensive documentation, see [VECTOR_WAVE_AUDIT_PLAN.md](./VECTOR_WAVE_AUDIT_PLAN.md)*

**🚀 Ready to audit? Start with Essential Audit option above!**