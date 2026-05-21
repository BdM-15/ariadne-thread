---
name: subcontractor-sow-builder
description: Dependency-gated Ariadne candidate inspired by Theseus subcontractor-sow-builder. Do not execute as a runnable skill yet. Use only to surface reviewed scope package and renderer readiness gaps, focused subcontractor/SOW decomposition options, and next enabling action.
capability_type: workspace_skill
capability_status: dependency_gated
maturity: prototype
validation_status: unvalidated
lifecycle_fit: pursuing, bidding
workstream_fit: partner_strategy, solution_shaping, artifact_development
product_workflow_fit: artifact_assembly, action_plan, capability_studio
persona_fit: capture_manager, proposal_manager, partner_lead
source_family: ariadne_context
input_expectations: opportunity_id, reviewed_scope_package_ref, teammate_role_refs
output_summary_shape: Future subcontractor SOW outputs must be scoped assumption lists, workshare boundaries, review gaps, and renderer-ready artifact blocks.
quality_gate: reviewed_scope_package_before_sow_draft
review_destination: Artifact Content Block
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: false
missing_dependencies: reviewed_scope_package, teammate_role_review, renderer_readiness
decomposition_options: subcontractor-assumption-list, workshare-boundary-checker, teammate-input-question-list, sow-section-block-planner
product_workflow_destination: Artifact Content Block
next_enabling_action: Review scope package and teammate roles before enabling subcontractor SOW draft candidates.
provenance_requirements: capability_id, reviewed_scope_package_ref, teammate_role_refs, source_refs, review_state
---

# Subcontractor SOW Builder Candidate

Dependency-gated candidate only. Do not run this as a broad SOW builder.

## Missing Dependencies

- Reviewed scope package
- Teammate role review
- Renderer readiness

## Future Focused Skills

- `subcontractor-assumption-list`
- `workshare-boundary-checker`
- `teammate-input-question-list`
- `sow-section-block-planner`

## Current Behavior

Report blocked status and next enabling action. Do not draft SOW language, create artifact blocks, assign teammate workshare, or write trusted outputs.