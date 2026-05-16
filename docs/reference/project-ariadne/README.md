# Project Ariadne Reference Knowledge

This directory preserves the Project Ariadne `knowledge/` tree as imported reference material for Ariadne Thread.

- Source: https://github.com/BdM-15/project-ariadne/tree/main/knowledge
- Source commit: `87e7eff2cbb7606b0346168fe6ee9a963b14a0ec`
- Imported: 2026-05-15
- Local copy: `docs/reference/project-ariadne/knowledge/`

## Intended Use

Use this corpus as public-source Capture Reference Context for bid qualification, Quick Capture inference, Capture Intelligence Drafts, packet gap recognition, action-plan suggestions, and capture mentoring.

The company-specific capability and organization pages are intentionally in scope because they are public-source domain intel for bid qualification. They should help Ariadne infer likely discriminators, proof points, risks, customer fit, and follow-up questions when processing messy notes or uploaded material.

The first Quick Capture implementation can treat this corpus as a lightweight Reference Wiki: local Markdown notes with frontmatter, headings, filenames, folders, and wikilinks that support auditable retrieval before Ariadne has a full vector database or RAG engine.

## Boundary

This corpus can guide inference, but it is not opportunity-specific Evidence by itself. When Ariadne produces a recommendation or draft from a raw note, the user-provided note or uploaded source remains the Source Evidence for that opportunity. Project Ariadne reference pages should be cited as background context or rationale unless a workflow later turns a specific reference page into a traceable Evidence Item under review.

Do not assume this import means a vector database, RAG engine, Obsidian sync, MinerU parsing, or Hermes runtime is already selected. Those remain later integration decisions unless implemented behind Ariadne's approved adapters.