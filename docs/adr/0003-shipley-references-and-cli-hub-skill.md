# ADR 0003: Shipley References and CLI-Hub Developer Skill

Status: accepted
Date: 2026-05-15

## Context

Ariadne Thread needs Shipley-aligned domain knowledge before product workflows are built. The repo now has commit-safe Shipley guides and extracted JSON that should shape terminology, decision gates, and artifact workflows.

The project also expects agents to use professional tools through stable, structured interfaces. CLI-Anything provides a broad catalog of agent-native CLIs, but vendoring the full monorepo would add unnecessary size and maintenance cost before a specific harness is needed.

## Decision

- Store global Shipley knowledge references under `docs/reference/shipley/`.
- Treat those files as methodology source material, not a committed choice of RAG/indexing engine.
- Vendor only CLI-Anything's `cli-hub-meta-skill` under `.github/skills/cli-hub-meta-skill/`.
- Use `uv tool install cli-anything-hub` for CLI-Hub developer tooling to stay aligned with Ariadne's Python tooling rules.
- Do not vendor the full CLI-Anything monorepo or generated harnesses until a specific product or developer workflow needs one.

## Consequences

- Future build work can cite Shipley references without inventing capture language from scratch.
- Knowledge architecture remains open until a retrieval/indexing decision is made.
- Agents can discover professional CLI harnesses when useful, while the repo stays small and focused.
- Any later generated CLI harness should arrive through a narrow, documented architecture decision.