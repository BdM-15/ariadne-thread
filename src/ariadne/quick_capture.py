from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.evidence import EvidenceItem, create_source_evidence
from ariadne.reference_wiki import ReferenceWiki, ReferenceWikiInfluence


class RawCaptureStatus(StrEnum):
    CAPTURED = "captured"


class ProposedDestination(StrEnum):
    EVIDENCE_ITEM_REVIEW = "evidence_item_review"
    ACTION_PLAN_ITEM_REVIEW = "action_plan_item_review"


class ProposalStatus(StrEnum):
    PENDING_REVIEW = "pending_review"


class CaptureReviewStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"


class CaptureIntelligenceDraftStatus(StrEnum):
    PENDING_REVIEW = "pending_review"


class RawCaptureItem(BaseModel):
    id: str
    content: str
    opportunity_id: str | None = None
    status: RawCaptureStatus = RawCaptureStatus.CAPTURED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CaptureReviewProposal(BaseModel):
    id: str
    destination: ProposedDestination
    status: ProposalStatus = ProposalStatus.PENDING_REVIEW
    proposed_content: str
    evidence: EvidenceItem | None = None


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
    trusted_opportunity_knowledge_updated: bool = False


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
) -> RawCaptureItem:
    return RawCaptureItem(
        id=raw_item_id or f"raw_{uuid4().hex}",
        content=content,
        opportunity_id=opportunity_id,
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
                        source_ref=f"raw_capture:{raw_item.id}",
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
    return CaptureIntelligenceDraft(
        id=f"draft_{uuid4().hex}",
        raw_item_id=raw_item.id,
        opportunity_id=raw_item.opportunity_id,
        raw_source_content=content,
        inferred_claims=_infer_claims(lowered),
        reference_influences=reference_influences,
        assumptions=_infer_assumptions(reference_influences),
        confidence_notes=_infer_confidence_notes(reference_influences),
        likely_risks=_infer_likely_risks(lowered),
        discriminator_candidates=_infer_discriminator_candidates(lowered),
        packet_implications=_infer_packet_implications(lowered),
        action_candidates=_infer_action_candidates(content),
        gaps=_infer_gaps(lowered),
        follow_up_questions=_infer_follow_up_questions(lowered),
    )


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
