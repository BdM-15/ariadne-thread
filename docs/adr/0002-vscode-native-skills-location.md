# ADR 0002: VS Code-Native Skills Location

Status: accepted  
Date: 2026-05-15

## Context

VS Code workspace customizations use `.github/` for team-shared agent assets. Project Theseus uses `.github/skills/` as the canonical repository convention, so Ariadne should follow the same shape.

The `skills@latest` CLI currently writes to its own agent-specific install location, but the committed repository layout should remain VS Code-native.

## Decision

Use `.github/skills/<name>/SKILL.md` as Ariadne Thread's canonical skill location.

Do not keep alternate committed skill trees or marker directories for installed skills.

## Consequences

- Ariadne mirrors Project Theseus and VS Code's workspace-customization shape.
- GitHub Copilot can discover team-shared skills from `.github/skills/`.
- Validate VS Code skills by file layout: every skill has `.github/skills/<name>/SKILL.md`.
- Future CLI installs should be moved into `.github/skills/` before commit unless the CLI adds native support for that path.
