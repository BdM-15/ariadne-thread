# Opportunity Activation + Packet Field Action Matrix Plan

## Selected MVP Target

The next MVP target after the production Command Center UI review branch is **Opportunity Activation Run + Packet Field Action Matrix**.

Goal: after an Opportunity is created, selected, imported, or refreshed, Ariadne should inspect the Living Packet field set, identify answer paths, expose blocked and review-ready fields, recommend routes, and preserve a compact Autonomy Digest without writing trusted capture records automatically.

## First Slice

The first slice is deterministic and local-first:

- Add an `OpportunityActivationRun` model and local JSON store.
- Build a `PacketFieldActionMatrix` from canonical Packet Field Definitions and any existing Packet Field Answers.
- Produce an `Autonomy Digest` with coverage, blocked-field counts, recommended chains, approvals, source limitations, and next-best actions.
- Store an initial activation run when Opportunity Intake creates a Standard Opportunity Scaffold.
- Expose API routes to list and request activation runs for one Opportunity.
- Keep all outputs review-gated; do not create Evidence, Packet Field Answers, Action Plan Items, or other trusted records automatically.

## UI Slice

The first visible Command Center slice keeps activation inside the main Opportunity workspace:

- Load the latest activation run for the selected Opportunity from the Next.js server component.
- Show an Autonomy Digest panel with coverage gained, blocked and review-ready counts, approval needs, source limitations, skill-chain suggestions, and next-best actions.
- Show the Packet Field Action Matrix as compact field route cards with field status, evidence status, value kind, approval needs, and recommended route.
- Let the operator request a new deterministic activation run from the panel, then refresh the workspace without introducing polling or background workers.
- Add explicit per-field review controls: accept/edit creates a reviewed Packet Field Answer, while route and discard record review state without creating trusted answers.

## Review-Gated Field Promotion Slice

The first promotion path keeps the matrix operational without weakening the review gate:

- Store reviewed Packet Field Answers in a separate local `ARIADNE_PACKET_FIELD_ANSWERS_DIR` so trusted answers remain opportunity-scoped and auditable.
- Expose a production Command Center review-decision route for activation fields.
- Require an explicit accept/edit decision and value before writing a Packet Field Answer.
- Let route/discard decisions update activation-run output review state without writing trusted downstream records.
- Feed stored Packet Field Answers back into later activation runs so accepted answers show as answered fields.

## Architecture Notes

- `src/ariadne/opportunity_activation.py` owns the activation run interface, Packet Field Action Matrix, digest generation, and local store.
- `src/ariadne/packet_knowledge.py` owns the local Packet Field Answer store used by review-gated activation field promotion.
- `src/ariadne/production_command_center.py` calls the activation module during Opportunity Intake and reuses the activation route recommendation helper for field slots.
- `src/ariadne/server.py` exposes activation runs and activation field review decisions through the production Command Center API.
- `ui/components/OpportunityActivationPanel.tsx` renders the main workspace Autonomy Digest, request action, Packet Field Action Matrix, and explicit field review controls from the latest activation run.
- `ui/app/page.tsx` loads the latest activation run after selecting or creating an Opportunity and passes it to the panel.
- `ARIADNE_OPPORTUNITY_ACTIVATION_DIR` keeps activation state separate from Opportunity scaffold state and workflow routing state.
- `ARIADNE_PACKET_FIELD_ANSWERS_DIR` keeps reviewed Packet Field Answers separate from activation-run history.

## Deferred

- Live source collection, hosted/local model synthesis, external API calls, and capability execution during activation.
- Review actions that promote activation outputs into trusted Evidence, Action Plan Items, Call Plan updates, Research Briefs, or broader downstream work products.
- Resume/progress UI for long-running activation work.
- Policy-based graduated autonomy for safe repeated activation routes.

## Validation

- Unit tests cover field coverage, answered/review-ready/blocked counts, review-gated outputs, and local store round-trips.
- Unit tests also cover Packet Field Answer store round-trips, accept/edit field promotion, route-only review decisions, duplicate-review guards, and reruns that include stored answers.
- Production Command Center tests cover initial activation storage after Opportunity creation, on-demand activation run API behavior, field answer promotion, and route-only review decisions.
- Next.js validation covers the activation panel through `npm --prefix ui run typecheck`, `npm --prefix ui run build`, and local HTTP/browser smoke checks for the panel, matrix, request action, and field review controls.
