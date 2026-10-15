# Vector Wave — STATUS (2025-08-17)

- AI Writing Flow v2 (Enhanced API) — LinkedIn generation hotfix deployed.
  - Symptom: `/v2/generate/multi-platform` returned no content for LinkedIn in prompt/direct.
  - Hotfix:
    - In `ai-writing-flow-service` `platform_optimizer.py` we now return a minimal, valid result when V2 yields no content:
      - direct mode: short analysis + summary scaffold
      - prompt mode (carousel): constructed prompt text
    - UI proxy `/api/generate-draft` temporarily forces `direct_content=true` for LinkedIn.
  - Result: Orchestrator `/publish` returns `platform_content.linkedin.content` with `generator: aiwf_v2`.

- Kanban updates:
  - Added: `AIWF-LinkedIn: Naprawa v2 (prompt/direct) [P1]` (backlog) — implement proper V2 behavior (remove hotfix path, generate real content, tests, docs).
  - Added: `AIWF-Hotfix: UI force direct_content (LinkedIn) [P1]` (in progress) — UI-side temporary measure (change applied; smoke pending).

- Next steps:
  - Implement proper prompt/direct generation in AIWF v2 and remove hotfix scaffolds.
  - Smoke E2E UI→Orchestrator→AIWF and mark `AIWF-Hotfix` as done.
