# SAM.gov Enrichment Plan

Date: 2026-05-17  
Status: completed; first command-surface UI shape accepted as good enough for now

## Selected Epic

Build the **SAM.gov Enrichment Profile** vertical slice after the completed Federal Data MCP Foundation + USAspending Recompete Intelligence Intake epic.

Epic branch: `05-build/sam-gov-enrichment-profile`.

Suggested progression branches:

- `05-build/01-sam-gov-domain-store`
- `05-build/02-sam-gov-adapter`
- `05-build/03-sam-gov-attachments-document-intake`
- `05-build/04-sam-gov-command-surface`
- `05-build/05-sam-gov-command-surface-review-candidates`

The slice should use official SAM.gov data to enrich a recompete or opportunity profile through entity records, known opportunity records, discovery searches, and approved attachment intake. It extends the Federal Data Capability boundary from ADR 0007 and the Document Intake extraction boundary from ADR 0006.

## Product Thesis

USAspending gives Ariadne the award-history spine for a recompete. SAM.gov should add the official acquisition-facing context around that spine: entity registration and vendor ecosystem clues, current or archived opportunity notices, pre-solicitation discovery, customer/office/program search, set-aside and timing signals, and official solicitation attachments that can enter Document Intake.

The first SAM.gov slice should stay deterministic and review-gated. It should not become broad web research, artifact generation, autonomous orchestration, or solicitation parsing. It should create high-quality source profiles, source limitations, and downstream candidates the user can accept, route, or defer.

## Decisions Resolved

- Build **SAM.gov Enrichment Profile** as the next vertical epic.
- Use one combined profile with lanes for entity records, known opportunity records, opportunity discovery, and attachment intake.
- Use **SAM.gov Entity Record** for official SAM.gov entity registration or responsibility records so the term does not conflict with Document Intake `Entity Candidate` language.
- Use **SAM.gov Opportunity Record** for official notices, solicitations, RFIs, Sources Soughts, Special Notices, and related opportunity records.
- Include **SAM.gov Opportunity Discovery** for cases where no solicitation ID exists yet, using customer, office, program-name, description, keyword, renamed-program, notice-type, NAICS/PSC, set-aside, and date-window signals.
- Treat provider-backed web research as a deferred enrichment route for renamed, ambiguous, stale, or incomplete official-source signals. Do not implement live web source collection in this epic.
- Include **SAM.gov Opportunity Attachment Intake** for official opportunity description links and resource links surfaced by SAM.gov results.
- Ask before downloading opportunity attachments. Approved downloads should become Document Intake records.
- Use best-effort official-source retrieval for current and prior or archived solicitation documents. Missing or inaccessible attachments become source limitations and possible follow-up routes.
- Keep search, entity, and opportunity data behind the upstream `sam-gov-mcp` Federal Data Capability adapter. Do not build a duplicate Ariadne SAM.gov data MCP.
- Allow direct official-link fetches only for user-approved attachment downloads surfaced by SAM.gov results.
- Classify downloaded attachments through Document Intake before extraction. Generic material can use generic extraction; solicitation-family material should wait for or route to a Solicitation Parser Capability such as Project Theseus.
- Persist the SAM.gov profile as a structured, reviewable source profile. Trusted Evidence, Packet Field Answers, Action Plan Items, Risk Register Items, Call Plan signals, Opportunity Knowledge, and follow-up routes remain review-gated candidates until accepted or routed.
- Record these decisions in this architecture plan rather than a new ADR because ADR 0007 and ADR 0006 already carry the hard-to-reverse platform boundaries.
- Require a private `SAM_GOV_API_KEY` for live SAM.gov profile creation. Tests and demo fixtures should use fake adapter responses and never depend on live secrets or rate limits.
- Treat the SAM.gov key as rotating private configuration. The current expected limit is 1,000 requests per day, which is ample for a single-user local workflow. Build and test the capability robustly rather than artificially constraining it around rate-limit fear.
- Every SAM.gov profile and result should carry a provenance source mode such as `live_sam_gov`, `fake_adapter_test`, or `demo_fixture`. Fake-adapter and demo-fixture outputs must not be presented as proof of live source success.

## Profile Lanes

### Entity Record Lane

Starts from UEI, parent UEI, vendor name, incumbent name, or user-entered company search terms.

Outputs should include official entity matches, registration status, entity names, UEI, CAGE when available, business types, NAICS/PSC signals, responsibility or integrity signals when exposed by the available access level, hierarchy or parent-company clues when exposed, source limitations, and review-gated vendor ecosystem leads.

Use cases include incumbent validation, parent-company discovery, subcontractor or partner research, competitor discovery, and teaming-target identification. Official SAM.gov entity data is not a complete capability picture; the profile should surface gaps and recommend follow-up research when needed.

### Known Opportunity Lane

Starts from a solicitation number, notice ID, or clean opportunity pivot supplied by the PIID Contract Intelligence Profile, an Opportunity record, Document Intake, or the user.

Outputs should include matched opportunity records, notice type, title, organization path, customer office, posted date, response deadline, active/archive state, set-aside, NAICS, PSC/classification code, point-of-contact fields when available, description/resource links, and source limitations.

### Opportunity Discovery Lane

Starts when Ariadne does not have a solicitation ID. Inputs can include customer, office, agency/subtier, program name, old program name, description fragment, keyword, notice type, NAICS, PSC, set-aside, posted date window, response date window, and place-of-performance clues.

Outputs should include search runs, query parameters, matched notices, match rationale, confidence, ambiguity notes, renamed-program clues, gaps, and recommendations for follow-up. If official SAM.gov results are weak or ambiguous, the profile should recommend a deferred provider-backed web enrichment route rather than running broad web research in this epic.

### Opportunity Attachment Intake Lane

Starts from opportunity records that expose description links, resource links, or related official SAM.gov attachment metadata.

Outputs should include attachment metadata, source opportunity trace, download eligibility, review state, download status, Document Intake record links for approved downloads, and source limitations for unavailable or inaccessible documents.

Downloaded material should enter the existing Document Intake Queue. Solicitation-family files such as RFIs, Sources Soughts, draft RFPs, final RFPs, amendments, and requirements attachments should be classified as Solicitation Documents and remain parser-required until a Solicitation Parser Capability is integrated. Generic source material can continue through the existing generic intake path.

## Review-Gated Candidate Destinations

The SAM.gov profile can create candidates for:

- Source Evidence from official entity, opportunity, and attachment metadata.
- Derived Evidence for Ariadne interpretations such as discovery confidence, vendor ecosystem signal, or notice-timing signal.
- Packet Field Answers for customer, office, incumbent, vehicle, timing, competition, set-aside, requirements, and risk fields.
- Action Plan Items for follow-up research, customer engagement, attachment review, or parser-required document work.
- Risk Register signals for timing, competition, set-aside fit, source gaps, or incumbent/vendor ecosystem concerns.
- Call Plan signals for customer office validation, POC follow-up, pre-solicitation engagement, or teaming outreach.
- Follow-up enrichment routes for Firecrawl, BLS/GSA pricing, subaward profiles, competitor/customer profiles, solicitation parser work, or artifact preparation.

None of these candidates should write trusted downstream records until reviewed.

## Explicitly Deferred

- Firecrawl or broad web enrichment.
- Direct non-SAM web crawling or search.
- Guessing hidden attachment URLs.
- Solicitation parsing with Project Theseus or any other parser.
- MinerU, RAGAnything, LightRAG, OCR, or multimodal extraction.
- Artifact Renderer, DOCX, XLSX, presentation, or huashu-design export.
- Hermes runtime, autonomous tool choice, or workflow mutation.
- Skill chaining or LangGraph orchestration.
- Full Next.js UI migration.
- Treating SAM.gov results or downloaded documents as trusted opportunity knowledge without review gates.

## Runtime And Test Boundary

Live SAM.gov enrichment is the normal product behavior when `SAM_GOV_API_KEY` is present in the private `.env`. The purpose of the upstream MCP is to retrieve current source data when the user asks Ariadne to run a SAM.gov workflow. The key rotates outside the repository and must never appear in committed docs, fixtures, logs, diagnostics, or tests.

Automated tests should use fake SAM.gov adapter responses by default because test suites must stay deterministic and must not require private secrets. Fake-adapter tests prove Ariadne's mapping, persistence, review gates, error handling, and command-surface behavior; they must not be reported as proof that live SAM.gov is reachable or returning current data. The Command Center may show saved profiles, fixture-backed demos, and missing-key readiness state without invoking live SAM.gov calls. User-triggered SAM.gov product actions should call live SAM.gov by default when the key is configured.

Because the expected API allowance is 1,000 requests per day for a single-user local workflow, implementation should be practical rather than timid. Page render should not trigger live calls, broad research should still be a deliberate product action, and attachment downloads still require approval, but profile creation, discovery pagination, archived-notice checks, and retry/error handling should be robust enough for real work.

Automated tests should not be artificially limited to tiny result sets. They should use fake adapter responses that cover multiple entity matches, hierarchy clues, known opportunity matches, discovery searches, active and archived notices, pagination, attachments, inaccessible documents, rate/auth failures, and no-result cases. Test fixtures and demo profiles should carry provenance that marks them as fixture or fake-adapter output, not live source success. Separate live validation may exist for developer confidence, but it is not the normal unit-test path and does not change the product rule: live user workflows use live SAM.gov when configured.

Only live-source SAM.gov outputs should be eligible for trusted Evidence promotion in normal product use. Fake-adapter tests may exercise review-gate mechanics and candidate projection, but their provenance must prevent fixture data from being confused with source truth.

## Implementation Trail

### Issue #35: Entity Record Profile Lane

The first progression branch adds the SAM.gov Entity Record lane as a concrete product-integrated slice over the upstream `sam-gov-mcp` capability. It introduces a local SAM.gov Enrichment Profile module with source-mode provenance, fake/live runner separation, profile persistence, entity lookup by UEI or vendor name, review-gated candidates, review-decision events, FastAPI profile routes, a read-only Command Center panel, and public configuration for the SAM.gov profile store path.

This slice intentionally does not implement known opportunity lookup, no-solicitation-ID discovery, attachment download/intake, Firecrawl, solicitation parsing, or trusted downstream promotion. Those remain in later SAM.gov issues.

### Issue #36: Opportunity Discovery Lane

The second progression branch adds user-triggered SAM.gov Opportunity Discovery for cases where Ariadne does not yet have a solicitation ID. It introduces discovery queries over customer, office, program name, renamed-program clues, notice type, NAICS, PSC, set-aside, and posted date windows, then calls the upstream `search_opportunities` tool through the same fake/live source-mode boundary used by the Entity Record lane.

Discovery results persist inside the SAM.gov Enrichment Profile with retrieved-at provenance, source mode, mapped notice fields, match rationale, confidence, ambiguity notes, total-record metadata, and source limitations. The slice creates review-gated Source Evidence, Derived Evidence, Packet Field Answer, Action Plan, Call Plan, and deferred Web Enrichment Support route candidates, but still does not implement Firecrawl, attachment intake, known opportunity lookup, or trusted downstream writes.

### Issue #37: Known Opportunity Record Lane

The third progression branch adds the Known Opportunity lane to an existing SAM.gov Enrichment Profile. It resolves a clean solicitation number or notice ID through the upstream `search_opportunities` tool, preserves source-mode and retrieved-at provenance, records official opportunity fields, and surfaces no-match, ambiguous, archived, stale, or incomplete responses as source limitations rather than silent success.

Known opportunity results persist beside the existing Entity Record and Opportunity Discovery lanes. The slice creates review-gated Source Evidence, Packet Field Answer, Action Plan, and Call Plan candidates while preserving the existing profile and avoiding trusted downstream writes, attachment intake, Firecrawl, broad discovery, and solicitation parsing.

### Issue #38: SAM.gov Attachment Intake Lane

The fourth progression branch adds the Attachment Intake lane for official SAM.gov description and resource links surfaced by Known Opportunity and Opportunity Discovery records. It preserves pending-approval state during enrichment and page render, filters download eligibility to official SAM.gov surfaced links, and records non-SAM.gov or missing resource links as source limitations.

Approved downloads use an explicit API action before fetching any file. Downloaded material creates Document Intake records with provenance back to the SAM.gov profile, attachment metadata, opportunity identifiers, and source mode. Generic readable material can continue through the existing generic extraction path; solicitation-family material is queued as parser-required Document Intake work for a future Solicitation Parser Capability. Inaccessible or expired official links become Attachment Intake source limitations rather than silent success.

### Issue #39: Full SAM.gov Command Surface And Review Candidates

The fifth progression branch makes the four-lane SAM.gov profile coherent as a saved command surface rather than separate read-only lane snippets. Opportunity Discovery can now be attached to an existing profile beside Entity Record, Known Opportunity, and Attachment Intake lanes. The Command Center links each saved profile to a detail page that reads persisted state only and does not trigger live SAM.gov calls or attachment downloads.

The saved profile detail page and summary API show live readiness, source-mode labels, all lane states, source limitations, linked Document Intake records, review-gated candidate destinations, and explicit deferrals for provider-backed Web Enrichment Support, Specialized Solicitation Parser, Project Theseus parser integration, Artifact Renderer/export, Hermes/LangGraph, and additional federal data sources. The surface keeps fake-adapter output visually distinct from live SAM.gov success and repeats that trusted writes remain absent until an explicit reviewer action occurs.

This branch provided the user-facing shape for human review. The first UI shape was accepted as good enough for now, so the SAM.gov epic can merge to `main` and later UI polish can be selected through a separate documented slice.

## Completion Note

SAM.gov Enrichment Profile is complete for this epic. The accepted scope includes all four lanes, saved profile detail pages, command-surface summary API, fake/live/demo provenance, live readiness, review-gated candidates, explicit deferrals, source limitations, attachment approval, and Document Intake provenance. Remaining ideas should be treated as future slices rather than unfinished work inside this epic.

## Accepted Four-Lane Demo

The first acceptance demo should show one recompete or opportunity profile flowing through all four SAM.gov enrichment lanes:

1. Ariadne shows SAM.gov as the next product-integrated Federal Data Capability without changing the upstream MCP boundary.
2. A PIID profile or user input provides at least one entity pivot and one opportunity/discovery pivot.
3. Ariadne creates a SAM.gov Enrichment Profile with entity, known opportunity or discovery, attachment, source limitation, and recommended follow-up sections.
4. The profile shows review-gated candidates for Evidence, Packet, Action Plan, Risk Register, Call Plan, and follow-up routes.
5. The user approves at least one official attachment download.
6. The downloaded file appears in the Document Intake Queue with provenance back to the SAM.gov profile and opportunity record.
7. Solicitation-family material remains queued for a future Solicitation Parser Capability, while generic material can use the existing generic extraction path.
8. No Firecrawl, artifact rendering, Hermes runtime behavior, or trusted downstream promotion occurs without explicit review.

## Accepted Implementation Order

1. Add SAM.gov profile domain models and local persistence.
2. Add robust fake-adapter tests covering entity records, known opportunities, discovery searches, attachments, pagination, inaccessible documents, no-results, auth/rate errors, source modes, and review gates.
3. Add a SAM.gov adapter boundary over the upstream `sam-gov-mcp` command surface for live user-triggered workflows.
4. Add profile builders for entity records, known opportunity records, opportunity discovery, source limitations, and review-gated candidates.
5. Add attachment metadata and approved-download handling for official SAM.gov links surfaced by the adapter.
6. Route approved downloads into Document Intake with source provenance and parser-required status where appropriate.
7. Surface the profile through FastAPI API routes and the existing Command Center shell.
8. Add tests and update PRD/current-state docs after the implemented slice is validated.
