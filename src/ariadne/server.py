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
    AcceptedDocumentEvidenceLink,
    AcceptedSourceSpanEvidenceResult,
    DocumentIntakeAdapterDeclaration,
    DocumentIntakeAdapterStatus,
    DocumentIntakeCaptureCandidate,
    DocumentIntakeCandidate,
    DocumentIntakeRecord,
    DocumentIntakeStatus,
    DocumentIntakeStore,
    KnowledgeNoteProjection,
    UploadedSourceMaterial,
    accept_source_spans_to_evidence,
    classify_uploaded_source_material,
    create_capture_intelligence_draft_from_extraction_bundle,
    create_document_intake_record,
    create_generic_extraction_bundle,
    create_knowledge_note_projection_from_accepted_evidence,
    create_review_gated_capture_candidates_from_extraction_bundle,
    list_document_intake_adapter_declarations,
)
from ariadne.evidence import EvidenceItem, LocalEvidenceStore
from ariadne.federal_data import (
    FederalDataCapabilityManifest,
    FederalDataProductStatus,
    list_federal_data_capability_manifests,
)
from ariadne.local_admin_model import request_local_admin_draft_assist
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


class DocumentIntakeUploadResponse(BaseModel):
    record: DocumentIntakeRecord


class DocumentIntakeQueueResponse(BaseModel):
    records: tuple[DocumentIntakeRecord, ...]


class DocumentIntakeExtractionDraftsResponse(BaseModel):
    drafts: tuple[CaptureIntelligenceDraft, ...]


class DocumentIntakeCaptureCandidatesResponse(BaseModel):
    candidates: tuple[DocumentIntakeCaptureCandidate, ...]


class DocumentIntakeCapabilitiesResponse(BaseModel):
    capabilities: tuple[DocumentIntakeAdapterDeclaration, ...]
    available_count: int
    deferred_count: int
    extraction_bundle_boundary: str = (
        "Document Intake adapters must produce reviewable Extraction Bundles; "
        "deferred declarations do not invoke external tools."
    )


class FederalDataCapabilitiesResponse(BaseModel):
    capabilities: tuple[FederalDataCapabilityManifest, ...]
    registered_count: int
    smoke_tested_count: int
    product_integrated_count: int
    deferred_product_workflow_count: int


class DocumentIntakeKnowledgeNoteProjectionRequest(BaseModel):
    extraction_bundle_id: str
    projection_id: str | None = None


class DocumentIntakeKnowledgeNoteProjectionResponse(BaseModel):
    projection: KnowledgeNoteProjection | None = None


class DocumentIntakeKnowledgeNoteProjectionsResponse(BaseModel):
    projections: tuple[KnowledgeNoteProjection, ...]


class DocumentIntakeReviewDecisionRequest(BaseModel):
    action: ReviewDecisionAction
    extraction_bundle_id: str
    source_span_ids: tuple[str, ...]
    reviewer_rationale: str
    draft_part_id: str | None = None
    evidence_content: str | None = None
    opportunity_id: str | None = None
    evidence_id: str | None = None


class DocumentIntakeReviewDecisionResponse(BaseModel):
    evidence: EvidenceItem
    accepted_link: AcceptedDocumentEvidenceLink
    duplicate: bool = False
    evidence_store_count: int


class DocumentIntakeSourceMaterialRequest(BaseModel):
    content: str
    filename: str | None = None
    mime_type: str | None = None
    opportunity_id: str | None = None


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
            "local_admin_model": {
                "enabled": runtime_settings.local_admin_model.enabled,
                "model": runtime_settings.local_admin_model.model,
                "ollama_base_url": runtime_settings.local_admin_model.ollama_base_url,
                "timeout_seconds": runtime_settings.local_admin_model.timeout_seconds,
            },
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

    @app.get("/api/document-intake/capabilities")
    def document_intake_capabilities() -> DocumentIntakeCapabilitiesResponse:
        capabilities = list_document_intake_adapter_declarations()
        return DocumentIntakeCapabilitiesResponse(
            capabilities=capabilities,
            available_count=sum(
                capability.status is DocumentIntakeAdapterStatus.AVAILABLE
                for capability in capabilities
            ),
            deferred_count=sum(
                capability.status is DocumentIntakeAdapterStatus.DEFERRED
                for capability in capabilities
            ),
        )

    @app.get("/api/federal-data/capabilities")
    def federal_data_capabilities() -> FederalDataCapabilitiesResponse:
        registry = list_federal_data_capability_manifests()
        capabilities = registry.capabilities
        return FederalDataCapabilitiesResponse(
            capabilities=capabilities,
            registered_count=sum(
                capability.product_status is FederalDataProductStatus.REGISTERED
                for capability in capabilities
            ),
            smoke_tested_count=sum(
                capability.product_status is FederalDataProductStatus.SMOKE_TESTED
                for capability in capabilities
            ),
            product_integrated_count=sum(
                capability.product_status is FederalDataProductStatus.PRODUCT_INTEGRATED
                for capability in capabilities
            ),
            deferred_product_workflow_count=sum(
                capability.product_status
                is FederalDataProductStatus.DEFERRED_PRODUCT_WORKFLOW
                for capability in capabilities
            ),
        )

    @app.get("/api/document-intake/queue")
    def document_intake_queue() -> DocumentIntakeQueueResponse:
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        return DocumentIntakeQueueResponse(records=tuple(store.list()))

    @app.get("/api/document-intake/extraction-drafts")
    def document_intake_extraction_drafts() -> DocumentIntakeExtractionDraftsResponse:
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        return DocumentIntakeExtractionDraftsResponse(
            drafts=tuple(
                create_capture_intelligence_draft_from_extraction_bundle(bundle)
                for bundle in store.list_extraction_bundles()
            )
        )

    @app.get("/api/document-intake/capture-candidates")
    def document_intake_capture_candidates() -> DocumentIntakeCaptureCandidatesResponse:
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        return DocumentIntakeCaptureCandidatesResponse(
            candidates=tuple(store.list_capture_candidates())
        )

    @app.get("/api/document-intake/knowledge-note-projections")
    def document_intake_knowledge_note_projections(
        bundle_id: str | None = None,
        intake_record_id: str | None = None,
        evidence_id: str | None = None,
    ) -> DocumentIntakeKnowledgeNoteProjectionsResponse:
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        return DocumentIntakeKnowledgeNoteProjectionsResponse(
            projections=tuple(
                store.list_knowledge_note_projections(
                    bundle_id=bundle_id,
                    intake_record_id=intake_record_id,
                    evidence_id=evidence_id,
                )
            )
        )

    @app.post("/api/document-intake/knowledge-note-projections")
    def generate_document_intake_knowledge_note_projection(
        request: DocumentIntakeKnowledgeNoteProjectionRequest,
    ) -> DocumentIntakeKnowledgeNoteProjectionResponse:
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        evidence_store = LocalEvidenceStore(
            _resolve_runtime_path(runtime_settings.ariadne_evidence_dir)
        )
        try:
            bundle = store.read_extraction_bundle(request.extraction_bundle_id)
            projection = create_knowledge_note_projection_from_accepted_evidence(
                bundle,
                intake_store=store,
                evidence_store=evidence_store,
                projection_id=request.projection_id,
            )
            if projection is None:
                raise HTTPException(
                    status_code=409,
                    detail="accepted document evidence is required before projection",
                )
            store.write_knowledge_note_projection(projection)
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="extraction bundle not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return DocumentIntakeKnowledgeNoteProjectionResponse(projection=projection)

    @app.post("/api/document-intake/review-decisions")
    def document_intake_review_decision(
        request: DocumentIntakeReviewDecisionRequest,
    ) -> DocumentIntakeReviewDecisionResponse:
        if request.action is not ReviewDecisionAction.ACCEPT_EVIDENCE:
            raise HTTPException(
                status_code=400,
                detail="document intake currently supports accept_evidence only",
            )
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        evidence_store = LocalEvidenceStore(
            _resolve_runtime_path(runtime_settings.ariadne_evidence_dir)
        )
        try:
            bundle = store.read_extraction_bundle(request.extraction_bundle_id)
            result = accept_source_spans_to_evidence(
                bundle,
                source_span_ids=request.source_span_ids,
                reviewer_rationale=request.reviewer_rationale,
                intake_store=store,
                evidence_store=evidence_store,
                draft_part_id=request.draft_part_id,
                evidence_content=request.evidence_content,
                opportunity_id=request.opportunity_id,
                evidence_id=request.evidence_id,
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="extraction bundle not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        return _document_intake_review_response(result, evidence_store)

    @app.post("/api/document-intake/uploads")
    async def document_intake_upload(
        file: UploadFile = File(...),
        opportunity_id: str | None = Form(default=None),
    ) -> DocumentIntakeUploadResponse:
        source_material = classify_uploaded_source_material(
            filename=file.filename,
            mime_type=file.content_type,
            content=await file.read(),
        )
        record = create_document_intake_record(
            source_material,
            opportunity_id=opportunity_id,
        )
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        return DocumentIntakeUploadResponse(
            record=_write_intake_record_and_generic_bundle(
                store,
                record,
                source_material,
            )
        )

    @app.post("/api/document-intake/source-material")
    def document_intake_source_material(
        request: DocumentIntakeSourceMaterialRequest,
    ) -> DocumentIntakeUploadResponse:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="source material is empty")
        source_material = classify_uploaded_source_material(
            filename=request.filename,
            mime_type=request.mime_type,
            content=request.content.encode("utf-8"),
        )
        record = create_document_intake_record(
            source_material,
            opportunity_id=request.opportunity_id,
        )
        store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        return DocumentIntakeUploadResponse(
            record=_write_intake_record_and_generic_bundle(
                store,
                record,
                source_material,
            )
        )

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
            local_admin_model_assist=_local_admin_model_assist(
                request.content,
                runtime_settings,
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
        review = process_raw_capture_item(
            raw_item,
            reference_wiki=wiki,
            local_admin_model_assist=_local_admin_model_assist(
                raw_item.content,
                runtime_settings,
            ),
        )
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
        review = process_raw_capture_item(
            raw_item,
            reference_wiki=wiki,
            local_admin_model_assist=_local_admin_model_assist(
                raw_item.content,
                runtime_settings,
            ),
        )
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
            local_admin_model_assist=_local_admin_model_assist(
                raw_item.content,
                runtime_settings,
            ),
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
        review = process_raw_capture_item(
            raw_item,
            reference_wiki=wiki,
            local_admin_model_assist=_local_admin_model_assist(
                raw_item.content,
                runtime_settings,
            ),
        )
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
                return CapturePromotionResponse(
                    review=review, packet_answer=packet_answer
                )

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


def _write_intake_record_and_generic_bundle(
    store: DocumentIntakeStore,
    record: DocumentIntakeRecord,
    source_material: UploadedSourceMaterial,
) -> DocumentIntakeRecord:
    persisted_record = store.write(record)
    if source_material.text is None:
        return persisted_record
    bundle = create_generic_extraction_bundle(persisted_record, source_material)
    store.write_extraction_bundle(bundle)
    for candidate in create_review_gated_capture_candidates_from_extraction_bundle(
        bundle
    ):
        store.write_capture_candidate(candidate)
    return store.write(persisted_record.with_extraction_bundle(bundle))


def _document_intake_review_response(
    result: AcceptedSourceSpanEvidenceResult,
    evidence_store: LocalEvidenceStore,
) -> DocumentIntakeReviewDecisionResponse:
    return DocumentIntakeReviewDecisionResponse(
        evidence=result.evidence,
        accepted_link=result.accepted_link,
        duplicate=result.duplicate,
        evidence_store_count=len(evidence_store.list()),
    )


def _local_admin_model_assist(content: str, settings: RuntimeSettings):
    return request_local_admin_draft_assist(
        content,
        settings=settings.local_admin_model,
    )


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
