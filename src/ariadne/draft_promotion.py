from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.action_plans import ActionPlanItem, AutonomyTier
from ariadne.opportunities import CoreCaptureWorkstream
from ariadne.packet_knowledge import (
    PacketFieldAnswer,
    PacketFieldAnswerStatus,
    create_packet_field_answer,
)
from ariadne.packets import CanonicalPacketSection, EvidenceStatus
from ariadne.packets import LivingBriefingPacket
from ariadne.quick_capture import (
    CaptureIntelligenceDraftPart,
    CaptureIntelligenceDraftPartType,
    CaptureReview,
)


class DraftPartPromotionDecision(BaseModel):
    id: str = Field(default_factory=lambda: f"promotion_{uuid4().hex}")
    status: str
    draft_part_id: str
    source_raw_item_id: str
    source_draft_id: str | None = None
    discard_reason: str | None = None
    promoted_output_created: bool = False


def promote_action_candidate_to_plan_item(
    review: CaptureReview,
    *,
    draft_part_id: str,
    reviewer_rationale: str,
    edited_content: str | None = None,
    evidence_ids: tuple[str, ...] = (),
    action_item_id: str | None = None,
) -> ActionPlanItem:
    draft_part = _find_draft_part(
        review,
        draft_part_id,
        expected_type=CaptureIntelligenceDraftPartType.ACTION_CANDIDATE,
    )
    return ActionPlanItem(
        id=action_item_id or f"ap_item_{uuid4().hex}",
        action=edited_content or draft_part.content,
        rationale=reviewer_rationale,
        related_workstream=CoreCaptureWorkstream.CUSTOMER_INSIGHT,
        related_packet_section=CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
        related_evidence_ids=evidence_ids,
        autonomy_tier=AutonomyTier.ASK_BEFORE_RUNNING,
        review_status="accepted",
        promoted_from_draft_part_id=draft_part.id,
        source_raw_item_id=review.raw_item_id,
        source_draft_id=_review_draft_id(review),
        review_edits=_review_edits(draft_part, edited_content),
    )


def promote_packet_implication_to_field_answer(
    review: CaptureReview,
    *,
    draft_part_id: str,
    field_key: str,
    reviewer_rationale: str,
    edited_value: str | None = None,
    evidence_ids: tuple[str, ...] = (),
    confidence: float | None = None,
) -> PacketFieldAnswer:
    draft_part = _find_draft_part(
        review,
        draft_part_id,
        expected_type=CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
    )
    return create_packet_field_answer(
        field_key=field_key,
        opportunity_id=review.opportunity_id or "unscoped_opportunity",
        value=edited_value or draft_part.content,
        status=PacketFieldAnswerStatus.NEEDS_REVIEW,
        evidence_status=EvidenceStatus.PARTIAL,
        evidence_ids=evidence_ids,
        assumption=_first_draft_assumption(review),
        confidence=confidence,
        provenance_note=reviewer_rationale,
        review_status="accepted",
        promoted_from_draft_part_id=draft_part.id,
        source_raw_item_id=review.raw_item_id,
        source_draft_id=_review_draft_id(review),
        review_edits=_review_edits(draft_part, edited_value),
    )


def promote_risk_to_packet_gap_update(
    review: CaptureReview,
    packet: LivingBriefingPacket,
    *,
    draft_part_id: str,
    section: CanonicalPacketSection,
    reviewer_rationale: str,
    edited_gap_summary: str | None = None,
) -> LivingBriefingPacket:
    draft_part = _find_draft_part(
        review,
        draft_part_id,
        expected_type=CaptureIntelligenceDraftPartType.LIKELY_RISK,
    )
    current = packet.sections[section]
    packet.sections[section] = current.model_copy(
        update={
            "gap_summary": edited_gap_summary or draft_part.content,
            "gap_provenance_notes": current.gap_provenance_notes
            + (
                f"accepted {draft_part.id} from {review.raw_item_id}: "
                f"{reviewer_rationale}",
                *_review_edits(draft_part, edited_gap_summary),
            ),
        }
    )
    return packet


def discard_draft_part_promotion(
    review: CaptureReview,
    *,
    draft_part_id: str,
    discard_reason: str,
) -> DraftPartPromotionDecision:
    draft_part = _find_any_draft_part(review, draft_part_id)
    return DraftPartPromotionDecision(
        status="discarded",
        draft_part_id=draft_part.id,
        source_raw_item_id=review.raw_item_id,
        source_draft_id=_review_draft_id(review),
        discard_reason=discard_reason,
    )


def _find_draft_part(
    review: CaptureReview,
    draft_part_id: str,
    *,
    expected_type: CaptureIntelligenceDraftPartType,
) -> CaptureIntelligenceDraftPart:
    if review.intelligence_draft is None:
        raise ValueError("capture review has no intelligence draft")
    for part in review.intelligence_draft.intelligence_pieces:
        if part.id == draft_part_id:
            if part.part_type is not expected_type:
                raise ValueError(
                    f"draft part {draft_part_id} is {part.part_type.value}, "
                    f"not {expected_type.value}"
                )
            return part
    raise ValueError(f"unknown draft part: {draft_part_id}")


def _find_any_draft_part(
    review: CaptureReview,
    draft_part_id: str,
) -> CaptureIntelligenceDraftPart:
    if review.intelligence_draft is None:
        raise ValueError("capture review has no intelligence draft")
    for part in review.intelligence_draft.intelligence_pieces:
        if part.id == draft_part_id:
            return part
    raise ValueError(f"unknown draft part: {draft_part_id}")


def _review_draft_id(review: CaptureReview) -> str | None:
    if review.intelligence_draft is None:
        return None
    return review.intelligence_draft.id


def _first_draft_assumption(review: CaptureReview) -> str | None:
    if review.intelligence_draft is None or not review.intelligence_draft.assumptions:
        return None
    return review.intelligence_draft.assumptions[0]


def _review_edits(
    draft_part: CaptureIntelligenceDraftPart,
    edited_content: str | None,
) -> tuple[str, ...]:
    if not edited_content or edited_content == draft_part.content:
        return ()
    return (f"edited from draft: {draft_part.content}",)