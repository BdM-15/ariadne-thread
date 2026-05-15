# Phase 0 Architecture Review

Date: 2026-05-15  
Scope: fresh repository before application code

## Current State

- Product source of truth exists in `PRD.md`.
- Domain language exists in `CONTEXT.md`.
- Matt Pocock architecture/setup/write-a-skill, first-principles, skill-creator, and Ariadne UI/UX skills are installed or created project-locally.
- Agent setup docs exist in `AGENTS.md` and `docs/agents/`.
- Live secrets are excluded by `.gitignore`; `.env.example` contains only public configuration shape.

## Deepening Opportunities To Consider Before App Code

1. Capture lifecycle module: expose a small interface around opportunity state, gate transitions, evidence, risks, and next actions instead of scattering Shipley rules across UI components.
2. Knowledge layer adapter: keep LightRAG, embeddings, graph storage, and local vault concerns behind one Ariadne retrieval interface so Theseus-derived behavior can evolve without leaking vendor details.
3. Artifact renderer module: separate artifact intent, preview state, and export adapters so DOCX/XLSX/presentation outputs share one workflow without one oversized renderer.
4. Agent runtime module: define a narrow Hermes execution interface before wiring model providers, local tools, skills, and memory.
5. Environment configuration module: translate `.env` provider settings into typed runtime capabilities without exposing raw Project Theseus variable sprawl to application callers.

## Guardrails

- Do not split modules just because files approach a small line count; use the deletion test and require real leverage.
- Prefer a single deep module over duplicated shallow helpers when workflows share invariants.
- Record rejected or load-bearing architectural decisions as ADRs before they become folklore.
