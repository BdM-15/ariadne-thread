# Command Center Work Modes IA Plan

Date: 2026-05-20  
Status: selected MVP-1B IA slice

## Purpose

Prevent the production Command Center from becoming one long scroll surface as real Opportunity work grows. The Command Center should remain the daily pulse and routing cockpit, while focused Work Modes hold the deeper action surfaces for packet fields, activation, research, documents, action plans, engagements, risks, artifacts, knowledge, and capability routes.

## Product Decision

The Command Center Home answers the first-order questions quickly:

- What is the state of this Opportunity?
- What matters next?
- What can Ariadne do now?
- What needs review?
- What work product changed?
- Where should I go to act?

Focused Work Modes handle the detailed work. The user should not need a huge single page to manage a real Opportunity with global/reference knowledge, packet data elements, capture research, documents, risk register, call plans, engagement notes, artifacts, and renderer outputs.

## First Shell Slice

- Keep the existing left rail and Opportunity switcher.
- Turn work-mode nav into deep-linkable mode links instead of inert buttons.
- Add a `mode` query parameter with stable values such as `pulse`, `packet`, `activation`, `capture`, and `artifacts`.
- Default to `pulse` as Command Center Home.
- Show only the relevant section for the selected mode while preserving current backend behavior.
- Keep unfinished modes as focused placeholder surfaces, not hidden fake product claims.

## Mode Responsibilities

- `pulse`: Opportunity state, readiness signals, top packet summary, work routing map, and next best entry points.
- `packet`: Living Packet coverage, required packet fields, answer paths, review state, source support, assumptions, and field-level actions.
- `activation`: Autonomy Digest, Packet Field Action Matrix, and activation field review controls.
- `capture`: Assisted Capture goals, route recommendation, run/review/route loop.
- `artifacts`: renderer readiness, draft/export status, future huashu-design and DOCX/XLSX paths.

Future modes may add `research`, `documents`, `action-plan`, `engagement`, `risks`, `knowledge`, and `capabilities` when those workflows have enough product behavior to justify a focused surface.

## UX Guardrails

- Command Center Home is pulse and router, not all actions.
- Product workflows first; toolchain views stay behind focused modes or Capability Studio.
- Every home item must answer either "so what?" or "where do I act?".
- Detailed review/actions live in the mode for the work product they change.
- Routes can appear on Home as summaries, but full controls belong in context.
- Do not advertise Hermes, Neo4j, LightRAG, huashu-design export, or live external execution as implemented before those product workflows exist.
- Preserve review gates: focused modes may create trusted records only through explicit accept/edit/review decisions.

## Validation

- Next.js typecheck and build pass.
- Local HTTP smoke proves each initial mode URL renders.
- Existing activation field review API and UI smoke remain valid.
- No backend behavior changes are required for the first shell slice.
