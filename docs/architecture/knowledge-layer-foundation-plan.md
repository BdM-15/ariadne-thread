# Knowledge Layer Foundation Plan

Date: 2026-05-18  
Status: selected through `grill-with-docs`; ready for implementation

## Selected Epic

Build the **Knowledge Layer Foundation** vertical slice after the completed Capability Run Foundation epic.

Suggested epic branch: `07-build/knowledge-layer-foundation`.

Published progression issues:

- #45 Build the Structured Knowledge Index projection
- #46 Compose the Opportunity Knowledge Context View
- #47 Persist deterministic Next Action Recommendations
- #48 Review recommendations into Action Plan work
- #49 Show Knowledge Context in the Command Center
- #50 Validate and document Knowledge Layer Foundation

The slice should create Ariadne's first deterministic, local-first relationship projection across accepted capture records before adding semantic retrieval, graph visualization, Hermes memory, parser integrations, or artifact workflows.

## Product Thesis

Ariadne now has multiple useful stores and command surfaces, but the knowledge across them is still mostly workflow-local. Future Hermes recommendations, graph visualization, parser integration, RAG, artifact rendering, and richer Command Center actions all need a reliable way to answer what a capture object is connected to, what supports it, what gaps or limitations remain, and what the user should open next.

The next slice should prove that foundation with an on-demand **Structured Knowledge Index** and a Command Center **Knowledge Context Panel** focused first on **Opportunity Knowledge Context**.

## Decisions Resolved

- Build **Knowledge Layer Foundation** as the next vertical epic.
- Use a deterministic **Structured Knowledge Index** before embeddings, semantic search, RAG, LightRAG, graph databases, graph visualization, Hermes memory, or autonomous recommendations.
- Include only already-built Ariadne records in the first projection: Opportunities, accepted Evidence Items, Packet Field Answers, Action Plan Items, accepted Document Intake evidence links, PIID Contract Intelligence Profiles, SAM.gov Enrichment Profiles, Capability Runs, and Capability Run Outputs.
- Exclude full Risk Register, Call Plan, Artifact drafts, Hermes memories, semantic chunks, graph nodes, and external web research from the first index because they either remain deferred or do not yet have complete product stores.
- Rebuild the first index on demand from existing source stores rather than persisting a separate index store.
- Treat the existing stores as the source of truth. The index is a projection, not a new durable authority.
- Allow the projection builder to include all known records from completed stores, while keeping this epic's user-facing query and panel scoped to one selected Opportunity.
- Connect records through explicit references and accepted provenance first; defer fuzzy name matching, semantic similarity, model-inferred links, entity resolution, and other inferred relationship discovery.
- Use a **Knowledge Context Panel** in the existing Command Center as the first proof surface.
- Use **Opportunity Knowledge Context** as the required tracer bullet because Opportunity is Ariadne's durable center of gravity.
- Expose one composed Opportunity Knowledge Context view first, with smaller internal helpers hidden behind that interface.
- Return structured data with concise display summaries from the Opportunity Knowledge Context view, not HTML, layout strings, CSS classes, or final presentation copy.
- Scope the first Knowledge Context Panel to one Opportunity at a time. Cross-opportunity sensemaking remains deferred unless records are already explicitly linked.
- Add a practical Knowledge Context Panel to the existing FastAPI Command Center shell for the first proof surface, without treating this as full UI polish or Next.js migration.
- Use a compact default panel with expandable provenance and detail so production use stays command-first.
- Separate trusted context from reviewable context in the panel, but keep production command execution simple: the user should see clear next actions while Ariadne handles aggregation, provenance, and heavy lifting behind the scenes.
- The first AI-assisted command should be **Recommend Next Capture Actions**. Recommended actions should include action capability routes that show available tools, partial assistance, user-owned steps, and capability gaps.
- Generate first action capability routes deterministically from the Capability Catalog and known product workflows. Hermes may later observe capability gaps and propose ways to fill them, but Hermes gap-filling is not part of this epic.
- Generate next-action candidates from deterministic structured signals first. Optional Local Admin Model assistance may polish wording, summarize rationale, or group actions when available, but action generation must still work without Ollama, hosted frontier models, Hermes, semantic retrieval, or RAG.
- Save recommended action candidates as **Next Action Recommendations** before they become Action Plan Items or routed work.
- Own Next Action Recommendations in the Knowledge Layer Foundation until they are accepted or routed; do not store them as Action Plan commitments before review.
- Preserve a lightweight **Recommendation Context Snapshot** on each Next Action Recommendation so review, provenance, and future autonomy learning can see what the recommendation was based on when generated.
- Persist Next Action Recommendations in a narrow local-first **Next Action Recommendation Store**, while keeping the Structured Knowledge Index itself on-demand and non-authoritative.
- Allow an explicitly accepted Next Action Recommendation to create an Action Plan Item with provenance back to the Knowledge Context, recommendation, supporting trusted and reviewable context, action capability route, rationale, and review decision.
- Link created Action Plan Items back to their accepted Next Action Recommendations so recommendation history, review outcome, and autonomy learning context remain traceable.
- Preserve the long-term click-reduction path through Graduated Autonomy: repeated recommendation approvals, review outcomes, and capability routes should create structured signals Hermes can later use for Operational Learning and Improvement Proposals, but this epic should not automatically handle actions without human-approved autonomy rules.
- Record autonomy learning signals as metadata on Next Action Recommendations and review decisions, without using those signals to reduce clicks automatically in this epic.
- Record this slice in an architecture plan rather than a new ADR because it follows existing local-first, review-gated, adapter-boundary decisions and avoids choosing a hard-to-reverse storage or retrieval engine.

## First Structured Knowledge Index Scope

The first index should answer exact, deterministic questions over accepted or reviewable Ariadne records:

- Which records are connected to this Opportunity, profile, evidence item, packet field, action item, or capability run?
- Which accepted Evidence Items support this object?
- Which Packet Field Answers, gaps, assumptions, and Action Plan Items are connected?
- Which PIID and SAM.gov profile signals or source limitations are relevant?
- Which Capability Runs and Capability Run Outputs produced related reviewable work?
- Which pending reviews or source limitations block trusted use?
- Which Command Surface should the user open next?

The first index should not perform semantic search, model synthesis, ranking, hidden reasoning, automatic recommendation generation, or trusted downstream writes.

The projection can include all known records for exact lookup and reference validation, but the first query API should center on one `opportunity_id`. It should not produce cross-opportunity recommendations, inferred related-opportunity links, or unrelated shared-entity context. Tests should verify records from unrelated Opportunities do not leak into the Knowledge Context Panel.

The first public query should be a single composed view, such as `get_opportunity_knowledge_context(opportunity_id)`. It should assemble trusted context, reviewable context, gaps, limitations, related runs, recommendations, and next command links. Internally, the module may use helpers for evidence, packet fields, action items, profiles, capability runs, and recommendations, but avoid user-facing query or endpoint sprawl in this epic.

The composed view should include structured refs and typed categories plus concise human-readable summaries such as title, summary, status labels, counts, source-strength notes, gap labels, and next command labels. It should not include HTML, CSS classes, layout sections as strings, long explanatory prose, or final design copy. Keep the output reusable for the current FastAPI Command Center scaffold, future Next.js UI, and future agents.

## First Connection Model

The first connection model should include direct references and accepted provenance already present in Ariadne records:

- direct IDs such as opportunity IDs, evidence IDs, draft part IDs, packet field IDs, profile IDs, run IDs, and document intake IDs;
- source-to-derived evidence lineage;
- source-span-to-evidence links;
- public-data profile links and source limitations;
- review or routing links from accepted candidates;
- capability run input refs and output refs when they point to known Ariadne objects.

Do not include fuzzy name matching, semantic similarity, model-inferred relationships, entity resolution, or "looks related" links in this epic.

## First Proof Surface

The first **Knowledge Context Panel** should appear inside the existing Command Center and stay action-oriented rather than becoming a passive data browser. For a selected Opportunity, it should show:

- connected accepted evidence;
- packet fields, gaps, assumptions, and confidence notes;
- action plan items and next capture outcomes;
- accepted Document Intake evidence links;
- related PIID profile and SAM.gov profile signals;
- related Capability Runs and reviewable outputs;
- source limitations, pending reviews, and unresolved gaps;
- links to the next relevant Command Surfaces.

The first panel should prove the relationship model before Ariadne invests in a full Knowledge Graph View.

The first panel should stay single-Opportunity. It may include shared knowledge entities only when they are already explicitly linked through existing packet, evidence, or workflow records. Defer similar-opportunity search, related-customer discovery, incumbent comparison across pursuits, semantic similarity, inferred reusable insights, and cross-opportunity graph exploration to later Knowledge Graph, Reusable Insight, or retrieval slices.

The first proof surface should be added to the existing FastAPI Command Center shell. It should include a practical panel or detail section plus API routes for the composed view and recommendation commands. Keep styling and interaction patterns consistent with the current scaffold, preserve accessible labels and predictable command buttons, and avoid making capability/provenance detail overwhelm the primary action flow. Defer full Next.js UI, full visual polish, graph visualization, and advanced interaction design.

The panel should default to a compact action-oriented summary: context health, trusted and reviewable counts, top gaps or source limitations, pending recommendations, one primary **Recommend Next Capture Actions** command, and clear next command links. Expandable detail can show exact supporting refs, provenance, stale snapshot comparisons, capability route details, review history, and rejected or discarded recommendation history.

The panel should distinguish context states without becoming convoluted:

- **Trusted context**: accepted Evidence Items, accepted Packet Field Answers, accepted Action Plan Items, and accepted source-span evidence links.
- **Reviewable context**: pending or routed candidates, pending Capability Run Outputs, SAM.gov or PIID review candidates, Document Intake draft parts, and parser-required intake records.
- **Rejected or discarded context**: hidden by default from the main panel, but available through provenance or history views when needed.

The primary production interaction should be command-first. The panel can summarize counts, source strength, gaps, and recommended next actions, while deeper provenance and review history remain one click away.

## First AI-Assisted Command

The first AI-assisted command should be **Recommend Next Capture Actions**.

The command should consume deterministic Opportunity Knowledge Context and produce reviewable **Next Action Recommendations**. Each recommendation should include:

- the recommended capture action;
- the gap, weak evidence, pending review, public-data follow-up, packet-readiness issue, or customer-engagement need it addresses;
- supporting trusted context and reviewable context;
- an action capability route showing which Capability Modules or product workflows can help;
- whether Ariadne can handle the action directly, partially assist it, route it to user work, or mark it as a Capability Gap;
- the next command surface to open;
- concise rationale and provenance.

The first implementation may make capability routing deterministic from the existing Capability Catalog and known product workflows. Hermes may later observe repeated capability gaps and propose Improvement Proposals, but Hermes runtime behavior remains deferred in this epic.

Recommendation generation should be deterministic-first. Useful first signals include missing or weak packet fields, pending reviewable context, source limitations, unsupported or parser-required documents, stale or absent evidence, SAM.gov or PIID follow-up routes, Capability Gaps, known product workflows, and Capability Catalog entries. Optional Local Admin Model polish can improve wording or grouping, but the core recommendation logic must not depend on model availability.

Explicit user acceptance may create an Action Plan Item in this epic. Generation alone must not write trusted downstream records. Accepted action-plan writes should preserve the supporting Opportunity Knowledge Context, Next Action Recommendation, trusted and reviewable context refs, capability route, rationale, and review decision.

Next Action Recommendations should remain distinct from Action Plan Items. Before acceptance, they belong to the Opportunity Knowledge Context as reviewable recommendation records with review state such as pending, accepted, routed, discarded, or edited. Accepted recommendations can create Action Plan Items, and the resulting Action Plan Items should link back to the originating recommendation.

Next Action Recommendations should be persisted because they carry user decisions, created action links, and autonomy learning signals. The store should stay narrow: recommendations, review state, context refs, capability routes, autonomy hints, created Action Plan links, and review decisions. Do not persist the full Structured Knowledge Index or create a broad knowledge database in this epic.

Each Next Action Recommendation should preserve a lightweight Recommendation Context Snapshot. The snapshot should include stable refs such as evidence IDs, packet field IDs, action IDs, profile IDs, capability run IDs, and document intake IDs, plus short summaries of the gap, source limitation, recommendation cause, capability route, and autonomy hint. Do not store the full Structured Knowledge Index, giant source text, documents, raw prompts, or sensitive blobs. If current Opportunity Knowledge Context diverges from the snapshot later, Ariadne can mark the recommendation as potentially stale.

Stale recommendation behavior should stay simple in the production flow:

- Pending recommendation plus changed context: show it in the Knowledge Context Panel with a stale label and a refresh recommendation action.
- Accepted recommendation: show it through Action Plan or provenance history, not as an active recommendation.
- Discarded recommendation: hide it from the main panel and keep it in history.
- Routed recommendation: show it only if the route still needs user action.
- Recommendation stale because supporting evidence or context changed materially: require re-review before it can create an Action Plan Item.

Refreshing a stale recommendation should create a new version rather than overwriting the existing record. The recommendation family should preserve the original basis, stale trigger, refreshed version, and final user decision. The older version should be marked stale or superseded, the refreshed version should get a fresh Recommendation Context Snapshot, and only an accepted current version can create an Action Plan Item.

The first implementation should support light editing before acceptance. The user may edit the action title or description, owner, due date, workstream, packet field link, and rationale note. Edits should create a new version or review decision entry, preserve the original generated text in history, and allow the edited recommendation to create an Action Plan Item when accepted. Defer complex collaborative editing, rich text, attachment editing, and multi-step action decomposition.

Accepting a recommendation should support explicit create-or-update behavior for the Action Plan. The default accept path creates a new Action Plan Item. The user may explicitly choose to attach the recommendation to an existing action or update an existing action. Updates should preserve the original Action Plan history and link the recommendation as supporting context. Ariadne may suggest likely duplicates deterministically, but it should not auto-merge recommendations into existing actions in this epic. Defer bulk merge and complex task decomposition.

Deterministic duplicate suggestions should use explicit shared references only. Compare shared opportunity ID, packet field ID, evidence ID, document intake ID, profile ID, capability run or output ID, gap key, workstream, and capability route. Do not fuzzy-match title or body text in this epic. Show possible existing actions as user choices only.

The first implementation should also preserve enough review history for future autonomy learning. Ariadne should be able to learn later that the user repeatedly accepts certain low-risk recommendations, but the transition from review-required to fewer-click or automatically handled flows belongs to a later Graduated Autonomy slice.

Autonomy learning signals should include why the action was recommended, which deterministic signals produced it, which capability route was suggested, whether the user accepted, routed, discarded, or edited it, whether it created an Action Plan Item, whether similar actions might later be candidates for fewer-click handling, and which safety conditions would need to be true before autonomy increases.

Future fewer-click or automatic handling should be blocked unless an action is low-risk, reversible, grounded in trusted context or clearly bounded reviewable context, not customer-facing, not externally sent, not deleting or weakening evidence, not changing sensitive labels, not spending credits or making broad external calls, not making gate or bid/no-bid decisions, not making pricing/compliance/legal decisions, repeatedly accepted by the user in similar contexts, and tied to a capability route with reliable provenance and predictable output.

Next Action Recommendations may carry advisory autonomy hints such as `review_required`, `candidate_for_fewer_clicks_later`, `never_auto_handle`, or `requires_user_approval`. These hints are metadata only in this epic.

## Required Tracer Bullet

The required tracer is **Opportunity Knowledge Context**.

Acceptance should show one Opportunity whose context can be reconstructed from existing stores and displayed in the Command Center. The context should explain what supports the opportunity, what remains unknown, what source limitations exist, what capability outputs still need review, and which command surfaces can advance the work.

## Acceptance Demo

The acceptance demo should show a single Opportunity moving through the full Knowledge Context loop:

1. The user opens one Opportunity in the Command Center.
2. The Knowledge Context Panel rebuilds context on demand from existing Ariadne stores.
3. The panel separates trusted context from reviewable context.
4. The panel shows connected evidence, packet fields, action items, Document Intake links, PIID profile, SAM.gov profile, Capability Runs, gaps, source limitations, and pending reviews.
5. The user runs **Recommend Next Capture Actions**.
6. Ariadne produces reviewable Next Action Recommendations with action capability routes.
7. Each action shows whether existing tools can help, can partially help, require user work, or represent a Capability Gap.
8. The user accepts, routes, or discards one candidate.
9. An explicitly accepted Next Action Recommendation can create an Action Plan Item with provenance back to the Knowledge Context and recommendation.
10. No other trusted downstream record is created automatically, and action handling does not become automatic without future human-approved Graduated Autonomy rules.
11. The local FastAPI Command Center runs on the project-standard `9622` port for the first UI shape review.
12. The user reviews the first UI shape and either accepts it as good enough for this stage or requests changes before the UI/HITL acceptance criteria are considered complete.
13. Semantic search, graph visualization, Hermes runtime, and persistent indexing remain absent.

## Accepted Implementation Order

1. Build the Structured Knowledge Index domain model and on-demand projection builder, with early tests around relationship correctness and trust boundaries.
2. Add adapters or readers over existing stores for Opportunities, Evidence Items, Packet Field Answers, Action Plan Items, Document Intake accepted evidence links, PIID profiles, SAM.gov profiles, and Capability Runs.
3. Add query functions for Opportunity Knowledge Context.
4. Add deterministic action capability routing from the Capability Catalog and known product workflows.
5. Add **Recommend Next Capture Actions** as reviewable Next Action Recommendations.
6. Add the Command Center Knowledge Context Panel.
7. Add accept, route, and discard behavior for recommended action candidates, allowing explicit acceptance to create Action Plan Items while preserving review provenance and preventing other automatic trusted writes.
8. Run the local Command Center on port `9622` for first UI shape review when validating the panel.
9. Add tests and update PRD/current-state docs after validation.

## Explicitly Deferred

- OpenAI embedding calls and semantic retrieval.
- LightRAG, RAGAnything, vector databases, graph databases, or persistent indexing engines.
- Full Knowledge Graph View or graph visualization UI.
- Hermes runtime, Hermes memory, autonomous observation loops, or automatic recommendations.
- Background indexing jobs, sync queues, automatic reindex triggers, or persisted index files.
- Project Theseus solicitation parser integration.
- MinerU, OCR, multimodal extraction, or full document parser integrations.
- Artifact Renderer, DOCX, XLSX, presentation, or huashu-design workflows.
- Automatic trusted downstream writes from indexed relationships.

## ADR Note

No ADR is needed for this slice as currently scoped. The narrow Next Action Recommendation Store follows the existing local-first workflow-store pattern and does not select a new storage engine or broad knowledge database.

Create an ADR only if a later decision chooses a persistent index store, vector database, graph database, LightRAG runtime, embedding/index-isolation strategy, Hermes memory model, generalized knowledge/action database, automatic action handling, or another hard-to-reverse knowledge engine boundary.
