# Ariadne knowledge tree

Three tiers of capture knowledge:

- `global_wiki/` — Foundational, reusable knowledge (Shipley methodology, FAR/DFARS, company capabilities). Seed from Theseus ontology modules:

  ```powershell
  python ariadne/scripts/seed_global_wiki.py
  ```

- `pursuits/<slug>/` — Per-pursuit knowledge:
  - `raw/` — original artifacts (call notes, emails, transcripts)
  - `wiki/` — synthesized Obsidian-compatible Markdown
  - `evergreen_ontology.json` — promoted entities/relationships layered on top of Theseus

- `shipley_pdfs/` — Reference PDFs (Shipley Capture/Proposal Guides). Not loaded automatically; consult during writing.

All Markdown files use `[[wikilinks]]` and are fully editable in Obsidian — point your vault at this folder and you get a UI for free.
