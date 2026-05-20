from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel


REQUIRED_VAULT_DIRECTORIES: tuple[str, ...] = (
    "inbox",
    "foundation",
    "data-elements",
    "entities",
    "relationships",
    "sources",
    "opportunities",
    "workflows",
    "skills-capabilities",
    "reusable-insights",
    "proposals",
    "generated-projections",
    "reports",
    "hermes-learning",
)

REQUIRED_VAULT_FILES: tuple[str, ...] = (
    "index.md",
    "log.md",
    "AGENTS.md",
    "foundation/ariadne-wiki-schema.md",
)


class KnowledgeVaultReadiness(BaseModel):
    vault_root: str
    ready: bool
    present_required_paths: tuple[str, ...]
    missing_required_paths: tuple[str, ...]


def ensure_knowledge_vault_scaffold(vault_root: Path | str) -> KnowledgeVaultReadiness:
    root = Path(vault_root)
    root.mkdir(parents=True, exist_ok=True)

    for directory in REQUIRED_VAULT_DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)

    today = datetime.now(UTC).date().isoformat()
    _write_if_missing(root / "index.md", _index_template())
    _write_if_missing(root / "log.md", _log_template(today))
    _write_if_missing(root / "AGENTS.md", _agents_template())
    _write_if_missing(
        root / "foundation" / "ariadne-wiki-schema.md",
        _schema_template(),
    )

    return inspect_knowledge_vault_readiness(root)


def inspect_knowledge_vault_readiness(vault_root: Path | str) -> KnowledgeVaultReadiness:
    root = Path(vault_root)
    present: list[str] = []
    missing: list[str] = []

    for relative_path in _required_paths():
        path = root / relative_path
        if path.exists():
            present.append(relative_path)
        else:
            missing.append(relative_path)

    return KnowledgeVaultReadiness(
        vault_root=str(root),
        ready=not missing,
        present_required_paths=tuple(present),
        missing_required_paths=tuple(missing),
    )


def _required_paths() -> tuple[str, ...]:
    return REQUIRED_VAULT_FILES + REQUIRED_VAULT_DIRECTORIES


def _write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _index_template() -> str:
    return """# Ariadne Thread Knowledge Vault

Canonical local LLM-wiki for Ariadne global capture knowledge.

## Start Here

- [[foundation/ariadne-wiki-schema|Ariadne Wiki Schema]]
- [[log|Vault Log]]

## Main Areas

- [[data-elements/|Global Data Elements]]
- [[sources/|Source Summaries]]
- [[relationships/|Typed Relationships]]
- [[skills-capabilities/|Skills and Capabilities]]
- [[reusable-insights/|Reusable Insights]]
- [[proposals/|Mirror Update Proposals]]
- [[hermes-learning/|Hermes Learning]]

## Boundary

Vault pages can inform capture work. Opportunity-specific Packet Field Answers,
Evidence Items, Action Plan state, review decisions, and trusted workflow records
remain in Ariadne structured stores.
"""


def _log_template(today: str) -> str:
    return f"""# Ariadne Thread Knowledge Vault Log

## [{today}] scaffold | Canonical vault initialized

- Created first Ariadne LLM-wiki scaffold.
- Preserved structured-store boundary for opportunity-specific execution truth.
"""


def _agents_template() -> str:
    return """# Ariadne Wiki Maintainer Instructions

You are Ariadne wiki maintainer for this vault.

## Purpose

Maintain a persistent, compounding LLM-wiki for Ariadne capture knowledge. Update
cross-links, source summaries, concept pages, contradictions, stale claims, and
reusable insight candidates as knowledge grows.

## Source-Of-Truth Boundary

This vault owns global synthesis and relationships. It does not own
opportunity-specific execution truth. Changes affecting Packet Field Answers,
Evidence Items, Action Plan state, review decisions, source spans, Capability Run
Outputs, Artifact Block Reviews, or trusted workflow records must become Mirror
Update Proposals.
"""


def _schema_template() -> str:
    return """# Ariadne Wiki Schema

This schema adapts the Karpathy LLM-wiki pattern to Ariadne's capture platform.

## Page Families

- Global data elements
- Capture concepts
- Source summaries
- Entities
- Relationships
- Workflow and capability pages
- Reusable insight candidates
- Opportunity projections
- Mirror Update Proposals
- Hermes learning proposals

## Link Discipline

Use typed relationships to connect knowledge pages. Early relationship language
includes supports, answers, informs, blocks, contradicts, derived from, evidence
for, fills gap in, suggests route, uses capability, applies to gate, produces
artifact block, and candidate reusable insight.

## Maintenance

Update `index.md` for discoverability. Append `log.md` for ingests, queries,
lint passes, migrations, and schema changes.
"""