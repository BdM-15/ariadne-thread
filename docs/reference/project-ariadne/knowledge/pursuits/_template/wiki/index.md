# Pursuit Wiki

_Auto-generated landing page for synthesized intel. Edit freely._

## Customer

_TBD_

## Competition

_TBD_

## Win themes

_TBD_

## Open questions

_TBD_

---

## Authoring entity / relationship tags (optional)

Per-pursuit wiki pages can declare entities and relationships in their YAML
frontmatter. When present, `core/ontology_promoter.py` treats these as
ground-truth and merges them into the pursuit's Evergreen Ontology
(promoted to the Theseus knowledge graph + Neo4j on workspace mount).

This applies to **per-pursuit wikis only** — `knowledge/global_wiki/` and
`knowledge/domain_intel/` pages are methodology and intentionally skip
ontology tagging.

Validation lives in `core/wiki_ontology.py` (vendored vocabulary;
`scripts/check_ontology_sync.py` guards against drift from the Theseus
schema).

```yaml
---
title: AFCAP V Re-Compete
entities:
  - name: AFCAP V
    type: program
    description: Air Force Contract Augmentation Program, Phase V (re-compete)
  - name: HQ AFCEC
    type: organization
    description: Issuing customer
relationships:
  - src: AFCAP V
    tgt: HQ AFCEC
    type: governed_by # case-insensitive; normalized to GOVERNED_BY
    description: AFCAP V is administered by HQ AFCEC
    weight: 1.0
---
```

**Entity rules** (strict): `type` must be one of the canonical lowercase
entity types (`organization`, `program`, `requirement`, `evaluation_factor`,
…). Unknown types are rejected.

**Relationship rules** (lenient): `type` is normalized to one of the
canonical UPPER_SNAKE relationship types. Common rogue forms (`PART_OF`,
`SUBJECT_TO`, `IMPLEMENTED_BY`, …) auto-map; anything else falls back to
`RELATED_TO` with a warning so authors can update the source.

The authoritative type lists live in `core/wiki_ontology.py` (vendored
from `theseus/src/ontology/schema.py`); run
`python scripts/check_ontology_sync.py` to confirm vendored vocabulary
matches the Theseus schema.
