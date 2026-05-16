# Competitor Intel Corpus

One subfolder per competitor (e.g., `acme-cyber/`, `globex-defense/`).

Each subfolder contains capability pages with the **same frontmatter shape**
as `knowledge/domain_intel/capabilities/` — that is, a `tags:` block with
`domains`, `contract_vehicles`, `agencies`, `geographic_scope`, `naics`,
`certifications`, `proof_strength`, plus a `summary:` line. This shape is
required by `core/fit_score.py` so the same scoring engine can rate each
competitor's coverage of an RFP's requirements (Black Hat analysis), using
`subject_pages_dir=competitor_dir(slug)` and `label="competitor:<slug>"`.

This directory is empty in P050 (scaffolding). The synthesizer that
populates it lands in P051 (`core/competitor_intel.py::synthesize_competitor`),
and the Black Hat agent that drives it lands in P052
(`agents/tools/black_hat_agent.py`).
