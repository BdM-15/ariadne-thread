# Phase 0 Architecture Review

Date: 2026-05-15  
Scope: fresh repository before application code

## Current State

- Product source of truth exists in `PRD.md`.
- Domain language exists in `CONTEXT.md`.
- Matt Pocock architecture/setup/write-a-skill, first-principles, skill-creator, Ariadne UI/UX, and CLI-Anything builder skills are installed or vendored project-locally. CLI-Hub meta-skill is optional discovery only.
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
6. External tool adapter: use MCP and, when helpful, CLI-Hub-discovered CLIs through narrow adapters rather than letting tool-specific commands spread through agents or UI code.
7. CLI-first harness adapter: expose repeatable Ariadne operations as Python CLIs with JSON output when that avoids complicated UI or bespoke integration code.

## Accepted First Build Slice

Build a thin vertical slice that establishes the load-bearing structure before broad feature work:

- Opportunity shell with lifecycle state, entry context, and core capture workstreams.
- Quick Capture Inbox for raw notes, thoughts, meeting fragments, pasted text, and uploaded material.
- Pydantic-validated Evidence Item model backed by a local-first Evidence Store adapter.
- Living Briefing Packet skeleton with packet readiness, briefing view, coverage view, and evidence/gap status.
- Capture Action Plan skeleton with outcome-level tasks and expandable execution details.
- Read-only Capability Catalog in the advanced Capability Studio surface.

Implementation order: build the Python domain/storage layer first, then put a thin Command Center UI shell on top immediately after. Treat this as a days-scale sequence, not a weeks-or-months architecture phase.

Initial package shape: use one `src/ariadne/` package with deep internal modules for `config`, `opportunities`, `evidence`, `packets`, `actions`, and `capabilities`. Do not split into many top-level packages until the deletion test shows a real seam with leverage and locality.

Test approach: use the `tdd` skill from the start of the first slice. Write behavior tests through public interfaces, one tracer bullet at a time, then implement the minimum code needed to pass. Focus initial tests on opportunity creation, evidence validation/storage, packet readiness, action-plan item creation, and read-only capability catalog discovery. Do not write all tests first or couple tests to internal implementation details.

First tracer bullet: prove that a user can create an Opportunity that starts at a later Lifecycle State because of an Entry Context, while still preserving the standard Core Capture Workstreams and Backfill Needs for earlier work that may need to be revisited.

First public interface: start with an application-facing `create_opportunity(...)` function that accepts an opportunity name and Entry Context, then returns an Opportunity with lifecycle state, entry context, core capture workstreams, and backfill needs initialized. Keep nested Pydantic models available, but do not require callers to manually assemble every internal object for the first behavior.

Defer full Hermes autonomy, full RAG/graph implementation, third-party skill installation, artifact rendering, and external tool integrations until the first slice proves the product shape and interfaces.

Do not let that deferral make those integrations vague. Use `docs/architecture/future-integration-strategy.md` to preserve the planned attachment points for Hermes, graph visualization, MinerU, huashu-design, RAG, external APIs, and advanced skills while keeping the first slice small.

## Guardrails

- Do not split modules just because files approach a small line count; use the deletion test and require real leverage.
- Prefer a single deep module over duplicated shallow helpers when workflows share invariants.
- Record rejected or load-bearing architectural decisions as ADRs before they become folklore.
- Do not build a UI for operations that are better expressed as deterministic CLI commands plus UI-triggered review/preview.
