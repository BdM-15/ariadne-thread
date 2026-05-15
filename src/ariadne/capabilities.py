from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


CANONICAL_CAPABILITY_LOCATIONS = (".github/skills",)


class CapabilityType(StrEnum):
    WORKSPACE_SKILL = "workspace_skill"
    CLI_HARNESS = "cli_harness"
    MCP_TOOL = "mcp_tool"
    PARSER = "parser"
    RENDERER = "renderer"
    MODEL_WORKFLOW = "model_workflow"
    ADAPTER = "adapter"


class CapabilityMaturity(StrEnum):
    PROTOTYPE = "prototype"
    EXPERIMENTAL = "experimental"
    STABLE = "stable"
    PRODUCTION = "production"


class CapabilityValidationStatus(StrEnum):
    UNVALIDATED = "unvalidated"
    TESTED = "tested"
    VALIDATED = "validated"
    DEPRECATED = "deprecated"


class CapabilityCatalogEntry(BaseModel):
    id: str
    name: str
    description: str
    capability_type: CapabilityType
    source_path: str
    maturity: CapabilityMaturity = CapabilityMaturity.EXPERIMENTAL
    validation_status: CapabilityValidationStatus = (
        CapabilityValidationStatus.UNVALIDATED
    )
    lifecycle_fit: tuple[str, ...] = ()
    workstream_fit: tuple[str, ...] = ()
    product_workflow_fit: tuple[str, ...] = ()
    provenance_note: str = "Discovered from local skill metadata."


class CapabilityCatalog(BaseModel):
    entries: tuple[CapabilityCatalogEntry, ...]
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    read_only: bool = True
    canonical_locations: tuple[str, ...] = CANONICAL_CAPABILITY_LOCATIONS


def discover_local_capability_catalog(workspace_root: Path) -> CapabilityCatalog:
    skill_root = workspace_root / ".github" / "skills"
    entries = tuple(
        _catalog_entry_from_skill_file(workspace_root, skill_file)
        for skill_file in sorted(skill_root.glob("*/SKILL.md"))
    )
    return CapabilityCatalog(entries=entries)


def _catalog_entry_from_skill_file(
    workspace_root: Path,
    skill_file: Path,
) -> CapabilityCatalogEntry:
    frontmatter = _read_frontmatter(skill_file)
    capability_id = skill_file.parent.name
    return CapabilityCatalogEntry(
        id=capability_id,
        name=frontmatter.get("name", capability_id),
        description=frontmatter.get("description", ""),
        capability_type=CapabilityType(
            frontmatter.get("capability_type", CapabilityType.WORKSPACE_SKILL.value)
        ),
        source_path=skill_file.relative_to(workspace_root).as_posix(),
        maturity=CapabilityMaturity(
            frontmatter.get("maturity", CapabilityMaturity.EXPERIMENTAL.value)
        ),
        validation_status=CapabilityValidationStatus(
            frontmatter.get(
                "validation_status",
                CapabilityValidationStatus.UNVALIDATED.value,
            )
        ),
        lifecycle_fit=_csv_values(frontmatter.get("lifecycle_fit", "")),
        workstream_fit=_csv_values(frontmatter.get("workstream_fit", "")),
        product_workflow_fit=_csv_values(frontmatter.get("product_workflow_fit", "")),
    )


def _read_frontmatter(skill_file: Path) -> dict[str, str]:
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    frontmatter: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter


def _csv_values(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())
