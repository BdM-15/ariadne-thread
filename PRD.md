# Ariadne Thread
**Product Requirements Document (PRD) v1.0**

**North Star: One elegant, powerful Capture Command Center that allows a single capture professional to manage the entire capture lifecycle — from opportunity identification through award — with maximum effectiveness and minimum friction.**

**Repo Name:** ariadne-thread  
**Date:** May 15, 2026  
**Status:** Ready for immediate bootstrap

---

## 1. North Star Vision & Core Guiding Principles (Non-Negotiable)

**Vision**  
A single, immersive Command Center (dark cyberpunk aesthetic — deep blacks, neon cyan/magenta accents, information-dense yet calm) where one professional can see the full state of all pursuits, advance opportunities through decision gates, generate high-quality artifacts, interact with a living knowledge layer, and leverage autonomous agents — all without leaving the main interface.

The platform embodies Shipley’s fundamental principles (customer-centricity, early influence, decision-gate discipline, living iterative planning, action-oriented execution) while leveraging modern agentic AI, deep modular architecture, and a beautiful, immersive user interface.

**Core Guiding Principles**
- **Shipley Foundation**: Every major feature and workflow must align with proven capture methodology.
- **Deep Modular Architecture (Matt Pocock influence)**: Rich functionality behind simple, clean interfaces. Constant evaluation and refactoring toward deeper, more composable modules.
- **Simplicity & Focus**: Maximum simplicity. Minimum tool sprawl. No redundancy. Dual-purpose capabilities preferred.
- **UI-First Mindset**: Custom interfaces (especially for knowledge/RAG and HITL skills) take priority. The user should complete the vast majority of capture work inside one cohesive interface.
- **Agentic Execution**: Self-improving, persistent agents that reduce manual effort over time. Hybrid model usage (powerful reasoning models for complex work + efficient local models for daily execution).
- **Self-Improvement**: The platform and its agents become more effective the more they are used on real opportunities.

**Success Criteria**
- One professional can manage 5–10+ high-value opportunities per year with significantly less manual effort and higher consistency.
- Measurable improvement in win probability and capture efficiency.
- The platform feels like a natural extension of the user’s thinking and workflow.
- The codebase remains clean, modular, and easy to evolve.

---

## 2. Developer Skills Bootstrap (Priority Zero — Install First)

**Rationale**  
Developer skills are required to *build* the platform itself. They must be active from the very first commit. Matt Pocock’s architecture guardian runs in parallel, but UI/UX and skill-creation capabilities enable us to create the custom Command Center, deep modules, and interfaces correctly from day one.

**Required Developer Skills (Install in Parallel on Day 0)**

| Skill                              | Purpose                                                                 | Installation Command / Source                                                                 |
|------------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **mattpocock/skills** (full pack, including improve-codebase-architecture and setup-matt-pocock-skills) | Architectural guardian, diagnosis, TDD, triage, issue/PRD workflows, prototyping, handoff, and productivity skills | `npx skills@latest add mattpocock/skills`, then keep committed skills under `.github/skills/` |
| **ui-ux-pro-max**                  | Master UI/UX design & component generation for cyberpunk Command Center (custom panels, Theseus-inspired interfaces, visual renderer) | Vendor from https://github.com/nextlevelbuilder/ui-ux-pro-max-skill under `.github/skills/ui-ux-pro-max/` |
| **skill-creator** (Anthropic-style) | Dynamic generation of new skills/MCPs with proper structure             | `npx skills add anthropic/skills` or equivalent skill-creator pattern; save under `.github/skills/` |
| **first-principles-skill**         | Systematic first-principles analysis for architecture and strategy      | `npx skills add awesome-skills/first-principles-skill`, then keep committed skill under `.github/skills/` |

**Exact Day-0 Installation Sequence (Run in VSCode Terminal)**

```bash
# 1. Matt Pocock Skills (Architecture Guardian)
npx skills@latest add mattpocock/skills

# 2. First-Principles Skill
npx skills add awesome-skills/first-principles-skill

# 3. Skill-Creator (for dynamic skill generation)
npx skills add anthropic/skills

# 4. Vendor ui-ux-pro-max (Critical — Run this immediately after)
```

**How to Vendor `ui-ux-pro-max` on Day 0**

After installing the skill-creator, vendor the upstream skill:

> Vendor `nextlevelbuilder/ui-ux-pro-max-skill` into `.github/skills/ui-ux-pro-max/`. Keep upstream resources (`data`, `scripts`, license, README, and skill metadata) with the skill, and patch command examples only as needed for VS Code workspace paths.

Commit the vendored skill immediately.

**Post-Installation Verification**
- Run `improve-codebase-architecture` on the fresh repo.
- Commit the resulting architectural recommendations before writing any application code.

---

## 3. Core Platform Components

| Component                        | Purpose                                                                 | GitHub / Source                                                                 |
|----------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Hermes Agent                     | Primary self-hosted, persistent, self-improving autonomous operator     | To be implemented (local-first)                                                 |
| Grok 4.3 (xAI)                   | Primary reasoning & complex artifact generation model                   | xAI Console                                                                     |
| Local Efficient Models           | Fast daily execution (Qwen3.5 / 9B-class via Ollama)                    | https://ollama.com                                                              |
| OpenAI text-embedding-3-large    | High-quality semantic search in knowledge layer                         | https://platform.openai.com                                                     |
| MinerU                           | Primary document parser (PDFs, RFPs, guides)                            | https://github.com/opendatalab/MinerU                                           |
| LightRAG (custom UI)             | Opportunity-centric knowledge management with settings + integrated chat| https://github.com/HKUDS/LightRAG                                               |
| LangGraph (selective)            | Clean skill/MCP chaining only where it adds clear value                 | https://github.com/langchain-ai/langgraph                                       |
| huashu-design                    | Visual artifact renderer (platform skill)                               | Internal (guided by ui-ux-pro-max)                                             |
| Custom Renderer Skill            | DOCX + XLSX generation (modeled on Theseus patterns)                    | Internal (guided by ui-ux-pro-max)                                             |
| Custom HITL Chat Interface       | Back-and-forth interaction for skills requiring human decision input    | Internal (guided by ui-ux-pro-max)                                             |
| Obsidian Integration             | Living PKM and capture plans                                            | https://github.com/kepano/obsidian-skills                                       |
| 1102tools/federal-contracting-skills | Government contracting deliverables (IGCE, SOW/PWS, market research)   | https://github.com/1102tools/federal-contracting-skills                         |
| coreyhaines31/marketingskills    | Value propositions, positioning, messaging, CRO                         | https://github.com/coreyhaines31/marketingskills                                |
| Firecrawl                        | Primary research/scraping engine                                        | https://github.com/mendableai/firecrawl                                         |

---

## 4. Technical Architecture

- **Frontend**: Next.js 15 + Tailwind + shadcn/ui + custom cyberpunk components (guided by ui-ux-pro-max)
- **Backend**: TypeScript, deep modular structure (enforced by Matt Pocock skills)
- **Agents**: Hermes Agent (persistent memory) + Grok 4.3 for complex work + local models for speed
- **Knowledge Layer**: LightRAG with custom Theseus-inspired UI (settings panel + chat)
- **Artifact Generation**: Custom renderer skill (DOCX, XLSX, presentations, visuals)
- **Storage**: Local-first (Obsidian + file system) with optional encrypted sync
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
- Transition to local embeddings (Ollama) when volume increases

### Firecrawl
- Site: https://www.firecrawl.dev
- Free signup → Dashboard → API Key
- Add to `.env` as `FIRECRAWL_API_KEY`
- 500 credits/month free tier (ample for research)

### Zero-Cost Local Stack
- Ollama (local models): https://ollama.com
- MinerU: `pip install mineru[all]`
- LightRAG: Local clone from GitHub

**`.env.example`**
```env
XAI_API_KEY=your_xai_key
OPENAI_API_KEY=your_openai_key
FIRECRAWL_API_KEY=your_firecrawl_key
```

---

## 6. UI/UX Requirements (Command Center Aesthetic)

- Dark cyberpunk theme (deep #0a0a0a background, neon cyan/magenta accents, subtle grid overlays)
- Information-dense but calm — mission-control feel
- Persistent sidebar with opportunity list + decision-gate status
- Custom panels guided by `ui-ux-pro-max`:
  - Quick Capture (native, frictionless)
  - Knowledge Chat (LightRAG + settings)
  - HITL Strategy Sessions (brainstorming, first-principles reviews)
  - Living Capture Plan viewer
  - Artifact preview & export
- All major workflows remain inside the single interface

---

## 7. Phased Development Roadmap

**Phase 0 – Developer Skills + Architecture Foundation (Week 0–1)** ← **CURRENT PHASE**
- Install all developer skills in parallel (Section 2)
- Vendor `ui-ux-pro-max`
- Run `improve-codebase-architecture` on fresh repo and commit recommendations
- Establish `CONTEXT.md`, `docs/adr/`, and domain language
- Bootstrap Command Center shell using `ui-ux-pro-max`

**Phase 1 – Core Infrastructure**
- Hermes Agent skeleton + persistent memory
- LightRAG with custom UI
- Basic Command Center shell with cyberpunk theme

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
├── .env.example
├── .github/
│   ├── copilot-instructions.md
│   └── skills/
│       ├── mattpocock skills...
│       ├── ui-ux-pro-max/
│       ├── first-principles-thinking/
│       └── skill-creator/
├── src/
├── docs/
│   ├── adr/
│   └── agents/
└── ui/
```

**Bootstrap Command for Copilot (use this exact prompt)**

> “Create a new public GitHub repository named `ariadne-thread`. Initialize it with this exact PRD.md as the root file. Immediately execute **Section 2 Developer Skills Bootstrap** in full — install all four skills in parallel, vendor `ui-ux-pro-max`, run `improve-codebase-architecture` on the new repo, and commit the results before writing any application code. Follow the North Star Vision and deep modular principles at every step. Set up the exact folder structure shown in the PRD.”

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

**End of PRD v1.0**

**Ready for bootstrap.**  
Once the repository is created and developer skills are installed as specified, reply with the repo URL and we will officially begin platform construction.

---

*This document contains no company-identifying information and is suitable for public repository use.*