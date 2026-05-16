from ariadne.evidence import EvidenceKind, LocalEvidenceStore
from ariadne.quick_capture import (
    CaptureIntelligenceDraftStatus,
    CaptureReviewStatus,
    ProposalStatus,
    ProposedDestination,
    accept_capture_review_proposal,
    RawCaptureStatus,
    RawCaptureSourceType,
    capture_pasted_text,
    capture_raw_item,
    capture_raw_item_from_upload,
    discard_capture_review_proposal,
    process_raw_capture_item,
    route_capture_follow_up_questions,
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


def test_pasted_text_capture_preserves_source_metadata() -> None:
    raw_item = capture_pasted_text(
        "Customer pasted note says transition risk needs follow up.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_pasted_customer_note",
    )

    assert raw_item.source_metadata is not None
    assert raw_item.source_metadata.source_type is RawCaptureSourceType.PASTED_TEXT
    assert raw_item.source_metadata.intake_status == "ready_for_quick_capture"
    assert raw_item.source_metadata.byte_size == len(raw_item.content.encode("utf-8"))


def test_uploaded_markdown_capture_uses_same_draft_path_as_manual_notes() -> None:
    raw_item = capture_raw_item_from_upload(
        "# Call note\n\nCustomer says transition risk needs packet gap.",
        filename="customer-call.md",
        mime_type="text/markdown",
        content_type="markdown",
        byte_size=57,
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_uploaded_customer_call",
    )

    review = process_raw_capture_item(raw_item)

    assert raw_item.source_metadata is not None
    assert raw_item.source_metadata.source_type is RawCaptureSourceType.UPLOADED_TEXT
    assert raw_item.source_metadata.filename == "customer-call.md"
    assert review.raw_item_id == "raw_uploaded_customer_call"
    assert review.intelligence_draft is not None
    assert review.intelligence_draft.raw_source_content == raw_item.content
    assert "packet" in review.intelligence_draft.packet_implications[0].lower()


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


def test_intelligence_draft_breaks_outputs_into_reviewable_pieces() -> None:
    raw_item = capture_raw_item(
        "Customer says transition risk needs proof from PM before next call.",
        raw_item_id="raw_transition_skill_chain_note",
    )

    review = process_raw_capture_item(raw_item)
    draft = review.intelligence_draft

    assert draft is not None
    assert draft.intelligence_pieces
    follow_up_piece = next(
        piece
        for piece in draft.intelligence_pieces
        if piece.part_type == "follow_up_question"
        and piece.recommended_route == "customer_engagement_to_call_plan"
    )
    assert follow_up_piece.id.startswith(f"{draft.id}_follow_up_question_")
    assert "transition" in follow_up_piece.content.lower()
    assert follow_up_piece.suggested_skill_chain == (
        "guided_capture_mentor",
        "call_plan_builder",
    )
    assert follow_up_piece.review_required is True


def test_accepting_evidence_review_proposal_writes_source_evidence_with_provenance(
    tmp_path,
) -> None:
    store = LocalEvidenceStore(tmp_path / "evidence")
    raw_item = capture_raw_item(
        "Customer says incumbent response times are weak.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_customer_response_note",
    )
    review = process_raw_capture_item(raw_item)
    evidence_proposal = next(
        proposal
        for proposal in review.proposals
        if proposal.destination is ProposedDestination.EVIDENCE_ITEM_REVIEW
    )

    assert store.list() == []

    decision = accept_capture_review_proposal(
        review,
        evidence_proposal.id,
        evidence_store=store,
        reviewer_rationale="Customer call note accepted as source evidence.",
    )

    assert decision.status is ProposalStatus.ACCEPTED
    assert decision.proposal_id == evidence_proposal.id
    assert decision.raw_item_id == "raw_customer_response_note"
    assert decision.draft_id == review.intelligence_draft.id
    assert decision.evidence is not None
    assert decision.evidence.kind is EvidenceKind.SOURCE
    assert decision.evidence.raw_item_id == "raw_customer_response_note"
    assert decision.evidence.draft_id == review.intelligence_draft.id
    assert decision.evidence.rationale[0] == (
        "Customer call note accepted as source evidence."
    )
    assert store.list() == [decision.evidence]


def test_discarding_review_proposal_tracks_decision_without_writing_evidence(
    tmp_path,
) -> None:
    store = LocalEvidenceStore(tmp_path / "evidence")
    raw_item = capture_raw_item(
        "Customer signal is too vague to use yet. Need follow up.",
        raw_item_id="raw_vague_customer_signal",
    )
    review = process_raw_capture_item(raw_item)
    action_proposal = next(
        proposal
        for proposal in review.proposals
        if proposal.destination is ProposedDestination.ACTION_PLAN_ITEM_REVIEW
    )

    decision = discard_capture_review_proposal(
        review,
        action_proposal.id,
        discard_reason="Not actionable until the customer source is confirmed.",
    )

    assert decision.status is ProposalStatus.DISCARDED
    assert decision.proposal_id == action_proposal.id
    assert decision.raw_item_id == "raw_vague_customer_signal"
    assert decision.discard_reason == "Not actionable until the customer source is confirmed."
    assert decision.trusted_evidence_written is False
    assert decision.evidence is None
    assert store.list() == []


def test_follow_up_questions_can_be_explicitly_routed_without_writing_evidence(
    tmp_path,
) -> None:
    store = LocalEvidenceStore(tmp_path / "evidence")
    raw_item = capture_raw_item(
        "Customer says transition risk needs proof from PM.",
        raw_item_id="raw_transition_question",
    )
    review = process_raw_capture_item(raw_item)

    route = route_capture_follow_up_questions(
        review,
        reviewer_rationale="Need customer engagement prep before evidence promotion.",
    )

    assert route.raw_item_id == "raw_transition_question"
    assert route.draft_id == review.intelligence_draft.id
    assert route.status is ProposalStatus.ROUTED
    assert route.routed_follow_up_questions == review.intelligence_draft.follow_up_questions
    assert route.reviewer_rationale == (
        "Need customer engagement prep before evidence promotion."
    )
    assert route.trusted_evidence_written is False
    assert store.list() == []


def _write_reference_note(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
