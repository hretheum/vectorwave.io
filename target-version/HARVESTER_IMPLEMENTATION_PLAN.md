# Trend-Harvester Service: Complete Implementation Plan

**Version:** 1.0
**Date:** 2025-08-11
**Status:** Ready for Implementation

## 1. Overview

This document provides a complete, atomized, and incremental implementation plan for the `Trend-Harvester` microservice. It is the single source of truth for this feature and supersedes any previous definitions in the main roadmap.

The plan is designed to deliver a working, data-fetching prototype as quickly as possible, and then incrementally add layers of AI-driven intelligence and automation.

## 2. Phase 1: Foundation & Core Data Pipeline (Rapid Prototype)

**Goal:** To have a containerized service that can be manually triggered to fetch real data from key APIs and store it in a dedicated ChromaDB collection.

### Task 1.1: Harvester Service Foundation (0.5 days) ⏱️ 4h
```yaml
objective: "Create the Trend-Harvester microservice foundation with a container-first approach"
deliverable: "A running, skeletal FastAPI service on port 8043, integrated into the main docker-compose file under the 'harvester' profile"
acceptance_criteria:
  - The `harvester/` directory is created with a standard project structure.
  - The service can be started with `docker compose --profile harvester up -d`.
  - The `/health` endpoint returns a 200 OK status.

validation_commands:
  - "docker compose --profile harvester up -d --build"
  - "curl http://localhost:8043/health"
```

### Task 1.2: [USER ACTION REQUIRED] Provide API Keys & Tokens (0.5 days) ⏱️ 4h
```yaml
objective: "Provide the necessary API keys and tokens for the Trend Harvester to access external and internal services"
deliverable: "Updated environment variable configuration (`.env` file or similar) with the required secrets"
acceptance_criteria:
  - The development environment is configured with valid keys for the services listed below.

api_list:
  - **GitHub:** For tracking open-source projects. ([Docs](https://docs.github.com/en/rest/authentication/creating-a-personal-access-token))
  - **Product Hunt:** For discovering new tech products. ([Docs](https://api.producthunt.com/v2/docs))
  - **Dev.to:** For developer articles and tutorials. ([Docs](https://developers.forem.com/api/v1))
  - **NewsData.io:** For global news aggregation. ([Docs](https://newsdata.io/docs))
  - **TOPIC_MANAGER_TOKEN:** A secret Bearer token for authenticating with the Topic Manager service.

note: "Hacker News and ArXiv do not require API keys."
```

### Task 1.3: Core Data Ingestion Pipeline (2 days) ⏱️ 16h
```yaml
objective: "Implement the core functionality of fetching and storing real data from external APIs"
deliverable: "A triggerable workflow that populates the `raw_trends` ChromaDB collection with data from configured APIs"
acceptance_criteria:
  - A `Fetcher Engine` is implemented, capable of querying all 6 initial sources: Hacker News, ArXiv, GitHub, Product Hunt, Dev.to, and NewsData.io.
  - A `Storage Service` is implemented to save normalized data to a new ChromaDB collection named `raw_trends`.
  - The `POST /harvest/trigger` endpoint successfully executes the entire fetch-and-store pipeline.
  - The process is resilient; failure of one API does not stop the others.

validation_commands:
  - "curl -X POST http://localhost:8043/harvest/trigger"
  - "sleep 30 && python scripts/verify_chroma_collection.py --collection raw_trends --min-count 50"
```

## 3. Phase 2: Integration with Core Services

**Goal:** To enable the `Harvester` to communicate with other services (`Editorial Service`, `Topic Manager`) to gather the necessary context for intelligent decision-making.

### Task 2.1: Editorial Service Profile Endpoint (1 day) ⏱️ 8h
```yaml
objective: "Enhance the Editorial Service to expose a profile-scoring endpoint"
deliverable: "A new `POST /profile/score` endpoint in the Editorial Service"
acceptance_criteria:
  - The new endpoint accepts a JSON payload with `content_summary` (string).
  - It performs a ChromaDB query against the `style_editorial_rules` collection using the summary.
  - **Scoring Logic:** The returned `profile_fit_score` is calculated as `1.0 - distance`, where `distance` is the value returned by ChromaDB for the most relevant rule. The score must be between 0.0 and 1.0.
  - If no rules are found, the score must be `0.0`.
  - The response includes a list of `matching_rules` containing the content of the top 3 matched rules.

validation_commands:
  - "curl -X POST http://localhost:8040/profile/score -H 'Content-Type: application/json' -d '{\"content_summary\": "A new AI model for code generation"}' | jq '.profile_fit_score'"
```

### Task 2.2: Topic Manager Integration Endpoints (0.5 weeks) ⏱️ 4h
```yaml
objective: "Implement the specific endpoints in Topic Manager required for the Trend Harvester service"
deliverable: "Functional `/novelty-check` and `/suggestion` endpoints in the Topic Manager"
acceptance_criteria:
  - `POST /topics/novelty-check` is implemented according to the integration contract, performing a similarity search.
  - `POST /topics/suggestion` is implemented, accepting suggestions from Harvester and creating new topics.
  - Both endpoints are protected and require a Bearer token.
  - The `Idempotency-Key` header is correctly handled for the `/suggestion` endpoint to prevent duplicates.

validation_commands:
  - "pytest topic-manager/tests/test_harvester_integration.py"
```

## 4. Phase 3: AI-Powered Triage & Automation

**Goal:** To implement the AI-driven decision-making layer and fully automate the workflow.

### Task 3.1: Triage Crew Implementation (2 days) ⏱️ 16h
```yaml
objective: "Implement the `Triage Crew` of AI agents for automated assessment, using the formal integration contract"
deliverable: "A functional CrewAI team within the Harvester that processes items from the `raw_trends` collection"
dependencies: ["Task 2.1", "Task 2.2"]
acceptance_criteria:
  - The crew's `NoveltyCheckAgent` successfully calls the `POST /topics/novelty-check` endpoint on the Topic Manager.
  - The crew's `ProfileAssessorAgent` successfully calls the `POST /profile/score` endpoint on the Editorial Service.
  - **Decision Logic:** The crew produces a final decision based on the following rule: `PROMOTE` if `profile_fit_score >= 0.7 AND novelty_score >= 0.8`, otherwise `REJECT`.
  - For promoted items, the crew constructs the precise JSON payload required by the `POST /topics/suggestion` endpoint.
  - The crew correctly generates and includes `Authorization` and `Idempotency-Key` headers in its requests to the Topic Manager.

validation_commands:
  - "pytest harvester/tests/test_triage_crew.py"
```

### Task 3.2: Topic Promotion & Scheduling (1.5 days) ⏱️ 12h
```yaml
objective: "Implement the final step of the workflow: promoting topics and scheduling the process"
deliverable: "A complete, scheduled workflow that automatically discovers, triages, and promotes new topics"
acceptance_criteria:
  - Items marked `PROMOTE` by the Triage Crew are sent to the `POST /topics/suggestion` endpoint of the Topic Manager.
  - The status of the item in the `raw_trends` collection is updated to `promoted`.
  - The entire process is scheduled to run automatically using APScheduler.

validation_commands:
  - "curl -X POST http://localhost:8043/harvest/trigger"
  - "docker compose logs harvester | grep 'Harvest cycle completed. Promoted X topics.'"
```

### Task 3.3: Final Integration & Monitoring (1 day) ⏱️ 8h
```yaml
objective: "Fully integrate the Harvester service and add monitoring"
deliverable: "A stable, observable Harvester service"
acceptance_criteria:
  - The `/health` endpoint correctly reflects the status of all dependencies.
  - The `/harvest/status` endpoint provides accurate information about runs.
  - The main `VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md` diagram is updated to reflect the final workflow.

validation_commands:
  - "curl http://localhost:8043/harvest/status | jq '.last_run.status'"
```
