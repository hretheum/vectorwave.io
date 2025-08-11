### 📋 Phase 2 Task Breakdown (Revised Section)

##### Task 2.2: Kolegium Integration (1 week)
```yaml
objective: "Integrate the main Kolegium workflow with the Editorial Service for comprehensive validation"
deliverable: "Modified Kolegium main loop that uses the Editorial Service API instead of local, hardcoded style guides"
acceptance_criteria:
  - Kolegium workflow successfully calls the /validate/comprehensive endpoint
  - The response from the Editorial Service is correctly parsed and used to guide content generation
  - All hardcoded rule lists in the main Kolegium flow are removed
  - End-to-end tests for the Kolegium workflow pass using the live Editorial Service

validation_commands:
  - "pytest kolegium/tests/test_kolegium_e2e_integration.py"
  - "curl -X POST http://localhost:8001/kolegium/run -d '{\"topic\": \"Test\"}' | jq '.validation_source' # Expected: 'editorial-service'"

test_requirements:
  unit_tests:
    - test_kolegium_editorial_client_integration()
    - test_comprehensive_response_parsing()
  integration_tests:
    - test_kolegium_workflow_with_live_editorial_service()
    - test_fallback_mechanism_when_editorial_service_is_down()
  performance_tests:
    - "Kolegium workflow E2E latency with validation < 60s"
```

##### Task 2.3 (Revised): Topic Manager Foundation & Harvester Integration API (2 weeks) 🆕
This task is revised to include the implementation of endpoints required for the Harvester integration.

##### Task 2.3.1: Topic Manager Service Foundation (1.5 weeks)
```yaml
objective: "Build and deploy the Topic Manager service for intelligent topic suggestion"
deliverable: "A fully functional Topic Manager service running on port 8041, with foundational CRUD endpoints for topics"
acceptance_criteria:
  - Topic Manager service is containerized and runs via docker-compose.
  - `POST /topics/manual`, `GET /topics/{id}`, `GET /topics` endpoints are functional.
  - The service is integrated into the main AI Writing Flow for suggesting topics to the UI.

validation_commands:
  - "curl http://localhost:8041/health"
  - "python topic-manager/tests/test_crud.py"
```

##### Task 2.3.2: Harvester Integration Endpoints (0.5 weeks) ⏱️ 4h
```yaml
objective: "Implement the specific endpoints required for the Trend Harvester service"
deliverable: "Functional `/novelty-check` and `/suggestion` endpoints in the Topic Manager"
acceptance_criteria:
  - `POST /topics/novelty-check` is implemented according to the integration contract, performing a similarity search.
  - `POST /topics/suggestion` is implemented, accepting suggestions from Harvester and creating new topics.
  - Both endpoints are protected and require a Bearer token.
  - The `Idempotency-Key` header is correctly handled for the `/suggestion` endpoint to prevent duplicates.

validation_commands:
  - "pytest topic-manager/tests/test_harvester_integration.py"
```
