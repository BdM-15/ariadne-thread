# Workspace Skills

This is Ariadne Thread's canonical VS Code and GitHub Copilot skill directory.

Skills in this folder are team-shared workspace customizations. Each skill lives at `.github/skills/<name>/SKILL.md` and may include sibling references, scripts, examples, assets, or evals when needed.

If a CLI installs skills somewhere else, move them here before committing so the repository matches the VS Code-native convention used by Project Theseus.

CLI-Anything support has two workspace skills:

- `.github/skills/cli-anything/`: builder methodology for creating/refining/testing/validating agent-native CLI harnesses.
- `.github/skills/cli-hub-meta-skill/`: discovery layer for existing CLI-Anything harnesses.

Do not vendor the full CLI-Anything monorepo into this repo. Add generated harnesses only when a concrete Ariadne product or developer workflow needs one.
