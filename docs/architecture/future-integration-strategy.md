# Future Integration Strategy

Date: 2026-05-15

This note explains how Ariadne's first vertical slice should leave room for Hermes, graph visualization, MinerU, huashu-design, RAG, external APIs, and advanced skills without trying to build all of them immediately.

## Principle

The first slice should create stable product concepts and interfaces, not placeholder UI. Later capabilities should plug into Opportunity, Evidence Item, Living Briefing Packet, Capture Action Plan, Capability Module, and Artifact Renderer concepts rather than inventing their own parallel data paths.

Before implementing any future integration slice, run a `grill-with-docs` session scoped to that slice. The session should review the original North Star, current PRD, CONTEXT, ADRs, and this strategy; sharpen terminology; confirm the attachment point; and document what is built now versus deferred.

## Integration Anchors

### Hermes Agent

Hermes should enter through a narrow agent runtime interface that can inspect Opportunities, Evidence Items, Action Plan Items, Capability Runs, and Exploratory Capture Sessions. Hermes may recommend next actions, draft packet updates, identify capability gaps, and create Improvement Proposals, but durable state changes continue through review or approval gates.

### Command Surfaces And Agentic Actions

Future UI surfaces should treat important work items as command surfaces, not passive records. Capture Intelligence Drafts, Evidence Items, Packet Field Answers, Action Plan Items, Call Plans, Engagement Artifacts, and Capability Run Outputs should expose context-aware actions when useful: accept, edit, discard, promote, route follow-up questions, run a skill or skill chain, start research, prepare an artifact, or recommend a next workflow such as customer engagement -> call plan. The action may be handled by Hermes, a model workflow, a CLI harness, a skill, or another Capability Module, but the product workflow owns the user-facing decision, autonomy tier, provenance, and review gate.

### Knowledge Graph View

The graph should be a projection of Ariadne's primary structured knowledge, not the primary store itself. It should read relationships among Opportunities, Evidence Items, Core Capture Workstreams, Packet Sections, Action Plan Items, Artifacts, Reusable Capture Insights, and Capability Runs. The first graph can be a local projection; a later graph database is an adapter decision, not a product-model change.

### MinerU And Document Intake

MinerU should be treated as a Document Intake adapter. It extracts text, tables, figures, page context, and other source material from uploaded documents, then Ariadne turns that output into Source Evidence. MinerU should not own opportunity state, packet logic, or the knowledge model.

### huashu-design And Artifact Rendering

huashu-design should sit behind the Artifact Renderer as a rendering capability module. It consumes structured artifact intent, packet content, visual requirements, and private Artifact Export Profiles, then produces reviewable Capability Run Outputs. Interactive huashu-design sessions should be supported through Interactive Capability Sessions when human design input is required.

### RAG And Knowledge Retrieval

RAG should sit behind a Knowledge Layer adapter. The product should ask for sourced retrieval over Ariadne knowledge; the adapter can later choose LightRAG, another graph/retrieval engine, or a custom stack. OpenAI `text-embedding-3-large` remains the canonical embedding path unless an ADR defines migration and index isolation.

### External APIs

SAM.gov, USAspending, BLS, Firecrawl, api.data.gov tools, MCPs, and future research connectors should run as Capability Modules or CLI-first harnesses. Their outputs become Source Evidence or Capability Run Outputs with API metadata, timestamps, confidence, and provenance. Credit-spending or broad external research should use the ask-before-running autonomy tier.

### Advanced Skills

Skills, skill chains, MCP tools, CLI harnesses, parsers, renderers, and model workflows are Capability Modules. Product workflows decide when to use them; Capability Studio manages local cataloging, testing, iteration, provenance, artifacts, and later third-party installation. Capability Run Outputs land in review before promotion into trusted knowledge or final artifacts.

## First Slice Requirements

The first implementation should include IDs and relationship fields that future integrations can use:

- Opportunity IDs and lifecycle state.
- Core Capture Workstream IDs.
- Packet Section IDs.
- Evidence Item IDs with source-vs-derived lineage.
- Action Plan Item IDs tied to gaps, workstreams, packet sections, and evidence.
- Capability Module metadata and Capability Run provenance fields.

The first slice should not implement full Hermes autonomy, graph storage, RAG indexing, document parsing, artifact rendering, external API research, or third-party skill installation. It should make those later integrations straightforward by giving them stable concepts and interfaces to attach to.
