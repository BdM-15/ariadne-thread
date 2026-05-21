---
name: anomaly-route-recommender
description: Use this Ariadne workspace skill after a data-table profile identifies missing values, duplicate identifiers, mixed types, empty tables, or other table anomalies. It creates one reviewable anomaly route recommendation for Action Plan, packet, research, or data-quality follow-up without writing trusted records. Trigger for table anomaly route, data quality next action, profiler follow-up route, missing table values next step, duplicate ID review route, or route a data-table profile anomaly.
capability_type: workspace_skill
capability_status: runnable
maturity: prototype
validation_status: tested
lifecycle_fit: opportunity_intake, pursuing, bidding
workstream_fit: capture_research, competitive_intelligence, pricing, solution_shaping
product_workflow_fit: action_plan, capability_studio, living_briefing_packet, capture_research
persona_fit: capture_manager, proposal_manager, solution_architect
source_family: structured_table
input_expectations: data_table_profile, source_output_id
output_summary_shape: Anomaly route recommendation with priority, rationale, action-plan destination, assumptions, gaps, provenance, and no trusted downstream writes.
quality_gate: human_review_required_before_action_creation
review_destination: Action Plan recommendation
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: true
provenance_requirements: capability_id, data_table_profile, source_output_id, source_refs, anomaly_count
---

# Anomaly Route Recommender

Turn one reviewed or reviewable data-table profile into one pending-review route recommendation. Keep the scope narrow: decide whether table anomalies should become a data-quality action, packet/research review route, or downstream-use confirmation. Do not perform broad analysis, pricing interpretation, workload analysis, charting, model synthesis, or trusted record promotion.

## When To Use

Use this skill after `data-table-profiler` or another trusted parser has produced a structured profile with anomaly signals such as missing values, duplicate identifiers, mixed value types, or empty rows. It is a second-stage follow-up for deciding what Ariadne should ask the user to review next.

## Input Contract

Provide:

- `data_table_profile`: one profile created by the Data Table Profiler contract.
- Optional `source_output_id`: the Capability Run Output that carried the profile.
- Optional `opportunity_id`: the Opportunity context.
- Optional `approval_basis`: why this route recommendation is allowed to run.

Do not read raw files or source systems here. If source material still needs parsing or profiling, route it to Document Intake or `data-table-profiler` first.

## Output Contract

Return one pending-review Capability Run Output with:

- route id, label, priority, and rationale.
- review destination of `Action Plan recommendation`.
- anomaly list carried forward from the data-table profile.
- assumptions and gaps.
- source refs and source output id.
- provenance showing no model, no network, and no trusted downstream writes.

## Execution Pattern

Use the Python capability in `src/ariadne/anomaly_route_recommender.py` inside this repo:

```python
from ariadne.anomaly_route_recommender import (
    AnomalyRouteRecommendationRequest,
    run_anomaly_route_recommender_capability,
)
from ariadne.capability_runs import CapabilityRunStore

run = run_anomaly_route_recommender_capability(
    request=AnomalyRouteRecommendationRequest(
        data_table_profile=profile,
        source_output_id="output_data_table_profile_example",
        opportunity_id="opp-example",
    ),
    store=CapabilityRunStore(".ariadne/capability-runs"),
)
```

The output remains review-gated. A reviewer must explicitly accept or route it before Ariadne creates Action Plan items or treats the recommendation as trusted workflow state.

## Boundaries

- No live model calls.
- No network calls.
- No implicit file reads.
- No automatic Action Plan Item, Packet Field Answer, Evidence Item, research brief, or source-profile writes.
- No broad Theseus-style data analysis. If the user asks for workload, pricing, or competitive conclusions, recommend the next focused route instead of producing those conclusions here.