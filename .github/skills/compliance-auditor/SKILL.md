---
name: compliance-auditor
description: Dependency-gated Ariadne candidate inspired by Theseus compliance-auditor. Do not execute as a runnable skill yet. Use only to surface clause/eCFR readiness gaps, focused compliance decomposition options, and next enabling action for future artifact or proposal review paths.
capability_type: workspace_skill
capability_status: dependency_gated
maturity: prototype
validation_status: unvalidated
lifecycle_fit: bidding, pursuing
workstream_fit: compliance, proposal_development, artifact_development
product_workflow_fit: artifact_assembly, document_intake, capability_studio
persona_fit: proposal_manager, compliance_lead, capture_manager
source_family: solicitation_document
input_expectations: opportunity_id, requirement_refs, clause_refs
output_summary_shape: Future compliance audit outputs must be reviewable clause and requirement checks with cited refs.
quality_gate: clause_and_requirement_refs_reviewed_before_audit
review_destination: Artifact Content Block
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: false
missing_dependencies: clause_ecfr_readiness, solicitation_extraction, reviewed_requirement_refs
decomposition_options: clause-obligation-checker, compliance-matrix-gap-checker, section-l-response-checker, artifact-compliance-block-reviewer
product_workflow_destination: Artifact Content Block
next_enabling_action: Load reviewed requirement refs and clause/eCFR context before enabling compliance audit candidates.
provenance_requirements: capability_id, requirement_refs, clause_refs, source_refs, review_state
---

# Compliance Auditor Candidate

Dependency-gated candidate only. Do not run this as a broad compliance auditor.

## Missing Dependencies

- Clause/eCFR readiness
- Solicitation extraction
- Reviewed requirement refs

## Future Focused Skills

- `clause-obligation-checker`
- `compliance-matrix-gap-checker`
- `section-l-response-checker`
- `artifact-compliance-block-reviewer`

## Current Behavior

Report blocked status and next enabling action. Do not audit compliance, write matrix rows, create artifact blocks, or produce trusted outputs.