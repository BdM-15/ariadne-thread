from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from pathlib import Path
import re

from pydantic import BaseModel

from ariadne.config import RuntimeSettings
from ariadne.opportunities import (
    CoreCaptureWorkstream,
    EntryContext,
    EntryReason,
    LifecycleState,
    create_opportunity,
)
from ariadne.packet_knowledge import (
    AnswerPathKind,
    PacketFieldAnswerStatus,
    PacketFieldDefinition,
    build_default_packet_field_definitions,
    create_packet_field_answer,
)
from ariadne.packets import EvidenceStatus, create_living_briefing_packet
from ariadne.quick_capture_demo import build_quick_capture_demo_thread


class ProductionCommandCenterOpportunity(BaseModel):
    id: str
    name: str
    lifecycle_state: str
    gate_status: str


class ProductionCommandCenterPacket(BaseModel):
    title: str
    readiness_label: str
    answered_section_count: int
    gap_section_count: int
    partial_section_count: int


class ProductionCommandCenterContextSummary(BaseModel):
    trusted_count: int
    reviewable_count: int
    gap_count: int
    source_limitation_count: int


class ProductionCommandCenterRegion(BaseModel):
    id: str
    label: str
    purpose: str


class ProductionCommandCenterWorkMode(BaseModel):
    id: str
    label: str
    pending_count: int = 0


class ProductionOpportunityIntakeRequest(BaseModel):
    name: str
    entry_reason: EntryReason = EntryReason.NEW_LEAD
    starting_lifecycle_state: LifecycleState = LifecycleState.IDENTIFIED
    rationale: str | None = None
    missing_or_stale_workstreams: tuple[CoreCaptureWorkstream, ...] = ()


class ProductionOpportunityWorkstream(BaseModel):
    id: str
    label: str
    status: str


class ProductionOpportunityBackfillNeed(BaseModel):
    workstream_id: str
    label: str
    rationale: str


class ProductionOpportunityPacketSection(BaseModel):
    id: str
    label: str
    evidence_status: str


class ProductionOpportunityPacketFieldSlot(BaseModel):
    key: str
    label: str
    question: str
    section: str
    status: str
    evidence_status: str
    answer_paths: tuple[str, ...]
    recommended_route: str


class OpportunityActivationDigest(BaseModel):
    coverage_gained: tuple[str, ...]
    review_ready_count: int
    blocked_field_count: int
    recommended_skill_chains: tuple[str, ...]
    approval_required_routes: tuple[str, ...]
    source_limitations: tuple[str, ...]
    next_best_actions: tuple[str, ...]


class ProductionOpportunityScaffold(BaseModel):
    opportunity: ProductionCommandCenterOpportunity
    entry_reason: str
    entry_rationale: str
    workstreams: tuple[ProductionOpportunityWorkstream, ...]
    backfill_needs: tuple[ProductionOpportunityBackfillNeed, ...]
    packet: ProductionCommandCenterPacket
    packet_sections: tuple[ProductionOpportunityPacketSection, ...]
    packet_fields: tuple[ProductionOpportunityPacketFieldSlot, ...]
    activation_digest: OpportunityActivationDigest


class ProductionOpportunityCreateResponse(BaseModel):
    scaffold: ProductionOpportunityScaffold


class AssistedCaptureWorkProduct(StrEnum):
    CALL_PLAN = "call_plan"
    LIVING_PACKET = "living_packet"
    ACTION_PLAN = "action_plan"
    CAPTURE_RESEARCH = "capture_research"
    MARKETING_SKILL = "marketing_skill"


class AssistedCaptureAutonomyTier(StrEnum):
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    ASK_BEFORE_RUNNING = "ask_before_running"
    SAFE_TO_AUTO_RUN_LATER = "safe_to_auto_run_later"


class AssistedCaptureGoal(BaseModel):
    id: str
    label: str
    description: str
    primary_work_product: AssistedCaptureWorkProduct
    work_product_targets: tuple[AssistedCaptureWorkProduct, ...]


class AssistedCaptureSelectionPrompt(BaseModel):
    kind: str = "goal_selector"
    label: str = "What do you want Ariadne to help prepare next?"


class CapabilityRouteStepStatus(StrEnum):
    PLANNED = "planned"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CapabilityRouteStep(BaseModel):
    capability_id: str
    label: str
    capability_type: str
    executor_kind: str
    output_target: str
    status: CapabilityRouteStepStatus = CapabilityRouteStepStatus.PLANNED


class CapabilityRouteCard(BaseModel):
    id: str
    title: str
    capability_count: int
    steps: tuple[CapabilityRouteStep, ...]


class CapabilityRouteProgress(BaseModel):
    percent_complete: int
    steps: tuple[CapabilityRouteStep, ...]


class AssistedRouteRecommendation(BaseModel):
    id: str
    opportunity_id: str
    goal_id: str
    route_label: str
    route_summary: str
    autonomy_tier: AssistedCaptureAutonomyTier
    requires_review: bool = True
    work_product_targets: tuple[AssistedCaptureWorkProduct, ...]
    recommended_capability_chain: tuple[str, ...]
    capability_route_card: CapabilityRouteCard
    input_refs: tuple[str, ...]
    reasoning: tuple[str, ...]
    status: str = "recommended"


class AssistedRouteRunStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class AssistedRouteRunStageStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AssistedRouteOutputReviewState(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class AssistedRouteReviewDecisionType(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class WorkProductUpdateState(StrEnum):
    READY_FOR_APPLY = "ready_for_apply"
    HELD_FOR_REWORK = "held_for_rework"


class AssistedRouteRunStage(BaseModel):
    id: str
    label: str
    status: AssistedRouteRunStageStatus
    summary: str


class AssistedRouteOutput(BaseModel):
    id: str
    recommendation_id: str
    opportunity_id: str
    title: str
    summary: str
    recommended_destination: AssistedCaptureWorkProduct
    work_product_targets: tuple[AssistedCaptureWorkProduct, ...]
    capability_chain: tuple[str, ...]
    source_refs: tuple[str, ...]
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]
    review_state: AssistedRouteOutputReviewState = (
        AssistedRouteOutputReviewState.PENDING_REVIEW
    )


class AssistedRouteRun(BaseModel):
    id: str
    recommendation_id: str
    opportunity_id: str
    status: AssistedRouteRunStatus
    executor_kind: str = "deterministic_python"
    network_required: bool = False
    model_required: bool = False
    capability_progress: CapabilityRouteProgress
    stages: tuple[AssistedRouteRunStage, ...]
    output: AssistedRouteOutput


class AssistedRouteOutputReviewDecision(BaseModel):
    id: str
    output_id: str
    decision: AssistedRouteReviewDecisionType
    reviewer_rationale: str
    accepted_destination: AssistedCaptureWorkProduct | None = None
    review_gate: str


class WorkProductUpdateProjection(BaseModel):
    id: str
    source_output_id: str
    review_decision_id: str
    destination: AssistedCaptureWorkProduct
    state: WorkProductUpdateState
    before_summary: str
    after_summary: str
    source_refs: tuple[str, ...]


class AssistedRouteRecommendationRequest(BaseModel):
    goal_id: str
    operator_intent: str | None = None


class AssistedRouteRunRequest(BaseModel):
    approved: bool = False


class AssistedRouteOutputReviewRequest(BaseModel):
    decision: AssistedRouteReviewDecisionType
    reviewer_rationale: str
    accepted_destination: AssistedCaptureWorkProduct | None = None


class AssistedRouteRecommendationResponse(BaseModel):
    selection_prompt: AssistedCaptureSelectionPrompt
    goal: AssistedCaptureGoal
    recommendations: tuple[AssistedRouteRecommendation, ...]


class AssistedRouteRunResponse(BaseModel):
    run: AssistedRouteRun


class AssistedRouteOutputReviewResponse(BaseModel):
    output: AssistedRouteOutput
    decision: AssistedRouteOutputReviewDecision
    accepted_updates: tuple[WorkProductUpdateProjection, ...]


class AssistedRouteProvenanceView(BaseModel):
    recommendation: AssistedRouteRecommendation
    input_refs: tuple[str, ...]
    capability_chain: tuple[str, ...]
    reasoning: tuple[str, ...]
    run: AssistedRouteRun | None = None
    output: AssistedRouteOutput | None = None
    review_decisions: tuple[AssistedRouteOutputReviewDecision, ...] = ()
    work_product_updates: tuple[WorkProductUpdateProjection, ...] = ()


class AssistedRouteProvenanceResponse(BaseModel):
    provenance: AssistedRouteProvenanceView


class WorkProductUpdateListResponse(BaseModel):
    updates: tuple[WorkProductUpdateProjection, ...]
    summary: dict[str, int]


class ProductionCommandCenterHealthResponse(BaseModel):
    status: str = "ready"
    ui_contract: str = "nextjs_command_center_shell"
    api_contract_version: str = "v1"
    route_execution: str = "deterministic_local"
    review_gate_required: bool = True
    external_network_required: bool = False
    external_model_required: bool = False


class RendererCapability(BaseModel):
    id: str
    label: str
    engine: str
    output_formats: tuple[str, ...]
    readiness_state: str
    mvp_required: bool
    role: str


class RendererExportAction(BaseModel):
    id: str
    label: str
    renderer_id: str
    output_format: str
    review_required: bool
    enabled: bool
    disabled_reason: str


class RendererReadinessView(BaseModel):
    target_artifact: str
    target_label: str
    target_rationale: str
    renderers: tuple[RendererCapability, ...]
    export_actions: tuple[RendererExportAction, ...]
    backend_blockers: tuple[str, ...]


class RendererReadinessResponse(BaseModel):
    readiness: RendererReadinessView


class ProductionCommandCenterWorkspace(BaseModel):
    production_ui_contract: str
    scaffold_role: str
    opportunity: ProductionCommandCenterOpportunity
    packet: ProductionCommandCenterPacket
    context_summary: ProductionCommandCenterContextSummary
    layout_regions: tuple[ProductionCommandCenterRegion, ...]
    work_modes: tuple[ProductionCommandCenterWorkMode, ...]
    assisted_capture_goals: tuple[AssistedCaptureGoal, ...]


class OpportunityScaffoldStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write_scaffold(
        self,
        scaffold: ProductionOpportunityScaffold,
    ) -> ProductionOpportunityScaffold:
        self._scaffold_path(scaffold.opportunity.id).write_text(
            scaffold.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return scaffold

    def read_scaffold(self, opportunity_id: str) -> ProductionOpportunityScaffold:
        return ProductionOpportunityScaffold.model_validate_json(
            self._scaffold_path(opportunity_id).read_text(encoding="utf-8")
        )

    def has_scaffold(self, opportunity_id: str) -> bool:
        return self._scaffold_path(opportunity_id).exists()

    def list_scaffolds(self) -> tuple[ProductionOpportunityScaffold, ...]:
        return tuple(
            ProductionOpportunityScaffold.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            for path in sorted(self.root.glob("*.json"))
        )

    def _scaffold_path(self, opportunity_id: str) -> Path:
        if not opportunity_id or opportunity_id != Path(opportunity_id).name:
            raise ValueError("opportunity_id must be a file-safe identifier")
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root / f"{opportunity_id}.json"


class WorkflowRoutingStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write_recommendations(
        self,
        recommendations: tuple[AssistedRouteRecommendation, ...],
    ) -> tuple[AssistedRouteRecommendation, ...]:
        for recommendation in recommendations:
            self._recommendation_path(recommendation.id).write_text(
                recommendation.model_dump_json(indent=2),
                encoding="utf-8",
            )
        return recommendations

    def read_recommendation(self, recommendation_id: str) -> AssistedRouteRecommendation:
        return AssistedRouteRecommendation.model_validate_json(
            self._recommendation_path(recommendation_id).read_text(encoding="utf-8")
        )

    def write_run(self, run: AssistedRouteRun) -> AssistedRouteRun:
        self._run_path(run.id).write_text(run.model_dump_json(indent=2), encoding="utf-8")
        self.write_output(run.output)
        return run

    def read_run(self, run_id: str) -> AssistedRouteRun:
        return AssistedRouteRun.model_validate_json(
            self._run_path(run_id).read_text(encoding="utf-8")
        )

    def list_runs(self) -> tuple[AssistedRouteRun, ...]:
        return tuple(
            AssistedRouteRun.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._child_dir("runs").glob("*.json"))
        )

    def write_output(self, output: AssistedRouteOutput) -> AssistedRouteOutput:
        self._output_path(output.id).write_text(
            output.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return output

    def read_output(self, output_id: str) -> AssistedRouteOutput:
        return AssistedRouteOutput.model_validate_json(
            self._output_path(output_id).read_text(encoding="utf-8")
        )

    def write_review_decision(
        self,
        decision: AssistedRouteOutputReviewDecision,
    ) -> AssistedRouteOutputReviewDecision:
        self._decision_path(decision.id).write_text(
            decision.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return decision

    def list_review_decisions(self) -> tuple[AssistedRouteOutputReviewDecision, ...]:
        return tuple(
            AssistedRouteOutputReviewDecision.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            for path in sorted(self._child_dir("review-decisions").glob("*.json"))
        )

    def write_work_product_update(
        self,
        update: WorkProductUpdateProjection,
    ) -> WorkProductUpdateProjection:
        self._work_product_update_path(update.id).write_text(
            update.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return update

    def list_work_product_updates(self) -> tuple[WorkProductUpdateProjection, ...]:
        return tuple(
            WorkProductUpdateProjection.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            for path in sorted(self._child_dir("work-product-updates").glob("*.json"))
        )

    def _recommendation_path(self, recommendation_id: str) -> Path:
        if not recommendation_id or recommendation_id != Path(recommendation_id).name:
            raise ValueError("recommendation_id must be a file-safe identifier")
        return self._child_path("recommendations", recommendation_id)

    def _run_path(self, run_id: str) -> Path:
        if not run_id or run_id != Path(run_id).name:
            raise ValueError("run_id must be a file-safe identifier")
        return self._child_path("runs", run_id)

    def _output_path(self, output_id: str) -> Path:
        if not output_id or output_id != Path(output_id).name:
            raise ValueError("output_id must be a file-safe identifier")
        return self._child_path("outputs", output_id)

    def _decision_path(self, decision_id: str) -> Path:
        if not decision_id or decision_id != Path(decision_id).name:
            raise ValueError("decision_id must be a file-safe identifier")
        return self._child_path("review-decisions", decision_id)

    def _work_product_update_path(self, update_id: str) -> Path:
        if not update_id or update_id != Path(update_id).name:
            raise ValueError("update_id must be a file-safe identifier")
        return self._child_path("work-product-updates", update_id)

    def _child_path(self, child_dir: str, record_id: str) -> Path:
        directory = self._child_dir(child_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{record_id}.json"

    def _child_dir(self, child_dir: str) -> Path:
        return self.root / child_dir


ASSISTED_CAPTURE_GOALS: tuple[AssistedCaptureGoal, ...] = (
    AssistedCaptureGoal(
        id="prepare_customer_call",
        label="Prepare customer call",
        description="Turn known gaps and trusted context into a call plan and follow-up work.",
        primary_work_product=AssistedCaptureWorkProduct.CALL_PLAN,
        work_product_targets=(
            AssistedCaptureWorkProduct.CALL_PLAN,
            AssistedCaptureWorkProduct.LIVING_PACKET,
            AssistedCaptureWorkProduct.ACTION_PLAN,
        ),
    ),
    AssistedCaptureGoal(
        id="close_packet_gap",
        label="Close packet gap",
        description="Route trusted and reviewable context toward the next packet answer.",
        primary_work_product=AssistedCaptureWorkProduct.LIVING_PACKET,
        work_product_targets=(
            AssistedCaptureWorkProduct.LIVING_PACKET,
            AssistedCaptureWorkProduct.ACTION_PLAN,
        ),
    ),
    AssistedCaptureGoal(
        id="build_capture_action_plan",
        label="Build capture action plan",
        description="Convert open gaps into sequenced capture actions with review gates.",
        primary_work_product=AssistedCaptureWorkProduct.ACTION_PLAN,
        work_product_targets=(
            AssistedCaptureWorkProduct.ACTION_PLAN,
            AssistedCaptureWorkProduct.CAPTURE_RESEARCH,
        ),
    ),
)


CAPABILITY_STEP_METADATA: dict[str, tuple[str, str, str, str]] = {
    "knowledge_context_review": (
        "Knowledge context review",
        "skill",
        "deterministic_python",
        "Route inputs",
    ),
    "capture_research_enrichment": (
        "Capture research enrichment",
        "workflow",
        "deterministic_python",
        "Customer insight",
    ),
    "call_plan_draft": (
        "Call plan draft",
        "skill",
        "deterministic_python",
        "Call Plan",
    ),
    "packet_gap_review": (
        "Packet gap review",
        "skill",
        "deterministic_python",
        "Packet gaps",
    ),
    "next_action_recommendation": (
        "Next action recommendation",
        "workflow",
        "deterministic_python",
        "Action Plan",
    ),
    "packet_answer_draft": (
        "Packet answer draft",
        "skill",
        "deterministic_python",
        "Living Packet",
    ),
    "action_plan_update": (
        "Action plan update",
        "skill",
        "deterministic_python",
        "Action Plan",
    ),
}


def create_standard_opportunity_scaffold(
    *,
    request: ProductionOpportunityIntakeRequest,
    store: OpportunityScaffoldStore,
) -> ProductionOpportunityScaffold:
    opportunity_name = request.name.strip()
    if not opportunity_name:
        raise ValueError("Opportunity name is required")

    rationale = (
        request.rationale.strip()
        if request.rationale and request.rationale.strip()
        else "Capture operator identified this Opportunity for Ariadne activation."
    )
    opportunity_id = _opportunity_id_from_name(opportunity_name)
    entry_context = EntryContext(
        reason=request.entry_reason,
        starting_lifecycle_state=request.starting_lifecycle_state,
        rationale=rationale,
        missing_or_stale_workstreams=set(request.missing_or_stale_workstreams),
    )
    opportunity = create_opportunity(
        name=opportunity_name,
        entry_context=entry_context,
    )
    packet = create_living_briefing_packet(opportunity)
    packet_states = tuple(packet.sections.values())
    definitions = build_default_packet_field_definitions()
    packet_field_slots = tuple(
        _packet_field_slot_for_new_opportunity(
            opportunity_id=opportunity_id,
            definition=definition,
        )
        for definition in definitions
    )

    scaffold = ProductionOpportunityScaffold(
        opportunity=ProductionCommandCenterOpportunity(
            id=opportunity_id,
            name=opportunity.name,
            lifecycle_state=opportunity.lifecycle_state.value,
            gate_status="opportunity_activation_ready",
        ),
        entry_reason=entry_context.reason.value,
        entry_rationale=entry_context.rationale,
        workstreams=tuple(
            ProductionOpportunityWorkstream(
                id=workstream.value,
                label=_label_from_identifier(workstream.value),
                status=state.status.value,
            )
            for workstream, state in opportunity.workstreams.items()
        ),
        backfill_needs=tuple(
            ProductionOpportunityBackfillNeed(
                workstream_id=need.workstream.value,
                label=_label_from_identifier(need.workstream.value),
                rationale=need.rationale,
            )
            for need in opportunity.backfill_needs
        ),
        packet=ProductionCommandCenterPacket(
            title="Living Milestone Decision Briefing Packet",
            readiness_label=packet.readiness.value,
            answered_section_count=0,
            gap_section_count=sum(
                1 for state in packet_states if state.evidence_status is EvidenceStatus.GAP
            ),
            partial_section_count=0,
        ),
        packet_sections=tuple(
            ProductionOpportunityPacketSection(
                id=state.section.value,
                label=_label_from_identifier(state.section.value),
                evidence_status=state.evidence_status.value,
            )
            for state in packet_states
        ),
        packet_fields=packet_field_slots,
        activation_digest=_activation_digest_for_new_opportunity(
            packet_field_count=len(packet_field_slots),
            packet_section_count=len(packet_states),
            workstream_count=len(opportunity.workstreams),
        ),
    )
    return store.write_scaffold(scaffold)


def build_production_command_center_workspace(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> ProductionCommandCenterWorkspace:
    demo = build_quick_capture_demo_thread(
        settings,
        workspace_root=workspace_root or Path.cwd(),
    )
    packet_states = tuple(demo.packet.sections.values())
    gap_count = sum(1 for state in packet_states if state.evidence_status is EvidenceStatus.GAP)
    partial_count = sum(
        1 for state in packet_states if state.evidence_status is EvidenceStatus.PARTIAL
    )
    answered_count = sum(
        1 for state in packet_states if state.evidence_status is EvidenceStatus.ANSWERED
    )
    reviewable_count = (
        len(demo.capture_review.proposals)
        + len(demo.pasted_review.proposals)
        + len(demo.uploaded_review.proposals)
        + len(demo.document_intake.candidates)
    )

    return ProductionCommandCenterWorkspace(
        production_ui_contract="nextjs_command_center_shell",
        scaffold_role="fallback_debug_only",
        opportunity=ProductionCommandCenterOpportunity(
            id="opp-aflcmc-recompete",
            name=demo.opportunity.name,
            lifecycle_state=demo.opportunity.lifecycle_state.value,
            gate_status="capture_working_session",
        ),
        packet=ProductionCommandCenterPacket(
            title="Living Milestone Decision Briefing Packet",
            readiness_label=demo.packet.readiness.value,
            answered_section_count=answered_count,
            gap_section_count=gap_count,
            partial_section_count=partial_count,
        ),
        context_summary=ProductionCommandCenterContextSummary(
            trusted_count=3,
            reviewable_count=reviewable_count,
            gap_count=gap_count + partial_count,
            source_limitation_count=len(demo.unsupported_upload.warnings),
        ),
        layout_regions=(
            ProductionCommandCenterRegion(
                id="left_rail",
                label="Opportunity and work-mode navigation",
                purpose="Switch Opportunity, inspect gate state, and move between work modes.",
            ),
            ProductionCommandCenterRegion(
                id="packet_workspace",
                label="Living Milestone Decision Briefing Packet workspace",
                purpose="Show packet readiness, supported answers, gaps, assumptions, and source chips.",
            ),
            ProductionCommandCenterRegion(
                id="command_review_rail",
                label="Command and review rail",
                purpose="Start assisted capture, inspect route recommendations, and review output.",
            ),
            ProductionCommandCenterRegion(
                id="provenance_drawer",
                label="Provenance and output inspection",
                purpose="Inspect sources, route rationale, run details, and output trace.",
            ),
        ),
        work_modes=(
            ProductionCommandCenterWorkMode(id="packet", label="Packet", pending_count=gap_count + partial_count),
            ProductionCommandCenterWorkMode(id="actions", label="Actions", pending_count=len(demo.action_plan.items)),
            ProductionCommandCenterWorkMode(id="engagement", label="Engagement"),
            ProductionCommandCenterWorkMode(id="research", label="Research"),
            ProductionCommandCenterWorkMode(id="documents", label="Documents", pending_count=1),
            ProductionCommandCenterWorkMode(id="artifacts", label="Artifacts"),
            ProductionCommandCenterWorkMode(id="capability_studio", label="Capability Studio"),
        ),
        assisted_capture_goals=ASSISTED_CAPTURE_GOALS,
    )


def production_command_center_health() -> ProductionCommandCenterHealthResponse:
    return ProductionCommandCenterHealthResponse()


def build_renderer_readiness() -> RendererReadinessResponse:
    readiness = RendererReadinessView(
        target_artifact="living_milestone_decision_briefing_packet",
        target_label="Living Milestone Decision Briefing Packet",
        target_rationale=(
            "The Living Packet is the central accumulation artifact for capture "
            "decisions, call prep, and downstream export readiness."
        ),
        renderers=(
            RendererCapability(
                id="huashu_design_pptx",
                label="Milestone briefing deck",
                engine="huashu-design",
                output_formats=("pptx",),
                readiness_state="planned_integration",
                mvp_required=True,
                role="Visual briefing deck and slide export path.",
            ),
            RendererCapability(
                id="pandoc_docx",
                label="Narrative briefing document",
                engine="pandoc",
                output_formats=("docx",),
                readiness_state="planned_integration",
                mvp_required=True,
                role="DOCX narrative packet export path.",
            ),
            RendererCapability(
                id="xlsx_export",
                label="Capture workbook export",
                engine="xlsx-export",
                output_formats=("xlsx",),
                readiness_state="planned_integration",
                mvp_required=True,
                role="XLSX tabular export path for action, risk, and evidence views.",
            ),
        ),
        export_actions=(
            RendererExportAction(
                id="export_packet_pptx",
                label="Prepare PPTX briefing deck",
                renderer_id="huashu_design_pptx",
                output_format="pptx",
                review_required=True,
                enabled=False,
                disabled_reason="huashu-design adapter is not wired yet.",
            ),
            RendererExportAction(
                id="export_packet_docx",
                label="Prepare DOCX narrative brief",
                renderer_id="pandoc_docx",
                output_format="docx",
                review_required=True,
                enabled=False,
                disabled_reason="Pandoc DOCX adapter is not wired yet.",
            ),
            RendererExportAction(
                id="export_packet_xlsx",
                label="Prepare XLSX capture workbook",
                renderer_id="xlsx_export",
                output_format="xlsx",
                review_required=True,
                enabled=False,
                disabled_reason="XLSX export adapter is not wired yet.",
            ),
        ),
        backend_blockers=(
            "Renderer execution adapters are not wired in this UI epic.",
            "Exports stay disabled until renderer adapters produce reviewable artifact drafts.",
        ),
    )
    return RendererReadinessResponse(readiness=readiness)


def recommend_assisted_capture_routes(
    *,
    opportunity_id: str,
    goal_id: str,
    store: WorkflowRoutingStore | None = None,
) -> AssistedRouteRecommendationResponse:
    goal = _goal_by_id(goal_id)
    recommendations = _recommendations_for_goal(opportunity_id=opportunity_id, goal=goal)
    if store is not None:
        store.write_recommendations(recommendations)
    return AssistedRouteRecommendationResponse(
        selection_prompt=AssistedCaptureSelectionPrompt(),
        goal=goal,
        recommendations=recommendations,
    )


def production_opportunity_context_exists(
    opportunity_id: str,
    *,
    store: OpportunityScaffoldStore,
) -> bool:
    return opportunity_id == "opp-aflcmc-recompete" or store.has_scaffold(opportunity_id)


def execute_assisted_capture_route(
    *,
    store: WorkflowRoutingStore,
    recommendation_id: str,
    approved: bool,
) -> AssistedRouteRun:
    if not approved:
        raise PermissionError("Route execution requires explicit operator approval")
    recommendation = store.read_recommendation(recommendation_id)
    output = AssistedRouteOutput(
        id=f"output_{recommendation.id}_reviewable-draft",
        recommendation_id=recommendation.id,
        opportunity_id=recommendation.opportunity_id,
        title=_output_title_for_route(recommendation),
        summary=_output_summary_for_route(recommendation),
        recommended_destination=recommendation.work_product_targets[0],
        work_product_targets=recommendation.work_product_targets,
        capability_chain=recommendation.recommended_capability_chain,
        source_refs=recommendation.input_refs,
        assumptions=(
            "Draft content remains reviewable until the capture operator accepts it.",
            "No external model or network call was used for this deterministic run.",
        ),
        gaps=(
            "Validate customer decision-maker map before treating call-plan content as trusted.",
        ),
    )
    run = AssistedRouteRun(
        id=f"run_{recommendation.id}_deterministic-draft",
        recommendation_id=recommendation.id,
        opportunity_id=recommendation.opportunity_id,
        status=AssistedRouteRunStatus.NEEDS_REVIEW,
        stages=(
            AssistedRouteRunStage(
                id="inspect_inputs",
                label="Inspect route inputs",
                status=AssistedRouteRunStageStatus.SUCCEEDED,
                summary="Loaded the recommended route and source references.",
            ),
            AssistedRouteRunStage(
                id="apply_capability_chain",
                label="Apply deterministic capability chain",
                status=AssistedRouteRunStageStatus.SUCCEEDED,
                summary="Applied route-specific capture drafting heuristics.",
            ),
            AssistedRouteRunStage(
                id="prepare_reviewable_output",
                label="Prepare reviewable output",
                status=AssistedRouteRunStageStatus.SUCCEEDED,
                summary="Created one review-gated work product draft.",
            ),
        ),
        capability_progress=_capability_progress_for_route(
            recommendation.capability_route_card
        ),
        output=output,
    )
    return store.write_run(run)


def review_assisted_route_output(
    *,
    store: WorkflowRoutingStore,
    output_id: str,
    request: AssistedRouteOutputReviewRequest,
) -> AssistedRouteOutputReviewResponse:
    output = store.read_output(output_id)
    review_state = (
        AssistedRouteOutputReviewState.ACCEPTED
        if request.decision is AssistedRouteReviewDecisionType.ACCEPT
        else AssistedRouteOutputReviewState.REJECTED
    )
    reviewed_output = output.model_copy(update={"review_state": review_state})
    store.write_output(reviewed_output)
    decision = AssistedRouteOutputReviewDecision(
        id=f"decision_{output_id}_{request.decision.value}",
        output_id=output_id,
        decision=request.decision,
        reviewer_rationale=request.reviewer_rationale,
        accepted_destination=request.accepted_destination,
        review_gate=(
            "human_accepted"
            if request.decision is AssistedRouteReviewDecisionType.ACCEPT
            else "human_rejected"
        ),
    )
    store.write_review_decision(decision)
    accepted_updates = (
        _work_product_updates_for_acceptance(reviewed_output, decision)
        if request.decision is AssistedRouteReviewDecisionType.ACCEPT
        else ()
    )
    for update in accepted_updates:
        store.write_work_product_update(update)
    return AssistedRouteOutputReviewResponse(
        output=reviewed_output,
        decision=decision,
        accepted_updates=accepted_updates,
    )


def get_assisted_route_provenance(
    *,
    store: WorkflowRoutingStore,
    recommendation_id: str,
) -> AssistedRouteProvenanceResponse:
    recommendation = store.read_recommendation(recommendation_id)
    matching_runs = tuple(
        run for run in store.list_runs() if run.recommendation_id == recommendation_id
    )
    run = matching_runs[-1] if matching_runs else None
    output = None
    if run is not None:
        output = store.read_output(run.output.id)
    output_id = output.id if output is not None else None
    review_decisions = tuple(
        decision
        for decision in store.list_review_decisions()
        if decision.output_id == output_id
    )
    stored_updates = tuple(
        update
        for update in store.list_work_product_updates()
        if update.source_output_id == output_id
    )
    work_product_updates = _ordered_updates_for_output(output, stored_updates)
    return AssistedRouteProvenanceResponse(
        provenance=AssistedRouteProvenanceView(
            recommendation=recommendation,
            input_refs=recommendation.input_refs,
            capability_chain=recommendation.recommended_capability_chain,
            reasoning=recommendation.reasoning,
            run=run,
            output=output,
            review_decisions=review_decisions,
            work_product_updates=work_product_updates,
        )
    )


def list_work_product_update_projections(
    *,
    store: WorkflowRoutingStore,
) -> WorkProductUpdateListResponse:
    updates = _ordered_work_product_updates(store.list_work_product_updates())
    summary: dict[str, int] = {}
    for update in updates:
        summary[update.destination.value] = summary.get(update.destination.value, 0) + 1
    return WorkProductUpdateListResponse(updates=updates, summary=summary)


def _opportunity_id_from_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    stable_slug = slug[:48].strip("-") or "opportunity"
    digest = sha256(name.encode("utf-8")).hexdigest()[:10]
    return f"opp-{stable_slug}-{digest}"


def _label_from_identifier(identifier: str) -> str:
    return " ".join(part.capitalize() for part in identifier.split("_"))


def _packet_field_slot_for_new_opportunity(
    *,
    opportunity_id: str,
    definition: PacketFieldDefinition,
) -> ProductionOpportunityPacketFieldSlot:
    answer = create_packet_field_answer(
        field_key=definition.key,
        opportunity_id=opportunity_id,
        status=PacketFieldAnswerStatus.UNANSWERED,
        evidence_status=EvidenceStatus.GAP,
        gap_summary=f"{definition.label} has not been answered for this Opportunity.",
        provenance_note="Created by the production Opportunity intake scaffold.",
    )
    return ProductionOpportunityPacketFieldSlot(
        key=definition.key,
        label=definition.label,
        question=definition.question,
        section=definition.section.value,
        status=answer.status.value,
        evidence_status=answer.evidence_status.value,
        answer_paths=tuple(path.label for path in definition.answer_paths),
        recommended_route=_recommended_route_for_definition(definition),
    )


def _recommended_route_for_definition(definition: PacketFieldDefinition) -> str:
    kinds = {path.kind for path in definition.answer_paths}
    if AnswerPathKind.CAPABILITY_MODULE in kinds:
        return "Recommend a capability or skill-backed research route."
    if AnswerPathKind.EVIDENCE_EXTRACTION in kinds:
        return "Inspect source material and extract a reviewable answer candidate."
    if AnswerPathKind.IMPORTED_DATA in kinds:
        return "Import or lookup source-profile data before synthesis."
    if AnswerPathKind.MODEL_SYNTHESIS in kinds:
        return "Synthesize a reviewable answer from accepted evidence and gaps."
    return "Ask the capture lead or prepare a customer follow-up question."


def _activation_digest_for_new_opportunity(
    *,
    packet_field_count: int,
    packet_section_count: int,
    workstream_count: int,
) -> OpportunityActivationDigest:
    return OpportunityActivationDigest(
        coverage_gained=(
            f"Created {workstream_count} standard capture workstreams.",
            f"Created {packet_section_count} Living Packet sections.",
            f"Created {packet_field_count} packet field action slots.",
        ),
        review_ready_count=0,
        blocked_field_count=packet_field_count,
        recommended_skill_chains=(
            "source-profile lookup -> packet implication -> action recommendation",
            "research brief -> customer insight -> call-plan prep",
            "requirements fit -> packet implication -> action recommendation",
        ),
        approval_required_routes=(
            "Approve live source collection before public web research runs.",
            "Approve official attachment downloads before document intake.",
            "Review customer-facing material before export or delivery.",
        ),
        source_limitations=(
            "No accepted source evidence is attached to this Opportunity yet.",
            "No source profile has been selected for deterministic lookup yet.",
        ),
        next_best_actions=(
            "Attach source material or approve source discovery.",
            "Run the Packet Field Action Matrix against the new scaffold.",
            "Prepare customer questions for fields Ariadne cannot answer safely.",
        ),
    )


def _goal_by_id(goal_id: str) -> AssistedCaptureGoal:
    for goal in ASSISTED_CAPTURE_GOALS:
        if goal.id == goal_id:
            return goal
    raise ValueError(f"Unsupported assisted capture goal: {goal_id}")


def _recommendations_for_goal(
    *,
    opportunity_id: str,
    goal: AssistedCaptureGoal,
) -> tuple[AssistedRouteRecommendation, ...]:
    if goal.id == "prepare_customer_call":
        return (
            AssistedRouteRecommendation(
                id=(recommendation_id := f"route_{opportunity_id}_{goal.id}_customer-call-plan"),
                opportunity_id=opportunity_id,
                goal_id=goal.id,
                route_label="Customer call plan route",
                route_summary=(
                    "Review trusted context, enrich customer pain, and draft a call "
                    "plan with follow-up actions."
                ),
                autonomy_tier=AssistedCaptureAutonomyTier.HUMAN_APPROVAL_REQUIRED,
                work_product_targets=goal.work_product_targets,
                recommended_capability_chain=(
                    "knowledge_context_review",
                    "capture_research_enrichment",
                    "call_plan_draft",
                ),
                capability_route_card=_capability_route_card(
                    recommendation_id=recommendation_id,
                    title="Customer call plan route",
                    capability_chain=(
                        "knowledge_context_review",
                        "capture_research_enrichment",
                        "call_plan_draft",
                    ),
                ),
                input_refs=(
                    "packet.customer_context",
                    "evidence.ev_customer_call",
                    "action_plan.customer_insight_backfill",
                ),
                reasoning=(
                    "Customer context gap is partially supported and needs a validated "
                    "decision-maker map before the next engagement.",
                    "A call plan is the shortest useful work product because it can "
                    "feed the Living Packet and Action Plan after review.",
                ),
            ),
            AssistedRouteRecommendation(
                id=(recommendation_id := f"route_{opportunity_id}_{goal.id}_packet-gap-triage"),
                opportunity_id=opportunity_id,
                goal_id=goal.id,
                route_label="Packet gap triage route",
                route_summary=(
                    "Summarize packet gaps and propose the next evidence collection "
                    "moves before drafting engagement material."
                ),
                autonomy_tier=AssistedCaptureAutonomyTier.ASK_BEFORE_RUNNING,
                work_product_targets=(
                    AssistedCaptureWorkProduct.LIVING_PACKET,
                    AssistedCaptureWorkProduct.ACTION_PLAN,
                ),
                recommended_capability_chain=(
                    "packet_gap_review",
                    "next_action_recommendation",
                ),
                capability_route_card=_capability_route_card(
                    recommendation_id=recommendation_id,
                    title="Packet gap triage route",
                    capability_chain=(
                        "packet_gap_review",
                        "next_action_recommendation",
                    ),
                ),
                input_refs=(
                    "packet.customer_context",
                    "packet.risks_and_gaps",
                ),
                reasoning=(
                    "Packet gaps should stay visible before any call plan content is "
                    "treated as trusted capture knowledge.",
                ),
            ),
        )
    if goal.id == "close_packet_gap":
        return (
            AssistedRouteRecommendation(
                id=(recommendation_id := f"route_{opportunity_id}_{goal.id}_packet-answer-draft"),
                opportunity_id=opportunity_id,
                goal_id=goal.id,
                route_label="Packet answer draft route",
                route_summary="Draft a reviewable packet answer from trusted source refs.",
                autonomy_tier=AssistedCaptureAutonomyTier.HUMAN_APPROVAL_REQUIRED,
                work_product_targets=goal.work_product_targets,
                recommended_capability_chain=(
                    "knowledge_context_review",
                    "packet_answer_draft",
                ),
                capability_route_card=_capability_route_card(
                    recommendation_id=recommendation_id,
                    title="Packet answer draft route",
                    capability_chain=(
                        "knowledge_context_review",
                        "packet_answer_draft",
                    ),
                ),
                input_refs=("packet.customer_context", "evidence.ev_customer_call"),
                reasoning=(
                    "The Living Packet has a partial customer-context answer that can "
                    "be advanced with source-backed review.",
                ),
            ),
        )
    return (
        AssistedRouteRecommendation(
            id=(recommendation_id := f"route_{opportunity_id}_{goal.id}_action-plan-sequence"),
            opportunity_id=opportunity_id,
            goal_id=goal.id,
            route_label="Action plan sequencing route",
            route_summary="Turn open workstreams and packet gaps into next capture actions.",
            autonomy_tier=AssistedCaptureAutonomyTier.HUMAN_APPROVAL_REQUIRED,
            work_product_targets=goal.work_product_targets,
            recommended_capability_chain=(
                "knowledge_context_review",
                "next_action_recommendation",
                "action_plan_update",
            ),
            capability_route_card=_capability_route_card(
                recommendation_id=recommendation_id,
                title="Action plan sequencing route",
                capability_chain=(
                    "knowledge_context_review",
                    "next_action_recommendation",
                    "action_plan_update",
                ),
            ),
            input_refs=("action_plan", "packet.gaps", "capability_catalog"),
            reasoning=(
                "Backfill workstreams should be converted into reviewable actions "
                "before downstream capture work depends on them.",
            ),
        ),
    )


def _output_title_for_route(recommendation: AssistedRouteRecommendation) -> str:
    if recommendation.route_label == "Customer call plan route":
        return "Customer call plan draft"
    if recommendation.route_label == "Packet answer draft route":
        return "Packet answer draft"
    if recommendation.route_label == "Action plan sequencing route":
        return "Capture action plan update draft"
    return f"{recommendation.route_label} output draft"


def _output_summary_for_route(recommendation: AssistedRouteRecommendation) -> str:
    if recommendation.route_label == "Customer call plan route":
        return (
            "Draft call objective, key questions, likely customer concerns, and "
            "follow-up actions from the current packet gap and trusted context."
        )
    if recommendation.route_label == "Packet answer draft route":
        return "Draft a source-backed packet answer for review before promotion."
    if recommendation.route_label == "Action plan sequencing route":
        return "Draft sequenced capture actions from packet gaps and workstream backfill."
    return recommendation.route_summary


def _work_product_updates_for_acceptance(
    output: AssistedRouteOutput,
    decision: AssistedRouteOutputReviewDecision,
) -> tuple[WorkProductUpdateProjection, ...]:
    return tuple(
        WorkProductUpdateProjection(
            id=f"update_{output.id}_{destination.value}",
            source_output_id=output.id,
            review_decision_id=decision.id,
            destination=destination,
            state=WorkProductUpdateState.READY_FOR_APPLY,
            before_summary=_before_summary_for_destination(destination),
            after_summary=_after_summary_for_destination(output, destination),
            source_refs=output.source_refs,
        )
        for destination in output.work_product_targets
    )


def _before_summary_for_destination(destination: AssistedCaptureWorkProduct) -> str:
    if destination is AssistedCaptureWorkProduct.CALL_PLAN:
        return "No accepted call-plan draft from this assisted route."
    if destination is AssistedCaptureWorkProduct.LIVING_PACKET:
        return "Packet gap remains open until the accepted route output is applied."
    if destination is AssistedCaptureWorkProduct.ACTION_PLAN:
        return "Action Plan has no accepted follow-up from this route."
    return "No accepted update from this assisted route."


def _after_summary_for_destination(
    output: AssistedRouteOutput,
    destination: AssistedCaptureWorkProduct,
) -> str:
    if destination is AssistedCaptureWorkProduct.CALL_PLAN:
        return output.summary
    if destination is AssistedCaptureWorkProduct.LIVING_PACKET:
        return "Add a packet note that the customer call plan is ready for review-backed use."
    if destination is AssistedCaptureWorkProduct.ACTION_PLAN:
        return "Add follow-up actions for PM engagement and decision-maker validation."
    return output.summary


def _ordered_updates_for_output(
    output: AssistedRouteOutput | None,
    updates: tuple[WorkProductUpdateProjection, ...],
) -> tuple[WorkProductUpdateProjection, ...]:
    if output is None:
        return updates
    updates_by_destination = {update.destination: update for update in updates}
    return tuple(
        updates_by_destination[destination]
        for destination in output.work_product_targets
        if destination in updates_by_destination
    )


def _ordered_work_product_updates(
    updates: tuple[WorkProductUpdateProjection, ...],
) -> tuple[WorkProductUpdateProjection, ...]:
    destination_order = {
        AssistedCaptureWorkProduct.CALL_PLAN: 0,
        AssistedCaptureWorkProduct.LIVING_PACKET: 1,
        AssistedCaptureWorkProduct.ACTION_PLAN: 2,
        AssistedCaptureWorkProduct.CAPTURE_RESEARCH: 3,
        AssistedCaptureWorkProduct.MARKETING_SKILL: 4,
    }
    return tuple(
        sorted(
            updates,
            key=lambda update: (
                destination_order.get(update.destination, 99),
                update.id,
            ),
        )
    )


def _capability_route_card(
    *,
    recommendation_id: str,
    title: str,
    capability_chain: tuple[str, ...],
) -> CapabilityRouteCard:
    steps = tuple(_capability_route_step(capability_id) for capability_id in capability_chain)
    return CapabilityRouteCard(
        id=f"card_{recommendation_id}",
        title=title,
        capability_count=len(steps),
        steps=steps,
    )


def _capability_route_step(
    capability_id: str,
    *,
    status: CapabilityRouteStepStatus = CapabilityRouteStepStatus.PLANNED,
) -> CapabilityRouteStep:
    label, capability_type, executor_kind, output_target = CAPABILITY_STEP_METADATA.get(
        capability_id,
        (capability_id.replace("_", " ").title(), "skill", "deterministic_python", "Review output"),
    )
    return CapabilityRouteStep(
        capability_id=capability_id,
        label=label,
        capability_type=capability_type,
        executor_kind=executor_kind,
        output_target=output_target,
        status=status,
    )


def _capability_progress_for_route(
    route_card: CapabilityRouteCard,
) -> CapabilityRouteProgress:
    steps = tuple(
        _capability_route_step(
            step.capability_id,
            status=CapabilityRouteStepStatus.SUCCEEDED,
        )
        for step in route_card.steps
    )
    return CapabilityRouteProgress(percent_complete=100, steps=steps)