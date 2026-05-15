# Evidence-First AI Recommendations

Status: accepted  
Date: 2026-05-15

Ariadne will let frontier models reason broadly, generate hypotheses, synthesize incomplete information, and recommend action under uncertainty, but user-facing recommendations must be traceable to sources, assumptions, confidence, gaps, and rationale. This is a steering decision, not a model-capability constraint: the platform should preserve the power of frontier reasoning while making its outputs auditable enough for capture decisions.

## Consequences

- Milestone decision briefing packets and other capture outputs should distinguish sourced facts, inferred judgments, assumptions, and gaps.
- Incomplete evidence does not block recommendations when the uncertainty and recommended gap-closing actions are explicit.
- Missing capture information should create backfill needs or action-plan items; missing platform support should create capability gaps for future skills, views, adapters, or workflows.
- UI, agent, and artifact workflows should preserve source traceability and rationale rather than presenting polished conclusions without provenance.
