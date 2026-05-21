---
name: subcontractor-assumption-list
description: Use this Ariadne workspace skill when partner, teaming, subcontractor, or scope gaps should become reviewable assumptions and questions for call-plan or partner follow-up. It does not draft SOWs, teaming agreements, legal terms, or trusted workshare records. Trigger for subcontractor assumptions, partner scope gaps, teaming questions, workshare assumptions, partner call-plan prep, or subcontractor follow-up list.
capability_type: workspace_skill
capability_status: runnable
maturity: prototype
validation_status: tested
lifecycle_fit: pursuing, bidding
workstream_fit: partner_strategy, solution_shaping
product_workflow_fit: call_plan, action_plan, capability_studio
persona_fit: capture_manager, proposal_manager, solution_architect
source_family: partner_scope_context
input_expectations: partner_scope_gaps, partner_strategy_notes, source_refs
output_summary_shape: Partner assumptions and questions with route note, source refs, review state, provenance, and no trusted downstream writes.
quality_gate: partner_or_capture_lead_review_required
review_destination: Call Plan signal
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: true
provenance_requirements: capability_id, partner_scope_gaps, partner_strategy_notes, source_refs
---

# Subcontractor Assumption List

Turn reviewed partner/scope gaps into assumptions and questions for call-plan or partner follow-up. Keep scope narrow: no SOW drafting, no workshare decision, no legal/commercial terms.

## Input Contract

- `partner_scope_gaps`: scope, partner, workshare, capability, staffing, or responsibility gaps.
- `partner_strategy_notes`: optional reviewed partner strategy context.
- `source_refs`: packet, evidence, research, or source-profile refs.

## Output Contract

Return pending-review assumptions, questions, route note, source refs, and provenance. Destination is `Call Plan signal`.

## Execution Pattern

Use `src/ariadne/focused_capture_skills.py`:

```python
from ariadne.focused_capture_skills import SubcontractorAssumptionListRequest, run_subcontractor_assumption_list_capability

run = run_subcontractor_assumption_list_capability(request=request, store=store)
```

No subcontractor SOW generation, no renderer/export, no trusted downstream writes.