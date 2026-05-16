# ADR 0006: Document Intake Extraction Boundary

Status: accepted  
Date: 2026-05-16

## Context

Ariadne needs parser-backed Document Intake without rebuilding the existing Project Theseus solicitation parser or letting a generic parser define Ariadne's knowledge model. Generic source material, solicitation-family documents, visual source material, and future retrieval engines have different strengths, but their outputs need to flow into one capture knowledge foundation.

## Decision

Build Document Intake around a shared **Extraction Bundle** before integrating parser engines. Generic source material can use generic extraction adapters, visual source material can later use multimodal extraction capabilities, and solicitation documents can later use a specialized **Solicitation Parser Capability** such as Project Theseus. MinerU, RAGAnything, LightRAG, and similar tools may appear as configured adapters or knowledge-layer components, but Ariadne's trusted entities, relationships, provenance, and review gates stay owned by the Ariadne domain model.

## Consequences

- Ariadne can process generic source material without pretending to understand solicitation structure.
- Theseus can later integrate through a narrow solicitation parser boundary instead of being copied wholesale into Ariadne.
- Multiple parser or retrieval configurations can coexist, but they produce reviewable outputs rather than becoming competing sources of truth.
- The next Document Intake slice should prove the extraction contract and review routing before committing to a specific parser or RAG runtime.
