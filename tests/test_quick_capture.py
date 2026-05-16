from ariadne.evidence import EvidenceKind
from ariadne.quick_capture import (
    CaptureIntelligenceDraftStatus,
    CaptureReviewStatus,
    ProposalStatus,
    ProposedDestination,
    RawCaptureStatus,
    capture_raw_item,
    process_raw_capture_item,
)
from ariadne.reference_wiki import load_reference_wiki


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


def test_processing_can_attach_reference_wiki_influences_without_trusted_write(
    tmp_path,
) -> None:
    _write_reference_note(
        tmp_path / "global_wiki" / "capture" / "incumbent-analysis-strategy.md",
        """---
title: Incumbent Analysis Strategy
---

Incumbent transition risk, weak response times, and customer complaints should
shape capture follow-up.
""",
    )
    _write_reference_note(
        tmp_path / "global_wiki" / "capture" / "customer-hot-buttons.md",
        """---
title: Customer Hot Button Identification
---

Customer complaints and operational pain indicate hot buttons.
""",
    )
    _write_reference_note(
        tmp_path / "global_wiki" / "shipley" / "capture-planning-phase.md",
        """---
title: Capture Planning Phase
---

Follow-up work after customer calls belongs in capture planning.
""",
    )
    raw_item = capture_raw_item(
        "Customer says incumbent response times are weak and transition risk "
        "needs follow up.",
        raw_item_id="raw_customer_transition_note",
    )

    review = process_raw_capture_item(
        raw_item,
        reference_wiki=load_reference_wiki(tmp_path),
    )

    assert len(review.reference_influences) == 3
    assert review.reference_influences[0].title == "Incumbent Analysis Strategy"
    assert review.trusted_opportunity_knowledge_updated is False


def test_messy_raw_capture_produces_reviewable_intelligence_draft(
    tmp_path,
) -> None:
    _write_reference_note(
        tmp_path / "global_wiki" / "capture" / "incumbent-analysis-strategy.md",
        """---
title: Incumbent Analysis Strategy
---

Incumbent transition risk, weak response times, customer complaints, proof points,
and ghost strategy should shape capture follow-up.
""",
    )
    raw_item = capture_raw_item(
        "call blur: customer says incumbent response times weak. transition plan "
        "looks risky. Need proof points and follow up with PM. maybe packet gap?",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_messy_customer_call",
    )

    review = process_raw_capture_item(
        raw_item,
        reference_wiki=load_reference_wiki(tmp_path),
    )

    assert review.intelligence_draft is not None
    draft = review.intelligence_draft
    assert draft.id.startswith("draft_")
    assert draft.raw_item_id == "raw_messy_customer_call"
    assert draft.opportunity_id == "opp-aflcmc-recompete"
    assert draft.status is CaptureIntelligenceDraftStatus.PENDING_REVIEW
    assert draft.raw_source_content == raw_item.content
    assert draft.reference_influences[0].title == "Incumbent Analysis Strategy"
    assert "transition" in draft.inferred_claims[0].lower()
    assert "transition" in draft.likely_risks[0].lower()
    assert "proof" in draft.discriminator_candidates[0].lower()
    assert "packet" in draft.packet_implications[0].lower()
    assert "follow up" in draft.action_candidates[0].lower()
    assert draft.assumptions
    assert draft.confidence_notes
    assert draft.gaps
    assert draft.follow_up_questions
    assert draft.trusted_opportunity_knowledge_updated is False


def _write_reference_note(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
