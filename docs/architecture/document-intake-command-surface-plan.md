# Document Intake Command Surface Plan

Date: 2026-05-16  
Scope: next vertical epic after Quick Capture Knowledge Processing

## What We Are Building Now

Build a **Document Intake Command Surface** that turns uploaded source material into extraction provenance, Capture Intelligence Draft Parts, recommendations, skill-chain options, and review-gated actions.

The first tracer bullet should support generic source material end to end: upload or register source material, classify it, persist an intake record, create an Extraction Bundle, convert useful findings into Capture Intelligence Draft Parts, accept source spans into Evidence Items, surface review-gated candidates for actions/packet/risk/call-plan follow-up, generate a Knowledge Note Projection, and show the workflow in the Command Center.

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

1. Build and test the domain/store layer for intake records and Extraction Bundles.
2. Convert Extraction Bundle findings into Capture Intelligence Draft Parts with recommendations, skill-chain options, and candidate routes.
3. Promote accepted source spans into Evidence Items and create review-gated candidate outputs.
4. Generate Knowledge Note Projections from accepted extracted content.
5. Add a Command Center Document Intake Queue over the real behavior.
