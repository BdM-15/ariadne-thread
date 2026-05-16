from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ariadne.action_plans import ActionPlanItem
from ariadne.capabilities import CapabilityCatalog, discover_local_capability_catalog
from ariadne.command_center import render_command_center_shell
from ariadne.config import RuntimeSettings
from ariadne.draft_promotion import (
    DraftPartPromotionDecision,
    discard_draft_part_promotion,
    promote_action_candidate_to_plan_item,
    promote_packet_implication_to_field_answer,
)
from ariadne.document_intake import (
    DocumentIntakeCandidate,
    DocumentIntakeStatus,
    classify_uploaded_source_material,
)
from ariadne.evidence import LocalEvidenceStore
from ariadne.packet_knowledge import (
    PacketFieldAnswer,
    PacketFieldReview,
    build_demo_packet_field_review,
)
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
    CaptureIntelligenceDraftPartType,
    CaptureReview,
    CaptureReviewDecision,
    ProposedDestination,
    RawCaptureItem,
    accept_capture_review_proposal,
    capture_pasted_text,
    capture_raw_item,
    capture_raw_item_from_upload,
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


class PromotionType(StrEnum):
    ACTION_PLAN_ITEM = "action_plan_item"
    PACKET_FIELD_ANSWER = "packet_field_answer"
    DISCARD = "discard"


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


class QuickCaptureSourceMaterialRequest(BaseModel):
    content: str
    opportunity_id: str | None = None
    raw_item_id: str | None = None


class QuickCaptureSourceMaterialResponse(BaseModel):
    raw_item: RawCaptureItem
    review: CaptureReview


class QuickCaptureUploadResponse(BaseModel):
    status: DocumentIntakeStatus
    raw_item: RawCaptureItem | None = None
    review: CaptureReview | None = None
    intake_candidate: DocumentIntakeCandidate | None = None


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


class CapturePromotionRequest(BaseModel):
    content: str
    opportunity_id: str | None = None
    raw_item_id: str | None = None
    promotion_type: PromotionType
    draft_part_id: str | None = None
    field_key: str = "risks"
    reviewer_rationale: str
    edited_content: str | None = None
    evidence_ids: tuple[str, ...] = ()
    confidence: float | None = Field(default=None, ge=0, le=1)
    discard_reason: str | None = None


class CapturePromotionResponse(BaseModel):
    review: CaptureReview
    action_item: ActionPlanItem | None = None
    packet_answer: PacketFieldAnswer | None = None
    decision: DraftPartPromotionDecision | None = None


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

    @app.post("/api/quick-capture/source-material")
    def quick_capture_source_material(
        request: QuickCaptureSourceMaterialRequest,
    ) -> QuickCaptureSourceMaterialResponse:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="source material is empty")
        wiki = load_reference_wiki(
            _resolve_runtime_path(runtime_settings.ariadne_reference_wiki_dir)
        )
        raw_item = capture_pasted_text(
            request.content,
            opportunity_id=request.opportunity_id,
            raw_item_id=request.raw_item_id,
        )
        review = process_raw_capture_item(raw_item, reference_wiki=wiki)
        return QuickCaptureSourceMaterialResponse(raw_item=raw_item, review=review)

    @app.post("/api/quick-capture/uploads")
    async def quick_capture_upload(
        file: UploadFile = File(...),
        opportunity_id: str | None = Form(default=None),
    ) -> QuickCaptureUploadResponse:
        source_material = classify_uploaded_source_material(
            filename=file.filename,
            mime_type=file.content_type,
            content=await file.read(),
        )
        if source_material.intake_candidate is not None:
            return QuickCaptureUploadResponse(
                status=source_material.status,
                intake_candidate=source_material.intake_candidate,
            )
        if source_material.text is None:
            raise HTTPException(status_code=400, detail="upload text was not readable")

        wiki = load_reference_wiki(
            _resolve_runtime_path(runtime_settings.ariadne_reference_wiki_dir)
        )
        raw_item = capture_raw_item_from_upload(
            source_material.text,
            filename=source_material.filename,
            mime_type=source_material.mime_type,
            content_type=source_material.content_type.value,
            byte_size=source_material.byte_size,
            source_ref=source_material.source_ref,
            warnings=source_material.warnings,
            opportunity_id=opportunity_id,
        )
        review = process_raw_capture_item(raw_item, reference_wiki=wiki)
        return QuickCaptureUploadResponse(
            status=source_material.status,
            raw_item=raw_item,
            review=review,
        )

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

    @app.post("/api/quick-capture/promotions")
    def quick_capture_promotion(
        request: CapturePromotionRequest,
    ) -> CapturePromotionResponse:
        wiki = load_reference_wiki(
            _resolve_runtime_path(runtime_settings.ariadne_reference_wiki_dir)
        )
        raw_item = capture_raw_item(
            request.content,
            opportunity_id=request.opportunity_id,
            raw_item_id=request.raw_item_id,
        )
        review = process_raw_capture_item(raw_item, reference_wiki=wiki)
        try:
            if request.promotion_type is PromotionType.ACTION_PLAN_ITEM:
                action_item = promote_action_candidate_to_plan_item(
                    review,
                    draft_part_id=request.draft_part_id
                    or _draft_part_id_for_type(
                        review,
                        CaptureIntelligenceDraftPartType.ACTION_CANDIDATE,
                    ),
                    reviewer_rationale=request.reviewer_rationale,
                    edited_content=request.edited_content,
                    evidence_ids=request.evidence_ids,
                )
                return CapturePromotionResponse(review=review, action_item=action_item)
            if request.promotion_type is PromotionType.PACKET_FIELD_ANSWER:
                packet_answer = promote_packet_implication_to_field_answer(
                    review,
                    draft_part_id=request.draft_part_id
                    or _draft_part_id_for_type(
                        review,
                        CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
                    ),
                    field_key=request.field_key,
                    reviewer_rationale=request.reviewer_rationale,
                    edited_value=request.edited_content,
                    evidence_ids=request.evidence_ids,
                    confidence=request.confidence,
                )
                return CapturePromotionResponse(review=review, packet_answer=packet_answer)

            decision = discard_draft_part_promotion(
                review,
                draft_part_id=request.draft_part_id
                or _draft_part_id_for_type(
                    review,
                    CaptureIntelligenceDraftPartType.INFERRED_CLAIM,
                ),
                discard_reason=request.discard_reason or request.reviewer_rationale,
            )
            return CapturePromotionResponse(review=review, decision=decision)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

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


def _draft_part_id_for_type(
    review: CaptureReview,
    part_type: CaptureIntelligenceDraftPartType,
) -> str:
    if review.intelligence_draft is None:
        raise ValueError("capture review has no intelligence draft")
    for part in review.intelligence_draft.intelligence_pieces:
        if part.part_type is part_type:
            return part.id
    raise ValueError(f"capture review has no draft part for {part_type.value}")
