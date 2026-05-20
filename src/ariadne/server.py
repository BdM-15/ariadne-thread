from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from ariadne.action_plans import ActionPlanItem
from ariadne.artifact_assembly import (
    ArtifactAssemblyStore,
    ArtifactBlockReviewAction,
    ArtifactDraft,
    ArtifactSourcePackage,
    ArtifactSourcePackageSummary,
    assemble_milestone_packet_draft,
    create_artifact_source_package_from_context,
    review_artifact_block,
    summarize_artifact_source_package,
)
from ariadne.capabilities import CapabilityCatalog, discover_local_capability_catalog
from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunReviewDecisionType,
    CapabilityRunStore,
    record_capability_run_output_review,
    run_capability_catalog_validation,
    run_local_admin_model_readiness_probe,
)
from ariadne.capture_research import (
    ApprovedWebSourceCollectionAdapter,
    CaptureResearchCandidateReviewDecisionType,
    CaptureResearchLens,
    CaptureResearchRun,
    CaptureResearchRunStatus,
    CaptureResearchStore,
    FakeWebSourceCollectionAdapter,
    SourceProviderRegistry,
    SourceProviderSmokeCheckResult,
    SourceProviderSmokeRunner,
    SourceProfileRef,
    build_seller_baseline_query,
    build_source_provider_registry,
    create_source_provider_adapter,
    create_source_context_research_run,
    create_user_prompted_research_run,
    project_capture_research_downstream_candidates,
    record_capture_research_candidate_review_decision,
    run_approved_source_provider_collection,
    run_competitive_gap_analysis,
    run_requirements_fit_analysis,
    run_selected_capture_lens_analysis,
    run_source_provider_smoke_check,
    run_web_source_collection,
)
from ariadne.command_center import (
    build_command_center_knowledge_context,
    render_capability_studio_shell,
    render_artifact_draft_shell,
    render_command_center_shell,
    render_sam_gov_enrichment_profile_shell,
)
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
    FederalDataInitializeRunner,
    FederalDataProductStatus,
    FederalDataSmokeCheckResult,
    list_federal_data_capability_manifests,
    run_federal_data_initialize_smoke_check,
    run_mcp_initialize_command,
)
from ariadne.local_admin_model import LocalAdminModelClient, request_local_admin_draft_assist
from ariadne.next_action_recommendations import (
    NextActionRecommendationStore,
    accept_next_action_recommendation,
    recommend_next_capture_actions,
)
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
from ariadne.piid_profiles import (
    PiidContractIntelligenceProfile,
    PiidProfileStore,
    PiidReviewState,
    create_piid_contract_intelligence_profile,
    record_piid_review_decision,
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
from ariadne.sam_gov_profiles import (
    SamGovAttachmentFetchResult,
    SamGovAttachmentFetcher,
    SamGovCommandSurfaceSummary,
    SamGovEnrichmentProfile,
    SamGovKnownOpportunityQuery,
    SamGovMcpToolRunner,
    SamGovOpportunityDiscoveryQuery,
    SamGovProfileStore,
    SamGovReviewState,
    SamGovSourceMode,
    add_sam_gov_known_opportunity_lane,
    add_sam_gov_opportunity_discovery_lane,
    build_sam_gov_command_surface_summary,
    create_sam_gov_enrichment_profile,
    create_sam_gov_lookup_runner,
    create_sam_gov_opportunity_discovery_profile,
    find_sam_gov_attachment,
    is_official_sam_gov_attachment_url,
    record_sam_gov_attachment_download,
    record_sam_gov_attachment_download_failure,
    record_sam_gov_review_decision,
    resolve_sam_gov_entity_lookup,
    resolve_sam_gov_known_opportunity,
    resolve_sam_gov_opportunity_discovery,
)
from ariadne.usaspending import (
    USAspendingAwardLookupResult,
    USAspendingAwardLookupStatus,
    USAspendingMcpToolRunner,
    create_usaspending_lookup_runner,
    fetch_usaspending_award_history,
    resolve_usaspending_piid,
)
from ariadne.production_command_center import (
    AssistedRouteRecommendationRequest,
    AssistedRouteRecommendationResponse,
    AssistedRouteRunRequest,
    AssistedRouteRunResponse,
    ProductionCommandCenterWorkspace,
    WorkflowRoutingStore,
    build_production_command_center_workspace,
    execute_assisted_capture_route,
    recommend_assisted_capture_routes,
)


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
    safe_smoke_check_method: str = "json_rpc_initialize_only"
    smoke_check_endpoint_template: str = (
        "/api/federal-data/capabilities/{capability_id}/smoke-check"
    )


class FederalDataSmokeCheckResponse(BaseModel):
    result: FederalDataSmokeCheckResult
    safe_smoke_check_method: str = "json_rpc_initialize_only"


class CapabilityRunResponse(BaseModel):
    run: CapabilityRun


class CapabilityRunListResponse(BaseModel):
    runs: tuple[CapabilityRun, ...]


class ArtifactSourcePackageResponse(BaseModel):
    package: ArtifactSourcePackage
    summary: ArtifactSourcePackageSummary


class ArtifactDraftResponse(BaseModel):
    draft: ArtifactDraft


class CapabilityRunOutputReviewRequest(BaseModel):
    decision: CapabilityRunReviewDecisionType
    reviewer_rationale: str = ""
    routed_destination: str | None = None


class CaptureResearchRunCreateRequest(BaseModel):
    prompt: str
    trigger_summary: str | None = None
    opportunity_id: str | None = None
    source_profile_refs: tuple[SourceProfileRef, ...] = ()
    selected_lenses: tuple[CaptureResearchLens, ...]
    source_targets: tuple[str, ...]
    source_limits: tuple[str, ...]
    evidence_goals: tuple[str, ...] = ()
    known_pivots: tuple[str, ...] = ()


class CaptureResearchRunResponse(BaseModel):
    run: CaptureResearchRun


class CaptureResearchRunListResponse(BaseModel):
    runs: tuple[CaptureResearchRun, ...]


class CaptureResearchSourceProviderResponse(BaseModel):
    registry: SourceProviderRegistry


class CaptureResearchSourceProviderSmokeCheckRequest(BaseModel):
    approved: bool = False
    smoke_target: str = "https://example.com"
    checked_at: str | None = None


class CaptureResearchSourceProviderSmokeCheckResponse(BaseModel):
    result: SourceProviderSmokeCheckResult


class CaptureResearchFakeCollectionRequest(BaseModel):
    collected_at: str | None = None


class CaptureResearchSourceProviderCollectionRequest(BaseModel):
    approved: bool = False
    provider_ids: tuple[str, ...] = ()
    collected_at: str | None = None


class CaptureResearchRequirementsFitRequest(BaseModel):
    analyzed_at: str | None = None
    reference_limit: int = Field(default=5, ge=0, le=10)


class CaptureResearchCompetitiveGapRequest(BaseModel):
    analyzed_at: str | None = None


class CaptureResearchSelectedLensAnalysisRequest(BaseModel):
    analyzed_at: str | None = None
    selected_lenses: tuple[CaptureResearchLens, ...] | None = None


class CaptureResearchCandidateProjectionRequest(BaseModel):
    projected_at: str | None = None


class CaptureResearchCandidateReviewDecisionRequest(BaseModel):
    decision: CaptureResearchCandidateReviewDecisionType
    reviewer_rationale: str
    decided_at: str | None = None
    routed_destination: str | None = None


class USAspendingPiidLookupRequest(BaseModel):
    contract_number: str
    limit: int = Field(default=5, ge=1, le=100)


class USAspendingPiidLookupResponse(BaseModel):
    result: USAspendingAwardLookupResult


class USAspendingPiidProfileCreateRequest(BaseModel):
    contract_number: str
    limit: int = Field(default=5, ge=1, le=100)
    transaction_limit: int = Field(default=100, ge=1, le=5000)
    funding_limit: int = Field(default=50, ge=1, le=100)
    vehicle_child_limit: int = Field(default=50, ge=1, le=100)


class USAspendingPiidProfileResponse(BaseModel):
    profile: PiidContractIntelligenceProfile


class USAspendingPiidProfileReviewDecisionRequest(BaseModel):
    candidate_id: str
    review_state: PiidReviewState
    reviewer_rationale: str


class USAspendingPiidProfilesResponse(BaseModel):
    profiles: tuple[PiidContractIntelligenceProfile, ...]


class SamGovEnrichmentProfileCreateRequest(BaseModel):
    input_pivot: str
    limit: int = Field(default=10, ge=1, le=10)


class SamGovOpportunityDiscoveryRequest(SamGovOpportunityDiscoveryQuery):
    pass


class SamGovKnownOpportunityRequest(SamGovKnownOpportunityQuery):
    pass


class SamGovEnrichmentProfileResponse(BaseModel):
    profile: SamGovEnrichmentProfile


class SamGovEnrichmentProfilesResponse(BaseModel):
    profiles: tuple[SamGovEnrichmentProfile, ...]


class SamGovCommandSurfaceResponse(BaseModel):
    summary: SamGovCommandSurfaceSummary


class SamGovEnrichmentProfileReviewDecisionRequest(BaseModel):
    candidate_id: str
    review_state: SamGovReviewState
    reviewer_rationale: str


class SamGovAttachmentDownloadApprovalRequest(BaseModel):
    reviewer_rationale: str


class SamGovAttachmentDownloadResponse(BaseModel):
    profile: SamGovEnrichmentProfile
    intake_record: DocumentIntakeRecord | None = None


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


class ProductionCommandCenterWorkspaceResponse(BaseModel):
    workspace: ProductionCommandCenterWorkspace


def create_app(
    settings: RuntimeSettings | None = None,
    *,
    federal_data_smoke_runner: FederalDataInitializeRunner = run_mcp_initialize_command,
    usaspending_lookup_runner: USAspendingMcpToolRunner | None = None,
    sam_gov_entity_runner: SamGovMcpToolRunner | None = None,
    sam_gov_opportunity_runner: SamGovMcpToolRunner | None = None,
    sam_gov_attachment_fetcher: SamGovAttachmentFetcher | None = None,
    sam_gov_source_mode: SamGovSourceMode | None = None,
    local_admin_model_client: LocalAdminModelClient | None = None,
    source_provider_adapter: ApprovedWebSourceCollectionAdapter | None = None,
    source_provider_smoke_runner: SourceProviderSmokeRunner | None = None,
) -> FastAPI:
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

    @app.get("/api/production-command-center/workspace")
    def production_command_center_workspace() -> ProductionCommandCenterWorkspaceResponse:
        return ProductionCommandCenterWorkspaceResponse(
            workspace=build_production_command_center_workspace(
                runtime_settings,
                workspace_root=Path.cwd(),
            )
        )

    @app.post(
        "/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations"
    )
    def production_command_center_route_recommendations(
        opportunity_id: str,
        request: AssistedRouteRecommendationRequest,
    ) -> AssistedRouteRecommendationResponse:
        if opportunity_id != "opp-aflcmc-recompete":
            raise HTTPException(status_code=404, detail="Opportunity context not found")
        try:
            return recommend_assisted_capture_routes(
                opportunity_id=opportunity_id,
                goal_id=request.goal_id,
                store=WorkflowRoutingStore(runtime_settings.ariadne_workflow_routing_dir),
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/production-command-center/routes/{recommendation_id}/runs")
    def production_command_center_execute_route(
        recommendation_id: str,
        request: AssistedRouteRunRequest,
    ) -> AssistedRouteRunResponse:
        try:
            run = execute_assisted_capture_route(
                store=WorkflowRoutingStore(runtime_settings.ariadne_workflow_routing_dir),
                recommendation_id=recommendation_id,
                approved=request.approved,
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Route recommendation not found") from error
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return AssistedRouteRunResponse(run=run)

    @app.get("/", response_class=HTMLResponse)
    def command_center_status() -> str:
        return render_command_center_shell(runtime_settings)

    @app.get("/capability-studio", response_class=HTMLResponse)
    def capability_studio() -> str:
        return render_capability_studio_shell(runtime_settings)

    @app.get("/capability-studio/runs/{run_id}", response_class=HTMLResponse)
    def capability_studio_run_detail(run_id: str) -> str:
        try:
            return render_capability_studio_shell(runtime_settings, run_id=run_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Capability Run not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/capability-studio/actions/catalog-validation")
    def capability_studio_catalog_validation_action() -> RedirectResponse:
        store = CapabilityRunStore(runtime_settings.ariadne_capability_runs_dir)
        run = run_capability_catalog_validation(workspace_root=Path.cwd(), store=store)
        return RedirectResponse(
            url=f"/capability-studio/runs/{run.run_id}",
            status_code=303,
        )

    @app.post(
        "/knowledge-context/opportunities/{opportunity_id}/"
        "recommend-next-capture-actions"
    )
    def knowledge_context_recommend_next_capture_actions(
        opportunity_id: str,
    ) -> RedirectResponse:
        knowledge_context = build_command_center_knowledge_context(
            runtime_settings,
            workspace_root=Path.cwd(),
        )
        if opportunity_id != knowledge_context.opportunity_id:
            raise HTTPException(status_code=404, detail="Opportunity context not found")
        store = NextActionRecommendationStore(
            _resolve_runtime_path(runtime_settings.ariadne_next_action_recommendations_dir)
        )
        recommend_next_capture_actions(
            context=knowledge_context.context,
            capability_catalog=discover_local_capability_catalog(Path.cwd()),
            store=store,
            generated_at=_utc_timestamp(),
        )
        return RedirectResponse(url="/#knowledge-context", status_code=303)

    @app.post("/knowledge-context/recommendations/{recommendation_id}/accept")
    def knowledge_context_accept_recommendation(
        recommendation_id: str,
    ) -> RedirectResponse:
        store = NextActionRecommendationStore(
            _resolve_runtime_path(runtime_settings.ariadne_next_action_recommendations_dir)
        )
        try:
            recommendation = store.read(recommendation_id)
            knowledge_context = build_command_center_knowledge_context(
                runtime_settings,
                workspace_root=Path.cwd(),
            )
            if recommendation.opportunity_id != knowledge_context.opportunity_id:
                raise HTTPException(
                    status_code=400,
                    detail="Recommendation does not match selected Opportunity",
                )
            accept_next_action_recommendation(
                store=store,
                recommendation_id=recommendation_id,
                action_plan=knowledge_context.action_plan,
                reviewer_rationale="Accepted from Knowledge Context Panel.",
                decided_at=_utc_timestamp(),
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Recommendation not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return RedirectResponse(url="/#knowledge-context", status_code=303)

    @app.post("/artifact-assembly/opportunities/{opportunity_id}/source-package")
    def artifact_assembly_create_source_package_action(
        opportunity_id: str,
    ) -> RedirectResponse:
        _create_artifact_source_package(opportunity_id, runtime_settings)
        return RedirectResponse(url="/#artifact-assembly", status_code=303)

    @app.post(
        "/api/artifact-assembly/opportunities/{opportunity_id}/source-package"
    )
    def artifact_assembly_create_source_package(
        opportunity_id: str,
    ) -> ArtifactSourcePackageResponse:
        return _create_artifact_source_package(opportunity_id, runtime_settings)

    @app.post(
        "/artifact-assembly/source-packages/{source_package_id}/milestone-packet-draft"
    )
    def artifact_assembly_create_milestone_packet_draft_action(
        source_package_id: str,
    ) -> RedirectResponse:
        draft = _create_milestone_packet_draft(source_package_id, runtime_settings)
        return RedirectResponse(
            url=f"/artifact-assembly/drafts/{draft.draft_id}",
            status_code=303,
        )

    @app.post(
        "/api/artifact-assembly/source-packages/{source_package_id}/milestone-packet-draft"
    )
    def artifact_assembly_create_milestone_packet_draft(
        source_package_id: str,
    ) -> ArtifactDraftResponse:
        draft = _create_milestone_packet_draft(source_package_id, runtime_settings)
        return ArtifactDraftResponse(draft=draft)

    @app.get("/artifact-assembly/drafts/{draft_id}", response_class=HTMLResponse)
    def artifact_draft_command_surface(draft_id: str) -> str:
        try:
            return render_artifact_draft_shell(runtime_settings, draft_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Artifact draft not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/artifact-assembly/drafts/{draft_id}/blocks/{block_id}/review")
    def artifact_draft_review_block_action(
        draft_id: str,
        block_id: str,
        action: str = Form(...),
        reviewer_notes: str = Form(""),
        edited_body: str | None = Form(None),
        routed_destination: str | None = Form(None),
    ) -> RedirectResponse:
        store = ArtifactAssemblyStore(
            _resolve_runtime_path(runtime_settings.ariadne_artifact_assembly_dir)
        )
        try:
            review_artifact_block(
                draft_id=draft_id,
                block_id=block_id,
                action=ArtifactBlockReviewAction(action),
                store=store,
                reviewed_at=_utc_timestamp(),
                reviewer_notes=reviewer_notes,
                edited_body=edited_body,
                routed_destination=routed_destination,
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Artifact draft not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return RedirectResponse(
            url=f"/artifact-assembly/drafts/{draft_id}",
            status_code=303,
        )

    @app.get(
        "/federal-data/sam-gov/enrichment-profiles/{profile_id}",
        response_class=HTMLResponse,
    )
    def sam_gov_enrichment_profile_command_surface(profile_id: str) -> str:
        try:
            return render_sam_gov_enrichment_profile_shell(
                runtime_settings,
                profile_id,
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="SAM.gov enrichment profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

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

    @app.post("/api/capability-runs/catalog-validation")
    def capability_catalog_validation_run() -> CapabilityRunResponse:
        store = CapabilityRunStore(runtime_settings.ariadne_capability_runs_dir)
        return CapabilityRunResponse(
            run=run_capability_catalog_validation(
                workspace_root=Path.cwd(),
                store=store,
            )
        )

    @app.post("/api/capability-runs/local-admin-model-readiness-probe")
    def local_admin_model_readiness_probe() -> CapabilityRunResponse:
        store = CapabilityRunStore(runtime_settings.ariadne_capability_runs_dir)
        return CapabilityRunResponse(
            run=run_local_admin_model_readiness_probe(
                settings=runtime_settings.local_admin_model,
                store=store,
                client=local_admin_model_client,
            )
        )

    @app.get("/api/capability-runs")
    def capability_runs() -> CapabilityRunListResponse:
        store = CapabilityRunStore(runtime_settings.ariadne_capability_runs_dir)
        return CapabilityRunListResponse(runs=tuple(store.list()))

    @app.get("/api/capability-runs/{run_id}")
    def capability_run_detail(run_id: str) -> CapabilityRunResponse:
        store = CapabilityRunStore(runtime_settings.ariadne_capability_runs_dir)
        try:
            return CapabilityRunResponse(run=store.read(run_id))
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Capability Run not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capability-runs/{run_id}/outputs/{output_id}/review")
    def capability_run_output_review(
        run_id: str,
        output_id: str,
        request: CapabilityRunOutputReviewRequest,
    ) -> CapabilityRunResponse:
        store = CapabilityRunStore(runtime_settings.ariadne_capability_runs_dir)
        try:
            return CapabilityRunResponse(
                run=record_capability_run_output_review(
                    store=store,
                    run_id=run_id,
                    output_id=output_id,
                    decision=request.decision,
                    reviewer_rationale=request.reviewer_rationale,
                    routed_destination=request.routed_destination,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Capability Run not found") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capture-research/runs")
    def create_capture_research_run(
        request: CaptureResearchRunCreateRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        try:
            if request.source_profile_refs:
                run = create_source_context_research_run(
                    request.trigger_summary or request.prompt,
                    opportunity_id=request.opportunity_id,
                    source_profile_refs=request.source_profile_refs,
                    prompt=request.prompt,
                    selected_lenses=request.selected_lenses,
                    source_targets=request.source_targets,
                    source_limits=request.source_limits,
                    evidence_goals=request.evidence_goals,
                    known_pivots=request.known_pivots,
                )
            else:
                run = create_user_prompted_research_run(
                    request.prompt,
                    opportunity_id=request.opportunity_id,
                    selected_lenses=request.selected_lenses,
                    source_targets=request.source_targets,
                    source_limits=request.source_limits,
                    evidence_goals=request.evidence_goals,
                    known_pivots=request.known_pivots,
            )
            return CaptureResearchRunResponse(run=store.write(run))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/api/capture-research/runs")
    def capture_research_runs(
        opportunity_id: str | None = None,
        status: CaptureResearchRunStatus | None = None,
    ) -> CaptureResearchRunListResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        return CaptureResearchRunListResponse(
            runs=tuple(store.list(opportunity_id=opportunity_id, status=status))
        )

    @app.get("/api/capture-research/source-providers")
    def capture_research_source_providers() -> CaptureResearchSourceProviderResponse:
        return CaptureResearchSourceProviderResponse(
            registry=build_source_provider_registry(
                runtime_settings.capture_research_source_env
            )
        )

    @app.post("/api/capture-research/source-providers/{provider_id}/smoke-check")
    def capture_research_source_provider_smoke_check(
        provider_id: str,
        request: CaptureResearchSourceProviderSmokeCheckRequest,
    ) -> CaptureResearchSourceProviderSmokeCheckResponse:
        try:
            return CaptureResearchSourceProviderSmokeCheckResponse(
                result=run_source_provider_smoke_check(
                    provider_id=provider_id,
                    env=runtime_settings.capture_research_source_env,
                    approved=request.approved,
                    smoke_target=request.smoke_target,
                    runner=source_provider_smoke_runner,
                    checked_at=request.checked_at,
                    timeout_seconds=runtime_settings.mcp_tool_timeout_seconds,
                )
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/api/capture-research/runs/{research_run_id}")
    def capture_research_run_detail(
        research_run_id: str,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        try:
            return CaptureResearchRunResponse(run=store.read(research_run_id))
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capture-research/runs/{research_run_id}/source-provider-collection")
    def capture_research_source_provider_collection(
        research_run_id: str,
        request: CaptureResearchSourceProviderCollectionRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        registry = build_source_provider_registry(
            runtime_settings.capture_research_source_env
        )
        try:
            adapter = source_provider_adapter or create_source_provider_adapter(
                env=runtime_settings.capture_research_source_env,
                registry=registry,
                provider_ids=request.provider_ids,
            )
            return CaptureResearchRunResponse(
                run=run_approved_source_provider_collection(
                    store=store,
                    research_run_id=research_run_id,
                    registry=registry,
                    adapter=adapter,
                    approved=request.approved,
                    provider_ids=request.provider_ids,
                    collected_at=request.collected_at,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capture-research/runs/{research_run_id}/fake-web-source-collection")
    def capture_research_fake_web_source_collection(
        research_run_id: str,
        request: CaptureResearchFakeCollectionRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        try:
            return CaptureResearchRunResponse(
                run=run_web_source_collection(
                    store=store,
                    research_run_id=research_run_id,
                    adapter=FakeWebSourceCollectionAdapter(),
                    collected_at=request.collected_at,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capture-research/runs/{research_run_id}/requirements-fit-analysis")
    def capture_research_requirements_fit_analysis(
        research_run_id: str,
        request: CaptureResearchRequirementsFitRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        evidence_store = LocalEvidenceStore(
            _resolve_runtime_path(runtime_settings.ariadne_evidence_dir)
        )
        try:
            run = store.read(research_run_id)
            reference_influences = load_reference_wiki(
                _resolve_runtime_path(runtime_settings.ariadne_reference_wiki_dir)
            ).find_influences(
                build_seller_baseline_query(run),
                limit=request.reference_limit,
            )
            return CaptureResearchRunResponse(
                run=run_requirements_fit_analysis(
                    store=store,
                    research_run_id=research_run_id,
                    evidence_items=tuple(evidence_store.list()),
                    reference_influences=reference_influences,
                    analyzed_at=request.analyzed_at,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capture-research/runs/{research_run_id}/competitive-gap-analysis")
    def capture_research_competitive_gap_analysis(
        research_run_id: str,
        request: CaptureResearchCompetitiveGapRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        try:
            return CaptureResearchRunResponse(
                run=run_competitive_gap_analysis(
                    store=store,
                    research_run_id=research_run_id,
                    analyzed_at=request.analyzed_at,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capture-research/runs/{research_run_id}/selected-lens-analysis")
    def capture_research_selected_lens_analysis(
        research_run_id: str,
        request: CaptureResearchSelectedLensAnalysisRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        try:
            return CaptureResearchRunResponse(
                run=run_selected_capture_lens_analysis(
                    store=store,
                    research_run_id=research_run_id,
                    selected_lenses=request.selected_lenses,
                    analyzed_at=request.analyzed_at,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/capture-research/runs/{research_run_id}/downstream-candidates")
    def capture_research_downstream_candidates(
        research_run_id: str,
        request: CaptureResearchCandidateProjectionRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        try:
            return CaptureResearchRunResponse(
                run=project_capture_research_downstream_candidates(
                    store=store,
                    research_run_id=research_run_id,
                    projected_at=request.projected_at,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post(
        "/api/capture-research/runs/{research_run_id}/downstream-candidates/{candidate_id}/review-decisions"
    )
    def capture_research_candidate_review_decision(
        research_run_id: str,
        candidate_id: str,
        request: CaptureResearchCandidateReviewDecisionRequest,
    ) -> CaptureResearchRunResponse:
        store = CaptureResearchStore(
            _resolve_runtime_path(runtime_settings.ariadne_capture_research_dir)
        )
        try:
            return CaptureResearchRunResponse(
                run=record_capture_research_candidate_review_decision(
                    store=store,
                    research_run_id=research_run_id,
                    candidate_id=candidate_id,
                    decision=request.decision,
                    reviewer_rationale=request.reviewer_rationale,
                    decided_at=request.decided_at,
                    routed_destination=request.routed_destination,
                )
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Capture Research run not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

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

    @app.post("/api/federal-data/capabilities/{capability_id}/smoke-check")
    def federal_data_capability_smoke_check(
        capability_id: str,
    ) -> FederalDataSmokeCheckResponse:
        registry = list_federal_data_capability_manifests()
        manifest = next(
            (
                capability
                for capability in registry.capabilities
                if capability.id == capability_id
            ),
            None,
        )
        if manifest is None:
            raise HTTPException(
                status_code=404, detail="Federal Data Capability not found"
            )
        return FederalDataSmokeCheckResponse(
            result=run_federal_data_initialize_smoke_check(
                manifest,
                runner=federal_data_smoke_runner,
                env=_federal_data_env_for_manifest(manifest, runtime_settings),
                timeout_seconds=runtime_settings.mcp_tool_timeout_seconds,
            )
        )

    @app.post("/api/federal-data/usaspending/piid-lookup")
    def usaspending_piid_lookup(
        request: USAspendingPiidLookupRequest,
    ) -> USAspendingPiidLookupResponse:
        manifest = _federal_data_manifest("usaspending")
        runner = usaspending_lookup_runner or create_usaspending_lookup_runner(
            command=manifest.command,
            timeout_seconds=runtime_settings.mcp_tool_timeout_seconds,
            env=_federal_data_env_for_manifest(manifest, runtime_settings),
        )
        return USAspendingPiidLookupResponse(
            result=resolve_usaspending_piid(
                request.contract_number,
                runner=runner,
                lookup_limit=request.limit,
            )
        )

    @app.get("/api/federal-data/usaspending/piid-profiles")
    def usaspending_piid_profiles() -> USAspendingPiidProfilesResponse:
        store = PiidProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_piid_profiles_dir)
        )
        return USAspendingPiidProfilesResponse(profiles=tuple(store.list()))

    @app.post("/api/federal-data/usaspending/piid-profiles")
    def create_usaspending_piid_profile(
        request: USAspendingPiidProfileCreateRequest,
    ) -> USAspendingPiidProfileResponse:
        manifest = _federal_data_manifest("usaspending")
        runner = usaspending_lookup_runner or create_usaspending_lookup_runner(
            command=manifest.command,
            timeout_seconds=runtime_settings.mcp_tool_timeout_seconds,
            env=_federal_data_env_for_manifest(manifest, runtime_settings),
        )
        lookup = resolve_usaspending_piid(
            request.contract_number,
            runner=runner,
            lookup_limit=request.limit,
        )
        if lookup.status is not USAspendingAwardLookupStatus.SUCCESS:
            raise HTTPException(
                status_code=409,
                detail="resolved USAspending award is required",
            )
        award_history = fetch_usaspending_award_history(
            lookup,
            runner=runner,
            transaction_limit=request.transaction_limit,
            funding_limit=request.funding_limit,
            vehicle_child_limit=request.vehicle_child_limit,
        )
        profile = create_piid_contract_intelligence_profile(
            lookup,
            award_history=award_history,
        )
        store = PiidProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_piid_profiles_dir)
        )
        return USAspendingPiidProfileResponse(profile=store.write(profile))

    @app.get("/api/federal-data/usaspending/piid-profiles/{profile_id}")
    def usaspending_piid_profile(
        profile_id: str,
    ) -> USAspendingPiidProfileResponse:
        store = PiidProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_piid_profiles_dir)
        )
        try:
            profile = store.read(profile_id)
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="PIID profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return USAspendingPiidProfileResponse(profile=profile)

    @app.post(
        "/api/federal-data/usaspending/piid-profiles/{profile_id}/review-decisions"
    )
    def usaspending_piid_profile_review_decision(
        profile_id: str,
        request: USAspendingPiidProfileReviewDecisionRequest,
    ) -> USAspendingPiidProfileResponse:
        store = PiidProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_piid_profiles_dir)
        )
        try:
            profile = store.read(profile_id)
            updated_profile = record_piid_review_decision(
                profile,
                candidate_id=request.candidate_id,
                review_state=request.review_state,
                reviewer_rationale=request.reviewer_rationale,
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="PIID profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return USAspendingPiidProfileResponse(profile=store.write(updated_profile))

    @app.get("/api/federal-data/sam-gov/enrichment-profiles")
    def sam_gov_enrichment_profiles() -> SamGovEnrichmentProfilesResponse:
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        return SamGovEnrichmentProfilesResponse(profiles=tuple(store.list()))

    @app.post("/api/federal-data/sam-gov/enrichment-profiles")
    def create_sam_gov_enrichment_profile_api(
        request: SamGovEnrichmentProfileCreateRequest,
    ) -> SamGovEnrichmentProfileResponse:
        runner, source_mode = _sam_gov_entity_runner_and_source_mode(
            runtime_settings,
            injected_runner=sam_gov_entity_runner,
            injected_source_mode=sam_gov_source_mode,
            missing_key_detail="SAM.gov API key is required for live SAM.gov entity enrichment",
        )
        lookup = resolve_sam_gov_entity_lookup(
            request.input_pivot,
            runner=runner,
            source_mode=source_mode,
            lookup_limit=request.limit,
        )
        profile = create_sam_gov_enrichment_profile(lookup)
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        return SamGovEnrichmentProfileResponse(profile=store.write(profile))

    @app.post("/api/federal-data/sam-gov/enrichment-profiles/opportunity-discovery")
    def create_sam_gov_opportunity_discovery_profile_api(
        request: SamGovOpportunityDiscoveryRequest,
    ) -> SamGovEnrichmentProfileResponse:
        runner, source_mode = _sam_gov_entity_runner_and_source_mode(
            runtime_settings,
            injected_runner=sam_gov_opportunity_runner or sam_gov_entity_runner,
            injected_source_mode=sam_gov_source_mode,
            missing_key_detail=(
                "SAM.gov API key is required for live SAM.gov opportunity discovery"
            ),
        )
        discovery = resolve_sam_gov_opportunity_discovery(
            request,
            runner=runner,
            source_mode=source_mode,
        )
        profile = create_sam_gov_opportunity_discovery_profile(discovery)
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        return SamGovEnrichmentProfileResponse(profile=store.write(profile))

    @app.post(
        "/api/federal-data/sam-gov/enrichment-profiles/{profile_id}/opportunity-discovery"
    )
    def add_sam_gov_opportunity_discovery_lane_api(
        profile_id: str,
        request: SamGovOpportunityDiscoveryRequest,
    ) -> SamGovEnrichmentProfileResponse:
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        try:
            profile = store.read(profile_id)
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="SAM.gov enrichment profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        runner, source_mode = _sam_gov_entity_runner_and_source_mode(
            runtime_settings,
            injected_runner=sam_gov_opportunity_runner or sam_gov_entity_runner,
            injected_source_mode=sam_gov_source_mode,
            missing_key_detail=(
                "SAM.gov API key is required for live SAM.gov opportunity discovery"
            ),
        )
        discovery = resolve_sam_gov_opportunity_discovery(
            request,
            runner=runner,
            source_mode=source_mode,
        )
        updated_profile = add_sam_gov_opportunity_discovery_lane(profile, discovery)
        return SamGovEnrichmentProfileResponse(profile=store.write(updated_profile))

    @app.post(
        "/api/federal-data/sam-gov/enrichment-profiles/{profile_id}/known-opportunity"
    )
    def add_sam_gov_known_opportunity_lane_api(
        profile_id: str,
        request: SamGovKnownOpportunityRequest,
    ) -> SamGovEnrichmentProfileResponse:
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        try:
            profile = store.read(profile_id)
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="SAM.gov enrichment profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        runner, source_mode = _sam_gov_entity_runner_and_source_mode(
            runtime_settings,
            injected_runner=sam_gov_opportunity_runner or sam_gov_entity_runner,
            injected_source_mode=sam_gov_source_mode,
            missing_key_detail=(
                "SAM.gov API key is required for live SAM.gov known opportunity enrichment"
            ),
        )
        lookup = resolve_sam_gov_known_opportunity(
            request,
            runner=runner,
            source_mode=source_mode,
        )
        updated_profile = add_sam_gov_known_opportunity_lane(profile, lookup)
        return SamGovEnrichmentProfileResponse(profile=store.write(updated_profile))

    @app.post(
        "/api/federal-data/sam-gov/enrichment-profiles/{profile_id}/attachments/{attachment_id}/approve-download"
    )
    def approve_sam_gov_attachment_download_api(
        profile_id: str,
        attachment_id: str,
        request: SamGovAttachmentDownloadApprovalRequest,
    ) -> SamGovAttachmentDownloadResponse:
        if not request.reviewer_rationale.strip():
            raise HTTPException(
                status_code=400,
                detail="reviewer_rationale is required to approve attachment download",
            )
        profile_store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        try:
            profile = profile_store.read(profile_id)
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="SAM.gov enrichment profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        attachment = find_sam_gov_attachment(profile, attachment_id)
        if attachment is None:
            raise HTTPException(status_code=404, detail="SAM.gov attachment not found")
        if not is_official_sam_gov_attachment_url(attachment.url):
            raise HTTPException(
                status_code=400,
                detail="SAM.gov attachment download requires an official SAM.gov surfaced link",
            )

        fetcher = sam_gov_attachment_fetcher or _fetch_sam_gov_attachment
        fetched = fetcher(attachment.url)
        if not fetched.ok or fetched.content is None:
            updated_profile = record_sam_gov_attachment_download_failure(
                profile,
                attachment_id=attachment.id,
                source_limitation=(
                    fetched.error_message or "SAM.gov attachment download failed"
                ),
            )
            return SamGovAttachmentDownloadResponse(
                profile=profile_store.write(updated_profile),
                intake_record=None,
            )

        source_material = classify_uploaded_source_material(
            filename=fetched.filename or attachment.filename,
            mime_type=fetched.mime_type or attachment.mime_type,
            content=fetched.content,
        )
        intake_store = DocumentIntakeStore(
            _resolve_runtime_path(runtime_settings.ariadne_document_intake_dir)
        )
        intake_record = _write_intake_record_and_generic_bundle(
            intake_store,
            create_document_intake_record(
                source_material,
                opportunity_id=profile.id,
                record_id=f"intake_{attachment.id}",
                source_provenance=_sam_gov_attachment_source_provenance(
                    profile,
                    attachment,
                ),
            ),
            source_material,
        )
        updated_profile = record_sam_gov_attachment_download(
            profile,
            attachment_id=attachment.id,
            intake_record_id=intake_record.id,
            intake_record_source_ref=intake_record.source_ref,
            intake_material_type=(
                intake_record.material_type.value
                if intake_record.material_type is not None
                else "unknown"
            ),
            intake_status=intake_record.status.value,
        )
        return SamGovAttachmentDownloadResponse(
            profile=profile_store.write(updated_profile),
            intake_record=intake_record,
        )

    @app.get(
        "/api/federal-data/sam-gov/enrichment-profiles/{profile_id}/command-surface"
    )
    def sam_gov_enrichment_profile_command_surface_api(
        profile_id: str,
    ) -> SamGovCommandSurfaceResponse:
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        try:
            profile = store.read(profile_id)
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="SAM.gov enrichment profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return SamGovCommandSurfaceResponse(
            summary=build_sam_gov_command_surface_summary(
                profile,
                live_ready="SAM_GOV_API_KEY" in runtime_settings.federal_data_env,
            )
        )

    @app.get("/api/federal-data/sam-gov/enrichment-profiles/{profile_id}")
    def sam_gov_enrichment_profile(
        profile_id: str,
    ) -> SamGovEnrichmentProfileResponse:
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        try:
            profile = store.read(profile_id)
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="SAM.gov enrichment profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return SamGovEnrichmentProfileResponse(profile=profile)

    @app.post(
        "/api/federal-data/sam-gov/enrichment-profiles/{profile_id}/review-decisions"
    )
    def sam_gov_enrichment_profile_review_decision(
        profile_id: str,
        request: SamGovEnrichmentProfileReviewDecisionRequest,
    ) -> SamGovEnrichmentProfileResponse:
        store = SamGovProfileStore(
            _resolve_runtime_path(runtime_settings.ariadne_sam_gov_profiles_dir)
        )
        try:
            profile = store.read(profile_id)
            updated_profile = record_sam_gov_review_decision(
                profile,
                candidate_id=request.candidate_id,
                review_state=request.review_state,
                reviewer_rationale=request.reviewer_rationale,
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="SAM.gov enrichment profile not found"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return SamGovEnrichmentProfileResponse(profile=store.write(updated_profile))

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


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _create_artifact_source_package(
    opportunity_id: str,
    runtime_settings: RuntimeSettings,
) -> ArtifactSourcePackageResponse:
    knowledge_context = build_command_center_knowledge_context(
        runtime_settings,
        workspace_root=Path.cwd(),
    )
    if opportunity_id != knowledge_context.opportunity_id:
        raise HTTPException(status_code=404, detail="Opportunity context not found")
    store = ArtifactAssemblyStore(
        _resolve_runtime_path(runtime_settings.ariadne_artifact_assembly_dir)
    )
    package = create_artifact_source_package_from_context(
        context=knowledge_context.context,
        store=store,
        created_at=_utc_timestamp(),
    )
    return ArtifactSourcePackageResponse(
        package=package,
        summary=summarize_artifact_source_package(package),
    )


def _create_milestone_packet_draft(
    source_package_id: str,
    runtime_settings: RuntimeSettings,
) -> ArtifactDraft:
    store = ArtifactAssemblyStore(
        _resolve_runtime_path(runtime_settings.ariadne_artifact_assembly_dir)
    )
    try:
        return assemble_milestone_packet_draft(
            source_package_id=source_package_id,
            store=store,
            assembled_at=_utc_timestamp(),
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Artifact source package not found",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _federal_data_env_for_manifest(
    manifest: FederalDataCapabilityManifest,
    settings: RuntimeSettings,
) -> dict[str, str]:
    env = {
        name: value
        for name, value in settings.federal_data_env.items()
        if name
        in manifest.required_env_vars
        + manifest.optional_env_vars
        + manifest.upstream_env_vars
    }
    for ariadne_name, upstream_name in zip(
        manifest.required_env_vars,
        manifest.upstream_env_vars,
        strict=False,
    ):
        if ariadne_name in env and upstream_name not in env:
            env[upstream_name] = env[ariadne_name]
    if manifest.id == "regulations_gov" and "API_DATA_GOV_KEY" in env:
        env.setdefault("REGULATIONS_GOV_API_KEY", env["API_DATA_GOV_KEY"])
    return env


def _federal_data_manifest(capability_id: str) -> FederalDataCapabilityManifest:
    registry = list_federal_data_capability_manifests()
    manifest = next(
        (
            capability
            for capability in registry.capabilities
            if capability.id == capability_id
        ),
        None,
    )
    if manifest is None:
        raise HTTPException(status_code=404, detail="Federal Data Capability not found")
    return manifest


def _sam_gov_entity_runner_and_source_mode(
    settings: RuntimeSettings,
    *,
    injected_runner: SamGovMcpToolRunner | None,
    injected_source_mode: SamGovSourceMode | None,
    missing_key_detail: str,
) -> tuple[SamGovMcpToolRunner, SamGovSourceMode]:
    if injected_runner is not None:
        return (
            injected_runner,
            injected_source_mode or SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    manifest = _federal_data_manifest("sam_gov")
    env = _federal_data_env_for_manifest(manifest, settings)
    missing_env_vars = tuple(
        env_var_name
        for env_var_name in manifest.required_env_vars
        if not env.get(env_var_name)
    )
    if missing_env_vars:
        raise HTTPException(
            status_code=409,
            detail=missing_key_detail,
        )
    return (
        create_sam_gov_lookup_runner(
            command=manifest.command,
            timeout_seconds=settings.mcp_tool_timeout_seconds,
            env=env,
        ),
        injected_source_mode or SamGovSourceMode.LIVE_SAM_GOV,
    )


def _fetch_sam_gov_attachment(url: str) -> SamGovAttachmentFetchResult:
    request = Request(url, headers={"User-Agent": "ariadne-thread/0.1"})
    try:
        with urlopen(request, timeout=30) as response:
            content = response.read(25 * 1024 * 1024 + 1)
            if len(content) > 25 * 1024 * 1024:
                return SamGovAttachmentFetchResult(
                    ok=False,
                    error_message="SAM.gov attachment exceeded local download size limit.",
                )
            return SamGovAttachmentFetchResult(
                ok=True,
                content=content,
                filename=Path(url).name or None,
                mime_type=response.headers.get_content_type(),
            )
    except HTTPError as error:
        return SamGovAttachmentFetchResult(
            ok=False,
            error_message=f"SAM.gov attachment download failed: HTTP {error.code}",
        )
    except URLError as error:
        return SamGovAttachmentFetchResult(
            ok=False,
            error_message=f"SAM.gov attachment download failed: {error.reason}",
        )


def _sam_gov_attachment_source_provenance(
    profile: SamGovEnrichmentProfile,
    attachment,
) -> dict[str, str]:
    source_mode = (
        profile.attachment_intake_lane.provenance.source_mode.value
        if profile.attachment_intake_lane is not None
        else SamGovSourceMode.LIVE_SAM_GOV.value
    )
    provenance = {
        "source_system": "sam.gov",
        "sam_gov_profile_id": profile.id,
        "sam_gov_attachment_id": attachment.id,
        "sam_gov_attachment_url": attachment.url,
        "sam_gov_source_mode": source_mode,
    }
    if attachment.source_notice_id:
        provenance["sam_gov_source_notice_id"] = attachment.source_notice_id
    if attachment.source_solicitation_number:
        provenance["sam_gov_source_solicitation_number"] = (
            attachment.source_solicitation_number
        )
    return provenance


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
