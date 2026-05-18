# Next Grill-With-Docs Session Prep

Date: 2026-05-18
Purpose: prepare the next conversation to choose the vertical epic after the completed Capability Run Foundation epic.

## Current Baseline

- Phase 0, first-slice domain/storage, Quick Capture Knowledge Processing, Document Intake Command Surface, Federal Data MCP Foundation, USAspending Recompete Intelligence Intake, SAM.gov Enrichment Profile, and Capability Run Foundation are complete.
- The current runtime is a local FastAPI Command Center on port `9622`; `9621` remains reserved for Project Theseus.
- The latest completed validation: `uv run ruff check src tests` and `uv run pytest -q` with 209 tests passing.
- Federal Data now registers all eight upstream `1102tools/federal-contracting-mcps` servers as manifest-only Federal Data Capabilities.
- USAspending is the first product-integrated federal data source, with PIID lookup/history adapter behavior, persisted PIID Contract Intelligence Profiles, burn posture, vehicle context, deterministic pivots, source-limit gaps, review-gated candidates, Hermes-observable events, and a Command Center demo surface.
- SAM.gov is the second product-integrated federal data source, with persisted SAM.gov Enrichment Profiles, Entity Record, Known Opportunity, Opportunity Discovery, and Attachment Intake lanes, source-mode provenance, explicit download approval, Document Intake provenance, saved command surfaces, and review-gated candidates.
- Capability Run Foundation adds a local Capability Run Store, deterministic Capability Catalog validation runs, optional Local Admin Model readiness probe runs, reviewable Capability Run Outputs, output review decisions without trusted downstream writes, Capability Studio run history/detail/Capability Reasoning Views, and Command Center launch/review entry points.
- BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, Regulations.gov, Firecrawl/web enrichment, parser integrations, artifact rendering, Hermes runtime, graph visualization, and advanced capability workflows remain deferred until selected through a fresh documented slice.

## Session Inputs

- `PRD.md` for product source of truth and next build gate.
- `CONTEXT.md` for domain language and relationship rules.
- `docs/adr/0006-document-intake-extraction-boundary.md` for parser/retrieval boundary constraints.
- `docs/adr/0007-upstream-federal-data-mcps.md` for the upstream MCP integration boundary.
- `docs/architecture/document-intake-command-surface-plan.md` for the completed Document Intake implementation trail.
- `docs/architecture/federal-data-mcp-foundation-plan.md` for the completed Federal Data implementation trail and deferred enrichment paths.
- `docs/architecture/sam-gov-enrichment-plan.md` for the completed SAM.gov implementation trail and source-boundary decisions.
- `docs/architecture/capability-run-foundation-plan.md` for the completed Capability Run implementation trail, Capability Run Store, Capability Provenance, Capability Reasoning View, review-gated output, and Graduated Autonomy constraints.
- `docs/architecture/future-integration-strategy.md` for future Hermes, graph, parser, RAG, artifact, external API, and advanced skill integration rules.
- The running Command Center at `http://127.0.0.1:9622` when the local runtime is active.

## Decisions To Force Next

- Which vertical epic follows Capability Run Foundation.
- Whether the next slice is primarily Command Center UI workflow, CLI-first harness, external integration adapter, Capability Run executor expansion, or both.
- Which Ariadne product object receives the output: Evidence Item, Packet Field Answer, Action Plan Item, Risk Register Item, Call Plan signal, Capability Run Output, Artifact draft, or Improvement Proposal.
- What remains explicitly deferred so the next slice does not become a broad platform sweep.
- Whether a new ADR is needed because the decision is hard to reverse, surprising without context, or trade-off driven.

## Session Notes

- Risk Register Item and Risk Response Plan remain important downstream Ariadne concepts, but a standalone Risk Register command surface is too narrow as the immediate next epic unless the slice also proves how risk signals are populated from source material, capability runs, federal data, call plans, packet gaps, or other reviewed inputs.
- The next slice should favor an upstream population path or execution structure that can feed multiple product objects, including Risk Register Items, rather than only refining the Risk Register artifact shape.
- Microsoft Agent Framework is accepted only as a candidate future Hermes or multi-agent workflow runtime adapter. Do not make it the focus of the next slice or add it as a dependency until Ariadne has a concrete runtime problem that the existing skills, CLI harnesses, MCP adapters, and Python modules cannot handle cleanly.
- The selected next epic direction is **Capability Run Foundation + Assisted Execution Command Surface**. It should create durable Capability Run and Capability Run Output records before adding new external integrations or autonomous agent runtimes.
- CLI-Anything should help when a capability is repeatable, batchable, tool-facing, or agent-facing and benefits from deterministic JSON output. In this epic it should be treated as one executor style under Capability Runs, not as the whole product workflow.
- Project Theseus patterns for source tracing, skill-run chain tracing, and reasoning views are relevant inspiration for Ariadne's Capability Provenance and Capability Reasoning View. Ariadne should show why an output exists, what sources and assumptions support it, what logic or transformations were applied, what gaps remain, and what review decision is needed, without copying Theseus UI/runtime structure.
- The first required tracer bullet should be a deterministic **Capability Catalog validation run** that works without Ollama, hosted models, external APIs, or autonomous agents. A second optional tracer can run a **Local Admin Model readiness/probe** through existing `OLLAMA_HOST`, `LOCAL_DAILY_MODEL`, and `LOCAL_ADMIN_MODEL_TIMEOUT_SECONDS` settings, recording `used`, `unavailable`, or `invalid_response` style outcomes as Capability Run provenance rather than making Ollama availability required for the epic.
- Future model-assisted capability runs should preserve user-facing rationale through **Model Rationale Summaries** and **Capability Reasoning Views**. Do not make raw hidden model reasoning a required durable artifact; Ariadne's trusted record should be evidence, sources, assumptions, confidence, gaps, transformations, outputs, and human review decisions.
- The first epic should use a separate local-first **Capability Run Store**, likely under `.ariadne/capability-runs`, because the Capability Catalog records what can run, the Evidence Store records trusted support, and the Capability Run Store records execution history, outputs, review decisions, iterations, and provenance.
- First-epic Capability Run Outputs should land in review and should not automatically create trusted downstream records. Later **Graduated Autonomy** can allow selected low-risk automatic handling after repeated reliability, provenance quality, reversibility, sensitivity limits, and user-approved autonomy rules are proven. Hermes may recommend those changes as Improvement Proposals, but it must not silently expand its own permissions.
- First-epic Capability Run Outputs may carry autonomy recommendation metadata such as `review_required`, `ask_before_running`, or `safe_to_auto_handle_later`, but Ariadne should not act on those recommendations automatically in this slice.
- The first UI shape should be Capability Studio first, with a lightweight Command Center entry point. The Command Center should help the user efficiently launch, review, route, and complete work with minimal clicks, while Capability Studio exposes run history, validation detail, provenance, reasoning views, and executor diagnostics for deeper inspection.
- The first acceptance demo should show the Command Center surfacing a Capability Catalog validation action; the user launching it; Ariadne creating a Capability Run in the Capability Run Store; deterministic local validation producing Capability Run Outputs with provenance and autonomy recommendation metadata; Capability Studio showing run history and a Capability Reasoning View; the Command Center surfacing outputs needing review; and the user accepting, discarding, or routing one output without automatic trusted downstream writes.
- Accepted implementation order: build the Capability Run domain model and Capability Run Store first; add the deterministic Capability Catalog validation executor second; add optional Local Admin Model readiness/probe third; add review decisions fourth; surface Capability Studio run history/detail/reasoning views plus lightweight Command Center entries fifth; then update docs and automated coverage.
- No new ADR is needed for the Capability Run Foundation slice because it follows existing local-first, Capability Module, and review-gated-promotion decisions. `docs/architecture/capability-run-foundation-plan.md` records the selected plan. Create an ADR only if a later decision adopts an agent runtime framework, changes the storage engine, enables automatic trusted writes, or makes a graph/workflow engine the Capability Run runtime.

## Candidate Directions

- BLS, GSA CALC, or GSA Per Diem pricing and labor context from NAICS, place-of-performance, or role signals.
- Firecrawl or web enrichment seeded by customer, incumbent, office, vehicle, or solicitation pivots.
- Focused competitor, customer, subaward, or vehicle profile workflow built from accepted PIID profile content.
- Artifact Renderer export from accepted PIID profile content into DOCX, XLSX, presentation, or huashu-design downstream work.
- Hermes operational learning over repeated PIID profile runs and review decisions.
- Capability Studio progression beyond the first run history/detail/reasoning view, such as artifact library, validation-status promotion, executor diagnostics, or richer review workflows.
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
