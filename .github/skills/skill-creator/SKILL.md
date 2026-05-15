---
name: skill-creator
description: Creates or refines Ariadne Thread agent skills using Anthropic-style progressive disclosure and the installed write-a-skill guidance. Use when adding project skills, MCP wrappers, HITL workflows, renderer skills, or reusable agent instructions.
---

# Skill Creator

## Purpose

Create compact, discoverable, project-local skills that extend Ariadne Thread without scattering workflow logic across the app.

## Workflow

1. Confirm the skill's job, trigger phrases, inputs, outputs, and whether it needs scripts or only instructions.
2. Draft `SKILL.md` with frontmatter, a focused quick start, workflow steps, and links to one-level-deep references only when needed.
3. Keep the main skill under 100 lines where practical; move long schemas, examples, or deterministic helpers into sibling files.
4. Align every skill with the PRD: Shipley discipline, deep modules, UI-first workflows, and local-first execution.
5. Validate the description as the discovery surface: third person, concrete capability, and a `Use when...` trigger sentence.

## Guardrails

- Prefer one deep skill over several shallow overlapping skills.
- Do not bake secrets, model keys, or environment-specific paths into a skill.
- Add scripts only for deterministic work that would otherwise be repeatedly generated.
- Record durable product or architecture decisions in `CONTEXT.md` or `docs/adr/`, not inside a transient prompt.
