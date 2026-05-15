# Phase 0 Architecture Review

Date: 2026-05-15  
Scope: fresh repository before application code

## Current State

- Product source of truth exists in `PRD.md`.
- Domain language exists in `CONTEXT.md`.
- Matt Pocock architecture/setup/write-a-skill, first-principles, skill-creator, Ariadne UI/UX, CLI-Anything builder, and CLI-Hub meta-skills are installed or vendored project-locally.
- Agent setup docs exist in `AGENTS.md` and `docs/agents/`.
- Live secrets are excluded by `.gitignore`; `.env.example` contains only public configuration shape.
- Commit-safe Shipley references live under `docs/reference/shipley/` as global methodology source material.
- OpenAI `text-embedding-3-large` is the canonical embedding path unless a later ADR defines migration and index isolation.

## Deepening Opportunities To Consider Before App Code

1. Capture lifecycle module: expose a small interface around opportunity state, gate transitions, evidence, risks, and next actions instead of scattering Shipley rules across UI components.
2. Knowledge layer adapter: keep candidate RAG engines, embeddings, graph storage, and local vault concerns behind one Ariadne retrieval interface so implementation details do not leak into capture workflows.
3. Artifact renderer module: separate artifact intent, preview state, and export adapters so DOCX/XLSX/presentation outputs share one workflow without one oversized renderer.
4. Agent runtime module: define a narrow Hermes execution interface before wiring model providers, local tools, skills, and memory.
5. Environment configuration module: translate `.env` provider settings into typed runtime capabilities without exposing raw Project Theseus variable sprawl to application callers.
6. External tool adapter: use MCP and CLI-Hub-discovered CLIs through narrow adapters rather than letting tool-specific commands spread through agents or UI code.
7. CLI-first harness adapter: expose repeatable Ariadne operations as Python CLIs with JSON output when that avoids complicated UI or bespoke integration code.

## Guardrails

- Do not split modules just because files approach a small line count; use the deletion test and require real leverage.
- Prefer a single deep module over duplicated shallow helpers when workflows share invariants.
- Record rejected or load-bearing architectural decisions as ADRs before they become folklore.
- Do not build a UI for operations that are better expressed as deterministic CLI commands plus UI-triggered review/preview.
