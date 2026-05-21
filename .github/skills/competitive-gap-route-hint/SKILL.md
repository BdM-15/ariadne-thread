---
name: competitive-gap-route-hint
description: Use this Ariadne workspace skill when an incumbent, competitor, or seller-baseline signal should become one reviewable packet/action implication. It creates a narrow competitive gap route hint for Packet Field Answer candidate review without doing broad live competitor research. Trigger for competitive gap route, incumbent signal to packet implication, seller baseline comparison, competitor implication, or packet competition hint.
capability_type: workspace_skill
capability_status: runnable
maturity: prototype
validation_status: tested
lifecycle_fit: pursuing, bidding
workstream_fit: competitive_intelligence, capture_research
product_workflow_fit: living_briefing_packet, action_plan, capability_studio
persona_fit: capture_manager, solution_architect
source_family: reviewed_competitive_context
input_expectations: incumbent_signals, seller_baseline_summary, source_refs
output_summary_shape: One competitive packet implication with recommended route, rationale, assumptions, gaps, provenance, and no trusted downstream writes.
quality_gate: states_assumptions_and_evidence_gaps
review_destination: Packet Field Answer candidate
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: true
provenance_requirements: capability_id, incumbent_signals, seller_baseline_summary, source_refs
---

# Competitive Gap Route Hint

Convert one reviewed competitive or incumbent signal plus seller baseline context into one packet implication route. Keep output narrow and review-gated.

## Input Contract

- `incumbent_signals`: incumbent, competitor, or award-history signals.
- `seller_baseline_summary`: reviewed seller proof or capability baseline summary.
- `field_key`: packet field to route toward, default `competition`.
- `source_refs`: evidence, source-profile, research, or packet refs.

## Output Contract

Return one pending-review Packet Field Answer candidate route hint with implication, recommended route, rationale, assumptions, gaps, and source refs.

## Execution Pattern

Use `src/ariadne/focused_capture_skills.py`:

```python
from ariadne.focused_capture_skills import CompetitiveGapRouteHintRequest, run_competitive_gap_route_hint_capability

run = run_competitive_gap_route_hint_capability(request=request, store=store)
```

No live research, no broad competitor dossier, no packet answer promotion, no trusted downstream writes.