# Ariadne Thread

**Product Requirements Document (PRD) v1.43**

**North Star: One elegant, powerful Capture Command Center that allows a single capture professional to manage the entire capture lifecycle — from opportunity identification through award — with maximum effectiveness and minimum friction.**

**Repo Name:** ariadne-thread  
**Date:** May 20, 2026
**Status:** Artifact Assembly Foundation complete; production Command Center UI/UX plan incorporated; MVP-1 production Command Center tracer is on review branch with the first Opportunity Intake and Portfolio Foundation loop; MVP-1B Opportunity Activation + Packet Field Action Matrix now has a deterministic local-first activation run seam, a Next.js Autonomy Digest and Packet Field Action Matrix surface, the first explicit review-gated Packet Field Answer promotion path, a selected Command Center Work Modes IA correction so the home surface stays a pulse/router instead of a mega-scroll page, clarified Milestone 1-4 gate discipline with the Living Milestone Decision Briefing Packet as the primary opportunity roadmap, first-class Milestone Gate status in the Opportunity scaffold/portfolio/workspace contract, and a stage-relative, gate-scoped packet roadmap model that turns missing data elements into recommended actions, research, engagement, teaming, or artifact-content routes; next MVP work is full portfolio lifecycle management, broader route execution, Ariadne Knowledge Vault, and real capability/skill/MCP execution behind product workflows

---

## 0. Current State Snapshot (May 19, 2026)

**Completed**

- Developer skills are installed or vendored under `.github/skills/`, including Matt Pocock's full pack, first-principles thinking, skill-creator, ui-ux-pro-max, CLI-Anything builder skill, and the full `coreyhaines31/marketingskills` v2.0 pack. CLI-Hub meta-skill is present only as an optional discovery aid.
- Python-first workspace defaults are established with Python 3.14.5 / `>=3.14`, `uv`, `.python-version`, `pyproject.toml`, `uv.lock`, and local `.venv/`.
- Secret hygiene is established: `.env` and `.env.*` remain private; `.env.example` is the public descriptive config contract.
- OpenAI `text-embedding-3-large` is the single canonical embedding path unless an ADR later defines migration/index isolation for alternatives.
- Architecture foundation docs exist in `docs/architecture/` and `docs/adr/`.
- Shipley global knowledge references are commit-safe and organized under `docs/reference/shipley/`.
- Project Ariadne public-source knowledge is imported under `docs/reference/project-ariadne/knowledge/` as Capture Reference Context, including company-specific public-source bid-qualification intel.
- CLI-first harnesses are an approved architecture option for repeatable, batchable, tool-facing, or agent-facing capabilities that should not become complicated UI or bespoke tool sprawl.
- The first-slice domain/storage epic is complete on `01-build/first-slice-domain-storage` and merged to `main`: Opportunity shell, Evidence Store, Quick Capture review routing, Living Briefing Packet skeleton/review, Capture Action Plan skeleton, read-only Capability Catalog, first Command Center shell, and packet data elements as cross-opportunity knowledge slots.
- The Quick Capture Knowledge Processing epic is complete on `02-build/quick-capture-knowledge-processing`: Reference Wiki influences, Capture Intelligence Drafts, per-piece review/route/skill-chain controls, review-gated promotions into Evidence/Action Plan/Packet outputs, polished trusted evidence with raw trace/admin context, low-signal clarification routing, pasted text and text/Markdown upload intake, parser-required unsupported upload candidates, public call plan/risk register dictionaries, optional Local Admin Model assist through central local-model config, and an end-to-end Command Center demo thread.
- The Document Intake Command Surface first vertical epic is complete on `03-build/document-intake-command-surface`: persisted Document Intake Queue, classification for generic/visual/solicitation/unsupported material, generic Extraction Bundles, document-derived Capture Intelligence Draft Parts, accepted Source Span promotion into Evidence Items, review-gated downstream candidates for Action Plan, Packet, Risk Register, and Call Plan workflows, one-way Knowledge Note Projections, inert future parser/retrieval adapter declarations, and an accepted first Command Center demo thread over real behavior.
- A local FastAPI runtime exists via `uv run python app.py` or `python app.py` with `.env`; the project-standard local UI port is `9622`, while `9621` is reserved for Project Theseus.
- The first Command Center shell is command-first: it supports pulse checks, quick actions, and AI-support entry points rather than serving as a passive metrics wall.
- Packet data modeling now distinguishes reusable Packet Field Definitions from opportunity-specific Packet Field Answers, evidence/provenance, assumptions, confidence, gaps, Action Plan links, Shared Knowledge Entities, and Knowledge Mirror projections.
- A `grill-with-docs` planning session selected the **Document Intake Command Surface** as the next vertical product slice. `CONTEXT.md` now defines the Capture Knowledge Foundation, Extraction Bundle, Source Span, Entity Candidate, Relationship Candidate, Extraction Warning, Generic Source Material, Visual Source Material, Solicitation Document, Unsupported Document, Document Intake Queue, Document Intake Store, Knowledge Note Projection, Multimodal Extraction Capability, and Solicitation Parser Capability.
- ADR 0006 records the Document Intake extraction boundary: parser, retrieval, OCR, multimodal, MinerU, RAGAnything, LightRAG, and Theseus-style tools produce reviewable Extraction Bundles, while Ariadne owns trusted entities, relationships, provenance, and review gates.
- `docs/architecture/document-intake-command-surface-plan.md` records the completed Document Intake implementation trail and hand-off notes for future parser/retrieval integration work.
- A `grill-with-docs` planning session selected **Federal Data MCP Foundation + USAspending Recompete Intelligence Intake** as a vertical product epic. ADR 0007 records that Ariadne should integrate upstream `1102tools/federal-contracting-mcps` as manifest-only Federal Data Capabilities instead of creating unique Ariadne MCP servers for the same public data sources.
- `docs/architecture/federal-data-mcp-foundation-plan.md` records the completed Federal Data MCP Foundation epic plan and implementation trail: all eight 1102 MCPs are registered with honest status labels, USAspending is the first product-integrated source, and the PIID Contract Intelligence Profile workflow supports recompete capture research.
- The Federal Data MCP Foundation epic includes manifest registration, safe initialize smoke checks, richer operational MCP descriptions, USAspending PIID lookup/history adapter behavior, local PIID profile persistence, burn posture, vehicle context, deterministic pivots, source-limit gaps, recommended enrichment routes, review-gated command-surface candidates, Hermes-observable event records, review-decision recording without automatic trusted-output promotion, and a persisted PIID Profile Command Surface in the existing Command Center shell.
- A fresh `grill-with-docs` planning session selected the **SAM.gov Enrichment Profile** as the next vertical product epic. `CONTEXT.md` now defines SAM.gov Enrichment Profile, SAM.gov Entity Record, SAM.gov Opportunity Record, SAM.gov Opportunity Discovery, SAM.gov Opportunity Attachment Intake, and Web Enrichment Support.
- `docs/architecture/sam-gov-enrichment-plan.md` records the selected SAM.gov epic plan: one combined profile with entity, known opportunity, discovery, and attachment-intake lanes; live SAM.gov product behavior when `SAM_GOV_API_KEY` is configured; fake-adapter tests that never masquerade as live source success; source-mode provenance; approved official-link attachment downloads into Document Intake; and review-gated downstream candidates.
- SAM.gov Enrichment Profile is complete: Entity Record lane, Opportunity Discovery lane, Known Opportunity Record lane, Attachment Intake lane, saved-profile command surface, and command-surface summary API. It preserves live/fake/demo source-mode boundaries, local profile persistence, Command Center links, source limitations, explicit attachment-download approval, Document Intake provenance, explicit deferrals, and review-gated downstream candidates for Evidence, Living Briefing Packet, Capture Action Plan, Risk Register, Call Plan, Document Intake, and follow-up routes.
- The first SAM.gov command-surface UI shape was reviewed as good enough for the SAM.gov stage before Capability Run Foundation planning.
- SAM.gov completion validation: `uv run ruff check src tests` and `uv run pytest -q` passed with 192 tests.
- A `grill-with-docs` planning session selected **Capability Run Foundation + Assisted Execution Command Surface** as the next vertical product epic. `CONTEXT.md` now defines Capability Run Store, Capability Reasoning View, Model Rationale Summary, and Graduated Autonomy.
- `docs/architecture/capability-run-foundation-plan.md` records the selected Capability Run epic plan: separate local-first Capability Run Store, deterministic Capability Catalog validation as the required tracer, optional Local Admin Model readiness/probe through existing Ollama settings, CLI-Anything as one executor style, Microsoft Agent Framework as a future candidate runtime only, Theseus-inspired but Ariadne-native provenance/reasoning views, review-gated Capability Run Outputs, metadata-only autonomy recommendations, and no new ADR for this slice.
- Capability Run Foundation is complete on `06-build/capability-run-foundation`: local Capability Run Store, deterministic Capability Catalog validation runs, reviewable Capability Run Outputs, review decisions without trusted downstream writes, Capability Reasoning View, Capability Studio run history/detail pages, optional Local Admin Model readiness probe, and Command Center launch/review entry points. Issues #40 through #44 are closed as completed.
- Knowledge Layer Foundation is complete on `07-build/knowledge-layer-foundation`: deterministic on-demand Structured Knowledge Index projection, Opportunity Knowledge Context View, persisted Next Action Recommendations, recommendation review into Action Plan work with provenance, stale/refresh and duplicate-suggestion safeguards, and a compact Command Center Knowledge Context Panel with expandable provenance and recommendation history.
- The Knowledge Layer Foundation acceptance demo ran in the local FastAPI Command Center on port `9622`: one Opportunity rebuilt context on demand, separated Trusted Context from Reviewable Context, generated a reviewable Next Action Recommendation, accepted it through the panel, and showed the accepted review history without creating other trusted downstream records automatically. The first UI shape was reviewed as good enough for this stage.
- `docs/architecture/knowledge-layer-foundation-plan.md` records the completed Knowledge Layer Foundation implementation trail and validation outcome. The slice preserves these boundaries: the Structured Knowledge Index remains an on-demand non-authoritative projection, the Next Action Recommendation Store stays narrow, trusted downstream writes remain human-gated, and semantic retrieval/RAG, graph visualization, Hermes runtime, parser integrations, artifact rendering, automatic action handling, broad databases, and persistent indexing remain deferred.
- A `grill-with-docs` planning session selected **Capture Research Enrichment** as the next vertical product epic. `CONTEXT.md` now defines Capture Research Enrichment, Source Profile, Research Trigger Context, User-Prompted Research Request, Capture Research Brief, Web Source Collection, Live Source Collection Run, Source Finding, Seller Capability Baseline, Capture Research Lens, Requirements Fit Analysis, Competitive Gap Analysis, Bidder Comparison Chart, Teaming Partner Need, Price-to-Win Research, Burn Rate Analysis, Workload Analysis, Research Summary View, Capture Research Enrichment Command Surface, and related review boundaries.
- `docs/architecture/capture-research-enrichment-plan.md` records the selected Capture Research Enrichment epic plan: provider-registry Web Source Collection with free/local Crawl4AI and SearXNG first, SerpApi and Olostep as optional recurring-free API-backed providers, Firecrawl kept optional for later paid use, fake adapters for automated tests, source-profile references rather than duplicated PIID/SAM.gov fields, bounded user-prompted research, selected marketing/capture lenses, seller baseline from accepted/reference Ariadne knowledge, reviewable source findings and insight candidates, and no LangGraph/Hermes runtime or automatic trusted downstream writes in the first slice.
- Capture Research Enrichment implementation through issue #59 now includes bounded research-run creation, source-profile references, fake Web Source Collection, source-provider registry/readiness/smoke checks, approved provider-backed collection, Seller Capability Baseline refs from accepted evidence and Reference Wiki context, reviewable Requirements Fit Analysis outputs, reviewable Competitive Gap Analysis outputs with BCC-ready inputs, selected capture-lens analyses, reviewable downstream candidate projection with candidate review decisions, and an end-to-end Capture Research Command Surface in the existing Command Center scaffold.
- Competitive Gap Analysis produces BCC-ready notes only as reviewable input for later Bidder Comparison Chart work. It does not generate BCC rows, scores, slides, artifacts, or trusted downstream records in this slice.
- Selected capture-lens analysis keeps price-to-win, burn-rate, workload, and engagement outputs separated by lens, with provenance, assumptions, source limitations, follow-up needs, confidence, and review state. The targeted CRO lens is limited to call-plan and customer-engagement clarity and is not used as the primary burn-rate or price-to-win lens.
- Downstream candidate projection groups Source Findings and research/lens outputs into reviewable Evidence, Packet, Action Plan, Risk Register, Call Plan, Follow-Up Route, Price/Workload Assumptions, Teaming Partner Needs, and BCC-Ready Notes candidates. Accept, discard, and route decisions update review state and preserve run, brief, trigger, source-finding, selected-lens, source-profile, and seller-baseline provenance without creating trusted downstream records.
- The Capture Research Command Surface now shows live source readiness, the Capture Research Brief, trigger context, source-profile refs, collection provenance, Source Findings, selected lenses, seller-baseline refs, Research Summary View, grouped review candidates, review actions, review decisions, and related Ariadne record links. The first UI shape was reviewed and approved during issue #59.
- Issue #60 adds a standalone local-development single-startup path after the Capture Research Enrichment epic merged to `main`. `docker-compose.local.yml` starts only the selected local providers, SearXNG on `http://localhost:8080` with JSON results enabled and Crawl4AI on `http://localhost:11235`; `scripts/start-local-dev.ps1` starts those providers and Ariadne on port `9622`; `scripts/smoke-local-dev.ps1` validates direct provider health plus Ariadne's approved `crawl4ai_local` and `searxng_local` smoke endpoints. Ollama remains optional/external through existing `OLLAMA_HOST`, and Neo4j, Postgres, vector databases, graph databases, LightRAG, and broad persistent storage remain out of scope.
- Current automated validation: `uv run ruff check src tests` and `uv run pytest -q` pass on the local-dev stack issue #60 progression branch, with 262 tests passing.
- A `grill-with-docs` planning session selected **Artifact Assembly Foundation** as the next foundation epic. `CONTEXT.md` now defines Artifact Assembly Foundation, Artifact Assembly Capability, Artifact Assembly Store, Artifact Source Package, Artifact Draft, Artifact Section, Artifact Content Block, and Artifact Block Review. ADR 0008 records the architecture decision: Ariadne should build artifact capability through source packages, section/block drafts, block-level review, reviewed artifact content, and renderer-ready contracts before final DOCX, XLSX, huashu-design visual/PPTX, Bidder Comparison Chart, or customer-facing export workflows.
- `docs/architecture/artifact-assembly-foundation-plan.md` records the selected Artifact Assembly Foundation epic plan: the first tracer is a reviewable Milestone Decision Briefing Packet draft assembled from Opportunity Knowledge Context through an explicit Artifact Source Package; AI/LLM assistance may coordinate, synthesize, prioritize, and draft prose, but every artifact output must land in deterministic, source-backed, reviewable schema; accepted artifact blocks do not automatically become trusted downstream records; autonomy hints are metadata only; the first surface remains in the existing FastAPI Command Center scaffold; and final rendering/export remains deferred.
- Artifact Assembly Foundation implementation through issue #66 now includes the local Artifact Assembly Store, Artifact Source Packages from Opportunity Knowledge Context, deterministic Milestone Decision Briefing Packet drafts, typed source-backed Artifact Content Blocks, block review decisions and readiness calculation, FastAPI draft assembly/review routes, and the first Artifact Draft Command Surface. The validation loop proves preview/export readiness can be calculated without generating DOCX, XLSX, huashu-design visual/PPTX, or other final exported files and without automatically writing accepted blocks into trusted downstream records.
- Current automated validation after issue #66: `uv run ruff check src tests` passes and `uv run pytest -q` passes with 275 tests. The first Artifact Draft Command Surface was reviewed by the maintainer and accepted as good enough for this stage.
- The production Command Center UI review branch (`11-build/production-command-center-ui`) implements the first route-first tracer: a Next.js Opportunity workspace, Living Packet center surface, assisted capture goal selector, deterministic route recommendations, local route execution, explicit human review gate, provenance view, capability route cards, before/after work-product projections, renderer readiness surface, and local HTTP/browser smoke validation. This proves the interaction loop, but it is not the full capture platform.
- Product direction clarified: once an Opportunity is identified, Ariadne should run a bounded Opportunity Activation Run that gathers as many packet-field answers, source-backed candidates, recommendations, source limitations, and skill/capability route matches as current permissions allow. The UX must present that work as compact coverage, deltas, review queues, and next-best actions rather than as a clunky pile of tools.
- The same review branch now includes the first Opportunity Intake and Portfolio Foundation path: a production Command Center API and simple Next.js modal can create a user-identified Opportunity from only a name, persist a Standard Opportunity Scaffold with core workstreams, Living Packet sections, packet-field action slots, and an initial Autonomy Digest, open the newly created workspace immediately, and let the operator revisit managed Opportunities from the Command Center left rail.
- The next MVP branch (`12-build/opportunity-activation-field-matrix`) now includes a deterministic Opportunity Activation Run module, local activation-run store, Packet Field Action Matrix model, Autonomy Digest generation from packet-field definitions and answers, create-time initial activation storage, production Command Center API routes to list or request activation runs, and a Next.js Opportunity Activation panel that shows latest-run coverage, blocked fields, review-ready counts, approvals, source limits, next-best actions, and field route cards from inside the main workspace. The branch also adds an explicit field review decision path: accepting or editing a matrix field creates an opportunity-scoped Packet Field Answer with provenance, while route and discard decisions only record review state. It now makes Milestone 1-4 Gate status first-class in Opportunity creation, scaffold persistence, portfolio pulse, and workspace display, and Packet Field Definitions/Action Matrix rows carry gate scope so the Packet roadmap shows data elements required for the current milestone before future-gate fields. The current IA correction is to keep the Command Center Home as a pulse-and-routing cockpit, then move detailed action surfaces into focused Work Modes so real Opportunity management does not become one huge scrolling page. This slice remains deliberately review-gated and does not create trusted Evidence, Action Plan Items, or downstream work products automatically.

**Still Deferred**

- Hermes runtime, semantic retrieval or RAG engine, graph visualization, full MinerU integration, RAGAnything integration, LightRAG integration, Theseus solicitation parser integration, OCR/multimodal extraction, final huashu-design/artifact rendering adapters, external API integrations beyond completed SAM.gov and the selected Capture Research Enrichment source-provider lane, additional third-party skill installation beyond the vendored marketing skills, persisted indexing or graph/vector storage, persistent storage beyond local/demo or narrow workflow adapters, full autonomous Opportunity Activation Runs, trusted field promotion beyond the first Packet Field Answer accept/edit path, full multi-opportunity lifecycle management, and the full Ariadne Knowledge Vault UI are not implemented yet. MVP-1 now has a production-shaped Next.js route tracer and first portfolio selector, and MVP-1B now has a deterministic activation-run seam plus first visible field matrix surface and first explicit field-review controls, but broad UI migration, full portfolio workflows, trusted field-level automation, and real capability execution remain governed by the MVP roadmap. Work Modes may expose placeholders for focused surfaces only when they honestly show current implementation status.
- Document Intake UI polish is still deferred beyond the accepted first shape; the existing FastAPI HTML surfaces are review/runtime scaffolds and demo threads, not the final frontend architecture.
- Neo4j, Postgres, vector databases, graph databases, LightRAG runtime, RAGAnything runtime, and broad persistent storage are still not part of the local-development stack unless a later ADR or PRD update explicitly selects them.

**Next Build Gate**

- After review of the MVP-1 production Command Center tracer, the next build epic is MVP-1B: Opportunity Activation + Packet Field Action Matrix + Opportunity Portfolio Foundation. Do not start unrelated deferred artifact, renderer, graph, RAG, Hermes, parser, external API, or broad UI migration work outside that selected spine.
- Treat the completed Knowledge Layer Foundation as the required baseline for future knowledge, recommendation, retrieval, graph, artifact, parser, or Hermes work: exact structured context and human-gated review come first.
- Artifact Source Packages should begin from Opportunity Knowledge Context as the primary aggregator, then Artifact Drafts should move through block-level review and readiness calculation before any future renderer consumes them.
- Provider-backed Web Source Collection is selected only inside Capture Research Enrichment, with explicit approval or future approved autonomy policy, source limits, provenance, and fake adapters for tests. Use free/local Crawl4AI and SearXNG first, SerpApi and Olostep as optional API-backed providers, and Firecrawl only as an optional later paid provider. Keep BLS/GSA pricing product workflows, full subaward/competitor/customer profile products, Bidder Comparison Chart artifact generation, Theseus solicitation parsing, artifact rendering beyond MVP renderer paths, Hermes runtime, Agent Framework, broad skill chaining/LangGraph, graph visualization, additional third-party capability installation, automatic trusted downstream writes, persisted indexing, semantic retrieval/RAG, and broad Next.js migration beyond the selected MVP-1 shell deferred unless a later `grill-with-docs` session explicitly selects one.
- Preserve completed boundaries: upstream federal-data MCPs stay behind Federal Data Capabilities, downloaded source material enters Document Intake, Capability Run Outputs land in review, Knowledge Mirror/Obsidian-style material remains non-authoritative, the Structured Knowledge Index remains an on-demand projection, and trusted downstream writes remain human-gated.

---

## 1. North Star Vision & Core Guiding Principles (Non-Negotiable)

**Vision**  
A single, immersive Command Center (dark cyberpunk aesthetic — deep blacks, neon cyan/magenta accents, information-dense yet calm) where one professional can see the full state of all pursuits, advance opportunities through decision gates, generate high-quality artifacts, interact with a living knowledge layer, and leverage autonomous agents — all without leaving the main interface.

The platform embodies Shipley’s fundamental principles (customer-centricity, early influence, decision-gate discipline, living iterative planning, action-oriented execution) while leveraging modern agentic AI, deep modular architecture, and a beautiful, immersive user interface.

**Core Guiding Principles**

- **Shipley Foundation**: Every major feature and workflow must align with proven capture methodology.
- **Deep Modular Architecture (Matt Pocock influence)**: Rich functionality behind simple, clean interfaces. Constant evaluation and refactoring toward deeper, more composable modules.
- **Python-First Platform**: Python is the primary application, backend, agent, orchestration, and data-processing language. Use the latest stable Python supported by the dependency stack, managed through `uv`; keep TypeScript scoped to the Next.js interface where it is the right tool.
- **Simplicity & Focus**: Maximum simplicity. Minimum tool sprawl. No redundancy. Dual-purpose capabilities preferred.
- **UI-First Mindset**: Custom interfaces (especially for knowledge/RAG and HITL skills) take priority. The user should complete the vast majority of capture work inside one cohesive interface.
- **Agentic Execution**: Self-improving, persistent agents that reduce manual effort over time. Hybrid model usage (powerful reasoning models for complex work + efficient local models for daily execution).
- **Model Role Discipline**: Use frontier reasoning models for strategy, synthesis, mentoring, hard tradeoffs, and executive-ready recommendations; use local/admin models for lower-risk work such as tagging, summarizing, date extraction, deduplication, formatting, and evidence preparation.
- **Self-Improvement**: The platform and its agents become more effective the more they are used on real opportunities.

**Success Criteria**

- One professional can manage 5–10+ high-value opportunities per year with significantly less manual effort and higher consistency.
- Measurable improvement in win probability and capture efficiency.
- The platform feels like a natural extension of the user’s thinking and workflow.
- The codebase remains clean, modular, and easy to evolve.

---

## 2. Developer Skills Bootstrap (Priority Zero — Install First)

**Rationale**  
Developer skills are required to _build_ the platform itself. They must be active from the very first commit. Matt Pocock’s architecture guardian runs in parallel, but UI/UX and skill-creation capabilities enable us to create the custom Command Center, deep modules, and interfaces correctly from day one.

**Required Developer Skills (Install in Parallel on Day 0)**

| Skill                                                                                                   | Purpose                                                                                                                               | Installation Command / Source                                                                                               |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **mattpocock/skills** (full pack, including improve-codebase-architecture and setup-matt-pocock-skills) | Architectural guardian, diagnosis, TDD, triage, issue/PRD workflows, prototyping, handoff, and productivity skills                    | `npx skills@latest add mattpocock/skills`, then keep committed skills under `.github/skills/`                               |
| **ui-ux-pro-max**                                                                                       | Master UI/UX design & component generation for cyberpunk Command Center (custom panels, Ariadne-specific interfaces, visual renderer) | Vendor from https://github.com/nextlevelbuilder/ui-ux-pro-max-skill under `.github/skills/ui-ux-pro-max/`                   |
| **skill-creator** (Anthropic-style)                                                                     | Dynamic generation of new skills/MCPs with proper structure                                                                           | `npx skills add anthropic/skills` or equivalent skill-creator pattern; save under `.github/skills/`                         |
| **first-principles-skill**                                                                              | Systematic first-principles analysis for architecture and strategy                                                                    | `npx skills add awesome-skills/first-principles-skill`, then keep committed skill under `.github/skills/`                   |
| **CLI-Anything builder skill**                                                                          | Generate, refine, test, and validate agent-native Python CLI harnesses for Ariadne internal capabilities or external software/tools   | Vendor `codex-skill/` plus selected `cli-anything-plugin/` methodology resources from https://github.com/HKUDS/CLI-Anything |

**Exact Day-0 Installation Sequence (Run in VSCode Terminal)**

```bash
# 1. Matt Pocock Skills (Architecture Guardian)
npx skills@latest add mattpocock/skills

# 2. First-Principles Skill
npx skills add awesome-skills/first-principles-skill

# 3. Skill-Creator (for dynamic skill generation)
npx skills add anthropic/skills

# 4. Vendor ui-ux-pro-max (Critical — Run this immediately after)

# 5. Vendor CLI-Anything builder skill
```

**How to Vendor `ui-ux-pro-max` on Day 0**

After installing the skill-creator, vendor the upstream skill:

> Vendor `nextlevelbuilder/ui-ux-pro-max-skill` into `.github/skills/ui-ux-pro-max/`. Keep upstream resources (`data`, `scripts`, license, README, and skill metadata) with the skill, and patch command examples only as needed for VS Code workspace paths.

Commit the vendored skill immediately.

**How to Vendor CLI-Anything Builder Skill**

Vendor upstream `codex-skill/` from `HKUDS/CLI-Anything` into `.github/skills/cli-anything/`, then bundle selected `cli-anything-plugin/` methodology resources under `.github/skills/cli-anything/resources/cli-anything-plugin/` so agents can read the full `HARNESS.md` playbook without vendoring the full monorepo. Patch installation examples to `uv`/`uv pip`/`uv tool` forms for Ariadne.

**Optional: How to Vendor CLI-Hub Meta-Skill**

Vendor only `skills/cli-hub-meta-skill/` from `HKUDS/CLI-Anything` into `.github/skills/cli-hub-meta-skill/` when live catalog discovery is useful before building or choosing an external-tool harness. Include upstream license and provenance. Do not vendor the full CLI-Anything monorepo unless a later architecture decision requires a specific generated harness.

**CLI-First Architecture Rule**

Use the CLI-Anything builder skill when a capability is repeatable, batchable, tool-facing, or agent-facing and benefits from deterministic JSON output. Prefer CLI-first harnesses for research/data pulls, document conversion, artifact export, Shipley reference extraction/refresh, future knowledge ingestion/reindexing jobs, admin validation, and wrappers around real external software or APIs. Keep strategic review, decision-making, visual sensemaking, and high-context human workflows in the Command Center UI, with CLI harnesses behind the UI where useful.

**Post-Installation Verification**

- Run `improve-codebase-architecture` on the fresh repo.
- Commit the resulting architectural recommendations before writing any application code.
- Verify expected skills live under `.github/skills/` and no `.agents`, top-level `skills`, or `skills-lock.json` paths remain.

---

## 3. Core Platform Components

| Component                                     | Purpose                                                                                                                                                    | GitHub / Source                                         |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Hermes Agent                                  | Primary self-hosted, persistent, self-improving autonomous operator                                                                                        | To be implemented (local-first)                         |
| Grok 4.3 (xAI)                                | Primary reasoning & complex artifact generation model                                                                                                      | xAI Console                                             |
| Local Efficient Models                        | Fast daily execution (Qwen3.5 / 9B-class via Ollama)                                                                                                       | https://ollama.com                                      |
| OpenAI text-embedding-3-large                 | High-quality semantic search in knowledge layer                                                                                                            | https://platform.openai.com                             |
| MinerU                                        | Candidate generic and multimodal extraction adapter for generic source material and visual source material; not Ariadne's source of truth                  | https://github.com/opendatalab/MinerU                   |
| RAGAnything                                   | Candidate future document/RAG pipeline adapter for multimodal or complex source material after Ariadne's extraction contract is proven                     | https://github.com/HKUDS/RAG-Anything                   |
| Project Theseus Solicitation Parser Candidate | Existing specialized parser candidate for solicitation-family documents such as RFIs, Sources Soughts, draft RFPs, final RFPs, amendments, and attachments | https://github.com/BdM-15/proj-theseus                  |
| Knowledge Engine Candidate                    | Opportunity-centric retrieval and graph context with settings + integrated chat; LightRAG is a candidate, not a committed runtime shape                    | https://github.com/HKUDS/LightRAG                       |
| LangGraph (selective)                         | Clean skill/MCP chaining only where it adds clear value                                                                                                    | https://github.com/langchain-ai/langgraph               |
| CLI-Anything Harness Methodology              | Agent-native CLI surfaces for repeatable Ariadne workflows and external software/tool access                                                               | https://github.com/HKUDS/CLI-Anything                   |
| huashu-design                                 | Visual artifact renderer and PPTX-capable artifact path                                                                                                    | Internal (guided by ui-ux-pro-max)                      |
| Custom Renderer Skill                         | DOCX generation through the Pandoc/John MacFarlane path plus separate XLSX generation for capture artifacts                                                | Internal (guided by ui-ux-pro-max)                      |
| Custom HITL Chat Interface                    | Back-and-forth interaction for skills requiring human decision input                                                                                       | Internal (guided by ui-ux-pro-max)                      |
| Obsidian Integration                          | Living PKM and capture plans                                                                                                                               | https://github.com/kepano/obsidian-skills               |
| 1102tools/federal-contracting-mcps            | Hardened public federal data MCPs for USAspending, SAM.gov, BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, and Regulations.gov                       | https://github.com/1102tools/federal-contracting-mcps   |
| 1102tools/federal-contracting-skills          | Government contracting deliverables (IGCE, SOW/PWS, market research)                                                                                       | https://github.com/1102tools/federal-contracting-skills |
| coreyhaines31/marketingskills                 | Vendored workspace skills for value propositions, positioning, messaging, customer research, competitor profiling, sales enablement, pricing, and CRO      | https://github.com/coreyhaines31/marketingskills        |
| Crawl4AI                                      | Primary free/local page crawling and LLM-ready extraction provider for Capture Research Web Source Collection                                              | https://github.com/unclecode/crawl4ai                   |
| SearXNG                                       | Primary free/local search discovery provider for Capture Research Web Source Collection                                                                    | https://github.com/searxng/searxng                      |
| SerpApi                                       | Optional API-backed SERP/search provider for Capture Research fallback discovery                                                                           | https://serpapi.com                                     |
| Olostep                                       | Optional API-backed search, scraping, and crawling provider for Capture Research fallback collection                                                       | https://www.olostep.com                                 |
| Firecrawl                                     | Optional paid/later research and scraping provider if its quality is worth the spend                                                                       | https://github.com/mendableai/firecrawl                 |

---

## 4. Technical Architecture

- **Primary Language**: Python 3.14.5 / `>=3.14` as the default implementation baseline for backend services, agents, orchestration, document processing, knowledge workflows, and platform tools. Downgrade only through an ADR if a required dependency blocks 3.14.
- **Python Tooling**: Use `uv` for dependency, lockfile, and virtualenv management; use `uvx` for one-off Python CLIs. Keep a local `.venv/` ignored by git.
- **Frontend**: Next.js 15 + Tailwind + shadcn/ui + custom cyberpunk components (guided by ui-ux-pro-max). Use TypeScript only for the frontend and frontend-adjacent tooling.
- **Backend**: Python-first, deep modular structure (enforced by Matt Pocock skills)
- **Initial Python Package Shape**: Start with one `src/ariadne/` package and deep internal modules for the first slice rather than many small top-level packages. Initial module homes should include configuration, opportunities, evidence, packets, action plans, and capability catalog concerns.
- **CLI-First Harnesses**: Use Python Click-style CLIs with `--json` output for repeatable, batchable, tool-facing, or agent-facing operations. These CLIs should sit behind the UI or agent runtime rather than replacing human-facing strategy workflows.
- **Federal Data MCP Foundation**: Integrate upstream `1102tools/federal-contracting-mcps` through manifest-only Federal Data Capability declarations. Ariadne should pin upstream packages, record provenance and env-var names, smoke-test MCP initialize behavior, and deeply integrate one source at a time through product workflows rather than building unique federal data MCP servers.
- **Capture Research Enrichment**: Build a bounded research workflow over deterministic source profiles, Opportunity Knowledge Context, user-prompted research requests, provider-backed public source collection, selected capture/marketing lenses, and seller-baseline reference knowledge. Persist research briefs, trigger context, source findings, selected lenses, insight candidates, review decisions, and downstream candidate links in a narrow local workflow store; keep PIID/SAM.gov source-profile data referenced rather than duplicated.
- **Evidence Store**: Store traceable Evidence Items local-first behind a Pydantic-validated interface. Start with structured local files as the first adapter, while keeping callers isolated from whether persistence later becomes SQLite, Postgres, or another storage engine.
- **Document Intake Command Surface**: Turn uploaded source material into extraction provenance, Capture Intelligence Draft Parts, recommendations, skill-chain options, accepted Evidence Items, review-gated downstream candidates, Knowledge Note Projections, and Command Center actions. Build functionality first through domain models, a narrow Document Intake Store, and Extraction Bundle behavior before rendering UI.
- **Extraction Boundary**: Use Extraction Bundles as the shared parser output contract for generic source material, visual source material, and solicitation-family documents. Parser, OCR, multimodal, retrieval, MinerU, RAGAnything, LightRAG, and Theseus-style tools must act as adapters that produce reviewable output; Ariadne keeps trusted entities, relationships, provenance, and review gates in the domain model.
- **Agents**: Hermes Agent (persistent memory) + Grok 4.3 for complex work + local models for speed
- **Knowledge Layer**: Opportunity-centric retrieval and graph context with a custom Command Center UI. LightRAG is a candidate component, but exact integration details should be decided during architecture work.
- **Artifact Generation**: Custom renderer capabilities for DOCX, XLSX, and huashu-design visual/PPTX outputs
- **Storage**: Local-first structured Evidence Store, narrow workflow stores such as the Document Intake Store, and file system with optional encrypted sync; Obsidian or Markdown-style projections can be optional human-readable Knowledge Mirrors rather than the primary source of truth.
- **Development Discipline**: Every change reviewed by `improve-codebase-architecture` before merge

---

## 5. API & External Service Requirements — Free Tier Walkthrough

**Stay fully functional on free tiers during development.**

### xAI Grok 4.3

- Console: https://console.x.ai
- Create free account → API Keys → New key
- Add to `.env` as `XAI_API_KEY`
- Free tier sufficient for personal/high-value capture work (rate-limited but generous for development)

### OpenAI Embeddings

- Console: https://platform.openai.com
- New account receives free credits ($5–18 typical)
- Add to `.env` as `OPENAI_API_KEY`
- Use `text-embedding-3-large` as the single canonical embedding path for Ariadne indexes unless an ADR explicitly defines migration and index isolation.

### Capture Research Source Providers

- Crawl4AI: free/local page crawling and LLM-ready extraction. Set `CRAWL4AI_BASE_URL` only after a local or self-hosted Crawl4AI endpoint is running.
- SearXNG: free/local metasearch discovery. Set `SEARXNG_BASE_URL` only after a local or self-hosted SearXNG endpoint is running.
- SerpApi: optional API-backed SERP/search fallback. Add your existing key to private `.env` as `SERPAPI_API_KEY`.
- Olostep: optional API-backed search, scraping, and crawling fallback. Add your existing key to private `.env` as `OLOSTEP_API_KEY`.
- Firecrawl: optional paid/later provider if quality justifies spend. Add `FIRECRAWL_API_KEY` only when deliberately using Firecrawl credits.
- Vendor free tiers and quotas can change; Ariadne should record provider identity, approval basis, source limits, and budget/free-tier assumptions instead of assuming any one provider remains free forever.
- Provider readiness is exposed at `GET /api/capture-research/source-providers`; it reports provider IDs, source modes, status, missing env-var names, and quality status without returning API keys or base URL values.
- Manual provider smoke checks use `POST /api/capture-research/source-providers/{provider_id}/smoke-check` with explicit approval, covering `crawl4ai_local`, `searxng_local`, `serpapi_live`, `olostep_live`, and `firecrawl_live` when their env vars or local services are configured.
- Manual live collection runs should create a Capture Research Run with bounded public source targets, then call `POST /api/capture-research/runs/{research_run_id}/source-provider-collection` with explicit approval. Automated tests use injected fake provider clients and smoke runners and must not consume SerpApi, Olostep, Firecrawl, or local crawler quota.

### Capture Research Seller Baseline And Requirements Fit

- The first Seller Capability Baseline uses existing accepted Ariadne knowledge and Capture Reference Context, including accepted Evidence Items and Reference Wiki notes. It must attach stable refs with summarized support, assumptions, matched terms, and baseline gaps rather than storing a new seller profile or business-unit profile.
- Requirements Fit Analysis uses the research brief, source findings, selected lenses, and Seller Capability Baseline refs to produce reviewable strengths, weaknesses, qualification risks, proof needs, and follow-up recommendations.
- Requirements fit is exposed through `POST /api/capture-research/runs/{research_run_id}/requirements-fit-analysis` and in the existing Command Center Capture Research panel. It may update the research run with reviewable insight candidates, but it must not create trusted Evidence, Packet, Action Plan, Risk Register, or Call Plan records without explicit downstream review.

### Capture Research Competitive Gap And BCC-Ready Notes

- Competitive Gap Analysis uses Source Findings and Seller Capability Baseline refs to identify reviewable discriminator candidates, vulnerabilities, proof gaps, competitor/incumbent notes, Teaming Partner Needs, and follow-up recommendations.
- Competitive gap is exposed through `POST /api/capture-research/runs/{research_run_id}/competitive-gap-analysis` and in the existing Command Center Capture Research panel with source provenance, seller-baseline refs, confidence, review state, and explicit BCC-ready input labels.
- BCC-ready notes are inputs for later Bidder Comparison Chart generation only. This endpoint must not create BCC rows, scores, slides, artifacts, Milestone Briefing Packet add-ons, or trusted downstream records without a later selected workflow and explicit review.

### Capture Research Selected Lens Analysis

- Selected lens analysis uses Source Findings, Source Profile refs, and Seller Capability Baseline refs to create reviewable outputs for Price-to-Win Research, Burn Rate Analysis, Workload Analysis, and targeted call-plan CRO engagement improvements.
- Selected lens analysis is exposed through `POST /api/capture-research/runs/{research_run_id}/selected-lens-analysis`. The request may use the run's selected lenses or supply a supported subset.
- Price-to-win outputs produce pricing strategy assumptions, confidence, source limitations, and follow-up needs. Burn-rate outputs connect PIID/source-profile context and source findings to funding, timing, recompete, and price/workload implications. Workload outputs connect scope, staffing, timing, funding, and operational complexity assumptions to reviewable follow-up. Call-plan CRO outputs sharpen value, proof, friction, objection, and next-action clarity for customer engagement only.
- All selected lens outputs remain reviewable insight candidates. They do not write trusted Evidence, Packet, Action Plan, Risk Register, Call Plan, price, workload, or artifact records without explicit downstream review.

### Capture Research Reviewable Candidate Projection

- Reviewable downstream candidate projection is exposed through `POST /api/capture-research/runs/{research_run_id}/downstream-candidates`. It prepares grouped candidates for Evidence, Packet, Action Plan, Risk Register, Call Plan, Follow-Up Route, Price/Workload Assumptions, Teaming Partner Needs, and BCC-Ready Notes from Source Findings and generated insight candidates.
- Candidate review decisions are exposed through `POST /api/capture-research/runs/{research_run_id}/downstream-candidates/{candidate_id}/review-decisions` with `accept`, `discard`, and `route` decisions, reviewer rationale, decided timestamp, and routed destination when routing.
- Candidate review decisions preserve provenance to the Capture Research run, research brief, trigger context, Source Findings, Source Profile refs, selected lens, supporting Seller Capability Baseline refs, and source insight candidate. They update candidate review state only; they do not create trusted downstream records automatically.

### Capture Research Data APIs

- SAM.gov: opportunity and entity data; add an API key to `.env` as `SAM_GOV_API_KEY` when needed.
- USAspending.gov: award, agency, and spending context; base URL is public and tracked in `.env.example`.
- BLS: labor, wage, and market context for price-to-win and staffing analysis; add `BLS_API_KEY` when needed.
- api.data.gov: shared key for public-data connectors such as GSA Per Diem and Regulations.gov MCPs; add `API_DATA_GOV_KEY` when needed.

### MCP Tool Integration

- Use MCP for external tool connectors where it keeps the Command Center simpler.
- Keep MCP configuration path and timeout settings in `.env.example`; define actual server wiring only when a connector is selected.

### Zero-Cost Local Stack Candidates

- Ollama (local models): https://ollama.com
- MinerU: candidate generic/multimodal extraction adapter for generic source material and visual source material.
- RAGAnything: candidate future document/RAG pipeline adapter after Ariadne's Extraction Bundle boundary is proven.
- LightRAG: candidate knowledge layer component.
- Project Theseus: candidate future Solicitation Parser Capability for solicitation-family documents.

**`.env.example`**

The committed `.env.example` is a public, secret-free template for Ariadne's known configuration needs. Keep it intentionally lean until architecture decisions are made. Include stable platform settings, model-provider keys, local-model defaults, capture research APIs, MCP tool settings, and local file paths; do not preconfigure undecided internals such as a specific RAG engine, graph database, parser backend, or agent runtime.

Local development uses a private `.env` file that is ignored by git. Update `.env.example` whenever the public configuration shape changes.

Model provider keys, model defaults, local model settings, public-data API settings, and local storage paths should be centralized in `.env` through the typed runtime configuration module rather than hard-coded into workflows, skills, UI components, or agent prompts.

---

## 6. UI/UX Requirements (Command Center Aesthetic)

- Dark cyberpunk theme (deep #0a0a0a background, neon cyan/magenta accents, subtle grid overlays)
- Information-dense but calm — mission-control feel
- Persistent sidebar with opportunity list + decision-gate status
- Custom panels guided by `ui-ux-pro-max`:
  - Quick Capture Inbox (native, frictionless intake for rough notes, ideas, meeting fragments, and uploaded material)
  - Document Intake Queue and Document Intake Command Surface for heavier source material, extraction provenance, recommendations, skill-chain options, and review-gated actions
  - Knowledge Chat (candidate RAG/graph layer + settings)
  - HITL Strategy Sessions (brainstorming, first-principles reviews)
  - Living Capture Plan viewer
  - Living Briefing Packet dashboard
  - Action Plan dashboard
  - Capability Studio for advanced skill/capability management
  - Artifact preview & export
- All major workflows remain inside the single interface, but not all on one page. The Command Center Home should be a pulse-and-routing cockpit; detailed actions belong in focused Work Modes, tabs, pages, or drawers for the work product they change.

## 6.1 Production Command Center UI/UX Plan

The production Command Center should be a capture operating cockpit, not a reporting dashboard, generic chat surface, tool launcher, or one-page mega-scroll. It should let the user open one Opportunity, understand readiness, choose a capture goal, approve or run an assisted route, review output with evidence and provenance, route accepted results into real work products, and see the Living Milestone Decision Briefing Packet, action plan, call/engagement prep, risk signals, and artifacts improve through one coherent interface with focused Work Modes.

The UI is ready for production planning and an MVP-1 production-shaped skeleton, but not final visual polish detached from workflow proof. MVP-1 must include the first working route action inside the Next.js shell: selected goal -> route recommendation -> run/review -> accepted output routed into packet, action, or call-plan work. Deterministic or demo data is acceptable only as a temporary backend stand-in. MVP-4 then hardens the production UI after route-first orchestration, AI/skills integration, and work-product routing prove the interaction model.

Project Theseus is useful inspiration, but not a copy target. Ariadne should adapt Theseus patterns such as Capture Chat, Intel Panels, document/source drawers, Studio artifact provenance, run reasoning, and artifact-to-source traceability into an Ariadne-native command workspace. Theseus is centered on final solicitation ingestion and proposal intelligence; Ariadne is centered on active capture management before, during, and after opportunity pursuit.

External UX research reinforces the same direction: dashboard quality comes from information architecture, not chart volume; command centers need structured decision loops; enterprise SaaS must reduce cognitive load through stable grouping and clear conflict indicators; AI-native UX must expose uncertainty, provenance, review state, and feedback loops; and human-in-the-loop workflows need tiered review, interrupt/resume behavior, and durable routing history.

The default screen should answer six questions quickly:

1. What is the state of this Opportunity?
2. What matters next?
3. What can Ariadne do now?
4. What needs my review?
5. What work product changed?
6. What evidence supports it?

The production desktop layout should use three stable regions plus focused overlays:

- **Left rail: Opportunity and work-mode navigation** with opportunity switcher, lifecycle/gate state, work modes, and badges for review needs or blockers.
- **Main Opportunity dashboard and Living Packet workspace** with descriptive pulse check signals, packet readiness, section navigation, compact answer/gap/risk/recommendation blocks, source chips, evidence status, assumptions, confidence, and inline actions such as "improve this".
- **Embedded command surfaces** inside the main workspace for Autonomy Digest, assisted capture goals, route recommendations, active runs, grouped review queues, and approval controls. Routes should appear next to the packet field, action, call-plan, research, artifact, or review need they advance rather than hanging in a detached right rail.
- **Modal/drawer layer** for low-friction Opportunity Intake, provenance and source previews, Capability Run reasoning, output/artifact preview, and "why this output?" trace.

Mobile and small screens are secondary but must not break. They should use a top Opportunity header, segmented work modes, bottom action bar, and drawers for review/provenance instead of trying to recreate dense desktop parity.

Core interaction loops:

- **Assisted Capture Start**: user chooses a packet field, work-product need, or goal such as preparing a milestone review, improving the packet, preparing a call, resolving evidence gaps, researching customer/competitor/teaming/pricing questions, processing documents, or preparing export.
- **Route Recommendation**: Ariadne shows the need, route, input refs, output destination, autonomy/risk tier, approval requirement, expected cost/time if known, and actions to run, inspect, edit, defer, or discard.
- **Capability Run and Skill Chain**: the UI shows staged progress: prepare inputs, run capability or skill, summarize output, review output, route accepted result.
- **Review and Routing**: review cards are destination-first: Evidence candidate, Packet update, Action item, Call/Engagement prep, Risk signal, Artifact block, or Follow-up route. Each card shows summary, source support, assumptions, gaps, confidence, model/capability provenance, destination, and accept/edit/route/defer/discard/needs-evidence actions.
- **Work Product Update**: after review, the UI shows what changed: packet field updated, readiness improved or still blocked, action created, call-plan prep improved, artifact draft refreshed, or export readiness changed. Important updates should show visible before -> after state.

Production information architecture should include these top-level areas while keeping day-to-day flow centered on the Command Center:

1. **Command Center**: day-to-day workspace and assisted capture loop.
2. **Opportunity Workspace**: one Opportunity, centered on the Living Milestone Decision Briefing Packet.
3. **Action Plan**: outcome tasks, urgency, timelines, ownership, and AI support.
4. **Engagement**: call plans, customer meetings, stakeholder prep, and follow-up commitments.
5. **Research**: capture research briefs, findings, source collection, selected lenses, and review candidates.
6. **Documents**: intake queue, extraction bundles, source spans, and parser-required items.
7. **Artifacts**: drafts, renderer readiness, DOCX, XLSX, and huashu-design outputs.
8. **Capability Studio**: advanced inventory, runs, artifacts, provenance, and validation.

Design system direction:

- Keep the dark, calm, cyberpunk-leaning command aesthetic: deep black/blue surfaces, cyan/magenta accents, restrained glow, and dense but scannable surfaces.
- Use semantic status color for blocked, needs review, trusted, running, ready, and risk states; never rely on color alone for meaning.
- Use icons for repeated actions with tooltips, stable dimensions for packet sections, route cards, review cards, run states, and output previews.
- Preserve accessibility: readable contrast, visible focus states, keyboard navigation, labels for icon-only controls, and clear error/recovery states.
- Avoid nested cards, hero sections, passive metric walls, decorative bloat, and text walls where an action surface is needed.

Anti-convolution rules:

- One primary next action per panel.
- Primary capture work should not live in a persistent right sidebar; pulse checks, routes, reviews, and next-best actions belong in the main Opportunity dashboard or in context-specific drawers/modals.
- Product workflows first, tools second.
- Show actionable status by default; keep details in drawers.
- Every surfaced item must answer "so what?" or "what can I do?"
- Do not create separate pages for every store unless the user workflow requires it.
- Do not make chat the only way to act.
- Do not let graph, RAG, artifact, or studio views compete with the Living Milestone Decision Briefing Packet as the center of gravity.
- Do not build a new UI surface unless it changes a user decision or work product.

MVP UI sequencing:

1. **MVP-1 UI Skeleton + First Route Action**: build the production-shaped Next.js Opportunity workspace, main packet/dashboard panel, embedded route/review surfaces, active-run drawer, provenance drawer, and one working route action. FastAPI remains fallback/debug only.
2. **MVP-2 AI/Skills UI**: add capability route cards, skill-chain stage view, model-role display, approval prompts, run progress, output summary, and provenance.
3. **MVP-3 Work Product UI**: add packet update review, call/engagement prep, action-plan update flow, risk/follow-up routing, and work-product before/after state.
4. **MVP-4 Production UI Hardening**: complete responsive polish, accessibility pass, keyboard navigation, empty/loading/error states, component cleanup, and explicit user review of the first real UI shape.
5. **MVP-5 Renderer UI**: add reviewed draft preview, DOCX export status, XLSX export status, huashu-design visual/PPTX-capable action/status, and private Artifact Export Profile selection.

The production UI is good enough for MVP only when the user can open one Opportunity, understand readiness in roughly 30 seconds, start assisted capture in one click, approve or run a route without hunting through tools, review output with evidence/provenance visible, route the result into packet/action/call/artifact work, see the work product change, export DOCX/XLSX/first huashu-design output from reviewed content, and recover from errors without losing context.

The supporting planning note is `docs/architecture/production-command-center-ui-plan.md`, but this PRD remains the product source of truth.

## 6.2 First Flagship Workflow: Milestone Decision Briefing Packet

The first flagship product workflow is the Milestone Decision Briefing Packet because it becomes the strategic foundation for the rest of Ariadne. It forces the platform to gather multi-source capture data, connect opportunity-specific knowledge to reusable insight, surface gaps across core capture workstreams, recommend next actions, manage dates and owners, and produce a professional decision-support artifact.

Gate decisions in Ariadne are the Milestone 1, Milestone 2, Milestone 3, and Milestone 4 decisions for an Opportunity, not generic workflow approvals. Each Opportunity should have a Living Milestone Decision Briefing Packet, also understandable as the Living Milestone Gate Briefing Packet, that acts as the primary roadmap for the current phase. Everything Ariadne gathers, ingests, analyzes, researches, brainstorms, drafts, routes, or reviews should either fill the relevant packet, expose a packet gap, create an action to close that gap, or provide explicit support for the next milestone gate decision.

The packet roadmap must be stage-relative. When an Opportunity is preparing for Milestone 1, 2, 3, or 4, the Living Briefing Packet should show the data elements needed for that specific gate, which ones are populated, which ones are weak or stale, which ones are still gaps, and what action would most likely close each gap. Recommended routes may include customer call planning, customer questions, document intake, capture research, competitor or teaming search, company capability gap analysis, supplier-diversity or small-business-liaison outreach, APEX Accelerator support, partner-event follow-up, or an artifact/visual content recommendation.

The workflow should use the generic structure in `docs/reference/generic-milestone-intelligence-checklist.md` as public, company-agnostic inspiration. The checklist must remain free of company-specific template names, internal review-body names, CRM assumptions, local file paths, or proprietary labels.

Initial packet output should be evidence-first. It should include evidence status, source quality, source traceability, assumptions, confidence, gaps, risks, win probability rationale, recommended Milestone 1-4 gate action, dated next actions, and mentor-style explanations that teach the user why each item matters. Ariadne may recommend action before every answer is complete, but it must clearly show what is sourced, what is inferred, what remains unknown, and whether closing a gap requires a next action or a new platform capability. This evidence discipline should steer frontier-model reasoning toward auditable capture outcomes without constraining hypothesis generation, synthesis, or strategic judgment.

The packet should exist first as a Living Briefing Packet dashboard inside the Command Center, with slide-like packet sections, packet readiness labels, evidence/gap status, risks, actions, and mentor explanations visible before export. The dashboard should be useful even when the packet is not decision-ready: early versions become the work plan for closing gaps. Packet sections are the user-facing skin, while core capture workstreams and Evidence Items are the underlying readiness and evidence structure. The internal packet sections should form a company-agnostic Canonical Packet Section Model inspired by the user's real briefing needs, while the Milestone Intelligence Checklist supplies the questions and evidence prompts that populate those sections. The exact private deck/template format can be handled later through an Artifact Export Profile. When ready, the user can trigger the Artifact Renderer, including huashu-design where appropriate, to export the packet through a private Artifact Export Profile into a user- or organization-specific format. Private templates and organization-specific mappings must remain out of the public repo.

The user must also have freedom to add packet content beyond the default checklist. If the user or Ariadne identifies that an infographic, comparison visual, timeline, capability map, customer-org visual, opportunity synopsis add-on, partner ecosystem view, or other explanatory block would improve the gate packet, Ariadne should record it as a reviewable packet content opportunity tied to the relevant section and gate. During MVP, Ariadne may recommend the appropriate artifact route and stage the structured content request; final huashu-design/PPTX-capable rendering remains part of the practical artifact rendering/export path rather than an automatic packet mutation.

The Living Briefing Packet should support both a Briefing View and a Coverage View. The Briefing View is the primary working surface for Milestone 1-4 gate judgment, leadership-ready status, risks, recommendations, and next actions. The Coverage View is the supporting evidence matrix for checklist questions, source traceability, gaps, assumptions, and validation state. The user should manage outcomes, approvals, relationships, and strategy while Ariadne performs the under-the-hood research, synthesis, note organization, artifact drafting, and action-plan maintenance through guided capture workflows.

Ariadne should use tiered autonomy for assisted execution. Low-risk administrative work such as ingestion, tagging, summarization, date extraction, duplicate detection, coverage scoring, and draft gap lists may run automatically. Credit-spending research, broad web searches, external tool calls, major packet regeneration, and artifact rendering should ask before running. Gate decisions, Insight Promotion, customer-facing artifacts, external communications, evidence deletion, sensitive label changes, and final packet exports require human approval.

The primary Command Center experience should be product-workflow first, not toolchain-first. The user should normally choose outcomes such as building a milestone packet, creating a call plan, researching competitors, preparing an engagement artifact, or updating the action plan from notes. Most work items should eventually become command surfaces with context-aware AI actions: handle the action, prepare the artifact, route the question, launch a capability module, or recommend the next product workflow. Skills, skill chains, CLI harnesses, MCP tools, parser adapters, renderer adapters, and model workflows should operate as Capability Modules behind those product workflows. Because Ariadne is built for a single user-developer, it should also include an advanced Capability Studio for adding, testing, refining, and validating capability modules without making capability management the default capture workflow.

The Capability Studio should be visible from the main Command Center but presented as an advanced/admin surface rather than equal-weight capture navigation. It can borrow inspiration from Project Theseus while improving the architecture for Ariadne: dual-use `.github/skills/` files remain the authoring source for workspace skills; product workflows decide when capability modules are useful; capability cataloging should support filtering by lifecycle state, core capture workstream, product workflow, capability type, and maturity; each Capability Run should preserve provenance; and a Capability Artifact Library should let the user inspect outputs, source links, run rationale, and evidence connections before promoting anything into Opportunity Knowledge, reusable insights, or final artifacts.

Capability Studio should start with a safer local catalog and quality workflow before supporting third-party installation from GitHub, skills.sh, or other catalogs. The first version should show installed/local capability modules, metadata, maturity, related product workflows, test prompts, validation status, run history, artifacts, and provenance. Capability run outputs should land in review so the user can accept, refine, iterate, promote, or discard them before they become trusted Evidence Items, Opportunity Knowledge, Action Plan Items, reusable insights, or final artifacts. Iteration should be versioned so the original output, user feedback, revised outputs, accepted version, and promotion history remain traceable. Some capability modules are one-shot or batch workflows, while others are Interactive Capability Sessions that require back-and-forth user input, staged decisions, or clarification during execution, such as design/rendering workflows or grilling-style strategy sessions. Interactive Capability Sessions should be reusable across session contexts: product mode when tied to an Opportunity or product workflow, studio mode when testing or refining the module itself, and exploratory mode when the user is learning, researching, or ideating before a specific Opportunity exists. The architecture should keep the capability module reusable and pass context into it rather than duplicating separate implementations for each UI surface. Third-party installation can come later after trust, path safety, versioning, rollback, and provenance guardrails exist.

Exploratory Capture Sessions should be saved as first-class knowledge objects even when they are not tied to a specific Opportunity. They may later become reusable insights, raw capture items, action items, new Opportunities, artifact drafts, skill ideas, or workflow improvements. Hermes should be able to observe saved product, studio, and exploratory sessions for Operational Learning so Ariadne can recommend improvements to workflows, capability modules, action plans, and mentoring behavior over time, while keeping durable knowledge changes, final artifacts, and user-facing decisions under review or approval.

Hermes may propose improvements to Ariadne itself through human-reviewed Improvement Proposals. These can recommend new capability modules, skill refinements, workflow changes, checklist updates, product views, issues, documentation edits, or PRD changes based on observed friction and repeated user behavior. Hermes must not automatically change durable product behavior, public documentation, code, or source-of-truth knowledge without user approval.

Every Opportunity should have a first-class Capture Action Plan. Action plan items should carry the action, why it matters, owner, due date, related lifecycle state, related core capture workstream, related packet section, evidence or gap addressed, autonomy tier, status, and recommended next step. The Action Plan dashboard should support multiple views rather than a single task board: a focused next-actions list, status board, timeline or calendar view, filters by workstream/packet section/readiness/gap, and task detail views that show supporting evidence and mentor explanations. The primary UI should show outcome-level tasks while keeping lower-level AI execution details available on expansion, so the user manages capture outcomes while Ariadne manages supporting execution.

Quick Capture should follow a low-friction idea-capture pattern: let the user dump rough thoughts, meeting fragments, stray ideas, pasted text, or uploaded files quickly, then let Ariadne classify, polish, connect, and route them through a Knowledge Processing Workflow. Ariadne should use Capture Reference Context, including the imported Project Ariadne public-source knowledge, to infer useful Capture Intelligence Drafts from rushed raw material while keeping promotion into trusted knowledge review-gated. Trusted evidence should save the polished Capture Intelligence Draft output, not the truly raw note; raw source text is retained only as trace/admin context for auditability. If a note is too low-signal for Ariadne to infer useful capture intel, it should create a clarification request back to the user instead of becoming evidence. The Capture Intelligence Draft review surface should become a command-and-action workspace: the user can accept, edit, discard, route follow-up questions, launch research, request a skill or skill chain, or prepare artifacts such as call plan recommendations when the draft implies customer engagement is needed. Review and routing should operate on individual draft parts, not only on whole-draft summaries, because some intelligence will be deterministic and low-risk while other pieces need careful curation. The surface should also support bulk selection for repeated low-risk or same-route actions, while preserving per-piece review, provenance, and override controls. Ariadne should suggest relevant skill chains or product workflows per draft part and flag opportunities for Hermes to create or improve a skill when no suitable capability exists. The first stage can use lightweight Reference Wiki retrieval over local Markdown/frontmatter/wikilink-style notes before a full vector database or RAG engine exists. Processing can create Evidence Items, Opportunity Knowledge, Action Plan Items, Reusable Capture Insight candidates, or follow-up questions. Pasted text and simple text or Markdown uploads should become Raw Capture Items with source metadata and follow the same Capture Intelligence Draft path as manual notes. Lightweight uploads can begin in Quick Capture, while heavier source material should move into the Document Intake Queue for classification, extraction status, parser requirements, source-span review, warnings, and document-derived action. The Command Center should keep an end-to-end demo thread for this workflow showing messy raw input, Reference Wiki influences, draft inferences, review controls, accepted evidence/action/packet outputs, discarded outputs, and trace links back to raw input and draft rationale.

The completed Document Intake Command Surface turns uploaded source material into extraction provenance, Capture Intelligence Draft Parts, recommendations, skill-chain options, and review-gated actions. The Command Center is not a passive data center: document-derived data should be shown with what Ariadne recommends next, which skill chains or product workflows are relevant, what source spans can become Evidence Items, and which Action Plan, Packet, Risk Register, Call Plan, and Knowledge Note Projection candidates need review. The first tracer bullet supports generic source material end to end: upload or register source material, classify it, persist a Document Intake Store record, create an Extraction Bundle, convert useful findings into Capture Intelligence Draft Parts, surface recommendations and skill-chain options, accept source spans into Evidence Items, create review-gated candidates for downstream capture work, generate a Knowledge Note Projection, and show the workflow in the Command Center.

Document Intake should use an Extraction Bundle as the shared parser output contract before any parser or retrieval engine becomes trusted knowledge. An Extraction Bundle should carry source material metadata, Source Spans, Entity Candidates, Relationship Candidates, Extraction Warnings, confidence, parser provenance, and review state. The first ontology core should stay intentionally small: Document, Source Span, Entity Candidate, Relationship Candidate, and Extraction Warning. Initial entity candidates should cover customer, organization, stakeholder, opportunity, requirement or need, date or milestone, risk, action or commitment, artifact or document, capability, and discriminator. Initial relationship candidates should cover mentions, supports, creates risk, addresses need, owned by, due on, related to opportunity, and evidence for. Extraction Bundles provide trace context; Capture Intelligence Draft Parts remain the primary user review, recommendation, skill-chain, and assisted-execution surface.

Document Intake classification should begin with four buckets. **Generic Source Material** includes non-solicitation material such as articles, customer slide decks, conference material, transcripts, briefings, notes, screenshots, or photos that can inform capture work through generic extraction and review. **Visual Source Material** includes images, screenshots, scans, or photos of physical or digital material; the first slice should record, classify, and preserve this material with provenance, while OCR, image understanding, and multimodal extraction remain deferred behind a future Multimodal Extraction Capability. **Solicitation Documents** include buyer-issued opportunity documents such as RFIs, Sources Soughts, draft RFPs, final RFPs, amendments, instructions, requirements attachments, and evaluation-related files; these should be queued for a future Solicitation Parser Capability, with Project Theseus treated as the likely specialized adapter rather than something Ariadne rebuilds casually. **Unsupported Documents** are documents Ariadne records but cannot currently extract because of adapter, readability, encryption, unknown type, or parser gaps; unsupported means a capability gap, not a refusal to process the document. Document sensitivity should affect Autonomy Tier, review, approval, and trace handling rather than whether Ariadne records the material for intake.

The first Document Intake Store should be narrow and local-first. It should persist only records needed for this workflow: intake records, Extraction Bundles, review decisions, accepted evidence links, and generated Knowledge Note Projections. It should not become a broad storage-platform epic. Accepted document-derived source spans become trusted Evidence Items with lineage back to the intake record, Extraction Bundle, source span, parser provenance, source ref, confidence, warnings, and review rationale. Recommendations, skill-chain options, inferred tasks, packet updates, risks, call-plan signals, and note projections remain review-gated command-surface candidates until the user accepts or routes them. Knowledge Note Projections should be one-way Markdown-style notes over accepted Ariadne knowledge so humans and lightweight retrieval can browse connected context without making notes the source of truth.

Document Intake should use tiered autonomy. Low-risk local work such as ingestion, classification, extraction, source-span capture, and draft preparation may run automatically. Trusted promotion, external tool calls, broad research, deletion, sensitive label changes, and customer-facing outputs require approval. MinerU, RAGAnything, LightRAG, OCR/frontier multimodal extraction, and Theseus should remain future Capability Modules or Knowledge Layer adapters until the Extraction Bundle boundary and review routing are proven.

Risk Register work should follow the same evidence-first pattern as the Living Briefing Packet and Call Plan. Private workbook files stay local and ignored, while Ariadne models normalized Risk Register Items, Risk Response Plans, scoring, evidence links, packet-field connections, call-plan signal connections, and action-plan follow-through as review-gated product workflow data.

Quick Capture may optionally use a Local Admin Model such as an Ollama-hosted Qwen model for low-risk draft support, but deterministic heuristic processing must remain the default and must work when the local model is unavailable. Local admin assist should reuse central local-model configuration such as `OLLAMA_HOST` and `LOCAL_DAILY_MODEL` rather than introducing workflow-specific model names. Capture Intelligence Draft provenance should show whether local model assistance was used, unavailable, invalid, or disabled.

The Knowledge Layer should include a Knowledge Graph View that visualizes Ariadne's primary structured knowledge: opportunities, evidence items, core capture workstreams, packet sections, action plan items, artifacts, and reusable capture insights. The first stage should be Graph Sensemaking Mode for exploration and understanding. A later stage can add Graph Action Mode so selected nodes can create actions, suggest Insight Promotion, generate briefing sections, or launch research workflows. Obsidian may mirror selected knowledge into readable notes for browsing and reflection, but graph visualization should be built from Ariadne's source knowledge model rather than relying on Obsidian vault conventions.

If Obsidian or another Knowledge Mirror is edited directly, those edits should return to Ariadne as Mirror Update Proposals rather than directly overwriting structured knowledge. Ariadne should classify, validate, and route those proposals through the same Knowledge Processing Workflow used by Quick Capture so traceability and source-of-truth discipline are preserved.

The completed Federal Data MCP Foundation + USAspending Recompete Intelligence Intake epic registers all eight upstream 1102tools federal data MCPs as manifest-only Federal Data Capabilities while deeply integrating USAspending first through a structured PIID Contract Intelligence Profile. The profile starts from one contract number and produces award baseline, burn posture, vehicle context, deterministic pivots, gaps, recommended enrichments, Hermes-observable events, and review-gated candidates. It remains structured source data for artifacts, skills, renderer capabilities, and future agent behavior; DOCX, XLSX, and huashu-design output now belong in the MVP renderer path, while 1102 deliverable skills, LangGraph, and Hermes runtime behavior remain later unless needed to unlock the MVP loop. Provider-backed source collection is now selected only inside the later Capture Research Enrichment workflow.

## 6.3 Completed Epic PRD: SAM.gov Enrichment Profile

### Problem Statement

Ariadne can now turn one PIID or contract number into a structured USAspending-backed recompete intelligence spine, but the capture professional still needs official acquisition-facing context from SAM.gov. Many real opportunities do not start with a clean solicitation ID. The user may only know a customer office, program name, legacy program name, vague description, NAICS/PSC signal, incumbent, or vendor ecosystem clue. Current and prior SAM.gov postings may also include documents that should enter Document Intake, but Ariadne does not yet discover, download, classify, or route those official attachments.

The problem is not simply “look up a solicitation.” The user needs a command-first SAM.gov workflow that can enrich a recompete or opportunity with entity records, known notices, discovery searches, official attachment intake, source limitations, and review-gated next actions without blurring official SAM.gov data with web research, fake tests, or trusted downstream knowledge.

### Solution

The completed **SAM.gov Enrichment Profile** combines four lanes in one reviewable command surface:

1. **Entity Record lane** for official SAM.gov entity registration or responsibility records used in incumbent, parent-company, vendor ecosystem, competitor, subcontractor, and teaming research.
2. **Known Opportunity lane** for official SAM.gov opportunity records found from a solicitation number, notice ID, or other clean pivot.
3. **Opportunity Discovery lane** for finding RFIs, Sources Sought notices, Special Notices, solicitations, and related notices when no solicitation ID exists yet, using customer, office, program-name, description, keyword, renamed-program, NAICS/PSC, set-aside, and date-window signals.
4. **Opportunity Attachment Intake lane** for discovering official SAM.gov description links and resource links, asking before download, downloading approved official links, and routing those files into Document Intake.

The product should call live SAM.gov by default for user-triggered workflows when `SAM_GOV_API_KEY` is configured. Automated tests should use fake adapters for deterministic coverage, but fixture output must be clearly labeled and must never be treated as proof of live source success. Every profile/result should carry provenance source mode such as `live_sam_gov`, `fake_adapter_test`, or `demo_fixture`.

The SAM.gov profile is a structured, reviewable source profile. It may create candidates for Evidence, Packet Field Answers, Action Plan Items, Risk Register signals, Call Plan signals, and follow-up enrichment routes, but trusted downstream records require user review.

### User Stories

1. As a capture professional, I want to enrich a PIID profile with official SAM.gov data, so that my recompete research includes current acquisition-facing signals.
2. As a capture professional, I want a single SAM.gov Enrichment Profile, so that entity, opportunity, discovery, and attachment signals stay connected in one command surface.
3. As a capture professional, I want to search SAM.gov by UEI, so that I can validate an incumbent or vendor against official entity records.
4. As a capture professional, I want to search SAM.gov by vendor name, so that I can find possible matches even when I do not know the UEI.
5. As a capture professional, I want SAM.gov Entity Records to show registration and responsibility signals, so that I can assess vendor suitability and follow-up needs.
6. As a capture professional, I want parent-company or hierarchy clues when available, so that I can understand a vendor ecosystem more deeply.
7. As a capture professional, I want NAICS, PSC, business-type, and socioeconomic signals from entity records, so that I can compare company positioning against opportunity needs.
8. As a capture professional, I want entity records to suggest subcontractor, competitor, and teaming leads, so that I can plan outreach and partner strategy.
9. As a capture professional, I want Ariadne to preserve source limitations on SAM.gov entity data, so that I do not over-trust incomplete public records.
10. As a capture professional, I want to look up a known solicitation number or notice ID, so that I can connect a clean opportunity pivot to official SAM.gov records.
11. As a capture professional, I want official opportunity records to show notice type, title, customer, office, posted date, response deadline, set-aside, NAICS, PSC, and contact signals, so that I can understand timing and qualification quickly.
12. As a capture professional, I want to discover opportunities without a solicitation ID, so that early or renamed programs can still be researched.
13. As a capture professional, I want to search by customer agency and office, so that I can find notices from the buying organization I care about.
14. As a capture professional, I want to search by program name, old program name, description, and keywords, so that I can handle renamed or ambiguous programs.
15. As a capture professional, I want to filter discovery by notice type such as RFI, Sources Sought, Special Notice, solicitation, and combined synopsis/solicitation, so that I can focus on the right acquisition phase.
16. As a capture professional, I want discovery to use NAICS, PSC, set-aside, posted date, response date, and place-of-performance clues when available, so that search results are relevant.
17. As a capture professional, I want discovery results to include match rationale and confidence, so that I can judge whether a notice is actually relevant.
18. As a capture professional, I want weak or ambiguous SAM.gov results to create a deferred Web Enrichment Support route, so that Firecrawl-style research can be launched later without polluting official SAM.gov records.
19. As a capture professional, I want Ariadne to discover documents attached to new SAM.gov postings, so that official solicitation material does not stay outside the capture workflow.
20. As a capture professional, I want Ariadne to discover documents from prior or archived solicitations when official links are available, so that recompete research can use historical acquisition material.
21. As a capture professional, I want Ariadne to ask before downloading SAM.gov attachments, so that I control document intake and avoid surprise external activity.
22. As a capture professional, I want downloaded SAM.gov documents to enter the Document Intake Queue, so that they follow Ariadne's existing extraction, review, and parser-boundary rules.
23. As a capture professional, I want downloaded RFIs, Sources Sought notices, draft RFPs, final RFPs, amendments, and requirements attachments to be classified as Solicitation Documents, so that they can route to a future Solicitation Parser Capability.
24. As a capture professional, I want generic SAM.gov attachments to use generic Document Intake when appropriate, so that non-solicitation material can still produce useful source spans and draft intelligence.
25. As a capture professional, I want inaccessible or missing historical documents to become source limitations, so that the profile remains honest about what it could not retrieve.
26. As a capture professional, I want every SAM.gov result to show whether it came from live SAM.gov, a fake adapter test, or a demo fixture, so that I know what can be trusted.
27. As a capture professional, I want live user-triggered workflows to use real SAM.gov connections by default, so that Ariadne gets current source data when I ask for it.
28. As a developer, I want automated tests to use fake adapter data that is clearly marked, so that tests are deterministic without pretending live SAM.gov succeeded.
29. As a developer, I want fake tests to cover broad and messy scenarios, so that Ariadne handles multiple matches, pagination, attachments, auth/rate failures, inaccessible documents, and no-result cases.
30. As a capture professional, I want SAM.gov profile outputs to become review-gated candidates, so that I can accept, route, discard, or defer them before they affect trusted capture records.
31. As a capture professional, I want SAM.gov enrichment to suggest Packet Field Answer candidates, so that official data can help fill customer, office, incumbent, timing, competition, set-aside, requirement, and risk fields.
32. As a capture professional, I want SAM.gov enrichment to suggest Action Plan Items, so that follow-up research, customer engagement, attachment review, and parser-required work become managed capture tasks.
33. As a capture professional, I want SAM.gov enrichment to suggest Risk Register signals, so that timing, competition, set-aside fit, source gaps, and vendor ecosystem concerns are visible before gate decisions.
34. As a capture professional, I want SAM.gov enrichment to suggest Call Plan signals, so that customer office validation, POC follow-up, pre-solicitation engagement, and teaming outreach can be prepared.
35. As a capture professional, I want the Command Center to show SAM.gov enrichment as active capture work, so that the data turns into recommendations, decisions, routes, and actions.

### Implementation Decisions

- Build a deep SAM.gov profile module with a small interface for creating, persisting, listing, and reviewing SAM.gov Enrichment Profiles.
- Keep the profile model structured around the four accepted lanes: Entity Record, Known Opportunity, Opportunity Discovery, and Opportunity Attachment Intake.
- Keep SAM.gov search, entity, and opportunity data behind the upstream `sam-gov-mcp` Federal Data Capability adapter; do not build a duplicate Ariadne SAM.gov MCP.
- Allow direct official-link fetching only for user-approved attachment downloads surfaced by SAM.gov results.
- Route approved downloaded attachments into Document Intake with provenance back to the SAM.gov profile, opportunity record, source URL, and source mode.
- Let Document Intake classification determine whether downloaded material follows generic extraction or waits for a future Solicitation Parser Capability such as Project Theseus.
- Persist profile source limitations when SAM.gov fields, historical versions, archived documents, attachments, or hierarchy details are missing or inaccessible.
- Keep provider-backed web enrichment as a deferred Web Enrichment Support route, not part of the first SAM.gov implementation.
- Add provenance source mode values for live SAM.gov, fake adapter tests, and demo fixtures. Fake and demo output must not be eligible for normal trusted Evidence promotion.
- User-triggered product workflows should call live SAM.gov by default when the private key is configured. Page render should not trigger live calls.
- The Command Center should show saved SAM.gov profiles, live-readiness status, profile lanes, source limitations, review candidates, attachment download state, and Document Intake links.
- Implemented on epic branch `05-build/sam-gov-enrichment-profile`, with progression branches for domain/store, adapter, attachment intake, and command surface work.

### Testing Decisions

- Test external behavior: profile creation, source-mode provenance, candidate projection, review gating, persistence, attachment intake behavior, Document Intake routing, and API/Command Center responses.
- Do not write tests that only verify private helper structure or implementation details.
- Normal automated tests should use fake SAM.gov adapter responses so the suite is deterministic and does not require private secrets or live network access.
- Fake test fixtures should be broad rather than tiny: cover multiple entity matches, hierarchy clues, known opportunity matches, discovery searches, active and archived notices, pagination, attachments, inaccessible documents, no-result cases, auth failures, rate failures, and source limitations.
- Fake-adapter tests must assert that fixture output is labeled as fake or demo data and is not reported as proof of live SAM.gov success.
- Live SAM.gov behavior can have separate local validation, but normal CI/unit tests must not depend on live SAM.gov availability.
- Prior test patterns include PIID Contract Intelligence Profile tests for structured profile creation, Federal Data Capability tests for MCP registry and secret-safe behavior, Document Intake tests for queueing/classification/extraction boundaries, and runtime tests for FastAPI route behavior.

### Out of Scope For This Epic Slice

This list means these capabilities were not built inside the SAM.gov Enrichment Profile slice. It does not remove them from Ariadne's production platform scope. Deferred production capabilities must re-enter through the MVP Roadmap or a future documented integration slice; the enduring constraints are review gates, source provenance, and no unsafe access bypass.

**Deferred platform capabilities**

- Firecrawl or broad web enrichment.
- Direct non-SAM web crawling or guessing hidden attachment URLs.
- Solicitation parsing with Project Theseus or another parser.
- MinerU, RAGAnything, LightRAG, OCR, or multimodal extraction.
- Artifact Renderer, DOCX, XLSX, or huashu-design export.
- Hermes runtime, autonomous tool choice, operational learning, or workflow mutation.
- Skill chaining or LangGraph orchestration.
- Product workflows for BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, and Regulations.gov.
- Full Next.js UI migration.

**Trust and safety boundaries**

- Automatic trusted downstream promotion from SAM.gov results or downloaded documents.

### Further Notes

This epic extends ADR 0007 and ADR 0006 rather than requiring a new ADR. ADR 0007 keeps federal data access behind upstream 1102tools Federal Data Capabilities. ADR 0006 keeps parser and retrieval outputs behind Document Intake's Extraction Bundle and review boundaries. The SAM.gov plan and implementation trail are recorded in `docs/architecture/sam-gov-enrichment-plan.md`.

## 6.4 Selected Epic PRD: Capture Research Enrichment

### Problem Statement

Ariadne can now build structured official-source profiles from USAspending and SAM.gov, and it can assemble deterministic Opportunity Knowledge Context from accepted and reviewable records. But real capture work still requires targeted external research: customer context, competitor positioning, incumbent signals, teaming gaps, public proof, price/workload assumptions, and requirement-fit analysis. Without a product workflow for this, source providers, marketing skills, seller knowledge, and future agent coordination would become disconnected tool calls or detached research reports.

The user needs Ariadne to turn source-profile gaps, ambiguous official signals, packet/action needs, or bounded research prompts into traceable research findings and reviewable capture implications that feed existing work surfaces.

### Solution

The selected **Capture Research Enrichment** epic creates a bounded research workflow:

1. Start from an Opportunity, PIID or SAM.gov Source Profile gap, Opportunity Knowledge Context gap, packet need, action-plan need, or User-Prompted Research Request.
2. Create a Capture Research Brief that states the research question, known pivots, source targets, selected research lenses, evidence goals, source limits, and approval basis.
3. Use existing Source Profiles and a small Research Trigger Context snapshot by reference rather than copying full deterministic profiles.
4. Use accepted Ariadne knowledge, Capture Reference Context, and the Reference Wiki as the first Seller Capability Baseline.
5. Run live provider-backed Web Source Collection when a local provider or API key is configured and the run is explicitly approved or covered by a future approved autonomy policy. Automated tests use fake source-collection adapters.
6. Convert collected public-source material into Source Findings with URL/source provenance, timestamps, limitations, and capability trace.
7. Apply selected Shipley-aligned capture lenses, including customer research, competitor profiling, product/positioning, sales enablement, pricing, workload analysis, price-to-win thinking, and targeted CRO for call-plan or engagement-friction questions.
8. Produce reviewable Marketing Insight Candidates, Requirements Fit Analysis, Competitive Gap Analysis, Teaming Partner Needs, price/workload assumptions, Evidence candidates, Packet candidates, Action Plan candidates, Risk Register candidates, Call Plan candidates, and follow-up routes.
9. Show one Capture Research Enrichment run in a Command Surface, with a readable Research Summary View and review controls on the underlying findings and candidates.

The first slice should prove the fixed product sequence before adding LangGraph, Hermes runtime, general skill chaining, or autonomous multi-step research.

### User Stories

1. As a capture professional, I want a PIID or SAM.gov source limitation to launch bounded research, so that ambiguous official data becomes actionable without polluting official records.
2. As a capture professional, I want to start a user-prompted research request when I do not yet have deterministic details, so that exploratory research can still enter Ariadne's reviewable workflow.
3. As a capture professional, I want Ariadne to use configured live source providers when approved, so that public web research can support real capture work without depending on one paid credit meter.
4. As a capture professional, I want every web finding to show its source URL, collection time, source type, and limitation, so that I can trust or reject the research appropriately.
5. As a capture professional, I want competitor research to compare competitors against my seller baseline, so that it helps requirements fit, discriminators, vulnerabilities, and teaming strategy rather than becoming isolated competitor notes.
6. As a capture professional, I want the seller baseline to draw from accepted Ariadne knowledge and the Reference Wiki, so that Project Ariadne knowledge becomes useful in active opportunity work.
7. As a capture professional, I want price-to-win, burn-rate, and workload assumptions to connect USAspending/SAM.gov context with public findings, so that pricing and scope risks are surfaced early.
8. As a capture professional, I want CRO-style analysis to help sharpen call-plan asks and engagement recommendations, so that customer interactions have clearer next actions and less friction.
9. As a capture professional, I want research output to create reviewable Evidence, Packet, Action Plan, Risk Register, and Call Plan candidates, so that research moves capture execution forward.
10. As a capture professional, I want Bidder Comparison Chart-ready evidence and analysis when relevant, but not a full BCC slide-generation workflow in this first slice.

### Implementation Decisions

- Build a narrow Capture Research Enrichment domain module and local store.
- Persist research briefs, trigger context, source-profile refs, source collection records, source findings, seller-baseline refs, selected lenses, insight candidates, review decisions, and downstream candidate links.
- Keep Capability Runs available for execution/provenance detail, while the Capture Research Enrichment Store owns product workflow meaning.
- Reference PIID and SAM.gov Source Profiles by ID and source-profile element; do not embed full source-profile records.
- Preserve a small Research Trigger Context snapshot so a research brief remains auditable if the source profile later changes.
- Use a source-provider registry for live Web Source Collection. Page render must not trigger live calls.
- Prefer Crawl4AI and SearXNG for free/local capability, SerpApi and Olostep for optional API-backed fallback, and Firecrawl only as optional later paid fallback.
- Require a configured provider and explicit user approval or future approved autonomy policy before a live provider run.
- Keep restricted or logged-in sites such as LinkedIn and X out of first-slice crawling unless the user provides exports, notes, screenshots, or other user-mediated material. Do not bypass login, paywall, or anti-bot controls.
- Treat Grokipedia or similar public references as possible source targets when relevant, with provenance and source limitations.
- Use the installed `coreyhaines31/marketingskills` pack as capability inventory, but choose a narrow lens set per Capture Research Brief.
- Prioritize Shipley capture principles: customer understanding, hot buttons, evaluation criteria, discriminators, proof, competitive position, price-to-win, workload, call-plan questions, and gate-decision implications.
- Feed Bidder Comparison Chart and Milestone Briefing Packet add-on work later, but do not make BCC artifact generation the core first-slice deliverable.

### Testing Decisions

- Automated tests should use fake source-collection adapters and must not depend on private credentials, live network access, paid credits, or a running local crawler/search service.
- Fake and demo source output must carry source-mode provenance and must not be presented as live source success.
- Tests should cover research brief creation, source-profile refs, trigger context, approval boundaries, source finding creation, seller-baseline refs, selected lenses, candidate projection, review decisions, persistence, and Command Center responses.
- Tests should assert Capture Research Enrichment references PIID/SAM.gov profiles instead of duplicating deterministic source-profile fields.
- Optional local validation can run live provider smoke checks when the relevant local service or private API key is configured, but that is outside the normal unit-test path.

### Out of Scope For This Epic Slice

This list means these capabilities were not built inside the first Capture Research Enrichment slice. It does not mean they are outside the production Ariadne platform. Many are core production features and are now mapped into the MVP Roadmap: route-first orchestration, AI and skills integration, production Command Center UI/UX, artifact rendering/export, document/solicitation intake integration, Hermes, graph/RAG, and broader external-data workflows. The only durable exclusions are unsafe source-access behavior and unreviewed trusted promotion.

**Deferred platform capabilities**

- LangGraph, general skill-chain orchestration, or Hermes runtime.
- Autonomous live research beyond explicit user-triggered or future approved-policy runs.
- BLS, GSA CALC, or GSA Per Diem product integrations, except as future recommended routes or manually provided context.
- Full subaward, customer, vehicle, or competitor profile products beyond first-slice research outputs.
- Bidder Comparison Chart artifact generation or Milestone Briefing Packet slide rendering.
- A new seller-profile editor or dedicated KBR/business-unit profile store.
- Semantic retrieval/RAG, persisted indexes, graph database, Knowledge Graph View, or cross-opportunity inferred matching.
- Project Theseus solicitation parsing, MinerU, OCR, or multimodal extraction.
- Artifact Renderer, DOCX, XLSX, or huashu-design export.
- Full Next.js UI migration.

**Trust and safety boundaries**

- Browser-mediated logged-in source access for LinkedIn, X, or other restricted platforms remains deferred unless a future User-Mediated Source Access workflow preserves explicit user authorization, provenance, and access limits.
- Paywall, login, or anti-bot bypass is not allowed.
- Automatic trusted downstream promotion from research findings or insight candidates is not allowed without an explicit future Graduated Autonomy decision and human-approved safety rules.

### Further Notes

This epic extends existing ADRs and architecture notes rather than requiring a new ADR. ADR 0006 keeps parser and retrieval outputs behind Document Intake's Extraction Bundle and review boundaries. ADR 0007 keeps federal data access behind upstream 1102tools Federal Data Capabilities. The Capability Run Foundation keeps execution provenance reviewable. The Knowledge Layer Foundation keeps structured context deterministic and non-authoritative. Create a new ADR only if a later decision adopts a workflow engine, autonomous live-research policy, new storage engine, or automatic trusted-write model.

The selected plan and implementation trail live in `docs/architecture/capture-research-enrichment-plan.md`.

## 6.5 Future Capability Integration Strategy

The early build slices were intentionally narrow, but they must create stable attachment points for the systems named in the North Star. Hermes, graph visualization, MinerU, RAG, external APIs, advanced skills, and renderer capabilities should not be forgotten or bolted on as unrelated tools. They should plug into Ariadne's core product concepts: Opportunity, Evidence Item, Living Briefing Packet, Capture Action Plan, Capability Module, Artifact Renderer, and Knowledge Layer. DOCX, XLSX, and huashu-design are now MVP renderer requirements rather than distant someday features.

Use `docs/architecture/future-integration-strategy.md` as the working architecture note for these future integrations.

- **Hermes Agent** observes opportunities, evidence, action plans, capability runs, and exploratory sessions through a narrow agent runtime interface. It can recommend actions and create Improvement Proposals, but durable changes remain review- or approval-gated.
- **Knowledge Graph View** visualizes Ariadne's primary structured knowledge as a projection of evidence, opportunities, workstreams, packet sections, actions, artifacts, reusable insights, and capability runs.
- **MinerU** enters as a generic or multimodal Document Intake extraction adapter that can produce Extraction Bundles from Generic Source Material or Visual Source Material; it does not own Ariadne knowledge.
- **RAGAnything** may enter as a future document/RAG pipeline adapter after the Extraction Bundle boundary is proven.
- **Project Theseus** may enter as a Solicitation Parser Capability for RFIs, Sources Soughts, draft RFPs, final RFPs, amendments, and solicitation attachments; Ariadne should integrate through a narrow adapter instead of copying Theseus wholesale or rebuilding its parser casually.
- **huashu-design** enters through the Artifact Renderer as a rendering capability module, including Interactive Capability Sessions when human design input is required.
- **RAG and retrieval** sit behind a Knowledge Layer adapter. The product asks for sourced retrieval; the adapter can later choose LightRAG, RAGAnything, another engine, or a custom stack without changing the product model.
- **External APIs and research tools** run as Capability Modules or CLI-first harnesses that produce traceable Source Evidence or Capability Run Outputs.
- **Advanced skills** remain under product workflows and Capability Studio, with provenance, iteration, review, and promotion before outputs become trusted knowledge or final artifacts.

Before implementing any future integration slice for Hermes, graph visualization, MinerU, huashu-design, RAG/retrieval, external APIs, advanced skills, artifact rendering, or third-party capability installation, run a `grill-with-docs` session for that slice. The session must review the original North Star details, current `PRD.md`, `CONTEXT.md`, ADRs, and `docs/architecture/future-integration-strategy.md`; resolve terminology and product boundaries; update `CONTEXT.md` inline for domain-language changes; and add or update ADRs only when the decision is hard to reverse, surprising without context, and trade-off driven.

Each future slice should leave a short documentation trail before code: what is being built now, what is intentionally deferred, which Ariadne concepts it plugs into, which capability modules or adapters are involved, and what evidence/provenance/review rules apply.

---

## 7. MVP Roadmap: Assisted Capture Platform

This roadmap supersedes the old broad phase list. Historical implementation trail lives in the Current State Snapshot and `docs/architecture/`; future work should be selected against the MVP spine below, not against whichever foundation was built most recently.

The end-state remains the same: one Capture Command Center that turns an Opportunity into actionable capture intelligence, managed work, engagement preparation, and useful artifacts. The correction is that every near-term epic must now connect the operating loop rather than adding another isolated middle layer.

### 7.1 MVP Outcome

Ariadne reaches MVP when one capture professional can manage a portfolio of real past, present, and future Opportunities, open one Opportunity for a focused working session, and leave with materially better capture work done.

The MVP must let the user:

- assemble opportunity context from Quick Capture, Document Intake, Source Profiles, Capture Research, accepted Evidence, Action Plan items, packet fields, capability outputs, and user prompts.
- accumulate that context into the **Living Milestone Decision Briefing Packet** as the primary working artifact and roadmap for Milestone 1-4 gate readiness and capture judgment.
- check a global Opportunity pulse across lifecycle state, pursuit status, archive/outcome state, source freshness, packet readiness, gate urgency, and next-action urgency, then open an Opportunity that needs attention without turning the home surface into a detailed action workspace.
- run or queue a bounded Opportunity Activation Run once an Opportunity is identified, so Ariadne can research permitted sources, gather as many packet-field answers or candidates as possible, identify recommendations, match skills/capabilities, and expose remaining gaps without waiting for the user to manually visit every tool.
- create a Standard Opportunity Scaffold from a user-identified opportunity name and entry context, including core capture workstreams, Living Packet sections, packet-field action slots, and activation status.
- treat every required Living Packet data element or Packet Field Definition as an actionable slot for the current milestone gate: show status, source support, gaps, answer paths, recommended routes, and at least one AI/capability/user action to answer or advance it.
- see the most important gaps, risks, source limitations, recommended actions, and relevant capability routes for the opportunity.
- run or request AI/LLM assistance, installed skills, short skill chains, source collection, federal-data tools, document-intake actions, renderers, and capture/marketing capabilities from inside product workflows through Capability Modules.
- review outputs with provenance, evidence strength, assumptions, model/capability trace, and source limitations visible.
- route reviewed outputs into Evidence, Packet Field Answers, Capture Action Plan items, Risk Register candidates, Call Plan or engagement prep, Capture Research follow-up, Artifact Draft blocks, and reviewable packet content opportunities.
- browse and reuse the Ariadne Knowledge Vault: accepted evidence, source material, packet answers, source profiles, capability outputs, lessons, reusable insights, and mirror projections with clear authority and opportunity scope.
- improve the Living Milestone Decision Briefing Packet, a practical call/engagement prep surface, updated capture actions, reviewable artifact-content recommendations, and reviewed DOCX, XLSX, and huashu-design artifact output paths.
- keep autonomous assistance clean and efficient: background work should resolve into compact coverage summaries, grouped review queues, source limitations, and next-best actions rather than tool clutter, interruptive prompts, or long status walls.

The MVP is not complete because another store, schema, panel, or adapter exists. It is complete when the Command Center can perform the assisted capture loop on a real opportunity with reviewable outputs that help the user's capture job.

### 7.2 MVP Operating Spine

All near-term implementation should strengthen this spine:

1. **Opportunity context**: the user selects, creates, or imports an Opportunity; Ariadne gathers existing trusted and reviewable context through Opportunity Knowledge Context.
2. **Opportunity activation**: Ariadne runs or queues a bounded activation sweep that checks required packet fields, source profiles, accepted evidence, documents, capture research options, federal-data capabilities, installed skills, and source limitations.
3. **Portfolio awareness**: Ariadne shows the global pulse across active, future, past, archived, won, lost, and watchlist Opportunities, including packet readiness, gate urgency, source freshness, blockers, and next-action urgency, while preserving opportunity-specific answer scope.
4. **Packet field action matrix**: every required packet data element for the current milestone gate has status, answer paths, source refs, gaps, and a recommended action route such as run research, inspect document spans, use a federal-data MCP, synthesize evidence, ask the user, prepare a customer call plan with suggested questions, run competitor or teaming research, engage a company small-business liaison or APEX Accelerator, or stage an artifact/visual recommendation.
5. **Capture need selection**: Ariadne identifies the next useful capture needs: packet gaps, research needs, customer-engagement needs, document/parser needs, source limitations, evidence gaps, risk signals, action-plan gaps, artifact-content opportunities, or artifact-readiness blockers.
6. **Assistance recommendation**: Ariadne recommends a Product Workflow, Capability Module, model workflow, installed skill, short skill chain, source-provider run, document-intake action, or user action for each need.
7. **Approved execution**: the user approves or starts the chosen assistance; low-risk local/admin tasks can use existing autonomy rules, while external calls, broad research, rendering, and customer-facing outputs require approval.
8. **Capability output capture**: results land as Capability Run Outputs, Source Findings, Capture Intelligence Draft Parts, Next Action Recommendations, Artifact Content Blocks, or workflow-specific candidates with provenance.
9. **Autonomy digest**: Ariadne summarizes background work as coverage gained, answers/candidates ready for review, blocked fields, source limitations, recommended skills/chains, approvals needed, and next-best actions.
10. **Workflow routing**: the user accepts, edits, discards, routes, or marks outputs as needing evidence; accepted or routed outputs improve the appropriate product workflow.
11. **Work product improvement**: the Living Milestone Decision Briefing Packet is the main accumulating roadmap artifact for the next Milestone 1-4 gate decision, while the Capture Action Plan, call/engagement prep, Evidence Store, Risk Register, Capture Research run, and Artifact Draft visibly improve around it.
12. **Knowledge vault capture**: accepted knowledge, reusable insights, lessons, source refs, and reviewed capability outputs become discoverable in the Ariadne Knowledge Vault without confusing mirrors or projections for source-of-truth records.
13. **Learning hooks**: repeated routes, accepted outputs, discarded suggestions, and friction become future Operational Learning inputs, but broad Hermes autonomy waits until the loop is reliable.

### 7.3 Core Component Map

- **Capture Command Center** is the operating surface for the MVP loop; it should show context, recommended routes, running/finished assistance, review needs, and improved work products together.
- **Opportunity Portfolio** is the management layer for multiple past, present, and future Opportunities. It must support create/import, watchlist, active pursuit, hold, archive, won/lost outcome, lifecycle state, next-action urgency, and cross-opportunity learning without treating another opportunity's packet answer as valid for the selected one.
- **Opportunity Activation Run** is the bounded autonomous sweep Ariadne performs after opportunity identification or on user request. It gathers permitted context, evaluates packet-field coverage, runs low-risk/local or pre-approved capabilities, identifies likely skills/chains/MCP routes, records source limitations, and queues reviewable candidates or approval requests.
- **Opportunity Knowledge Context** is the context spine; it gathers accepted and reviewable Ariadne records for one opportunity before AI, skills, artifacts, or routes act.
- **Autonomy Digest** is the clean UX pattern for autonomous work: compact coverage deltas, grouped review items, blockers, approvals, and next-best actions, with detailed tool/provenance traces available in drawers instead of dominating the workspace.
- **Ariadne Knowledge Vault** is the local-first authoritative knowledge workspace made from Ariadne source-of-truth stores and explicit projections: Evidence Store, Document Intake, Source Profiles, Packet Field Answers, Action Plan items, Capability Runs, Workflow Routing outputs, Artifact Drafts, reusable insights, Reference Wiki context, and optional Knowledge Mirrors. It is not just Obsidian and not just RAG; it is the user's browsable, searchable, source-scoped capture memory.
- **Packet Field Action Matrix** maps every required Living Packet data element for the current milestone gate to answer paths, current answer state, source support, AI/model options, skill-chain options, MCP/tool options, research routes, call/engagement routes, teaming or supplier-diversity routes, artifact-content routes, and manual/user actions. A field with no answer must still have a recommendation for how to get the answer.
- **Evidence Store, Document Intake, PIID Profiles, SAM.gov Profiles, Capture Research, Quick Capture, and Reference Wiki** are data and research inputs; they should feed the loop instead of remaining separate destinations.
- **AI Usage Layer** should route work to the correct Model Role: local/admin models for low-risk tagging, summarization, extraction, formatting, and draft prep; frontier reasoning models for strategy, synthesis, customer engagement, tradeoffs, and executive-ready recommendations.
- **Capability Module Integration** connects installed skills, marketing skills, federal-data capabilities, CLI harnesses, MCP tools, source providers, model workflows, parsers, and renderers to Product Workflows so AI/LLM assistance can take approved action without bypassing review.
- **Skill chaining** should start as explicit, inspectable, short chains with named stages, approved inputs, output contracts, and review destinations. It should not begin as an opaque autonomous planner.
- **Capability Run Store and Capability Reasoning View** record what ran, why it ran, what it used, what it produced, and how the user reviewed it.
- **Workflow Routing** is the product glue that sends outputs into Evidence, Packet, Action Plan, Risk Register, Call Plan, Capture Research, Document Intake, Artifact Assembly, or follow-up work.
- **Living Milestone Decision Briefing Packet** is the primary accumulating artifact and opportunity roadmap for MVP; it should continuously gather reviewed answers, assumptions, gaps, risks, recommendations, source support, visual/content opportunities, and readiness signals from the assisted capture loop so the user can make the appropriate Milestone 1, 2, 3, or 4 decision.
- **Call Plan or Engagement Prep, Capture Action Plan, Risk Register, and Artifact Drafts** are the other first work products the loop must improve around the packet.
- **Artifact Renderer** should enter as a consumer of reviewed Artifact Drafts and call/packet content, not as a source of truth or a freeform document generator. DOCX, XLSX, and huashu-design output paths are MVP-critical renderer capabilities.
- **Production Command Center UI/UX** is required before the product is considered usable beyond internal validation; the current FastAPI shell remains a scaffold for proving behavior. The product requirements live in Section 6, with `docs/architecture/production-command-center-ui-plan.md` as the supporting planning note.
- **Hermes, graph/RAG engines, Knowledge Graph View, full solicitation parsers, and broad third-party installation** are post-spine accelerators unless a narrow slice directly unlocks the MVP loop.

### 7.4 MVP Build Sequence

**MVP-1A: Production Command Center Route Tracer** ← **CURRENT REVIEW BRANCH**

Goal: connect the existing foundations into one route-first operating loop.

Deliverables:

- Add a Command Center entry point such as “Start assisted capture” for one Opportunity.
- Start the production-shaped Next.js Command Center shell in parallel with the route-first loop: Opportunity workspace, Living MS Briefing Packet center panel, main-dashboard pulse checks, embedded route/review surfaces, active-run drawer, and source/provenance drawer.
- Implement one working route action inside that Next.js shell: selected goal -> route recommendation -> run/review -> route accepted output into packet/action or call-plan destination. Deterministic/demo data is acceptable only as a temporary backend stand-in.
- Stop adding new primary user workflow screens to the FastAPI scaffold except as fallback/debug surfaces.
- Use Opportunity Knowledge Context plus the user's selected goal to identify capture needs and route options.
- Match needs to existing Product Workflows and Capability Modules, including Capture Research, Capability Runs, Quick Capture, Document Intake, packet gaps, action-plan work, artifact assembly, and call/engagement preparation.
- Persist route decisions and review state in the narrowest suitable existing store, or add a small Workflow Routing store only if existing stores cannot own the state cleanly.
- Let users run, route, accept, discard, or defer recommendations without leaving the Command Center.
- Preserve provenance from source context, recommendation, model/capability run, review decision, and routed destination.

Acceptance demo:

- One Opportunity shows trusted context, reviewable context, gaps, limitations, and route recommendations.
- The production-shaped Command Center shell can display and execute at least one working assisted route, even if some supporting actions still use deterministic/demo data.
- The user starts one assisted route, receives a reviewable output, and routes it into at least two real work products, such as a Packet Field Answer and an Action Plan Item or Call Plan candidate.
- The loop does not create trusted downstream records, external calls, or final artifacts without explicit review/approval.

**MVP-1B: Opportunity Activation + Packet Field Action Matrix + Opportunity Portfolio Foundation** ← **NEXT AFTER REVIEW**

Goal: once an Opportunity is identified, make Ariadne automatically inventory the work, gather what it safely can, identify the right skills/routes, and make the Living Packet operational at the data-element level across a usable Opportunity Portfolio.

Deliverables:

- Add an Opportunity Portfolio surface and API for active, future, past, held, archived, won, and lost Opportunities, with lifecycle state, next-action urgency, source freshness, packet readiness, and review counts.
- Add create/import/update/archive behavior for Opportunities with local-first persistence and deterministic tests, beginning with a low-friction Create Opportunity command that requires only the user-identified Opportunity name before Ariadne produces a Standard Opportunity Scaffold.
- Add an Opportunity Activation Run that can start from opportunity creation/import or a user action, then evaluate required packet fields, known source profiles, accepted evidence, documents, capture research options, federal-data capabilities, local skills, source limitations, and approval requirements.
- Allow the activation run to perform low-risk/local or pre-approved gathering automatically, while queuing external calls, paid/credit-spending providers, broad research, and sensitive/customer-facing work for explicit approval.
- Present activation results as an Autonomy Digest: coverage gained, field candidates ready for review, blocked fields, recommended skills/chains, MCP/source-provider routes, approvals needed, and next-best actions.
- Render the Living Packet as packet sections plus required Packet Field Definitions, not only aggregate section counts.
- For every required Packet Field Definition, show current answer status, answer path options, source support, assumptions, confidence, gaps, and an action menu.
- Build a Packet Field Action Matrix that can recommend at least one route for every unanswered, partial, stale, or assumption-based field.
- Support route types such as use accepted evidence, inspect document spans, run Capture Research, run federal-data MCP/source profile lookup, ask the user, synthesize with the selected model role, run a skill or short skill chain, create an Action Plan task, or prepare a customer call plan with suggested questions.
- Route accepted field outputs into Packet Field Answers with provenance and, when the answer cannot be produced yet, into a concrete recommendation such as "call customer" with a generated call-plan question set.

Acceptance demo:

- The user can switch among at least three Opportunities representing active, future/watchlist, and past/archive states.
- Creating or selecting an Opportunity can launch or resume an activation run that inventories fields, sources, capabilities, recommended skills, and remaining gaps without forcing the user through separate tool screens.
- The selected Opportunity shows required packet data elements with field-level answer status and action routes.
- At least three different field routes work end to end: one evidence/source-backed answer, one research or MCP-backed answer candidate, and one customer-call-plan recommendation for a field that cannot be safely answered from available data.
- The activation digest is compact enough for the user to understand coverage, review needs, blockers, and next-best actions without reading raw tool logs.
- Packet field updates remain opportunity-scoped, review-gated, and traceable to source refs, capability runs, user decisions, or call-plan recommendations.

**MVP-1C: Ariadne Knowledge Vault Foundation**

Goal: make Ariadne's accumulated capture memory visible and usable without making a knowledge mirror or RAG engine the source of truth.

Deliverables:

- Add a Knowledge Vault index/view that lists accepted evidence, source material, packet answers, source profiles, action items, capability outputs, workflow-route outputs, artifact drafts, reusable insights, and Knowledge Mirror projections by opportunity, entity, source type, trust state, and freshness.
- Distinguish Ariadne source-of-truth records from Reference Wiki context, Knowledge Mirror projections, and future RAG/graph indexes.
- Allow selected vault records to feed packet-field actions, capture research briefs, call-plan prep, action recommendations, and artifact drafts.
- Add reusable insight promotion as a review-gated path from one Opportunity's accepted knowledge into future-opportunity context.

Acceptance demo:

- The user can browse the vault, filter by Opportunity and trust state, inspect provenance, and use a vault record as input to a packet-field route or call-plan route.
- A reusable insight can be proposed from one Opportunity and used as context, not copied as a valid answer, for another Opportunity.

**MVP-2: AI Usage Layer + Skills Integration**

Goal: make AI/LLM assistance and installed skills take as much approved capture action as possible rather than remaining decorative inventory.

Deliverables:

- Add explicit model-use contracts for capture need analysis, packet synthesis support, call/engagement prep, value proposition/messaging, research brief creation, output review summaries, and artifact-block drafting.
- Use fake model runners in automated tests and real configured providers only in user-approved local runs.
- Expose local workspace skills and vendored marketing skills as Capability Modules with typed input expectations, output summaries, review destinations, and route metadata.
- Expose MCP tools and federal-data capabilities as Capability Modules with clear source family, env readiness, approval requirement, output schema, and packet-field/product-workflow fit.
- Connect each relevant Packet Field Definition to at least one model role, skill, skill chain, MCP/source-profile tool, or user-action fallback.
- Let AI/LLM assistance prepare inputs, recommend Capability Modules, run approved low-risk capability routes, summarize outputs, propose next routes, and draft reviewed work-product updates.
- Let Opportunity Activation Runs identify and invoke approved model roles, skills, skill chains, source providers, and MCP tools from the Packet Field Action Matrix rather than waiting for manual tool selection.
- Support short skill chains such as research brief -> customer insight -> call-plan prep, requirements fit -> packet implication -> action recommendation, or value proposition -> engagement messaging -> artifact block.
- Keep chain stages visible, bounded, interruptible, and review-gated.

Acceptance demo:

- A user can choose a capture goal and see which AI/model role, skill, or skill chain Ariadne recommends.
- At least one installed skill or skill-backed capability can run through the Capability Run Store and route a reviewable output into packet/call/action/artifact work.
- At least one MCP-backed/federal-data capability can produce a reviewable packet-field or source-profile candidate, with source limitations visible.
- The same workflow works without a live model by using deterministic or fake runners in tests.

**MVP-3: Capture Work Product Loop**

Goal: prove that routed AI/skill/research outputs improve the capture work the user cares about.

Deliverables:

- Update the Living Milestone Decision Briefing Packet as the main accumulating artifact from reviewed routed outputs, including packet answers, assumptions, gaps, risks, recommendations, source support, and readiness signals.
- Build the first practical Call Plan or engagement-prep loop from Opportunity Knowledge Context, customer/research findings, marketing/value-proposition skills, and action commitments.
- Connect routed outputs to the Capture Action Plan as outcome-level tasks with evidence and rationale.
- Route risk/discriminator/teaming/price/workload findings into Risk Register or follow-up candidates where appropriate.
- Reassemble Artifact Drafts from improved context so the user can see the packet or engagement work product improve after routing.

Acceptance demo:

- Starting from one opportunity, Ariadne improves a Milestone Decision Briefing Packet working draft, creates or updates action-plan items, and prepares a call/engagement artifact candidate from reviewed AI/skill/research output.
- The user can inspect source refs, model/capability provenance, assumptions, gaps, and review decisions for each improvement.

**MVP-4: Production Command Center UI/UX Hardening**

Goal: harden the production-shaped Command Center into a genuinely usable product surface instead of continuing to rely on the FastAPI scaffold.

Deliverables:

- Build the production Command Center experience around the MVP loop: opportunity context, assisted routes, running/finished capability work, review decisions, packet readiness, action plan, call/engagement prep, and artifact status in one coherent workspace.
- Treat the Living Milestone Decision Briefing Packet as the central accumulation surface, with compact readiness, evidence, assumptions, gaps, risks, recommendations, and source trace visible without overwhelming the user.
- Provide production-quality interaction flows for starting assisted capture, approving/running capability routes, reviewing outputs, routing results, and seeing work products update.
- Keep advanced Capability Studio, raw toolchain details, and verbose provenance secondary to the user's active capture work.
- Use the project-standard production UI stack when this slice begins; the existing shell remains available only as a runtime scaffold and fallback demo surface.

Acceptance demo:

- A user can complete the MVP assisted capture loop in the production Command Center UI without needing the internal scaffold pages.
- The UI makes the Living Milestone Decision Briefing Packet, next actions, call/engagement prep, review queue, and artifact readiness feel like one connected workspace.
- The first production UI shape receives explicit user review before the slice is considered complete.

**MVP-5: Practical Artifact Rendering And Export**

Goal: provide usable DOCX, XLSX, and huashu-design output paths without letting rendering drive the product model.

Deliverables:

- Add renderer adapters that consume reviewed Artifact Draft content and produce practical local DOCX and XLSX exports.
- Add a first huashu-design renderer path for reviewed packet or engagement content that needs visual or PPTX-capable artifact support.
- Use Markdown or HTML only as internal preview/debug support, not as the MVP substitute for DOCX, XLSX, or huashu-design output.
- Support Milestone Decision Briefing Packet and call/engagement prep content before broad template or presentation work.
- Preserve source appendix, assumptions, gaps, and provenance in the rendered output.
- Keep private Artifact Export Profiles local/ignored and out of the public repo.

Acceptance demo:

- An export-ready reviewed draft can produce usable local DOCX and XLSX files without inventing new claims, bypassing review, or writing back to trusted stores.
- A reviewed packet or engagement artifact can produce a first huashu-design visual/PPTX-capable output from reviewed content.
- Renderer outputs are traceable to reviewed Artifact Content Blocks and source refs.

**MVP-6: Document And Solicitation Intake Integration Into The Loop**

Goal: make document intake a living source of capture work rather than a side queue.

Deliverables:

- Surface document-derived needs and parser-required items inside Assisted Capture routes.
- Let a document source span or extraction warning trigger research, evidence review, packet updates, call-plan questions, or action-plan items.
- Choose a first solicitation-parser adapter only when it directly improves the MVP loop for RFIs, Sources Soughts, RFPs, amendments, or requirements attachments.
- Keep MinerU, RAGAnything, LightRAG, OCR, multimodal extraction, and Theseus behind the Extraction Bundle contract.

Acceptance demo:

- A document-derived signal can move from Document Intake through assisted routing into packet/call/action/evidence work with traceability.

**MVP-7: Post-MVP Acceleration**

Goal: add power after the route-first loop is useful.

Candidates:

- Hermes runtime for observing the loop, proposing improvements, and eventually coordinating low-risk repeated work.
- Knowledge Graph View and semantic/RAG retrieval for richer sensemaking after structured context and routes are reliable.
- Continued Next.js/production UI refinement after the first production Command Center slice proves the workflow shape.
- Advanced huashu-design/PPTX polish, richer private template profiles, and renderer polish after DOCX, XLSX, and first huashu-design MVP paths are reliable.
- Third-party skill installation and broader catalog management after local skills and explicit chains prove useful.
- Additional federal-data product workflows such as BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, and Regulations.gov when they feed named capture routes.

### 7.5 MVP Definition Of Done

MVP is done when the acceptance demo can show all of the following in one local Command Center run:

- create or open one Opportunity.
- manage a portfolio of multiple Opportunities across active, future/watchlist, and past/archive states.
- gather context from at least three real input families, such as accepted evidence, source profiles, capture research, document intake, quick capture, packet fields, action items, or capability outputs.
- show every required Living Packet data element as a field-level action surface with answer paths, status, provenance, and a recommendation when the answer is missing.
- browse the Ariadne Knowledge Vault and use a vault record as context for a packet, call-plan, research, or action route.
- generate route-first capture recommendations tied to packet, call/engagement, action, evidence, research, risk, or artifact needs.
- run at least one AI/model-assisted step and at least one skill/capability-backed step with provenance.
- run or recommend at least one MCP/source-profile backed step and one skill-chain backed step with reviewable outputs.
- show an Autonomy Digest for an Opportunity Activation Run with coverage deltas, review queue, recommended skills/chains, approvals needed, source limitations, and next-best actions.
- review the outputs and route them into at least three work products, including the Milestone Decision Briefing Packet, Capture Action Plan, and call/engagement preparation.
- produce a reviewed Artifact Draft plus traceable DOCX, XLSX, and first huashu-design outputs from reviewed content.
- complete the assisted capture loop through the production Command Center UI, not only the internal FastAPI scaffold.
- show source support, assumptions, gaps, source limitations, model/capability provenance, route decisions, and created/updated work-product links.
- pass automated tests with fake model/capability runners and no required live credentials.

### 7.6 Build Gates From Here Forward

- Every new epic must state which step of the MVP Operating Spine it advances.
- Every new epic must improve at least one capture work product, not only create a new schema, store, adapter, or panel.
- Every required Packet Field Definition must have at least one answer path and at least one actionable fallback route before MVP is considered complete.
- Every multi-opportunity feature must preserve opportunity-specific answer scope while allowing reusable insight and source-context reuse across Opportunities.
- Every new integration must identify the Product Workflow it serves and the review/routing destination for its outputs.
- Every new AI or skill-chain feature must preserve model/capability provenance and must work in tests without live credentials.
- Every autonomous or background feature must resolve into an Autonomy Digest, review queue, or concrete work-product update; do not ship autonomous behavior as raw logs, scattered cards, or a separate tool maze.
- Every Opportunity Activation Run must respect approved autonomy policy: local/low-risk work may run automatically, but external calls, broad research, paid/credit-spending providers, customer-facing outputs, sensitive actions, and trusted downstream writes remain approval-gated.
- Every artifact-rendering slice must consume reviewed Artifact Draft content and must not become the source of truth.
- Every external call, broad research run, paid/credit-spending provider, final export, customer-facing output, sensitive label change, deletion, or gate decision remains approval-gated.
- A future `grill-with-docs` session should ask first, “How does this make the assisted capture loop more useful?” before adding new foundations.

---

## 8. Repository Setup Instructions (ariadne-thread)

**Public GitHub Repository Name:** `ariadne-thread`

**Initial Structure (created automatically)**

```
ariadne-thread/
├── PRD.md
├── README.md
├── pyproject.toml
├── .python-version
├── .gitignore
├── .env.example
├── .github/
│   ├── copilot-instructions.md
│   └── skills/
│       ├── mattpocock skills...
│       ├── ui-ux-pro-max/
│       ├── cli-anything/
│       ├── cli-hub-meta-skill/  # optional discovery aid
│       ├── first-principles-thinking/
│       └── skill-creator/
├── src/
├── docs/
│   ├── adr/
│   ├── agents/
│   ├── architecture/
│   └── reference/
│       └── shipley/
└── ui/
```

**Bootstrap Command for Copilot (use this exact prompt)**

> “Create a new public GitHub repository named `ariadne-thread`. Initialize it with this exact PRD.md as the root file. Immediately execute **Section 2 Developer Skills Bootstrap** in full — install or vendor all required developer skills, including Matt Pocock skills, first-principles thinking, skill-creator, `ui-ux-pro-max`, and CLI-Anything builder skill. Treat CLI-Hub meta-skill as optional catalog discovery only. Run `improve-codebase-architecture` on the new repo and commit the results before writing any application code. Follow the North Star Vision and deep modular principles at every step. Set up the exact folder structure shown in the PRD.”

---

## 9. How to Use This Document

This PRD is the single source of truth for the Ariadne Thread project.

In any future conversation or task:

- Reference these principles first.
- Ensure all proposals, features, and refactors align with the North Star, Developer Skills Bootstrap, and deep modular philosophy.
- Keep discussions at the appropriate level of abstraction.

When in doubt, ask:  
“Does this make the Command Center more powerful, simpler, and more aligned with Shipley + deep modular principles while keeping the user inside the UI as much as possible?”

---

**End of PRD v1.33**

**The next build direction after production UI review is MVP-1B: Opportunity Activation + Packet Field Action Matrix + Opportunity Portfolio Foundation, followed by Ariadne Knowledge Vault Foundation and real AI/skills/MCP execution behind those field-level routes.**

---

_This document contains no company-identifying information and is suitable for public repository use._
