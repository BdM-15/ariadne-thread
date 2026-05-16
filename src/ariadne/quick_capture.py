from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.evidence import EvidenceItem, LocalEvidenceStore, create_source_evidence
from ariadne.reference_wiki import ReferenceWiki, ReferenceWikiInfluence


class RawCaptureStatus(StrEnum):
    CAPTURED = "captured"


class RawCaptureSourceType(StrEnum):
    MANUAL_NOTE = "manual_note"
    PASTED_TEXT = "pasted_text"
    UPLOADED_TEXT = "uploaded_text"


class ProposedDestination(StrEnum):
    EVIDENCE_ITEM_REVIEW = "evidence_item_review"
    ACTION_PLAN_ITEM_REVIEW = "action_plan_item_review"


class ProposalStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"
    ROUTED = "routed"


class CaptureReviewStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"


class CaptureIntelligenceDraftStatus(StrEnum):
    PENDING_REVIEW = "pending_review"


class CaptureIntelligenceDraftPartType(StrEnum):
    INFERRED_CLAIM = "inferred_claim"
    LIKELY_RISK = "likely_risk"
    DISCRIMINATOR_CANDIDATE = "discriminator_candidate"
    PACKET_IMPLICATION = "packet_implication"
    ACTION_CANDIDATE = "action_candidate"
    FOLLOW_UP_QUESTION = "follow_up_question"


class RawCaptureSourceMetadata(BaseModel):
    source_type: RawCaptureSourceType
    filename: str | None = None
    mime_type: str | None = None
    content_type: str | None = None
    byte_size: int | None = None
    intake_status: str | None = None
    source_ref: str | None = None
    warnings: tuple[str, ...] = ()


class RawCaptureItem(BaseModel):
    id: str
    content: str
    opportunity_id: str | None = None
    source_metadata: RawCaptureSourceMetadata | None = None
    status: RawCaptureStatus = RawCaptureStatus.CAPTURED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CaptureReviewProposal(BaseModel):
    id: str
    destination: ProposedDestination
    status: ProposalStatus = ProposalStatus.PENDING_REVIEW
    proposed_content: str
    evidence: EvidenceItem | None = None


class CaptureIntelligenceDraftPart(BaseModel):
    id: str
    part_type: CaptureIntelligenceDraftPartType
    content: str
    recommended_route: str
    suggested_skill_chain: tuple[str, ...] = ()
    review_required: bool = True


class CaptureIntelligenceDraft(BaseModel):
    id: str
    raw_item_id: str
    opportunity_id: str | None = None
    status: CaptureIntelligenceDraftStatus = (
        CaptureIntelligenceDraftStatus.PENDING_REVIEW
    )
    raw_source_content: str
    inferred_claims: tuple[str, ...]
    reference_influences: tuple[ReferenceWikiInfluence, ...] = ()
    assumptions: tuple[str, ...]
    confidence_notes: tuple[str, ...]
    likely_risks: tuple[str, ...]
    discriminator_candidates: tuple[str, ...]
    packet_implications: tuple[str, ...]
    action_candidates: tuple[str, ...]
    gaps: tuple[str, ...]
    follow_up_questions: tuple[str, ...]
    intelligence_pieces: tuple[CaptureIntelligenceDraftPart, ...] = ()
    trusted_opportunity_knowledge_updated: bool = False


class CaptureReviewDecision(BaseModel):
    id: str
    proposal_id: str | None = None
    raw_item_id: str
    draft_id: str | None = None
    destination: ProposedDestination | None = None
    status: ProposalStatus
    reviewer_rationale: str | None = None
    discard_reason: str | None = None
    evidence: EvidenceItem | None = None
    routed_follow_up_questions: tuple[str, ...] = ()
    trusted_evidence_written: bool = False
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CaptureReview(BaseModel):
    raw_item_id: str
    opportunity_id: str | None = None
    status: CaptureReviewStatus = CaptureReviewStatus.NEEDS_REVIEW
    proposals: tuple[CaptureReviewProposal, ...]
    reference_influences: tuple[ReferenceWikiInfluence, ...] = ()
    intelligence_draft: CaptureIntelligenceDraft | None = None
    trusted_opportunity_knowledge_updated: bool = False


def capture_raw_item(
    content: str,
    *,
    opportunity_id: str | None = None,
    raw_item_id: str | None = None,
    source_metadata: RawCaptureSourceMetadata | None = None,
) -> RawCaptureItem:
    return RawCaptureItem(
        id=raw_item_id or f"raw_{uuid4().hex}",
        content=content,
        opportunity_id=opportunity_id,
        source_metadata=source_metadata,
    )


def capture_pasted_text(
    content: str,
    *,
    opportunity_id: str | None = None,
    raw_item_id: str | None = None,
) -> RawCaptureItem:
    item_id = raw_item_id or f"raw_{uuid4().hex}"
    return capture_raw_item(
        content,
        opportunity_id=opportunity_id,
        raw_item_id=item_id,
        source_metadata=RawCaptureSourceMetadata(
            source_type=RawCaptureSourceType.PASTED_TEXT,
            content_type="text",
            byte_size=len(content.encode("utf-8")),
            intake_status="ready_for_quick_capture",
            source_ref=f"pasted:{item_id}",
        ),
    )


def capture_raw_item_from_upload(
    content: str,
    *,
    filename: str | None,
    mime_type: str | None,
    content_type: str,
    byte_size: int,
    opportunity_id: str | None = None,
    raw_item_id: str | None = None,
    source_ref: str | None = None,
    warnings: tuple[str, ...] = (),
) -> RawCaptureItem:
    item_id = raw_item_id or f"raw_{uuid4().hex}"
    return capture_raw_item(
        content,
        opportunity_id=opportunity_id,
        raw_item_id=item_id,
        source_metadata=RawCaptureSourceMetadata(
            source_type=RawCaptureSourceType.UPLOADED_TEXT,
            filename=filename,
            mime_type=mime_type,
            content_type=content_type,
            byte_size=byte_size,
            intake_status="ready_for_quick_capture",
            source_ref=source_ref or f"upload:{item_id}",
            warnings=warnings,
        ),
    )


def process_raw_capture_item(
    raw_item: RawCaptureItem,
    *,
    reference_wiki: ReferenceWiki | None = None,
) -> CaptureReview:
    destinations = [ProposedDestination.EVIDENCE_ITEM_REVIEW]
    if _looks_actionable(raw_item.content):
        destinations.append(ProposedDestination.ACTION_PLAN_ITEM_REVIEW)

    reference_influences = (
        reference_wiki.find_influences(raw_item.content) if reference_wiki else ()
    )
    intelligence_draft = create_capture_intelligence_draft(
        raw_item,
        reference_influences=reference_influences,
    )

    return CaptureReview(
        raw_item_id=raw_item.id,
        opportunity_id=raw_item.opportunity_id,
        reference_influences=reference_influences,
        intelligence_draft=intelligence_draft,
        proposals=tuple(
            CaptureReviewProposal(
                id=f"proposal_{uuid4().hex}",
                destination=destination,
                proposed_content=raw_item.content,
                evidence=(
                    create_source_evidence(
                        content=raw_item.content,
                        source_ref=_source_ref_for_raw_item(raw_item),
                        opportunity_id=raw_item.opportunity_id,
                    )
                    if destination is ProposedDestination.EVIDENCE_ITEM_REVIEW
                    else None
                ),
            )
            for destination in destinations
        ),
    )


def create_capture_intelligence_draft(
    raw_item: RawCaptureItem,
    *,
    reference_influences: tuple[ReferenceWikiInfluence, ...] = (),
) -> CaptureIntelligenceDraft:
    content = raw_item.content
    lowered = content.lower()
    draft_id = f"draft_{uuid4().hex}"
    inferred_claims = _infer_claims(lowered)
    likely_risks = _infer_likely_risks(lowered)
    discriminator_candidates = _infer_discriminator_candidates(lowered)
    packet_implications = _infer_packet_implications(lowered)
    action_candidates = _infer_action_candidates(content)
    follow_up_questions = _infer_follow_up_questions(lowered)
    return CaptureIntelligenceDraft(
        id=draft_id,
        raw_item_id=raw_item.id,
        opportunity_id=raw_item.opportunity_id,
        raw_source_content=content,
        inferred_claims=inferred_claims,
        reference_influences=reference_influences,
        assumptions=_infer_assumptions(reference_influences),
        confidence_notes=_infer_confidence_notes(reference_influences),
        likely_risks=likely_risks,
        discriminator_candidates=discriminator_candidates,
        packet_implications=packet_implications,
        action_candidates=action_candidates,
        gaps=_infer_gaps(lowered),
        follow_up_questions=follow_up_questions,
        intelligence_pieces=_build_intelligence_pieces(
            draft_id=draft_id,
            inferred_claims=inferred_claims,
            likely_risks=likely_risks,
            discriminator_candidates=discriminator_candidates,
            packet_implications=packet_implications,
            action_candidates=action_candidates,
            follow_up_questions=follow_up_questions,
        ),
    )


def _build_intelligence_pieces(
    *,
    draft_id: str,
    inferred_claims: tuple[str, ...],
    likely_risks: tuple[str, ...],
    discriminator_candidates: tuple[str, ...],
    packet_implications: tuple[str, ...],
    action_candidates: tuple[str, ...],
    follow_up_questions: tuple[str, ...],
) -> tuple[CaptureIntelligenceDraftPart, ...]:
    pieces: list[CaptureIntelligenceDraftPart] = []
    for part_type, items in (
        (CaptureIntelligenceDraftPartType.INFERRED_CLAIM, inferred_claims),
        (CaptureIntelligenceDraftPartType.LIKELY_RISK, likely_risks),
        (
            CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE,
            discriminator_candidates,
        ),
        (CaptureIntelligenceDraftPartType.PACKET_IMPLICATION, packet_implications),
        (CaptureIntelligenceDraftPartType.ACTION_CANDIDATE, action_candidates),
        (CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION, follow_up_questions),
    ):
        for index, item in enumerate(items, start=1):
            route, skill_chain = _suggest_piece_route(part_type, item)
            pieces.append(
                CaptureIntelligenceDraftPart(
                    id=f"{draft_id}_{part_type.value}_{index}",
                    part_type=part_type,
                    content=item,
                    recommended_route=route,
                    suggested_skill_chain=skill_chain,
                )
            )
    return tuple(pieces)


def _suggest_piece_route(
    part_type: CaptureIntelligenceDraftPartType,
    content: str,
) -> tuple[str, tuple[str, ...]]:
    lowered = content.lower()
    if part_type is CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION and (
        "customer" in lowered or "transition" in lowered
    ):
        return "customer_engagement_to_call_plan", (
            "guided_capture_mentor",
            "call_plan_builder",
        )
    if part_type is CaptureIntelligenceDraftPartType.ACTION_CANDIDATE:
        return "capture_action_plan_review", (
            "guided_capture_mentor",
            "action_plan_update",
        )
    if part_type is CaptureIntelligenceDraftPartType.PACKET_IMPLICATION:
        return "packet_field_review", ("packet_field_review",)
    if part_type is CaptureIntelligenceDraftPartType.LIKELY_RISK:
        return "risk_and_gap_review", ("capture_strategy_review",)
    if part_type is CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE:
        return "discriminator_evidence_review", ("capture_strategy_review",)
    return "evidence_or_knowledge_review", ("guided_capture_mentor",)


def accept_capture_review_proposal(
    review: CaptureReview,
    proposal_id: str,
    *,
    evidence_store: LocalEvidenceStore,
    reviewer_rationale: str | None = None,
) -> CaptureReviewDecision:
    proposal = _find_review_proposal(review, proposal_id)
    if proposal.destination is not ProposedDestination.EVIDENCE_ITEM_REVIEW:
        raise ValueError("only evidence review proposals can write source evidence")
    if proposal.evidence is None:
        raise ValueError("evidence review proposal is missing evidence draft")

    evidence = EvidenceItem.model_validate(
        proposal.evidence.model_dump()
        | {
            "raw_item_id": review.raw_item_id,
            "draft_id": _review_draft_id(review),
            "rationale": _accepted_evidence_rationale(review, reviewer_rationale),
        }
    )
    written = evidence_store.write(evidence)
    return CaptureReviewDecision(
        id=f"decision_{uuid4().hex}",
        proposal_id=proposal.id,
        raw_item_id=review.raw_item_id,
        draft_id=_review_draft_id(review),
        destination=proposal.destination,
        status=ProposalStatus.ACCEPTED,
        reviewer_rationale=reviewer_rationale,
        evidence=written,
        trusted_evidence_written=True,
    )


def discard_capture_review_proposal(
    review: CaptureReview,
    proposal_id: str,
    *,
    discard_reason: str,
) -> CaptureReviewDecision:
    proposal = _find_review_proposal(review, proposal_id)
    return CaptureReviewDecision(
        id=f"decision_{uuid4().hex}",
        proposal_id=proposal.id,
        raw_item_id=review.raw_item_id,
        draft_id=_review_draft_id(review),
        destination=proposal.destination,
        status=ProposalStatus.DISCARDED,
        discard_reason=discard_reason,
        trusted_evidence_written=False,
    )


def route_capture_follow_up_questions(
    review: CaptureReview,
    *,
    reviewer_rationale: str | None = None,
    selected_questions: tuple[str, ...] | None = None,
) -> CaptureReviewDecision:
    if review.intelligence_draft is None:
        raise ValueError("capture review has no intelligence draft to route")
    questions = selected_questions or review.intelligence_draft.follow_up_questions
    return CaptureReviewDecision(
        id=f"decision_{uuid4().hex}",
        raw_item_id=review.raw_item_id,
        draft_id=review.intelligence_draft.id,
        status=ProposalStatus.ROUTED,
        reviewer_rationale=reviewer_rationale,
        routed_follow_up_questions=questions,
        trusted_evidence_written=False,
    )


def _find_review_proposal(
    review: CaptureReview,
    proposal_id: str,
) -> CaptureReviewProposal:
    for proposal in review.proposals:
        if proposal.id == proposal_id:
            return proposal
    raise ValueError(f"unknown review proposal: {proposal_id}")


def _source_ref_for_raw_item(raw_item: RawCaptureItem) -> str:
    if raw_item.source_metadata and raw_item.source_metadata.source_ref:
        return raw_item.source_metadata.source_ref
    return f"raw_capture:{raw_item.id}"


def _review_draft_id(review: CaptureReview) -> str | None:
    if review.intelligence_draft is None:
        return None
    return review.intelligence_draft.id


def _accepted_evidence_rationale(
    review: CaptureReview,
    reviewer_rationale: str | None,
) -> tuple[str, ...]:
    rationale: list[str] = []
    if reviewer_rationale:
        rationale.append(reviewer_rationale)
    if review.intelligence_draft is not None:
        rationale.extend(
            f"Draft claim: {claim}" for claim in review.intelligence_draft.inferred_claims
        )
        rationale.extend(
            f"Draft confidence: {note}"
            for note in review.intelligence_draft.confidence_notes
        )
    return tuple(rationale or ("Reviewer accepted raw capture item as source evidence.",))


def _looks_actionable(content: str) -> bool:
    lowered = content.lower()
    return any(
        marker in lowered
        for marker in ("need ", "needs ", "follow up", "next step", "action")
    )


def _infer_claims(lowered_content: str) -> tuple[str, ...]:
    claims: list[str] = []
    if "transition" in lowered_content:
        claims.append("Raw note signals transition concerns that need capture review.")
    if "incumbent" in lowered_content:
        claims.append("Raw note points to incumbent performance or positioning concerns.")
    if "customer" in lowered_content:
        claims.append("Raw note contains customer feedback that may shape strategy.")
    return tuple(claims or ("Raw note contains capture-relevant intelligence for review.",))


def _infer_assumptions(
    reference_influences: tuple[ReferenceWikiInfluence, ...],
) -> tuple[str, ...]:
    influence_note = (
        f"Reference context includes {len(reference_influences)} influence(s)."
        if reference_influences
        else "No Reference Wiki influence validated this draft yet."
    )
    return (
        "Draft treats raw note as unverified user-provided source material.",
        influence_note,
    )


def _infer_confidence_notes(
    reference_influences: tuple[ReferenceWikiInfluence, ...],
) -> tuple[str, ...]:
    if reference_influences:
        return (
            "Medium confidence: raw note language aligns with Reference Wiki context.",
        )
    return ("Low confidence: draft needs reference or evidence support before promotion.",)


def _infer_likely_risks(lowered_content: str) -> tuple[str, ...]:
    risks: list[str] = []
    if "transition" in lowered_content:
        risks.append("Transition risk may be a customer concern or evaluation weakness.")
    if "weak" in lowered_content or "complaint" in lowered_content:
        risks.append("Weak performance signal may need mitigation before gate review.")
    if "incumbent" in lowered_content:
        risks.append("Incumbent positioning may create competitive or ghosting implications.")
    return tuple(risks or ("Unvalidated capture risk may need follow-up evidence.",))


def _infer_discriminator_candidates(lowered_content: str) -> tuple[str, ...]:
    if "proof" in lowered_content:
        return ("Proof points could become discriminators if backed by evidence.",)
    if "weak" in lowered_content or "transition" in lowered_content:
        return ("Transition mitigation could become a discriminator if substantiated.",)
    return ("Potential discriminator needs clearer customer pain and evidence.",)


def _infer_packet_implications(lowered_content: str) -> tuple[str, ...]:
    implications: list[str] = []
    if "packet" in lowered_content or "risk" in lowered_content:
        implications.append(
            "Packet may need a risk, mitigation, or evidence gap entry for this signal."
        )
    if "customer" in lowered_content:
        implications.append("Customer Context section may need updated pain-point evidence.")
    return tuple(implications or ("Packet impact needs reviewer classification.",))


def _infer_action_candidates(content: str) -> tuple[str, ...]:
    lowered_content = content.lower()
    if "follow up" in lowered_content:
        return ("Follow up with named owner or PM to validate raw customer signal.",)
    if _looks_actionable(content):
        return ("Create action candidate to validate and route this capture signal.",)
    return ("Ask reviewer whether this raw signal requires an action item.",)


def _infer_gaps(lowered_content: str) -> tuple[str, ...]:
    gaps = ["Need reviewer validation before promotion into trusted knowledge."]
    if "customer" in lowered_content:
        gaps.append("Need source details: who said it, when, and in what context.")
    if "proof" in lowered_content:
        gaps.append("Need supporting proof points before using as discriminator.")
    return tuple(gaps)


def _infer_follow_up_questions(lowered_content: str) -> tuple[str, ...]:
    questions = ["Who is the source and how reliable is this signal?"]
    if "transition" in lowered_content:
        questions.append("What transition evidence or mitigation would satisfy the customer?")
    if "incumbent" in lowered_content:
        questions.append("Which incumbent weakness can be substantiated without overclaiming?")
    return tuple(questions)
