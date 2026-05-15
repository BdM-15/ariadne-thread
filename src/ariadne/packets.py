from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from ariadne.opportunities import Opportunity


class PacketReadiness(StrEnum):
    NOT_READY = "not_ready"
    DRAFT_READY = "draft_ready"
    REVIEW_READY = "review_ready"
    DECISION_READY = "decision_ready"


class CanonicalPacketSection(StrEnum):
    OPPORTUNITY_OVERVIEW = "opportunity_overview"
    CUSTOMER_CONTEXT = "customer_context"
    REQUIREMENTS_AND_SCOPE = "requirements_and_scope"
    COMPETITIVE_POSITION = "competitive_position"
    SOLUTION_STRATEGY = "solution_strategy"
    PRICE_TO_WIN = "price_to_win"
    RISKS_AND_GAPS = "risks_and_gaps"
    RECOMMENDATION_AND_NEXT_ACTIONS = "recommendation_and_next_actions"


class PacketSectionStatus(StrEnum):
    NEEDS_EVIDENCE = "needs_evidence"
    PARTIALLY_SUPPORTED = "partially_supported"
    SUPPORTED = "supported"
    ASSUMPTION = "assumption"


class EvidenceStatus(StrEnum):
    ANSWERED = "answered"
    PARTIAL = "partial"
    GAP = "gap"
    ASSUMPTION = "assumption"


class PacketSectionState(BaseModel):
    section: CanonicalPacketSection
    status: PacketSectionStatus = PacketSectionStatus.NEEDS_EVIDENCE
    evidence_status: EvidenceStatus = EvidenceStatus.GAP
    evidence_ids: tuple[str, ...] = ()
    gap_summary: str | None = None


class BriefingViewSection(BaseModel):
    section: CanonicalPacketSection
    status: PacketSectionStatus


class BriefingView(BaseModel):
    opportunity_name: str
    readiness: PacketReadiness
    sections: tuple[BriefingViewSection, ...]


class CoverageViewSection(BaseModel):
    section: CanonicalPacketSection
    evidence_status: EvidenceStatus
    evidence_ids: tuple[str, ...]
    gap_summary: str | None = None


class CoverageView(BaseModel):
    opportunity_name: str
    sections: tuple[CoverageViewSection, ...]


class LivingBriefingPacket(BaseModel):
    opportunity_name: str
    readiness: PacketReadiness = PacketReadiness.NOT_READY
    sections: dict[CanonicalPacketSection, PacketSectionState]


def create_living_briefing_packet(opportunity: Opportunity) -> LivingBriefingPacket:
    return LivingBriefingPacket(
        opportunity_name=opportunity.name,
        sections={
            section: PacketSectionState(section=section)
            for section in CanonicalPacketSection
        },
    )


def build_briefing_view(packet: LivingBriefingPacket) -> BriefingView:
    return BriefingView(
        opportunity_name=packet.opportunity_name,
        readiness=packet.readiness,
        sections=tuple(
            BriefingViewSection(section=section, status=state.status)
            for section, state in packet.sections.items()
        ),
    )



def update_packet_section_coverage(
    packet: LivingBriefingPacket,
    *,
    section: CanonicalPacketSection,
    evidence_status: EvidenceStatus,
    evidence_ids: list[str] | tuple[str, ...] = (),
    gap_summary: str | None = None,
) -> LivingBriefingPacket:
    packet.sections[section] = packet.sections[section].model_copy(
        update={
            "status": _section_status_for_evidence(evidence_status),
            "evidence_status": evidence_status,
            "evidence_ids": tuple(evidence_ids),
            "gap_summary": gap_summary,
        }
    )
    return packet


def _section_status_for_evidence(evidence_status: EvidenceStatus) -> PacketSectionStatus:
    if evidence_status is EvidenceStatus.ANSWERED:
        return PacketSectionStatus.SUPPORTED
    if evidence_status is EvidenceStatus.PARTIAL:
        return PacketSectionStatus.PARTIALLY_SUPPORTED
    if evidence_status is EvidenceStatus.ASSUMPTION:
        return PacketSectionStatus.ASSUMPTION
    return PacketSectionStatus.NEEDS_EVIDENCE


def update_packet_readiness(
    packet: LivingBriefingPacket,
    readiness: PacketReadiness,
) -> LivingBriefingPacket:
    packet.readiness = readiness
    return packet


def build_coverage_view(packet: LivingBriefingPacket) -> CoverageView:
    return CoverageView(
        opportunity_name=packet.opportunity_name,
        sections=tuple(
            CoverageViewSection(
                section=section,
                evidence_status=state.evidence_status,
                evidence_ids=state.evidence_ids,
                gap_summary=state.gap_summary,
            )
            for section, state in packet.sections.items()
        ),
    )