from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json

from pydantic import BaseModel

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
from ariadne.data_table_profiler import DataTableAnomaly, DataTableProfile


class AnomalyRouteRecommendationRequest(BaseModel):
    data_table_profile: DataTableProfile
    opportunity_id: str | None = None
    source_output_id: str | None = None
    approval_basis: str = "reviewed_data_table_profile"


class AnomalyRouteRecommendation(BaseModel):
    source_profile_ref: str
    source_output_id: str | None
    route_id: str
    label: str
    rationale: str
    priority: str
    review_destination: str = "Action Plan recommendation"
    anomalies: tuple[DataTableAnomaly, ...]
    source_refs: tuple[str, ...]
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]
    approval_basis: str
    review_state: str = "pending_review"
    trusted_downstream_writes: bool = False


def build_anomaly_route_recommendation(
    request: AnomalyRouteRecommendationRequest,
) -> AnomalyRouteRecommendation:
    profile = request.data_table_profile
    route_id, label, rationale, priority = _route_choice(profile)
    return AnomalyRouteRecommendation(
        source_profile_ref=profile.source_ref,
        source_output_id=request.source_output_id,
        route_id=route_id,
        label=label,
        rationale=rationale,
        priority=priority,
        anomalies=profile.anomalies,
        source_refs=profile.source_refs,
        assumptions=(
            "Route recommendation is derived only from the reviewed data-table profile.",
            "A reviewer must accept or route this output before creating an Action Plan item.",
            "No live model, network, source collection, or trusted write was used.",
        ),
        gaps=_recommendation_gaps(profile),
        approval_basis=request.approval_basis,
    )


def run_anomaly_route_recommender_capability(
    *,
    request: AnomalyRouteRecommendationRequest,
    store: CapabilityRunStore,
    product_workflow: str = "action_plan",
) -> CapabilityRun:
    recommendation = build_anomaly_route_recommendation(request)
    completed_at = datetime.now(UTC)
    digest = _request_digest(request)
    output = CapabilityRunOutput(
        output_id=f"output_anomaly_route_recommendation_{digest}",
        output_type="anomaly_route_recommendation",
        title=f"Anomaly route recommendation: {request.data_table_profile.table_label}",
        summary=(
            f"{recommendation.priority} priority route {recommendation.route_id}; "
            f"{len(recommendation.anomalies)} anomaly signal(s) require review."
        ),
        gaps=recommendation.gaps,
        review_state=CapabilityRunOutputReviewState.PENDING,
        autonomy_recommendation=CapabilityRunAutonomyRecommendation.REVIEW_REQUIRED,
        recommended_destination=recommendation.review_destination,
        provenance={
            "capability_id": "anomaly-route-recommender",
            "anomaly_route_recommendation": recommendation.model_dump(mode="json"),
            "source_profile_ref": recommendation.source_profile_ref,
            "source_output_id": recommendation.source_output_id,
            "source_refs": list(recommendation.source_refs),
            "review_gate_required": True,
            "trusted_downstream_writes": False,
        },
    )
    run = CapabilityRun(
        run_id=f"caprun_anomaly_route_recommendation_{digest}",
        capability_id="anomaly-route-recommender",
        capability_type=CapabilityRunCapabilityType.SKILL,
        executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
        session_context=CapabilityRunSessionContext.PRODUCT,
        opportunity_id=request.opportunity_id,
        product_workflow=product_workflow,
        status=CapabilityRunStatus.NEEDS_REVIEW,
        inputs_summary=(
            f"Recommended a review route from data-table profile {recommendation.source_profile_ref}."
        ),
        input_refs=_input_refs(request),
        outputs=(output,),
        provenance={
            "capability_id": "anomaly-route-recommender",
            "executor": CapabilityRunExecutorKind.DETERMINISTIC_PYTHON.value,
            "source_profile_ref": recommendation.source_profile_ref,
            "source_output_id": recommendation.source_output_id,
            "source_refs": list(recommendation.source_refs),
            "route_id": recommendation.route_id,
            "priority": recommendation.priority,
            "network_required": False,
            "model_required": False,
            "trusted_downstream_writes": False,
            "completed_at": completed_at.isoformat(),
        },
        completed_at=completed_at,
    )
    return store.write(run)


def _route_choice(profile: DataTableProfile) -> tuple[str, str, str, str]:
    if not profile.anomalies:
        return (
            "review_profile_for_downstream_use",
            "Review profile before downstream use",
            "No anomaly signals were found, but profile use still requires human review.",
            "low",
        )
    if any(anomaly.severity == "high" for anomaly in profile.anomalies):
        return (
            "create_data_quality_action_before_packet_use",
            "Create data-quality action before packet use",
            "High-severity table anomalies can distort packet, workload, or research decisions.",
            "high",
        )
    return (
        "review_table_anomalies_before_route_use",
        "Review table anomalies before route use",
        "Medium-severity anomalies need review before Ariadne routes the table downstream.",
        "medium",
    )


def _recommendation_gaps(profile: DataTableProfile) -> tuple[str, ...]:
    gaps = list(profile.gaps)
    if profile.anomalies:
        gaps.append("Reviewer must decide whether anomalies block packet, research, or action use.")
    else:
        gaps.append("Reviewer must confirm profile is adequate before downstream use.")
    return tuple(dict.fromkeys(gaps))


def _input_refs(request: AnomalyRouteRecommendationRequest) -> tuple[str, ...]:
    refs = list(request.data_table_profile.source_refs)
    if request.source_output_id:
        refs.append(request.source_output_id)
    return tuple(dict.fromkeys(refs))


def _request_digest(request: AnomalyRouteRecommendationRequest) -> str:
    payload = {
        "profile": request.data_table_profile.model_dump(mode="json"),
        "opportunity_id": request.opportunity_id,
        "source_output_id": request.source_output_id,
        "approval_basis": request.approval_basis,
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]