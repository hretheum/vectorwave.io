# ADR 001: Repository strategy (monorepo vs subtree vs submodules)

Status: Accepted — 2025-08-16

## Context
We extracted multiple services from `kolegium/*` into deployable service directories (e.g., `ai-writing-flow-service/`, `publishing-orchestrator-service/`, `linkedin-ppt-service/`, `gamma-ppt-service/`). We need a durable repo strategy that supports:
- Independent service builds and runtime isolation
- Clear ownership and documentation per service
- Simple cross-service changes (frequent at this stage)
- Low operational overhead for CI/CD and local dev

## Decision Drivers
- Early stage: frequent cross-service edits and refactors
- Single team ownership, single deployment target
- Minimal friction for contributors (no extra tooling/state for checkout)
- CI simplicity (one pipeline orchestrating multiple services)
- Future option to split out reusable services without churn

## Options Considered
1) Monorepo (current) with service subdirectories
2) Git subtree per service (split-friendly)
3) Git submodules per service (hard isolation)

## Pros/Cons (summary)
### Monorepo
- Pros: simplest DX/CI; atomic cross-service changes; single source of truth; trivial onboarding
- Cons: repo growth; shared history; requires conventions to keep contexts clean

### Subtree
- Pros: later extraction to standalone repos is smooth; history can be preserved per service
- Cons: extra tooling/flows for split/merge; mild operational overhead

### Submodules
- Pros: strong isolation; separate versioning
- Cons: fragile UX (init/update); CI complexity; cross-repo changes painful; overkill for current team/phase

## Decision
Stay in monorepo for now.
- Maintain one repo with dedicated service directories and standardized structure
- Defer subtree/submodules until services reach stability/reuse across projects

## Consequences
- CI/CD remains simple; compose-based local dev stays trivial
- Enforce service standards to avoid context leakage (Dockerfile, .dockerignore, README, health, metrics)
- Revisit when at least two services are reused externally or require separate release cadence

## Rollout Plan
1) Adopt service directory standard (Task 1.16.1) across all extracted/new services
2) Keep docker-compose as integration backbone; add profiles where needed
3) Prepare subtree playbook (optional) for future extraction with preserved history

## Re-evaluation Trigger
- Any service needed in another product/repo
- Diverging release cadence/ownership requiring separate governance
- Compliance/licensing constraints per service

## Links
- Kanban Task 1.16 (Service extraction roadmap)
- Kanban Task 1.21 (ADR decision gate)
- docker-compose.yml (service topology)

