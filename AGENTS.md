# Ariadne Thread Agent Guide

## Agent skills

### Issue tracker

GitHub Issues are the intended tracker once the public `ariadne-thread` remote is connected. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: root `CONTEXT.md` plus ADRs in `docs/adr/`. See `docs/agents/domain.md`.

## Working Rules

- Treat `PRD.md` as the product source of truth.
- Keep live secrets out of git; the provided `.env` is reference only.
- Run architecture review before substantive application code.
- Prefer deep modules with small interfaces over scattered workflow logic.
