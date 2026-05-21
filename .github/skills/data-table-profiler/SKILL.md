---
name: data-table-profiler
description: Use this Ariadne workspace skill when profiling a structured table or table-like source for capture work. It creates one reviewable data-table profile with shape, fields, missing values, anomalies, assumptions, provenance, and a recommended next route. Trigger for profile this table, analyze this CSV/table, data quality summary, missing fields, structured source table, or first-pass data analysis for Ariadne capability runs.
capability_type: workspace_skill
capability_status: runnable
maturity: prototype
validation_status: tested
lifecycle_fit: opportunity_intake, pursuing, bidding
workstream_fit: capture_research, competitive_intelligence, pricing, solution_shaping
product_workflow_fit: capability_studio, living_briefing_packet, capture_research
persona_fit: capture_manager, proposal_manager, solution_architect
source_family: structured_table
input_expectations: table_source_ref, table_rows
output_summary_shape: Data table profile with shape, key fields, missing values, anomalies, assumptions, gaps, and recommended next route.
quality_gate: human_review_required_before_trusted_use
review_destination: Capability Run Output
autonomy_tier: human_approval_required
model_role: none
fake_runner_supported: true
provenance_requirements: capability_id, table_source_ref, row_count, column_count, source_refs
---

# Data Table Profiler

Profile one structured table-like input and return one reviewable Capability Run Output. Keep this skill narrow: describe table shape, fields, missing values, anomalies, assumptions, gaps, provenance, and the next recommended route. Do not perform broad analysis, business interpretation, charting, model synthesis, or trusted record promotion.

## When To Use

Use this skill when the user or Ariadne route has normalized table rows from a CSV, spreadsheet extract, source profile, document table, API result, or test fixture and needs a first-pass profile before deciding whether the data is usable for packet, research, pricing, workload, or source-profile review.

## Input Contract

Provide:

- `table_source_ref`: a stable source reference or fixture reference.
- `table_rows`: normalized rows as dictionaries with column names as keys.
- Optional `source_refs`: source, document, profile, or fixture refs that support the rows.
- Optional `opportunity_id`: the Opportunity context for the Capability Run.

Do not read arbitrary external files inside this skill. If a file needs parsing, route that work to Document Intake or a parser capability first, then pass normalized rows here.

## Output Contract

Return one pending-review Capability Run Output with:

- table shape: row count and column count.
- field profiles: name, value kind, non-null count, missing count, missing ratio, distinct count, and sample values.
- key field candidates.
- anomalies, especially missing values, mixed value types, duplicate identifier values, or empty tables.
- assumptions and gaps.
- recommended next route.
- provenance showing source refs, no network, no model, no external file access, and no trusted downstream writes.

## Execution Pattern

Use the Python capability in `src/ariadne/data_table_profiler.py` when running inside this repo:

```python
from ariadne.capability_runs import CapabilityRunStore
from ariadne.data_table_profiler import DataTableProfileRequest, run_data_table_profile_capability

request = DataTableProfileRequest(
    table_label="Award history rows",
    source_ref="fixture://award-history-table",
    rows=({"Contract ID": "FA123", "Vendor": "Acme"},),
)
run = run_data_table_profile_capability(
    request=request,
    store=CapabilityRunStore(".ariadne/capability-runs"),
    opportunity_id="opp-example",
)
```

The output remains review-gated. A reviewer must explicitly accept, discard, or route it before Ariadne treats the profile as useful downstream context.

## Boundaries

- No live model calls.
- No network calls.
- No implicit file reads.
- No automatic Packet Field Answer, Evidence Item, Action Plan, research brief, or source-profile writes.
- No broad Theseus-style data analysis. If the user asks for strategy, pricing, workload, or competitive conclusions, profile the table first, then recommend the next focused route.