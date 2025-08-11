# 📚 Vector Wave Documentation

## 🎯 Documentation Structure

Vector Wave maintains a clean, organized documentation ecosystem aligned with target architecture:

### **🚀 For New Developers**
- **[developer/ONBOARDING_GUIDE.md](developer/ONBOARDING_GUIDE.md)** - Complete developer onboarding
  - Target architecture overview
  - Container-first development workflow  
  - Health checks, testing, and debugging
  - Zero hardcoded rules approach

### **🏗️ For Architecture Reference**
- **[../target-version/](../target-version/)** - Single source of truth for architecture
  - Complete system architecture specifications
  - CrewAI integration patterns (Linear Flow)
  - ChromaDB schema and Editorial Service design
  - Migration roadmap with validation scripts
  - Service dependencies map: **[DEPENDENCIES_MAP.md](DEPENDENCIES_MAP.md)**

### **🔌 For Production Integration**
- **[integration/PRODUCTION_SYSTEMS.md](integration/PRODUCTION_SYSTEMS.md)** - Production system coordination
  - LinkedIn system integration (production ready)
  - Publisher system integration (85% complete)
  - Editorial Service shared validation architecture
  - Integration patterns and health monitoring

#### Smoke runner
- E2E Kolegium smoke: `scripts/run_kolegium_e2e.sh` (sprawdza zdrowie 8040/8042 i uruchamia tylko `kolegium/ai_writing_flow/tests/test_e2e_kolegium_flow.py`)

- **[integration/PORT_ALLOCATION.md](integration/PORT_ALLOCATION.md)** - Infrastructure coordination
  - Complete port allocation registry
  - Conflict resolution (Editorial Service: 8040)
  - Service discovery and health checks

### **📚 For Historical Context**
- **[historical/README.md](historical/README.md)** - Historical documentation archive
  - **project-evolution/** - Analysis documents with resolution status
  - **deprecated-approaches/** - Anti-patterns to avoid
  - Complete evolution timeline with cross-references

## 🎯 Quick Navigation

### **I want to...**

#### **Start developing immediately**
→ **[developer/ONBOARDING_GUIDE.md](developer/ONBOARDING_GUIDE.md)**

#### **Understand the target architecture**  
→ **[../target-version/VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md](../target-version/VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md)**

#### **Integrate with production systems**
→ **[integration/PRODUCTION_SYSTEMS.md](integration/PRODUCTION_SYSTEMS.md)**

#### **Understand why something was changed**
→ **[historical/project-evolution/](historical/project-evolution/)**

#### **Avoid deprecated patterns**
→ **[historical/deprecated-approaches/](historical/deprecated-approaches/)**

## 🏗️ Architecture Principles

All documentation in this ecosystem follows these principles:

### **Zero Hardcoded Rules**
- All validation through Editorial Service (port 8040)
- ChromaDB-sourced rules only
- No fallback to hardcoded patterns

### **Container-First Development**
- Everything runs in Docker containers
- Coordinated port allocation
- Health checks and monitoring built-in

### **Linear Flow Pattern**
- No @router/@listen patterns (cause infinite loops)
- Sequential agent execution (Process.sequential)
- Predictable execution and debugging

### **Single Source of Truth**
- **target-version/** for all architectural decisions
- Cross-references from supporting documentation
- Historical context preserved separately

## 📊 Documentation Health

### **Current Status**: 🟢 **EXCELLENT**

| Metric | Status | Details |
|--------|--------|---------|
| **Anti-patterns** | ✅ Zero | No hardcoded rules or @router/@listen examples |
| **Architecture Alignment** | ✅ 100% | All docs reference target-version/ |  
| **Developer Safety** | ✅ Secure | No dangerous patterns accessible |
| **Historical Preservation** | ✅ Complete | All valuable content preserved |
| **Integration Coverage** | ✅ Comprehensive | Production systems documented |

### **Success Metrics Achieved**:
- 🎯 **Zero hardcoded rule promotion** (validation passed)
- 🎯 **Zero @router/@listen examples** in active docs (validation passed)
- 🎯 **Consistent port allocation** (Editorial Service: 8040, validation passed)
- 🎯 **Target architecture references** (3+ active references, validation passed)
- 🎯 **Developer guidance clarity** (consolidated onboarding guide, validation passed)

## ⚠️ Important Guidelines

### **For Current Development**
- **ALWAYS** use target-version/ as reference
- **NEVER** follow patterns from historical/deprecated-approaches/
- **CHECK** integration/ for production system coordination

### **For Architecture Changes**
- **UPDATE** target-version/ first
- **CROSS-REFERENCE** from other documentation
- **PRESERVE** historical context in historical/

### **For New Features**
- **START** with developer/ONBOARDING_GUIDE.md
- **FOLLOW** Linear Flow patterns
- **VALIDATE** through Editorial Service
- **DOCUMENT** integration points

---

**Documentation Ecosystem Status**: 🎉 **COMPREHENSIVE & ALIGNED**  
**Last Consolidated**: 2025-08-08  
**Next Review**: Quarterly or on major architecture changes  

**For Support**: See individual documents for specific guidance areas