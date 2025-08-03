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
- **TESTY**: ✅ WYKONANE - agent QA stworzył 282+ testów z >80% coverage
- **BŁĘDY**: ✅ NAPRAWIONE - structlog.testing.BoundLogger → structlog.stdlib.BoundLogger

### W TRAKCIE 🔄

#### 1. Dekompozycja atomowych zadań CrewAI Flow
- **STATUS**: ✅ WYKONANE przez project-architect
- **DELIVERABLE**: CREWAI_FLOW_ATOMIC_TASKS.md
- **STRUKTURA**: 39 bloków, 4 fazy, ~100+ atomic tasks
- **SPECIAL**: Dodano krytyczną instrukcję code review co 150 linii

### DO ZROBIENIA 📋

#### 1. Przeprojektowanie AI Writing Flow (KRYTYCZNE)
- Usunąć wszystkie @router decorators
- Implementować linear flow pattern
- Dodać proper state guards
- Plan szczegółowy w: CREWAI_FLOW_ARCHITECTURE_PLAN.md

#### 2. Dokończyć Knowledge Base
- [x] Uruchomić testy przez agenta QA
- [x] Pobrać dokumentację CrewAI z GitHub (docs/en)
- [x] Populować content - używamy RAGTool zamiast własnego
- [x] Integrować z AI Writing Flow - dodano tools do research_crew
- [x] Setup auto-sync z CrewAI docs - GitHub Action + cron

#### 3. Pozostałe
- [ ] Naprawić style_crew.py i quality_crew.py (module-level tools)
- [ ] Przetestować cały flow end-to-end
- [ ] Deploy z monitoring

### PLIKI KLUCZOWE 📁

1. **Plany i Dokumentacja**:
   - `/kolegium/ai_writing_flow/CREWAI_FLOW_ARCHITECTURE_PLAN.md` - Kompletny plan naprawy
   - `/kolegium/ai_writing_flow/CREWAI_FLOW_ATOMIC_TASKS.md` - ✅ NOWE: Dekompozycja atomowych zadań
   - `/kolegium/ai_writing_flow/CREWAI_FLOW_FIX_PLAN.md` - Root cause analysis
   - `/kolegium/ai_writing_flow/FLOOD_FIX.md` - Historia napraw flood logów
   - `/knowledge-base/ARCHITECTURE.md` - Architektura KB
   - `/knowledge-base/QA_TEST_INSTRUCTIONS.md` - Instrukcje testów

2. **Kod do naprawy**:
   - `/kolegium/ai_writing_flow/src/ai_writing_flow/main.py` - Główny flow z @router
   - `/kolegium/ai_writing_flow/src/ai_writing_flow/crews/*.py` - Częściowo naprawione

3. **Knowledge Base** (✅ GOTOWE):
   - `/knowledge-base/src/` - Pełna implementacja
   - `/knowledge-base/docker/` - Docker setup
   - `/knowledge-base/tests/` - 282+ testów z >80% coverage
   - `/knowledge-base/data/crewai-docs/` - Dokumentacja CrewAI
   - `/knowledge-base/scripts/sync_crewai_docs.sh` - Auto-sync script

### METRYKI SUKCESU 🎯

- ❌ No infinite loops (obecnie: TAK SĄ)
- ❌ CPU <30% (obecnie: 97.9% przy loop)
- ✅ Query latency <200ms (KB gotowa, testy pokazują <200ms avg)
- ✅ 100% code coverage planu
- ✅ >80% test coverage dla Knowledge Base
- ❌ Production ready (KB prawie, Flow daleko)

### NASTĘPNE KROKI 🚀

1. **NAJPILNIEJSZE**: Wykonać dekompozycję atomowych zadań (`/nakurwiaj 0`)
2. Implementować linear flow pattern dla AI Writing
3. Przeprowadzić comprehensive testing
4. Zintegrować wszystkie komponenty
5. Deploy z monitoring

### TODOLIST STAN (2025-08-03 17:30)

1. ✅ Uruchomić testy Knowledge Base przez agenta QA (high)
2. ✅ Sprawdzić wyniki testów i naprawić ewentualne błędy (high)
3. ✅ Pobrać dokumentację CrewAI z GitHub repo (docs/en folder) (high)
4. ✅ Populować Knowledge Base dokumentacją CrewAI (medium)
5. ✅ Zintegrować KB z AI Writing Flow (medium)
6. ✅ Setup auto-sync z CrewAI docs (low)
7. ✅ Dekompozycja atomowych zadań przez project-architect (high)

## 🔥 FRUSTRACJE → ROZWIĄZANIA ✅

1. ~~Agent QA nie działa mimo poprawnej konfiguracji~~ → Działa! 
2. CrewAI ma known bugs których nie da się obejść → Plan linear flow gotowy
3. ~~System cache'uje listę agentów i nie odświeża~~ → Agent QA zadziałał

## 📝 NOTATKI

- **ODKRYCIE**: Dokumentacja CrewAI jest w pełni dostępna w GitHub repo
- **DECYZJA**: Zamiast tworzyć scraper, użyjemy git sparse-checkout
- **AGENT QA**: Stworzył kompletny system testów (282+ testów, >80% coverage)
- **RAGTool**: Oficjalne narzędzie CrewAI lepsze niż własna implementacja
- **ATOMIC TASKS**: 39 bloków, code review co 150 linii kodu OBOWIĄZKOWE!

---
*Ostatnia aktualizacja: 2025-08-03 17:30*