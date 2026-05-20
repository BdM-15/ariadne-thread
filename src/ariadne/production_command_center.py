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
    input_refs: tuple[str, ...]
    reasoning: tuple[str, ...]
    status: str = "recommended"


class AssistedRouteRecommendationRequest(BaseModel):
    goal_id: str
    operator_intent: str | None = None


class AssistedRouteRecommendationResponse(BaseModel):
    selection_prompt: AssistedCaptureSelectionPrompt
    goal: AssistedCaptureGoal
    recommendations: tuple[AssistedRouteRecommendation, ...]


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
        self.root.mkdir(parents=True, exist_ok=True)
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

    def _recommendation_path(self, recommendation_id: str) -> Path:
        if not recommendation_id or recommendation_id != Path(recommendation_id).name:
            raise ValueError("recommendation_id must be a file-safe identifier")
        return self.root / f"{recommendation_id}.json"


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
                id=f"route_{opportunity_id}_{goal.id}_customer-call-plan",
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
                id=f"route_{opportunity_id}_{goal.id}_packet-gap-triage",
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
                id=f"route_{opportunity_id}_{goal.id}_packet-answer-draft",
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
                input_refs=("packet.customer_context", "evidence.ev_customer_call"),
                reasoning=(
                    "The Living Packet has a partial customer-context answer that can "
                    "be advanced with source-backed review.",
                ),
            ),
        )
    return (
        AssistedRouteRecommendation(
            id=f"route_{opportunity_id}_{goal.id}_action-plan-sequence",
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
            input_refs=("action_plan", "packet.gaps", "capability_catalog"),
            reasoning=(
                "Backfill workstreams should be converted into reviewable actions "
                "before downstream capture work depends on them.",
            ),
        ),
    )