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
- Python-first implementation: use Python 3.14.5 / `>=3.14` as the current baseline, manage dependencies and virtualenvs with `uv`, run one-off Python CLIs with `uvx`, and keep `.venv/` local. Only downgrade by ADR if a required dependency blocks 3.14.
- Prefer custom in-product interfaces over tool sprawl.
- Prefer CLI-first harnesses for repeatable, batchable, tool-facing, or agent-facing workflows that need deterministic JSON output. Keep visual judgment, strategy, and high-context human decisions in the Command Center UI.
- Keep the provided Project Theseus `.env` as reference material only; never commit live secrets or copy Theseus-specific runtime assumptions into Ariadne before architecture decisions are made. Maintain `.env.example` as the public, secret-free configuration contract.
- Treat `docs/reference/shipley/` as global capture-methodology knowledge. Use it to shape language, decision gates, workflows, and artifacts, but do not build indexing/runtime assumptions before architecture decisions are made.

## Domain Language

- Capture Command Center: the single working surface for opportunities, decision gates, knowledge, HITL sessions, plans, agents, and artifacts.
- Opportunity: a potential pursuit with customer, requirements, status, evidence, risks, and next actions.
- Pursuit: the active lifecycle of moving an opportunity through Shipley-aligned gates toward bid and award.
- Decision Gate: a disciplined checkpoint that turns evidence into a go/no-go/hold action.
- Knowledge Layer: the local-first retrieval and graph context behind opportunity-specific reasoning.
- HITL Strategy Session: a structured human-in-the-loop exchange for brainstorming, challenge, review, and action capture.
- Artifact Renderer: the module family responsible for previewing and exporting DOCX, XLSX, presentation, and visual deliverables.
- Hermes Agent: the local-first persistent operator that coordinates skills, memory, and execution.
- Global Knowledge Reference: commit-safe source material that informs product behavior and terminology without implying a specific retrieval/indexing implementation.
- Agent-Native CLI Harness: a Python CLI surface with machine-readable JSON output that exposes repeatable Ariadne or external-tool capabilities to agents, scripts, and optionally the UI.
