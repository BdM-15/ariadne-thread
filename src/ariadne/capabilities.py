from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


CANONICAL_CAPABILITY_LOCATIONS = (".github/skills",)


class CapabilityType(StrEnum):
    WORKSPACE_SKILL = "workspace_skill"
    SKILL_CHAIN = "skill_chain"
    CLI_HARNESS = "cli_harness"
    MCP_TOOL = "mcp_tool"
    SOURCE_PROVIDER = "source_provider"
    SOURCE_PROFILE_ROUTE = "source_profile_route"
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


class CapabilityStatus(StrEnum):
    RUNNABLE = "runnable"
    DEPENDENCY_GATED = "dependency_gated"
    DEFERRED = "deferred"
    UTILITY_META = "utility_meta"
    INSPIRATION_ONLY = "inspiration_only"


class CapabilityAutonomyTier(StrEnum):
    AUTOMATIC = "automatic"
    ASK_BEFORE_RUNNING = "ask_before_running"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


class CapabilityModelRole(StrEnum):
    NONE = "none"
    LOCAL_ADMIN_MODEL = "local_admin_model"
    FRONTIER_REASONING_MODEL = "frontier_reasoning_model"


class CapabilityContract(BaseModel):
    persona_fit: tuple[str, ...] = ()
    source_family: str | None = None
    input_expectations: tuple[str, ...] = ()
    output_summary_shape: str = "Reviewable Capability Run Output summary."
    quality_gate: str = "human_review_required"
    review_destination: str = "Capability Studio"
    autonomy_tier: CapabilityAutonomyTier = CapabilityAutonomyTier.HUMAN_APPROVAL_REQUIRED
    model_role: CapabilityModelRole = CapabilityModelRole.NONE
    fake_runner_supported: bool = False
    missing_dependencies: tuple[str, ...] = ()
    decomposition_options: tuple[str, ...] = ()
    product_workflow_destination: str | None = None
    next_enabling_action: str | None = None
    provenance_requirements: tuple[str, ...] = (
        "capability_id",
        "source_path",
        "input_refs",
    )


class CapabilityCatalogEntry(BaseModel):
    id: str
    name: str
    description: str
    capability_type: CapabilityType
    capability_status: CapabilityStatus = CapabilityStatus.RUNNABLE
    source_path: str
    maturity: CapabilityMaturity = CapabilityMaturity.EXPERIMENTAL
    validation_status: CapabilityValidationStatus = (
        CapabilityValidationStatus.UNVALIDATED
    )
    lifecycle_fit: tuple[str, ...] = ()
    workstream_fit: tuple[str, ...] = ()
    product_workflow_fit: tuple[str, ...] = ()
    contract: CapabilityContract = Field(default_factory=CapabilityContract)
    provenance_note: str = "Discovered from local skill metadata."


class CapabilityCatalog(BaseModel):
    entries: tuple[CapabilityCatalogEntry, ...]
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    read_only: bool = True
    canonical_locations: tuple[str, ...] = CANONICAL_CAPABILITY_LOCATIONS


class CapabilityDependencyGate(BaseModel):
    capability_id: str
    capability_status: CapabilityStatus
    executable: bool
    blocked_reason: str
    missing_dependencies: tuple[str, ...]
    decomposition_options: tuple[str, ...]
    next_enabling_action: str | None = None
    review_destination: str
    trusted_downstream_writes: bool = False


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
        capability_status=CapabilityStatus(
            frontmatter.get("capability_status", CapabilityStatus.RUNNABLE.value)
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
        contract=CapabilityContract(
            persona_fit=_csv_values(frontmatter.get("persona_fit", "")),
            source_family=_optional_value(frontmatter.get("source_family", "")),
            input_expectations=_csv_values(frontmatter.get("input_expectations", "")),
            output_summary_shape=frontmatter.get(
                "output_summary_shape",
                CapabilityContract.model_fields["output_summary_shape"].default,
            ),
            quality_gate=frontmatter.get(
                "quality_gate",
                CapabilityContract.model_fields["quality_gate"].default,
            ),
            review_destination=frontmatter.get(
                "review_destination",
                CapabilityContract.model_fields["review_destination"].default,
            ),
            autonomy_tier=CapabilityAutonomyTier(
                frontmatter.get(
                    "autonomy_tier",
                    CapabilityAutonomyTier.HUMAN_APPROVAL_REQUIRED.value,
                )
            ),
            model_role=CapabilityModelRole(
                frontmatter.get("model_role", CapabilityModelRole.NONE.value)
            ),
            fake_runner_supported=_bool_value(
                frontmatter.get("fake_runner_supported", "false")
            ),
            missing_dependencies=_csv_values(
                frontmatter.get("missing_dependencies", "")
            ),
            decomposition_options=_csv_values(
                frontmatter.get("decomposition_options", "")
            ),
            product_workflow_destination=_optional_value(
                frontmatter.get("product_workflow_destination", "")
            ),
            next_enabling_action=_optional_value(
                frontmatter.get("next_enabling_action", "")
            ),
            provenance_requirements=_csv_values(
                frontmatter.get(
                    "provenance_requirements",
                    "capability_id, source_path, input_refs",
                )
            ),
        ),
    )


def dependency_gate_for_catalog_entry(
    entry: CapabilityCatalogEntry,
) -> CapabilityDependencyGate:
    if entry.capability_status is not CapabilityStatus.DEPENDENCY_GATED:
        return CapabilityDependencyGate(
            capability_id=entry.id,
            capability_status=entry.capability_status,
            executable=True,
            blocked_reason="Capability is not dependency-gated.",
            missing_dependencies=(),
            decomposition_options=entry.contract.decomposition_options,
            next_enabling_action=entry.contract.next_enabling_action,
            review_destination=entry.contract.review_destination,
        )
    return CapabilityDependencyGate(
        capability_id=entry.id,
        capability_status=entry.capability_status,
        executable=False,
        blocked_reason="Dependency-gated capability candidate cannot execute until prerequisites are satisfied.",
        missing_dependencies=entry.contract.missing_dependencies,
        decomposition_options=entry.contract.decomposition_options,
        next_enabling_action=entry.contract.next_enabling_action,
        review_destination=entry.contract.review_destination,
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


def _optional_value(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def _bool_value(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
