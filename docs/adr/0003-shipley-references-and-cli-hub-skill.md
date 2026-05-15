# ADR 0003: Shipley References and CLI-Anything Developer Skills

Status: accepted
Date: 2026-05-15

## Context

Ariadne Thread needs Shipley-aligned domain knowledge before product workflows are built. The repo now has commit-safe Shipley guides and extracted JSON that should shape terminology, decision gates, and artifact workflows.

The project also expects agents to use professional tools through stable, structured interfaces. CLI-Anything provides a broad catalog of agent-native CLIs and a harness methodology for generating new CLI surfaces. Ariadne should be able to use that methodology for internal platform capabilities that are better expressed as deterministic CLI operations than complicated UI or bespoke tool integrations.

## Decision

- Store global Shipley knowledge references under `docs/reference/shipley/`.
- Treat those files as methodology source material, not a committed choice of RAG/indexing engine.
- Vendor CLI-Anything's builder skill under `.github/skills/cli-anything/` from upstream `codex-skill/`, with selected `cli-anything-plugin/` methodology resources bundled under `resources/cli-anything-plugin/`.
- Keep CLI-Anything's `cli-hub-meta-skill` under `.github/skills/cli-hub-meta-skill/` as an optional discovery aid for checking whether an existing external-tool harness already exists.
- Use `uv tool install cli-anything-hub` only when live catalog discovery is needed, to stay aligned with Ariadne's Python tooling rules.
- Do not vendor the full CLI-Anything monorepo or generated harnesses until a specific product or developer workflow needs one.
- Prefer CLI-first harnesses for repeatable, batchable, tool-facing, or agent-facing Ariadne capabilities that need deterministic JSON output.

## Consequences

- Future build work can cite Shipley references without inventing capture language from scratch.
- Knowledge architecture remains open until a retrieval/indexing decision is made.
- Agents can optionally discover existing professional CLI harnesses before building new external-tool wrappers, while the repo stays small and focused.
- UI work is less likely to absorb batch jobs, data pulls, document conversion, validation, or tool wrappers that belong behind CLI/agent surfaces.
- Any later generated CLI harness should arrive through a narrow, documented architecture decision or issue tied to a concrete workflow.
