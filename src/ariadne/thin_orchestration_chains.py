from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any

from pydantic import BaseModel, Field

from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunAutonomyRecommendation,
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutput,
    CapabilityRunOutputReviewState,
    CapabilityRunSessionContext,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.data_table_profiler import (
    DataTableProfileRequest,
    run_data_table_profile_capability,
)
from ariadne.skill_chain_plan_maps import (
    SkillChainPlanMap,
    SkillChainPlanStage,
    build_skill_chain_plan_from_capture_goal,
)


class ThinOrchestrationStageRecord(BaseModel):
    stage_id: str
    title: str
    capability_id: str
    status: str
    input_refs: tuple[str, ...]
    produced_handoff: str
    quality_gate_result: str
    review_destination: str
    assumptions: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    provenance: dict[str, Any] = Field(default_factory=dict)


class ThinOrchestrationChainRecord(BaseModel):
    chain_id: str
    status: str
    approval_status: str
    approval_basis: str
    plan: SkillChainPlanMap
    stage_records: tuple[ThinOrchestrationStageRecord, ...]
    output_summary: str
    review_destination: str = "Capability Run Output"
    execution_mode: str = "deterministic_plan_map"
    langgraph_runtime_used: bool = False
    network_required: bool = False
    model_required: bool = False
    broad_hermes_autonomy_used: bool = False
    trusted_downstream_writes: bool = False
    provenance: dict[str, Any] = Field(default_factory=dict)


def plan_data_table_profile_next_route_chain(
    request: DataTableProfileRequest,
    *,
    opportunity_id: str | None = None,
) -> ThinOrchestrationChainRecord:
    digest = _request_digest(
        request=request,
        opportunity_id=opportunity_id,
        approval_basis="planned",
    )
    plan = build_skill_chain_plan_from_capture_goal(
        capture_goal="data table profile -> next route",
        available_inputs=("table_source_ref", "table_rows"),
    )
    return ThinOrchestrationChainRecord(
        chain_id=f"chain_data_table_profile_next_route_{digest}",
        status="planned",
        approval_status="not_approved",
        approval_basis="planned",
        plan=plan,
        stage_records=tuple(
            _planned_stage_record(stage, request)
            for stage in plan.stages
        ),
        output_summary="Thin chain planned; explicit approval required before execution.",
        provenance={
            "opportunity_id": opportunity_id,
            "source_ref": request.source_ref,
            "source_refs": list(_source_refs(request)),
            "planned_at": datetime.now(UTC).isoformat(),
        },
    )


def approve_thin_orchestration_chain(
    chain: ThinOrchestrationChainRecord,
    *,
    approval_basis: str,
) -> ThinOrchestrationChainRecord:
    return chain.model_copy(
        update={
            "status": "approved",
            "approval_status": "approved",
            "approval_basis": approval_basis,
            "stage_records": tuple(
                stage.model_copy(update={"status": "approved"})
                for stage in chain.stage_records
            ),
            "output_summary": "Thin chain approved; deterministic execution may start.",
            "provenance": {
                **chain.provenance,
                "approval_basis": approval_basis,
                "approved_at": datetime.now(UTC).isoformat(),
            },
        }
    )


def run_data_table_profile_next_route_chain(
    *,
    request: DataTableProfileRequest,
    store: CapabilityRunStore,
    opportunity_id: str | None = None,
    approval_basis: str,
) -> CapabilityRun:
    planned_chain = plan_data_table_profile_next_route_chain(
        request,
        opportunity_id=opportunity_id,
    )
    approved_chain = approve_thin_orchestration_chain(
        planned_chain,
        approval_basis=approval_basis,
    )
    return execute_data_table_profile_next_route_chain(
        approved_chain,
        request=request,
        store=store,
        opportunity_id=opportunity_id,
    )


def execute_data_table_profile_next_route_chain(
    chain: ThinOrchestrationChainRecord,
    *,
    request: DataTableProfileRequest,
    store: CapabilityRunStore,
    opportunity_id: str | None = None,
) -> CapabilityRun:
    if chain.approval_status != "approved":
        raise ValueError("thin orchestration chain requires approval before execution")

    profile_run = run_data_table_profile_capability(
        request=request,
        store=store,
        opportunity_id=opportunity_id,
        product_workflow="thin_orchestration_chain",
    )
    profile_output = profile_run.outputs[0]
    profile_payload = _dict_payload(profile_output.provenance["data_table_profile"])
    route_payload = _dict_payload(profile_payload["recommended_next_route"])
    stage_by_id = {stage.stage_id: stage for stage in chain.plan.stages}
    data_profile_stage = _data_profile_stage_record(
        stage=stage_by_id["stage_1_data_table_profiler"],
        profile_run=profile_run,
        profile_payload=profile_payload,
    )
    route_review_stage = _route_review_stage_record(
        stage=stage_by_id["stage_2_data_profile_route_review"],
        input_handoff=data_profile_stage.produced_handoff,
        profile_payload=profile_payload,
        route_payload=route_payload,
    )
    completed_chain = chain.model_copy(
        update={
            "status": "needs_review",
            "stage_records": (data_profile_stage, route_review_stage),
            "output_summary": _output_summary(route_payload, profile_payload),
            "provenance": {
                **chain.provenance,
                "executed_at": datetime.now(UTC).isoformat(),
                "stage_run_ids": [profile_run.run_id],
                "stage_output_ids": [profile_output.output_id],
            },
        }
    )
    return _write_chain_capability_run(
        chain=completed_chain,
        request=request,
        store=store,
        opportunity_id=opportunity_id,
    )


def _planned_stage_record(
    stage: SkillChainPlanStage,
    request: DataTableProfileRequest,
) -> ThinOrchestrationStageRecord:
    return ThinOrchestrationStageRecord(
        stage_id=stage.stage_id,
        title=stage.title,
        capability_id=stage.capability_id,
        status="planned",
        input_refs=_planned_input_refs(stage, request),
        produced_handoff="pending_execution",
        quality_gate_result="pending_execution",
        review_destination=stage.review_destination,
        assumptions=("Execution requires explicit operator approval.",),
        provenance={
            "depends_on": list(stage.depends_on),
            "input_expectations": list(stage.input_expectations),
            "produced_handoff_type": stage.produced_handoff_type,
            "quality_gate": stage.quality_gate,
        },
    )


def _planned_input_refs(
    stage: SkillChainPlanStage,
    request: DataTableProfileRequest,
) -> tuple[str, ...]:
    if "table_source_ref" in stage.input_expectations:
        return (request.source_ref,)
    return ()


def _data_profile_stage_record(
    *,
    stage: SkillChainPlanStage,
    profile_run: CapabilityRun,
    profile_payload: dict[str, Any],
) -> ThinOrchestrationStageRecord:
    output = profile_run.outputs[0]
    return ThinOrchestrationStageRecord(
        stage_id=stage.stage_id,
        title=stage.title,
        capability_id=stage.capability_id,
        status="needs_review",
        input_refs=profile_run.input_refs,
        produced_handoff=output.output_id,
        quality_gate_result="passed_pending_human_review",
        review_destination=stage.review_destination,
        assumptions=_string_tuple(profile_payload.get("assumptions", ())),
        gaps=_string_tuple(profile_payload.get("gaps", ())),
        provenance={
            "capability_run_id": profile_run.run_id,
            "capability_output_id": output.output_id,
            "review_state": output.review_state.value,
            "quality_gate": stage.quality_gate,
            "trusted_downstream_writes": False,
        },
    )


def _route_review_stage_record(
    *,
    stage: SkillChainPlanStage,
    input_handoff: str,
    profile_payload: dict[str, Any],
    route_payload: dict[str, Any],
) -> ThinOrchestrationStageRecord:
    return ThinOrchestrationStageRecord(
        stage_id=stage.stage_id,
        title=stage.title,
        capability_id=stage.capability_id,
        status="needs_review",
        input_refs=(input_handoff,),
        produced_handoff=f"data_profile_route_review:{route_payload['route_id']}",
        quality_gate_result="review_before_route_use_pending",
        review_destination=stage.review_destination,
        assumptions=(
            "Route recommendation is advisory until human review accepts it.",
            "No packet, research, or action record was written by this chain.",
        ),
        gaps=_string_tuple(profile_payload.get("gaps", ())),
        provenance={
            "route_id": route_payload["route_id"],
            "route_label": route_payload["label"],
            "route_rationale": route_payload["rationale"],
            "quality_gate": stage.quality_gate,
            "trusted_downstream_writes": False,
        },
    )


def _write_chain_capability_run(
    *,
    chain: ThinOrchestrationChainRecord,
    request: DataTableProfileRequest,
    store: CapabilityRunStore,
    opportunity_id: str | None,
) -> CapabilityRun:
    completed_at = datetime.now(UTC)
    digest = _request_digest(
        request=request,
        opportunity_id=opportunity_id,
        approval_basis=chain.approval_basis,
    )
    output = CapabilityRunOutput(
        output_id=f"output_chain_data_table_profile_next_route_{digest}",
        output_type="thin_orchestration_chain_summary",
        title="Data-table profile to next-route chain",
        summary=chain.output_summary,
        gaps=_unique_strings(
            gap
            for stage in chain.stage_records
            for gap in stage.gaps
        ),
        review_state=CapabilityRunOutputReviewState.PENDING,
        autonomy_recommendation=CapabilityRunAutonomyRecommendation.REVIEW_REQUIRED,
        recommended_destination=chain.review_destination,
        provenance={
            "thin_orchestration_chain": chain.model_dump(mode="json"),
            "review_gate_required": True,
            "trusted_downstream_writes": False,
        },
    )
    run = CapabilityRun(
        run_id=f"caprun_chain_data_table_profile_next_route_{digest}",
        capability_id="data-table-profile-next-route-chain",
        capability_type=CapabilityRunCapabilityType.SKILL_CHAIN,
        executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
        session_context=CapabilityRunSessionContext.PRODUCT,
        opportunity_id=opportunity_id,
        product_workflow="thin_orchestration_chain",
        status=CapabilityRunStatus.NEEDS_REVIEW,
        inputs_summary=(
            f"Ran approved data-table profile to next-route chain for {request.source_ref}."
        ),
        input_refs=_source_refs(request),
        outputs=(output,),
        provenance={
            "capability_id": "data-table-profile-next-route-chain",
            "executor": CapabilityRunExecutorKind.DETERMINISTIC_PYTHON.value,
            "execution_mode": chain.execution_mode,
            "approval_basis": chain.approval_basis,
            "stage_progression": [
                stage.model_dump(mode="json") for stage in chain.stage_records
            ],
            "source_refs": list(_source_refs(request)),
            "network_required": chain.network_required,
            "model_required": chain.model_required,
            "langgraph_runtime_used": chain.langgraph_runtime_used,
            "broad_hermes_autonomy_used": chain.broad_hermes_autonomy_used,
            "trusted_downstream_writes": chain.trusted_downstream_writes,
            "completed_at": completed_at.isoformat(),
        },
        completed_at=completed_at,
    )
    return store.write(run)


def _output_summary(
    route_payload: dict[str, Any],
    profile_payload: dict[str, Any],
) -> str:
    shape = _dict_payload(profile_payload["shape"])
    return (
        "Thin chain produced a reviewable next-route summary from "
        f"{shape['row_count']} row(s) and {shape['column_count']} column(s); "
        f"recommended route: {route_payload['label']}."
    )


def _source_refs(request: DataTableProfileRequest) -> tuple[str, ...]:
    return tuple(dict.fromkeys((request.source_ref, *request.source_refs)))


def _request_digest(
    *,
    request: DataTableProfileRequest,
    opportunity_id: str | None,
    approval_basis: str,
) -> str:
    payload = {
        "request": request.model_dump(mode="json"),
        "opportunity_id": opportunity_id,
        "approval_basis": approval_basis,
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _dict_payload(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("expected dictionary payload")
    return value


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple | list):
        return tuple(str(item) for item in value)
    if value is None:
        return ()
    return (str(value),)


def _unique_strings(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value).strip()))