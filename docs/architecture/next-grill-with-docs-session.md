# Next Grill-With-Docs Session Prep

Date: 2026-05-17
Purpose: prepare the next conversation to choose the vertical epic after the completed SAM.gov Enrichment Profile epic.

## Current Baseline

- Phase 0, first-slice domain/storage, Quick Capture Knowledge Processing, Document Intake Command Surface, Federal Data MCP Foundation, USAspending Recompete Intelligence Intake, and SAM.gov Enrichment Profile are complete.
- The current runtime is a local FastAPI Command Center on port `9622`; `9621` remains reserved for Project Theseus.
- The latest completed validation: `uv run ruff check src tests` and `uv run pytest -q` with 192 tests passing.
- Federal Data now registers all eight upstream `1102tools/federal-contracting-mcps` servers as manifest-only Federal Data Capabilities.
- USAspending is the first product-integrated federal data source, with PIID lookup/history adapter behavior, persisted PIID Contract Intelligence Profiles, burn posture, vehicle context, deterministic pivots, source-limit gaps, review-gated candidates, Hermes-observable events, and a Command Center demo surface.
- SAM.gov is the second product-integrated federal data source, with persisted SAM.gov Enrichment Profiles, Entity Record, Known Opportunity, Opportunity Discovery, and Attachment Intake lanes, source-mode provenance, explicit download approval, Document Intake provenance, saved command surfaces, and review-gated candidates.
- BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, Regulations.gov, Firecrawl/web enrichment, parser integrations, artifact rendering, Hermes runtime, graph visualization, and advanced capability workflows remain deferred until selected through a fresh documented slice.

## Session Inputs

- `PRD.md` for product source of truth and next build gate.
- `CONTEXT.md` for domain language and relationship rules.
- `docs/adr/0006-document-intake-extraction-boundary.md` for parser/retrieval boundary constraints.
- `docs/adr/0007-upstream-federal-data-mcps.md` for the upstream MCP integration boundary.
- `docs/architecture/document-intake-command-surface-plan.md` for the completed Document Intake implementation trail.
- `docs/architecture/federal-data-mcp-foundation-plan.md` for the completed Federal Data implementation trail and deferred enrichment paths.
- `docs/architecture/sam-gov-enrichment-plan.md` for the completed SAM.gov implementation trail and source-boundary decisions.
- `docs/architecture/future-integration-strategy.md` for future Hermes, graph, parser, RAG, artifact, external API, and advanced skill integration rules.
- The running Command Center at `http://127.0.0.1:9622` when the local runtime is active.

## Decisions To Force Next

- Which vertical epic follows SAM.gov.
- Whether the next slice is primarily Command Center UI workflow, CLI-first harness, external integration adapter, or both.
- Which Ariadne product object receives the output: Evidence Item, Packet Field Answer, Action Plan Item, Risk Register Item, Call Plan signal, Capability Run Output, Artifact draft, or Improvement Proposal.
- What remains explicitly deferred so the next slice does not become a broad platform sweep.
- Whether a new ADR is needed because the decision is hard to reverse, surprising without context, or trade-off driven.

## Candidate Directions

- BLS, GSA CALC, or GSA Per Diem pricing and labor context from NAICS, place-of-performance, or role signals.
- Firecrawl or web enrichment seeded by customer, incumbent, office, vehicle, or solicitation pivots.
- Focused competitor, customer, subaward, or vehicle profile workflow built from accepted PIID profile content.
- Artifact Renderer export from accepted PIID profile content into DOCX, XLSX, presentation, or huashu-design downstream work.
- Hermes operational learning over repeated PIID profile runs and review decisions.
- Capability Studio progression from read-only catalog toward tested capability runs, provenance, artifacts, and validation status.
- Knowledge Graph sensemaking over accepted evidence, opportunities, action items, packet answers, document-intake outputs, and PIID profiles.
- Project Theseus solicitation parser adapter through the Extraction Bundle contract.
- Deeper Risk Register or Call Plan promotion workflows from review-gated candidates.
- Follow-on SAM.gov polish only if scoped as a separate vertical slice, such as live-run ergonomics, richer attachment review, or deeper opportunity-to-plan promotion.

## Guardrails

- Run `grill-with-docs` before implementation for any Hermes, graph visualization, MinerU, huashu-design, RAG/retrieval, external API, advanced skill, artifact rendering, or third-party capability slice.
- Keep the next epic vertical and reviewable.
- Preserve the Extraction Bundle boundary for parser and retrieval tools.
- Preserve the Federal Data Capability boundary for upstream 1102 MCPs; do not create duplicate Ariadne MCP servers for those sources.
- Keep trusted promotions human-gated.
- Prefer CLI-first harnesses for repeatable, batchable, tool-facing, or agent-facing work with deterministic JSON output.
- Keep the main Command Center command-first: evidence, recommendations, and actions should stay connected.
