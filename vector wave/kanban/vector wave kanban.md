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
- [ ] VW-23 Docs: zaktualizować harvester i Gamma.app ^EPIC-VW-16]
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

- [ ] [P0] Stand up self-hosted Kanban (Vikunja) via Docker; expose locally; prepare backup plan. [owner: infra]
- [ ] [P0] Smoke E2E: chromadb + editorial-service + topic-manager + crewai-orchestrator up; health checks green. [owner: platform]
- [ ] [P0] Harvester smoke: /harvest/trigger → triage-preview and selective-triage promote path to TM. [owner: data]
- [ ] [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
- [ ] [P0] Orchestrator happy-path flow: research→audience→writer with selective validation calls; return content. [owner: kolegium]
- [ ] [P1] Publisher smoke: enqueue → minimal dry-run to LinkedIn adapter (no real publish), metrics visible. [owner: publishing]
- [ ] [P1] Topic Manager vector index: reindex + search happy path; embed fallback without OPENAI_API_KEY. [owner: platform]
- [ ] [P2] Analytics placeholder API scaffolding (no data collection yet). [owner: analytics]
- [ ] [P2] Gamma.app service skeleton kept archived; no integration work. [owner: publishing]


## in progress

- [ ] [EPIC] VW-16 zaktualizować całą dokumentację ^EPIC-VW-16
	   - id: 16
	   - Subtasks:
	 - [x] VW-26 Doksy: przegląd całej dokumentacji (repo + submoduły)
	 - [x] VW-27 Doksy: plan konsolidacji dokumentacji
	 - [x] VW-33 Doksy: raport rozbieżności vs target-version
	 - [x] VW-28 Doksy: Topic Manager — bez scraperów, integracje
- [ ] Doksy: ujednolicenie README i QUICK_START (VW-35) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - follows: VW-31, VW-28, VW-29
	   - notes:
	 - Kontekst: PROJECT_CONTEXT; TM bez scraperów; ujednolicenie QUICK_START.
- [ ] Doksy: standard README/QUICK_START template i ToC (VW-31) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	 - Źródła: docs/DOCS_CONSOLIDATION_PLAN.md, docs/DOCS_INVENTORY.md, target-version/VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md, istniejące README w usługach
	   - notes:
	 - Artefakty do utworzenia: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md
- [ ] Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - blocks: VW-12
	   - follows: VW-27
	   - comments:
	 - Gamma docs → kolegium/gamma-ppt-generator/README.md
- [ ] Kanban: synchronizacja z PROJECT_CONTEXT (priorytety, etykiety, relacje) (VW-32)
	   - follows: VW-36
	   - comments:
	 - Kontekst → PROJECT_CONTEXT.md
- [ ] PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16]
   ↳ Parent: [^EPIC-VW-16]
   - comments:
 	 - Źródła: PROJECT_CONTEXT.md, target-version/KANBAN.md, docker-compose.yml (porty/usługi), stan Kanban (Vikunja/Wekan)
   - notes:
 	 - Zrealizowano: sekcje "Standard etykiet i priorytetów (Normalization)" i "SOP pracy z Kanbanem" w PROJECT_CONTEXT.md
- [ ] Doksy: cele/metryki/walidacja w README serwisów (VW-34) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - follows: VW-37
- [ ] Doksy: KPI/validation framework — definicja i checklisty (VW-37) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	 - Źródła: tests/e2e/workflow/TEST_PLAN.md, tests/e2e/test_complete_user_workflow.py, publisher/docs/* (monitoring), kolegium/analytics-service/README.md


## done

**Complete**
- [x] [P0] Remove TM scraping stub and docs mentioning /topics/scrape.
- [x] Doksy: Topic Manager — bez scraperów, integracje (VW-28) ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  - comments:
	- TM docs → topic-manager/README.md
- [x] Doksy: Analytics Service — status i API szkic (VW-29) ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Analytics docs → kolegium/analytics-service/README.md
- [x] Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Gamma plan → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
- [x] Doksy: standard README/QUICK_START template i ToC (VW-31) ^EPIC-VW-16]
	  ↳ Parent: [^EPIC-VW-16]
	  	- comments:
	  	- Artefakty: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md
 - [x] PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16]
  ↳ Parent: [^EPIC-VW-16]
  	- comments:
  	- Zmiany: PROJECT_CONTEXT.md → sekcje Normalization + SOP; Źródła: target-version/KANBAN.md, docker-compose.yml
- [x] zadanie testowe dodane przez www (VW-1)
- [x] TEST PUT (VW-2)


## Archive

- [x] 2025-08-13 Doksy: Analytics Service — status i API szkic (VW-29) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Analytics docs → kolegium/analytics-service/README.md
- [x] 2025-08-13 Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Gamma plan → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
- [x] 2025-08-13 Doksy: standard README/QUICK_START template i ToC (VW-31) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Artefakty: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md

- [x] 2025-08-13 PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16]
   ↳ Parent: [^EPIC-VW-16]
  	  - comments:
  	- Zmiany: PROJECT_CONTEXT.md → sekcje Normalization + SOP; Źródła: target-version/KANBAN.md, docker-compose.yml
- [x] 2025-08-13 18:38 Doksy: przegląd całej dokumentacji (repo + submoduły) (VW-26) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	 	  - comments:
	 	- Inwentarz → docs/DOCS_INVENTORY.md
- [x] 2025-08-13 18:38 Doksy: plan konsolidacji dokumentacji (VW-27) ^EPIC-VW-16]
	   ↳ Parent: [
- [x] 2025-08-13 18:38 Doksy: raport rozbieżności vs target-version (VW-33) ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	 	  - comments:
	 	- Raport → docs/DOCS_DIFF_REPORT.md


## blocked





%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[true,true,false,false,true,true],"show-checkboxes":true,"move-tags":false,"move-dates":false}
```
%%