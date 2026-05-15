# Ariadne Thread Copilot Instructions

Read `PRD.md`, `CONTEXT.md`, and `AGENTS.md` before substantive architecture or implementation work.

Use workspace skills from `.github/skills/`. In particular:

- Use `setup-matt-pocock-skills` configuration from `AGENTS.md` and `docs/agents/`.
- Use `improve-codebase-architecture` before major application code or refactors.
- Use `ui-ux-pro-max` for Command Center UI work.
- Use `cli-anything` when building, refining, testing, or validating agent-native CLI harnesses for repeatable Ariadne capabilities or external tools. Use `cli-hub-meta-skill` to discover existing CLI-Anything harnesses.
- Use Python as the main application language for backend, agents, orchestration, document processing, knowledge workflows, and platform tooling. Prefer the latest stable Python supported by the dependency stack; start with Python 3.13+.
- Use `uv` for Python dependency management, lockfiles, sync, and `.venv/` creation. Use `uvx` for one-off Python CLIs. Do not introduce pip/Poetry/Pipenv workflows unless explicitly requested.
- Keep TypeScript scoped to the Next.js UI and frontend-adjacent tooling.
- Keep live secrets out of git; `.env` and `.env.*` are private reference only. Maintain `.env.example` as the public, secret-free configuration shape whenever env vars change.
- Environment files are for non-expert coders too: every env var in `.env.example` should have a nearby plain-English comment explaining what it controls, when it is required, where to get the value if applicable, and whether the default is safe for local development.
- Treat OpenAI `text-embedding-3-large` as Ariadne's single canonical embedding path unless an ADR explicitly changes that. Do not add local/alternate embedding env vars without a migration/index-isolation plan.
