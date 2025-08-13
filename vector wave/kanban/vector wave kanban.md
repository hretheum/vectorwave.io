---

kanban-plugin: board

---

## backlog

- [ ] [EPIC] VW-19 Orchestrator → Editorial integration ^EPIC-VW-19
	   - id: 19
	   - labels: EPIC
	   - Subtasks:
	 - [ ] VW-19 Orchestrator→Editorial: sprawdzenie integracji (follows: Orchestrator happy-path in Todo)
	   - notes:
	 - Cel: potwierdzić ścieżki Orchestrator→Editorial (health, validate, error handling)
- [ ] [EPIC] Publishing (multi-platform) ^EPIC-PUBLISHING
	   - Subtasks:
	 - [ ] VW-9 Publisher smoke (Typefully dry-run) (moved to Todo)
	 - [ ] VW-20 Publisher: dry‑run do LinkedIn adapter
	 - [ ] VW-25 Publisher: integracja z Gamma (toggle + fallback)
	   - notes:
	 - Zależności: Presenton/LinkedIn adapter (Phase 7 planned); toggle Gamma (po VW-24)
- [ ] VW-7 MIG TEST
	   - id: 7
	   - description: assign to Todo
- [ ] VW-19 Orchestrator→Editorial: sprawdzenie integracji
	   - id: 19
	   - labels: EPIC
- [ ] VW-20 Publisher: dry‑run do LinkedIn adapter
	   - id: 20
- [ ] VW-23 Docs: zaktualizować harvester i Gamma.app ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - id: 23
- [ ] VW-24 Gamma: MVP (health + generate)
	   - id: 24
	   - comments:
	   - STATUS.md: komponent nieukończony → zostawić w Backlog; dodać Subtasks
	   - Subtasks:
	- [ ] Implement /generate i /health real mode z GAMMA_API_KEY
	- [ ] Circuit breaker i quota awareness w health
	- [ ] Demo mode smoke bez klucza
- [ ] VW-25 Publisher: integracja z Gamma (toggle + fallback)
	   - id: 25
	   - follows: VW-24
	   - comments:
	   - STATUS.md: brak integracji → dodać Subtasks
	   - Subtasks:
	- [ ] Env toggle GAMMA_ENABLED + GAMMA_URL
	- [ ] Branching Presenton/Gamma w orchestratorze publikacji
	- [ ] Fallback path + testy kontraktowe
- [ ] VW-11 Analytics placeholder API scaffolding
	   - id: 11
	   - blocked by: 31 (Doksy: Analytics Service — status i API szkic)
- [ ] VW-12 Gamma.app service skeleton
	   - id: 12
	   - blocked by: 32 (Doksy: Gamma.app — stan, plan i wymagania)

 - [ ] [P1] Orchestrator: Redis readiness for sequence (REDIS_URL + compose) [owner: kolegium]
   - comments:
   - Przygotować usługę Redis w compose i zmienne środowiskowe (`REDIS_URL`) dla Orchestratora pod sekwencje
   - follows: [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
   - blocks: [P1] Orchestrator: enable sequence endpoint (/checkpoints/sequence/start) [owner: kolegium]
   - Subtasks:
    - [ ] Dodać `redis` do docker-compose i sieć
    - [ ] Ustawić `REDIS_URL` w Orchestratorze i smoke połączenia
    - [ ] (Opcjonalnie) Rozszerzyć `/health` o `sequence_ready`

 - [ ] [P1] Orchestrator: Sequence API contract & examples [owner: kolegium]
   - comments:
   - Uzupełnić README/API_CONTRACT o minimalny payload `{content, platform}`, przykłady curl i typowe błędy
   - follows: [P1] Orchestrator: Redis readiness for sequence (REDIS_URL + compose) [owner: kolegium]
   - blocks: [P1] Orchestrator: enable sequence endpoint (/checkpoints/sequence/start) [owner: kolegium]
   - Subtasks:
    - [ ] Zaktualizować `crewai-orchestrator/API_CONTRACT.md`
    - [ ] Dodać przykłady do `crewai-orchestrator/README.md`
    - [ ] Dodać sekcję „typowe błędy i kody” (422/501)


## todo

 
- [ ] [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
	   - comments:
	   - Źródła: kolegium/docker-compose.test.yml, kolegium/AI_WRITING_FLOW_TASKS.md, kolegium/AI_WRITING_FLOW_DESIGN.md
	   - follows: [P0] Smoke E2E: chromadb + editorial-service + topic-manager + crewai-orchestrator up; health checks green. [owner: platform]
	   - Subtasks:
	- [ ] Uruchom CI-Light tests (docker-compose.test.yml) lub wykonaj smoke endpointami Orchestratora
	- [x] Sprawdź zdrowie Orchestratora (8042) i triage endpoints (/api/triage/policy, /api/triage/seed)
	- [ ] Zaprotokołuj wyniki (policy snapshot, seed result) i flaki/retry
	   - notes:
	- 2025-08-13: /api/triage/policy OK (snapshot pobrany); /api/triage/seed accepted; test suite nieodnaleziony — fallback smoke przez API
- [ ] [P0] Orchestrator happy-path flow: research→audience→writer with selective validation calls; return content. [owner: kolegium]
	   - comments:
	   - Źródła: kolegium/publishing-orchestrator/README.md; integracja z Editorial Service (8040)
	   - follows: [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
	   - Subtasks:
	 - [x] Skonfiguruj minimalny temat wejściowy (content: "Test content for happy path", platform: linkedin)
	 - [ ] Uruchom sekwencję research→audience→writer (fallback: pojedynczy checkpoint)
	 - [x] Zweryfikuj wywołania selektywnej walidacji do Editorial (rule_count>0, processing_time_ms zapisane)
	 - [x] Zbierz i zapisz wynik (treść, czasy) w PROJECT_CONTEXT.md
- [ ] [P1] Publisher smoke: enqueue → minimal dry-run via Twitter adapter (Typefully; no real publish), metrics visible. [owner: publishing]
 - [ ] [P1] Orchestrator: enable sequence endpoint (/checkpoints/sequence/start) [owner: kolegium]
   - comments:
   - Diagnoza: endpoint istnieje, wymaga `{content, platform}` i możliwej konfiguracji (Redis/flow). Wcześniej 404; create/status działają.
   - Źródła: kolegium/publishing-orchestrator/README.md, crewai-orchestrator/src/checkpoints_api.py, crewai-orchestrator/API_CONTRACT.md
   - follows: [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
   - blocks: [P0] Orchestrator happy-path flow: research→audience→writer with selective validation calls; return content. [owner: kolegium]
   - Subtasks:
    - [ ] Zweryfikuj minimalny payload `{content, platform}` i przykład w README/API_CONTRACT
    - [ ] Potwierdź wymagania środowiskowe (np. `REDIS_URL`) i ewentualnie dodać usługę Redis w compose
    - [ ] Smoke: `POST /checkpoints/sequence/start` → `flow_id` + `running`; `GET /checkpoints/sequence/status/{id}` raportuje listę checkpointów
	   - comments:
	   - Źródła: publisher/README.md; metryki: /metrics; health: 8085
	   - Subtasks:
	- [ ] Skonfiguruj TYPEFULLY_API_KEY (dev)
	- [ ] Uruchom publisher (profil publishing)
	- [ ] POST /publish z twitter.enabled=true (bez real publish)
	- [ ] Zweryfikuj /metrics i /health
 
- [ ] [P2] Analytics Service: API skeleton v2.0.0 — health + insights smoke (no data collection yet). [owner: analytics]
	   - comments:
	   - Źródła: kolegium/analytics-service/README.md; health + /analytics/insights/{user_id}
	   - follows: [P0] Orchestrator happy-path flow: research→audience→writer with selective validation calls; return content. [owner: kolegium]
	   - Subtasks:
	- [ ] Uruchom analytics-service (profil analytics)
	- [ ] GET /health (P95 < 80ms)
	- [ ] GET /analytics/insights/{user_id} (Bearer dev; sprawdź data_quality_score)
- [ ] [P2] Gamma.app service skeleton kept archived; no integration work. [owner: publishing]
	   - comments:
	   - Plan i wymagania → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
	   - Subtasks:
	- [ ] Potwierdź tryb archived (brak pracy dev w tym sprincie)
	- [ ] Opcjonalny GET /health w demo mode (jeśli uruchomiony)


## in progress



## done

**Complete**
- [x] 2025-08-13 P0 Smoke E2E: chromadb+editorial+topic-manager+orchestrator up; health OK; triage seed accepted ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - PROJECT_CONTEXT logged; health 8000/8040/8041/8042 OK; /checkpoints/sequence/start 404 (not implemented); fallback via /api/triage/seed
- [x] Kanban: synchronizacja z PROJECT_CONTEXT (priorytety, etykiety, relacje) (VW-32)
	   - follows: VW-36
	   - comments:
	 - Kontekst → PROJECT_CONTEXT.md
- [x] [EPIC] VW-16 zaktualizować całą dokumentację ^EPIC-VW-16
	   - id: 16
	   - Subtasks:
	 - [x] VW-26 Doksy: przegląd całej dokumentacji (repo + submoduły)
	 - [x] VW-27 Doksy: plan konsolidacji dokumentacji
	 - [x] VW-33 Doksy: raport rozbieżności vs target-version
	 - [x] VW-28 Doksy: Topic Manager — bez scraperów, integracje
- [x] [P0] Remove TM scraping stub and docs mentioning /topics/scrape.
- [x] Doksy: Topic Manager — bez scraperów, integracje (VW-28) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  - comments:
	- TM docs → topic-manager/README.md
- [x] Doksy: Analytics Service — status i API szkic (VW-29) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Analytics docs → kolegium/analytics-service/README.md
- [x] Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Gamma plan → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
- [x] Doksy: standard README/QUICK_START template i ToC (VW-31)
- [x] Kanban: synchronizacja z PROJECT_CONTEXT (priorytety, etykiety, relacje) (VW-32) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	- comments:
	- Synchronizacja: usunięto duplikaty kotwicy ^EPIC-VW-16, poprawiono „↳ Parent” i literówki; zgodnie z PROJECT_CONTEXT.md
- [x] Doksy: ujednolicenie README i QUICK_START (VW-35) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	- comments:
	- Wdrożenie standardów: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md; Indeks: docs/README.md; Linter: scripts/docs_lint_readme.py; Znormalizowane README: editorial-service, topic-manager, publisher, presenton, kolegium/analytics-service, kolegium/gamma-ppt-generator, kolegium
- [x] Doksy: KPI/validation framework — definicja i checklisty (VW-37) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	- comments:
	- Dokument: docs/KPI_VALIDATION_FRAMEWORK.md; Zastosowanie w README usług (sekcje KPIs i Walidacja)
- [x] Doksy: cele/metryki/walidacja w README serwisów (VW-34) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	- follows: VW-37
	- comments:
	- README zaktualizowane i zlinkowane do KPI framework; linter przechodzi na wszystkich usługach
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Artefakty: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md
- [x] PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Zmiany: PROJECT_CONTEXT.md → sekcje Normalization + SOP; Źródła: target-version/KANBAN.md, docker-compose.yml
- [x] zadanie testowe dodane przez www (VW-1)
- [x] TEST PUT (VW-2)


## Archive

- [x] 2025-08-13 VW-14 E2E: start core stack i health (duplicate of P0 Smoke E2E) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 Smoke E2E (Todo)
- [x] 2025-08-13 VW-15 Harvester: trigger i triage-preview (duplicate of Todo Harvester smoke) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 Harvester smoke (Todo)
- [x] 2025-08-13 VW-17 Harvester: promote selective-triage do TM (duplicate; part of VW-15) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; część Subtasks w Harvester smoke (Todo)
- [x] 2025-08-13 VW-18 Kolegium: selective checkpoints vs Editorial Service (duplicate of Todo CI-Light) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 CI-Light (Todo)
- [x] 2025-08-13 VW-21 Topic Manager: reindex + search happy path (duplicate of Todo TM vector index) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P1 TM vector index (Todo)
- [x] 2025-08-13 VW-22 Analytics: API skeleton + /health (duplicate of Todo Analytics v2.0.0 skeleton) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P2 Analytics skeleton (Todo)
- [x] 2025-08-13 VW-8 Orchestrator happy-path flow (duplicate of Todo Orchestrator happy-path) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 Orchestrator happy-path (Todo)
- [x] 2025-08-13 VW-10 Topic Manager vector index (duplicate of Todo TM vector index) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P1 TM vector index (Todo)
- [x] 2025-08-13 Doksy: Analytics Service — status i API szkic (VW-29) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Analytics docs → kolegium/analytics-service/README.md
- [x] 2025-08-13 Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Gamma plan → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
- [x] 2025-08-13 Doksy: ujednolicenie README i QUICK_START (VW-35) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Linter: scripts/docs_lint_readme.py (wynik: wszystkie README OK); Wdrożone standardy: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md; Znormalizowane README: editorial-service, topic-manager, publisher, presenton, kolegium/analytics-service, kolegium/gamma-ppt-generator, kolegium
- [x] 2025-08-13 Doksy: KPI/validation framework — definicja i checklisty (VW-37) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Dokument: docs/KPI_VALIDATION_FRAMEWORK.md; zastosowane w README usług
- [x] 2025-08-13 Doksy: cele/metryki/walidacja w README serwisów (VW-34) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- README zaktualizowane o sekcję KPIs i Walidacja; linter OK
- [x] 2025-08-13 Doksy: standard README/QUICK_START template i ToC (VW-31) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Artefakty: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md
- [x] 2025-08-13 PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Zmiany: PROJECT_CONTEXT.md → sekcje Normalization + SOP; Źródła: target-version/KANBAN.md, docker-compose.yml
- [x] 2025-08-13 18:38 Doksy: przegląd całej dokumentacji (repo + submoduły) (VW-26) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	 	  - comments:
	 	- Inwentarz → docs/DOCS_INVENTORY.md
- [x] 2025-08-13 18:38 Doksy: plan konsolidacji dokumentacji (VW-27) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [
- [x] 2025-08-13 18:38 Doksy: raport rozbieżności vs target-version (VW-33)
- [x] 2025-08-13 Kanban: synchronizacja z PROJECT_CONTEXT (priorytety, etykiety, relacje) (VW-32) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  - comments:
	- Synchronizacja: usunięto duplikaty kotwicy ^EPIC-VW-16, poprawiono „↳ Parent” i literówki; zgodnie z PROJECT_CONTEXT.md
	   ↳ Parent: [^EPIC-VW-16]
	 	  - comments:
	 	- Raport → docs/DOCS_DIFF_REPORT.md


## blocked





%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[false,false,false,true,true,true],"show-checkboxes":true,"move-tags":false,"move-dates":false}
```
%%