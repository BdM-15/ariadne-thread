from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.opportunities import CoreCaptureWorkstream, LifecycleState, Opportunity
from ariadne.packets import (
    CanonicalPacketSection,
    EvidenceStatus,
    LivingBriefingPacket,
)


class ActionPlanItemStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"


class AutonomyTier(StrEnum):
    AUTOMATIC = "automatic"
    ASK_BEFORE_RUNNING = "ask_before_running"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


class ExecutionDetailStatus(StrEnum):
    PROPOSED = "proposed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionDetail(BaseModel):
    id: str
    description: str
    proposed_by_capability: str | None = None
    status: ExecutionDetailStatus = ExecutionDetailStatus.PROPOSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActionPlanItem(BaseModel):
    id: str
    action: str
    rationale: str
    related_lifecycle_state: LifecycleState | None = None
    related_workstream: CoreCaptureWorkstream | None = None
    related_packet_section: CanonicalPacketSection | None = None
    related_packet_field_key: str | None = None
    related_evidence_ids: tuple[str, ...] = ()
    gap_summary: str | None = None
    status: ActionPlanItemStatus = ActionPlanItemStatus.PENDING
    autonomy_tier: AutonomyTier = AutonomyTier.ASK_BEFORE_RUNNING
    review_status: str | None = None
    promoted_from_draft_part_id: str | None = None
    source_raw_item_id: str | None = None
    source_draft_id: str | None = None
    source_recommendation_id: str | None = None
    recommendation_context_refs: tuple[str, ...] = ()
    recommendation_capability_route: str | None = None
    recommendation_review_decision_id: str | None = None
    review_edits: tuple[str, ...] = ()
    execution_details: tuple[ExecutionDetail, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CaptureActionPlan(BaseModel):
    opportunity_name: str
    items: tuple[ActionPlanItem, ...] = ()


class ActionPlanItemSummary(BaseModel):
    id: str
    action: str
    rationale: str
    related_lifecycle_state: LifecycleState | None = None
    related_workstream: CoreCaptureWorkstream | None = None
    related_packet_section: CanonicalPacketSection | None = None
    related_packet_field_key: str | None = None
    status: ActionPlanItemStatus
    autonomy_tier: AutonomyTier
    gap_summary: str | None = None


class ActionPlanView(BaseModel):
    opportunity_name: str
    items: tuple[ActionPlanItemSummary, ...] = ()


class ActionPlanItemDetailView(BaseModel):
    id: str
    action: str
    rationale: str
    related_lifecycle_state: LifecycleState | None = None
    related_workstream: CoreCaptureWorkstream | None = None
    related_packet_section: CanonicalPacketSection | None = None
    related_packet_field_key: str | None = None
    related_evidence_ids: tuple[str, ...] = ()
    gap_summary: str | None = None
    status: ActionPlanItemStatus
    autonomy_tier: AutonomyTier
    review_status: str | None = None
    promoted_from_draft_part_id: str | None = None
    source_raw_item_id: str | None = None
    source_draft_id: str | None = None
    source_recommendation_id: str | None = None
    recommendation_context_refs: tuple[str, ...] = ()
    recommendation_capability_route: str | None = None
    recommendation_review_decision_id: str | None = None
    review_edits: tuple[str, ...] = ()
    execution_details: tuple[ExecutionDetail, ...]


def create_capture_action_plan(opportunity: Opportunity) -> CaptureActionPlan:
    return CaptureActionPlan(
        opportunity_name=opportunity.name,
        items=tuple(
            ActionPlanItem(
                id=f"ap_item_{uuid4().hex}",
                action=f"Resolve {_display_name(need.workstream)} backfill",
                rationale=need.rationale,
                related_lifecycle_state=opportunity.lifecycle_state,
                related_workstream=need.workstream,
            )
            for need in opportunity.backfill_needs
        ),
    )


def add_packet_gap_actions(
    plan: CaptureActionPlan,
    packet: LivingBriefingPacket,
) -> CaptureActionPlan:
    gap_actions = tuple(
        ActionPlanItem(
            id=f"ap_item_{uuid4().hex}",
            action=f"Close {_display_name(section)} evidence gap",
            rationale=state.gap_summary or "Packet section needs supporting evidence.",
            related_packet_section=section,
            related_evidence_ids=state.evidence_ids,
            gap_summary=state.gap_summary,
        )
        for section, state in packet.sections.items()
        if state.evidence_status in {EvidenceStatus.GAP, EvidenceStatus.PARTIAL}
        and state.gap_summary
    )
    return plan.model_copy(update={"items": plan.items + gap_actions})


def create_execution_detail(
    *,
    description: str,
    proposed_by_capability: str | None = None,
    detail_id: str | None = None,
) -> ExecutionDetail:
    return ExecutionDetail(
        id=detail_id or f"ap_detail_{uuid4().hex}",
        description=description,
        proposed_by_capability=proposed_by_capability,
    )


def attach_execution_detail(
    item: ActionPlanItem,
    detail: ExecutionDetail,
) -> ActionPlanItem:
    return item.model_copy(
        update={"execution_details": item.execution_details + (detail,)}
    )


def build_action_plan_view(plan: CaptureActionPlan) -> ActionPlanView:
    return ActionPlanView(
        opportunity_name=plan.opportunity_name,
        items=tuple(
            ActionPlanItemSummary(
                id=item.id,
                action=item.action,
                rationale=item.rationale,
                related_lifecycle_state=item.related_lifecycle_state,
                related_workstream=item.related_workstream,
                related_packet_section=item.related_packet_section,
                related_packet_field_key=item.related_packet_field_key,
                status=item.status,
                autonomy_tier=item.autonomy_tier,
                gap_summary=item.gap_summary,
            )
            for item in plan.items
        ),
    )


def build_action_plan_item_detail_view(
    item: ActionPlanItem,
) -> ActionPlanItemDetailView:
    return ActionPlanItemDetailView(
        id=item.id,
        action=item.action,
        rationale=item.rationale,
        related_lifecycle_state=item.related_lifecycle_state,
        related_workstream=item.related_workstream,
        related_packet_section=item.related_packet_section,
        related_packet_field_key=item.related_packet_field_key,
        related_evidence_ids=item.related_evidence_ids,
        gap_summary=item.gap_summary,
        status=item.status,
        autonomy_tier=item.autonomy_tier,
        review_status=item.review_status,
        promoted_from_draft_part_id=item.promoted_from_draft_part_id,
        source_raw_item_id=item.source_raw_item_id,
        source_draft_id=item.source_draft_id,
        source_recommendation_id=item.source_recommendation_id,
        recommendation_context_refs=item.recommendation_context_refs,
        recommendation_capability_route=item.recommendation_capability_route,
        recommendation_review_decision_id=item.recommendation_review_decision_id,
        review_edits=item.review_edits,
        execution_details=item.execution_details,
    )


def _display_name(value: StrEnum) -> str:
    return value.value.replace("_", " ")