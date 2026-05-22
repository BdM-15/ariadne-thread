from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunOutput,
    CapabilityRunStore,
)
from ariadne.focused_capture_skills import CompetitiveGapRouteHint
from ariadne.next_action_recommendations import (
    ActionCapabilityRoute,
    ActionCapabilityRouteSupport,
    NextActionRecommendation,
    NextActionRecommendationStore,
    RecommendationAutonomyHint,
    RecommendationContextSnapshot,
)
from ariadne.opportunities import MilestoneGate
from ariadne.opportunity_activation import (
    OpportunityActivationRun,
    OpportunityActivationRunStore,
    OpportunityActivationRunTrigger,
    run_opportunity_activation,
)
from ariadne.packet_knowledge import (
    PacketFieldAnswer,
    PacketFieldAnswerStatus,
    PacketFieldAnswerStore,
    build_default_packet_field_definitions,
    create_packet_field_answer,
)
from ariadne.packets import EvidenceStatus


class WorkProductDeltaDestination(StrEnum):
    LIVING_PACKET = "living_packet"
    ACTION_PLAN = "action_plan"
    CALL_PLAN = "call_plan"
    RISK_REGISTER = "risk_register"
    FOLLOW_UP_ROUTE = "follow_up_route"
    ARTIFACT_CONTEXT = "artifact_context"


class WorkProductDeltaReviewState(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    EDITED = "edited"
    DISCARDED = "discarded"
    ROUTED = "routed"


class WorkProductDeltaReviewDecisionType(StrEnum):
    ACCEPT = "accept"
    EDIT = "edit"
    DISCARD = "discard"
    ROUTE = "route"


class WorkProductDeltaReviewDecision(BaseModel):
    decision_id: str
    delta_id: str
    decision: WorkProductDeltaReviewDecisionType
    reviewer_rationale: str
    review_gate: str
    packet_field_answer_created: bool = False
    next_action_recommendation_created: bool = False
    routed_destination: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkProductDelta(BaseModel):
    id: str
    opportunity_id: str
    destination: WorkProductDeltaDestination
    title: str
    field_key: str | None = None
    source_capability_run_id: str
    source_output_id: str
    source_capability_id: str
    review_state: WorkProductDeltaReviewState = (
        WorkProductDeltaReviewState.PENDING_REVIEW
    )
    before_summary: str
    after_summary: str
    source_refs: tuple[str, ...] = ()
    capability_output_refs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    review_decisions: tuple[WorkProductDeltaReviewDecision, ...] = ()
    provenance: dict[str, object] = Field(default_factory=dict)


class WorkProductDeltaCreateFromCapabilityOutputRequest(BaseModel):
    opportunity_id: str
    capability_run_id: str
    output_id: str


class EngagementPrepSourcePreference(StrEnum):
    ACTION_PLAN_LINK = "action_plan_link"
    PACKET_GAP = "packet_gap"
    CUSTOMER_CALL_PLAN_FALLBACK = "customer_call_plan_fallback"


class EngagementPrepDeltaCreateRequest(BaseModel):
    opportunity_id: str
    source_preference: EngagementPrepSourcePreference | None = None


class WorkProductDeltaListResponse(BaseModel):
    deltas: tuple[WorkProductDelta, ...]
    summary: dict[str, int]


class WorkProductDeltaDetailResponse(BaseModel):
    delta: WorkProductDelta


class WorkProductDeltaReviewRequest(BaseModel):
    decision: WorkProductDeltaReviewDecisionType
    reviewer_rationale: str
    edited_value: str | None = None
    routed_destination: str | None = None


class WorkProductDeltaReviewResponse(BaseModel):
    delta: WorkProductDelta
    decision: WorkProductDeltaReviewDecision
    packet_field_answer: PacketFieldAnswer | None = None
    next_action_recommendation: NextActionRecommendation | None = None
    activation_run: OpportunityActivationRun | None = None


class WorkProductDeltaStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, delta: WorkProductDelta) -> WorkProductDelta:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(delta.id).write_text(
            delta.model_dump_json(indent=2), encoding="utf-8"
        )
        return delta

    def read(self, delta_id: str) -> WorkProductDelta:
        return WorkProductDelta.model_validate_json(
            self._path(delta_id).read_text(encoding="utf-8")
        )

    def list(
        self,
        *,
        opportunity_id: str | None = None,
        destination: WorkProductDeltaDestination | None = None,
        source_output_id: str | None = None,
    ) -> tuple[WorkProductDelta, ...]:
        if not self.root.exists():
            return ()
        deltas = tuple(
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        )
        if opportunity_id is not None:
            deltas = tuple(
                delta for delta in deltas if delta.opportunity_id == opportunity_id
            )
        if destination is not None:
            deltas = tuple(
                delta for delta in deltas if delta.destination is destination
            )
        if source_output_id is not None:
            deltas = tuple(
                delta for delta in deltas if delta.source_output_id == source_output_id
            )
        return deltas

    def _path(self, delta_id: str) -> Path:
        if not delta_id or delta_id != Path(delta_id).name:
            raise ValueError("delta_id must be a file-safe identifier")
        return self.root / f"{delta_id}.json"


def create_work_product_deltas_from_capability_output(
    *,
    capability_store: CapabilityRunStore,
    delta_store: WorkProductDeltaStore,
    request: WorkProductDeltaCreateFromCapabilityOutputRequest,
) -> WorkProductDeltaListResponse:
    run = capability_store.read(request.capability_run_id)
    output = _find_run_output(run, request.output_id)
    deltas = build_competitive_gap_work_product_deltas(
        run=run,
        output=output,
        opportunity_id=request.opportunity_id,
    )
    stored_deltas = tuple(delta_store.write(delta) for delta in deltas)
    return WorkProductDeltaListResponse(
        deltas=_ordered_deltas(stored_deltas),
        summary=_delta_summary(stored_deltas),
    )


def create_engagement_prep_work_product_delta(
    *,
    delta_store: WorkProductDeltaStore,
    activation_store: OpportunityActivationRunStore,
    recommendation_store: NextActionRecommendationStore,
    request: EngagementPrepDeltaCreateRequest,
) -> WorkProductDeltaListResponse:
    recommendation = _latest_linked_action_recommendation(
        recommendation_store=recommendation_store,
        opportunity_id=request.opportunity_id,
    )
    latest_activation = _latest_activation_run(
        activation_store=activation_store,
        opportunity_id=request.opportunity_id,
    )
    engagement_field = _engagement_field_from_activation(latest_activation)

    source_preference = request.source_preference
    source_mode: EngagementPrepSourcePreference
    if source_preference is EngagementPrepSourcePreference.ACTION_PLAN_LINK:
        if recommendation is None:
            raise ValueError("No linked Action Plan recommendation available")
        source_mode = EngagementPrepSourcePreference.ACTION_PLAN_LINK
    elif source_preference is EngagementPrepSourcePreference.PACKET_GAP:
        if engagement_field is None or latest_activation is None:
            raise ValueError("No packet-gap engagement context available")
        source_mode = EngagementPrepSourcePreference.PACKET_GAP
    elif source_preference is EngagementPrepSourcePreference.CUSTOMER_CALL_PLAN_FALLBACK:
        source_mode = EngagementPrepSourcePreference.CUSTOMER_CALL_PLAN_FALLBACK
    elif recommendation is not None:
        source_mode = EngagementPrepSourcePreference.ACTION_PLAN_LINK
    elif engagement_field is not None and latest_activation is not None:
        source_mode = EngagementPrepSourcePreference.PACKET_GAP
    else:
        source_mode = EngagementPrepSourcePreference.CUSTOMER_CALL_PLAN_FALLBACK

    if source_mode is EngagementPrepSourcePreference.ACTION_PLAN_LINK:
        engagement_delta = _engagement_delta_from_action_recommendation(
            recommendation=recommendation,
            opportunity_id=request.opportunity_id,
        )
    elif source_mode is EngagementPrepSourcePreference.PACKET_GAP:
        engagement_delta = _engagement_delta_from_packet_gap(
            run=latest_activation,
            field=engagement_field,
            opportunity_id=request.opportunity_id,
        )
    else:
        engagement_delta = _engagement_delta_from_fallback(
            opportunity_id=request.opportunity_id,
        )

    stored_delta = delta_store.write(engagement_delta)
    return WorkProductDeltaListResponse(
        deltas=_ordered_deltas((stored_delta,)),
        summary=_delta_summary((stored_delta,)),
    )


def list_work_product_deltas(
    *,
    store: WorkProductDeltaStore,
    opportunity_id: str | None = None,
    destination: WorkProductDeltaDestination | None = None,
) -> WorkProductDeltaListResponse:
    deltas = store.list(opportunity_id=opportunity_id, destination=destination)
    return WorkProductDeltaListResponse(
        deltas=_ordered_deltas(deltas),
        summary=_delta_summary(deltas),
    )


def get_work_product_delta(
    *,
    store: WorkProductDeltaStore,
    delta_id: str,
) -> WorkProductDeltaDetailResponse:
    return WorkProductDeltaDetailResponse(delta=store.read(delta_id))


def record_packet_work_product_delta_review(
    *,
    delta_store: WorkProductDeltaStore,
    answer_store: PacketFieldAnswerStore,
    activation_store: OpportunityActivationRunStore,
    recommendation_store: NextActionRecommendationStore,
    delta_id: str,
    request: WorkProductDeltaReviewRequest,
    current_milestone_gate: MilestoneGate = MilestoneGate.MILESTONE_3,
    vault_root: Path | str | None = None,
) -> WorkProductDeltaReviewResponse:
    delta = delta_store.read(delta_id)
    if delta.review_state is not WorkProductDeltaReviewState.PENDING_REVIEW:
        raise ValueError("Work Product Delta already reviewed")

    packet_field_answer: PacketFieldAnswer | None = None
    next_action_recommendation: NextActionRecommendation | None = None
    activation_run: OpportunityActivationRun | None = None
    routed_destination = _validated_routed_destination(request)
    accepted_value = _accepted_delta_value(delta=delta, request=request)
    if delta.destination is WorkProductDeltaDestination.LIVING_PACKET:
        if delta.field_key is None:
            raise ValueError("Packet delta is missing field_key")
        if accepted_value is not None:
            packet_field_answer = _packet_field_answer_from_delta_review(
                delta=delta,
                request=request,
                accepted_value=accepted_value,
            )
            answer_store.write(packet_field_answer)
            activation_run = run_opportunity_activation(
                opportunity_id=delta.opportunity_id,
                definitions=build_default_packet_field_definitions(),
                answers=answer_store.list(opportunity_id=delta.opportunity_id),
                trigger=OpportunityActivationRunTrigger.MATERIAL_REFRESH,
                store=activation_store,
                current_milestone_gate=current_milestone_gate,
                vault_root=vault_root,
            )
    elif delta.destination is WorkProductDeltaDestination.ACTION_PLAN:
        if accepted_value is not None:
            next_action_recommendation = _recommendation_from_action_plan_delta_review(
                delta=delta,
                request=request,
                accepted_summary=accepted_value,
            )
            recommendation_store.write(next_action_recommendation)
    elif delta.destination is WorkProductDeltaDestination.CALL_PLAN:
        # Engagement-prep acceptance is review-state only until explicit downstream action.
        pass
    else:
        raise ValueError(
            "Work Product Delta destination review is not supported yet"
        )

    decision = WorkProductDeltaReviewDecision(
        decision_id=f"wpdreview_{uuid4().hex}",
        delta_id=delta.id,
        decision=request.decision,
        reviewer_rationale=request.reviewer_rationale.strip(),
        review_gate=_review_gate_for_delta_decision(
            decision=request.decision,
            destination=delta.destination,
        ),
        packet_field_answer_created=packet_field_answer is not None,
        next_action_recommendation_created=next_action_recommendation is not None,
        routed_destination=routed_destination,
    )
    updated_delta = delta.model_copy(
        update={
            "review_state": _review_state_for_delta_decision(request.decision),
            "after_summary": accepted_value or delta.after_summary,
            "review_decisions": delta.review_decisions + (decision,),
        }
    )
    return WorkProductDeltaReviewResponse(
        delta=delta_store.write(updated_delta),
        decision=decision,
        packet_field_answer=packet_field_answer,
        next_action_recommendation=next_action_recommendation,
        activation_run=activation_run,
    )


def build_competitive_gap_work_product_deltas(
    *,
    run: CapabilityRun,
    output: CapabilityRunOutput,
    opportunity_id: str,
) -> tuple[WorkProductDelta, WorkProductDelta]:
    if run.capability_id != "competitive-gap-route-hint":
        raise ValueError("Capability Run is not a competitive-gap-route-hint run")
    if run.opportunity_id is not None and run.opportunity_id != opportunity_id:
        raise ValueError("Capability Run does not match the requested Opportunity")
    hint_payload = output.provenance.get("competitive_gap_route_hint")
    if hint_payload is None:
        raise ValueError(
            "Capability Run Output is missing competitive gap route hint provenance"
        )
    hint = CompetitiveGapRouteHint.model_validate(hint_payload)
    capability_output_ref = f"capability-run://{run.run_id}/outputs/{output.output_id}"
    shared = {
        "opportunity_id": opportunity_id,
        "field_key": hint.field_key,
        "source_capability_run_id": run.run_id,
        "source_output_id": output.output_id,
        "source_capability_id": run.capability_id,
        "source_refs": hint.source_refs,
        "capability_output_refs": (capability_output_ref,),
        "assumptions": hint.assumptions,
        "gaps": hint.gaps,
        "provenance": {
            "capability_id": run.capability_id,
            "capability_run_id": run.run_id,
            "capability_output_id": output.output_id,
            "capability_output_type": output.output_type,
            "recommended_route": hint.recommended_route,
            "rationale": hint.rationale,
            "review_destination": hint.review_destination,
            "source_output_review_state": output.review_state.value,
            "trusted_downstream_writes": False,
        },
    }
    return (
        WorkProductDelta(
            id=_delta_id(
                opportunity_id=opportunity_id,
                output_id=output.output_id,
                destination=WorkProductDeltaDestination.LIVING_PACKET,
            ),
            destination=WorkProductDeltaDestination.LIVING_PACKET,
            title="Living Packet competition update candidate",
            before_summary=(
                f"{_field_label(hint.field_key)} field remains unchanged until this "
                "Work Product Delta is reviewed."
            ),
            after_summary=hint.packet_implication,
            **shared,
        ),
        WorkProductDelta(
            id=_delta_id(
                opportunity_id=opportunity_id,
                output_id=output.output_id,
                destination=WorkProductDeltaDestination.ACTION_PLAN,
            ),
            destination=WorkProductDeltaDestination.ACTION_PLAN,
            title="Action Plan competitive proof-gap implication",
            before_summary=(
                "Action Plan has no reviewed proof-gap follow-up from this "
                "competitive gap route hint."
            ),
            after_summary=(
                "Review proof gaps and customer-validation follow-up before this "
                f"packet implication changes the Action Plan: {hint.recommended_route}"
            ),
            **shared,
        ),
    )


def _accepted_delta_value(
    *,
    delta: WorkProductDelta,
    request: WorkProductDeltaReviewRequest,
) -> str | None:
    if request.decision is WorkProductDeltaReviewDecisionType.ACCEPT:
        accepted_value = delta.after_summary.strip()
    elif request.decision is WorkProductDeltaReviewDecisionType.EDIT:
        accepted_value = request.edited_value.strip() if request.edited_value else ""
    else:
        return None
    if not accepted_value:
        raise ValueError("Accepted Work Product Delta review requires value")
    return accepted_value


def _validated_routed_destination(
    request: WorkProductDeltaReviewRequest,
) -> str | None:
    if request.decision is not WorkProductDeltaReviewDecisionType.ROUTE:
        return None
    if not request.routed_destination or not request.routed_destination.strip():
        raise ValueError("Routed Work Product Delta review requires destination")
    return request.routed_destination.strip()


def _packet_field_answer_from_delta_review(
    *,
    delta: WorkProductDelta,
    request: WorkProductDeltaReviewRequest,
    accepted_value: str,
) -> PacketFieldAnswer:
    evidence_status = EvidenceStatus.ASSUMPTION
    rationale = request.reviewer_rationale.strip()
    provenance_note = (
        "Accepted from Work Product Delta "
        f"{delta.id} / Capability Run Output {delta.source_output_id}: {rationale}"
        if rationale
        else (
            "Accepted from Work Product Delta "
            f"{delta.id} / Capability Run Output {delta.source_output_id}."
        )
    )
    return create_packet_field_answer(
        field_key=delta.field_key or "",
        opportunity_id=delta.opportunity_id,
        value=accepted_value,
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=evidence_status,
        evidence_ids=delta.source_refs,
        assumption="; ".join(delta.assumptions) if delta.assumptions else None,
        confidence=0.6,
        gap_summary="; ".join(delta.gaps) if delta.gaps else None,
        provenance_note=provenance_note,
        review_status=request.decision.value,
        source_draft_id=delta.id,
        review_edits=(
            f"source_capability_run_id: {delta.source_capability_run_id}",
            f"source_output_id: {delta.source_output_id}",
        ),
    )


def _review_state_for_delta_decision(
    decision: WorkProductDeltaReviewDecisionType,
) -> WorkProductDeltaReviewState:
    return {
        WorkProductDeltaReviewDecisionType.ACCEPT: WorkProductDeltaReviewState.ACCEPTED,
        WorkProductDeltaReviewDecisionType.EDIT: WorkProductDeltaReviewState.EDITED,
        WorkProductDeltaReviewDecisionType.DISCARD: WorkProductDeltaReviewState.DISCARDED,
        WorkProductDeltaReviewDecisionType.ROUTE: WorkProductDeltaReviewState.ROUTED,
    }[decision]


def _review_gate_for_delta_decision(
    *,
    decision: WorkProductDeltaReviewDecisionType,
    destination: WorkProductDeltaDestination,
) -> str:
    destination_prefix = {
        WorkProductDeltaDestination.LIVING_PACKET: "packet",
        WorkProductDeltaDestination.ACTION_PLAN: "action_plan",
        WorkProductDeltaDestination.CALL_PLAN: "call_plan",
    }.get(destination)
    if destination_prefix is None:
        return "work_product_delta_review"
    suffix = {
        WorkProductDeltaReviewDecisionType.ACCEPT: "acceptance",
        WorkProductDeltaReviewDecisionType.EDIT: "edit",
        WorkProductDeltaReviewDecisionType.DISCARD: "discard",
        WorkProductDeltaReviewDecisionType.ROUTE: "route",
    }[decision]
    return f"work_product_delta_{destination_prefix}_{suffix}"


def _recommendation_from_action_plan_delta_review(
    *,
    delta: WorkProductDelta,
    request: WorkProductDeltaReviewRequest,
    accepted_summary: str,
) -> NextActionRecommendation:
    generated_at = datetime.now(UTC).isoformat()
    cause = f"work_product_delta:{delta.id}"
    return NextActionRecommendation(
        id=_next_action_recommendation_id(delta),
        opportunity_id=delta.opportunity_id,
        title=delta.title,
        description=accepted_summary,
        cause=cause,
        rationale=request.reviewer_rationale.strip() or accepted_summary,
        capability_route=ActionCapabilityRoute(
            support=ActionCapabilityRouteSupport.PARTIAL_ASSISTANCE,
            next_command_id="review_action_plan_recommendation",
            next_command_label=(
                "Review recommendation and accept through Action Plan gate"
            ),
            capability_id=delta.source_capability_id,
            product_workflow="action_plan",
            rationale=(
                "Work Product Delta accepted for recommendation queue; trusted "
                "Action Plan write still requires recommendation acceptance."
            ),
        ),
        context_snapshot=RecommendationContextSnapshot(
            opportunity_id=delta.opportunity_id,
            trusted_refs=(),
            reviewable_refs=delta.source_refs + delta.capability_output_refs,
            gap_refs=delta.gaps,
            source_limitation_refs=delta.assumptions,
            recommendation_cause=cause,
            capability_route_id=delta.source_capability_id,
            autonomy_hint=RecommendationAutonomyHint.REQUIRES_USER_APPROVAL,
        ),
        autonomy_hint=RecommendationAutonomyHint.REQUIRES_USER_APPROVAL,
        generated_title=delta.title,
        generated_description=accepted_summary,
        generated_at=generated_at,
    )


def _next_action_recommendation_id(delta: WorkProductDelta) -> str:
    digest = sha256(
        f"{delta.id}:{delta.source_capability_run_id}:{delta.source_output_id}".encode(
            "utf-8"
        )
    ).hexdigest()[:12]
    return f"delta_rec_{digest}"


def _latest_linked_action_recommendation(
    *,
    recommendation_store: NextActionRecommendationStore,
    opportunity_id: str,
) -> NextActionRecommendation | None:
    recommendations = recommendation_store.list(opportunity_id=opportunity_id)
    linked = [
        recommendation
        for recommendation in recommendations
        if recommendation.cause.startswith("work_product_delta:")
    ]
    if not linked:
        return None
    return max(linked, key=lambda recommendation: recommendation.generated_at)


def _latest_activation_run(
    *,
    activation_store: OpportunityActivationRunStore,
    opportunity_id: str,
) -> OpportunityActivationRun | None:
    runs = activation_store.list(opportunity_id=opportunity_id)
    if not runs:
        return None
    return max(runs, key=lambda run: run.created_at)


def _engagement_field_from_activation(
    run: OpportunityActivationRun | None,
):
    if run is None:
        return None
    engagement_candidates = []
    for field in run.packet_field_action_matrix.fields:
        route_text = " ".join(
            [
                field.field_key,
                field.label,
                field.question,
                field.section,
                field.route_kind.value,
                field.recommended_route,
                field.route_rationale,
                *field.answer_paths,
            ]
        ).lower()
        if field.action_state.value == "answered":
            continue
        if any(
            token in route_text
            for token in (
                "customer_call_plan",
                "call",
                "customer",
                "engagement",
                "capture lead",
            )
        ):
            engagement_candidates.append(field)
    return engagement_candidates[0] if engagement_candidates else None


def _engagement_delta_from_action_recommendation(
    *,
    recommendation: NextActionRecommendation | None,
    opportunity_id: str,
) -> WorkProductDelta:
    if recommendation is None:
        raise ValueError("No linked Action Plan recommendation available")
    objective = recommendation.title
    prompts = _suggested_prompts(
        objective=objective,
        seed_summary=recommendation.description,
    )
    output_id = f"engagement_from_recommendation_{recommendation.id}"
    return WorkProductDelta(
        id=_delta_id(
            opportunity_id=opportunity_id,
            output_id=output_id,
            destination=WorkProductDeltaDestination.CALL_PLAN,
        ),
        opportunity_id=opportunity_id,
        destination=WorkProductDeltaDestination.CALL_PLAN,
        title="Engagement prep from linked Action Plan implication",
        source_capability_run_id=f"recommendation:{recommendation.id}",
        source_output_id=output_id,
        source_capability_id=(
            recommendation.capability_route.capability_id
            or "action-plan-link-engagement-prep"
        ),
        before_summary=(
            "No reviewed engagement-prep candidate accepted from linked "
            "Action Plan implication."
        ),
        after_summary=_engagement_after_summary(objective=objective, prompts=prompts),
        source_refs=recommendation.context_snapshot.reviewable_refs,
        capability_output_refs=tuple(
            ref
            for ref in recommendation.context_snapshot.reviewable_refs
            if ref.startswith("capability-run://")
        ),
        assumptions=recommendation.context_snapshot.source_limitation_refs
        + (
            "Engagement-prep candidate remains reviewable until explicit downstream acceptance.",
        ),
        gaps=recommendation.context_snapshot.gap_refs
        + (
            "Reviewer must accept/discard/route before call-plan artifact generation.",
        ),
        provenance={
            "source_mode": EngagementPrepSourcePreference.ACTION_PLAN_LINK.value,
            "linked_recommendation_id": recommendation.id,
            "engagement_objective": objective,
            "suggested_prompts": prompts,
            "trusted_downstream_writes": False,
        },
    )


def _engagement_delta_from_packet_gap(
    *,
    run: OpportunityActivationRun | None,
    field,
    opportunity_id: str,
) -> WorkProductDelta:
    if run is None or field is None:
        raise ValueError("No packet-gap engagement context available")
    objective = f"Prepare customer engagement around {field.label}"
    prompts = _suggested_prompts(objective=objective, seed_summary=field.question)
    output_id = f"engagement_from_activation_{run.run_id}_{field.field_key}"
    return WorkProductDelta(
        id=_delta_id(
            opportunity_id=opportunity_id,
            output_id=output_id,
            destination=WorkProductDeltaDestination.CALL_PLAN,
        ),
        opportunity_id=opportunity_id,
        destination=WorkProductDeltaDestination.CALL_PLAN,
        title="Engagement prep from packet gap route",
        field_key=field.field_key,
        source_capability_run_id=run.run_id,
        source_output_id=output_id,
        source_capability_id=(
            field.capability_routes[0].capability_id
            if field.capability_routes
            else "call-plan-question-prep"
        ),
        before_summary=(
            "No reviewed engagement-prep candidate tied to packet engagement gap."
        ),
        after_summary=_engagement_after_summary(objective=objective, prompts=prompts),
        source_refs=field.source_refs,
        capability_output_refs=(),
        assumptions=(
            field.route_rationale,
            "No customer-facing communication produced in this review step.",
        ),
        gaps=(
            field.gap_summary or "Packet engagement gap still open for operator review.",
            "Reviewer must decide destination before trusted downstream writes.",
        ),
        provenance={
            "source_mode": EngagementPrepSourcePreference.PACKET_GAP.value,
            "activation_run_id": run.run_id,
            "packet_field_key": field.field_key,
            "engagement_objective": objective,
            "suggested_prompts": prompts,
            "trusted_downstream_writes": False,
        },
    )


def _engagement_delta_from_fallback(*, opportunity_id: str) -> WorkProductDelta:
    objective = "Prepare first customer engagement validation call"
    prompts = _suggested_prompts(
        objective=objective,
        seed_summary="Use customer-call-plan fallback route when packet/action links missing.",
    )
    output_id = "engagement_customer_call_plan_fallback"
    return WorkProductDelta(
        id=_delta_id(
            opportunity_id=opportunity_id,
            output_id=output_id,
            destination=WorkProductDeltaDestination.CALL_PLAN,
        ),
        opportunity_id=opportunity_id,
        destination=WorkProductDeltaDestination.CALL_PLAN,
        title="Engagement prep from customer-call-plan fallback route",
        source_capability_run_id="fallback",
        source_output_id=output_id,
        source_capability_id="customer-call-plan-fallback-route",
        before_summary="No reviewed engagement-prep fallback candidate exists.",
        after_summary=_engagement_after_summary(objective=objective, prompts=prompts),
        source_refs=(),
        capability_output_refs=(),
        assumptions=(
            "Fallback route used because no linked packet gaps or action implications were available.",
            "No customer-facing communication produced in this review step.",
        ),
        gaps=(
            "No packet/action linkage available yet for call-specific prep context.",
            "Reviewer must route or accept before downstream work.",
        ),
        provenance={
            "source_mode": EngagementPrepSourcePreference.CUSTOMER_CALL_PLAN_FALLBACK.value,
            "engagement_objective": objective,
            "suggested_prompts": prompts,
            "linked_recommendation_id": None,
            "trusted_downstream_writes": False,
        },
    )


def _engagement_after_summary(*, objective: str, prompts: tuple[str, ...]) -> str:
    prompt_lines = "\n".join(f"- {prompt}" for prompt in prompts)
    return (
        f"Engagement objective: {objective}\n"
        "Suggested validation prompts:\n"
        f"{prompt_lines}"
    )


def _suggested_prompts(*, objective: str, seed_summary: str) -> tuple[str, ...]:
    first_prompt = f"What customer signal best validates this objective: {objective}?"
    second_prompt = (
        "Which incumbent or competitor claim should we challenge during call prep?"
    )
    third_prompt = f"What evidence follow-up should be captured next: {seed_summary}"
    return (first_prompt, second_prompt, third_prompt)


def _find_run_output(run: CapabilityRun, output_id: str) -> CapabilityRunOutput:
    for output in run.outputs:
        if output.output_id == output_id:
            return output
    raise FileNotFoundError(f"Capability Run Output not found: {output_id}")


def _delta_id(
    *,
    opportunity_id: str,
    output_id: str,
    destination: WorkProductDeltaDestination,
) -> str:
    digest = sha256(
        f"{opportunity_id}:{output_id}:{destination.value}".encode("utf-8")
    ).hexdigest()[:12]
    return f"delta_{digest}_{destination.value}"


def _field_label(field_key: str) -> str:
    return field_key.replace("_", " ").title()


def _delta_summary(deltas: tuple[WorkProductDelta, ...]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for delta in deltas:
        summary[delta.destination.value] = summary.get(delta.destination.value, 0) + 1
    return summary


def _ordered_deltas(
    deltas: tuple[WorkProductDelta, ...],
) -> tuple[WorkProductDelta, ...]:
    destination_order = {
        WorkProductDeltaDestination.LIVING_PACKET: 0,
        WorkProductDeltaDestination.ACTION_PLAN: 1,
        WorkProductDeltaDestination.CALL_PLAN: 2,
        WorkProductDeltaDestination.RISK_REGISTER: 3,
        WorkProductDeltaDestination.FOLLOW_UP_ROUTE: 4,
        WorkProductDeltaDestination.ARTIFACT_CONTEXT: 5,
    }
    return tuple(
        sorted(
            deltas,
            key=lambda delta: (destination_order.get(delta.destination, 99), delta.id),
        )
    )
