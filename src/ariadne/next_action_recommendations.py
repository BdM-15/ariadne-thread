from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel

from ariadne.action_plans import (
    ActionPlanItem,
    AutonomyTier,
    CaptureActionPlan,
)
from ariadne.capabilities import CapabilityCatalog, CapabilityCatalogEntry
from ariadne.structured_knowledge import (
    KnowledgeGapSummary,
    KnowledgeRecordKind,
    KnowledgeSourceLimitation,
    OpportunityKnowledgeContextView,
)


class NextActionRecommendationReviewState(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    ROUTED = "routed"
    DISCARDED = "discarded"
    EDITED = "edited"


class ActionCapabilityRouteSupport(StrEnum):
    AVAILABLE_TOOL = "available_tool"
    PARTIAL_ASSISTANCE = "partial_assistance"
    USER_WORK = "user_work"
    CAPABILITY_GAP = "capability_gap"


class RecommendationAutonomyHint(StrEnum):
    REVIEW_REQUIRED = "review_required"
    CANDIDATE_FOR_FEWER_CLICKS_LATER = "candidate_for_fewer_clicks_later"
    NEVER_AUTO_HANDLE = "never_auto_handle"
    REQUIRES_USER_APPROVAL = "requires_user_approval"


class ActionCapabilityRoute(BaseModel):
    support: ActionCapabilityRouteSupport
    next_command_id: str
    next_command_label: str
    capability_id: str | None = None
    product_workflow: str | None = None
    rationale: str


class RecommendationContextSnapshot(BaseModel):
    opportunity_id: str
    trusted_refs: tuple[str, ...] = ()
    reviewable_refs: tuple[str, ...] = ()
    gap_refs: tuple[str, ...] = ()
    source_limitation_refs: tuple[str, ...] = ()
    recommendation_cause: str
    capability_route_id: str | None = None
    autonomy_hint: RecommendationAutonomyHint


class RecommendationReviewDecision(BaseModel):
    decision_id: str
    decision: str
    reviewer_rationale: str = ""
    routed_destination: str | None = None
    decided_at: str


class NextActionRecommendation(BaseModel):
    id: str
    opportunity_id: str
    title: str
    description: str
    cause: str
    rationale: str
    review_state: NextActionRecommendationReviewState = (
        NextActionRecommendationReviewState.PENDING
    )
    capability_route: ActionCapabilityRoute
    context_snapshot: RecommendationContextSnapshot
    autonomy_hint: RecommendationAutonomyHint = RecommendationAutonomyHint.REVIEW_REQUIRED
    created_action_plan_item_ids: tuple[str, ...] = ()
    review_decisions: tuple[RecommendationReviewDecision, ...] = ()
    generated_title: str | None = None
    generated_description: str | None = None
    is_stale: bool = False
    stale_reason: str | None = None
    version: int = 1
    family_id: str | None = None
    supersedes_recommendation_id: str | None = None
    generated_at: str


class RecommendationActionPlanResult(BaseModel):
    recommendation: NextActionRecommendation
    action_plan: CaptureActionPlan
    action_item: ActionPlanItem


class RecommendationRefreshResult(BaseModel):
    original_recommendation: NextActionRecommendation
    refreshed_recommendation: NextActionRecommendation


class DuplicateActionPlanSuggestion(BaseModel):
    action_item_id: str
    shared_refs: tuple[str, ...]


class NextActionRecommendationStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(
        self,
        recommendation: NextActionRecommendation,
    ) -> NextActionRecommendation:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(recommendation.id).write_text(
            recommendation.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return recommendation

    def read(self, recommendation_id: str) -> NextActionRecommendation:
        return NextActionRecommendation.model_validate_json(
            self._path(recommendation_id).read_text(encoding="utf-8")
        )

    def list(
        self,
        *,
        opportunity_id: str | None = None,
        review_state: NextActionRecommendationReviewState | None = None,
    ) -> list[NextActionRecommendation]:
        if not self.root.exists():
            return []
        recommendations = [
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        ]
        if opportunity_id is not None:
            recommendations = [
                recommendation
                for recommendation in recommendations
                if recommendation.opportunity_id == opportunity_id
            ]
        if review_state is not None:
            recommendations = [
                recommendation
                for recommendation in recommendations
                if recommendation.review_state is review_state
            ]
        return recommendations

    def _path(self, recommendation_id: str) -> Path:
        if not recommendation_id or recommendation_id != Path(recommendation_id).name:
            raise ValueError("recommendation_id must be a file-safe identifier")
        return self.root / f"{recommendation_id}.json"


def recommend_next_capture_actions(
    *,
    context: OpportunityKnowledgeContextView,
    capability_catalog: CapabilityCatalog,
    store: NextActionRecommendationStore,
    generated_at: str,
) -> tuple[NextActionRecommendation, ...]:
    recommendations = tuple(
        [
            _recommendation_from_gap(
                context=context,
                gap=gap,
                capability_catalog=capability_catalog,
                generated_at=generated_at,
            )
            for gap in context.gaps
        ]
        + [
            _recommendation_from_source_limitation(
                context=context,
                limitation=limitation,
                capability_catalog=capability_catalog,
                generated_at=generated_at,
            )
            for limitation in context.source_limitations
        ]
    )
    for recommendation in recommendations:
        store.write(recommendation)
    return recommendations


def accept_next_action_recommendation(
    *,
    store: NextActionRecommendationStore,
    recommendation_id: str,
    action_plan: CaptureActionPlan,
    reviewer_rationale: str,
    decided_at: str,
    action_item_id: str | None = None,
    existing_action_item_id: str | None = None,
    update_existing_action: bool = False,
) -> RecommendationActionPlanResult:
    recommendation = store.read(recommendation_id)
    _ensure_pending_recommendation(recommendation)
    if action_plan.opportunity_name != recommendation.opportunity_id:
        raise ValueError("action plan opportunity must match recommendation")
    decision = _review_decision(
        recommendation,
        decision="accept",
        reviewer_rationale=reviewer_rationale,
        decided_at=decided_at,
    )
    if existing_action_item_id is None:
        action_item = _action_plan_item_from_recommendation(
            recommendation,
            decision_id=decision.decision_id,
            action_item_id=action_item_id,
        )
        updated_plan = action_plan.model_copy(
            update={"items": action_plan.items + (action_item,)}
        )
    else:
        action_item = _updated_existing_action_plan_item(
            action_plan=action_plan,
            existing_action_item_id=existing_action_item_id,
            recommendation=recommendation,
            decision_id=decision.decision_id,
            update_existing_action=update_existing_action,
        )
        updated_plan = _replace_action_plan_item(action_plan, action_item)
    updated_recommendation = recommendation.model_copy(
        update={
            "review_state": NextActionRecommendationReviewState.ACCEPTED,
            "created_action_plan_item_ids": (
                recommendation.created_action_plan_item_ids + (action_item.id,)
            ),
            "review_decisions": recommendation.review_decisions + (decision,),
        }
    )
    store.write(updated_recommendation)
    return RecommendationActionPlanResult(
        recommendation=updated_recommendation,
        action_plan=updated_plan,
        action_item=action_item,
    )


def route_next_action_recommendation(
    *,
    store: NextActionRecommendationStore,
    recommendation_id: str,
    routed_destination: str,
    reviewer_rationale: str,
    decided_at: str,
) -> NextActionRecommendation:
    recommendation = store.read(recommendation_id)
    _ensure_pending_recommendation(recommendation)
    decision = _review_decision(
        recommendation,
        decision="route",
        reviewer_rationale=reviewer_rationale,
        decided_at=decided_at,
        routed_destination=routed_destination,
    )
    return store.write(
        recommendation.model_copy(
            update={
                "review_state": NextActionRecommendationReviewState.ROUTED,
                "review_decisions": recommendation.review_decisions + (decision,),
            }
        )
    )


def discard_next_action_recommendation(
    *,
    store: NextActionRecommendationStore,
    recommendation_id: str,
    reviewer_rationale: str,
    decided_at: str,
) -> NextActionRecommendation:
    recommendation = store.read(recommendation_id)
    _ensure_pending_recommendation(recommendation)
    decision = _review_decision(
        recommendation,
        decision="discard",
        reviewer_rationale=reviewer_rationale,
        decided_at=decided_at,
    )
    return store.write(
        recommendation.model_copy(
            update={
                "review_state": NextActionRecommendationReviewState.DISCARDED,
                "review_decisions": recommendation.review_decisions + (decision,),
            }
        )
    )


def edit_next_action_recommendation(
    *,
    store: NextActionRecommendationStore,
    recommendation_id: str,
    title: str,
    description: str,
    reviewer_rationale: str,
    decided_at: str,
) -> NextActionRecommendation:
    recommendation = store.read(recommendation_id)
    _ensure_pending_recommendation(recommendation)
    decision = _review_decision(
        recommendation,
        decision="edit",
        reviewer_rationale=reviewer_rationale,
        decided_at=decided_at,
    )
    return store.write(
        recommendation.model_copy(
            update={
                "title": title,
                "description": description,
                "generated_title": recommendation.generated_title or recommendation.title,
                "generated_description": (
                    recommendation.generated_description or recommendation.description
                ),
                "review_decisions": recommendation.review_decisions + (decision,),
            }
        )
    )


def refresh_stale_next_action_recommendation(
    *,
    store: NextActionRecommendationStore,
    recommendation_id: str,
    stale_reason: str,
    title: str,
    description: str,
    generated_at: str,
) -> RecommendationRefreshResult:
    recommendation = store.read(recommendation_id)
    stale_recommendation = recommendation.model_copy(
        update={"is_stale": True, "stale_reason": stale_reason}
    )
    refreshed_recommendation = recommendation.model_copy(
        update={
            "id": _refreshed_recommendation_id(recommendation),
            "title": title,
            "description": description,
            "generated_title": title,
            "generated_description": description,
            "review_state": NextActionRecommendationReviewState.PENDING,
            "created_action_plan_item_ids": (),
            "review_decisions": (),
            "is_stale": False,
            "stale_reason": None,
            "version": recommendation.version + 1,
            "family_id": recommendation.family_id or recommendation.id,
            "supersedes_recommendation_id": recommendation.id,
            "generated_at": generated_at,
        }
    )
    store.write(stale_recommendation)
    store.write(refreshed_recommendation)
    return RecommendationRefreshResult(
        original_recommendation=stale_recommendation,
        refreshed_recommendation=refreshed_recommendation,
    )


def suggest_duplicate_action_plan_items(
    recommendation: NextActionRecommendation,
    action_plan: CaptureActionPlan,
) -> tuple[DuplicateActionPlanSuggestion, ...]:
    suggestions = []
    packet_field_ref = _packet_field_ref_from_recommendation(recommendation)
    evidence_refs = set(_evidence_refs_from_snapshot(recommendation))
    for item in action_plan.items:
        shared_refs: list[str] = []
        if packet_field_ref is not None and item.related_packet_field_key is not None:
            if packet_field_ref == f"packet_field:{item.related_packet_field_key}":
                shared_refs.append(packet_field_ref)
        shared_refs.extend(ref for ref in item.related_evidence_ids if ref in evidence_refs)
        if shared_refs:
            suggestions.append(
                DuplicateActionPlanSuggestion(
                    action_item_id=item.id,
                    shared_refs=tuple(shared_refs),
                )
            )
    return tuple(suggestions)


def _ensure_pending_recommendation(recommendation: NextActionRecommendation) -> None:
    if recommendation.is_stale:
        raise ValueError("stale recommendation must be refreshed before acceptance")
    if recommendation.review_state is not NextActionRecommendationReviewState.PENDING:
        raise ValueError("recommendation must be pending review")


def _review_decision(
    recommendation: NextActionRecommendation,
    *,
    decision: str,
    reviewer_rationale: str,
    decided_at: str,
    routed_destination: str | None = None,
) -> RecommendationReviewDecision:
    return RecommendationReviewDecision(
        decision_id=_decision_id(recommendation, decision),
        decision=decision,
        reviewer_rationale=reviewer_rationale,
        routed_destination=routed_destination,
        decided_at=decided_at,
    )


def _action_plan_item_from_recommendation(
    recommendation: NextActionRecommendation,
    *,
    decision_id: str,
    action_item_id: str | None,
) -> ActionPlanItem:
    return ActionPlanItem(
        id=action_item_id or _action_item_id(recommendation),
        action=recommendation.title,
        rationale=recommendation.description,
        related_packet_field_key=_packet_field_key_from_recommendation(recommendation),
        related_evidence_ids=_evidence_refs_from_snapshot(recommendation),
        gap_summary=recommendation.description,
        autonomy_tier=AutonomyTier.HUMAN_APPROVAL_REQUIRED,
        review_status="accepted",
        source_recommendation_id=recommendation.id,
        recommendation_context_refs=_context_refs_from_snapshot(recommendation),
        recommendation_capability_route=_capability_route_ref(recommendation),
        recommendation_review_decision_id=decision_id,
    )


def _updated_existing_action_plan_item(
    *,
    action_plan: CaptureActionPlan,
    existing_action_item_id: str,
    recommendation: NextActionRecommendation,
    decision_id: str,
    update_existing_action: bool,
) -> ActionPlanItem:
    item = _find_action_plan_item(action_plan, existing_action_item_id)
    review_edits = item.review_edits
    update = {
        "related_packet_field_key": item.related_packet_field_key
        or _packet_field_key_from_recommendation(recommendation),
        "related_evidence_ids": _merge_refs(
            item.related_evidence_ids,
            _evidence_refs_from_snapshot(recommendation),
        ),
        "gap_summary": item.gap_summary or recommendation.description,
        "review_status": "accepted",
        "source_recommendation_id": recommendation.id,
        "recommendation_context_refs": _merge_refs(
            item.recommendation_context_refs,
            _context_refs_from_snapshot(recommendation),
        ),
        "recommendation_capability_route": _capability_route_ref(recommendation),
        "recommendation_review_decision_id": decision_id,
    }
    if update_existing_action:
        review_edits = review_edits + (
            f"Previous action: {item.action}",
            f"Previous rationale: {item.rationale}",
        )
        update |= {
            "action": recommendation.title,
            "rationale": recommendation.description,
            "gap_summary": recommendation.description,
            "review_edits": review_edits,
        }
    return item.model_copy(update=update)


def _find_action_plan_item(
    action_plan: CaptureActionPlan,
    action_item_id: str,
) -> ActionPlanItem:
    for item in action_plan.items:
        if item.id == action_item_id:
            return item
    raise ValueError("existing action item was not found")


def _replace_action_plan_item(
    action_plan: CaptureActionPlan,
    updated_item: ActionPlanItem,
) -> CaptureActionPlan:
    return action_plan.model_copy(
        update={
            "items": tuple(
                updated_item if item.id == updated_item.id else item
                for item in action_plan.items
            )
        }
    )


def _context_refs_from_snapshot(
    recommendation: NextActionRecommendation,
) -> tuple[str, ...]:
    snapshot = recommendation.context_snapshot
    return snapshot.trusted_refs + snapshot.reviewable_refs + snapshot.source_limitation_refs


def _evidence_refs_from_snapshot(
    recommendation: NextActionRecommendation,
) -> tuple[str, ...]:
    return tuple(
        ref for ref in recommendation.context_snapshot.trusted_refs if ref.startswith("ev_")
    )


def _packet_field_key_from_recommendation(
    recommendation: NextActionRecommendation,
) -> str | None:
    for ref in recommendation.context_snapshot.gap_refs:
        if ref.startswith("packet_field_answer:"):
            return ref.rsplit(":", 1)[-1]
    return None


def _packet_field_ref_from_recommendation(
    recommendation: NextActionRecommendation,
) -> str | None:
    field_key = _packet_field_key_from_recommendation(recommendation)
    if field_key is None:
        return None
    return f"packet_field:{field_key}"


def _capability_route_ref(recommendation: NextActionRecommendation) -> str:
    return (
        recommendation.capability_route.capability_id
        or recommendation.capability_route.next_command_id
    )


def _merge_refs(first: tuple[str, ...], second: tuple[str, ...]) -> tuple[str, ...]:
    merged = list(first)
    for ref in second:
        if ref not in merged:
            merged.append(ref)
    return tuple(merged)


def _refreshed_recommendation_id(recommendation: NextActionRecommendation) -> str:
    family_id = recommendation.family_id or recommendation.id
    return f"{family_id}_v{recommendation.version + 1}"


def _action_item_id(recommendation: NextActionRecommendation) -> str:
    digest = sha256(f"action|{recommendation.id}".encode("utf-8")).hexdigest()
    return f"ap_item_{digest[:16]}"


def _decision_id(recommendation: NextActionRecommendation, decision: str) -> str:
    sequence = len(recommendation.review_decisions) + 1
    return f"rec_decision_{sequence}_{decision}_{recommendation.id}"


def _recommendation_from_gap(
    *,
    context: OpportunityKnowledgeContextView,
    gap: KnowledgeGapSummary,
    capability_catalog: CapabilityCatalog,
    generated_at: str,
) -> NextActionRecommendation:
    route = _capability_route_for_gap(gap, capability_catalog)
    autonomy_hint = RecommendationAutonomyHint.REVIEW_REQUIRED
    recommendation_id = _recommendation_id(
        context.opportunity_id,
        "packet_gap" if gap.record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER else "gap",
        gap.record_id,
    )
    return NextActionRecommendation(
        id=recommendation_id,
        opportunity_id=context.opportunity_id,
        title=_title_for_gap(gap),
        description=gap.summary,
        cause="packet_gap" if gap.record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER else "gap",
        rationale="Generated from deterministic Opportunity Knowledge Context gaps.",
        capability_route=route,
        context_snapshot=_snapshot_for_recommendation(
            context=context,
            gap=gap,
            route=route,
            autonomy_hint=autonomy_hint,
        ),
        autonomy_hint=autonomy_hint,
        generated_at=generated_at,
    )


def _recommendation_from_source_limitation(
    *,
    context: OpportunityKnowledgeContextView,
    limitation: KnowledgeSourceLimitation,
    capability_catalog: CapabilityCatalog,
    generated_at: str,
) -> NextActionRecommendation:
    route = _capability_route_for_source_limitation(limitation, capability_catalog)
    autonomy_hint = RecommendationAutonomyHint.REVIEW_REQUIRED
    recommendation_id = _recommendation_id(
        context.opportunity_id,
        "source_limitation",
        limitation.record_id,
    )
    return NextActionRecommendation(
        id=recommendation_id,
        opportunity_id=context.opportunity_id,
        title=f"Review source limitation: {limitation.record_id}",
        description=limitation.summary,
        cause="source_limitation",
        rationale="Generated from deterministic Opportunity Knowledge Context source limitations.",
        capability_route=route,
        context_snapshot=_snapshot_for_recommendation(
            context=context,
            source_limitation=limitation,
            route=route,
            autonomy_hint=autonomy_hint,
        ),
        autonomy_hint=autonomy_hint,
        generated_at=generated_at,
    )


def _capability_route_for_source_limitation(
    limitation: KnowledgeSourceLimitation,
    capability_catalog: CapabilityCatalog,
) -> ActionCapabilityRoute:
    matching_entry = _matching_capability_for_source_limitation(
        limitation,
        capability_catalog,
    )
    if matching_entry is not None:
        return ActionCapabilityRoute(
            support=ActionCapabilityRouteSupport.PARTIAL_ASSISTANCE,
            next_command_id="review_source_limitation",
            next_command_label="Review source limitation",
            capability_id=matching_entry.id,
            product_workflow="knowledge_context",
            rationale="Capability Catalog contains a possible enrichment workflow fit.",
        )
    return ActionCapabilityRoute(
        support=ActionCapabilityRouteSupport.CAPABILITY_GAP,
        next_command_id="review_source_limitation",
        next_command_label="Review source limitation",
        product_workflow="knowledge_context",
        rationale="No matching Capability Catalog entry is available for this source limitation.",
    )


def _capability_route_for_gap(
    gap: KnowledgeGapSummary,
    capability_catalog: CapabilityCatalog,
) -> ActionCapabilityRoute:
    matching_entry = _matching_capability_for_gap(gap, capability_catalog)
    if matching_entry is not None:
        return ActionCapabilityRoute(
            support=ActionCapabilityRouteSupport.AVAILABLE_TOOL,
            next_command_id=gap.command_id,
            next_command_label="Review packet gap",
            capability_id=matching_entry.id,
            product_workflow="living_briefing_packet",
            rationale="Capability Catalog contains a tested workflow fit for packet/action work.",
        )
    return ActionCapabilityRoute(
        support=ActionCapabilityRouteSupport.USER_WORK,
        next_command_id=gap.command_id,
        next_command_label="Review gap",
        product_workflow="knowledge_context",
        rationale="No matching Capability Catalog entry was available; user review is required.",
    )


def _matching_capability_for_gap(
    gap: KnowledgeGapSummary,
    capability_catalog: CapabilityCatalog,
) -> CapabilityCatalogEntry | None:
    desired_workflows = _desired_workflows_for_gap(gap)
    for entry in capability_catalog.entries:
        if desired_workflows.intersection(entry.product_workflow_fit):
            return entry
    return None


def _matching_capability_for_source_limitation(
    limitation: KnowledgeSourceLimitation,
    capability_catalog: CapabilityCatalog,
) -> CapabilityCatalogEntry | None:
    desired_workflows = {"sam_gov_enrichment", "document_intake", "knowledge_context"}
    if limitation.record_kind is KnowledgeRecordKind.SAM_GOV_PROFILE:
        desired_workflows.add("sam_gov")
    if limitation.record_kind is KnowledgeRecordKind.PIID_PROFILE:
        desired_workflows.add("usaspending")
    for entry in capability_catalog.entries:
        if desired_workflows.intersection(entry.product_workflow_fit):
            return entry
    return None


def _desired_workflows_for_gap(gap: KnowledgeGapSummary) -> set[str]:
    if gap.record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER:
        return {"living_briefing_packet", "action_plan"}
    return {"knowledge_context", "action_plan"}


def _snapshot_for_recommendation(
    *,
    context: OpportunityKnowledgeContextView,
    gap: KnowledgeGapSummary | None = None,
    source_limitation: KnowledgeSourceLimitation | None = None,
    route: ActionCapabilityRoute,
    autonomy_hint: RecommendationAutonomyHint,
) -> RecommendationContextSnapshot:
    recommendation_cause = "source_limitation" if source_limitation else "gap"
    if gap is not None and gap.record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER:
        recommendation_cause = "packet_gap"
    return RecommendationContextSnapshot(
        opportunity_id=context.opportunity_id,
        trusted_refs=tuple(
            item.record_id
            for item in context.trusted_context.items
            if item.record_kind is not KnowledgeRecordKind.OPPORTUNITY
        ),
        reviewable_refs=tuple(
            item.record_id
            for item in context.reviewable_context.items
            if item.record_kind is not KnowledgeRecordKind.OPPORTUNITY
        ),
        gap_refs=(gap.record_id,) if gap is not None else (),
        source_limitation_refs=tuple(
            limitation.record_id for limitation in context.source_limitations
        )
        if source_limitation is None
        else (source_limitation.record_id,),
        recommendation_cause=recommendation_cause,
        capability_route_id=route.capability_id,
        autonomy_hint=autonomy_hint,
    )


def _title_for_gap(gap: KnowledgeGapSummary) -> str:
    if gap.record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER:
        return f"Resolve packet gap: {gap.record_id.rsplit(':', 1)[-1]}"
    return "Resolve knowledge gap"


def _recommendation_id(opportunity_id: str, cause: str, target_id: str) -> str:
    digest = sha256(f"{opportunity_id}|{cause}|{target_id}".encode("utf-8")).hexdigest()
    return f"next_action_{digest[:16]}"