---
name: workload-analyzer
description: Dependency-gated Ariadne candidate inspired by Theseus workload-analyzer. Do not execute as a runnable skill yet. Use only to surface workload attachment intake gaps, focused workload decomposition options, and next enabling action for future capture research or pricing routes.
capability_type: workspace_skill
capability_status: dependency_gated
maturity: prototype
validation_status: unvalidated
lifecycle_fit: pursuing, bidding
workstream_fit: pricing, solution_shaping, capture_research
product_workflow_fit: capture_research, living_briefing_packet, action_plan
persona_fit: capture_manager, solution_architect, pricing_lead
source_family: structured_table
input_expectations: opportunity_id, workload_attachment_ref, reviewed_scope_refs
output_summary_shape: Future workload outputs must be bounded workload assumptions, source limits, staffing signals, and review routes.
quality_gate: workload_source_reviewed_before_analysis
review_destination: Capture Research candidate
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: false
missing_dependencies: workload_attachment_intake, reviewed_scope_package, data_table_profile_review
decomposition_options: staffing-table-profiler, workload-assumption-list, labor-category-gap-checker, burn-to-workload-signal-review
product_workflow_destination: Capture Research candidate
next_enabling_action: Intake workload attachments and review a data-table profile before enabling workload analysis candidates.
provenance_requirements: capability_id, workload_attachment_ref, reviewed_scope_refs, source_refs, review_state
---

# Workload Analyzer Candidate

Dependency-gated candidate only. Do not run this as a broad workload analysis skill.

## Missing Dependencies

- Workload attachment intake
- Reviewed scope package
- Data-table profile review

## Future Focused Skills

- `staffing-table-profiler`
- `workload-assumption-list`
- `labor-category-gap-checker`
- `burn-to-workload-signal-review`

## Current Behavior

Report blocked status and next enabling action. Do not infer staffing, estimate price, produce workload assumptions, or create trusted outputs.