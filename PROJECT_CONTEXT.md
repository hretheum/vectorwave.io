# PROJECT CONTEXT - Vector Wave AI Kolegium

## 🚨 AKTUALNY STAN PROJEKTU (2025-08-03)

### PROBLEM GŁÓWNY: CrewAI Flow Infinite Loops
- **Status**: ZDIAGNOZOWANY, PLAN NAPRAWY GOTOWY
- **Root Cause**: @router nie obsługuje pętli (known bug #1579)
- **Objawy**: Flood logów, CPU 97.9%, system się zawiesza
- **Plan**: Przeprojektowanie na linear flow pattern

### WYKONANE ZADANIA ✅

#### 1. Debugowanie CrewAI Tools
- Naprawiono problem z @tool decorator (Tool objects vs functions)
- Wszystkie tools przepisane na module-level functions
- Circuit breakers dodane (max 10 wywołań per tool)

#### 2. Normalizacja Pipeline
- Zaimplementowano pełną integrację normalizacji przed writing flow
- Backend sprawdza istniejące normalizacje i używa cache
- Frontend przekazuje folder name, backend rozwiązuje pełną ścieżkę

#### 3. Emergency Fixes
- Naprawiono infinite loop w monitor_flow() 
- Dodano timeout protection (5 min max)
- Emergency kill switch: /api/emergency/kill-all-flows

#### 4. Knowledge Base Implementation
- **ARCHITEKTURA**: ✅ Zaprojektowana (hybrid: Cache + Vector + Markdown + Web)
- **IMPLEMENTACJA**: ✅ 100% complete przez project-coder
- **STRUKTURA**: ✅ Wszystkie foldery, Docker, dependencies
- **TESTY**: ❌ ZABLOKOWANE - agent QA nie działa

### W TRAKCIE 🔄

#### 1. Agent QA Problem
- **PROBLEM**: System nie widzi nowego agenta qa mimo utworzenia
- **PRÓBY**: 
  - Utworzono /Users/hretheum/.claude/agents/qa.md z YAML front matter
  - Zmieniono nazwę z qa-test-engineer na qa
  - System nadal nie widzi agenta w liście available agents
- **STATUS**: ZABLOKOWANE - potrzebny restart systemu lub inna metoda

#### 2. Knowledge Base Testing
- Czeka na uruchomienie agenta QA
- Instrukcje zapisane w QA_TEST_INSTRUCTIONS.md

### DO ZROBIENIA 📋

#### 1. Przeprojektowanie AI Writing Flow (KRYTYCZNE)
- Usunąć wszystkie @router decorators
- Implementować linear flow pattern
- Dodać proper state guards
- Plan szczegółowy w: CREWAI_FLOW_ARCHITECTURE_PLAN.md

#### 2. Dokończyć Knowledge Base
- [ ] Uruchomić testy przez agenta QA
- [ ] Populować content (docs, issues, patterns)
- [ ] Integrować z AI Writing Flow
- [ ] Setup auto-sync z CrewAI docs

#### 3. Pozostałe
- [ ] Naprawić style_crew.py i quality_crew.py (module-level tools)
- [ ] Przetestować cały flow end-to-end
- [ ] Deploy z monitoring

### PLIKI KLUCZOWE 📁

1. **Plany i Dokumentacja**:
   - `/kolegium/ai_writing_flow/CREWAI_FLOW_ARCHITECTURE_PLAN.md` - Kompletny plan naprawy
   - `/kolegium/ai_writing_flow/CREWAI_FLOW_FIX_PLAN.md` - Root cause analysis
   - `/kolegium/ai_writing_flow/FLOOD_FIX.md` - Historia napraw flood logów
   - `/knowledge-base/ARCHITECTURE.md` - Architektura KB
   - `/knowledge-base/QA_TEST_INSTRUCTIONS.md` - Instrukcje testów

2. **Kod do naprawy**:
   - `/kolegium/ai_writing_flow/src/ai_writing_flow/main.py` - Główny flow z @router
   - `/kolegium/ai_writing_flow/src/ai_writing_flow/crews/*.py` - Częściowo naprawione

3. **Knowledge Base** (GOTOWE):
   - `/knowledge-base/src/` - Pełna implementacja
   - `/knowledge-base/docker/` - Docker setup
   - `/knowledge-base/tests/` - Czeka na testy

### METRYKI SUKCESU 🎯

- ❌ No infinite loops (obecnie: TAK SĄ)
- ❌ CPU <30% (obecnie: 97.9% przy loop)
- ❌ Query latency <200ms (KB gotowa, nie przetestowana)
- ✅ 100% code coverage planu
- ❌ Production ready (daleko od tego)

### NASTĘPNE KROKI 🚀

1. **NAJPILNIEJSZE**: Rozwiązać problem z agentem QA
2. Dokończyć testy Knowledge Base
3. Implementować linear flow pattern
4. Zintegrować KB z flow
5. Deploy z monitoring

### AGENT QA - INSTRUKCJA URUCHOMIENIA

```bash
# Agent jest w: /Users/hretheum/.claude/agents/qa.md
# Ma YAML front matter:
---
name: qa
description: Expert QA Test Engineer...
tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, Task
---

# PROBLEM: System nie odświeża listy agentów
# ROZWIĄZANIE: ???
```

## 🔥 FRUSTRACJE

1. Agent QA nie działa mimo poprawnej konfiguracji
2. CrewAI ma known bugs których nie da się obejść
3. System cache'uje listę agentów i nie odświeża

---
*Ostatnia aktualizacja: 2025-08-03 15:30*