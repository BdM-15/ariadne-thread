from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel

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
    decision: str
    reviewer_rationale: str = ""
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
    generated_at: str


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