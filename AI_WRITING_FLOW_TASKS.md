# Zadania atomowe - AI Writing Flow

## Blok 0: Przygotowanie struktury projektu

- [ ] Stwórz podstawową strukturę CrewAI Flow w `ai_writing_flow/src/ai_writing_flow/`
- [ ] Skonfiguruj pyproject.toml z zależnościami
- [ ] Stwórz pliki konfiguracyjne agents.yaml i tasks.yaml
- [ ] Zdefiniuj WritingFlowState w models.py
- [ ] Skonfiguruj main.py z podstawowym flow

## Blok 1: Implementacja agentów (część 1)

- [ ] Research Agent - deep content research ze źródłami
- [ ] Audience Mapper - mapowanie do 4 person
- [ ] Content Writer - generowanie draftu

## Blok 2: Implementacja agentów (część 2)

- [ ] Style Validator - walidacja zgodności ze styleguide
- [ ] Quality Controller - końcowa kontrola jakości
- [ ] Human Feedback Handler - obsługa feedbacku użytkownika

## Blok 3: Implementacja flow z routingiem

- [ ] Start node: odbieranie danych z Kolegium
- [ ] Router: ORIGINAL vs EXTERNAL content
- [ ] Draft Generation z output do UI
- [ ] Human-in-the-Loop decision point
- [ ] Conditional routing po human feedback

## Blok 4: Integracja ze styleguide

- [ ] Wczytywanie reguł styleguide do kontekstu
- [ ] Implementacja blacklist checker
- [ ] Forbidden phrases validator
- [ ] Audience scoring system

## Blok 5: Integracja z UI

- [ ] Endpoint do uruchamiania flow
- [ ] Websocket/SSE dla real-time updates
- [ ] Draft preview w ChatPanel
- [ ] Human feedback buttons
- [ ] Progress tracking

## Blok 6: Testy i walidacja

- [ ] Unit testy dla każdego agenta
- [ ] Integration test całego flow
- [ ] Test conditional routing
- [ ] Test human feedback paths
- [ ] End-to-end test z UI