# Next Grill-With-Docs Session Prep

Date: 2026-05-17
Purpose: prepare the next conversation to choose the vertical epic after the completed Federal Data MCP Foundation + USAspending Recompete Intelligence Intake epic.

## Current Baseline

- Phase 0, first-slice domain/storage, Quick Capture Knowledge Processing, Document Intake Command Surface, and Federal Data MCP Foundation are complete.
- The current runtime is a local FastAPI Command Center on port `9622`; `9621` remains reserved for Project Theseus.
- The latest completed validation: `uv run ruff check src tests` and `uv run pytest -q` with 160 tests passing.
- Federal Data now registers all eight upstream `1102tools/federal-contracting-mcps` servers as manifest-only Federal Data Capabilities.
- USAspending is the first product-integrated federal data source, with PIID lookup/history adapter behavior, persisted PIID Contract Intelligence Profiles, burn posture, vehicle context, deterministic pivots, source-limit gaps, review-gated candidates, Hermes-observable events, and a Command Center demo surface.
- Non-USAspending product workflows remain deferred until selected through a fresh documented slice.

## Session Inputs

- `PRD.md` for product source of truth and next build gate.
- `CONTEXT.md` for domain language and relationship rules.
- `docs/adr/0006-document-intake-extraction-boundary.md` for parser/retrieval boundary constraints.
- `docs/adr/0007-upstream-federal-data-mcps.md` for the upstream MCP integration boundary.
- `docs/architecture/document-intake-command-surface-plan.md` for the completed Document Intake implementation trail.
- `docs/architecture/federal-data-mcp-foundation-plan.md` for the completed Federal Data implementation trail and deferred enrichment paths.
- `docs/architecture/future-integration-strategy.md` for future Hermes, graph, parser, RAG, artifact, external API, and advanced skill integration rules.
- The running Command Center at `http://127.0.0.1:9622` when the local runtime is active.

## Decisions To Force Next

- Which vertical epic follows Federal Data.
- Whether the next slice is primarily Command Center UI workflow, CLI-first harness, external integration adapter, or both.
- Which Ariadne product object receives the output: Evidence Item, Packet Field Answer, Action Plan Item, Risk Register Item, Call Plan signal, Capability Run Output, Artifact draft, or Improvement Proposal.
- What remains explicitly deferred so the next slice does not become a broad platform sweep.
- Whether a new ADR is needed because the decision is hard to reverse, surprising without context, or trade-off driven.

## Candidate Directions

- SAM.gov entity and opportunity enrichment from UEI or solicitation pivots in PIID profiles.
- BLS, GSA CALC, or GSA Per Diem pricing and labor context from NAICS, place-of-performance, or role signals.
- Firecrawl or web enrichment seeded by customer, incumbent, office, vehicle, or solicitation pivots.
- Focused competitor, customer, subaward, or vehicle profile workflow built from accepted PIID profile content.
- Artifact Renderer export from accepted PIID profile content into DOCX, XLSX, presentation, or huashu-design downstream work.
- Hermes operational learning over repeated PIID profile runs and review decisions.
- Capability Studio progression from read-only catalog toward tested capability runs, provenance, artifacts, and validation status.
- Knowledge Graph sensemaking over accepted evidence, opportunities, action items, packet answers, document-intake outputs, and PIID profiles.
- Project Theseus solicitation parser adapter through the Extraction Bundle contract.
- Deeper Risk Register or Call Plan promotion workflows from review-gated candidates.

## Guardrails

- Run `grill-with-docs` before implementation for any Hermes, graph visualization, MinerU, huashu-design, RAG/retrieval, external API, advanced skill, artifact rendering, or third-party capability slice.
- Keep the next epic vertical and reviewable.
- Preserve the Extraction Bundle boundary for parser and retrieval tools.
- Preserve the Federal Data Capability boundary for upstream 1102 MCPs; do not create duplicate Ariadne MCP servers for those sources.
- Keep trusted promotions human-gated.
- Prefer CLI-first harnesses for repeatable, batchable, tool-facing, or agent-facing work with deterministic JSON output.
- Keep the main Command Center command-first: evidence, recommendations, and actions should stay connected.
