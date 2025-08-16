---

kanban-plugin: board

---

## backlog

- [ ] Task 1.15: [P2] Presenton fallback hardening (async, timeouts, SLO)
	   - comments:
	   - Ustabilizować Presenton jako fallback dla Gamma: async kolejka + polling/webhook, sensowne timeouts, SLO p95, CB i metryki, optymalizacja LibreOffice, cleanup plików
	   - follows: Task 1.9.3; Task 2.2
	   - blocks: LinkedIn E2E auto‑publish (production‑ready)
	   - Subtasks:
	   - [ ] 1.15.1 /generate → enqueue + /jobs/{id} status + opcjonalny webhook
	   - [ ] 1.15.2 Retry/backoff + circuit breaker + metryki (latencja, success rate)
	   - [ ] 1.15.3 PDF conversion tuning (LibreOffice) lub alternatywny konwerter; limity CPU/RAM
	   - [ ] 1.15.4 Cleanup scheduler (TTL plików, storage quotas)
- [ ] Task 1.16: [EPIC] Service extraction roadmap (monorepo → wydzielenie usług z `kolegium/*`)
	   - comments:
	   - Cel: trwale wyodrębnić usługi z `kolegium/*` do niezależnych katalogów usług w monorepo (stabilny build, health, CI‑light). Decyzja o repo‑strategii (monorepo vs subtree vs submodules) po ustabilizowaniu 2 usług.
	   - follows: Task 1.6 (AI Writing Flow Integration)
	   - Subtasks:
	   - [ ] 1.16.1 Standard katalogu usługi (Dockerfile, .dockerignore, README, QUICK_START, health, metrics)
	   - [ ] 1.16.2 Szablon compose dla nowej usługi (ports, healthcheck, depends_on, networks)
	   - [ ] 1.16.3 Wytyczne ENV/konfiguracji per usługa (konwencje nazw, domyślne wartości)
- [ ] Task 1.17: [P1] Publishing Orchestrator: wydzielenie z `kolegium/publishing-orchestrator` → `publishing-orchestrator-service/`
	   - comments:
	   - Oddzielenie builda od katalogu `kolegium/*`, stabilny endpoint (8085), health, dokumentacja i smoke.
	   - follows: Task 1.6; [P1] Orchestrator→Editorial integration (Done)
	   - blocks: [P1] E2E publish (multi‑platform) stabilizacja
	   - Subtasks:
	   - [ ] 1.17.1 Utwórz `publishing-orchestrator-service/` i przenieś minimalny kod runtime (bez testów/artefaktów)
	   - [ ] 1.17.2 Dodaj Dockerfile (uvicorn/gunicorn), `.dockerignore`, README/QUICK_START
	   - [ ] 1.17.3 Compose: dodaj usługę (8085), health `/health`, `depends_on` (editorial, redis)
	   - [ ] 1.17.4 ENV: `EDITORIAL_SERVICE_URL`, `GAMMA_PPT_URL`, `PRESENTON_URL`, toggles; dokumentacja
	   - [ ] 1.17.5 Smoke: `GET /health`, `/queue/status`, podstawowe ścieżki orchestracji
- [ ] Task 1.18: [P2] LinkedIn PPT Generator: wydzielenie z `kolegium/linkedin_ppt_generator` → `linkedin-ppt-service/`
	   - comments:
	   - Stabilny adapter do Presenton/Gamma, endpointy health/generate, izolacja od `kolegium/*`.
	   - follows: Task 1.17; Task 1.15 (Presenton fallback hardening)
	   - Subtasks:
	   - [ ] 1.18.1 Utwórz `linkedin-ppt-service/` + Dockerfile, `.dockerignore`
	   - [ ] 1.18.2 Compose: dodaj usługę (8002), health `/health`, `PRESENTON_SERVICE_URL`
	   - [ ] 1.18.3 Smoke: `GET /health`, `POST /generate` (demo payload)
	   - [ ] 1.18.4 Dokumentacja kontraktu (payload/odpowiedź)
- [ ] Task 1.19: [P2] Analytics Service: wydzielenie z `kolegium/analytics-service` → `analytics-service/`
	   - comments:
	   - API skeleton w dedykowanym katalogu usługi, health/insights, szybki build.
	   - follows: Task 1.2 (Analytics skeleton in Todo)
	   - Subtasks:
	   - [ ] 1.19.1 Utwórz `analytics-service/` + Dockerfile, `.dockerignore`
	   - [ ] 1.19.2 Compose: dodaj usługę (8081), health `/health`
	   - [ ] 1.19.3 Smoke: `GET /health`, `GET /analytics/insights/{user_id}`
- [ ] Task 1.20: [P2] Gamma PPT Generator: wydzielenie z `kolegium/gamma-ppt-generator` → `gamma-ppt-service/`
	   - comments:
	   - Usługa opcjonalna (profile: gamma); stabilny health i generate w demo/real mode.
	   - follows: Task 1.17; Task 1.15
	   - Subtasks:
	   - [ ] 1.20.1 Utwórz `gamma-ppt-service/` + Dockerfile, `.dockerignore`
	   - [ ] 1.20.2 Compose: dodaj usługę (8003), health `/health`, ENV `GAMMA_API_KEY` (opcjonalnie)
	   - [ ] 1.20.3 Smoke: `GET /health`, `POST /generate` (demo mode)
- [ ] Task 1.21: [ADR] Repo strategy decision point: monorepo vs git subtree vs submodules
	   - comments:
	   - Kryteria: niezależne cykle release, reuse między projektami, sekrety/licencje, kadencja zmian; propozycja rekomendacji + plan migracji (jeśli dotyczy)
	   - follows: Task 1.17; Task 1.18 (co najmniej 2 wydzielone usługi ustabilizowane)
	   - blocks: Task 1.22 (opcjonalna migracja repo)
	   - Subtasks:
	   - [ ] 1.21.1 ADR: zebrane kryteria, ocena opcji (monorepo, subtree, submodules)
	   - [ ] 1.21.2 Rekomendacja + plan (timeline, narzędzia, CI/CD wpływ)
	   - [ ] 1.21.3 Komunikacja: decyzja i wpływ na developer workflow
- [ ] Task 1.22: [Conditional] Implementacja repo strategy (jeśli ≠ monorepo)
	   - comments:
	   - Tylko jeśli decyzja z 1.21 wskazuje na subtree/submodules; przeniesienie historii wybranych usług
	   - follows: Task 1.21
	   - Subtasks:
	   - [ ] 1.22.1 POC: subtree/submodule na jednej usłudze (np. `ai-writing-flow-service`)
	   - [ ] 1.22.2 Migracja docelowych usług (publishing‑orchestrator, linkedin‑ppt, analytics, gamma‑ppt)
	   - [ ] 1.22.3 Aktualizacja CI/CD i dokumentacji deweloperskiej


## todo

- [ ] Task 1.2: [P2] Analytics Service: API skeleton v2.0.0 — health + insights smoke (no data collection yet). [owner: analytics]
	   - comments:
	   - Źródła: kolegium/analytics-service/README.md; health + /analytics/insights/{user_id}
	   - follows: [P0] Orchestrator happy-path flow: research→audience→writer with selective validation calls; return content. [owner: kolegium]
	   - Subtasks:
	   - [ ] 1.2.1 Uruchom analytics-service (profil analytics)
	   - [ ] 1.2.2 GET /health (P95 < 80ms)
	   - [ ] 1.2.3 GET /analytics/insights/{user_id} (Bearer dev; sprawdź data_quality_score)
- [ ] Task 1.3: [P2] Gamma.app service skeleton kept archived; no integration work. [owner: publishing]
	   - comments:
	   - Plan i wymagania → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
	   - Subtasks:
	   - [ ] 1.3.1 Potwierdź tryb archived (brak pracy dev w tym sprincie)
	   - [ ] 1.3.2 Opcjonalny GET /health w demo mode (jeśli uruchomiony)
- [ ] Task 1.5: [EPIC] Publishing (multi-platform)
	   - Subtasks:
	   - [ ] 1.5.1 VW-9 Publisher smoke (Typefully dry-run) (moved to Todo)
	   - [ ] 1.5.2 VW-20 Publisher: dry‑run do LinkedIn adapter
	   - [ ] 1.5.3 VW-25 Publisher: integracja z Gamma (toggle + fallback)
	   - notes:
	   - Zależności: Presenton/LinkedIn adapter (Phase 7 planned); toggle Gamma (po VW-24)
- [ ] Task 1.8: VW-24 Gamma: MVP (health + generate)
	   - id: 24
	   - comments:
	   - STATUS.md: komponent nieukończony → zostawić w Backlog; dodać Subtasks
	   - Subtasks:
	   - [ ] 1.8.1 Implement /generate i /health real mode z GAMMA_API_KEY
	   - [ ] 1.8.2 Circuit breaker i quota awareness w health
	   - [ ] 1.8.3 Demo mode smoke bez klucza
	   - status: In Progress (2025-08-15) — kontener uruchomiony profilem gamma, health w toku
- [ ] Task 2.1: [P1] Alerty/rate‑limits E2E (real adapter) [owner: publishing]
	  - comments:
	  - Wywołać kontrolowany błąd limitów; oczekiwać alertu (Telegram/Discord/Webhook) + metryki `alerts_sent_total`
	  - follows: [P1] Publisher E2E (Twitter/X, real)
	  - status: In Progress (2025-08-15) — przygotowanie kontroli 429 i webhook alert


## in progress

- [ ] Task 1.6: [P1] AI Writing Flow Integration (Phase 6) [owner: kolegium]
	   - comments:
	   - Cel: uruchomić AI Writing Flow w compose i spiąć z Orchestrator → pełny workflow redakcyjny na localhost
	   - follows: Task 1.1; [P0] Orchestrator happy-path flow
	   - blocks: E2E /publish z `direct_content=false`
	   - Subtasks:
	   - [ ] 1.6.1 Compose: dodać usługę `ai-writing-flow` (port 8003 lub 8004), `networks: [vector-wave]`, health `/health`
	   - [ ] 1.6.2 Orchestrator: ustawić `AI_WRITING_FLOW_URL=http://ai-writing-flow:8003`
	   - [ ] 1.6.3 Kontrakt payloadu: ujednolicić (flat vs `topic.*`) między Orchestrator → AIWF
	   - [ ] 1.6.4 Health-gate + retry/backoff dla wywołań AIWF
	   - [ ] 1.6.5 Smoke: `GET /health` i `POST /generate` (selective path)
	   - [ ] 1.6.6 E2E: `POST /publish` z `direct_content=false` (content przez AIWF)


## done

- [x] Task 1.9: VW-25 Publisher: integracja z Gamma (toggle + fallback)
	   - id: 25
	   - follows: VW-24
	   - comments:
	   - STATUS.md: brak integracji → dodać Subtasks
	   - Subtasks:
	   - [x] 1.9.1 Env toggle GAMMA_ENABLED + GAMMA_URL
	   - [x] 		.9.2 Branching Presenton/Gamma w orchestratorze publikacji
	   - [x] 1.9.3 Fallback path + testy kontraktowe
	   - status: In Progress (2025-08-15) — toggle `GAMMA_ENABLED` dodany do compose
- [x] Task 2.7: [P2] Ghost E2E (sandbox): publikacja do instancji testowej [owner: publishing]
	  - comments:
	  - Wykonano na produkcyjnym Ghost jako draft (Opcja B); `[TEST]` w tytule; bez harmonogramu; status `completed`
	  - follows: Task 2.6
	  - status: Done (2025-08-16) — publication_id=pub_4f7f9095-9a5f-452d-8fca-d7cdce3657ff
- [x] Task 2.6: [P1] Ghost Adapter real credentials: `GHOST_API_URL` + `GHOST_API_KEY` (dev sandbox) [owner: publishing]
	  - comments:
	  - `.env` skonfigurowane; `/config`=ready, `/health`=healthy; adapter działa z realnym API (bez publikacji prod poza draft)
	  - follows: [P1] Redis Worker E2E
	  - status: Done (2025-08-16) — adapter healthy, config OK
- [x] Task 2.5: [P1] Orchestrator→Worker→Twitter E2E (real schedule) [owner: publishing]
	  - comments:
	  - `POST /publish` (8095) z `platforms.twitter.enabled=true` → worker deleguje do twitter-adapter; status scheduled; po czasie published
	  - follows: Task 2.4
	  - blocks: [P1] Webhook callbacks E2E; [P1] Alerty/rate‑limits E2E
- [x] Task 2.4: [P1] Worker: Twitter payload mapping (orchestrator → adapter) [owner: publishing]
	  - comments:
	  - Zmapować payload w workerze: `topic.title/description` → `text`, opcjonalnie `schedule_time`, `thread_mode`; ustawić `TWITTER_ADAPTER_URL`
	  - follows: Task 2.3; [P1] Redis Worker E2E
	  - blocks: [P1] Orchestrator→Worker→Twitter E2E (real)
- [x] Task 1.14: [P2] Orchestrator: circuit breaker thresholds + exposure
	   - comments:
	   - Skalibrować progi CB (failure_threshold/recovery_timeout); dodać /monitoring z CB state
	   - follows: Task 1.12
	   - status: Done (2025-08-15) — ENV `EDITORIAL_CB_*` + `/monitoring/agents/circuit-breaker`
- [x] Task 1.13: [P2] Orchestrator: error taxonomy mapping + metrics
	   - comments:
	   - Mapować błędy Editorial do spójnych kodów/stanu flow; dodać metryki (latencja/sukces/błąd) per agent
	   - follows: Task 1.12
	   - status: Done (2025-08-15) — `/flows/execute` completed; `/validate/*` obecne w OpenAPI
- [x] Task 1.12: [P1] Orchestrator→Editorial: retry/backoff & timeout policy
	   - comments:
	   - Ustalić politykę retry (exponential backoff) i timeouts dla wywołań `/validate/*`; telemetry sukcesów/porażek
	   - follows: Task 1.4 (EPIC Orchestrator→Editorial integration)
	   - Subtasks:
	   - [x] 1.12.1 Ustawić domyślne timeouts i backoff w `AgentHTTPClient`
	   - [x] 1.12.2 Dodać test smoke z wymuszonym timeoutem
- [x] Task 1.4: [EPIC] Orchestrator → Editorial integration
	 	   - id: 19
	 	   - labels: EPIC
	 	   - Subtasks:
	 	   - [x] 1.4.1 Orchestrator→Editorial: sprawdzenie integracji (follows: Orchestrator happy-path in Todo)
	 	   - notes:
	 	   - Cel: potwierdzić ścieżki Orchestrator→Editorial (health, validate, error handling)
	 	   - status: Smoke OK (2025-08-15) — `/flows/execute` completed; `/validate/*` obecne w OpenAPI
	  - blocks: [P1] Publisher E2E (Twitter/X, real)
- [x] Task 2.3: [P1] Twitter Adapter (Typefully) hardening: API key + klient + 200/403 paths [owner: publishing]
	  - comments:
	  - Naprawić `typefully_client` (import/init), obsłużyć 403 z `/drafts/recently-published/`, ujednolicić odpowiedź `/publish`
	  - follows: [P1] Redis Worker E2E
	  - Subtasks:
	  - [x] 2.3.1 Health: napraw `name 'typefully_client' is not defined` w `/health` (użyj `TypefullyClient()` albo warunkowego sprawdzenia)
	  - [x] 2.3.2 Health: przy poprawnym API key raportuj `status=ok` i `api_available=true`
	  - [x] 2.3.3 Test: zweryfikuj `GET /health` (brak wyjątków, P95 < 1000ms)
- [x] - [ ] [P1] LinkedIn E2E (real): tekst + PDF przez moduł `linkedin` [owner: linkedin]
- [x] Task 1.11: [P1] Orchestrator: Sequence API contract & examples [owner: kolegium]
	 	   - comments:
	 	   - Uzupełnić README/API_CONTRACT o minimalny payload `{content, platform}`, przykłady curl i typowe błędy
	 	   - follows: [P1] Orchestrator: Redis readiness for sequence (REDIS_URL + compose) [owner: kolegium]
	 	   - blocks: [P1] Orchestrator: enable sequence endpoint (/checkpoints/sequence/start) [owner: kolegium]
	 	   - Subtasks:
	 	   - [x] 1.11.1 Zaktualizować `crewai-orchestrator/API_CONTRACT.md`
	 	   - [x] 1.11.2 Dodać przykłady do `crewai-orchestrator/README.md`
	 	   - [x] 1.11.3 Dodać sekcję „typowe błędy i kody” (422/501)
- [x] Task 1.10: [P1] Orchestrator: Redis readiness for sequence (REDIS_URL + compose) [owner: kolegium]
	 	   - comments:
	 	   - Przygotować usługę Redis w compose i zmienne środowiskowe (`REDIS_URL`) dla Orchestratora pod sekwencje
	 	   - follows: [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
	 	   - blocks: [P1] Orchestrator: enable sequence endpoint (/checkpoints/sequence/start) [owner: kolegium]
	 	   - Subtasks:
	 	   - [x] 1.10.1 docker-compose: dodać usługę `redis` i sieć (profile: default,publishing)
	 	   - [x] 1.10.2 Orchestrator: odczyt `REDIS_URL` i inicjalizacja klienta Redis
	 	   - [x] 1.10.3 Orchestrator: smoke połączenia (ping) na starcie; łagodne logowanie błędów
	 	   - [x] 1.10.4 Orchestrator: `/health` uzupełnić o `sequence_ready` (true/false)
	 	   - [x] 1.10.5 Dokumentacja: README aktualizacja (REDIS_URL, health field)
	 	   - [x] 1.10.6 Dokumentacja: API_CONTRACT aktualizacja (REDIS_URL, `sequence_ready`)
- [x] Task 2.8: [P1] Orchestrator: expose `/queue/status` w prod (8085) [owner: publishing]
	 	  - comments:
	 	  - Ujednolicić ścieżkę i odpowiedź tak, by była dostępna w service na 8085
	 	  - follows: [P1] Redis Worker E2E
- [x] [P1] LinkedIn Adapter connectivity/health hardening [owner: publishing]
	   - comments:
	   - Wyeliminować ciągłe próby połączeń do `host.docker.internal:8098`; dodać poprawny health gate i retry/backoff
	   - follows: [P1] Orchestrator→Worker→Twitter E2E (real schedule)
	   - blocks: [P1] LinkedIn E2E (real)
	   - Subtasks:
	   - [x] Dodać `LINKEDIN_ADAPTER_URL` do compose/ENV i healthcheck `/health`
	   - [x] W workerze: pominąć enqueue/linkedin, gdy adapter unhealthy; dodany circuit breaker (ENV: `CB_FAILURE_THRESHOLD`, `CB_OPEN_SECONDS`)
	   - [x] Dodać metryki adapter health oraz endpoint `/worker/circuit-state`
	   - [x] Test integracyjny: gdy adapter down → brak zalewu retry, brak blokowania innych zadań
- [x] - [ ] [P1] Publisher E2E (Twitter/X, real): Typefully schedule→auto‑publish [owner: publishing]
	  - comments:
	  - Użyć `schedule_time=now+5m`; po czasie status `completed`; potwierdzić publikację po stronie Typefully/X
	  - Progress 2025-08-14:
	- Naprawiono dekorator metryk (async) i skonfigurowano `TYPEFULLY_API_KEY`
	- Konto X podłączone w Typefully; `POST /publish` (8083) → scheduled=true, `tweet_id=6476931`
	- `GET /status/6476931` → status=scheduled (czeka na auto‑publish)
	  - Progress 2025-08-15:
	  - Realny run: `publication_id=pub_f299c62b-5d74-47fa-8480-f33329e8fb49` → `status=completed`
	  - Webhook: `tweet_id=6477779`, `scheduled=true`, komunikat „Tweet zaplanowany w Typefully (ID: 6477779)”
	  - follows: [P1] Redis Worker E2E
	  - blocks: [P1] Webhook callbacks E2E; [P1] Alerty/rate‑limits E2E
- [ ] - [x] [P1] Redis Worker E2E: przetwarzanie zadań i przejścia stanów [owner: publishing]
	  - comments:
	  - Potwierdzone przejścia queued→processing→completed/failed; `/publication/{id}`, `/worker/status`, `/queue/status` działają (8095)
	  - follows: [P1] Publisher smoke: enqueue
- [ ] - [x] [P1] Worker: Twitter payload mapping (orchestrator → adapter) [owner: publishing]
	  - comments:
	  - Zaimplementowano mapowanie `topic`→`text`, `schedule_time`, `thread_mode`; delegacja do `twitter-adapter` działa
	  - follows: [P1] Redis Worker E2E; [P1] Twitter Adapter (Typefully) hardening
- [ ] - [x] [P1] Orchestrator→Worker→Twitter E2E (real schedule) [owner: publishing]
	  - comments:
	  - `POST /publish` (8095) z `twitter.enabled=true` → worker deleguje do adaptera; status completed (delegacja OK), schedule potwierdzony po stronie adaptera
	  - follows: [P1] Worker: Twitter payload mapping
- [ ] - [x] [P1] Webhook callbacks E2E (publication status callbacks) [owner: publishing]
	  - comments:
	  - Uruchomiono lokalny `webhook-tester` (8099) i naprawiono wysyłkę callbacków w workerze (użycie `platform_client.http_client`)
	  - Publikacja z `webhook_url` → callback odebrany: `publication_id=pub_5c658718-c699-48c1-ab27-bcdba87a309b`, `platform=twitter`, `status=completed`
	  - follows: [P1] Orchestrator→Worker→Twitter E2E (real schedule)
	  - blocks: [P1] Alerty/rate‑limits E2E


## Archive

- [x] 2025-08-13 VW-14 E2E: start core stack i health (duplicate of P0 Smoke E2E) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 Smoke E2E (Todo)
- [x] 2025-08-13 VW-15 Harvester: trigger i triage-preview (duplicate of Todo Harvester smoke) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 Harvester smoke (Todo)
- [x] 2025-08-13 VW-17 Harvester: promote selective-triage do TM (duplicate; part of VW-15) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; część Subtasks w Harvester smoke (Todo)
- [x] 2025-08-13 VW-18 Kolegium: selective checkpoints vs Editorial Service (duplicate of Todo CI-Light) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 CI-Light (Todo)
- [x] 2025-08-13 VW-21 Topic Manager: reindex + search happy path (duplicate of Todo TM vector index) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P1 TM vector index (Todo)
- [x] 2025-08-13 VW-22 Analytics: API skeleton + /health (duplicate of Todo Analytics v2.0.0 skeleton) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P2 Analytics skeleton (Todo)
- [x] 2025-08-13 VW-8 Orchestrator happy-path flow (duplicate of Todo Orchestrator happy-path) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P0 Orchestrator happy-path (Todo)
- [x] 2025-08-13 VW-10 Topic Manager vector index (duplicate of Todo TM vector index) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	   - comments:
	   - Zarchiwizowano jako duplikat; realizacja w zadaniu P1 TM vector index (Todo)
- [x] 2025-08-13 Doksy: Analytics Service — status i API szkic (VW-29) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Analytics docs → kolegium/analytics-service/README.md
- [x] 2025-08-13 Doksy: Gamma.app — stan, plan i wymagania (VW-30) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Gamma plan → docs/GAMMA_INTEGRATION_PLAN.md; Service docs → kolegium/gamma-ppt-generator/README.md
- [x] 2025-08-13 Doksy: ujednolicenie README i QUICK_START (VW-35) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Linter: scripts/docs_lint_readme.py (wynik: wszystkie README OK); Wdrożone standardy: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md; Znormalizowane README: editorial-service, topic-manager, publisher, presenton, kolegium/analytics-service, kolegium/gamma-ppt-generator, kolegium
- [x] 2025-08-13 Doksy: KPI/validation framework — definicja i checklisty (VW-37) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Dokument: docs/KPI_VALIDATION_FRAMEWORK.md; zastosowane w README usług
- [x] 2025-08-13 Doksy: cele/metryki/walidacja w README serwisów (VW-34) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- README zaktualizowane o sekcję KPIs i Walidacja; linter OK
- [x] 2025-08-13 Doksy: standard README/QUICK_START template i ToC (VW-31) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Artefakty: docs/README_TEMPLATE.md, docs/QUICK_START_TEMPLATE.md, docs/DOCS_TOC_STANDARD.md
- [x] 2025-08-13 PROJECT_CONTEXT normalization: labels/priorities spec + SOP (VW-36) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  	  - comments:
	  	- Zmiany: PROJECT_CONTEXT.md → sekcje Normalization + SOP; Źródła: target-version/KANBAN.md, docker-compose.yml
- [x] 2025-08-13 18:38 Doksy: przegląd całej dokumentacji (repo + submoduły) (VW-26) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	 	  - comments:
	 	- Inwentarz → docs/DOCS_INVENTORY.md
- [x] 2025-08-13 18:38 Doksy: plan konsolidacji dokumentacji (VW-27) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [
- [x] 2025-08-13 18:38 Doksy: raport rozbieżności vs target-version (VW-33)
- [x] 2025-08-13 Kanban: synchronizacja z PROJECT_CONTEXT (priorytety, etykiety, relacje) (VW-32) ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16] ^EPIC-VW-16]
	   ↳ Parent: [^EPIC-VW-16]
	  - comments:
	- Synchronizacja: usunięto duplikaty kotwicy ^EPIC-VW-16, poprawiono „↳ Parent” i literówki; zgodnie z PROJECT_CONTEXT.md
	   ↳ Parent: [^EPIC-VW-16]
	 	  - comments:
	 	- Raport → docs/DOCS_DIFF_REPORT.md


## blocked

- [ ] Task 2.2: [P1] LinkedIn E2E (real): tekst + PDF przez moduł `linkedin` [owner: linkedin]
	   - comments:
	   - Zakres: generate (Gamma/Presenton) → zapisz `pdf_url`/`ppt_url` → (opcjonalnie) auto‑publish via LinkedIn API jeśli skonfigurowany
	   - Sesja w `linkedin` module; publikacja realnego posta/PDF; jeśli przez orchestrator: job queued→completed oraz URL posta
	   - follows: VW-24 Gamma; VW-25 Gamma toggle
	   - Subtasks:
	   - [ ] 2.2.1 Zasilić `LINKEDIN_API_ENABLED`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_OWNER_URN` (opcjonalnie)
	   - [x] 2.2.2 `POST /publish` zwraca `platform_content.linkedin.manual_upload` z `pdf_url`/`ppt_url`
	   - [ ] 2.2.3 (Opcja) Gdy LinkedIn API włączony, automatycznie utworzyć document post


## DAG: Todo + In Progress

- [ ] Task 1.6 → Task 1.16 → Task 1.17
	   - Uzasadnienie: uruchomienie AI Writing Flow w compose (1.6) umożliwia wdrożenie standardu ekstrakcji usług (1.16), po czym wydzielamy Orchestrator (1.17).
- [ ] Task 1.17 → Task 1.18, Task 1.20
	   - Po stabilizacji Orchestratora wydzielamy usługi zależne adapterów prezentacji (LinkedIn PPT oraz Gamma PPT).
- [ ] Task 1.2 ↔ Task 1.19
	   - Skeleton Analytics (1.2) jest prekursorem wydzielenia Analytics (1.19); mogą postępować równolegle po ustaleniu minimalnego kontraktu.
- [ ] Decision Gate: Task 1.21 (ADR)
	   - Wejścia: doświadczenia z min. 2 wydzielonymi usługami (1.17 + 1.18/1.19), koszty buildów/CI, potrzeba reuse.
	   - Wyjście: rekomendacja repo (pozostajemy w monorepo vs subtree/submodules) i plan (jeśli zmiana konieczna).
- [ ] Task 1.22 (Conditional) zależy od decyzji z 1.21.




%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[false,false,false,false,true,true,false],"show-checkboxes":true,"move-tags":true,"move-dates":false,"full-list-lane-width":true,"inline-metadata-position":"footer","lane-width":400}
```
%%