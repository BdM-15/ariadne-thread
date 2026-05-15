from ariadne.opportunities import EntryContext, EntryReason, LifecycleState, create_opportunity
from ariadne.packets import (
    CanonicalPacketSection,
    EvidenceStatus,
    PacketReadiness,
    PacketSectionStatus,
    build_briefing_view,
    build_coverage_view,
    create_living_briefing_packet,
    update_packet_readiness,
    update_packet_section_coverage,
)


def test_living_briefing_packet_can_be_created_for_opportunity() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
        ),
    )

    packet = create_living_briefing_packet(opportunity)

    assert packet.opportunity_name == "AFLCMC recompete support"
    assert packet.readiness is PacketReadiness.NOT_READY
    assert set(packet.sections) == set(CanonicalPacketSection)


def test_packet_readiness_can_move_through_decision_levels() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
        ),
    )
    packet = create_living_briefing_packet(opportunity)

    update_packet_readiness(packet, PacketReadiness.DRAFT_READY)
    update_packet_readiness(packet, PacketReadiness.REVIEW_READY)
    update_packet_readiness(packet, PacketReadiness.DECISION_READY)

    assert packet.readiness is PacketReadiness.DECISION_READY


def test_briefing_view_shows_packet_section_status() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
        ),
    )
    packet = create_living_briefing_packet(opportunity)

    briefing_view = build_briefing_view(packet)

    assert briefing_view.opportunity_name == "AFLCMC recompete support"
    assert briefing_view.readiness is PacketReadiness.NOT_READY
    assert briefing_view.sections[0].section is CanonicalPacketSection.OPPORTUNITY_OVERVIEW
    assert briefing_view.sections[0].status is PacketSectionStatus.NEEDS_EVIDENCE


def test_coverage_view_shows_evidence_and_gap_status() -> None:
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
        section=CanonicalPacketSection.CUSTOMER_CONTEXT,
        evidence_status=EvidenceStatus.PARTIAL,
        evidence_ids=["ev_customer_call"],
        gap_summary="Need validated customer pain and decision-maker map.",
    )

    coverage_view = build_coverage_view(packet)
    customer_context = next(
        section
        for section in coverage_view.sections
        if section.section is CanonicalPacketSection.CUSTOMER_CONTEXT
    )

    assert customer_context.evidence_status is EvidenceStatus.PARTIAL
    assert customer_context.evidence_ids == ("ev_customer_call",)
    assert customer_context.gap_summary == "Need validated customer pain and decision-maker map."


def test_packet_section_status_tracks_evidence_coverage() -> None:
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
        section=CanonicalPacketSection.OPPORTUNITY_OVERVIEW,
        evidence_status=EvidenceStatus.ANSWERED,
        evidence_ids=["ev_notice"],
    )

    briefing_view = build_briefing_view(packet)
    overview = next(
        section
        for section in briefing_view.sections
        if section.section is CanonicalPacketSection.OPPORTUNITY_OVERVIEW
    )

    assert overview.status is PacketSectionStatus.SUPPORTED
