# Ariadne Thread Context

## Intent

Build one elegant, powerful capture command center that lets a single capture professional manage 5-10+ high-value opportunities per year with less manual effort and higher consistency.

## Desired End-State

- A single immersive UI for opportunity status, decision gates, capture planning, knowledge chat, HITL strategy sessions, artifact preview, and exports.
- Shipley-aligned workflows embedded in the product rather than scattered across tools.
- Deep, composable Python modules with simple interfaces and clear ownership boundaries. TypeScript is reserved for the Next.js UI surface and frontend-adjacent tooling.
- Local-first knowledge and agent execution, with hosted reasoning models used where they add clear value.
- A self-improving agent layer that compounds learning from real capture work over time.

## Build Discipline

- PRD first, architecture foundation second, application code third.
- Python-first implementation: use the latest stable Python supported by the dependency stack, manage dependencies and virtualenvs with `uv`, run one-off Python CLIs with `uvx`, and keep `.venv/` local.
- Prefer custom in-product interfaces over tool sprawl.
- Keep the provided Project Theseus `.env` as reference only; never commit live secrets. Maintain `.env.example` as the public, secret-free configuration contract.

## Domain Language

- Capture Command Center: the single working surface for opportunities, decision gates, knowledge, HITL sessions, plans, agents, and artifacts.
- Opportunity: a potential pursuit with customer, requirements, status, evidence, risks, and next actions.
- Pursuit: the active lifecycle of moving an opportunity through Shipley-aligned gates toward bid and award.
- Decision Gate: a disciplined checkpoint that turns evidence into a go/no-go/hold action.
- Knowledge Layer: the local-first retrieval and graph context behind opportunity-specific reasoning.
- HITL Strategy Session: a structured human-in-the-loop exchange for brainstorming, challenge, review, and action capture.
- Artifact Renderer: the module family responsible for previewing and exporting DOCX, XLSX, presentation, and visual deliverables.
- Hermes Agent: the local-first persistent operator that coordinates skills, memory, and execution.
