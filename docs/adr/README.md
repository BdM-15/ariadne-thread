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
