from ariadne.action_plans import AutonomyTier
from ariadne.draft_promotion import (
    discard_draft_part_promotion,
    promote_action_candidate_to_plan_item,
    promote_packet_implication_to_field_answer,
    promote_risk_to_packet_gap_update,
)
from ariadne.opportunities import CoreCaptureWorkstream
from ariadne.packet_knowledge import PacketFieldAnswerStatus
from ariadne.packets import (
    CanonicalPacketSection,
    EvidenceStatus,
    create_living_briefing_packet,
    update_packet_section_coverage,
)
from ariadne.opportunities import EntryContext, EntryReason, LifecycleState, create_opportunity
from ariadne.quick_capture import (
    CaptureIntelligenceDraftPartType,
    capture_raw_item,
    process_raw_capture_item,
)


def test_accepted_action_candidate_promotes_to_action_plan_item_with_provenance() -> None:
    raw_item = capture_raw_item(
        "Need follow up with PM to validate transition proof points.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_transition_follow_up",
    )
    review = process_raw_capture_item(raw_item)
    draft = review.intelligence_draft
    assert draft is not None
    action_part = next(
        part
        for part in draft.intelligence_pieces
        if part.part_type is CaptureIntelligenceDraftPartType.ACTION_CANDIDATE
    )

    item = promote_action_candidate_to_plan_item(
        review,
        draft_part_id=action_part.id,
        reviewer_rationale="Reviewer accepted PM follow-up as next capture action.",
        evidence_ids=("ev_customer_transition_note",),
    )

    assert item.action == action_part.content
    assert item.rationale == "Reviewer accepted PM follow-up as next capture action."
    assert item.related_workstream is CoreCaptureWorkstream.CUSTOMER_INSIGHT
    assert item.related_packet_section is CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS
    assert item.related_evidence_ids == ("ev_customer_transition_note",)
    assert item.autonomy_tier is AutonomyTier.ASK_BEFORE_RUNNING
    assert item.review_status == "accepted"
    assert item.promoted_from_draft_part_id == action_part.id
    assert item.source_raw_item_id == "raw_transition_follow_up"
    assert item.source_draft_id == draft.id
    assert item.review_edits == ()


def test_accepted_packet_implication_promotes_to_packet_answer_with_edits() -> None:
    raw_item = capture_raw_item(
        "Customer says transition risk needs a packet gap and mitigation note.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_packet_gap_note",
    )
    review = process_raw_capture_item(raw_item)
    draft = review.intelligence_draft
    assert draft is not None
    packet_part = next(
        part
        for part in draft.intelligence_pieces
        if part.part_type is CaptureIntelligenceDraftPartType.PACKET_IMPLICATION
    )

    answer = promote_packet_implication_to_field_answer(
        review,
        draft_part_id=packet_part.id,
        field_key="risks",
        reviewer_rationale="Reviewer accepted this as risks packet content.",
        edited_value="Transition risk needs mitigation evidence before gate review.",
        evidence_ids=("ev_packet_gap_note",),
        confidence=0.66,
    )

    assert answer.field_key == "risks"
    assert answer.opportunity_id == "opp-aflcmc-recompete"
    assert answer.value == "Transition risk needs mitigation evidence before gate review."
    assert answer.status is PacketFieldAnswerStatus.NEEDS_REVIEW
    assert answer.evidence_status is EvidenceStatus.PARTIAL
    assert answer.evidence_ids == ("ev_packet_gap_note",)
    assert answer.confidence == 0.66
    assert answer.assumption == draft.assumptions[0]
    assert answer.provenance_note == "Reviewer accepted this as risks packet content."
    assert answer.review_status == "accepted"
    assert answer.promoted_from_draft_part_id == packet_part.id
    assert answer.source_raw_item_id == "raw_packet_gap_note"
    assert answer.source_draft_id == draft.id
    assert answer.review_edits == (
        f"edited from draft: {packet_part.content}",
    )


def test_accepted_risk_promotes_to_packet_gap_without_overwriting_evidence() -> None:
    raw_item = capture_raw_item(
        "Customer says transition plan is weak and creates gate risk.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_transition_risk_note",
    )
    review = process_raw_capture_item(raw_item)
    draft = review.intelligence_draft
    assert draft is not None
    risk_part = next(
        part
        for part in draft.intelligence_pieces
        if part.part_type is CaptureIntelligenceDraftPartType.LIKELY_RISK
    )
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
        ),
    )
    packet = create_living_briefing_packet(opportunity)
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.RISKS_AND_GAPS,
        evidence_status=EvidenceStatus.PARTIAL,
        evidence_ids=("ev_existing_risk",),
    )

    updated = promote_risk_to_packet_gap_update(
        review,
        packet,
        draft_part_id=risk_part.id,
        section=CanonicalPacketSection.RISKS_AND_GAPS,
        reviewer_rationale="Reviewer accepted risk as packet gap.",
        edited_gap_summary="Transition mitigation needs proof before gate review.",
    )

    state = updated.sections[CanonicalPacketSection.RISKS_AND_GAPS]
    assert state.evidence_status is EvidenceStatus.PARTIAL
    assert state.evidence_ids == ("ev_existing_risk",)
    assert state.gap_summary == "Transition mitigation needs proof before gate review."
    assert state.gap_provenance_notes == (
        f"accepted {risk_part.id} from raw_transition_risk_note: Reviewer accepted risk as packet gap.",
        f"edited from draft: {risk_part.content}",
    )


def test_discarding_draft_part_records_decision_without_promoted_output() -> None:
    raw_item = capture_raw_item(
        "Customer rumor might be stale and should not drive packet content.",
        raw_item_id="raw_stale_rumor",
    )
    review = process_raw_capture_item(raw_item)
    draft = review.intelligence_draft
    assert draft is not None
    part = draft.intelligence_pieces[0]

    decision = discard_draft_part_promotion(
        review,
        draft_part_id=part.id,
        discard_reason="Reviewer discarded stale or unsupported claim.",
    )

    assert decision.status == "discarded"
    assert decision.draft_part_id == part.id
    assert decision.source_raw_item_id == "raw_stale_rumor"
    assert decision.source_draft_id == draft.id
    assert decision.discard_reason == "Reviewer discarded stale or unsupported claim."
    assert decision.promoted_output_created is False