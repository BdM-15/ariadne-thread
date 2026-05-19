# Capture Research Enrichment Plan

Date: 2026-05-19
Status: selected through `grill-with-docs`; implementation in progress

## Selected Epic

Build the **Capture Research Enrichment** vertical slice after the completed Knowledge Layer Foundation epic.

Suggested epic branch: `08-build/capture-research-enrichment`.

Suggested progression branches:

- `08-build/01-capture-research-domain-store`
- `08-build/02-live-source-provider-registry`
- `08-build/03-seller-baseline-and-research-lenses`
- `08-build/04-reviewable-research-candidates`
- `08-build/05-capture-research-command-surface`

The slice should make external research useful inside Ariadne without turning the product into a loose web-scraping tool. It should begin from an opportunity, source-profile gap, packet/action need, or bounded user research request; create a Capture Research Brief; collect public sources through an approved source-provider registry when configured and approved; compare findings against seller baseline knowledge; apply selected capture research lenses; and produce reviewable evidence, packet, action, risk, call-plan, price-to-win, workload, and competitive-gap candidates.

## Product Thesis

Ariadne now has official source profiles, accepted/reference knowledge, deterministic knowledge context, and review-gated action recommendations. The next useful capability is to turn gaps and pivots from that foundation into live capture research.

The product value is not simply web scraping. The value is a bounded research workflow that connects official federal data, Reference Wiki seller knowledge, public web findings, marketing/capture skills, and Shipley-style analysis into concrete capture decisions. A capture professional should be able to ask Ariadne to research a customer, competitor, incumbent, opportunity, teaming gap, or price/workload assumption and receive traceable source findings plus reviewable downstream candidates instead of a detached research report.

## Decisions Resolved

- Build **Capture Research Enrichment** as the next selected vertical epic.
- Treat **Web Enrichment Support** as one lane inside Capture Research Enrichment, not the epic name.
- Use a **source-provider registry** for Web Source Collection rather than a Firecrawl-only adapter.
- Prefer free/local providers first: Crawl4AI for page crawling and extraction, and SearXNG for search discovery when self-hosted.
- Keep SerpApi and Olostep as optional API-backed search/source providers because the user already has keys and expects recurring free monthly usage to cover normal development.
- Keep Firecrawl optional for later paid or higher-quality collection if it proves worth the spend.
- Live source-provider runs are in scope when the relevant provider is configured and the run has explicit user approval or a future approved autonomy policy.
- Automated tests should use fake source-collection adapters and must never present fake output as live source-provider success.
- The first workflow should use a fixed product sequence rather than LangGraph, Hermes runtime, or general skill chaining.
- Future Hermes or agent-coordinated source collection should follow Graduated Autonomy rules: approved source scope, provider priority, free-tier or credit boundaries, provenance, reviewability, and reversible downstream effects.
- Allow **User-Prompted Research Requests** before Ariadne has complete deterministic details, but convert them into bounded **Capture Research Briefs** rather than unbounded web research.
- Prefer deterministic starts when available: PIID gaps, SAM.gov ambiguity, stale signals, source limitations, packet needs, action-plan needs, Opportunity Knowledge Context gaps, or user questions tied to an Opportunity.
- Keep **PIID Contract Intelligence Profiles** and **SAM.gov Enrichment Profiles** as source-specific Source Profiles. They are not subtypes of Capture Research Enrichment.
- Capture Research Enrichment should link to Source Profiles by ID and source-profile element, preserving a small Research Trigger Context snapshot. It should not duplicate award baseline, burn posture, entity matches, opportunity records, or attachment metadata.
- Create a narrow local-first **Capture Research Enrichment Store**. It should persist research briefs, trigger context, source-profile refs, source-collection records, source findings, selected lenses, seller-baseline refs, insight candidates, review decisions, and downstream candidate links.
- Capability Runs can record execution/provenance detail for source providers or skill execution, but the Capture Research Enrichment Store owns the product workflow meaning.
- Use the installed `coreyhaines31/marketingskills` pack as local capability inventory, but select a narrow set of capture-relevant lenses per research brief.
- First useful lenses should include customer research, competitor profiling, product/positioning, sales enablement, price-to-win, workload analysis, and targeted CRO for call-plan or engagement-friction questions. Do not treat the entire marketing pack as one automatic engine.
- Shipley-aligned lenses should prioritize customer understanding, competitive position, discriminators, price-to-win, workload, proof, call-plan, and gate-decision implications before generic marketing growth analysis.
- Competitor analysis should also research or retrieve the seller baseline so Ariadne can compare the user's organization against customer needs, requirements, incumbents, and competitors rather than researching competitors in isolation.
- The first **Seller Capability Baseline** should come from accepted Ariadne knowledge, Capture Reference Context, and the Reference Wiki, including Project Ariadne public-source knowledge. Do not build a new seller-profile editor in this epic.
- Seller baseline usage should show what reference notes, accepted evidence, assumptions, and baseline gaps supported the fit or gap analysis.
- **Requirements Fit Analysis** and **Competitive Gap Analysis** may create fit scores, proof needs, discriminator candidates, vulnerability mitigations, Teaming Partner Needs, packet implications, risk signals, and action-plan items.
- A **Bidder Comparison Chart** is important downstream and may become a Milestone Briefing Packet add-on slide later, but first-slice Capture Research Enrichment should feed BCC-ready evidence and analysis rather than generating BCC artifacts as the core deliverable.
- A Research Summary View is a readable compilation over findings, deterministic context, assumptions, limitations, and reviewable candidates. It is not a separate source-of-truth research object.
- The first review surface should be a **Capture Research Enrichment Command Surface** for one enrichment run, with grouped review sections for Source Findings, Marketing Insight Candidates, Evidence candidates, Packet candidates, Action Plan candidates, Risk Register candidates, Call Plan candidates, price-to-win/workload assumptions, and follow-up routes.
- Defer a global review queue until a later slice explicitly selects it.
- Record these decisions in this architecture plan rather than a new ADR because the slice extends existing local-first, source-profile, Capability Module, review-gated, and external-adapter boundaries. Create an ADR later if Ariadne adopts a new storage engine, workflow graph engine, autonomous live-research policy, or non-review-gated promotion model.

## First Workflow Sequence

The first implementation should prove a fixed sequence:

1. Start from an Opportunity, Source Profile gap/limitation/pivot, Opportunity Knowledge Context gap, Action Plan need, packet need, or bounded user prompt.
2. Create a **Capture Research Brief** with trigger context, source-profile refs, known pivots, research questions, selected lenses, source targets, evidence goals, source limits, and approval basis.
3. Retrieve relevant deterministic context and seller-baseline refs from existing Ariadne stores, Capture Reference Context, and the Reference Wiki.
4. Run fake or live Web Source Collection. Live source-provider runs require configured providers, bounded source targets, approval basis, and source provenance.
5. Convert collected material into **Source Findings** with URL, title/source label, source type, collection time, excerpt or finding text, confidence, limitations, and capability provenance.
6. Apply selected **Capture Research Lenses** to create **Marketing Insight Candidates**, Requirements Fit Analysis signals, Competitive Gap Analysis signals, Price-to-Win assumptions, Burn Rate/Workload implications, Teaming Partner Needs, CRO-style engagement improvements, and BCC-ready notes when appropriate.
7. Project reviewable downstream candidates into existing destinations: Evidence, Living Briefing Packet, Capture Action Plan, Risk Register, Call Plan, follow-up routes, and later BCC or artifact work.
8. Show the run in the **Capture Research Enrichment Command Surface**, with a summary view at the top and review actions on the underlying pieces.

## First Record Shape

The first store should stay narrow and product-specific:

- `research_run_id`
- optional `opportunity_id`
- `status`: planned, awaiting_approval, collecting, interpreting, needs_review, completed, failed, canceled
- `research_brief`
- `research_trigger_context`
- `source_profile_refs`: source profile ID, source profile type, source element ID/key, source element summary
- `user_prompt` when the run begins as a User-Prompted Research Request
- `selected_lenses`
- `seller_baseline_refs`
- `source_collection_records`
- `source_findings`
- `insight_candidates`
- `downstream_candidates`
- `research_summary_view`
- `capability_run_refs` for source-provider or skill executions when applicable
- `review_decisions`
- `created_at` and `updated_at`

Store stable references, concise snapshots, and source provenance by default. Do not store full source profiles, entire crawled websites, secrets, browser credentials, raw hidden reasoning, or broad research corpora in the first workflow store.

## Source Provider And Source-Access Boundary

Live source-provider behavior is part of the first build, but it should be deliberate and traceable:

- Page render must not trigger live source-provider calls.
- User-triggered runs may call configured providers only when the run is approved.
- Local/free-first provider priority should be Crawl4AI for crawling/extraction, SearXNG for search discovery, SerpApi and Olostep as API-backed fallback providers, and Firecrawl as optional paid/later fallback.
- The run must have bounded source targets from the Capture Research Brief, such as explicit public URLs, public domains, or public search targets.
- Each live run must record collection time, source target, capability identity, source mode, approval basis, and source limitations.
- Tests and CI use fake source-collection adapters.
- Live validation is a separate local/manual check when the relevant local service or private key is configured: inspect `GET /api/capture-research/source-providers`, create a bounded Capture Research Run, then call `POST /api/capture-research/runs/{research_run_id}/source-provider-collection` with explicit approval.
- Restricted or logged-in platforms such as LinkedIn or X should not be crawled through hidden credential handling, paywall bypass, or anti-bot bypass. First build should use public pages or user-provided exports/notes/screenshots; future User-Mediated Source Access can explore browser-mediated access with explicit user control.
- Grokipedia or similar public reference sources may be included as source targets when relevant, with provenance and limitations.

## Seller Baseline And Reference Wiki Boundary

The first Seller Capability Baseline should use existing connected knowledge instead of creating a new profile editor:

- accepted Evidence Items and Opportunity Knowledge where relevant;
- Capture Reference Context;
- Project Ariadne public-source Reference Wiki notes;
- capability, vehicle, past-performance, differentiator, certification, relationship, and constraint notes when available;
- explicit baseline gaps when Ariadne lacks proof.

The baseline should be used for fit and gap analysis, but it should not make private or unsupported claims. If the public/reference corpus is incomplete, Ariadne should surface baseline gaps and recommend follow-up research or user-provided evidence.

## Review-Gated Candidate Destinations

Capture Research Enrichment can prepare candidates for:

- Source Evidence from public-source findings;
- Derived Evidence from Ariadne interpretation over findings and deterministic context;
- Packet Field Answer candidates and packet gap updates;
- Action Plan Items for follow-up research, teaming, customer engagement, or evidence collection;
- Risk Register signals for source gaps, competitive vulnerabilities, transition risk, price risk, or proof gaps;
- Call Plan signals and customer engagement recommendations;
- Price-to-Win, Burn Rate, and Workload assumptions;
- Requirements Fit and Competitive Gap signals;
- Teaming Partner Needs;
- Follow-Up Question Routes;
- BCC-ready evidence and analysis for later Bidder Comparison Chart or Milestone Briefing Packet add-on work.

None of these should write trusted downstream records without explicit user review.

## Command Surface Expectations

The first Command Center surface should show one research run at a time and remain action-oriented:

- trigger context and source-profile refs;
- the Capture Research Brief;
- live-readiness and source-mode labels;
- approval state for live source collection and selected provider;
- source-collection records and source limitations;
- Source Findings grouped by source target;
- selected Capture Research Lenses and seller-baseline refs;
- Research Summary View as a readable overview;
- reviewable insight candidates and downstream candidate groups;
- review actions such as accept, discard, route, edit, or create follow-up action;
- links back to PIID, SAM.gov, Opportunity Knowledge Context, Evidence, Packet, Action Plan, Risk Register, Call Plan, and Capability Run details when available.

The UI can remain in the existing FastAPI Command Center scaffold for this epic. Defer full Next.js migration and polished artifact-style presentation.

## Explicitly Deferred

- LangGraph, general skill-chain orchestration, or Hermes runtime.
- Autonomous live web research beyond explicit user-triggered or future approved-policy runs.
- Browser-mediated logged-in source access for LinkedIn, X, or other restricted platforms.
- Paywall, login, or anti-bot bypass.
- BLS, GSA CALC, or GSA Per Diem product integration, except as future recommended routes or manually provided context.
- Full subaward, customer, vehicle, or competitor profile products beyond first-slice research outputs.
- Bidder Comparison Chart artifact generation or Milestone Briefing Packet slide rendering.
- New seller-profile editor or dedicated KBR/business-unit profile store.
- Semantic retrieval/RAG, persisted indexes, graph database, Knowledge Graph View, or cross-opportunity inferred matching.
- Project Theseus solicitation parsing, MinerU, OCR, or multimodal extraction.
- Artifact Renderer, DOCX, XLSX, presentation, or huashu-design export.
- Automatic trusted downstream writes.
- Full Next.js UI migration.

## Testing Decisions

- Test the external behavior: research brief creation, trigger context, source-profile references, fake/live source-mode labeling, approval requirements, source findings, seller-baseline refs, selected lenses, insight candidate projection, review decisions, persistence, and Command Center responses.
- Use fake source-collection adapters in normal automated tests.
- Assert fake and demo output cannot be confused with live source success.
- Test that Source Profiles are referenced, not embedded wholesale.
- Test that Research Summary Views remain composed from underlying findings and candidates rather than becoming trusted evidence.
- Test that accepting or routing candidates preserves provenance and does not create unrelated trusted downstream records.
- Keep optional live provider validation outside the normal unit-test path and require private local configuration.

## Acceptance Demo

The first acceptance demo should show one opportunity or source-profile gap flowing through the full research workflow:

1. A PIID profile, SAM.gov profile, Opportunity Knowledge Context gap, or bounded user prompt starts a Capture Research Enrichment run.
2. Ariadne creates a Capture Research Brief with trigger context, source-profile refs, selected lenses, seller-baseline refs, source targets, and evidence goals.
3. If a local or API-backed source provider is configured and the user approves, Ariadne runs live source collection against bounded public targets. If not, the demo can show fake-adapter behavior clearly marked as fake for development validation.
4. Ariadne records source-collection provenance, source limitations, and Source Findings.
5. Ariadne applies selected capture lenses to produce reviewable insight candidates, requirements-fit and competitive-gap signals, price/workload assumptions, teaming needs, and downstream candidate routes.
6. The Command Center shows a Research Summary View plus grouped review sections for the underlying findings and candidates.
7. The user accepts, discards, edits, or routes at least one candidate without automatic trusted downstream promotion.

## First Implementation Order

1. Run `improve-codebase-architecture` before substantive application code.
2. Add the Capture Research Enrichment domain model and narrow local store.
3. Add fake source-collection adapter tests and source-mode provenance.
4. Add the source-provider registry boundary and live readiness checks for Crawl4AI, SearXNG, SerpApi, Olostep, and optional Firecrawl.
5. Add research brief creation from source-profile refs, Opportunity context, and user-prompted requests.
6. Add seller-baseline ref selection from accepted Ariadne knowledge, Capture Reference Context, and Reference Wiki notes.
7. Add source finding creation and selected-lens interpretation into reviewable candidates.
8. Add review decisions and downstream candidate links without trusted auto-promotion.
9. Add the Capture Research Enrichment Command Surface in the existing Command Center scaffold.
10. Validate with `uv run ruff check src tests`, `uv run pytest -q`, and optional live provider smoke checks when configured.
11. Update PRD/current-state docs after implementation and user review.
