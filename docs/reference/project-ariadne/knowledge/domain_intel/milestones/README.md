---
title: Capture Milestones (MS1-MS4)
updated: 2026-04-23
---

# Capture Milestones (MS1-MS4)

A four-gate capture decision model used widely across federal contractor
business-development organizations. Each gate is an executive review where
leadership evaluates an opportunity's viability, strategy, risks, and
probability of winning, then decides whether to advance, adjust, or stop.

## The four milestones

| MS | Decision | Typical timing | Briefer |
|---|---|---|---|
| **[[ms1-qualification|MS1 Qualification]]** | Pursue or drop? | 12-24 months before Final RFP | Capture Manager, Account Manager, or Ops Lead |
| **[[ms2-pursuit|MS2 Pursuit / No-Pursuit]]** | Continue investing capture resources? | 9-12 months before FRFP | Capture Manager |
| **[[ms3-bid-no-bid|MS3 Bid / No-Bid]]** | Bid the proposal? | At DRFP release, or ~30 days pre-FRFP if no DRFP expected | Capture Manager |
| **[[ms4-pricing-approval|MS4 Pricing Approval]]** | Submit at the proposed price? | 7-14 days before submission | Pricing Lead, Contracts Lead, Legal, Ops Lead, Capture Manager, Proposal Manager |

## Mapping to Shipley

The MS1-MS4 model is a four-gate compression of the seven-phase
Shipley business-development lifecycle. Each milestone corresponds
roughly to a Shipley gate:

| Milestone | Shipley equivalent | Shipley reference |
|---|---|---|
| MS1 Qualification | Gate 1 (Pursuit Decision) | [[pursuit-decision-phase]] |
| MS2 Pursuit | Gate 3 (Capture Plan) | [[capture-planning-phase]] |
| MS3 Bid/No-Bid | Gate 4 (Bid Decision) | [[bid-no-bid-decision-framework]] |
| MS4 Pricing Approval | Gate 5 (Final Price + Compliance) | [[gate-review-process]] |

The MS model trades Shipley's full granularity for fewer, higher-stakes
executive checkpoints. Both vocabularies coexist in this knowledge base:
use Shipley pages for **methodology depth**, MS pages for **decision-gate
operations**.

## What each milestone review contains

Every milestone briefing presents the same 13 information areas, scoped
to where the opportunity stands at that point in the lifecycle:

1. Opportunity synopsis (ID, role, customer, dates, contract type, value, FTEs, SB goals, top competitors)
2. Bottom Line Up Front (strategic fit, capture progress, "what will it take to win")
3. Pursuit team assignments (which roles are filled at which MS)
4. Evaluation methodology (factors, ratings, basis of evaluated price, customer award trends)
5. SWOT
6. Path to Blue progress status (5 pursuit areas x previous/current/next-steps)
7. Pricing strategy (position vs competition, customer guidance, pricing variables, summary)
8. Proposed pricing summary (MS3 onward)
9. Execution business case model (revenue + operating margin, conservative vs optimistic)
10. High-risk elements (proposal risks + execution risks + responses)
11. Action plan (action / owner / due date)
12. Promotion criteria scorecard (the gate-specific yes/no checklist)
13. Capture/Ops recommendation

The promotion-criteria scorecards are the operational heart of each
gate and are tracked per-pursuit via the `core/gate_reviews.py`
persistence layer (one row per criterion in
`<pursuit>/05_reviews/gate_scorecards.json`).

## Pursuit areas tracked at every milestone (Path to Blue)

Five pursuit areas get a Progress Status (None / Low / Medium / Good /
Complete) at every milestone, with previous-status, current-status,
status update narrative, and next-steps:

1. **Opportunity Shaping / Customer Engagement** - call plans, white papers, RFIs, customer touches
2. **Pricing Strategy** - PtW analysis, pricing position, fee structure
3. **Staffing / Key Personnel** - named hires, recruiting pipeline, retention plan
4. **Tech Solutioning** - solution architecture, discriminators, proof points
5. **Other** - teaming, capital expenditure, facilities, investments

A mature MS3 typically shows Medium-to-Good status on all five.
MS4 typically shows Good-to-Complete.

## Briefing-format guidance

Each MS page documents:
- The decision being made
- Timing window
- Promotion criteria (the operative checklist)
- Briefer + audience
- What the briefing must cover (the 13 areas, scoped to that MS)
- Optional / required slides (subcontract bids, sole-source, accelerated
  acquisitions like OTA / CSO / Phase III may omit several areas)

Use these as living references the platform agents (Mnemosyne,
Shipley Coach) can cite when helping draft milestone content from
accumulated pursuit intel.
