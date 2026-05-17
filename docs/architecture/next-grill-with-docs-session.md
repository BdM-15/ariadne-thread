# Next Grill-With-Docs Session Prep

Date: 2026-05-16  
Purpose: record the completed planning outcome for the next vertical epic after the completed Document Intake Command Surface.

## Session Outcome

The next selected vertical epic is **Federal Data MCP Foundation + USAspending Recompete Intelligence Intake**. See `docs/architecture/federal-data-mcp-foundation-plan.md` and ADR 0007.

The selected approach registers all eight upstream `1102tools/federal-contracting-mcps` servers as manifest-only Federal Data Capabilities, while deeply integrating USAspending first through a structured PIID Contract Intelligence Profile workflow.

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

## Decisions Forced

- Next epic: Federal Data MCP Foundation + USAspending Recompete Intelligence Intake.
- Slice type: external integration foundation plus a product workflow command surface.
- ADR: ADR 0007 records the upstream 1102tools MCP integration decision.
- Tracer bullet: one PIID becomes a structured USAspending-backed PIID Contract Intelligence Profile with review-gated candidates.
- Explicit deferrals: full workflows for the other seven MCPs, Firecrawl/web enrichment, 1102 deliverable skills, skill chaining/LangGraph, Hermes runtime, artifact rendering, and Next.js migration.

## Candidate Directions Considered

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
