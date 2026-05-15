# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before Exploring, Read These

- **`PRD.md`** at the repo root for the product source of truth.
- **`CONTEXT.md`** at the repo root for domain language and current understanding.
- **`docs/adr/`** for architecture decisions that touch the area you're about to work in.

If `CONTEXT-MAP.md` appears later, treat the repo as multi-context and follow that map to the relevant context docs.

## File Structure

Single-context repo:

```text
/
├── PRD.md
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-phase-0-architecture-foundation.md
│   └── ...
└── src/
```

## Use The Glossary's Vocabulary

When output names a domain concept, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept you need is not in the glossary yet, either reconsider the language or note the gap for `grill-with-docs`.

## Flag ADR Conflicts

If output contradicts an existing ADR, surface it explicitly rather than silently overriding it.

Architecture and implementation skills should read `PRD.md` and `CONTEXT.md` before proposing application structure. ADRs should be consulted before revisiting foundational decisions.
