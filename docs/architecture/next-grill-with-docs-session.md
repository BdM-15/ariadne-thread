# Next Grill-With-Docs Session Prep

Date: 2026-05-19
Purpose: prepare the next conversation to choose the vertical epic after completed Artifact Assembly Foundation.

## Current Baseline

- Phase 0, first-slice domain/storage, Quick Capture Knowledge Processing, Document Intake Command Surface, Federal Data MCP Foundation, USAspending Recompete Intelligence Intake, SAM.gov Enrichment Profile, Capability Run Foundation, Knowledge Layer Foundation, Capture Research Enrichment, issue #60 local-dev provider stack, and Artifact Assembly Foundation are complete and merged to `main`.
- The current runtime is a local FastAPI Command Center on port `9622`; `9621` remains reserved for Project Theseus.
- The latest completed validation: `uv run ruff check src tests` and `uv run pytest -q` with 275 tests passing.
- The local-dev provider stack can start selected local providers plus Ariadne through `scripts/start-local-dev.ps1`; `scripts/smoke-local-dev.ps1` live-validates Crawl4AI, SearXNG JSON search, and Ariadne's approved `crawl4ai_local` and `searxng_local` smoke endpoints.
- Artifact Assembly Foundation now provides Artifact Source Packages from Opportunity Knowledge Context, deterministic Milestone Decision Briefing Packet drafts, typed source-backed Artifact Content Blocks, block-level review decisions, preview/export readiness metadata, a FastAPI Artifact Draft Command Surface, and validation that no final exported files or automatic trusted downstream writes are produced.
- Capture Research Enrichment now provides bounded Capture Research Briefs, source-profile refs, provider readiness/smoke checks, fake and approved provider-backed Web Source Collection, Seller Capability Baseline refs, Requirements Fit Analysis, Competitive Gap Analysis, selected capture-lens analyses, downstream candidate projection, candidate review decisions, and a reviewed Capture Research Command Surface.
- Knowledge Layer Foundation provides deterministic on-demand Structured Knowledge Index projection, Opportunity Knowledge Context, and reviewable Next Action Recommendations that can create Action Plan work only through human review.
- Capability Run Foundation provides durable Capability Runs, Capability Run Outputs, Capability Reasoning Views, deterministic Capability Catalog validation runs, optional Local Admin Model readiness/probe runs, and review decisions without automatic trusted downstream writes.
- Federal-data sources remain behind Federal Data Capabilities. USAspending and SAM.gov are product-integrated; GSA CALC, BLS, GSA Per Diem, eCFR, Federal Register, and Regulations.gov remain registered/deferred until selected by a future slice.
- Hermes runtime, semantic retrieval/RAG, graph visualization, MinerU, RAGAnything, LightRAG, huashu-design/artifact rendering, parser integrations, automatic trusted writes, and broad persistent storage remain deferred.

## Session Inputs

- `PRD.md` for product source of truth and next build gate.
- `CONTEXT.md` for domain language and relationship rules.
- `README.md` for the current local run and local provider stack workflow.
- `.env.example` for the public secret-free configuration contract.
- `docs/adr/0006-document-intake-extraction-boundary.md` for parser/retrieval boundary constraints.
- `docs/adr/0007-upstream-federal-data-mcps.md` for the upstream MCP integration boundary.
- `docs/adr/0008-artifact-assembly-foundation.md` for the source-package-first, block-review-first artifact boundary.
- `docs/architecture/document-intake-command-surface-plan.md` for the completed Document Intake implementation trail.
- `docs/architecture/federal-data-mcp-foundation-plan.md` for completed Federal Data implementation trail and deferred enrichment paths.
- `docs/architecture/sam-gov-enrichment-plan.md` for completed SAM.gov implementation trail and source-boundary decisions.
- `docs/architecture/capability-run-foundation-plan.md` for completed Capability Run implementation trail, Capability Run Store, Capability Provenance, Capability Reasoning View, review-gated output, and Graduated Autonomy constraints.
- `docs/architecture/knowledge-layer-foundation-plan.md` for completed Structured Knowledge Index, Opportunity Knowledge Context, and Next Action Recommendation boundaries.
- `docs/architecture/capture-research-enrichment-plan.md` for completed Capture Research Enrichment provider, source, baseline, lens, downstream-candidate, and Command Surface boundaries.
- `docs/architecture/artifact-assembly-foundation-plan.md` for completed Artifact Assembly implementation trail, Artifact Source Package, Artifact Draft, Artifact Content Block, block-review, readiness, and deferred renderer/export boundaries.
- `docs/architecture/future-integration-strategy.md` for future Hermes, graph, parser, RAG, artifact, external API, and advanced skill integration rules.
- The running Command Center at `http://127.0.0.1:9622` when the local runtime is active.

## Decisions To Force Next

- Which vertical epic follows Artifact Assembly Foundation.
- Whether the next slice is primarily a Command Center UI workflow, CLI-first harness, external integration adapter, Capability Run executor expansion, artifact/export path, parser/retrieval path, graph sensemaking path, or a narrow combination.
- What concrete tracer object starts the workflow and what durable Ariadne product object receives the output: Evidence Item, Packet Field Answer, Action Plan Item, Risk Register Item, Call Plan signal, Capability Run Output, Research Finding, Artifact draft, Improvement Proposal, or Knowledge Context projection.
- Whether the local provider stack should stay as infrastructure support only or become part of a new user-facing workflow.
- Whether the completed Artifact Assembly layer should stay as renderer-neutral preparation for another slice or become the input to a first renderer/export workflow.
- What remains explicitly deferred so the next slice does not become a broad platform sweep.
- Whether a new ADR is needed because the decision is hard to reverse, surprising without context, or trade-off driven.

## Candidate Directions

- BLS, GSA CALC, or GSA Per Diem pricing/labor context from NAICS, place-of-performance, labor category, or role signals, ideally feeding price-to-win, workload, action-plan, and risk candidates.
- Focused Bidder Comparison Chart preparation using accepted Capture Research outputs, while preserving the current boundary that no BCC artifact exists until selected.
- Artifact Renderer first slice for preview/export of reviewed Artifact Draft content into DOCX, XLSX, presentation, or huashu-design downstream work, while preserving Artifact Assembly as source of truth.
- Project Theseus solicitation parser adapter through the Extraction Bundle contract, scoped to reviewable solicitation entities, requirements, evaluation criteria, source spans, and parser limitations.
- Knowledge Graph sensemaking over accepted evidence, opportunities, action items, packet answers, document-intake outputs, PIID/SAM.gov profiles, Capture Research runs, and reusable insights.
- Hermes operational learning over repeated review decisions, Capability Runs, Capture Research runs, and accepted/rejected recommendations, constrained to Improvement Proposals.
- Capability Studio progression beyond run history/detail/reasoning views, such as artifact library, validation-status promotion, executor diagnostics, or richer review workflows.
- Deeper Risk Register or Call Plan promotion workflows from review-gated candidates already produced by Document Intake, SAM.gov, Knowledge Context, and Capture Research.
- Live source-provider ergonomics and provider-backed collection improvements only if scoped as a product workflow with explicit approval, provenance, limits, and reviewable outputs.

## Session Notes

- Risk Register Item and Risk Response Plan remain important downstream Ariadne concepts, but a standalone Risk Register command surface is too narrow unless the slice also proves how risk signals are populated from source material, capability runs, federal data, call plans, packet gaps, or reviewed Capture Research outputs.
- The next slice should favor an upstream population path or execution structure that can feed multiple product objects rather than only refining one artifact shape.
- Microsoft Agent Framework is accepted only as a candidate future Hermes or multi-agent workflow runtime adapter. Do not make it the focus of the next slice or add it as a dependency until Ariadne has a concrete runtime problem that existing skills, CLI harnesses, MCP adapters, local providers, and Python modules cannot handle cleanly.
- CLI-Anything should help when a capability is repeatable, batchable, tool-facing, or agent-facing and benefits from deterministic JSON output. Treat it as one executor style under Capability Runs, not as the whole product workflow.
- Future model-assisted capability runs should preserve user-facing rationale through Model Rationale Summaries and Capability Reasoning Views. Do not make raw hidden model reasoning a required durable artifact.
- Capture Research outputs remain reviewable candidates until accepted or routed. BCC-ready notes are inputs for later Bidder Comparison Chart work, not generated BCC rows, slides, scores, or artifacts.
- Artifact Drafts are renderer-neutral reviewed structures. `export_ready` means a future renderer may consume the draft; it does not mean Ariadne has generated a DOCX, XLSX, presentation, visual, or huashu artifact.
- Live source-provider calls require explicit approval or a future approved autonomy policy. Page render must not trigger provider calls.
- The local-dev stack selected only Crawl4AI and SearXNG. Ollama remains optional/external through `OLLAMA_HOST`; Neo4j, Postgres, vector databases, graph databases, LightRAG, RAGAnything, and broad persistent storage remain out of scope until selected by ADR/PRD.

## Guardrails

- Run `grill-with-docs` before implementation for any Hermes, graph visualization, MinerU, huashu-design, RAG/retrieval, external API, advanced skill, artifact rendering, or third-party capability slice.
- Keep the next epic vertical and reviewable.
- Preserve the Extraction Bundle boundary for parser and retrieval tools.
- Preserve the Federal Data Capability boundary for upstream 1102 MCPs; do not create duplicate Ariadne MCP servers for those sources.
- Preserve Capture Research boundaries: bounded briefs, explicit source limits, provider provenance, fake/live source-mode honesty, and reviewable downstream candidates.
- Preserve Artifact Assembly boundaries: explicit source packages before draft generation, typed block schema before renderers, block-level review before readiness claims, no automatic trusted downstream writes, and no final export unless a renderer slice explicitly selects it.
- Keep trusted promotions human-gated.
- Prefer CLI-first harnesses for repeatable, batchable, tool-facing, or agent-facing work with deterministic JSON output.
- Keep the main Command Center command-first: evidence, recommendations, and actions should stay connected.