---
name: rfp-reverse-engineer
description: Dependency-gated Ariadne candidate inspired by Theseus rfp-reverse-engineer. Do not execute as a runnable skill yet. Use only to surface missing solicitation extraction prerequisites, focused decomposition options, and next enabling action for future RFP analysis routes.
capability_type: workspace_skill
capability_status: dependency_gated
maturity: prototype
validation_status: unvalidated
lifecycle_fit: bidding, pursuing
workstream_fit: proposal_development, compliance, capture_research
product_workflow_fit: document_intake, living_briefing_packet, artifact_assembly
persona_fit: proposal_manager, capture_manager, compliance_lead
source_family: solicitation_document
input_expectations: opportunity_id, solicitation_extraction_bundle_ref
output_summary_shape: Future RFP reverse-engineering outputs must be split into focused reviewable candidates, not one broad imported skill.
quality_gate: solicitation_extraction_reviewed_before_analysis
review_destination: Document Intake Queue
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: false
missing_dependencies: solicitation_extraction, reviewed_extraction_bundle, parser_confidence_gate
decomposition_options: evaluation-criteria-extractor, section-l-instruction-mapper, section-m-scoring-signal-parser, rfp-timeline-extractor
product_workflow_destination: Document Intake Queue
next_enabling_action: Complete solicitation extraction bundle review before enabling RFP reverse-engineering candidates.
provenance_requirements: capability_id, solicitation_extraction_bundle_ref, source_refs, review_state
---

# RFP Reverse Engineer Candidate

Dependency-gated candidate only. Do not run this as a broad RFP reverse-engineering skill.

## Missing Dependencies

- Solicitation extraction
- Reviewed Extraction Bundle
- Parser confidence gate

## Future Focused Skills

- `evaluation-criteria-extractor`
- `section-l-instruction-mapper`
- `section-m-scoring-signal-parser`
- `rfp-timeline-extractor`

## Current Behavior

Report blocked status and next enabling action. Do not parse solicitations, infer compliance, create proposal records, or write trusted outputs.