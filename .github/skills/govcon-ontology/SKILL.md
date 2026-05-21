---
name: govcon-ontology
description: Dependency-gated Ariadne candidate inspired by Theseus govcon-ontology. Do not execute as a runnable skill yet. Use only to surface ontology alignment gaps, focused ontology decomposition options, and next enabling action for future Knowledge Vault and capability-route alignment.
capability_type: workspace_skill
capability_status: dependency_gated
maturity: prototype
validation_status: unvalidated
lifecycle_fit: opportunity_intake, pursuing, bidding
workstream_fit: knowledge_management, compliance, capture_research
product_workflow_fit: knowledge_vault, capability_studio, document_intake
persona_fit: capture_manager, knowledge_manager, proposal_manager
source_family: ariadne_context
input_expectations: ontology_candidate_ref, knowledge_vault_schema_ref
output_summary_shape: Future govcon ontology outputs must be reviewed term alignment, relationship candidates, and schema update proposals.
quality_gate: ontology_alignment_review_before_schema_change
review_destination: Ariadne Knowledge Vault
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: false
missing_dependencies: ontology_alignment, knowledge_vault_schema_review, mirror_update_proposal_review
decomposition_options: govcon-term-alignment-checker, relationship-type-gap-review, data-element-crosswalk-builder, ontology-mirror-update-proposal
product_workflow_destination: Ariadne Knowledge Vault
next_enabling_action: Review Knowledge Vault schema and ontology alignment before enabling govcon ontology candidates.
provenance_requirements: capability_id, ontology_candidate_ref, knowledge_vault_schema_ref, source_refs, review_state
---

# Govcon Ontology Candidate

Dependency-gated candidate only. Do not run this as a broad ontology migration skill.

## Missing Dependencies

- Ontology alignment
- Knowledge Vault schema review
- Mirror Update Proposal review

## Future Focused Skills

- `govcon-term-alignment-checker`
- `relationship-type-gap-review`
- `data-element-crosswalk-builder`
- `ontology-mirror-update-proposal`

## Current Behavior

Report blocked status and next enabling action. Do not change vault schema, add relationships, migrate ontology terms, or write trusted outputs.