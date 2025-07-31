# Mapa Dokumentacji - AI Kolegium Redakcyjne

## 🗺️ Status obecnej dokumentacji (Stan: 2025-01-31)

### ❌ Główne problemy do rozwiązania:
1. **Sprzeczności techniczne**: Dokumenty sugerują różne podejścia (CrewAI basic vs Flows)
2. **Duplikacja treści**: CREWAI_INTEGRATION.md vs CREWAI_COMPLETE_ANALYSIS.md
3. **Przestarzałe instrukcje**: Kroki "klonuj repo" vs "crewai create"
4. **Brak integracji**: Dokumenty nie linkują do siebie logicznie
5. **Niejasna ścieżka**: Brak przewodnika dla nowego developera

## 📚 Struktura dokumentacji (cel docelowy)

### 🌟 **Dokumenty główne** (MUST READ)
1. **README.md** → Punkt wejścia, overview, quick navigation
2. **PROJECT_CONTEXT.md** → Aktualny stan projektu, tech stack, metryki
3. **QUICK_START.md** ⭐ [NOWY] → Dla nowego developera (0→produktywność w 30 min)
4. **ROADMAP.md** → Plan implementacji z atomic tasks

### 🔧 **Dokumenty techniczne** (DEEP DIVE)
5. **docs/CREWAI_COMPLETE_ANALYSIS.md** → **GŁÓWNE ŹRÓDŁO PRAWDY** o CrewAI
6. **docs/CREWAI_FLOWS_DECISION_SYSTEM.md** → Specjalistyczny guide o Flows
7. **ARCHITECTURE_RECOMMENDATIONS.md** → Decyzje architektoniczne (ADRs)
8. **IMPLEMENTATION_GUIDE.md** → Szczegółowy przewodnik implementacji
9. **DEPLOYMENT.md** → Production deployment guide

### 📋 **Dekompozycje zadań** (EXECUTION)
10. **tasks/phase-1-foundation.md** → Bloki 0-4 (Infrastructure)
11. **tasks/phase-2-core-agents.md** → Bloki 5-8 (Content + Analytics agents)
12. **tasks/phase-3-human-in-the-loop.md** → Bloki 9-12 (Editorial + Quality)
13. **tasks/phase-4-production.md** → Bloki 13-17 (Orchestration + Production)
14. **tasks/phase-5-dynamic-agents.md** → Bloki 18-21 (Dynamic agent creation)

## 🔄 Mapa przepływu czytelnika

### 👤 **Nowy developer**:
README.md → PROJECT_CONTEXT.md → **QUICK_START.md** → ROADMAP.md → phase-1-foundation.md

### 🏗️ **Architekt systemu**:
README.md → CREWAI_COMPLETE_ANALYSIS.md → ARCHITECTURE_RECOMMENDATIONS.md → IMPLEMENTATION_GUIDE.md

### ⚡ **Agent executor (/nakurwiaj)**:
ROADMAP.md → tasks/phase-X-name.md → Specific atomic tasks

### 🚀 **DevOps/Deploy**:
PROJECT_CONTEXT.md → DEPLOYMENT.md → phase-4-production.md

## 🎯 Plan reorganizacji

### Phase 1: Cleanup & Deduplikacja
- [ ] **Usuń** docs/CREWAI_INTEGRATION.md (duplikat COMPLETE_ANALYSIS)
- [ ] **Scal** podobne sekcje między dokumentami
- [ ] **Zaktualizuj** wszystkie linki wewnętrzne
- [ ] **Ujednolic** terminologię (Crews→Flows, basic setup→scaffolding)

### Phase 2: Content Updates
- [ ] **CREWAI_COMPLETE_ANALYSIS.md**: Główne źródło prawdy (wszystkie discoveries)
- [ ] **ROADMAP.md**: Uwzględnij CrewAI scaffolding w task descriptions
- [ ] **tasks/*.md**: Aktualizuj do CrewAI Flows + built-in tools
- [ ] **PROJECT_CONTEXT.md**: Sync z najnowszymi discoveries

### Phase 3: Navigation & UX
- [ ] **Stwórz QUICK_START.md**: 30-minute onboarding guide
- [ ] **Dodaj Prerequisites** do każdego dokumentu
- [ ] **Dodaj Next Steps** na końcu każdego dokumentu
- [ ] **Cross-reference links** między wszystkimi docs

### Phase 4: Validation
- [ ] **Testuj flow**: Nowy developer może uruchomić system w 30 min
- [ ] **Weryfikuj spójność**: Wszystkie dokumenty się zgadzają
- [ ] **Sprawdź completeness**: Żadnych brakujących kroków

## 📋 Checklist spójności

### ✅ **Terminologia** (wszędzie tak samo):
- ~~"Clone repository"~~ → **"crewai create kolegium-redakcyjne"**
- ~~"Basic Crews"~~ → **"CrewAI Flows for decision-making"**
- ~~"Custom tools"~~ → **"Built-in tools + custom AG-UI integration"**
- ~~"Simple orchestration"~~ → **"Knowledge Sources + 4 memory types"**

### ✅ **Tech Stack** (jednoznaczne wszędzie):
- **Framework**: CrewAI with Flows (nie basic Crews)
- **LLM**: Multi-provider (OpenAI primary, Claude fallback)
- **Memory**: PostgreSQL with 4 memory types
- **Tools**: Built-in CrewAI tools + custom AG-UI tools
- **Frontend**: React + CopilotKit + AG-UI Protocol

### ✅ **Architecture Patterns** (spójne):
- **Event-driven**: AG-UI Protocol dla real-time communication
- **Clean Architecture**: Domain-driven design
- **CQRS + Event Sourcing**: Dla audytowalności
- **Container-first**: Docker + GitHub Container Registry
- **Human-in-the-loop**: CrewAI Flows z human input support

## 🚨 Critical Issues Found

### 1. **ROADMAP.md vs CREWAI_COMPLETE_ANALYSIS.md**
- ROADMAP: Podstawowe CrewAI setup
- COMPLETE_ANALYSIS: Zaawansowane Flows + scaffolding
- **Fix**: Update ROADMAP tasks do scaffolding approach

### 2. **phase-1-foundation.md vs PROJECT_CONTEXT.md**
- Phase-1: "Implementacja Clean Architecture structure"
- PROJECT_CONTEXT: Sugeruje CrewAI scaffolding
- **Fix**: Phase-1 powinien używać `crewai create` jako foundation

### 3. **README.md vs wszystkie inne**
- README: AG-UI focus, basic agents
- Inne: Zaawansowane Flows, Knowledge Sources, Memory
- **Fix**: README jako marketing, szczegóły w CREWAI_COMPLETE_ANALYSIS

### 4. **Implementation paths**
- Różne dokumenty sugerują różne drogi implementacji
- **Fix**: Jeden kanoniczny path w QUICK_START.md

## 🎉 Rezultat reorganizacji

Po reorganizacji będziemy mieli:

1. **Jednoznaczną ścieżkę** dla każdego typu użytkownika
2. **Spójną terminologię** we wszystkich dokumentach
3. **Logiczne linkowanie** między dokumentami
4. **Aktualne instrukcje** odzwierciedlające najnowsze discoveries
5. **30-minutowy onboarding** dla nowego developera
6. **Agent-ready tasks** dla automatyzacji przez /nakurwiaj

---

**Status**: Plan utworzony  
**Next**: Rozpocznij reorganizację od QUICK_START.md i updates w ROADMAP.md  
**Owner**: Claude Code (execution), User (approval)