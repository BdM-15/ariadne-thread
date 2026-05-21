from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ariadne.capabilities import (
    CapabilityCatalogEntry,
    discover_local_capability_catalog,
)
from ariadne.capture_research import (
    SourceCollectionProviderManifest,
    list_source_provider_manifests,
)
from ariadne.knowledge_vault import ensure_knowledge_vault_scaffold


class CapabilityRelationshipPageStatus(BaseModel):
    path: str
    title: str
    category: str
    exists: bool
    connected: bool
    weakly_sourced: bool
    readiness: str | None = None


class CapabilityRelationshipPageReport(BaseModel):
    vault_root: str
    pages: tuple[CapabilityRelationshipPageStatus, ...]
    page_count: int
    created_count: int = 0
    unconnected_count: int
    weakly_sourced_count: int


def ensure_capability_relationship_pages(
    vault_root: Path | str,
    *,
    workspace_root: Path | str,
    env: dict[str, str] | None = None,
) -> CapabilityRelationshipPageReport:
    root = Path(vault_root)
    ensure_knowledge_vault_scaffold(root)
    page_specs = _default_capability_relationship_page_specs(
        workspace_root=Path(workspace_root),
        env=env or {},
    )
    created_count = 0
    for spec in page_specs:
        path = root / spec["path"]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(spec["content"], encoding="utf-8")
            created_count += 1
    return inspect_capability_relationship_pages(root).model_copy(
        update={"created_count": created_count}
    )


def inspect_capability_relationship_pages(
    vault_root: Path | str,
) -> CapabilityRelationshipPageReport:
    root = Path(vault_root)
    pages: list[CapabilityRelationshipPageStatus] = []
    for folder in ("skills-capabilities", "workflows", "hermes-learning"):
        folder_path = root / folder
        if not folder_path.exists():
            continue
        for page_path in sorted(folder_path.glob("*.md")):
            frontmatter = _read_frontmatter(page_path)
            if not frontmatter:
                continue
            page_type = str(frontmatter.get("page_type", ""))
            if page_type not in {"workflow_capability", "hermes_learning_proposal"}:
                continue
            source_refs = _frontmatter_list(frontmatter.get("source_refs"))
            relationships = _frontmatter_list(frontmatter.get("relationships"))
            weakly_sourced = _has_weak_source_refs(source_refs)
            pages.append(
                CapabilityRelationshipPageStatus(
                    path=page_path.relative_to(root).as_posix(),
                    title=str(frontmatter.get("title", page_path.stem)),
                    category=str(frontmatter.get("category", "unknown")),
                    exists=True,
                    connected=bool(source_refs and relationships),
                    weakly_sourced=weakly_sourced,
                    readiness=_optional_str(frontmatter.get("readiness")),
                )
            )
    return CapabilityRelationshipPageReport(
        vault_root=str(root),
        pages=tuple(pages),
        page_count=len(pages),
        unconnected_count=sum(1 for page in pages if not page.connected),
        weakly_sourced_count=sum(1 for page in pages if page.weakly_sourced),
    )


def _default_capability_relationship_page_specs(
    *,
    workspace_root: Path,
    env: dict[str, str],
) -> tuple[dict[str, str], ...]:
    catalog = discover_local_capability_catalog(workspace_root)
    skill = _select_skill(catalog.entries)
    source_provider = _select_source_provider()
    source_provider_readiness = _source_provider_readiness(source_provider, env)
    return (
        _installed_skill_spec(skill),
        _document_intake_capability_spec(),
        _source_provider_spec(source_provider, source_provider_readiness),
        _capture_research_workflow_spec(),
        _hermes_learning_role_spec(),
    )


def _select_skill(
    entries: tuple[CapabilityCatalogEntry, ...],
) -> CapabilityCatalogEntry:
    for preferred_id in ("cli-anything", "tdd", "diagnose"):
        for entry in entries:
            if entry.id == preferred_id:
                return entry
    if entries:
        return entries[0]
    return CapabilityCatalogEntry(
        id="workspace-skill-placeholder",
        name="Workspace Skill Placeholder",
        description="No installed workspace skill was discovered.",
        capability_type="workspace_skill",
        source_path=".github/skills",
    )


def _select_source_provider() -> SourceCollectionProviderManifest:
    return next(
        manifest
        for manifest in list_source_provider_manifests()
        if manifest.id == "crawl4ai_local"
    )


def _source_provider_readiness(
    manifest: SourceCollectionProviderManifest,
    env: dict[str, str],
) -> str:
    missing = tuple(name for name in manifest.required_env_vars if not env.get(name))
    if missing:
        return "missing_config"
    return "available"


def _installed_skill_spec(skill: CapabilityCatalogEntry) -> dict[str, str]:
    slug = _slug(skill.id)
    relationships = (
        f"uses_capability:capability/{slug}",
        "suggests_route:workflow/capability-studio",
        "informs:workflow/capture-research",
        f"candidate_reusable_insight:reusable-insights/{slug}-usage-patterns",
    )
    return {
        "path": f"skills-capabilities/skill-{slug}.md",
        "content": _relationship_page_template(
            page_type="workflow_capability",
            title=skill.name,
            category="installed_skill",
            source_refs=(f"workspace-skill:{skill.source_path}",),
            relationships=relationships,
            readiness=skill.validation_status.value,
            maturity=skill.maturity.value,
            summary=skill.description or "Installed workspace skill.",
            likely_inputs=("Ariadne task context", "Workspace files", "User goal"),
            destinations=(
                "Capability Studio review",
                "Agent-native CLI harness",
                "Route recommendation",
            ),
            route_fit=(
                "Repeatable tool-facing work",
                "Batchable validation",
                "Agent handoff support",
            ),
            provenance=(skill.provenance_note, skill.source_path),
        ),
    }


def _document_intake_capability_spec() -> dict[str, str]:
    relationships = (
        "uses_capability:capability/document-intake",
        "suggests_route:workflow/document-intake",
        "informs:data-elements/primary_scope",
        "produces_artifact_block:artifact-block/source-appendix",
        "candidate_reusable_insight:reusable-insights/document-intake-routing",
    )
    return {
        "path": "skills-capabilities/capability-document-intake.md",
        "content": _relationship_page_template(
            page_type="workflow_capability",
            title="Document Intake Capability",
            category="capability_module",
            source_refs=("ariadne-module:document_intake",),
            relationships=relationships,
            readiness="tested",
            maturity="foundation",
            summary="Turns uploaded source material into reviewable extraction and downstream candidates.",
            likely_inputs=(
                "Uploaded source material",
                "Opportunity ID",
                "Review decision",
            ),
            destinations=(
                "Evidence review",
                "Packet field review",
                "Artifact source package",
            ),
            route_fit=(
                "Source-backed packet gaps",
                "Parser-required intake",
                "Source appendix preparation",
            ),
            provenance=(
                "Source material metadata",
                "Extraction bundle",
                "Review decision",
            ),
        ),
    }


def _source_provider_spec(
    manifest: SourceCollectionProviderManifest,
    readiness: str,
) -> dict[str, str]:
    relationships = (
        f"uses_capability:source-provider/{manifest.id}",
        "suggests_route:workflow/capture-research",
        "informs:data-elements/briefing-packet/customer",
        "candidate_reusable_insight:reusable-insights/source-provider-selection",
    )
    slug = _slug(manifest.id.replace("_", "-"))
    return {
        "path": f"skills-capabilities/source-provider-{slug}.md",
        "content": _relationship_page_template(
            page_type="workflow_capability",
            title=manifest.name,
            category="source_provider",
            source_refs=(f"source-provider-manifest:{manifest.id}",),
            relationships=relationships,
            readiness=readiness,
            maturity="local_first",
            summary="Capture Research source collection provider metadata; no live collection is run by this page.",
            likely_inputs=(
                "Approved source target",
                "Collection scope",
                "Provider readiness",
            ),
            destinations=(
                "Source Finding review",
                "Capture Research brief",
                "Packet field candidate",
            ),
            route_fit=(
                "Public page extraction",
                "Research source collection",
                "Source limitation discovery",
            ),
            provenance=(
                manifest.source_mode.value,
                manifest.role.value,
                *manifest.source_limitations,
            ),
        ),
    }


def _capture_research_workflow_spec() -> dict[str, str]:
    relationships = (
        "uses_capability:capability/document-intake",
        "uses_capability:source-provider/crawl4ai_local",
        "suggests_route:workflow/packet-field-action-matrix",
        "informs:data-elements/briefing-packet/customer",
        "produces_artifact_block:artifact-block/research-summary",
        "candidate_reusable_insight:reusable-insights/capture-research-routing",
    )
    return {
        "path": "workflows/capture-research.md",
        "content": _relationship_page_template(
            page_type="workflow_capability",
            title="Capture Research Workflow",
            category="product_workflow",
            source_refs=("ariadne-workflow:capture-research",),
            relationships=relationships,
            readiness="tested",
            maturity="foundation",
            summary="Plans and reviews bounded source collection, findings, and capture lenses.",
            likely_inputs=(
                "Research trigger context",
                "Source profile",
                "Operator-approved provider",
            ),
            destinations=(
                "Source findings",
                "Insight candidates",
                "Packet field review",
            ),
            route_fit=(
                "Customer/competitor gaps",
                "Source-limited packet fields",
                "Public-source enrichment",
            ),
            provenance=("Research brief", "Provider run metadata", "Review decision"),
        ),
    }


def _hermes_learning_role_spec() -> dict[str, str]:
    relationships = (
        "informs:proposals/mirror-update-proposals",
        "suggests_route:workflow/knowledge-vault-maintenance",
        "candidate_reusable_insight:hermes-learning/vault-maintenance",
    )
    return {
        "path": "hermes-learning/vault-maintainer-proposal-role.md",
        "content": _relationship_page_template(
            page_type="hermes_learning_proposal",
            title="Vault Maintainer Proposal Role",
            category="hermes_learning_role",
            source_refs=("ariadne-role:hermes-vault-maintainer",),
            relationships=relationships,
            readiness="proposal_only",
            maturity="deferred_runtime",
            summary="Future Hermes role for proposing vault maintenance and reusable learning updates.",
            likely_inputs=(
                "Vault health report",
                "Mirror update proposals",
                "Migration coverage",
            ),
            destinations=(
                "Human-reviewed improvement proposal",
                "Mirror Update Proposal",
                "Vault maintenance note",
            ),
            route_fit=(
                "Knowledge hygiene",
                "Relationship gap detection",
                "Reusable insight candidate triage",
            ),
            provenance=(
                "No direct trusted writes",
                "Human review required",
                "broad Hermes runtime behavior remains deferred",
            ),
        ),
    }


def _relationship_page_template(
    *,
    page_type: str,
    title: str,
    category: str,
    source_refs: tuple[str, ...],
    relationships: tuple[str, ...],
    readiness: str,
    maturity: str,
    summary: str,
    likely_inputs: tuple[str, ...],
    destinations: tuple[str, ...],
    route_fit: tuple[str, ...],
    provenance: tuple[str, ...],
) -> str:
    return f"""---
page_type: {page_type}
title: {title}
source_refs: [{", ".join(source_refs)}]
relationships: [{", ".join(relationships)}]
category: {category}
readiness: {readiness}
maturity: {maturity}
---

# {title}

{summary}

## Maturity Or Readiness

- Maturity: `{maturity}`
- Readiness: `{readiness}`
- No live capability execution is launched by this vault page.

## Likely Inputs

{_bullet_lines(likely_inputs)}

## Output And Review Destinations

{_bullet_lines(destinations)}

## Route Fit

{_bullet_lines(route_fit)}

## Provenance Expectations

{_bullet_lines(provenance)}

## Relationship Links

{_bullet_lines(tuple(f"`{relationship}`" for relationship in relationships))}
"""


def _bullet_lines(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _slug(value: str) -> str:
    return value.lower().replace("_", "-").replace(" ", "-")


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


def _has_weak_source_refs(source_refs: tuple[str, ...]) -> bool:
    if not source_refs:
        return True
    weak_markers = ("unknown", "placeholder", "todo", "manual:unknown", "missing")
    return any(
        any(marker in source_ref.lower() for marker in weak_markers)
        for source_ref in source_refs
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text
