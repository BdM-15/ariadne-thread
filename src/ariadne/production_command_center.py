from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from ariadne.config import RuntimeSettings
from ariadne.packets import EvidenceStatus
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


class ProductionCommandCenterWorkspace(BaseModel):
    production_ui_contract: str
    scaffold_role: str
    opportunity: ProductionCommandCenterOpportunity
    packet: ProductionCommandCenterPacket
    context_summary: ProductionCommandCenterContextSummary
    layout_regions: tuple[ProductionCommandCenterRegion, ...]
    work_modes: tuple[ProductionCommandCenterWorkMode, ...]
    assisted_capture_goals: tuple[AssistedCaptureGoal, ...]


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