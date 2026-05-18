from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.capabilities import CapabilityCatalogEntry, discover_local_capability_catalog


class CapabilityRunCapabilityType(StrEnum):
    SKILL = "skill"
    CLI_HARNESS = "cli_harness"
    MCP_TOOL = "mcp_tool"
    PARSER = "parser"
    RENDERER = "renderer"
    MODEL_WORKFLOW = "model_workflow"
    ADAPTER = "adapter"
    MANUAL_RECORD = "manual_record"


class CapabilityRunExecutorKind(StrEnum):
    DETERMINISTIC_PYTHON = "deterministic_python"
    CLI_ANYTHING = "cli_anything"
    LOCAL_ADMIN_MODEL = "local_admin_model"
    MCP = "mcp"
    HOSTED_MODEL = "hosted_model"
    FUTURE_AGENT_RUNTIME = "future_agent_runtime"


class CapabilityRunSessionContext(StrEnum):
    PRODUCT = "product"
    STUDIO = "studio"
    EXPLORATORY = "exploratory"


class CapabilityRunStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    CANCELED = "canceled"
    NEEDS_REVIEW = "needs_review"


class CapabilityRunOutputReviewState(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REFINED = "refined"
    DISCARDED = "discarded"
    ROUTED = "routed"
    PROMOTED = "promoted"


class CapabilityRunReviewDecisionType(StrEnum):
    ACCEPT = "accept"
    DISCARD = "discard"
    ROUTE = "route"


class CapabilityRunAutonomyRecommendation(StrEnum):
    REVIEW_REQUIRED = "review_required"
    ASK_BEFORE_RUNNING = "ask_before_running"
    SAFE_TO_AUTO_HANDLE_LATER = "safe_to_auto_handle_later"


class CapabilityRunReviewDecision(BaseModel):
    decision_id: str
    output_id: str
    decision: CapabilityRunReviewDecisionType
    reviewer_rationale: str = ""
    routed_destination: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CapabilityRunOutput(BaseModel):
    output_id: str
    output_type: str
    title: str
    summary: str
    gaps: tuple[str, ...] = ()
    review_state: CapabilityRunOutputReviewState = CapabilityRunOutputReviewState.PENDING
    autonomy_recommendation: CapabilityRunAutonomyRecommendation = (
        CapabilityRunAutonomyRecommendation.REVIEW_REQUIRED
    )
    recommended_destination: str | None = None
    review_decisions: tuple[CapabilityRunReviewDecision, ...] = ()
    provenance: dict[str, object] = Field(default_factory=dict)


class CapabilityRun(BaseModel):
    run_id: str
    capability_id: str
    capability_type: CapabilityRunCapabilityType
    executor_kind: CapabilityRunExecutorKind
    session_context: CapabilityRunSessionContext = CapabilityRunSessionContext.STUDIO
    opportunity_id: str | None = None
    product_workflow: str
    status: CapabilityRunStatus
    inputs_summary: str
    input_refs: tuple[str, ...] = ()
    outputs: tuple[CapabilityRunOutput, ...] = ()
    provenance: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class CapabilityRunStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, run: CapabilityRun) -> CapabilityRun:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(run.run_id).write_text(
            run.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return run

    def read(self, run_id: str) -> CapabilityRun:
        return CapabilityRun.model_validate_json(
            self._path(run_id).read_text(encoding="utf-8")
        )

    def list(self) -> list[CapabilityRun]:
        if not self.root.exists():
            return []
        return [
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        ]

    def _path(self, run_id: str) -> Path:
        if not run_id or run_id != Path(run_id).name:
            raise ValueError("run_id must be a file-safe identifier")
        return self.root / f"{run_id}.json"


def run_capability_catalog_validation(
    *,
    workspace_root: Path,
    store: CapabilityRunStore,
) -> CapabilityRun:
    catalog = discover_local_capability_catalog(workspace_root)
    outputs = tuple(
        _catalog_entry_validation_output(entry)
        for entry in catalog.entries
        if _catalog_entry_gaps(entry)
    )
    if not outputs:
        outputs = (_catalog_summary_output(len(catalog.entries)),)

    completed_at = datetime.now(UTC)
    run = CapabilityRun(
        run_id=f"caprun_{uuid4().hex}",
        capability_id="capability_catalog_validation",
        capability_type=CapabilityRunCapabilityType.ADAPTER,
        executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
        product_workflow="capability_catalog",
        status=CapabilityRunStatus.NEEDS_REVIEW,
        inputs_summary=(
            "Validated local Capability Catalog entries from canonical workspace skill "
            "locations."
        ),
        input_refs=tuple(catalog.canonical_locations),
        outputs=outputs,
        provenance={
            "sources": list(catalog.canonical_locations),
            "tool_names": ["discover_local_capability_catalog"],
            "executor": CapabilityRunExecutorKind.DETERMINISTIC_PYTHON.value,
            "catalog_indexed_at": catalog.indexed_at.isoformat(),
            "validated_at": completed_at.isoformat(),
            "entry_count": len(catalog.entries),
            "network_required": False,
            "model_required": False,
        },
        completed_at=completed_at,
    )
    return store.write(run)


def record_capability_run_output_review(
    *,
    store: CapabilityRunStore,
    run_id: str,
    output_id: str,
    decision: CapabilityRunReviewDecisionType,
    reviewer_rationale: str = "",
    routed_destination: str | None = None,
) -> CapabilityRun:
    run = store.read(run_id)
    updated_outputs: list[CapabilityRunOutput] = []
    matched_output = False
    if decision is CapabilityRunReviewDecisionType.ROUTE and not routed_destination:
        raise ValueError("routed review requires routed_destination")
    for output in run.outputs:
        if output.output_id != output_id:
            updated_outputs.append(output)
            continue
        matched_output = True
        if output.review_state is not CapabilityRunOutputReviewState.PENDING:
            raise ValueError("Capability Run Output already reviewed")
        review_decision = CapabilityRunReviewDecision(
            decision_id=f"capreview_{uuid4().hex}",
            output_id=output_id,
            decision=decision,
            reviewer_rationale=reviewer_rationale,
            routed_destination=routed_destination,
        )
        updated_outputs.append(
            output.model_copy(
                update={
                    "review_state": _review_state_for_decision(decision),
                    "review_decisions": output.review_decisions + (review_decision,),
                }
            )
        )
    if not matched_output:
        raise ValueError("Capability Run Output not found")

    reviewed_at = datetime.now(UTC)
    review_summary = {
        "output_id": output_id,
        "decision": decision.value,
        "reviewed_at": reviewed_at.isoformat(),
    }
    updated_run = run.model_copy(
        update={
            "outputs": tuple(updated_outputs),
            "provenance": {
                **run.provenance,
                "review_decisions": [
                    *run.provenance.get("review_decisions", []),
                    review_summary,
                ],
            },
        }
    )
    return store.write(updated_run)


def _review_state_for_decision(
    decision: CapabilityRunReviewDecisionType,
) -> CapabilityRunOutputReviewState:
    if decision is CapabilityRunReviewDecisionType.ACCEPT:
        return CapabilityRunOutputReviewState.ACCEPTED
    if decision is CapabilityRunReviewDecisionType.DISCARD:
        return CapabilityRunOutputReviewState.DISCARDED
    return CapabilityRunOutputReviewState.ROUTED


def _catalog_entry_validation_output(
    entry: CapabilityCatalogEntry,
) -> CapabilityRunOutput:
    gaps = _catalog_entry_gaps(entry)
    return CapabilityRunOutput(
        output_id=f"catalog_gap_{entry.id}",
        output_type="capability_catalog_validation_finding",
        title=f"Capability metadata gap: {entry.name}",
        summary=(
            f"Capability `{entry.id}` needs review before Ariadne treats its "
            "catalog metadata as validation-ready."
        ),
        gaps=gaps,
        recommended_destination="Improvement Proposal",
        provenance={
            "capability_id": entry.id,
            "source_path": entry.source_path,
            "capability_type": entry.capability_type.value,
            "maturity": entry.maturity.value,
            "validation_status": entry.validation_status.value,
        },
    )


def _catalog_summary_output(entry_count: int) -> CapabilityRunOutput:
    return CapabilityRunOutput(
        output_id="catalog_validation_summary",
        output_type="capability_catalog_validation_summary",
        title="Capability Catalog validation completed",
        summary=(
            f"Validated {entry_count} local Capability Catalog entries with no "
            "required metadata gaps found."
        ),
        recommended_destination="Capability Studio",
        provenance={"entry_count": entry_count},
    )


def _catalog_entry_gaps(entry: CapabilityCatalogEntry) -> tuple[str, ...]:
    gaps: list[str] = []
    if not entry.description.strip():
        gaps.append("Missing capability description metadata.")
    if not entry.source_path.strip():
        gaps.append("Missing source path.")
    if entry.validation_status.value == "unvalidated":
        gaps.append("Capability validation status is still unvalidated.")
    return tuple(gaps)