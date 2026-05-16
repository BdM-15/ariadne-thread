# ADR 0005: Project Ariadne Reference Knowledge

Status: accepted  
Date: 2026-05-15

## Context

The Quick Capture Knowledge Processing Workflow needs strong background material so Ariadne can infer useful capture intelligence from rushed notes and uploaded material. The Project Ariadne `knowledge/` tree contains public-source domain and company-specific capture intel for bid qualification.

## Decision

Import the full Project Ariadne `knowledge/` tree under `docs/reference/project-ariadne/knowledge/` as Capture Reference Context. Company-specific capability and organization material is intentionally in scope because it is public-source bid-qualification intel, not private company material. Use it to guide Capture Intelligence Drafts and follow-up questions, while keeping opportunity-specific Evidence separate from background reference context.

## Consequences

- Quick Capture can perform heavier foundation-informed inference without waiting for a full vector database or RAG slice.
- Future readers should not remove the company-specific public-source material merely because it names a company; that inclusion is deliberate.
- Reference pages can influence draft rationale, but they do not become trusted opportunity Evidence unless a later review workflow promotes them explicitly.
- A future retrieval/indexing decision can index this corpus behind the Knowledge Layer without changing its source provenance.
- The first Quick Capture implementation may use lightweight Reference Wiki retrieval over local Markdown, frontmatter, headings, and wikilinks before a full vector database or RAG engine exists.