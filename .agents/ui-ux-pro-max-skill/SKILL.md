---
name: ui-ux-pro-max-skill
description: Generates production-ready Ariadne Thread UI flows and components for the cyberpunk capture command center. Use when designing Next.js 15, Tailwind, shadcn/ui, knowledge chat, HITL sessions, quick capture, decision gates, artifact previews, or visual renderer interfaces.
---

# UI/UX Pro Max Skill

## North Star

Build Ariadne Thread as a single immersive Capture Command Center: deep black surfaces, neon cyan/magenta accents, calm information density, and workflows that keep capture professionals inside one coherent interface.

## Required Stack

- Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui, and lucide icons.
- Local design tokens for cyberpunk color, spacing, panel density, focus states, and data visualization.
- Deep modules: small public interfaces hiding rich behavior for capture workflows, knowledge panels, artifacts, and agent sessions.

## Workflow

1. Start from the PRD and `CONTEXT.md`; name domain concepts before naming files.
2. Design the real working screen first, not a marketing page.
3. Map the user job to Shipley flow: customer insight, early influence, decision gate, living plan, action, artifact.
4. Compose full workflows: empty, loading, active, error, review, export, and handoff states.
5. Keep panels dense but calm: persistent opportunity sidebar, decision-gate status, command surface, and contextual right rail where useful.
6. Use icons for tool actions, segmented controls for modes, toggles for binary settings, sliders/inputs for numeric controls, and menus for option sets.
7. Route complex behavior behind deep interfaces; avoid shallow pass-through components and duplicated state rules.
8. Verify responsive fit across desktop and mobile, including button text, grid bounds, and panel overflow.

## Ariadne Panels

- Quick Capture: frictionless intake for opportunity notes, requirements, contacts, risks, and next actions.
- Knowledge Chat: LightRAG-style retrieval, source controls, workspace settings, and answer review in one panel.
- HITL Strategy Sessions: back-and-forth brainstorming, first-principles challenge, Shipley gate discipline, and action capture.
- Living Capture Plan: editable plan viewer tied to opportunity state and knowledge artifacts.
- Artifact Preview: DOCX, XLSX, presentation, and visual artifact review with export controls.

## Visual Guardrails

- Use deep `#0a0a0a`-class backgrounds with restrained cyan and magenta accents; avoid one-note purple/blue gradients.
- Do not put cards inside cards or make page sections into floating cards.
- No decorative orbs, bokeh blobs, or purely atmospheric media.
- Text must fit its container at all supported viewports.
- Prefer real data structure and working controls over explanatory in-app copy.
