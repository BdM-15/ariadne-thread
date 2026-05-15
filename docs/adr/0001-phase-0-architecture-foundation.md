# ADR 0001: Phase 0 Architecture Foundation

Status: accepted  
Date: 2026-05-15

## Context

Ariadne Thread starts from a PRD-led bootstrap. Before application code, the repo needs enough structure for agent skills and architecture review to share the same domain language and decision history.

The workspace also contains a Project Theseus `.env` with live keys. That file is useful as private reference for future Ariadne configuration, but it must not become public repository content.

## Decision

- Treat `PRD.md` as the product source of truth and `CONTEXT.md` as the living domain vocabulary.
- Use a single-context documentation layout: root `CONTEXT.md` and ADRs in `docs/adr/`.
- Keep developer skills project-local under `.agents/skills/`, with PRD compatibility folders under `.agents/` where useful.
- Keep `.env` ignored and publish only a secret-free `.env.example`.
- Defer Next.js and application code until after the developer-skill foundation is committed.

## Consequences

- Architecture reviews can start from shared Ariadne language instead of generic module names.
- Future agents can find skill setup, triage vocabulary, and ADRs without extra prompting.
- The public repo can be created safely without leaking Project Theseus credentials.
- Early implementation work should resist splitting tiny files only for neatness; introduce a seam when it hides meaningful workflow complexity or a second adapter appears.
