# Next Grill-With-Docs Session Prep

Date: 2026-05-21
Purpose: prepare the next conversation to start MVP-3: Capture Work Product Loop.

## Current Baseline

- Phase 0 through MVP-1C are complete and merged to `main`.
- MVP-2: AI Usage Layer + Skills Integration is complete and merged to `main`.
- Current validation after MVP-2 completion: `uv run ruff check src tests` passed and `uv run pytest -q` passed with 402 tests.
- Local runtime remains FastAPI on `http://127.0.0.1:9622`; port `9621` remains reserved for Project Theseus.
- Next.js Command Center exists as a production-shaped tracer and MVP review surface, but full production UI hardening remains MVP-4.
- Local Admin Model readiness is wired through guarded Capability Runs. Hosted reasoning model readiness is wired but disabled by default through `HOSTED_REASONING_MODEL_ENABLED=false`.
- MVP-2 added explicit model-use contracts for capture need analysis, packet synthesis support, call/engagement prep, value proposition/messaging, research brief creation, output review summaries, and artifact-block drafting.
- Focused runnable skills are present: `data-table-profiler`, `anomaly-route-recommender`, `incumbent-award-history-brief`, `compliance-spine-planner`, `win-theme-synthesizer`, `competitive-gap-route-hint`, and `subcontractor-assumption-list`.
- Opportunity Activation now exposes route cards for source-backed answer, source-profile lookup, model synthesis, customer call-plan prep, and approved low-risk skill-chain execution.
- No LangGraph runtime, parser/RAG/graph/rendering expansion, broad Theseus mega-skill copy, or automatic trusted downstream writes were introduced in MVP-2.

## Session Inputs

- `PRD.md` for product source of truth and MVP-3 selected build direction.
- `CONTEXT.md` for domain language and relationship rules.
- `docs/architecture/mvp-2-skill-decomposition-map.md` for completed focused-skill map and remaining dependency gates.
- `docs/architecture/opportunity-activation-field-matrix-plan.md` for Activation Matrix and packet-field route spine.
- `docs/architecture/command-center-work-modes-ia-plan.md` for pulse/router vs focused Work Mode boundaries.
- `docs/architecture/production-command-center-ui-plan.md` for production-shaped UI tracer context, with MVP-4 hardening still deferred.
- `docs/architecture/capability-run-foundation-plan.md` for Capability Run Store, reviewable outputs, provenance, and Graduated Autonomy constraints.
- `docs/architecture/artifact-assembly-foundation-plan.md` for Artifact Source Package, Artifact Draft, Artifact Content Block, review, and renderer deferral boundaries.
- `docs/architecture/capture-research-enrichment-plan.md` for source findings, research lenses, seller baseline, downstream candidates, and review boundaries.
- `docs/architecture/future-integration-strategy.md` for future Hermes, graph, parser, RAG, artifact, external API, and advanced skill integration rules.
- `.env.example` for public secret-free model/provider config shape.

## MVP-3 Decision To Force

Choose the first work-product loop tracer. It should start from one reviewed or review-ready AI/skill/research route output and prove that Ariadne can improve concrete capture work, not only show capability inventory.

Force these choices early:

- Which work product gets first improvement: Living Milestone Decision Briefing Packet, Capture Action Plan, call/engagement prep, risk/follow-up candidate, or Artifact Draft context.
- Which existing output starts the tracer: Packet Field route output, focused skill output, Capability Run Output, Capture Research candidate, Source Profile signal, or Knowledge Context recommendation.
- What review object mediates the change: Work Product Delta, Packet Field Answer candidate, Action Plan recommendation, Call Plan signal, Risk Register candidate, or Artifact Content Block update.
- What gets persisted, what remains review-only, and what user action accepts or rejects the change.
- How the Command Center shows before/after work-product state without broad MVP-4 UI hardening.
- What remains deferred: final renderer/export, solicitation parser integration, RAG/graph runtime, Hermes runtime, external API expansion, broad autonomous planning, and automatic trusted writes.

## Candidate MVP-3 Tracers

1. Living Packet update loop. Use a reviewed Capability Run Output or skill output to propose packet-field answer updates, assumptions, gaps, risks, recommendations, source support, and readiness deltas.
2. Action Plan update loop. Route reviewed AI/skill/research output into outcome-level Action Plan recommendations with evidence, rationale, urgency, and follow-up state.
3. Call/engagement prep loop. Build a practical call-plan candidate from Opportunity Knowledge Context, customer/research findings, value proposition outputs, and unresolved packet gaps.
4. Risk/follow-up route loop. Turn competitive, workload, teaming, price, or source-limitation signals into Risk Register or follow-up candidates without building the full risk product surface first.
5. Artifact Draft refresh loop. Reassemble Artifact Source Packages and Artifact Draft sections after packet/action/call improvements so artifact readiness visibly improves without final renderer/export work.

## Recommended First Slice

Start packet-first but make the loop touch at least one adjacent product object.

Suggested tracer:

1. Pick one reviewed or review-ready output, such as `win-theme-synthesizer`, `competitive-gap-route-hint`, or `anomaly-route-recommender`.
2. Create a reviewable Work Product Delta that states proposed changes to the Living Packet plus linked Action Plan or call/engagement prep implications.
3. Let user accept, edit, discard, or route each delta.
4. On acceptance, update only the intended trusted record through existing review rules.
5. Recompute packet readiness and artifact source-package freshness so the user sees work-product improvement.

This keeps MVP-3 vertical, proves value, and avoids turning the slice into UI hardening or renderer work.

## Guardrails

- Run `grill-with-docs` before implementation if MVP-3 crosses into Hermes, graph visualization, MinerU, huashu-design, RAG/retrieval, external APIs, advanced skills, artifact rendering, or third-party capability installation.
- Preserve source refs, model/capability provenance, assumptions, gaps, review decisions, and created/updated work-product links.
- Keep all live hosted/cloud model calls disabled unless explicitly approved through local private config.
- Keep all external calls, broad research runs, paid/credit-spending providers, customer-facing outputs, sensitive actions, deletion, final export, and gate decisions approval-gated.
- Do not introduce LangGraph, parser/RAG/graph/rendering runtime, broad Hermes autonomy, or automatic trusted downstream writes in MVP-3.
- Do not let Capability Studio become the product workflow. Capability details should support the work-product loop, not replace it.
- Keep Command Center Home as pulse/router. Detailed review and before/after work-product state should live in focused Work Modes.