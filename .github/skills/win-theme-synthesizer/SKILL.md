---
name: win-theme-synthesizer
description: Use this Ariadne workspace skill when accepted or reviewable customer priorities, seller strengths, and competitive gaps should become a small set of candidate win themes. It creates reviewable win theme candidates only; it does not generate full proposals, final messaging, or trusted artifact content. Trigger for win theme synthesis, candidate win themes, value proposition from capture context, seller proof to customer priority, or competitive gap messaging.
capability_type: workspace_skill
capability_status: runnable
maturity: prototype
validation_status: tested
lifecycle_fit: pursuing, bidding
workstream_fit: customer_insight, competitive_intelligence, solution_shaping
product_workflow_fit: artifact_assembly, living_briefing_packet, capability_studio
persona_fit: capture_manager, proposal_manager, solution_architect
source_family: reviewed_capture_context
input_expectations: customer_priorities, seller_strengths, competitive_gaps, source_refs
output_summary_shape: Win theme candidates with rationale, supporting inputs, assumptions, gaps, provenance, and no trusted downstream writes.
quality_gate: reviewer_confirms_proof_before_external_use
review_destination: Capability Run Output
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: true
provenance_requirements: capability_id, customer_priorities, seller_strengths, competitive_gaps, source_refs
---

# Win Theme Synthesizer

Create a small reviewable set of candidate win themes from known capture context. Keep output bounded: one customer priority, one seller strength, one competitive gap per theme.

## Input Contract

- `customer_priorities`: accepted or reviewable customer needs, hot buttons, or decision concerns.
- `seller_strengths`: accepted or reviewable proof points, discriminators, past performance, or capability strengths.
- `competitive_gaps`: known vulnerabilities, proof gaps, or competitor pressure.
- `source_refs`: evidence, packet, research, or source-profile refs.

## Output Contract

Return pending-review win theme candidates with theme statement, rationale, supporting inputs, assumptions, gaps, and source refs. Destination is `Capability Run Output`.

## Execution Pattern

Use `src/ariadne/focused_capture_skills.py`:

```python
from ariadne.focused_capture_skills import WinThemeSynthesizerRequest, run_win_theme_synthesizer_capability

run = run_win_theme_synthesizer_capability(request=request, store=store)
```

No model calls, no network calls, no proposal generation, no trusted downstream writes.