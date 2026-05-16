# Document Intake Command Surface Plan

Date: 2026-05-16  
Scope: completed vertical epic after Quick Capture Knowledge Processing  
Status: complete on `03-build/document-intake-command-surface`; ready to merge to `main`

## What We Built

Built a **Document Intake Command Surface** that turns uploaded source material into extraction provenance, Capture Intelligence Draft Parts, recommendations, skill-chain options, accepted source evidence, review-gated downstream candidates, Knowledge Note Projections, and Command Center actions.

The completed tracer bullet supports generic source material end to end: upload or register source material, classify it, persist an intake record, create an Extraction Bundle, convert useful findings into Capture Intelligence Draft Parts, accept source spans into Evidence Items, surface review-gated candidates for actions/packet/risk/call-plan follow-up, generate a Knowledge Note Projection, and show the workflow in the Command Center.

## Completed Issue Trail

- #17 persisted generic source material in a local Document Intake Queue.
- #18 classified visual, solicitation, and unsupported material into parser-required buckets with capability hints.
- #19 created generic Extraction Bundles with parser provenance, source spans, entity candidates, relationship candidates, confidence, and warnings.
- #20 converted Extraction Bundles into document-derived Capture Intelligence Draft Parts with recommendations and skill-chain options.
- #21 promoted accepted source spans into trusted Evidence Items with intake, bundle, parser, confidence, warning, and draft-part lineage.
- #22 surfaced review-gated downstream candidates for Capture Action Plan, Living Briefing Packet, Risk Register, and Call Plan workflows.
- #23 generated one-way Knowledge Note Projections from accepted document evidence.
- #24 declared inert future parser/retrieval adapter hooks for OCR, multimodal, Theseus solicitation parsing, MinerU, RAGAnything, and LightRAG without invoking external tools.
- #25 added a Command Center demo thread over real Document Intake behavior; the first UI shape was reviewed and accepted as good enough for now, with polish deferred.

## Intentionally Deferred

- Full MinerU integration.
- Full RAGAnything or LightRAG integration.
- Theseus solicitation parser integration.
- OCR, image understanding, and frontier-model multimodal extraction.
- Full Knowledge Graph View or graph database storage.
- Bidirectional Obsidian/Knowledge Mirror sync.
- Complex skill-chain execution or orchestration.
- Broad storage-platform redesign beyond the narrow Document Intake Store.

## Attachment Points

- **Document Intake Store** persists intake records, Extraction Bundles, review decisions, accepted evidence links, and Knowledge Note Projections.
- **Extraction Bundle** is the shared parser output contract for generic, visual, and solicitation extraction adapters.
- **Capture Intelligence Draft Parts** remain the primary review and command surface for the user.
- **Evidence Items** are the first trusted destination for accepted source spans.
- **Action Plan**, **Living Briefing Packet**, **Risk Register**, **Call Plan**, and **Knowledge Note Projection** outputs remain review-gated candidates until accepted or routed.
- **Capability Modules** can later provide MinerU, RAGAnything, LightRAG, Theseus, OCR, or multimodal extraction adapters.

## Evidence, Provenance, And Review Rules

- Intake may run low-risk local work automatically: local ingestion, classification, extraction, source-span capture, and draft preparation.
- Trusted promotion, external tool calls, broad research, deletion, sensitive label changes, and customer-facing outputs require approval.
- Parser or retrieval engines never become source of truth. They produce reviewable Extraction Bundles.
- Accepted source spans become traceable Evidence Items with source refs, parser provenance, and links back to the intake record and bundle.
- Generated Knowledge Note Projections are one-way readable notes over accepted Ariadne knowledge, not authoritative records.

## First Implementation Order

1. Build and test the domain/store layer for intake records and Extraction Bundles. Complete.
2. Convert Extraction Bundle findings into Capture Intelligence Draft Parts with recommendations, skill-chain options, and candidate routes. Complete.
3. Promote accepted source spans into Evidence Items and create review-gated candidate outputs. Complete.
4. Generate Knowledge Note Projections from accepted extracted content. Complete.
5. Add a Command Center Document Intake Queue and demo thread over real behavior. Complete.

## Next Planning Handoff

- The next `grill-with-docs` session should not reopen this epic unless it is explicitly about UI polish, real parser integration, or downstream workflow promotion.
- Use ADR 0006 as the boundary for any future Theseus, MinerU, RAGAnything, LightRAG, OCR, or multimodal integration: external tools produce reviewable Extraction Bundles, while Ariadne owns trusted knowledge and review gates.
- Decide whether the next vertical epic should stay in Command Center product workflows, move into Capability Studio/tooling, or begin a carefully bounded integration slice.
- If the next slice touches Hermes, graph visualization, MinerU, huashu-design, RAG/retrieval, external APIs, advanced skills, artifact rendering, or third-party capability installation, run `grill-with-docs` first and record the decision in `CONTEXT.md` or a new ADR.
