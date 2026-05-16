from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ariadne.capabilities import CapabilityCatalog, discover_local_capability_catalog
from ariadne.command_center import render_command_center_shell
from ariadne.config import RuntimeSettings
from ariadne.evidence import LocalEvidenceStore
from ariadne.packet_knowledge import PacketFieldReview, build_demo_packet_field_review
from ariadne.packet_review import (
    build_demo_packet_briefing_view,
    build_demo_packet_coverage_view,
    render_demo_packet_review_shell,
)
from ariadne.packets import (
    BriefingView,
    CoverageView,
)
from ariadne.quick_capture import (
    CaptureIntelligenceDraft,
    CaptureReview,
    CaptureReviewDecision,
    ProposedDestination,
    accept_capture_review_proposal,
    capture_raw_item,
    create_capture_intelligence_draft,
    discard_capture_review_proposal,
    process_raw_capture_item,
    route_capture_follow_up_questions,
)
from ariadne.reference_wiki import ReferenceWikiInfluence, load_reference_wiki


class ReviewDecisionAction(StrEnum):
    ACCEPT_EVIDENCE = "accept_evidence"
    DISCARD_PROPOSAL = "discard_proposal"
    ROUTE_FOLLOW_UP_QUESTIONS = "route_follow_up_questions"


class ReferenceInfluenceRequest(BaseModel):
    content: str
    limit: int = Field(default=7, ge=1, le=7)


class ReferenceInfluenceResponse(BaseModel):
    influences: tuple[ReferenceWikiInfluence, ...]


class CaptureIntelligenceDraftRequest(BaseModel):
    content: str
    opportunity_id: str | None = None
    limit: int = Field(default=7, ge=1, le=7)


class CaptureIntelligenceDraftResponse(BaseModel):
    draft: CaptureIntelligenceDraft


class CaptureReviewDecisionRequest(BaseModel):
    content: str
    opportunity_id: str | None = None
    raw_item_id: str | None = None
    action: ReviewDecisionAction
    proposal_destination: ProposedDestination = ProposedDestination.EVIDENCE_ITEM_REVIEW
    reviewer_rationale: str | None = None
    discard_reason: str | None = None


class CaptureReviewDecisionResponse(BaseModel):
    review: CaptureReview
    decision: CaptureReviewDecision
    evidence_store_count: int


def create_app(settings: RuntimeSettings | None = None) -> FastAPI:
    runtime_settings = settings or RuntimeSettings.from_env_file()
    app = FastAPI(title=runtime_settings.public_app_name)

    @app.get("/api/runtime")
    def runtime_status() -> dict[str, object]:
        return {
            "app_name": runtime_settings.public_app_name,
            "environment": runtime_settings.ariadne_env,
            "workspace": runtime_settings.ariadne_workspace,
            "host": runtime_settings.host,
            "port": runtime_settings.port,
            "local_url": runtime_settings.local_url,
            "status": "online",
        }

    @app.get("/", response_class=HTMLResponse)
    def command_center_status() -> str:
        return render_command_center_shell(runtime_settings)

    @app.get("/packets/review", response_class=HTMLResponse)
    def packet_review(stage: str = "MS2", slide: int = 4) -> str:
        return render_demo_packet_review_shell(stage=stage, slide=slide)

    @app.get("/api/packets/review/briefing")
    def packet_review_briefing() -> BriefingView:
        return build_demo_packet_briefing_view()

    @app.get("/api/packets/review/coverage")
    def packet_review_coverage() -> CoverageView:
        return build_demo_packet_coverage_view()

    @app.get("/api/packets/review/knowledge-slots")
    def packet_review_knowledge_slots() -> PacketFieldReview:
        return build_demo_packet_field_review()

    @app.get("/api/capabilities/catalog")
    def capability_catalog() -> CapabilityCatalog:
        return discover_local_capability_catalog(Path.cwd())

    @app.post("/api/quick-capture/reference-influences")
    def quick_capture_reference_influences(
        request: ReferenceInfluenceRequest,
    ) -> ReferenceInfluenceResponse:
        wiki = load_reference_wiki(
            _resolve_runtime_path(runtime_settings.ariadne_reference_wiki_dir)
        )
        return ReferenceInfluenceResponse(
            influences=wiki.find_influences(request.content, limit=request.limit)
        )

    @app.post("/api/quick-capture/intelligence-drafts")
    def quick_capture_intelligence_draft(
        request: CaptureIntelligenceDraftRequest,
    ) -> CaptureIntelligenceDraftResponse:
        wiki = load_reference_wiki(
            _resolve_runtime_path(runtime_settings.ariadne_reference_wiki_dir)
        )
        raw_item = capture_raw_item(
            request.content,
            opportunity_id=request.opportunity_id,
        )
        draft = create_capture_intelligence_draft(
            raw_item,
            reference_influences=wiki.find_influences(
                request.content,
                limit=request.limit,
            ),
        )
        return CaptureIntelligenceDraftResponse(draft=draft)

    @app.post("/api/quick-capture/review-decisions")
    def quick_capture_review_decision(
        request: CaptureReviewDecisionRequest,
    ) -> CaptureReviewDecisionResponse:
        wiki = load_reference_wiki(
            _resolve_runtime_path(runtime_settings.ariadne_reference_wiki_dir)
        )
        raw_item = capture_raw_item(
            request.content,
            opportunity_id=request.opportunity_id,
            raw_item_id=request.raw_item_id,
        )
        review = process_raw_capture_item(
            raw_item,
            reference_wiki=wiki,
        )
        evidence_store = LocalEvidenceStore(
            _resolve_runtime_path(runtime_settings.ariadne_evidence_dir)
        )
        try:
            if request.action is ReviewDecisionAction.ACCEPT_EVIDENCE:
                decision = accept_capture_review_proposal(
                    review,
                    _proposal_id_for_destination(review, request.proposal_destination),
                    evidence_store=evidence_store,
                    reviewer_rationale=request.reviewer_rationale,
                )
            elif request.action is ReviewDecisionAction.DISCARD_PROPOSAL:
                decision = discard_capture_review_proposal(
                    review,
                    _proposal_id_for_destination(review, request.proposal_destination),
                    discard_reason=request.discard_reason
                    or "Reviewer discarded this draft part.",
                )
            else:
                decision = route_capture_follow_up_questions(
                    review,
                    reviewer_rationale=request.reviewer_rationale,
                )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        return CaptureReviewDecisionResponse(
            review=review,
            decision=decision,
            evidence_store_count=len(evidence_store.list()),
        )

    return app


def _resolve_runtime_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _proposal_id_for_destination(
    review: CaptureReview,
    destination: ProposedDestination,
) -> str:
    for proposal in review.proposals:
        if proposal.destination is destination:
            return proposal.id
    raise ValueError(f"capture review has no proposal for {destination.value}")
