from ariadne.evidence import EvidenceKind
from ariadne.quick_capture import (
    CaptureReviewStatus,
    ProposalStatus,
    ProposedDestination,
    RawCaptureStatus,
    capture_raw_item,
    process_raw_capture_item,
)


def test_raw_capture_item_can_be_created_from_text_with_optional_opportunity() -> None:
    raw_item = capture_raw_item(
        "Customer mentioned transition risk during recompete call.",
        opportunity_id="opp-aflcmc-recompete",
    )

    assert raw_item.id.startswith("raw_")
    assert raw_item.content == "Customer mentioned transition risk during recompete call."
    assert raw_item.opportunity_id == "opp-aflcmc-recompete"
    assert raw_item.status is RawCaptureStatus.CAPTURED


def test_processing_routes_raw_capture_to_review_without_trusted_write() -> None:
    raw_item = capture_raw_item(
        "Customer said transition plan is weak. Need follow up with PM next week.",
        opportunity_id="opp-aflcmc-recompete",
    )

    review = process_raw_capture_item(raw_item)

    assert review.raw_item_id == raw_item.id
    assert review.opportunity_id == "opp-aflcmc-recompete"
    assert review.status is CaptureReviewStatus.NEEDS_REVIEW
    assert {proposal.destination for proposal in review.proposals} == {
        ProposedDestination.EVIDENCE_ITEM_REVIEW,
        ProposedDestination.ACTION_PLAN_ITEM_REVIEW,
    }
    assert {proposal.status for proposal in review.proposals} == {
        ProposalStatus.PENDING_REVIEW
    }
    assert review.trusted_opportunity_knowledge_updated is False


def test_evidence_review_proposal_contains_source_evidence_draft() -> None:
    raw_item = capture_raw_item(
        "Customer mentioned incumbent response times are slipping.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_customer_response_note",
    )

    review = process_raw_capture_item(raw_item)
    evidence_proposal = next(
        proposal
        for proposal in review.proposals
        if proposal.destination is ProposedDestination.EVIDENCE_ITEM_REVIEW
    )

    assert evidence_proposal.evidence.kind is EvidenceKind.SOURCE
    assert evidence_proposal.evidence.content == raw_item.content
    assert evidence_proposal.evidence.source_ref == "raw_capture:raw_customer_response_note"
    assert evidence_proposal.evidence.opportunity_id == "opp-aflcmc-recompete"
