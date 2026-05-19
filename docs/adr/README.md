# Architecture Decision Records

ADRs record durable architectural decisions for Ariadne Thread. They prevent future architecture reviews from re-litigating settled choices unless new evidence appears.

Use concise records with this shape:

- Status: proposed, accepted, superseded, or rejected
- Context: why the decision exists
- Decision: what we chose
- Consequences: what becomes easier or harder

## Records

- `0001-phase-0-architecture-foundation.md`: PRD-led docs, ADRs, ignored secrets, and no app code before architecture foundation.
- `0002-vscode-native-skills-location.md`: `.github/skills/` is the canonical workspace skill location.
- `0003-shipley-references-and-cli-hub-skill.md`: Shipley references live under `docs/reference/shipley/`; CLI-Anything builder is required, while CLI-Hub meta-skill is optional discovery, both without the full CLI-Anything monorepo.
- `0004-evidence-first-ai-recommendations.md`: AI recommendations must remain traceable to sources, assumptions, confidence, gaps, and rationale.
- `0005-project-ariadne-reference-knowledge.md`: Project Ariadne public-source knowledge, including company-specific bid-qualification intel, is imported as Capture Reference Context.
- `0006-document-intake-extraction-boundary.md`: Document Intake uses a shared Extraction Bundle before parser or retrieval engines become trusted knowledge.
- `0007-upstream-federal-data-mcps.md`: Ariadne integrates upstream 1102tools federal data MCPs instead of creating unique Ariadne MCP servers for the same public data sources.
- `0008-artifact-assembly-foundation.md`: Artifact capability starts with source packages, section/block drafts, and block-level review before final rendering or export.
