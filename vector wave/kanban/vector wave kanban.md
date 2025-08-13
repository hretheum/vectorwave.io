---

kanban-plugin: board

---

## backlog

- [ ] [EPIC] VW-19 Orchestrator → Editorial integration ^EPIC-VW-19
	   - id: 19
	   - labels: EPIC
	   - Subtasks:
	 - [ ] VW-8 Orchestrator happy-path flow
	 - [ ] VW-19 Orchestrator→Editorial: sprawdzenie integracji
	   - notes:
	 - Cel: potwierdzić ścieżki Orchestrator→Editorial (health, validate, error handling)
- [ ] [EPIC] Publishing (multi-platform) ^EPIC-PUBLISHING
	   - Subtasks:
	 - [ ] VW-9 Publisher smoke (Typefully dry-run)
	 - [ ] VW-20 Publisher: dry‑run do LinkedIn adapter
	 - [ ] VW-25 Publisher: integracja z Gamma (toggle + fallback)
	   - notes:
	 - Zależności: Presenton/LinkedIn adapter; przyszły toggle Gamma
- [ ] VW-7 MIG TEST
	   - id: 7
	   - description: assign to Todo
- [ ] VW-14 E2E: start core stack i health
	   - id: 14
- [ ] VW-15 Harvester: trigger i triage-preview
	   - id: 15
- [ ] VW-17 Harvester: promote selective-triage do TM
	   - id: 17
- [ ] VW-18 Kolegium: selective checkpoints vs Editorial Service
	   - id: 18
- [ ] VW-19 Orchestrator→Editorial: sprawdzenie integracji
	   - id: 19
	   - labels: EPIC
- [ ] VW-20 Publisher: dry‑run do LinkedIn adapter
	   - id: 20
- [ ] VW-21 Topic Manager: reindex + search happy path
	   - id: 21
- [ ] VW-22 Analytics: API skeleton + /health
	   - id: 22
- [ ] VW-23 Docs: zaktualizować harvester i Gamma.app ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - id: 23
- [ ] VW-24 Gamma: MVP (health + generate)
	   - id: 24
- [ ] VW-25 Publisher: integracja z Gamma (toggle + fallback)
	   - id: 25
- [ ] VW-8 Orchestrator happy-path flow
	   - id: 8
- [ ] VW-9 Publisher smoke
	   - id: 9
	   - blocked by: 30 (Doksy: Publisher — Substack prod + plan Gamma)
- [ ] VW-10 Topic Manager vector index
	   - id: 10
	   - note: TM zaktualizowany — korzystaj z novelty-check/suggestion (brak /topics/scrape)
	   - blocked by: 29 (Doksy: Topic Manager — bez scraperów, integracje) [done]
- [ ] VW-11 Analytics placeholder API scaffolding
	   - id: 11
	   - blocked by: 31 (Doksy: Analytics Service — status i API szkic)
- [ ] VW-12 Gamma.app service skeleton
	   - id: 12
	   - blocked by: 32 (Doksy: Gamma.app — stan, plan i wymagania)


## todo

- [ ] [P0] Smoke E2E: chromadb + editorial-service + topic-manager + crewai-orchestrator up; health checks green. [owner: platform]
	   - comments:
	   - Źródła: README.md (Quick Start), PROJECT_CONTEXT.md, tests/e2e/workflow/TEST_PLAN.md; health: 8000/8040/8041
   - Subtasks:
    - [ ] Uruchom core: chromadb, editorial-service (8040), topic-manager (8041), crewai-orchestrator
    - [ ] Sprawdź /health: 8000 heartbeat, 8040/8041 200 OK
    - [ ] Minimalny run orchestratora (happy-path) zwraca treść
    - [ ] Zanotuj wynik (czas, statusy) w PROJECT_CONTEXT.md
- [ ] [P0] Harvester smoke: /harvest/trigger → triage-preview and selective-triage promote path to TM. [owner: data]
	   - comments:
	   - Źródła: harvester/README.md; ścieżka: trigger → triage-preview → selective-triage → TM /topics/suggestion
   - Subtasks:
    - [ ] Uruchom harvester (profil harvester w compose)
    - [ ] POST /harvest/trigger (limit=10)
    - [ ] GET /harvest/status (zweryfikuj promoted/promoted_ids_count)
    - [ ] Zweryfikuj ingest do TM (Idempotency-Key; brak duplikatów)
- [ ] [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
	   - comments:
	   - Źródła: kolegium/docker-compose.test.yml, kolegium/AI_WRITING_FLOW_TASKS.md, kolegium/AI_WRITING_FLOW_DESIGN.md
   - Subtasks:
    - [ ] Uruchom CI-Light tests (docker-compose.test.yml)
    - [ ] Sprawdź selektywne checkpointy vs Editorial (8040)
    - [ ] Zaprotokołuj ewentualne flaki i retry
- [ ] [P0] Orchestrator happy-path flow: research→audience→writer with selective validation calls; return content. [owner: kolegium]
	   - comments:
	   - Źródła: kolegium/publishing-orchestrator/README.md; integracja z Editorial Service (8040)
   - Subtasks:
    - [ ] Skonfiguruj minimalny temat wejściowy
    - [ ] Uruchom sekwencję research→audience→writer
    - [ ] Zweryfikuj wywołania selektywnej walidacji do Editorial
    - [ ] Zbierz i zapisz wynik (treść, czasy)
 - [ ] [P1] Publisher smoke: enqueue → minimal dry-run via Twitter adapter (Typefully; no real publish), metrics visible. [owner: publishing]
	   - comments:
	   - Źródła: publisher/README.md; metryki: /metrics; health: 8085
   - Subtasks:
    - [ ] Skonfiguruj TYPEFULLY_API_KEY (dev)
    - [ ] Uruchom publisher (profil publishing)
    - [ ] POST /publish z twitter.enabled=true (bez real publish)
    - [ ] Zweryfikuj /metrics i /health
- [ ] [P1] Topic Manager vector index: reindex + search happy path; embed fallback without OPENAI_API_KEY. [owner: platform]
	   - comments:
	   - Źródła: topic-manager/README.md; komendy: /topics/index/*, /topics/search; fallback bez OPENAI_API_KEY
   - Subtasks:
    - [ ] POST /topics/index/reindex (limit=200)
    - [ ] GET /topics/index/info (sprawdź diagnostykę)
    - [ ] GET /topics/search (2-3 zapytania testowe)
    - [ ] Test bez OPENAI_API_KEY (fallback)
- [ ] [P2] Analytics Service: API skeleton v2.0.0 — health + insights smoke (no data collection yet). [owner: analytics]
	   - comments:
	   - Źródła: kolegium/analytics-service/README.md; health + /analytics/insights/{user_id}
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
- [x] Doksy: Topic Manager — bez scraperów, integracje (VW-28) ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  - comments:
	- TM docs → topic-manager/README.md
- [x] Doksy: Analytics Service — status i API szkic (VW-29) ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Analytics docs → kolegium/analytics-service/README.md
- [x] Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Gamma plan → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
- [x] Doksy: standard README/QUICK_START template i ToC (VW-31)
- [x] Kanban: synchronizacja z PROJECT_CONTEXT (priorytety, etykiety, relacje) (VW-32) ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	- comments:
	- Synchronizacja: usunięto duplikaty kotwicy ^EPIC-VW-16, poprawiono „↳ Parent” i literówki; zgodnie z PROJECT_CONTEXT.md
- [x] Doksy: ujednolicenie README i QUICK_START (VW-35) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	- comments:
	- Wdrożenie standardów: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md; Indeks: docs/README.md; Linter: scripts/docs_lint_readme.py; Znormalizowane README: editorial-service, topic-manager, publisher, presenton, kolegium/analytics-service, kolegium/gamma-ppt-generator, kolegium
- [x] Doksy: KPI/validation framework — definicja i checklisty (VW-37) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	- comments:
	- Dokument: docs/KPI_VALIDATION_FRAMEWORK.md; Zastosowanie w README usług (sekcje KPIs i Walidacja)
- [x] Doksy: cele/metryki/walidacja w README serwisów (VW-34) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	- follows: VW-37
	- comments:
	- README zaktualizowane i zlinkowane do KPI framework; linter przechodzi na wszystkich usługach
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Artefakty: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md
- [x] PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Zmiany: PROJECT_CONTEXT.md → sekcje Normalization + SOP; Źródła: target-version/KANBAN.md, docker-compose.yml
- [x] zadanie testowe dodane przez www (VW-1)
- [x] TEST PUT (VW-2)


## Archive

- [x] 2025-08-13 Doksy: Analytics Service — status i API szkic (VW-29) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Analytics docs → kolegium/analytics-service/README.md
- [x] 2025-08-13 Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Gamma plan → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
- [x] 2025-08-13 Doksy: ujednolicenie README i QUICK_START (VW-35) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Linter: scripts/docs_lint_readme.py (wynik: wszystkie README OK); Wdrożone standardy: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md; Znormalizowane README: editorial-service, topic-manager, publisher, presenton, kolegium/analytics-service, kolegium/gamma-ppt-generator, kolegium
- [x] 2025-08-13 Doksy: KPI/validation framework — definicja i checklisty (VW-37) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Dokument: docs/KPI_VALIDATION_FRAMEWORK.md; zastosowane w README usług
- [x] 2025-08-13 Doksy: cele/metryki/walidacja w README serwisów (VW-34) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- README zaktualizowane o sekcję KPIs i Walidacja; linter OK
- [x] 2025-08-13 Doksy: standard README/QUICK_START template i ToC (VW-31) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Artefakty: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md
- [x] 2025-08-13 PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Zmiany: PROJECT_CONTEXT.md → sekcje Normalization + SOP; Źródła: target-version/KANBAN.md, docker-compose.yml
- [x] 2025-08-13 18:38 Doksy: przegląd całej dokumentacji (repo + submoduły) (VW-26) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	 	  - comments:
	 	- Inwentarz → docs/DOCS_INVENTORY.md
- [x] 2025-08-13 18:38 Doksy: plan konsolidacji dokumentacji (VW-27) ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [
- [x] 2025-08-13 18:38 Doksy: raport rozbieżności vs target-version (VW-33)
- [x] 2025-08-13 Kanban: synchronizacja z PROJECT_CONTEXT (priorytety, etykiety, relacje) (VW-32) ^EPIC-VW-16] ^EPIC-VW-16]
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