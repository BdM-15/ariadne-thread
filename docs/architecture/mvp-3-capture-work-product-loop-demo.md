# MVP-3 Capture Work Product Loop Demo Runbook

Date: 2026-05-22
Status: scripted acceptance demo for issue #106

## Goal

Run full MVP-3 first tracer from review-ready capability output to packet/action/engagement/artifact context improvements while preserving review gates and provenance.

## Preconditions

- Backend running on `http://127.0.0.1:9622`.
- Empty local runtime dirs for clean demo, or known test workspace.
- Opportunity ID: `opp-aflcmc-recompete`.

## Step 1: Create review-ready Work Product Deltas

```powershell
$base = "http://127.0.0.1:9622"

# Seed competitive-gap output into packet/action deltas
$seed = Invoke-RestMethod -Method Post -Uri "$base/api/production-command-center/work-product-deltas/from-capability-output" -ContentType "application/json" -Body (@{
  opportunity_id = "opp-aflcmc-recompete"
  capability_run_id = "<existing_or_seeded_run_id>"
  output_id = "<existing_or_seeded_output_id>"
} | ConvertTo-Json)

$seed.summary
$seed.deltas | Select-Object id,destination,review_state,field_key,title
```

Expected:

- Deltas include `living_packet` and `action_plan`.
- Each delta has source refs, capability output refs, assumptions, gaps, before/after summary.

## Step 2: Accept packet delta

```powershell
$packetDelta = ($seed.deltas | Where-Object { $_.destination -eq "living_packet" })[0]
$packetReview = Invoke-RestMethod -Method Post -Uri "$base/api/production-command-center/work-product-deltas/$($packetDelta.id)/review-decisions" -ContentType "application/json" -Body (@{
  decision = "accept"
  reviewer_rationale = "Apply competition update to living packet."
} | ConvertTo-Json)

$packetReview.delta.review_state
$packetReview.packet_field_answer | Select-Object opportunity_id,field_key,status,evidence_status,source_draft_id
$packetReview.activation_run.trigger
```

Expected:

- Delta state -> `accepted`.
- `packet_field_answer` created/updated.
- Activation run trigger -> `material_refresh`.

## Step 3: Review action implication through recommendation gate

```powershell
$actionDelta = ($seed.deltas | Where-Object { $_.destination -eq "action_plan" })[0]
$actionReview = Invoke-RestMethod -Method Post -Uri "$base/api/production-command-center/work-product-deltas/$($actionDelta.id)/review-decisions" -ContentType "application/json" -Body (@{
  decision = "accept"
  reviewer_rationale = "Queue action implication for operator review."
} | ConvertTo-Json)

$actionReview.delta.review_state
$actionReview.next_action_recommendation | Select-Object id,review_state,description
```

Expected:

- Delta state -> `accepted`.
- Next Action Recommendation created (reviewable, not trusted action write).

## Step 4: Create engagement-prep candidate

```powershell
$engagement = Invoke-RestMethod -Method Post -Uri "$base/api/production-command-center/work-product-deltas/engagement-prep" -ContentType "application/json" -Body (@{
  opportunity_id = "opp-aflcmc-recompete"
  source_preference = "action_plan_link"
} | ConvertTo-Json)

$engagement.summary
$engagement.deltas | Select-Object id,destination,review_state,title
```

Expected:

- One `call_plan` delta candidate with reviewable state and traceable provenance.

## Step 5: Verify artifact context refresh + freshness

```powershell
$artifact = Invoke-RestMethod -Method Get -Uri "$base/api/production-command-center/artifact-context-status?opportunity_id=opp-aflcmc-recompete"

$artifact.source_package | Select-Object package_id,created_at
$artifact.summary
$artifact.draft_freshness
$artifact.source_package.assumptions | Where-Object { $_ -like "artifact_context_refresh_*" }
```

Expected:

- Source package exists and reflects latest refresh timestamp.
- Assumptions include `artifact_context_refresh_*` trace refs.
- Draft freshness indicates stale/fresh relative to latest source package snapshot.

## Step 6: UI inspection checklist

Open Next.js Command Center and inspect:

- Packet mode: packet delta card shows before/after, assumptions, gaps, refs, decision state.
- Actions mode: action implication visible as delta + recommendation projection.
- Engagement mode: call/engagement prep delta candidate visible.
- Artifacts mode: source package counts, freshness status, refresh trace refs, renderer/export still disabled.

## Negative checks

- Route/discard decision creates no trusted downstream record.
- Engagement-prep review does not auto-write packet/action trusted records.
- Renderer/export calls are not triggered by MVP-3 flow.

## Validation commands used for closure

```powershell
uv run pytest -q tests/test_production_command_center.py
Set-Location ui
npm run typecheck
Set-Location ..
```

## Deferred work

- Final renderer/export adapters and export execution path (MVP-5).
- Production UI hardening and richer interaction polish (MVP-4).
- Broader risk/follow-up destination product surfaces beyond first tracer.
