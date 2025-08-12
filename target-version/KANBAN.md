# Vector Wave Backlog (Kanban)

Legend:
- P0 (now) – must-have for E2E launch
- P1 (soon) – important, next after launch
- P2 (later) – nice-to-have / defer
- Status: Todo | In-Progress | Blocked | Done

## Columns

### Todo
- [P0] Stand up self-hosted Kanban (Vikunja) via Docker; expose locally; prepare backup plan. [owner: infra]
- [P0] Smoke E2E: chromadb + editorial-service + topic-manager + crewai-orchestrator up; health checks green. [owner: platform]
- [P0] Harvester smoke: /harvest/trigger → triage-preview and selective-triage promote path to TM. [owner: data]
- [P0] Kolegium AI Writing Flow CI-Light: run basic selective checkpoints against Editorial Service. [owner: kolegium]
- [P0] Orchestrator happy-path flow: research→audience→writer with selective validation calls; return content. [owner: kolegium]
- [P1] Publisher smoke: enqueue → minimal dry-run to LinkedIn adapter (no real publish), metrics visible. [owner: publishing]
- [P1] Topic Manager vector index: reindex + search happy path; embed fallback without OPENAI_API_KEY. [owner: platform]
- [P2] Analytics placeholder API scaffolding (no data collection yet). [owner: analytics]
- [P2] Gamma.app service skeleton kept archived; no integration work. [owner: publishing]

### In-Progress
- (empty)

### Blocked
- (empty)

### Done
- [P0] Remove TM scraping stub and docs mentioning /topics/scrape.
