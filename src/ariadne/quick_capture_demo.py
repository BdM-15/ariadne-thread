from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ariadne.action_plans import (
    ActionPlanItem,
    ActionPlanView,
    add_packet_gap_actions,
    build_action_plan_view,
    create_capture_action_plan,
)
from ariadne.capabilities import CapabilityCatalog, discover_local_capability_catalog
from ariadne.config import RuntimeSettings
from ariadne.document_intake import UploadedSourceMaterial, classify_uploaded_source_material
from ariadne.draft_promotion import (
    DraftPartPromotionDecision,
    discard_draft_part_promotion,
    promote_action_candidate_to_plan_item,
    promote_packet_implication_to_field_answer,
)
from ariadne.evidence import EvidenceItem
from ariadne.opportunities import (
    CoreCaptureWorkstream,
    EntryContext,
    EntryReason,
    LifecycleState,
    Opportunity,
    create_opportunity,
)
from ariadne.packet_knowledge import PacketFieldAnswer
from ariadne.packets import (
    CanonicalPacketSection,
    CoverageView,
    EvidenceStatus,
    LivingBriefingPacket,
    PacketReadiness,
    build_coverage_view,
    create_living_briefing_packet,
    update_packet_readiness,
    update_packet_section_coverage,
)
from ariadne.quick_capture import (
    CaptureIntelligenceDraftPartType,
    CaptureReview,
    CaptureReviewDecision,
    ProposedDestination,
    accept_capture_review_proposal,
    capture_pasted_text,
    capture_raw_item,
    capture_raw_item_from_upload,
    process_raw_capture_item,
)
from ariadne.reference_wiki import ReferenceWikiInfluence, load_reference_wiki


@dataclass
class InMemoryDemoEvidenceStore:
    items: list[EvidenceItem] = field(default_factory=list)

    def write(self, evidence: EvidenceItem) -> EvidenceItem:
        self.items.append(evidence)
        return evidence

    def list(self) -> list[EvidenceItem]:
        return list(self.items)


@dataclass(frozen=True)
class QuickCaptureDemoThread:
    opportunity: Opportunity
    packet: LivingBriefingPacket
    quick_capture: object
    capture_review: CaptureReview
    pasted_capture: object
    pasted_review: CaptureReview
    uploaded_capture: object
    uploaded_review: CaptureReview
    unsupported_upload: UploadedSourceMaterial
    accepted_evidence: CaptureReviewDecision
    accepted_action: ActionPlanItem
    accepted_packet_answer: PacketFieldAnswer
    discarded_output: DraftPartPromotionDecision
    action_view: ActionPlanView
    reference_influences: tuple[ReferenceWikiInfluence, ...]
    coverage_view: CoverageView
    catalog: CapabilityCatalog


def build_quick_capture_demo_thread(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> QuickCaptureDemoThread:
    root = workspace_root or Path.cwd()
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
            missing_or_stale_workstreams={
                CoreCaptureWorkstream.CUSTOMER_INSIGHT,
                CoreCaptureWorkstream.COMPETITIVE_INTELLIGENCE,
            },
        ),
    )
    packet = create_living_briefing_packet(opportunity)
    update_packet_readiness(packet, PacketReadiness.DRAFT_READY)
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.OPPORTUNITY_OVERVIEW,
        evidence_status=EvidenceStatus.ANSWERED,
        evidence_ids=["ev_notice", "ev_contract_history"],
    )
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.CUSTOMER_CONTEXT,
        evidence_status=EvidenceStatus.PARTIAL,
        evidence_ids=["ev_customer_call"],
        gap_summary="Need validated customer pain and decision-maker map.",
    )
    quick_capture = capture_raw_item(
        "call blur: incumbent contractor advantages obvious; customer says "
        "incumbent response times weak, delays and quality complaints. "
        "transition plan looks risky. Need proof points, CPARS/protest scan, "
        "and follow up with PM next week. maybe packet gap?",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_demo_rushed_capture_note",
    )
    reference_wiki = load_reference_wiki(
        _reference_wiki_root(settings.ariadne_reference_wiki_dir, root)
    )
    capture_review = process_raw_capture_item(
        quick_capture,
        reference_wiki=reference_wiki,
    )
    pasted_capture = capture_pasted_text(
        "Customer pasted note says transition proof needs PM follow up.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_demo_pasted_transition_note",
    )
    pasted_review = process_raw_capture_item(
        pasted_capture,
        reference_wiki=reference_wiki,
    )
    uploaded_source = classify_uploaded_source_material(
        filename="customer-call.md",
        mime_type="text/markdown",
        content=b"# Call note\n\nCustomer says transition risk needs packet gap.",
    )
    if uploaded_source.text is None:
        raise ValueError("demo uploaded source material was not readable")
    uploaded_capture = capture_raw_item_from_upload(
        uploaded_source.text,
        filename=uploaded_source.filename,
        mime_type=uploaded_source.mime_type,
        content_type=uploaded_source.content_type.value,
        byte_size=uploaded_source.byte_size,
        source_ref=uploaded_source.source_ref,
        warnings=uploaded_source.warnings,
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_demo_uploaded_customer_call",
    )
    uploaded_review = process_raw_capture_item(
        uploaded_capture,
        reference_wiki=reference_wiki,
    )
    unsupported_upload = classify_uploaded_source_material(
        filename="draft-rfp.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4\n...",
    )
    accepted_evidence = accept_capture_review_proposal(
        capture_review,
        _proposal_id_for_destination(
            capture_review,
            ProposedDestination.EVIDENCE_ITEM_REVIEW,
        ),
        evidence_store=InMemoryDemoEvidenceStore(),
        reviewer_rationale="Reviewer accepted rushed customer note as source evidence.",
    )
    accepted_action = promote_action_candidate_to_plan_item(
        capture_review,
        draft_part_id=_draft_part_id_for_type(
            capture_review,
            CaptureIntelligenceDraftPartType.ACTION_CANDIDATE,
        ),
        reviewer_rationale="Reviewer accepted PM follow-up as next capture action.",
        evidence_ids=(accepted_evidence.evidence.id if accepted_evidence.evidence else "",),
    )
    accepted_packet_answer = promote_packet_implication_to_field_answer(
        capture_review,
        draft_part_id=_draft_part_id_for_type(
            capture_review,
            CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
        ),
        field_key="risks",
        reviewer_rationale="Reviewer accepted transition risk as packet update.",
        edited_value="Transition risk needs mitigation evidence before gate review.",
        evidence_ids=(accepted_evidence.evidence.id if accepted_evidence.evidence else "",),
        confidence=0.64,
    )
    discarded_output = discard_draft_part_promotion(
        capture_review,
        draft_part_id=_draft_part_id_for_type(
            capture_review,
            CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE,
        ),
        discard_reason="Reviewer discarded discriminator claim until proof points exist.",
    )
    action_plan = add_packet_gap_actions(
        create_capture_action_plan(opportunity),
        packet,
    )
    action_plan = action_plan.model_copy(
        update={"items": action_plan.items + (accepted_action,)}
    )
    action_view = build_action_plan_view(action_plan)

    return QuickCaptureDemoThread(
        opportunity=opportunity,
        packet=packet,
        quick_capture=quick_capture,
        capture_review=capture_review,
        pasted_capture=pasted_capture,
        pasted_review=pasted_review,
        uploaded_capture=uploaded_capture,
        uploaded_review=uploaded_review,
        unsupported_upload=unsupported_upload,
        accepted_evidence=accepted_evidence,
        accepted_action=accepted_action,
        accepted_packet_answer=accepted_packet_answer,
        discarded_output=discarded_output,
        action_view=action_view,
        reference_influences=capture_review.reference_influences,
        coverage_view=build_coverage_view(packet),
        catalog=discover_local_capability_catalog(root),
    )


def _reference_wiki_root(path: Path, workspace_root: Path) -> Path:
    if path.is_absolute():
        return path
    return workspace_root / path


def _proposal_id_for_destination(
    review: CaptureReview,
    destination: ProposedDestination,
) -> str:
    for proposal in review.proposals:
        if proposal.destination is destination:
            return proposal.id
    raise ValueError(f"capture review has no proposal for {destination.value}")


def _draft_part_id_for_type(review: CaptureReview, part_type: CaptureIntelligenceDraftPartType) -> str:
    if review.intelligence_draft is None:
        raise ValueError("capture review has no intelligence draft")
    for part in review.intelligence_draft.intelligence_pieces:
        if part.part_type is part_type:
            return part.id
    raise ValueError(f"capture review has no draft part for {part_type.value}")
