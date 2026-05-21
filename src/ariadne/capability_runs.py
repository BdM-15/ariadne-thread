from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.capabilities import CapabilityCatalogEntry, discover_local_capability_catalog
from ariadne.config import HostedModelSettings, LocalAdminModelSettings
from ariadne.hosted_model import (
    HostedModelAssistStatus,
    HostedModelClient,
    HostedModelPurpose,
    request_hosted_model_assist,
)
from ariadne.local_admin_model import (
    LocalAdminModelAssistStatus,
    LocalAdminModelClient,
    request_local_admin_draft_assist,
)


class CapabilityRunCapabilityType(StrEnum):
    SKILL = "skill"
    SKILL_CHAIN = "skill_chain"
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


class CapabilityReasoningView(BaseModel):
    run_id: str
    output_id: str
    title: str
    capability_id: str
    executor_kind: CapabilityRunExecutorKind
    input_summary: str
    input_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    tool_names: tuple[str, ...] = ()
    model_name: str | None = None
    model_status: str | None = None
    assumptions: tuple[str, ...] = ()
    validation_logic: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    recommended_destination: str | None = None
    autonomy_recommendation: CapabilityRunAutonomyRecommendation
    review_decision_history: tuple[str, ...] = ()


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


def run_local_admin_model_readiness_probe(
    *,
    settings: LocalAdminModelSettings,
    store: CapabilityRunStore,
    client: LocalAdminModelClient | None = None,
) -> CapabilityRun:
    assist = request_local_admin_draft_assist(
        "Capability Run readiness probe. Return one confidence note if available.",
        settings=settings,
        client=client,
    )
    completed_at = datetime.now(UTC)
    run = CapabilityRun(
        run_id=f"caprun_{uuid4().hex}",
        capability_id="local_admin_model_readiness_probe",
        capability_type=CapabilityRunCapabilityType.MODEL_WORKFLOW,
        executor_kind=CapabilityRunExecutorKind.LOCAL_ADMIN_MODEL,
        product_workflow="capability_catalog",
        status=(
            CapabilityRunStatus.NEEDS_REVIEW
            if assist.status is LocalAdminModelAssistStatus.USED
            else CapabilityRunStatus.UNAVAILABLE
        ),
        inputs_summary=(
            "Checked optional Local Admin Model readiness through existing Ollama "
            "configuration."
        ),
        outputs=(_local_admin_model_probe_output(assist, settings),),
        provenance={
            "sources": ["LOCAL_ADMIN_MODEL_ENABLED", "OLLAMA_HOST", "LOCAL_DAILY_MODEL"],
            "tool_names": ["request_local_admin_draft_assist"],
            "executor": CapabilityRunExecutorKind.LOCAL_ADMIN_MODEL.value,
            "source_mode": "local_admin_model_probe",
            "model_name": settings.model,
            "model_status": assist.status.value,
            "ollama_base_url": settings.ollama_base_url,
            "timeout_seconds": settings.timeout_seconds,
            "used": assist.used,
            "checked_at": completed_at.isoformat(),
        },
        completed_at=completed_at,
    )
    return store.write(run)


def run_hosted_model_readiness_probe(
    *,
    settings: HostedModelSettings,
    store: CapabilityRunStore,
    client: HostedModelClient | None = None,
) -> CapabilityRun:
    assist = request_hosted_model_assist(
        "Capability Run readiness probe. Return one concise confidence note.",
        purpose=HostedModelPurpose.OUTPUT_REVIEW_SUMMARY,
        settings=settings,
        client=client,
    )
    completed_at = datetime.now(UTC)
    run = CapabilityRun(
        run_id=f"caprun_{uuid4().hex}",
        capability_id="hosted_reasoning_model_readiness_probe",
        capability_type=CapabilityRunCapabilityType.MODEL_WORKFLOW,
        executor_kind=CapabilityRunExecutorKind.HOSTED_MODEL,
        product_workflow="capability_catalog",
        status=(
            CapabilityRunStatus.NEEDS_REVIEW
            if assist.status is HostedModelAssistStatus.USED
            else CapabilityRunStatus.UNAVAILABLE
        ),
        inputs_summary=(
            "Checked optional hosted reasoning model readiness through explicit "
            "operator-enabled configuration."
        ),
        outputs=(_hosted_model_probe_output(assist, settings),),
        provenance={
            "sources": [
                "HOSTED_REASONING_MODEL_ENABLED",
                "DEFAULT_LLM_PROVIDER",
                "REASONING_LLM_MODEL",
                "DAILY_LLM_MODEL",
            ],
            "tool_names": ["request_hosted_model_assist"],
            "executor": CapabilityRunExecutorKind.HOSTED_MODEL.value,
            "source_mode": "hosted_model_probe",
            "provider": assist.provider,
            "model_name": assist.model,
            "model_status": assist.status.value,
            "purpose": assist.purpose.value,
            "timeout_seconds": settings.timeout_seconds,
            "used": assist.used,
            "checked_at": completed_at.isoformat(),
            "network_required": bool(settings.enabled),
            "model_required": True,
            "trusted_downstream_writes": False,
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


def _local_admin_model_probe_output(
    assist,
    settings: LocalAdminModelSettings,
) -> CapabilityRunOutput:
    status = assist.status.value
    gaps = _local_admin_model_probe_gaps(assist.status, assist.reason)
    return CapabilityRunOutput(
        output_id=f"local_admin_model_probe_{status}",
        output_type="local_admin_model_readiness",
        title=f"Local Admin Model readiness: {status}",
        summary=_local_admin_model_probe_summary(status, assist.reason),
        gaps=gaps,
        recommended_destination="Capability Studio",
        provenance={
            "source_mode": "local_admin_model_probe",
            "model_name": settings.model,
            "ollama_base_url": settings.ollama_base_url,
            "timeout_seconds": settings.timeout_seconds,
            "model_status": status,
            "used": assist.used,
            "response_shape_valid": assist.status is LocalAdminModelAssistStatus.USED,
            "ollama_required": False,
            "reason": assist.reason,
        },
    )


def _hosted_model_probe_output(
    assist,
    settings: HostedModelSettings,
) -> CapabilityRunOutput:
    status = assist.status.value
    gaps = _hosted_model_probe_gaps(assist.status, assist.reason)
    return CapabilityRunOutput(
        output_id=f"hosted_model_probe_{status}",
        output_type="hosted_model_readiness",
        title=f"Hosted Reasoning Model readiness: {status}",
        summary=_hosted_model_probe_summary(status, assist.reason),
        gaps=gaps,
        recommended_destination="Capability Studio",
        provenance={
            "source_mode": "hosted_model_probe",
            "provider": assist.provider,
            "model_name": assist.model,
            "purpose": assist.purpose.value,
            "timeout_seconds": settings.timeout_seconds,
            "temperature": settings.temperature,
            "max_output_tokens": settings.max_output_tokens,
            "model_status": status,
            "used": assist.used,
            "response_shape_valid": assist.status is HostedModelAssistStatus.USED,
            "operator_enabled": settings.enabled,
            "reason": assist.reason,
            "trusted_downstream_writes": False,
        },
    )


def _hosted_model_probe_summary(status: str, reason: str) -> str:
    if status == HostedModelAssistStatus.USED.value:
        return "Hosted Reasoning Model returned reviewable draft support."
    if status == HostedModelAssistStatus.DISABLED.value:
        return "Hosted Reasoning Model is configured but disabled for safe local use."
    if status == HostedModelAssistStatus.MISSING_CREDENTIALS.value:
        return "Hosted Reasoning Model enabled but provider credentials are missing."
    return f"Hosted Reasoning Model is not ready: {reason}"


def _hosted_model_probe_gaps(
    status: HostedModelAssistStatus,
    reason: str,
) -> tuple[str, ...]:
    if status is HostedModelAssistStatus.USED:
        return ()
    if status is HostedModelAssistStatus.DISABLED:
        return ("Enable HOSTED_REASONING_MODEL_ENABLED before live hosted model runs.",)
    if status is HostedModelAssistStatus.MISSING_CREDENTIALS:
        return ("Add the provider API key to private .env before hosted model use.",)
    if status is HostedModelAssistStatus.INVALID_RESPONSE:
        return (f"Hosted Reasoning Model returned invalid response: {reason}",)
    return (f"Hosted Reasoning Model unavailable: {reason}",)


def _local_admin_model_probe_gaps(
    status: LocalAdminModelAssistStatus,
    reason: str,
) -> tuple[str, ...]:
    if status is LocalAdminModelAssistStatus.USED:
        return ()
    if status is LocalAdminModelAssistStatus.DISABLED:
        return ("Local Admin Model is disabled in runtime configuration.",)
    if status is LocalAdminModelAssistStatus.INVALID_RESPONSE:
        return (f"Local Admin Model returned invalid JSON or schema: {reason}",)
    return (f"Local Admin Model unavailable: {reason}",)


def _local_admin_model_probe_summary(status: str, reason: str) -> str:
    if status == LocalAdminModelAssistStatus.USED.value:
        return "Local Admin Model returned valid low-risk readiness support."
    return f"Local Admin Model probe completed with {status}: {reason}"


def build_capability_reasoning_view(
    run: CapabilityRun,
    *,
    output_id: str | None = None,
) -> CapabilityReasoningView:
    output = _select_reasoning_output(run, output_id)
    return CapabilityReasoningView(
        run_id=run.run_id,
        output_id=output.output_id,
        title=output.title,
        capability_id=run.capability_id,
        executor_kind=run.executor_kind,
        input_summary=run.inputs_summary,
        input_refs=run.input_refs,
        source_refs=_string_tuple(run.provenance.get("sources", ())),
        tool_names=_string_tuple(run.provenance.get("tool_names", ())),
        model_name=_optional_string(run.provenance.get("model_name")),
        model_status=_optional_string(run.provenance.get("model_status")),
        assumptions=_string_tuple(output.provenance.get("assumptions", ())),
        validation_logic=_validation_logic_for_output(output),
        gaps=output.gaps,
        limitations=_limitations_for_run(run, output),
        recommended_destination=output.recommended_destination,
        autonomy_recommendation=output.autonomy_recommendation,
        review_decision_history=tuple(
            _review_decision_summary(decision)
            for decision in output.review_decisions
        ),
    )


def _review_state_for_decision(
    decision: CapabilityRunReviewDecisionType,
) -> CapabilityRunOutputReviewState:
    if decision is CapabilityRunReviewDecisionType.ACCEPT:
        return CapabilityRunOutputReviewState.ACCEPTED
    if decision is CapabilityRunReviewDecisionType.DISCARD:
        return CapabilityRunOutputReviewState.DISCARDED
    return CapabilityRunOutputReviewState.ROUTED


def _select_reasoning_output(
    run: CapabilityRun,
    output_id: str | None,
) -> CapabilityRunOutput:
    if not run.outputs:
        raise ValueError("Capability Run has no outputs")
    if output_id is None:
        return run.outputs[0]
    for output in run.outputs:
        if output.output_id == output_id:
            return output
    raise ValueError("Capability Run Output not found")


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple | list):
        return tuple(str(item) for item in value)
    if value is None:
        return ()
    return (str(value),)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _validation_logic_for_output(
    output: CapabilityRunOutput,
) -> tuple[str, ...]:
    if output.output_type.startswith("capability_catalog_validation"):
        return (
            "Deterministic Capability Catalog validation inspected local skill metadata.",
            "No model, network call, external API, or agent runtime was required.",
        )
    return ("Capability Run Output preserved its executor provenance for review.",)


def _limitations_for_run(
    run: CapabilityRun,
    output: CapabilityRunOutput,
) -> tuple[str, ...]:
    limitations: list[str] = []
    if run.status in {CapabilityRunStatus.FAILED, CapabilityRunStatus.UNAVAILABLE}:
        limitations.append(f"Run status is {run.status.value}.")
    if output.review_state is CapabilityRunOutputReviewState.PENDING:
        limitations.append("Output still needs human review before trusted use.")
    if output.gaps:
        limitations.append("Validation gaps remain unresolved.")
    return tuple(limitations)


def _review_decision_summary(decision: CapabilityRunReviewDecision) -> str:
    destination = (
        f" -> {decision.routed_destination}" if decision.routed_destination else ""
    )
    rationale = (
        f": {decision.reviewer_rationale}" if decision.reviewer_rationale else ""
    )
    return f"{decision.decision.value}{destination}{rationale}"


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