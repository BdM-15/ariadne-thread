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


class KnowledgeVaultVocabularyItem(BaseModel):
    id: str
    label: str
    description: str


class KnowledgeVaultSchema(BaseModel):
    page_types: tuple[KnowledgeVaultVocabularyItem, ...]
    relationship_types: tuple[KnowledgeVaultVocabularyItem, ...]


class KnowledgeVaultValidationIssue(BaseModel):
    path: str
    code: str
    message: str


class KnowledgeVaultValidationReport(BaseModel):
    valid: bool
    issues: tuple[KnowledgeVaultValidationIssue, ...]


class KnowledgeVaultReadiness(BaseModel):
    vault_root: str
    ready: bool
    present_required_paths: tuple[str, ...]
    missing_required_paths: tuple[str, ...]


PAGE_TYPES: tuple[KnowledgeVaultVocabularyItem, ...] = (
    KnowledgeVaultVocabularyItem(
        id="global_data_element",
        label="Global Data Element",
        description="Reusable packet or workflow data slot shared across opportunities.",
    ),
    KnowledgeVaultVocabularyItem(
        id="capture_concept",
        label="Capture Concept",
        description="Reusable capture methodology, strategy, or domain concept.",
    ),
    KnowledgeVaultVocabularyItem(
        id="source_summary",
        label="Source Summary",
        description="Summary of a raw source, source family, or imported reference.",
    ),
    KnowledgeVaultVocabularyItem(
        id="entity",
        label="Entity",
        description="Customer, org, vehicle, competitor, stakeholder, capability, or similar node.",
    ),
    KnowledgeVaultVocabularyItem(
        id="relationship",
        label="Relationship",
        description="Typed link page that explains connection, support, limits, and provenance.",
    ),
    KnowledgeVaultVocabularyItem(
        id="workflow_capability",
        label="Workflow Capability",
        description="Product workflow, skill, source provider, parser, renderer, or adapter context.",
    ),
    KnowledgeVaultVocabularyItem(
        id="reusable_insight_candidate",
        label="Reusable Insight Candidate",
        description="Reviewable candidate insight that may support future opportunities.",
    ),
    KnowledgeVaultVocabularyItem(
        id="opportunity_projection",
        label="Opportunity Projection",
        description="Read-only projection or summary of structured opportunity context.",
    ),
    KnowledgeVaultVocabularyItem(
        id="mirror_update_proposal",
        label="Mirror Update Proposal",
        description="Proposed structured-record change derived from vault edits.",
    ),
    KnowledgeVaultVocabularyItem(
        id="hermes_learning_proposal",
        label="Hermes Learning Proposal",
        description="Future operational-learning note or improvement proposal for review.",
    ),
)

RELATIONSHIP_TYPES: tuple[KnowledgeVaultVocabularyItem, ...] = (
    KnowledgeVaultVocabularyItem(id="supports", label="Supports", description="Source or concept supports target claim or page."),
    KnowledgeVaultVocabularyItem(id="answers", label="Answers", description="Page helps answer target data element or question."),
    KnowledgeVaultVocabularyItem(id="informs", label="Informs", description="Page provides context for target page or workflow."),
    KnowledgeVaultVocabularyItem(id="blocks", label="Blocks", description="Gap or issue blocks target workflow or answer."),
    KnowledgeVaultVocabularyItem(id="contradicts", label="Contradicts", description="Page conflicts with target claim or page."),
    KnowledgeVaultVocabularyItem(id="derived_from", label="Derived From", description="Page was derived from target source or record."),
    KnowledgeVaultVocabularyItem(id="evidence_for", label="Evidence For", description="Page provides evidence for target claim, page, or route."),
    KnowledgeVaultVocabularyItem(id="fills_gap_in", label="Fills Gap In", description="Page fills gap in target data element or workflow."),
    KnowledgeVaultVocabularyItem(id="suggests_route", label="Suggests Route", description="Page suggests target action, workflow, or capability route."),
    KnowledgeVaultVocabularyItem(id="uses_capability", label="Uses Capability", description="Workflow or route uses target capability."),
    KnowledgeVaultVocabularyItem(id="applies_to_gate", label="Applies To Gate", description="Page applies to target milestone gate."),
    KnowledgeVaultVocabularyItem(id="produces_artifact_block", label="Produces Artifact Block", description="Workflow or source can produce target artifact block."),
    KnowledgeVaultVocabularyItem(id="candidate_reusable_insight", label="Candidate Reusable Insight", description="Page may become or support target reusable insight."),
)

_PAGE_TYPE_IDS = frozenset(item.id for item in PAGE_TYPES)
_RELATIONSHIP_TYPE_IDS = frozenset(item.id for item in RELATIONSHIP_TYPES)
_SCAFFOLD_MARKDOWN_PATHS = frozenset(
    {
        "AGENTS.md",
        "index.md",
        "log.md",
        "foundation/ariadne-wiki-schema.md",
    }
)


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


def get_knowledge_vault_schema() -> KnowledgeVaultSchema:
    return KnowledgeVaultSchema(
        page_types=PAGE_TYPES,
        relationship_types=RELATIONSHIP_TYPES,
    )


def validate_knowledge_vault_pages(vault_root: Path | str) -> KnowledgeVaultValidationReport:
    root = Path(vault_root)
    issues: list[KnowledgeVaultValidationIssue] = []

    for page_path in sorted(root.rglob("*.md")):
        relative_path = _relative_markdown_path(root, page_path)
        if relative_path in _SCAFFOLD_MARKDOWN_PATHS:
            continue
        frontmatter = _read_frontmatter(page_path)
        if frontmatter is None:
            issues.append(
                KnowledgeVaultValidationIssue(
                    path=relative_path,
                    code="missing_frontmatter",
                    message="Vault page must start with frontmatter.",
                )
            )
            continue
        page_type = str(frontmatter.get("page_type", "")).strip()
        if not page_type:
            issues.append(
                KnowledgeVaultValidationIssue(
                    path=relative_path,
                    code="missing_page_type",
                    message="Vault page frontmatter must include page_type.",
                )
            )
        elif page_type not in _PAGE_TYPE_IDS:
            issues.append(
                KnowledgeVaultValidationIssue(
                    path=relative_path,
                    code="unknown_page_type",
                    message=f"Unknown vault page_type: {page_type}.",
                )
            )

        if not str(frontmatter.get("title", "")).strip():
            issues.append(
                KnowledgeVaultValidationIssue(
                    path=relative_path,
                    code="missing_title",
                    message="Vault page frontmatter must include title.",
                )
            )

        source_refs = _frontmatter_list(frontmatter.get("source_refs"))
        if not source_refs:
            issues.append(
                KnowledgeVaultValidationIssue(
                    path=relative_path,
                    code="missing_source_refs",
                    message="Vault page frontmatter must include at least one source_ref.",
                )
            )

        for relationship_ref in _frontmatter_list(frontmatter.get("relationships")):
            relationship_type = relationship_ref.split(":", 1)[0].strip()
            if relationship_type and relationship_type not in _RELATIONSHIP_TYPE_IDS:
                issues.append(
                    KnowledgeVaultValidationIssue(
                        path=relative_path,
                        code="unknown_relationship_type",
                        message=f"Unknown relationship type: {relationship_type}.",
                    )
                )

    return KnowledgeVaultValidationReport(valid=not issues, issues=tuple(issues))


def _required_paths() -> tuple[str, ...]:
    return REQUIRED_VAULT_FILES + REQUIRED_VAULT_DIRECTORIES


def _write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _relative_markdown_path(root: Path, page_path: Path) -> str:
    return page_path.relative_to(root).as_posix()


def _read_frontmatter(path: Path) -> dict[str, object] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    frontmatter: dict[str, object] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return frontmatter
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        frontmatter[key.strip()] = _parse_frontmatter_value(raw_value.strip())
    return None


def _parse_frontmatter_value(raw_value: str) -> object:
    if raw_value.startswith("[") and raw_value.endswith("]"):
        inner = raw_value[1:-1].strip()
        if not inner:
            return ()
        return tuple(item.strip() for item in inner.split(",") if item.strip())
    return raw_value.strip('"').strip("'")


def _frontmatter_list(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    return ()


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

- `global_data_element`
- `capture_concept`
- `source_summary`
- `entity`
- `relationship`
- `workflow_capability`
- `reusable_insight_candidate`
- `opportunity_projection`
- `mirror_update_proposal`
- `hermes_learning_proposal`

## Required Frontmatter

Every maintained wiki page outside scaffold files needs frontmatter:

```yaml
---
page_type: global_data_element
title: Customer Insight
source_refs: [packet-field:customer_insight]
relationships: [suggests_route:workflow/capture-research]
---
```

## Link Discipline

Use typed relationships to connect knowledge pages. Early relationship language
includes `supports`, `answers`, `informs`, `blocks`, `contradicts`,
`derived_from`, `evidence_for`, `fills_gap_in`, `suggests_route`,
`uses_capability`, `applies_to_gate`, `produces_artifact_block`, and
`candidate_reusable_insight`.

## Complementary Systems

Project Theseus belongs in this vault as complementary capability context: a
solicitation parser candidate, implementation reference, and boundary/comparison
source that can inform Ariadne workflow and adapter pages. It should be linked to
Document Intake, Solicitation Parser Capability, Extraction Bundle, parser gap,
and capability route pages. It does not own Ariadne opportunity-specific answers,
trusted evidence, review decisions, or workflow state.

## Maintenance

Update `index.md` for discoverability. Append `log.md` for ingests, queries,
lint passes, migrations, and schema changes.
"""