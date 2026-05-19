# Artifact Assembly Foundation Plan

Date: 2026-05-19  
Status: selected through `grill-with-docs`; implementation not started

## Selected Epic

Build the **Artifact Assembly Foundation** vertical slice after the completed Capture Research Enrichment and local-dev stack follow-on work.

The slice should create the foundation that lets Ariadne move from capture knowledge, public data, research findings, action plans, and capability outputs into reviewable deliverable drafts without jumping straight to final DOCX, XLSX, presentation, visual rendering, huashu-design, or downstream artifact products.

## Product Thesis

Ariadne now has evidence, packet fields, action plans, source profiles, document intake, capability runs, knowledge context, next-action recommendations, and capture research enrichment. The next useful foundation is the artifact-preparation layer that gathers those records into structured, traceable drafts that future renderers and product workflows can consume.

The first artifact capability should prove the common artifact-building path rather than one polished output format. A capture professional should be able to assemble a reviewable Milestone Decision Briefing Packet draft from explicit source packages, inspect the section/block structure, review content at block level, and see what is ready for preview or later export.

## Decisions Resolved

- Build **Artifact Assembly Foundation** as the next selected foundation slice.
- Include the common artifact-building capability that enables the path from knowledge, data/research, and actions into deliverables/products, while avoiding a mega-slice that builds every final artifact type end to end.
- Treat skills as one kind of **Capability Module**. The slice should include an artifact-assembly capability contract, but it should not add third-party skill installation, LangGraph/Hermes orchestration, full skill chains, or final renderer execution.
- Use **Milestone Decision Briefing Packet draft** as the first tracer artifact.
- Use section-based **Artifact Drafts** made of typed **Artifact Content Blocks** such as narrative, decision summary, evidence table, action list, risk list, assumption list, gap list, and source appendix.
- Review artifact content at the block level through **Artifact Block Review**.
- Accepted Artifact Content Blocks become reviewed artifact content for preview or future export. They do not automatically become trusted Evidence Items, Packet Field Answers, Action Plan Items, Risk Register Items, Call Plan signals, Reusable Capture Insights, or other source-of-truth records.
- Record autonomy hints and review-decision signals on Artifact Content Blocks, but do not auto-accept, auto-promote, or auto-export artifact content in this slice.
- Create a narrow local-first **Artifact Assembly Store** for artifact-preparation state rather than storing drafts in the Evidence Store, packet store, Action Plan store, research store, or Capability Run Store.
- Allow AI/LLM assistance for coordination, synthesis, prioritization, and prose, while requiring every artifact output to be captured in a deterministic, source-backed, reviewable schema with a basic non-LLM fallback path.
- Create an explicit **Artifact Source Package** before draft generation so AI-assisted and deterministic assembly work from inspectable inputs rather than loose access to all Ariadne context.
- Allow Artifact Source Packages to include trusted and reviewable context, with reviewable context explicitly labeled and constrained to draft, gap, assumption, limitation, or needs-review use until related blocks are reviewed.
- Record the architecture decision in ADR 0008 because schema-first, source-package-first, block-review-first artifact assembly is hard to reverse once renderers and workflows depend on it.

## First Artifact Draft Readiness States

Artifact Drafts should use these readiness states in the first slice:

- `assembling`: source package exists or draft generation is in progress.
- `needs_review`: blocks are generated but not sufficiently reviewed.
- `partially_reviewed`: some blocks are accepted, edited, discarded, routed, or excluded.
- `preview_ready`: enough blocks are reviewed for an in-app preview.
- `export_ready`: all export-required blocks are reviewed and no blocking gaps remain.
- `superseded`: a newer draft version replaces this one.
- `canceled`: the draft is intentionally abandoned.

`export_ready` means a future renderer is allowed to consume the reviewed draft. It does not mean Ariadne has exported a DOCX, XLSX, presentation, visual deliverable, or huashu artifact.

## First Artifact Block Review Actions

Artifact Block Review should support these first actions:

- `accept`: approve the block for the draft.
- `edit`: change the block while preserving original/generated history.
- `discard`: reject the block and hide it from the active draft flow.
- `route`: send the block to a follow-up workflow such as research, evidence, packet, action plan, or capability run.
- `exclude_from_export`: keep the block for internal provenance or review while preventing it from appearing in exported deliverables.
- `mark_needs_evidence`: keep the block as useful but not export-ready until stronger support is added.

The first slice should avoid overbuilding collaboration, rich text editing, version branching, or automatic downstream promotion.

## First Command Surface

The first UI proof should be a practical **Artifact Draft Command Surface** in the existing FastAPI Command Center scaffold, not a full Next.js artifact workspace.

It should validate the workflow by showing:

- Artifact Source Package summary.
- Artifact Draft readiness state.
- Milestone Decision Briefing Packet sections.
- Artifact Content Blocks grouped by section.
- block evidence, provenance, assumptions, gaps, and source limitations.
- block review actions.
- preview-readiness and export-readiness indicators.
- links back to Evidence, Packet, Action Plan, Capture Research, Capability Runs, and Opportunity Knowledge Context.

The first surface should not become the final artifact editor, polished renderer, slide designer, DOCX previewer, or full Next.js migration.

## First Public Interface

The first implementation should expose one composed service/API for the tracer, such as `assemble_milestone_packet_draft`, instead of many separate artifact endpoints or helper calls.

The composed interface should:

- create or refresh the Artifact Source Package.
- assemble the Milestone Decision Briefing Packet draft.
- return sections, blocks, provenance, readiness, review actions, and renderer-readiness metadata.
- persist the draft in the Artifact Assembly Store.

Internal helpers can gather packet fields, evidence tables, action items, source-profile refs, research candidates, capability outputs, gaps, assumptions, and source limitations, but callers should not have to manually stitch together artifact assembly steps.

The first Artifact Source Package should be built from the existing **Opportunity Knowledge Context View** as the primary aggregator rather than separately querying every source store from the artifact module. The artifact module may follow refs into original stores for needed detail, but the dependency chain should stay: source stores -> Structured Knowledge Index / Opportunity Knowledge Context -> Artifact Source Package -> Artifact Draft -> future renderers.

## First Implementation Order

1. Add the Artifact Assembly domain model and narrow local Artifact Assembly Store.
2. Add an Artifact Source Package builder from Opportunity Knowledge Context.
3. Add a Milestone Decision Briefing Packet draft assembler with deterministic/basic AI-ready blocks.
4. Add Artifact Block Review decisions and readiness calculation.
5. Add the Artifact Draft Command Surface in the existing FastAPI Command Center scaffold.
6. Validate behavior and update docs/current-state notes.

This order keeps the store before UI, source packages before draft generation, draft schema before renderers, review/readiness before export-ready claims, and UI validation behind the domain workflow.

## Acceptance Demo

The acceptance demo should show one Opportunity moving through the Artifact Assembly Foundation loop:

1. Opportunity Knowledge Context seeds an Artifact Source Package.
2. Ariadne assembles a Milestone Decision Briefing Packet draft from the source package.
3. The draft contains sections and typed Artifact Content Blocks.
4. Trusted and reviewable support are visible and clearly labeled.
5. The user reviews blocks through Artifact Block Review actions.
6. Draft readiness changes after block review.
7. Preview-ready and export-ready states are calculated from reviewed content, support strength, and blocking gaps.
8. No DOCX, XLSX, presentation, visual, huashu, or other final exported file is generated.
9. No accepted Artifact Content Block automatically writes trusted downstream records.
10. The first Command Center Artifact Draft surface is reviewed as good enough for this stage.

## Explicitly Deferred

- Final DOCX, XLSX, presentation, visual, or huashu-design rendering.
- Bidder Comparison Chart artifact generation, scoring, slides, or add-on packet visuals.
- Customer-facing export workflows.
- LangGraph, Hermes runtime, autonomous artifact orchestration, or full skill-chain execution.
- Third-party skill installation or new external renderer installation.
- Full Next.js UI migration or polished artifact presentation surfaces.
- Automatic trusted downstream writes from accepted artifact blocks.
- Automatic artifact export or external delivery.
