# MVP-2 Skill Decomposition Map

Issue: #89

This map turns broad Project Theseus skill families into focused Ariadne-native capability candidates for MVP-2. Theseus inspiration only means Ariadne can reuse patterns, vocabulary, quality gates, and handoff ideas, but the broad skills are not copied wholesale into Ariadne.

MVP-2 keeps each candidate scoped to one repeatable outcome. Candidates must use the Capability Contract shape, preserve provenance, land in review, and avoid trusted downstream writes until a reviewer accepts or routes the output.

Status vocabulary:

- runnable-now: can be implemented with current Ariadne stores, fake runners, and review surfaces.
- dependency-gated: useful candidate, but blocked by an explicit prerequisite.
- deferred: belongs after MVP-2 or after another approved integration slice.
- utility/reference: reference material, metadata, or validation support rather than a user-facing run.
- inspiration-only: Theseus pattern stays as context; Ariadne does not build it in MVP-2.

Review destinations used by this map: Packet Field Answer candidate, Call Plan signal, Action Plan recommendation, Capture Research candidate, Artifact Content Block, and Capability Run Output.

Boundary: no parser/RAG/graph/rendering runtime expansion in MVP-2. This map can mention parser, retrieval, graph, or renderer prerequisites only as dependency gates or deferred work.

## Decomposition Table

| Theseus family | Ariadne candidate | Status | One repeatable outcome | Expected handoff | Dependency gate | Review destination |
| --- | --- | --- | --- | --- | --- | --- |
| `proposal-generator` | proposal-compliance-spine-planner | dependency-gated | Draft a compliance spine from reviewed packet fields, source refs, and known instructions. | compliance spine summary with cited packet/source refs | reviewed solicitation instruction extraction or manually entered instruction refs | Artifact Content Block |
| `proposal-generator` | win-theme-synthesizer | runnable-now | Draft candidate win themes from accepted customer priorities, seller baseline, and competitive gaps. | win theme candidates with assumptions and gaps | accepted or reviewable customer priority and seller baseline context | Capability Run Output |
| `proposal-generator` | proposal-outline-drafter | dependency-gated | Draft an outline skeleton from reviewed packet sections and known evaluation needs. | outline candidate by artifact section | renderer-ready artifact section model or reviewed instruction refs | Artifact Content Block |
| `proposal-generator` | full proposal generator | deferred | Produce full proposal volumes. | final proposal package | reviewed solicitation parser, artifact rendering/export, full compliance spine, human style review | Artifact Content Block |
| `competitive-intel` | incumbent-award-history-brief | runnable-now | Summarize incumbent, award history, obligation posture, and source limitations from USAspending/source-profile refs. | award-history brief plus source limitations | PIID profile or source-profile refs available | Capture Research candidate |
| `competitive-intel` | competitive-gap-route-hint | runnable-now | Convert incumbent and seller-baseline signals into one packet/action implication. | gap implication with recommended route | accepted seller baseline or reviewable source finding | Packet Field Answer candidate |
| `competitive-intel` | black-hat competitor brief | dependency-gated | Produce a scoped competitor hypothesis brief. | competitor hypothesis with evidence gaps | competitor identity refs, public-source collection approval, reviewable source findings | Capture Research candidate |
| `competitive-intel` | full live competitor research workbench | deferred | Multi-source competitor dossier and pricing position. | dossier package | broader source collection policy, live provider approvals, graph/RAG decision | Capability Run Output |
| `compliance-auditor` | instruction-evaluation-coverage-check | dependency-gated | Flag proposal instruction/evaluation factor coverage gaps. | coverage gap list | solicitation extraction bundle with instruction and evaluation entities | Capability Run Output |
| `compliance-auditor` | clause-reference-sanity-check | dependency-gated | Check cited clause/reference presence and review need. | clause sanity findings with source refs | clause/eCFR readiness and approved source access | Capability Run Output |
| `compliance-auditor` | deliverable-requirement-gap-finder | dependency-gated | Identify requirements without linked deliverables. | requirement/deliverable gap findings | solicitation requirements and deliverables extracted into reviewable bundle | Action Plan recommendation |
| `compliance-auditor` | full compliance audit | deferred | Full FAR/DFARS compliance report. | compliance report | eCFR adapter, reviewed extraction, clause model, human compliance review path | Capability Run Output |
| `rfp-reverse-engineer` | hot-button-signal-extractor | dependency-gated | Surface likely hot buttons from reviewed requirements, evaluation factors, and customer notes. | hot-button signals with confidence and gaps | reviewed solicitation/source extraction or manually entered requirement refs | Call Plan signal |
| `rfp-reverse-engineer` | discriminator-hook-finder | dependency-gated | Identify evaluation or requirement hooks that could support discriminators. | discriminator hook candidates | reviewed evaluation factor and seller proof refs | Packet Field Answer candidate |
| `rfp-reverse-engineer` | missing-section-signal-check | dependency-gated | Flag notable missing scope, QASP, key personnel, or evaluation signals. | missing-signal checklist | solicitation structure extraction readiness | Action Plan recommendation |
| `rfp-reverse-engineer` | hidden decision tree reconstruction | deferred | Reconstruct full contracting-officer decision tree. | decision tree envelope | solicitation parser, ontology alignment, graph/query layer | Capability Run Output |
| `workload-analyzer` | workload-table-shape-profiler | dependency-gated | Classify workload attachment shape, sheets, fields, joins, and data gaps. | workload shape profile | attachment table intake or uploaded structured table fixture | Capability Run Output |
| `workload-analyzer` | workload-assumption-candidate | dependency-gated | Convert workload table signals into one pricing or staffing assumption. | assumption candidate with source refs | workload attachment profile and reviewed table refs | Action Plan recommendation |
| `workload-analyzer` | site-scope-risk-snapshot | dependency-gated | Summarize geographic/site concentration risk from workload tables. | site risk snapshot | site list or workload table extraction | Capture Research candidate |
| `workload-analyzer` | price-to-win workload handoff | deferred | Full PTW workload package. | PTW handoff envelope | PTW workflow, renderer/export, reviewed workload table model | Artifact Content Block |
| `data-analyzer` | data-table-profiler | runnable-now | Profile table shape, missing fields, anomalies, assumptions, and recommended next route. | table profile summary | structured table fixture or user-provided table-like data | Capability Run Output |
| `data-analyzer` | anomaly-route-recommender | runnable-now | Turn detected anomalies into one reviewable next route. | anomaly route recommendation | data-table profile output | Action Plan recommendation |
| `data-analyzer` | dataset-comparison-snapshot | dependency-gated | Compare two structured datasets for changed counts, fields, and notable differences. | comparison snapshot | two accepted table refs and stable comparison contract | Capability Run Output |
| `data-analyzer` | full statistical analysis agent | deferred | Broad exploratory and inferential analysis. | analysis report | richer file intake, charting policy, statistical QA review | Capability Run Output |
| `subcontractor-sow-builder` | teaming-scope-outline-drafter | dependency-gated | Draft a scoped outline for partner responsibilities from reviewed scope refs. | scope outline candidate | reviewed scope package and partner identity | Artifact Content Block |
| `subcontractor-sow-builder` | subcontractor-assumption-list | runnable-now | Turn partner/scope gaps into assumptions and questions. | assumption/question list | existing packet gaps or partner strategy notes | Call Plan signal |
| `subcontractor-sow-builder` | partner-workshare-risk-check | dependency-gated | Flag workshare, deliverable, and responsibility risks. | workshare risk candidates | reviewed teaming scope package and deliverable refs | Action Plan recommendation |
| `subcontractor-sow-builder` | full subcontractor SOW builder | deferred | Draft full lower-tier SOW/PWS. | SOW/PWS artifact | reviewed scope package, legal/compliance review, renderer/export | Artifact Content Block |
| `govcon-ontology` | ariadne-theseus-term-crosswalk | utility/reference | Map Theseus ontology terms to Ariadne domain terms and explicit non-equivalences. | term crosswalk page | current CONTEXT.md and Theseus ontology reference | Capability Run Output |
| `govcon-ontology` | extraction-candidate-validator | dependency-gated | Validate reviewable extraction candidates against allowed term families. | validation findings | extraction bundle readiness | Capability Run Output |
| `govcon-ontology` | data-element-relationship-hint | utility/reference | Suggest relationship hints for packet data elements without writing graph state. | relationship hint list | accepted data-element dictionary and vault refs | Packet Field Answer candidate |
| `govcon-ontology` | full GovCon ontology runtime | deferred | Operate a full ontology-backed graph runtime. | ontology/graph runtime result | graph/RAG runtime decision, parser alignment, ADR | Capability Run Output |

## MVP-2 Candidate Priorities

1. Start with runnable-now candidates that exercise the Capability Contract without new runtime scope: `data-table-profiler`, `incumbent-award-history-brief`, `win-theme-synthesizer`, `competitive-gap-route-hint`, `anomaly-route-recommender`, and `subcontractor-assumption-list`.
2. Register dependency-gated candidates honestly so route cards can explain missing prerequisites instead of pretending broad skills are available.
3. Keep utility/reference candidates available for planning, validation, and Hermes Improvement Proposals, but do not expose them as automatic work-product generators.
4. Treat broad Theseus skills as inspiration-only or deferred until Ariadne has the required reviewable input contracts, source-profile coverage, parser boundary, renderer path, or graph/RAG decision.

## Handoff Rules

- Every candidate output must be reviewable before it updates a Packet Field Answer, Action Plan Item, Evidence Item, Artifact Content Block, Call Plan signal, or reusable insight.
- Expected handoffs should name their destination and the minimum source refs or input refs carried forward.
- Dependency-gated candidates should return a missing-prerequisite explanation and a next enabling action, not a failed run.
- Hermes can later propose decomposition changes, quality-gate updates, or eval gaps through Improvement Proposals, but it cannot mutate this map, skill contracts, or trusted workflow records without approval.
