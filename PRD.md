# Ariadne Thread

**Product Requirements Document (PRD) v1.5**

**North Star: One elegant, powerful Capture Command Center that allows a single capture professional to manage the entire capture lifecycle — from opportunity identification through award — with maximum effectiveness and minimum friction.**

**Repo Name:** ariadne-thread  
**Date:** May 15, 2026  
**Status:** First-slice domain/storage epic complete; ready for next planning grill

---

## 0. Current State Snapshot (May 15, 2026)

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
- A local FastAPI runtime exists via `uv run python app.py` or `python app.py` with `.env`; the project-standard local UI port is `9621`.
- The first Command Center shell is command-first: it supports pulse checks, quick actions, and AI-support entry points rather than serving as a passive metrics wall.
- Packet data modeling now distinguishes reusable Packet Field Definitions from opportunity-specific Packet Field Answers, evidence/provenance, assumptions, confidence, gaps, Action Plan links, Shared Knowledge Entities, and Knowledge Mirror projections.
- Current automated validation: `uv run ruff check src tests` and `uv run pytest -q` pass for the first slice.

**Still Deferred**

- Hermes runtime, knowledge/retrieval engine, graph visualization, MinerU document intake, huashu-design/artifact rendering, external API integrations, advanced skill installation, and full Next.js UI are not implemented yet.
- The existing FastAPI HTML surfaces are first-slice review/runtime scaffolds, not the final frontend architecture.

**Next Build Gate**

- Start the next iteration with a new `grill-with-docs` session. Review this PRD, `CONTEXT.md`, ADRs, `docs/architecture/phase-0-review.md`, and any future-integration notes before choosing the next epic.
- The next epic should be chosen as a vertical product slice, not a broad infrastructure sweep. Candidate directions include durable local storage beyond in-memory/demo builders, Knowledge Processing Workflow from Quick Capture, Document Intake, Knowledge Graph sensemaking, or Hermes-assisted capture mentoring.
- Before any future integration slice for Hermes, graph visualization, MinerU, huashu-design, RAG/retrieval, external APIs, advanced skills, artifact rendering, or third-party capability installation, run `grill-with-docs` and record any load-bearing decisions in `CONTEXT.md` or ADRs.

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

| Component                            | Purpose                                                                                                                                 | GitHub / Source                                         |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Hermes Agent                         | Primary self-hosted, persistent, self-improving autonomous operator                                                                     | To be implemented (local-first)                         |
| Grok 4.3 (xAI)                       | Primary reasoning & complex artifact generation model                                                                                   | xAI Console                                             |
| Local Efficient Models               | Fast daily execution (Qwen3.5 / 9B-class via Ollama)                                                                                    | https://ollama.com                                      |
| OpenAI text-embedding-3-large        | High-quality semantic search in knowledge layer                                                                                         | https://platform.openai.com                             |
| MinerU                               | Primary document parser (PDFs, RFPs, guides)                                                                                            | https://github.com/opendatalab/MinerU                   |
| Knowledge Engine Candidate           | Opportunity-centric retrieval and graph context with settings + integrated chat; LightRAG is a candidate, not a committed runtime shape | https://github.com/HKUDS/LightRAG                       |
| LangGraph (selective)                | Clean skill/MCP chaining only where it adds clear value                                                                                 | https://github.com/langchain-ai/langgraph               |
| CLI-Anything Harness Methodology     | Agent-native CLI surfaces for repeatable Ariadne workflows and external software/tool access                                            | https://github.com/HKUDS/CLI-Anything                   |
| huashu-design                        | Visual artifact renderer (platform skill)                                                                                               | Internal (guided by ui-ux-pro-max)                      |
| Custom Renderer Skill                | DOCX + XLSX generation for capture artifacts                                                                                            | Internal (guided by ui-ux-pro-max)                      |
| Custom HITL Chat Interface           | Back-and-forth interaction for skills requiring human decision input                                                                    | Internal (guided by ui-ux-pro-max)                      |
| Obsidian Integration                 | Living PKM and capture plans                                                                                                            | https://github.com/kepano/obsidian-skills               |
| 1102tools/federal-contracting-skills | Government contracting deliverables (IGCE, SOW/PWS, market research)                                                                    | https://github.com/1102tools/federal-contracting-skills |
| coreyhaines31/marketingskills        | Value propositions, positioning, messaging, CRO                                                                                         | https://github.com/coreyhaines31/marketingskills        |
| Firecrawl                            | Primary research/scraping engine                                                                                                        | https://github.com/mendableai/firecrawl                 |

---

## 4. Technical Architecture

- **Primary Language**: Python 3.14.5 / `>=3.14` as the default implementation baseline for backend services, agents, orchestration, document processing, knowledge workflows, and platform tools. Downgrade only through an ADR if a required dependency blocks 3.14.
- **Python Tooling**: Use `uv` for dependency, lockfile, and virtualenv management; use `uvx` for one-off Python CLIs. Keep a local `.venv/` ignored by git.
- **Frontend**: Next.js 15 + Tailwind + shadcn/ui + custom cyberpunk components (guided by ui-ux-pro-max). Use TypeScript only for the frontend and frontend-adjacent tooling.
- **Backend**: Python-first, deep modular structure (enforced by Matt Pocock skills)
- **Initial Python Package Shape**: Start with one `src/ariadne/` package and deep internal modules for the first slice rather than many small top-level packages. Initial module homes should include configuration, opportunities, evidence, packets, action plans, and capability catalog concerns.
- **CLI-First Harnesses**: Use Python Click-style CLIs with `--json` output for repeatable, batchable, tool-facing, or agent-facing operations. These CLIs should sit behind the UI or agent runtime rather than replacing human-facing strategy workflows.
- **Evidence Store**: Store traceable Evidence Items local-first behind a Pydantic-validated interface. Start with structured local files as the first adapter, while keeping callers isolated from whether persistence later becomes SQLite, Postgres, or another storage engine.
- **Agents**: Hermes Agent (persistent memory) + Grok 4.3 for complex work + local models for speed
- **Knowledge Layer**: Opportunity-centric retrieval and graph context with a custom Command Center UI. LightRAG is a candidate component, but exact integration details should be decided during architecture work.
- **Artifact Generation**: Custom renderer skill (DOCX, XLSX, presentations, visuals)
- **Storage**: Local-first structured Evidence Store and file system with optional encrypted sync; Obsidian can be an optional human-readable Knowledge Mirror rather than the primary source of truth.
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
- MinerU: candidate document parser for PDFs/RFPs
- LightRAG: candidate knowledge layer component

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

Quick Capture should follow a low-friction idea-capture pattern: let the user dump rough thoughts, meeting fragments, stray ideas, pasted text, or uploaded files quickly, then let Ariadne classify, polish, connect, and route them through a Knowledge Processing Workflow. Ariadne should use Capture Reference Context, including the imported Project Ariadne public-source knowledge, to infer useful Capture Intelligence Drafts from rushed raw material while keeping promotion into trusted knowledge review-gated. The Capture Intelligence Draft review surface should become a command-and-action workspace: the user can accept, edit, discard, route follow-up questions, launch research, request a skill or skill chain, or prepare artifacts such as call plan recommendations when the draft implies customer engagement is needed. Review and routing should operate on individual draft parts, not only on whole-draft summaries, because some intelligence will be deterministic and low-risk while other pieces need careful curation. Ariadne should suggest relevant skill chains or product workflows per draft part and flag opportunities for Hermes to create or improve a skill when no suitable capability exists. The first stage can use lightweight Reference Wiki retrieval over local Markdown/frontmatter/wikilink-style notes before a full vector database or RAG engine exists. Processing can create Evidence Items, Opportunity Knowledge, Action Plan Items, Reusable Capture Insight candidates, or follow-up questions. Uploaded documents should enter through Document Intake, with parser tools such as MinerU treated as adapters that extract Source Evidence rather than as the knowledge model itself.

The Knowledge Layer should include a Knowledge Graph View that visualizes Ariadne's primary structured knowledge: opportunities, evidence items, core capture workstreams, packet sections, action plan items, artifacts, and reusable capture insights. The first stage should be Graph Sensemaking Mode for exploration and understanding. A later stage can add Graph Action Mode so selected nodes can create actions, suggest Insight Promotion, generate briefing sections, or launch research workflows. Obsidian may mirror selected knowledge into readable notes for browsing and reflection, but graph visualization should be built from Ariadne's source knowledge model rather than relying on Obsidian vault conventions.

If Obsidian or another Knowledge Mirror is edited directly, those edits should return to Ariadne as Mirror Update Proposals rather than directly overwriting structured knowledge. Ariadne should classify, validate, and route those proposals through the same Knowledge Processing Workflow used by Quick Capture so traceability and source-of-truth discipline are preserved.

## 6.2 Future Capability Integration Strategy

The first build slice is intentionally narrow, but it must create stable attachment points for the later systems named in the North Star. Hermes, graph visualization, MinerU, huashu-design, RAG, external APIs, and advanced skills should not be forgotten or bolted on as unrelated tools. They should plug into Ariadne's core product concepts: Opportunity, Evidence Item, Living Briefing Packet, Capture Action Plan, Capability Module, Artifact Renderer, and Knowledge Layer.

Use `docs/architecture/future-integration-strategy.md` as the working architecture note for these future integrations.

- **Hermes Agent** observes opportunities, evidence, action plans, capability runs, and exploratory sessions through a narrow agent runtime interface. It can recommend actions and create Improvement Proposals, but durable changes remain review- or approval-gated.
- **Knowledge Graph View** visualizes Ariadne's primary structured knowledge as a projection of evidence, opportunities, workstreams, packet sections, actions, artifacts, reusable insights, and capability runs.
- **MinerU** enters as a Document Intake adapter that extracts source material from uploaded documents into Source Evidence.
- **huashu-design** enters through the Artifact Renderer as a rendering capability module, including Interactive Capability Sessions when human design input is required.
- **RAG and retrieval** sit behind a Knowledge Layer adapter. The product asks for sourced retrieval; the adapter can later choose LightRAG or another engine without changing the product model.
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

**Next Planning Gate**

- Run a new `grill-with-docs` session before starting the next epic.
- Decide whether the next vertical slice should deepen durable storage, Knowledge Processing Workflow, Document Intake, Knowledge Graph sensemaking, Hermes-assisted capture mentoring, or another product workflow.
- Keep the Command Center command-first: pulse check, quick action, and AI support should take priority over passive data display.

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

**End of PRD v1.5**

**Phase 0 and first-slice domain/storage epic complete. Next work starts with a new `grill-with-docs` planning session.**

---

_This document contains no company-identifying information and is suitable for public repository use._
