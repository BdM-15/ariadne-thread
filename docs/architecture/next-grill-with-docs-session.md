# Next Grill-With-Docs Session Prep

Date: 2026-05-16  
Purpose: choose the next vertical epic after the completed Document Intake Command Surface.

## Current Baseline

- Phase 0, the first-slice domain/storage epic, Quick Capture Knowledge Processing, and the Document Intake Command Surface first vertical epic are complete.
- The current runtime is a local FastAPI Command Center on port `9622`; `9621` remains reserved for Project Theseus.
- The latest completed validation before merge: `uv run ruff check src tests` and `uv run pytest -q` with 116 tests passing.
- Document Intake now proves the Extraction Bundle boundary before any Theseus, MinerU, OCR, multimodal, RAGAnything, LightRAG, or retrieval integration.

## Session Inputs

- `PRD.md` for product source of truth and next build gate.
- `CONTEXT.md` for domain language and relationship rules.
- `docs/adr/0006-document-intake-extraction-boundary.md` for parser/retrieval boundary constraints.
- `docs/architecture/document-intake-command-surface-plan.md` for the completed implementation trail.
- The running Command Center demo thread at `http://127.0.0.1:9622` when the local runtime is active.

## Decisions To Force

- Which one vertical epic should come next?
- Is the next epic primarily Command Center UI/product workflow, CLI-first harness work, Capability Studio, or external integration?
- Does the next epic require a new ADR before code?
- What existing behavior should become the tracer bullet and acceptance demo?
- What remains explicitly deferred so the next epic does not become a platform sweep?

## Candidate Directions

- Command Center UI polish or Next.js shell migration over the existing FastAPI-proven behavior.
- Capability Studio progression from read-only catalog toward tested capability runs and provenance.
- Knowledge Layer and retrieval architecture, including whether LightRAG or RAGAnything belong behind a narrow adapter boundary.
- Graph Sensemaking Mode over accepted Ariadne knowledge and projections.
- Project Theseus solicitation parser adapter through the Extraction Bundle contract.
- Artifact Renderer or huashu-design export path for Living Briefing Packet outputs.
- Hermes operational learning and improvement proposals over saved product sessions.
- Deeper Risk Register or Call Plan promotion workflows from review-gated candidates.

## Guardrails

- Keep the next epic vertical and reviewable.
- Preserve the Extraction Bundle boundary for parser and retrieval tools.
- Keep trusted promotions human-gated.
- Prefer CLI-first harnesses for repeatable, batchable, tool-facing, or agent-facing work with deterministic JSON output.
- Keep the main Command Center command-first: evidence, recommendations, and actions should stay connected.