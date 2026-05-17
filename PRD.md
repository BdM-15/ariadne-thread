# Ariadne Thread

**Product Requirements Document (PRD) v1.11**

**North Star: One elegant, powerful Capture Command Center that allows a single capture professional to manage the entire capture lifecycle — from opportunity identification through award — with maximum effectiveness and minimum friction.**

**Repo Name:** ariadne-thread  
**Date:** May 17, 2026
**Status:** SAM.gov Enrichment Profile implementation started on `05-build/sam-gov-enrichment-profile`

---

## 0. Current State Snapshot (May 17, 2026)

**Completed**

- Developer skills are installed or vendored under `.github/skills/`, including Matt Pocock's full pack, first-principles thinking, skill-creator, ui-ux-pro-max, and CLI-Anything builder skill. CLI-Hub meta-skill is present only as an optional discovery aid.
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
- SAM.gov Enrichment Profile implementation now includes the Entity Record lane, Opportunity Discovery lane, Known Opportunity Record lane, and Attachment Intake lane on the SAM.gov epic branch, with live/fake source-mode boundaries, local profile persistence, API routes, Command Center read surfaces, source limitations, explicit attachment-download approval, Document Intake provenance, and review-gated downstream candidates.
- Current automated validation: `uv run ruff check src tests` and `uv run pytest -q` pass on the SAM.gov Attachment Intake branch, with 189 tests passing.

**Still Deferred**

- Hermes runtime, durable knowledge/retrieval engine, graph visualization, full MinerU integration, RAGAnything integration, LightRAG integration, Theseus solicitation parser integration, OCR/multimodal extraction, huashu-design/artifact rendering, external API integrations beyond the selected SAM.gov enrichment slice, advanced skill installation, persistent storage beyond local/demo or narrow workflow adapters, and full Next.js UI are not implemented yet.
- Document Intake UI polish is still deferred beyond the accepted first shape; the existing FastAPI HTML surfaces are review/runtime scaffolds and demo threads, not the final frontend architecture.

**Next Build Gate**

- Implement the **SAM.gov Enrichment Profile** on epic branch `05-build/sam-gov-enrichment-profile`.
- Use `PRD.md`, `CONTEXT.md`, ADR 0006, ADR 0007, `docs/architecture/federal-data-mcp-foundation-plan.md`, `docs/architecture/future-integration-strategy.md`, and `docs/architecture/sam-gov-enrichment-plan.md` as implementation inputs.
- Preserve the Federal Data Capability boundary: SAM.gov search, entity, and opportunity data should flow through the upstream `sam-gov-mcp` capability rather than a duplicate Ariadne MCP.
- Preserve the Document Intake boundary: downloaded SAM.gov attachments enter Document Intake, then material classification determines generic extraction versus future Solicitation Parser Capability routing.
- Keep Firecrawl/web enrichment, BLS/GSA pricing, subaward/competitor/customer profile workflows, Theseus solicitation parsing, artifact rendering, Hermes runtime, skill chaining/LangGraph, and Next.js migration deferred until selected through their own documented slices.
- Keep the SAM.gov epic vertical and review-gated across entity records, known opportunity records, opportunity discovery, attachment intake, review candidates, and Command Center behavior.

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
| huashu-design                                 | Visual artifact renderer (platform skill)                                                                                                                  | Internal (guided by ui-ux-pro-max)                      |
| Custom Renderer Skill                         | DOCX + XLSX generation for capture artifacts                                                                                                               | Internal (guided by ui-ux-pro-max)                      |
| Custom HITL Chat Interface                    | Back-and-forth interaction for skills requiring human decision input                                                                                       | Internal (guided by ui-ux-pro-max)                      |
| Obsidian Integration                          | Living PKM and capture plans                                                                                                                               | https://github.com/kepano/obsidian-skills               |
| 1102tools/federal-contracting-mcps            | Hardened public federal data MCPs for USAspending, SAM.gov, BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, and Regulations.gov                       | https://github.com/1102tools/federal-contracting-mcps   |
| 1102tools/federal-contracting-skills          | Government contracting deliverables (IGCE, SOW/PWS, market research)                                                                                       | https://github.com/1102tools/federal-contracting-skills |
| coreyhaines31/marketingskills                 | Value propositions, positioning, messaging, CRO                                                                                                            | https://github.com/coreyhaines31/marketingskills        |
| Firecrawl                                     | Primary research/scraping engine                                                                                                                           | https://github.com/mendableai/firecrawl                 |

---

## 4. Technical Architecture

- **Primary Language**: Python 3.14.5 / `>=3.14` as the default implementation baseline for backend services, agents, orchestration, document processing, knowledge workflows, and platform tools. Downgrade only through an ADR if a required dependency blocks 3.14.
- **Python Tooling**: Use `uv` for dependency, lockfile, and virtualenv management; use `uvx` for one-off Python CLIs. Keep a local `.venv/` ignored by git.
- **Frontend**: Next.js 15 + Tailwind + shadcn/ui + custom cyberpunk components (guided by ui-ux-pro-max). Use TypeScript only for the frontend and frontend-adjacent tooling.
- **Backend**: Python-first, deep modular structure (enforced by Matt Pocock skills)
- **Initial Python Package Shape**: Start with one `src/ariadne/` package and deep internal modules for the first slice rather than many small top-level packages. Initial module homes should include configuration, opportunities, evidence, packets, action plans, and capability catalog concerns.
- **CLI-First Harnesses**: Use Python Click-style CLIs with `--json` output for repeatable, batchable, tool-facing, or agent-facing operations. These CLIs should sit behind the UI or agent runtime rather than replacing human-facing strategy workflows.
- **Federal Data MCP Foundation**: Integrate upstream `1102tools/federal-contracting-mcps` through manifest-only Federal Data Capability declarations. Ariadne should pin upstream packages, record provenance and env-var names, smoke-test MCP initialize behavior, and deeply integrate one source at a time through product workflows rather than building unique federal data MCP servers.
- **Evidence Store**: Store traceable Evidence Items local-first behind a Pydantic-validated interface. Start with structured local files as the first adapter, while keeping callers isolated from whether persistence later becomes SQLite, Postgres, or another storage engine.
- **Document Intake Command Surface**: Turn uploaded source material into extraction provenance, Capture Intelligence Draft Parts, recommendations, skill-chain options, accepted Evidence Items, review-gated downstream candidates, Knowledge Note Projections, and Command Center actions. Build functionality first through domain models, a narrow Document Intake Store, and Extraction Bundle behavior before rendering UI.
- **Extraction Boundary**: Use Extraction Bundles as the shared parser output contract for generic source material, visual source material, and solicitation-family documents. Parser, OCR, multimodal, retrieval, MinerU, RAGAnything, LightRAG, and Theseus-style tools must act as adapters that produce reviewable output; Ariadne keeps trusted entities, relationships, provenance, and review gates in the domain model.
- **Agents**: Hermes Agent (persistent memory) + Grok 4.3 for complex work + local models for speed
- **Knowledge Layer**: Opportunity-centric retrieval and graph context with a custom Command Center UI. LightRAG is a candidate component, but exact integration details should be decided during architecture work.
- **Artifact Generation**: Custom renderer skill (DOCX, XLSX, presentations, visuals)
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

### Firecrawl

- Site: https://www.firecrawl.dev
- Free signup → Dashboard → API Key
- Add to `.env` as `FIRECRAWL_API_KEY`
- 500 credits/month free tier (ample for research)

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
- All major workflows remain inside the single interface

## 6.1 First Flagship Workflow: Milestone Decision Briefing Packet

The first flagship product workflow is the Milestone Decision Briefing Packet because it becomes the strategic foundation for the rest of Ariadne. It forces the platform to gather multi-source capture data, connect opportunity-specific knowledge to reusable insight, surface gaps across core capture workstreams, recommend next actions, manage dates and owners, and produce a professional decision-support artifact.

The workflow should use the generic structure in `docs/reference/generic-milestone-intelligence-checklist.md` as public, company-agnostic inspiration. The checklist must remain free of company-specific template names, internal review-body names, CRM assumptions, local file paths, or proprietary labels.

Initial packet output should be evidence-first. It should include evidence status, source quality, source traceability, assumptions, confidence, gaps, risks, win probability rationale, recommended gate action, dated next actions, and mentor-style explanations that teach the user why each item matters. Ariadne may recommend action before every answer is complete, but it must clearly show what is sourced, what is inferred, what remains unknown, and whether closing a gap requires a next action or a new platform capability. This evidence discipline should steer frontier-model reasoning toward auditable capture outcomes without constraining hypothesis generation, synthesis, or strategic judgment.

The packet should exist first as a Living Briefing Packet dashboard inside the Command Center, with slide-like packet sections, packet readiness labels, evidence/gap status, risks, actions, and mentor explanations visible before export. The dashboard should be useful even when the packet is not decision-ready: early versions become the work plan for closing gaps. Packet sections are the user-facing skin, while core capture workstreams and Evidence Items are the underlying readiness and evidence structure. The internal packet sections should form a company-agnostic Canonical Packet Section Model inspired by the user's real briefing needs, while the Milestone Intelligence Checklist supplies the questions and evidence prompts that populate those sections. The exact private deck/template format can be handled later through an Artifact Export Profile. When ready, the user can trigger the Artifact Renderer, including huashu-design where appropriate, to export the packet through a private Artifact Export Profile into a user- or organization-specific format. Private templates and organization-specific mappings must remain out of the public repo.

The Living Briefing Packet should support both a Briefing View and a Coverage View. The Briefing View is the primary working surface for strategic decisions, leadership-ready status, risks, recommendations, and next actions. The Coverage View is the supporting evidence matrix for checklist questions, source traceability, gaps, assumptions, and validation state. The user should manage outcomes, approvals, relationships, and strategy while Ariadne performs the under-the-hood research, synthesis, note organization, artifact drafting, and action-plan maintenance through guided capture workflows.

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

The completed Federal Data MCP Foundation + USAspending Recompete Intelligence Intake epic registers all eight upstream 1102tools federal data MCPs as manifest-only Federal Data Capabilities while deeply integrating USAspending first through a structured PIID Contract Intelligence Profile. The profile starts from one contract number and produces award baseline, burn posture, vehicle context, deterministic pivots, gaps, recommended enrichments, Hermes-observable events, and review-gated candidates. It remains structured source data for future artifacts; huashu-design, DOCX, XLSX, presentation exports, Firecrawl/web enrichment, 1102 deliverable skills, skill chaining, LangGraph, and Hermes runtime behavior remain later slices until selected through a fresh `grill-with-docs` session.

## 6.2 Selected Next Epic PRD: SAM.gov Enrichment Profile

### Problem Statement

Ariadne can now turn one PIID or contract number into a structured USAspending-backed recompete intelligence spine, but the capture professional still needs official acquisition-facing context from SAM.gov. Many real opportunities do not start with a clean solicitation ID. The user may only know a customer office, program name, legacy program name, vague description, NAICS/PSC signal, incumbent, or vendor ecosystem clue. Current and prior SAM.gov postings may also include documents that should enter Document Intake, but Ariadne does not yet discover, download, classify, or route those official attachments.

The problem is not simply “look up a solicitation.” The user needs a command-first SAM.gov workflow that can enrich a recompete or opportunity with entity records, known notices, discovery searches, official attachment intake, source limitations, and review-gated next actions without blurring official SAM.gov data with web research, fake tests, or trusted downstream knowledge.

### Solution

Build the **SAM.gov Enrichment Profile** as the next vertical product epic. The profile should combine four lanes in one reviewable command surface:

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
- Keep Firecrawl/web enrichment as a deferred Web Enrichment Support route, not part of the first SAM.gov implementation.
- Add provenance source mode values for live SAM.gov, fake adapter tests, and demo fixtures. Fake and demo output must not be eligible for normal trusted Evidence promotion.
- User-triggered product workflows should call live SAM.gov by default when the private key is configured. Page render should not trigger live calls.
- The Command Center should show saved SAM.gov profiles, live-readiness status, profile lanes, source limitations, review candidates, attachment download state, and Document Intake links.
- The first implementation should use epic branch `05-build/sam-gov-enrichment-profile`, with progression branches for domain/store, adapter, attachment intake, and command surface work.

### Testing Decisions

- Test external behavior: profile creation, source-mode provenance, candidate projection, review gating, persistence, attachment intake behavior, Document Intake routing, and API/Command Center responses.
- Do not write tests that only verify private helper structure or implementation details.
- Normal automated tests should use fake SAM.gov adapter responses so the suite is deterministic and does not require private secrets or live network access.
- Fake test fixtures should be broad rather than tiny: cover multiple entity matches, hierarchy clues, known opportunity matches, discovery searches, active and archived notices, pagination, attachments, inaccessible documents, no-result cases, auth failures, rate failures, and source limitations.
- Fake-adapter tests must assert that fixture output is labeled as fake or demo data and is not reported as proof of live SAM.gov success.
- Live SAM.gov behavior can have separate local validation, but normal CI/unit tests must not depend on live SAM.gov availability.
- Prior test patterns include PIID Contract Intelligence Profile tests for structured profile creation, Federal Data Capability tests for MCP registry and secret-safe behavior, Document Intake tests for queueing/classification/extraction boundaries, and runtime tests for FastAPI route behavior.

### Out of Scope

- Firecrawl or broad web enrichment.
- Direct non-SAM web crawling or guessing hidden attachment URLs.
- Solicitation parsing with Project Theseus or another parser.
- MinerU, RAGAnything, LightRAG, OCR, or multimodal extraction.
- Artifact Renderer, DOCX, XLSX, presentation, or huashu-design export.
- Hermes runtime, autonomous tool choice, operational learning, or workflow mutation.
- Skill chaining or LangGraph orchestration.
- Product workflows for BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, and Regulations.gov.
- Full Next.js UI migration.
- Automatic trusted downstream promotion from SAM.gov results or downloaded documents.

### Further Notes

This epic extends ADR 0007 and ADR 0006 rather than requiring a new ADR. ADR 0007 keeps federal data access behind upstream 1102tools Federal Data Capabilities. ADR 0006 keeps parser and retrieval outputs behind Document Intake's Extraction Bundle and review boundaries. The SAM.gov plan is recorded in `docs/architecture/sam-gov-enrichment-plan.md`.

## 6.3 Future Capability Integration Strategy

The first build slice is intentionally narrow, but it must create stable attachment points for the later systems named in the North Star. Hermes, graph visualization, MinerU, huashu-design, RAG, external APIs, and advanced skills should not be forgotten or bolted on as unrelated tools. They should plug into Ariadne's core product concepts: Opportunity, Evidence Item, Living Briefing Packet, Capture Action Plan, Capability Module, Artifact Renderer, and Knowledge Layer.

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

## 7. Phased Development Roadmap

**Phase 0 – Developer Skills + Architecture Foundation (Week 0–1)** ← **COMPLETE**

**Completed**

- Installed/vendored developer skills in `.github/skills/`, including Matt Pocock skills, first-principles thinking, skill-creator, ui-ux-pro-max, and CLI-Anything builder skill. CLI-Hub meta-skill is vendored only as an optional discovery aid.
- Established Python 3.14.5 / `>=3.14` with `uv` as the default development stack, including `pyproject.toml`, `.python-version`, `.venv/`, and `uv.lock`.
- Established secret-safe environment handling with descriptive `.env.example` and private ignored `.env` files.
- Ran architecture foundation review and recorded ADRs before application code.
- Established `CONTEXT.md`, `AGENTS.md`, `docs/agents/`, `docs/architecture/`, and `docs/adr/`.
- Organized Shipley global knowledge references under `docs/reference/shipley/`.

**First Slice Epic – Domain/Storage Foundation** ← **COMPLETE**

- Built the local runtime and first Command Center shell.
- Built Opportunity, Entry Context, Lifecycle State, Core Capture Workstream, and Backfill Need domain scaffolding.
- Built Quick Capture raw-item intake and review routing without trusted knowledge writes.
- Built Pydantic-validated Evidence Items and a local Evidence Store adapter.
- Built Living Briefing Packet readiness, Briefing View, Coverage View, deck-shaped review UI, and packet evidence/gap status.
- Built Capture Action Plan outcome tasks with lower-level execution details kept out of the primary view.
- Built read-only Capability Catalog discovery from local `.github/skills/` metadata.
- Built Packet Field Definitions, Packet Field Answers, Answer Paths, Shared Knowledge Entities, and Packet Field Review connections so briefing data elements become reusable strategic slots without reusing another Opportunity's answers as truth.
- Closed issues #1 through #8 and merged the completed epic to `main` after validation.

**Quick Capture Knowledge Processing Epic** ← **COMPLETE**

- Imported Project Ariadne public-source knowledge as commit-safe Capture Reference Context and added lightweight Reference Wiki influence retrieval.
- Built Capture Intelligence Drafts from rushed notes and uploaded source material, including inferred claims, risks, discriminator candidates, packet implications, action candidates, gaps, follow-up questions, assumptions, confidence notes, Reference Wiki influence provenance, and optional Local Admin Model assist.
- Kept Local Admin Model config centralized through `OLLAMA_HOST` and `LOCAL_DAILY_MODEL`; local admin assist has only workflow-specific enablement and timeout controls.
- Added per-piece draft review controls, recommended routes, skill-chain suggestions, discard handling, and documented future bulk selection.
- Added review-gated promotions from draft parts into Evidence Items, Action Plan Items, Packet Field Answers, and packet gap updates while preserving raw item ID, draft ID, draft part ID, review rationale, evidence links, and edit history.
- Changed trusted evidence behavior so accepted evidence saves polished Capture Intelligence Draft output, while truly raw notes remain trace/admin context only. Low-signal notes route to clarification instead of evidence.
- Routed pasted text and text/Markdown uploads through the same Quick Capture path; unsupported uploads become parser-required Document Intake Candidates.
- Added public Call Plan and Risk Register data dictionaries while keeping private templates/workbooks/log examples ignored.
- Added an end-to-end Command Center demo thread showing messy input, Reference Wiki influences, draft inferences, review controls, accepted evidence/action/packet outputs, discarded output, traceability, and parser-required future Document Intake.
- Closed issues #9 through #15 on the epic branch after validation.

**Document Intake Command Surface Epic** ← **COMPLETE**

- Built functionality foundation first: domain models, Document Intake Store, Extraction Bundle creation, review-ready Capture Intelligence Draft inputs, and Command Center demo behavior.
- Completed the tracer bullet: upload or register generic source material, classify it, persist intake state, create an Extraction Bundle, convert useful findings into Capture Intelligence Draft Parts, surface recommendations and skill-chain options, accept source spans into Evidence Items, create review-gated Action Plan/Packet/Risk Register/Call Plan/Knowledge Note Projection candidates, and show the workflow in the Command Center.
- Kept Ariadne's Capture Knowledge Foundation authoritative across capture and solicitation workflows. Parser, retrieval, OCR, multimodal, MinerU, RAGAnything, LightRAG, and Theseus-style tools remain adapters that produce reviewable Extraction Bundles.
- Classified source material as Generic Source Material, Visual Source Material, Solicitation Document, or Unsupported Document. Visual and solicitation-family material are recorded while OCR/multimodal and Solicitation Parser Capability work remains deferred.
- Persisted a narrow local Document Intake Store for intake records, Extraction Bundles, review decisions, accepted evidence links, and Knowledge Note Projections without redesigning the full storage architecture.
- Generated Knowledge Note Projections as one-way Markdown-style notes over accepted Ariadne knowledge; they support lightweight sensemaking and future retrieval without becoming source of truth.
- Deferred full MinerU, RAGAnything, LightRAG, Theseus, OCR, frontier multimodal extraction, Knowledge Graph storage, bidirectional Obsidian sync, complex skill-chain execution, and broad storage-platform work.

**Federal Data MCP Foundation + USAspending Recompete Intelligence Intake Epic** ← **COMPLETE**

- Registered all eight upstream `1102tools/federal-contracting-mcps` servers as manifest-only Federal Data Capabilities rather than creating unique Ariadne MCP servers or vendoring upstream MCP source.
- Recorded pinned upstream versions, command shapes, provenance, license metadata, env-var names, richer operational descriptions, and product integration status labels so Ariadne can keep up with upstream updates through manifest bumps.
- Deeply integrated USAspending first because recompete-heavy capture work depends on award history, incumbents, customer buying behavior, vehicles, obligations, spending patterns, and timing signals.
- Built a PIID Contract Intelligence Profile workflow that starts from one contract number and produces structured award baseline, burn posture, vehicle context, deterministic pivots, PRIME gaps, recommended next enrichments, review-gated candidates, and Hermes-observable events.
- Treated user-provided PIID intelligence templates as strategy input, not product specs; Ariadne behavior is built around the upstream USAspending MCP and Ariadne's evidence/review model.
- Kept artifact rendering downstream: huashu-design, DOCX, XLSX, presentation, and report generation should consume accepted structured profile content in a later Artifact Renderer slice.
- Deferred product workflows for SAM.gov, BLS, GSA CALC, GSA Per Diem, eCFR, Federal Register, Regulations.gov, Firecrawl/web enrichment, 1102 deliverable skills, skill chaining/LangGraph, Hermes runtime, and full Next.js UI.

**SAM.gov Enrichment Profile Epic** ← **SELECTED / READY FOR IMPLEMENTATION**

- Selected through a fresh `grill-with-docs` session after the Federal Data MCP Foundation merge.
- Plan recorded in `docs/architecture/sam-gov-enrichment-plan.md`; no new ADR is needed because the slice extends ADR 0007's upstream Federal Data Capability boundary and ADR 0006's Document Intake extraction boundary.
- Epic branch: `05-build/sam-gov-enrichment-profile`.
- Build one SAM.gov Enrichment Profile with four lanes: Entity Record, Known Opportunity, Opportunity Discovery, and Opportunity Attachment Intake.
- Use live SAM.gov by default for user-triggered workflows when `SAM_GOV_API_KEY` is configured; keep automated tests deterministic with fake adapters that are clearly labeled and never presented as live source success.
- Route approved official SAM.gov attachment downloads into Document Intake; classify documents before choosing generic extraction versus future Solicitation Parser Capability routing.
- Keep all downstream Evidence, Packet, Action Plan, Risk Register, Call Plan, Opportunity Knowledge, and follow-up route outputs review-gated.
- Defer Firecrawl/web enrichment, Theseus solicitation parsing, BLS/GSA pricing, subaward/competitor/customer profile workflows, artifact rendering, Hermes runtime, skill chaining/LangGraph, and Next.js migration.

**Next Implementation Gate**

- Start implementation on `05-build/sam-gov-enrichment-profile`, with progression branches such as `05-build/01-sam-gov-domain-store`, `05-build/02-sam-gov-adapter`, `05-build/03-sam-gov-attachments-document-intake`, and `05-build/04-sam-gov-command-surface`.
- Keep the Command Center command-first: SAM.gov data should appear with recommendations, review candidates, source limitations, attachment actions, Document Intake links, and follow-up routes rather than as passive API output.
- Run `improve-codebase-architecture` before substantive application code or refactors in the SAM.gov epic.
- Before selecting the next external integration after SAM.gov, run another `grill-with-docs` session and update PRD/CONTEXT/architecture docs inline.

**Phase 1 – Core Infrastructure**

- Hermes Agent skeleton + persistent memory
- Select and wire the first knowledge layer candidate behind an Ariadne adapter
- Basic Command Center shell with cyberpunk theme
- Keep Phase 1 increments small and shippable, favoring visible working slices over long-running infrastructure efforts.

**Phase 2 – Domain Intelligence & Strategy**

- Integrate government contracting skills + marketing skills
- Add brainstorming skill with custom HITL wrapper
- First-principles reviews integrated into workflows

**Phase 3 – Full Command Center**

- Living Capture Plans (Obsidian sync)
- Full artifact generation pipeline
- Decision-gate discipline workflows
- Self-improvement loops

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

**End of PRD v1.11**

**Phase 0, first-slice domain/storage epic, Quick Capture Knowledge Processing epic, Document Intake Command Surface epic, and Federal Data MCP Foundation + USAspending Recompete Intelligence Intake epic are complete. SAM.gov Enrichment Profile is the selected next vertical slice.**

---

_This document contains no company-identifying information and is suitable for public repository use._
