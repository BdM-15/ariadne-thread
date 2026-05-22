# MVP-3 Capture Work Product Loop Plan

Date: 2026-05-22  
Status: implementation complete for first tracer (`#102`-`#106`); MVP-4 polish deferred

## Selected First Tracer

Start MVP-3 with a **packet-first Work Product Delta loop**.

The first concrete tracer should begin from a review-ready `competitive-gap-route-hint` capability output, create reviewable Work Product Deltas, and let the operator apply a Living Packet update plus a linked Action Plan implication without bypassing review gates.

This is the best first tracer because it uses current MVP-2 seams instead of inventing a new broad workflow:

- `competitive-gap-route-hint` is already a focused runnable skill.
- Its output already carries a `field_key`, packet implication, route rationale, assumptions, gaps, source refs, and the review destination `Packet Field Answer candidate`.
- The Living Packet already has a trusted `PacketFieldAnswerStore` and material-refresh activation behavior.
- The Action Plan already has reviewable Next Action Recommendation machinery, even though broad persistent Action Plan management is not the first MVP-3 target.
- Artifact Assembly can refresh from Opportunity Knowledge Context after packet context improves, without invoking final renderers or export.

## Grill-With-Docs Decisions

### Which Work Product Gets First Improvement?

Choose the **Living Milestone Decision Briefing Packet** first.

Reason: the Living Packet is Ariadne's primary Opportunity roadmap, current packet fields already drive activation, and a packet update can visibly improve readiness while staying inside existing review-gated domain rules.

### Which Existing Output Starts The Tracer?

Choose a review-ready **`competitive-gap-route-hint` Capability Run Output**.

Reason: it is narrower and more directly packet-shaped than `win-theme-synthesizer`, less generic than `anomaly-route-recommender`, and less call-plan-specific than `subcontractor-assumption-list`.

### What Review Object Mediates The Change?

Introduce **Work Product Delta** as the review object.

The first delta should describe proposed destination updates such as:

- Living Packet `competition` field candidate.
- Action Plan proof-gap or customer-validation recommendation.
- Optional Artifact Draft context freshness note after the packet update is accepted.

The delta should preserve before/after meaning, source refs, capability output refs, assumptions, gaps, provenance, intended destination, and review state.

### What Gets Persisted?

Persist Work Product Deltas in a narrow local-first store separate from Capability Runs, Packet Field Answers, Next Action Recommendations, and Artifact Drafts.

On review:

- Accept or edit a Living Packet delta -> create or update the intended Packet Field Answer through existing packet-answer review rules.
- Accept or edit an Action Plan implication -> create a reviewable Next Action Recommendation or, when the Action Plan review gate is explicitly invoked, an Action Plan Item through existing recommendation rules.
- Route a delta -> preserve the route decision and target workflow without creating trusted records.
- Discard a delta -> preserve provenance and decision history only.

### How Should UI Show Before/After Without MVP-4 Hardening?

Use the existing production-shaped Next.js Work Modes and keep the Command Center Home as pulse/router.

First visible proof can live in focused Packet and Actions surfaces:

- Packet mode shows pending Work Product Deltas against affected fields.
- Actions mode shows linked action-plan implications or recommendations.
- Artifacts mode shows source-package or draft freshness after accepted packet context improves.
- Home shows compact review counts and routes into the focused mode.

No broad UI polish, new shell architecture, or final artifact editor belongs in this tracer.

## First Implementation Shape

1. Add a small Work Product Delta model and local store.
2. Add a deterministic builder from `competitive-gap-route-hint` Capability Run Output into packet and action-plan deltas.
3. Add review decisions for accept, edit, discard, and route.
4. On accepted packet delta, write the `PacketFieldAnswer` for the targeted field and trigger material-refresh activation.
5. On accepted action implication, create a reviewable Next Action Recommendation first; defer direct trusted Action Plan writes unless the existing recommendation acceptance path is explicitly invoked.
6. Refresh Opportunity Knowledge Context and Artifact Source Package freshness after accepted packet context changes.
7. Show before/after delta state in focused Command Center modes, not as a new toolchain-first page.

## Acceptance Demo For First Tracer

1. One Opportunity has a missing or weak `competition` packet field.
2. Ariadne runs or loads a review-ready `competitive-gap-route-hint` output with source refs, assumptions, and gaps.
3. Ariadne creates Work Product Deltas for the Living Packet and linked Action Plan implication.
4. The operator inspects before/after, provenance, assumptions, gaps, and review destination.
5. Accepting the packet delta creates or updates only the intended Packet Field Answer.
6. Activation refresh shows improved packet coverage/readiness for the current gate.
7. The linked Action Plan implication remains reviewable until explicitly accepted through the action-plan/recommendation gate.
8. Artifact Source Package or draft freshness reflects the improved context, but no DOCX, XLSX, presentation, huashu-design, or final export runs.
9. Rejecting or routing any delta creates no trusted downstream record.

## Completion Evidence (2026-05-22)

- Implementation issues completed and merged to MVP-3 epic branch:
  - `#102` packet-delta apply + activation refresh
  - `#103` action-plan implication review gate via recommendation queue
  - `#104` engagement-prep delta creation/review path
  - `#105` artifact context refresh from accepted packet/action deltas + freshness status UI/API
  - `#106` acceptance demo/runbook + documentation closure
- Scripted acceptance runbook documented in `docs/architecture/mvp-3-capture-work-product-loop-demo.md`.
- Focused Work Mode visibility is now present:
  - Packet mode: living-packet deltas with before/after, refs, assumptions, gaps, review state.
  - Actions mode: action deltas + linked recommendation projections.
  - Engagement mode: call-plan/engagement delta candidates.
  - Artifacts mode: refreshed artifact source-package status, draft freshness, refresh trace refs.
- Review inspectability is present in API and UI for decision metadata, provenance, assumptions, gaps, and created/updated downstream record surfaces.
- Human-review sign-off completed through issue `#107`; current MVP-3 UI/workflow shape accepted for this stage.
- Boundaries remain enforced:
  - No automatic trusted writes on route/discard.
  - No renderer invocation or export execution in MVP-3 flow.

## Deferred

- Final renderer/export, DOCX, XLSX, presentation, or huashu-design work.
- Solicitation parser, RAG, graph runtime, Hermes runtime, LangGraph, or broad autonomous planning.
- External API expansion or live provider execution beyond already-approved source workflows.
- Broad Command Center UI hardening; MVP-4 owns production polish.
- Automatic trusted writes from Capability Run Outputs, Work Product Deltas, research candidates, or artifact blocks.
- Full risk-register product surface and full call-plan product surface, except as reviewable implications or follow-up routes.

## ADR Decision

No ADR is needed for the first tracer. Work Product Delta extends the existing local-first, provenance-rich, review-gated routing pattern. Create an ADR only if a later MVP-3 step adopts a shared workflow engine, changes storage architecture, enables automatic trusted writes, or makes Work Product Delta the universal persistence layer for all product workflows.
