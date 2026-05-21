---
name: incumbent-award-history-brief
description: Use this Ariadne workspace skill for narrow competitive intel from an existing USAspending PIID Contract Intelligence Profile. It creates one reviewable incumbent or award-history brief with incumbent, award, obligation, recompete, source limitation, approval, provenance, and route options. Trigger for incumbent brief, award history brief, competitive intel from PIID, recompete incumbent signal, USAspending source-profile summary, or packet-field competition support.
capability_type: workspace_skill
capability_status: runnable
maturity: prototype
validation_status: tested
lifecycle_fit: opportunity_intake, pursuing, bidding
workstream_fit: competitive_intelligence, capture_research, customer_insight
product_workflow_fit: living_briefing_packet, capture_research, action_plan, capability_studio
persona_fit: capture_manager, proposal_manager, competitive_intel_lead
source_family: usaspending
input_expectations: opportunity_id, piid_profile_ref
output_summary_shape: Incumbent award-history brief with incumbent, award, obligations, recompete signals, source limitations, assumptions, gaps, and route options.
quality_gate: cites_source_profile_and_limitations
review_destination: Packet Field Answer candidate
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: true
provenance_requirements: capability_id, input_refs, source_profile_refs, source_family, approval_basis
---

# Incumbent Award-History Brief

Create one focused competitive-intel output from one accepted or reviewable USAspending PIID Contract Intelligence Profile. Keep this skill small: it summarizes incumbent, award, obligation, recompete, and source-limitation signals so the operator can route the output into packet, research, action, or capability review.

## When To Use

Use this skill when Ariadne already has a PIID profile or source-profile ref and needs a first competitive-intel brief for an Opportunity, packet field, or capture research route. It is especially useful for incumbent questions, competition packet fields, recompete timing, and award-history context.

## Input Contract

Provide:

- `opportunity_id`: optional but preferred Opportunity context.
- `piid_profile_ref`: the selected PIID Contract Intelligence Profile or its loaded object.
- Optional `packet_field_key`: the packet field this may support, usually competition, incumbent, customer, pWin, or pricing.
- `approval_basis`: why this source-profile-backed run is allowed.

Do not call live USAspending, SAM.gov, search, model, browser, or network tools from this skill. Upstream federal-data collection belongs to source-provider capabilities before this skill runs.

## Output Contract

Return one pending-review Capability Run Output with:

- source family, source profile id, source refs, and approval basis.
- incumbent name and award summary.
- obligation and burn summary.
- deterministic recompete signals.
- source limitations and gaps.
- assumptions.
- route options for Packet Field Answer candidate, Capture Research candidate, Action Plan recommendation, and Capability Run Output.
- provenance showing no live federal-data call, no model call, no network call, and no trusted downstream writes.

## Execution Pattern

Use the Python capability in `src/ariadne/incumbent_award_history.py` when running inside this repo:

```python
from ariadne.capability_runs import CapabilityRunStore
from ariadne.incumbent_award_history import (
    IncumbentAwardHistoryBriefRequest,
    run_incumbent_award_history_brief_capability,
)

request = IncumbentAwardHistoryBriefRequest(
    opportunity_id="opp-example",
    packet_field_key="competition",
    piid_profile=loaded_piid_profile,
    approval_basis="operator_selected_source_profile",
)
run = run_incumbent_award_history_brief_capability(
    request=request,
    store=CapabilityRunStore(".ariadne/capability-runs"),
)
```

The output remains review-gated. Do not promote it into Packet Field Answers, Evidence, Capture Research, or Action Plan records without explicit review.

## Boundaries

- No broad competitor research mega-skill.
- No live federal-data calls.
- No model calls.
- No network calls.
- No automatic trusted writes.
- If the user asks for competitor strategy, price-to-win, workload, or teaming analysis, create this brief first, then route to the next focused capability.