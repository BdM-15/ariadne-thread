# Ariadne Thread Copilot Instructions

Read `PRD.md`, `CONTEXT.md`, and `AGENTS.md` before substantive architecture or implementation work.

Branch substantial work through numbered epic branches:

- Use `<NN>-build/<epic-slug>` for the epic branch, such as `01-build/first-slice-domain-storage`.
- Create each incremental progression branch from the epic branch and merge it back into the epic branch, not directly into `main`.
- Keep the epic branch out of `main` until all scoped epic enhancements are implemented, tested, and reviewed.
- For first-slice progression branch names, use sibling names under the numbered namespace, such as `01-build/02-local-evidence-store-tracer`, because Git refs cannot have both `01-build/first-slice-domain-storage` and child branches beneath that exact same path.

Use workspace skills from `.github/skills/`. In particular:

- Use `setup-matt-pocock-skills` configuration from `AGENTS.md` and `docs/agents/`.
- Use `improve-codebase-architecture` before major application code or refactors.
- Use `ui-ux-pro-max` for Command Center UI work.
- Use `cli-anything` when building, refining, testing, or validating agent-native CLI harnesses for repeatable Ariadne capabilities or external tools. Use `cli-hub-meta-skill` only when checking whether an existing external-tool CLI-Anything harness already exists.
- Use `skill-creator` for every workspace skill creation, rewrite, promotion, evaluation, or material skill adjustment.
- Before building a new capability, decide whether it is primarily a Command Center UI workflow, a CLI-first harness candidate, or both; prefer CLI harnesses for repeatable, batchable, tool-facing, or agent-facing work with deterministic JSON output.
- Use Python as the main application language for backend, agents, orchestration, document processing, knowledge workflows, and platform tooling. Use Python 3.14.5 / `>=3.14` as the current baseline; only downgrade by ADR if a required dependency blocks it.
- Use `uv` for Python dependency management, lockfiles, sync, and `.venv/` creation. Use `uvx` for one-off Python CLIs. Do not introduce pip/Poetry/Pipenv workflows unless explicitly requested.
- Keep TypeScript scoped to the Next.js UI and frontend-adjacent tooling.
- Keep live secrets out of git; `.env` and `.env.*` are private reference only. Maintain `.env.example` as the public, secret-free configuration shape whenever env vars change.
- Environment files are for non-expert coders too: every env var in `.env.example` should have a nearby plain-English comment explaining what it controls, when it is required, where to get the value if applicable, and whether the default is safe for local development.
- Treat OpenAI `text-embedding-3-large` as Ariadne's single canonical embedding path unless an ADR explicitly changes that. Do not add local/alternate embedding env vars without a migration/index-isolation plan.

UI and UX work has a hard skill gate:

- Before changing any Command Center UI, visual layout, interaction flow, navigation, responsive behavior, accessibility behavior, frontend styling, or user-facing view model intended for UI display, read `.github/skills/ui-ux-pro-max/SKILL.md` in that turn and apply it.
- Treat the Living Briefing Packet, Quick Capture Inbox, Action Plan dashboard, Capability Studio, Knowledge Graph View, artifact preview/export, and future Command Center shell as UI/UX work even when the first change is a thin scaffold.
- Do not close a UI/HITL issue whose acceptance criteria require user review until the user has reviewed the first UI shape or explicitly defers that review.
- When a dev server is needed for UI validation, use the project-standard env-driven port and report the local URL.

Workspace skill changes have a hard skill-creator gate:

- Before creating, importing, rewriting, promoting, evaluating, or materially changing any skill under `.github/skills/`, read `.github/skills/skill-creator/SKILL.md` in that turn and follow its workflow.
- Treat edits to `SKILL.md`, `references/`, `assets/`, `scripts/`, or `evals/evals.json` as skill changes unless they are typo-only, formatting-only, path-only, or version-only fixes with no behavior change.
- For non-trivial skill changes, snapshot the previous skill state to a gitignored workspace location, create or update `evals/evals.json` with at least three realistic prompts, establish a baseline, draft minimally, and run at least one smoke test or eval before committing.
- Keep skills portable: use `.github/skills/<name>/SKILL.md`, prefer `assets/` over `templates/`, keep long material in `references/`, keep `SKILL.md` concise, and avoid Ariadne-only assumptions unless they are placed under `metadata` or clearly documented as workspace context.
- Before committing any non-trivial skill change, state in the commit body or chat summary that `skill-creator` was loaded, the workflow was followed, what evals or smoke test ran, and whether any Capability Catalog or future chain/handoff metadata needs an update.
