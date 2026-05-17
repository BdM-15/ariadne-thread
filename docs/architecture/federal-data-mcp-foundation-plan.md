# Federal Data MCP Foundation Plan

Date: 2026-05-16  
Status: completed through Command Center demo
Planned epic branch: `04-build/federal-data-mcp-foundation`

## Completed Epic

Build the **Federal Data MCP Foundation + USAspending Recompete Intelligence Intake** vertical slice.

The slice should make all eight upstream `1102tools/federal-contracting-mcps` servers visible to Ariadne as pinned, manifest-only **Federal Data Capabilities**, while deeply integrating only USAspending into Ariadne product behavior first. The first product workflow is a **PIID Contract Intelligence Profile** that starts from one contract number and produces a structured, reviewable capture-intelligence record.

## Product Thesis

Ariadne's capture work is recompete-heavy. A single PIID or contract number should become a high-quality research spine: incumbent, customer, award value, period of performance, burn posture, vehicle context, obligation history, gaps, deterministic pivots, and recommended next enrichment actions.

The first slice should not try to create the entire future orchestration. It should prove the backbone that later SAM.gov, BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, Regulations.gov, Firecrawl, 1102 skills, LangGraph, huashu-design, DOCX/XLSX renderers, and Hermes-supported improvement loops can use.

## Decisions Resolved

- Use upstream 1102tools MCPs. Do not build Ariadne-specific federal data MCP servers for these public data sources.
- Use manifest-only integration. Do not vendor upstream MCP source code into Ariadne.
- Register all eight MCPs now, but distinguish `registered`, `smoke_tested`, `product_integrated`, and `deferred_product_workflow` status.
- Use USAspending as the first deep product integration because recompete capture depends on award history, incumbents, vehicles, obligations, spending patterns, and timing signals.
- Treat user-provided PIID intelligence templates as strategy input, not a product spec. Build the Ariadne profile around the actual USAspending MCP behavior and Ariadne's evidence/review model.
- Produce a structured PIID Contract Intelligence Profile record and command-surface candidates before any Markdown, DOCX, XLSX, presentation, or huashu-design export.
- Make Hermes observation possible through structured events, but do not implement Hermes execution, autonomous tool choice, or workflow mutation in this epic.
- Keep artifact rendering as a future downstream action. The profile should be renderer-ready, not renderer-owned.

## Federal Data MCP Registry Scope

The registry should capture package, version, command, upstream source, license, capability description, required and optional env var names, and product integration status.

| Capability       | Upstream package       | Initial pinned version | Command shape                                                 | Env shape                                                                                 | Initial product status               |
| ---------------- | ---------------------- | ---------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------ |
| USAspending      | `usaspending-gov-mcp`  | `0.3.2`                | `uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp`       | none                                                                                      | `product_integrated` target          |
| SAM.gov          | `sam-gov-mcp`          | `0.4.1`                | `uvx --from sam-gov-mcp==0.4.1 sam-gov-mcp`                   | upstream expects `SAM_API_KEY`; Ariadne may map from `SAM_GOV_API_KEY`                    | `registered` / `smoke_tested` target |
| GSA CALC+        | `gsa-calc-mcp`         | `0.2.7`                | `uvx --from gsa-calc-mcp==0.2.7 gsa-calc-mcp`                 | none                                                                                      | `registered` / `smoke_tested` target |
| BLS OEWS         | `bls-oews-mcp`         | `0.2.7`                | `uvx --from bls-oews-mcp==0.2.7 bls-oews-mcp`                 | optional `BLS_API_KEY`                                                                    | `registered` / `smoke_tested` target |
| GSA Per Diem     | `gsa-perdiem-mcp`      | `0.2.6`                | `uvx --from gsa-perdiem-mcp==0.2.6 gsa-perdiem-mcp`           | optional/recommended `PERDIEM_API_KEY`                                                    | `registered` / `smoke_tested` target |
| eCFR             | `ecfr-mcp`             | `0.2.6`                | `uvx --from ecfr-mcp==0.2.6 ecfr-mcp`                         | none                                                                                      | `registered` / `smoke_tested` target |
| Federal Register | `federal-register-mcp` | `0.2.7`                | `uvx --from federal-register-mcp==0.2.7 federal-register-mcp` | none                                                                                      | `registered` / `smoke_tested` target |
| Regulations.gov  | `regulationsgov-mcp`   | `0.2.5`                | `uvx --from regulationsgov-mcp==0.2.5 regulationsgov-mcp`     | optional/recommended `REGULATIONS_GOV_API_KEY` or Ariadne mapping from `API_DATA_GOV_KEY` | `registered` / `smoke_tested` target |

Smoke tests should verify MCP initialize behavior without making rate-limited or data-returning calls unless a specific issue explicitly opts in. Do not print live secrets.

## USAspending Product Workflow

The first deep workflow should start from `input_contract_number` and create a structured **PIID Contract Intelligence Profile**.

Initial behavior should include:

- resolve a PIID/contract number through USAspending;
- classify the scenario as `standalone_contract`, `parent_idiq`, `idiq_order`, or `unknown`;
- collect award baseline fields: dates, dollars, recipient, agency, offices, NAICS, PSC, solicitation, vehicle fields, and permalink;
- collect transaction and modification history where available;
- compute burn posture: net obligations, fiscal-year pattern, period-of-performance window, monthly/daily rate, option/modification signals, deobligation warnings, and derivation notes;
- collect parent, child, or sibling context where the USAspending MCP exposes enough linkage;
- identify deterministic pivots for future enrichment: UEI, parent UEI, solicitation ID, NAICS, PSC, agency/offices, parent IDV, subaward hooks, and permalink;
- record PRIME gaps and source limitations without filling missing values with guesses;
- create review-gated candidates for Evidence Items, Packet Field Answers, Action Plan Items, Risk Register signals, Call Plan signals, and follow-up enrichment routes;
- emit Hermes-observable events such as `profile_started`, `award_resolved`, `scenario_classified`, `burn_posture_computed`, `pivots_identified`, `gap_detected`, `next_enrichment_recommended`, and `review_decision_recorded`.

## Command Surface Expectations

The Command Center should present the profile as action-oriented capture work, not a static report.

Useful first commands include:

- accept award baseline as Source Evidence;
- accept burn posture as Derived Evidence;
- route an incumbent profile enrichment to a future SAM.gov/customer/competitor workflow;
- route NAICS or PSC signals to future BLS or market research workflows;
- route solicitation ID to future SAM.gov opportunity/document intake work;
- create an Action Plan Item for a recompete follow-up;
- create a Packet Field Answer candidate for incumbent, customer, value, timing, competition, or risk;
- mark missing values as gaps;
- defer artifact export until Artifact Renderer work exists.

## Explicitly Deferred

- Deep product workflows for SAM.gov, BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, and Regulations.gov.
- Firecrawl, SerpApi, Olostep, LinkedIn, X.com, social/news enrichment, or broad web scraping.
- 1102 deliverable skills such as SOW/PWS or IGCE builders.
- Skill chaining, LangGraph orchestration, or autonomous multi-capability planning.
- Hermes runtime, memory, autonomous execution, or self-modifying workflow behavior.
- huashu-design, DOCX, XLSX, presentation export, or final artifact generation.
- Full Next.js UI migration.
- Treating public data pulls as trusted opportunity knowledge without Ariadne review gates.

## Acceptance Demo

The acceptance demo should show one PIID flowing through the real USAspending-backed workflow:

1. Ariadne shows all eight 1102 Federal Data Capabilities in the registry with honest status labels.
2. USAspending is available as the first product-integrated capability.
3. A user enters one contract number.
4. Ariadne resolves the award, classifies the scenario, computes the baseline and burn posture, and records provenance.
5. The profile displays gaps, deterministic pivots, recommended next enrichments, and disabled/deferred artifact actions.
6. The user accepts or routes at least one review-gated candidate without bypassing the Evidence Store and review model.

## First Implementation Order

1. Add a Federal Data Capability registry and manifest model for the eight upstream 1102 MCPs.
2. Add manifest files and smoke-test coverage that verifies initialize behavior without leaking secrets.
3. Build the USAspending adapter boundary over the upstream MCP command surface.
4. Build the PIID Contract Intelligence Profile domain model and local persistence needed for the first workflow.
5. Convert USAspending responses into profile baseline, burn posture, vehicle context, pivots, gaps, recommendations, and review candidates.
6. Surface the workflow through FastAPI API routes and the existing Command Center shell.
7. Add tests and update docs/PRD with the completed behavior before moving to the next enrichment slice.

## Progress Note Through Issue #33

The PIID profile now projects populated USAspending profile data into recommended enrichment routes, review-gated candidates for Evidence, Packet Field Answer, Action Plan, Risk Register, Call Plan, and follow-up route workflows, and Hermes-observable event records. Review decisions update candidate state and emit `review_decision_recorded` events, but they do not write trusted Evidence, Packet, Action Plan, Risk Register, or Call Plan outputs.

The existing Command Center shell now shows all eight Federal Data Capabilities and a persisted PIID Profile Command Surface. The surface reads local PIID profile records only, displays award baseline, burn posture, vehicle context, pivots, gaps, recommended enrichments, review candidates, provenance, and deferred artifact actions, and does not start upstream MCP processes during page render.

## Next Slice Candidates After This Epic

- SAM.gov Entity and Opportunity enrichment from UEI or solicitation pivots.
- BLS/GSA CALC/GSA Per Diem pricing and labor context for profile pivots.
- Firecrawl or web enrichment seeded by customer, incumbent, and office pivots.
- Focused competitor, subaward, customer, or vehicle profile skills.
- Artifact Renderer export from accepted PIID profile content.
- Hermes operational learning over repeated PIID profile runs and review decisions.
