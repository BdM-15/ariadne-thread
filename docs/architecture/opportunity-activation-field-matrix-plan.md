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

## Architecture Notes

- `src/ariadne/opportunity_activation.py` owns the activation run interface, Packet Field Action Matrix, digest generation, and local store.
- `src/ariadne/production_command_center.py` calls the activation module during Opportunity Intake and reuses the activation route recommendation helper for field slots.
- `src/ariadne/server.py` exposes activation runs through the production Command Center API.
- `ARIADNE_OPPORTUNITY_ACTIVATION_DIR` keeps activation state separate from Opportunity scaffold state and workflow routing state.

## Deferred

- Live source collection, hosted/local model synthesis, external API calls, and capability execution during activation.
- UI Packet Field Action Matrix cards inside the Next.js workspace.
- Review actions that promote activation outputs into trusted Packet Field Answers, Evidence, Action Plan Items, Call Plan updates, or Research Briefs.
- Resume/progress UI for long-running activation work.
- Policy-based graduated autonomy for safe repeated activation routes.

## Validation

- Unit tests cover field coverage, answered/review-ready/blocked counts, review-gated outputs, and local store round-trips.
- Production Command Center tests cover initial activation storage after Opportunity creation and on-demand activation run API behavior.