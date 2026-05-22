# MVP-3 UI Sign-Off Checklist (Issue #107)

Date: 2026-05-22
Status: awaiting human review decision

## Purpose

Capture human UX sign-off for MVP-3 first tracer UI/workflow shape.

## Preconditions

- Branch with MVP-3 implementation merged: `88-build/mvp-3-capture-work-product-loop`.
- Backend running on `http://127.0.0.1:9622`.
- UI available in `ui/` Next.js app.

## Fast validation commands

```powershell
uv run pytest -q tests/test_production_command_center.py
Set-Location ui
npm run typecheck
Set-Location ..
```

Expected: all pass.

## Human review flow

Open Command Center. Use one opportunity (`opp-aflcmc-recompete`).

### 1. Packet mode

Check:

- Delta card shows before/after clearly.
- Source refs visible + understandable.
- Assumptions + gaps visible + understandable.
- Review decisions visible + unambiguous.

Decision:

- [ ] Pass
- [ ] Follow-up needed

Notes:

-

### 2. Actions mode

Check:

- Action delta links clearly to recommendation queue item.
- Recommendation state understandable (`pending`, etc.).
- Review implications clear (reviewable queue, not trusted write).

Decision:

- [ ] Pass
- [ ] Follow-up needed

Notes:

-

### 3. Engagement mode

Check:

- Call-plan candidate summary understandable.
- Review actions clear (accept/edit/route/discard behavior).
- No hidden trusted writes.

Decision:

- [ ] Pass
- [ ] Follow-up needed

Notes:

-

### 4. Artifacts mode

Check:

- Freshness signal understandable (`fresh` vs `stale`).
- Trace refs understandable (`artifact_context_refresh_*`).
- Snapshot counts useful for operator.
- Renderer/export still clearly disabled.

Decision:

- [ ] Pass
- [ ] Follow-up needed

Notes:

-

## Final sign-off

- [ ] Human confirms MVP-3 shape good enough for current stage.
- [ ] Human rejects sign-off and requests concrete follow-up issues.

Reviewer:

Date:

## If rejected: issue template

Create one issue per concrete UX problem.

Template:

- Title: `MVP-3 UX follow-up: <short problem>`
- Why: user confusion or friction impact.
- Scope: exact mode/surface + interaction.
- Acceptance: observable behavior change.
- Priority: `P1`, `P2`, or `P3`.
