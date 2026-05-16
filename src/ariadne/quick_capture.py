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


class CaptureReview(BaseModel):
    raw_item_id: str
    opportunity_id: str | None = None
    status: CaptureReviewStatus = CaptureReviewStatus.NEEDS_REVIEW
    proposals: tuple[CaptureReviewProposal, ...]
    reference_influences: tuple[ReferenceWikiInfluence, ...] = ()
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

    return CaptureReview(
        raw_item_id=raw_item.id,
        opportunity_id=raw_item.opportunity_id,
        reference_influences=reference_influences,
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


def _looks_actionable(content: str) -> bool:
    lowered = content.lower()
    return any(
        marker in lowered
        for marker in ("need ", "needs ", "follow up", "next step", "action")
    )
