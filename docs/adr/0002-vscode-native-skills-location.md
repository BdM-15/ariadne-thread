# ADR 0002: VS Code-Native Skills Location

Status: accepted  
Date: 2026-05-15

## Context

VS Code workspace customizations use `.github/` for team-shared agent assets. The local VS Code agent-customization guidance recognizes skills in `.github/skills/<name>/`, `.agents/skills/<name>/`, and `.claude/skills/<name>/`, but Project Theseus uses `.github/skills/` as the canonical repository convention.

The `skills@latest` CLI currently installs the `github-copilot` and `universal` targets into `.agents/skills/`. That path is CLI-compatible, but it does not match the Theseus convention or the most natural VS Code workspace layout.

## Decision

Use `.github/skills/<name>/SKILL.md` as Ariadne Thread's canonical skill location.

Keep `.agents/` only for PRD/bootstrap notes and compatibility readmes, not as a second discoverable skill tree.

## Consequences

- Ariadne mirrors Project Theseus and VS Code's workspace-customization shape.
- GitHub Copilot can discover team-shared skills from `.github/skills/`.
- The `skills@latest list` command may not reflect `.github/skills/` because the CLI scans its own `.agents/skills/` install path; validate VS Code skills by file layout instead.
- Future CLI installs should be migrated into `.github/skills/` before commit unless the CLI adds native `.github/skills/` support.
