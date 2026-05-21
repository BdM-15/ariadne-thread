---
name: compliance-spine-planner
description: Use this Ariadne workspace skill when decomposing a broad proposal-generator request into the first narrow proposal-support tracer. It maps accepted or reviewable requirement refs to proposal or artifact sections and produces one reviewable compliance spine plan. Trigger for compliance spine, proposal generator decomposition, requirement-to-section mapping, proposal support tracer, artifact compliance block, or first proposal-support capability.
capability_type: workspace_skill
capability_status: runnable
maturity: prototype
validation_status: tested
lifecycle_fit: bidding, pursuing
workstream_fit: proposal_development, compliance, artifact_development
product_workflow_fit: artifact_assembly, living_briefing_packet, capability_studio
persona_fit: proposal_manager, capture_manager, compliance_lead
source_family: ariadne_context
input_expectations: opportunity_id, requirement_refs, proposal_sections
output_summary_shape: Compliance spine plan with requirement-to-section mapping, source refs, response prompts, compliance risks, assumptions, gaps, and future separate proposal skills.
quality_gate: requirements_mapped_to_sections_with_source_refs
review_destination: Artifact Content Block
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: true
provenance_requirements: capability_id, requirement_refs, source_refs, review_state
---

# Compliance Spine Planner

Create one narrow proposal-support output: a compliance spine plan that maps explicit requirement refs to proposal or artifact sections. This is the first decomposition tracer for the broad Theseus-style `proposal-generator` idea. It is not a full proposal generator.

## Covered Piece

This skill covers only `compliance_spine_planner`: requirement-to-section mapping with source refs, response prompts, compliance risks, assumptions, gaps, and review destination.

Keep these as separate future skills:

- `win-theme-synthesizer`
- `fab-chain-builder`
- `proposal-outline-drafter`
- `executive-summary-drafter`
- `pricing-volume-planner`

## Input Contract

Provide:

- `opportunity_id`: optional but preferred Opportunity context.
- `requirement_refs`: accepted or reviewable Ariadne requirement references with id, text, source ref, and review state.
- `proposal_sections`: the proposal or artifact sections the requirements may map into.
- Optional `source_refs`: additional context refs used by the route.

Do not parse solicitations inside this skill. Solicitation parsing remains a separate parser capability. Do not create proposal text beyond a short response prompt per requirement.

## Output Contract

Return one pending-review Capability Run Output with:

- covered proposal-generator piece and future separate skills.
- input contract, output contract, quality gate, review destination, and provenance requirements.
- one compliance spine item per requirement.
- source refs and review states.
- assumptions and gaps.
- no model, no network, no broad proposal generator runtime, and no trusted downstream writes.

## Execution Pattern

Use the Python capability in `src/ariadne/proposal_support.py` when running inside this repo:

```python
from ariadne.capability_runs import CapabilityRunStore
from ariadne.proposal_support import (
    ComplianceRequirementRef,
    ComplianceSpinePlannerRequest,
    run_compliance_spine_planner_capability,
)

request = ComplianceSpinePlannerRequest(
    opportunity_id="opp-example",
    proposal_sections=("Technical Approach", "Management Approach"),
    requirement_refs=(
        ComplianceRequirementRef(
            requirement_id="C-1",
            text="Offeror shall describe the technical approach.",
            source_ref="doc://rfp/section-c#1",
            review_state="accepted",
        ),
    ),
)
run = run_compliance_spine_planner_capability(
    request=request,
    store=CapabilityRunStore(".ariadne/capability-runs"),
)
```

The output can participate in a skill-chain plan as one stage before Artifact Block Review. A reviewer must explicitly accept, route, or discard it before it informs proposal, packet, action, or artifact records.

## Boundaries

- No full proposal generation.
- No solicitation parser behavior.
- No win themes, FAB chains, pricing narratives, outlines, executive summaries, resumes, past-performance narratives, or volume drafting.
- No model calls.
- No network calls.
- No automatic trusted writes.