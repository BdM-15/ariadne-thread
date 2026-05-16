# Quick Capture Knowledge Processing Review

Date: 2026-05-16  
Scope: `02-build/quick-capture-knowledge-processing`

## Outcome

Status: complete on the epic branch after issues #9 through #15.

Delivered the first Quick Capture Knowledge Processing vertical slice: Reference Wiki influences over imported public-source capture knowledge, Capture Intelligence Drafts from rushed notes and supported text source material, per-piece review/route/skill-chain controls, review-gated promotions into trusted outputs, polished trusted evidence with raw trace/admin context, low-signal clarification routing, optional Local Admin Model assist through central local-model config, parser-required unsupported upload candidates, and an end-to-end Command Center demo thread.

## Validation

Current validation on the epic branch:

```powershell
uv run ruff check src tests
uv run pytest -q
```

Latest result: 74 tests passed.

## Key Decisions Preserved

- Quick Capture is intentionally AI-heavy: Ariadne should infer, polish, connect, and route rough notes before trusted save.
- Trusted Evidence Items save polished Capture Intelligence Draft output, not truly raw notes. Raw source text remains trace/admin context for auditability.
- Low-signal chicken scratch should rarely block the workflow, but when Ariadne cannot infer useful capture meaning, it creates a Clarification Request instead of Evidence.
- Capture Reference Context can guide draft inference but does not become opportunity-specific evidence by itself.
- Review and promotion happen at draft-part level, not only whole-draft level.
- Accepted outputs preserve raw item ID, draft ID, draft part ID, reviewer rationale, evidence IDs, confidence/gap notes, and edit history.
- Pasted text and text/Markdown uploads follow the same Quick Capture path as manual notes.
- Unsupported uploads become Document Intake Candidates until parser-backed intake exists.
- Optional Local Admin Model assist reuses central `OLLAMA_HOST` and `LOCAL_DAILY_MODEL`; no duplicate workflow-specific model/base URL variables.
- Private templates, workbooks, and engagement examples stay ignored; public normalized dictionaries are commit-safe.
- Ariadne uses port `9622`; Project Theseus owns port `9621`.

## Theseus Traceability Inspiration

Project Theseus has useful inspiration in Capture Chat source tracing and Studio reasoning views. For Ariadne, treat those patterns as inspiration only. Ariadne should prefer cleaner domain-native provenance through Evidence Items, Capture Intelligence Drafts, Draft Part Promotions, Capability Provenance, and future artifact reasoning views rather than copying Theseus UI or runtime assumptions.

## What Remains Deferred

- Durable storage beyond current local/demo adapters.
- Parser-backed Document Intake with MinerU or another adapter.
- Full Knowledge Layer/RAG/graph retrieval beyond lightweight Reference Wiki influence matching.
- Knowledge Graph View.
- Hermes runtime and Operational Learning loop.
- Call Plan/customer engagement product workflow.
- Capability Studio run history, artifact library, and reasoning/provenance views.
- Full Next.js Command Center UI.
- External research/API connector workflows.

## Next Grill Inputs

Before next implementation slice, run `grill-with-docs` and review:

- `PRD.md`
- `CONTEXT.md`
- `docs/adr/`
- `docs/architecture/phase-0-review.md`
- `docs/architecture/future-integration-strategy.md`
- this review note

Recommended next-slice candidates:

- Parser-backed Document Intake.
- Durable local storage and persisted review state.
- Knowledge Graph sensemaking.
- Hermes-assisted capture mentoring and improvement proposals.
- Call Plan/customer engagement workflow.
- Capability Studio run/provenance workflow.
