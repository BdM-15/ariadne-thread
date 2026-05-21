from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ariadne.opportunity_activation import PacketFieldActionItem, PacketFieldRouteKind


class SkillChainMissingInput(BaseModel):
    stage_id: str
    input_key: str
    question: str


class SkillChainPlanStage(BaseModel):
    stage_id: str
    title: str
    capability_id: str
    depends_on: tuple[str, ...] = ()
    input_expectations: tuple[str, ...] = ()
    accepted_inputs: tuple[str, ...] = ()
    produced_handoff_type: str
    search_retrieval_hints: tuple[str, ...] = ()
    quality_gate: str
    review_destination: str
    missing_input_question: str | None = None


class SkillChainPlanMap(BaseModel):
    plan_id: str
    title: str
    source: str
    capture_goal: str | None = None
    route_kind: str | None = None
    stages: tuple[SkillChainPlanStage, ...]
    missing_inputs: tuple[SkillChainMissingInput, ...] = ()
    execution_mode: str = "deterministic_plan_map"
    langgraph_runtime_used: bool = False
    network_required: bool = False
    model_required: bool = False
    trusted_downstream_writes: bool = False
    provenance: dict[str, Any] = Field(default_factory=dict)


class SkillChainPlanStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, plan: SkillChainPlanMap) -> SkillChainPlanMap:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{plan.plan_id}.json"
        path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        return plan

    def read(self, plan_id: str) -> SkillChainPlanMap:
        path = self.root / f"{plan_id}.json"
        return SkillChainPlanMap.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[SkillChainPlanMap]:
        if not self.root.exists():
            return []
        return [
            SkillChainPlanMap.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root.glob("*.json"))
        ]


def build_skill_chain_plan_from_capture_goal(
    *,
    capture_goal: str,
    available_inputs: tuple[str, ...] = (),
) -> SkillChainPlanMap:
    goal_slug = _slug(capture_goal)
    specs = _CAPTURE_GOAL_TEMPLATES.get(goal_slug, _generic_goal_template(capture_goal))
    stages, missing_inputs = _build_stages(specs, available_inputs)
    return SkillChainPlanMap(
        plan_id=f"chain_plan_{goal_slug}",
        title=capture_goal,
        source="capture_goal",
        capture_goal=capture_goal,
        stages=stages,
        missing_inputs=missing_inputs,
        provenance={
            "source": "capture_goal",
            "capture_goal": capture_goal,
            "trusted_downstream_writes": False,
        },
    )


def build_skill_chain_plan_from_packet_field_route(
    item: PacketFieldActionItem,
    *,
    available_inputs: tuple[str, ...] = (),
) -> SkillChainPlanMap:
    route_kind = item.route_kind.value
    specs = _PACKET_FIELD_ROUTE_TEMPLATES[item.route_kind]
    stages, missing_inputs = _build_stages(specs, available_inputs)
    return SkillChainPlanMap(
        plan_id=f"chain_plan_packet_field_{_slug(item.field_key)}_{route_kind}",
        title=f"{item.label} route chain plan",
        source="packet_field_action_matrix",
        route_kind=route_kind,
        stages=stages,
        missing_inputs=missing_inputs,
        provenance={
            "source": "packet_field_action_matrix",
            "packet_field_key": item.field_key,
            "route_kind": route_kind,
            "recommended_route": item.recommended_route,
            "approval_required": item.approval_required,
            "trusted_downstream_writes": False,
        },
    )


def _build_stages(
    specs: tuple[dict[str, object], ...],
    available_inputs: tuple[str, ...],
) -> tuple[tuple[SkillChainPlanStage, ...], tuple[SkillChainMissingInput, ...]]:
    available = set(available_inputs)
    stages: list[SkillChainPlanStage] = []
    missing: list[SkillChainMissingInput] = []
    for spec in specs:
        input_expectations = tuple(spec.get("input_expectations", ()))
        accepted_inputs = tuple(
            input_key for input_key in input_expectations if input_key in available
        )
        missing_keys = tuple(
            input_key for input_key in input_expectations if input_key not in available
        )
        stage_id = str(spec["stage_id"])
        question = _missing_input_question(missing_keys[0]) if missing_keys else None
        stages.append(
            SkillChainPlanStage(
                stage_id=stage_id,
                title=str(spec["title"]),
                capability_id=str(spec["capability_id"]),
                depends_on=tuple(spec.get("depends_on", ())),
                input_expectations=input_expectations,
                accepted_inputs=accepted_inputs,
                produced_handoff_type=str(spec["produced_handoff_type"]),
                search_retrieval_hints=tuple(spec.get("search_retrieval_hints", ())),
                quality_gate=str(spec["quality_gate"]),
                review_destination=str(spec["review_destination"]),
                missing_input_question=question,
            )
        )
        missing.extend(
            SkillChainMissingInput(
                stage_id=stage_id,
                input_key=input_key,
                question=_missing_input_question(input_key),
            )
            for input_key in missing_keys
        )
    return tuple(stages), tuple(missing)


def _missing_input_question(input_key: str) -> str:
    labels = {
        "piid_profile_ref": "Which PIID profile or award-history source should this chain use?",
        "source_limit_refs": "Which source limitations or approved research bounds should constrain this route?",
        "seller_baseline_ref": "Which seller baseline should be used for the competitive comparison?",
        "packet_field_key": "Which packet field should receive the reviewable candidate?",
        "opportunity_id": "Which Opportunity should this chain plan use?",
        "table_source_ref": "Which structured table or table-like source should be profiled?",
        "table_rows": "Which normalized rows should the data-table profiler inspect?",
        "requirement_refs": "Which accepted or reviewable requirement refs should the planner map?",
        "proposal_sections": "Which proposal or artifact sections should receive compliance spine items?",
    }
    return labels.get(input_key, f"What {input_key.replace('_', ' ')} should this stage use?")


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return normalized.strip("_") or "chain"


def _generic_goal_template(capture_goal: str) -> tuple[dict[str, object], ...]:
    return (
        {
            "stage_id": "stage_1_review_goal_context",
            "title": "Review goal context",
            "capability_id": "knowledge-context-review",
            "input_expectations": ("opportunity_id",),
            "produced_handoff_type": "Capability Run Output",
            "search_retrieval_hints": ("Opportunity Knowledge Context",),
            "quality_gate": "context_refs_present",
            "review_destination": "Capability Run Output",
        },
        {
            "stage_id": "stage_2_plan_reviewable_output",
            "title": capture_goal,
            "capability_id": "route-output-planner",
            "depends_on": ("stage_1_review_goal_context",),
            "input_expectations": (),
            "produced_handoff_type": "Capability Run Output",
            "search_retrieval_hints": (),
            "quality_gate": "human_review_required",
            "review_destination": "Capability Run Output",
        },
    )


_CAPTURE_GOAL_TEMPLATES: dict[str, tuple[dict[str, object], ...]] = {
    "compliance_spine_planner": (
        {
            "stage_id": "stage_1_compliance_spine_planner",
            "title": "Compliance spine planner",
            "capability_id": "compliance-spine-planner",
            "input_expectations": (
                "opportunity_id",
                "requirement_refs",
                "proposal_sections",
            ),
            "produced_handoff_type": "Artifact Content Block",
            "search_retrieval_hints": (
                "accepted requirement refs",
                "reviewable requirement refs",
                "proposal sections",
            ),
            "quality_gate": "requirements_mapped_to_sections_with_source_refs",
            "review_destination": "Artifact Content Block",
        },
        {
            "stage_id": "stage_2_artifact_block_review",
            "title": "Artifact block review",
            "capability_id": "artifact-block-review",
            "depends_on": ("stage_1_compliance_spine_planner",),
            "input_expectations": (),
            "produced_handoff_type": "Artifact Content Block",
            "search_retrieval_hints": ("Artifact Assembly Store",),
            "quality_gate": "human_review_before_artifact_use",
            "review_destination": "Artifact Content Block",
        },
    ),
    "data_table_profile_next_route": (
        {
            "stage_id": "stage_1_data_table_profiler",
            "title": "Data table profiler",
            "capability_id": "data-table-profiler",
            "input_expectations": ("table_source_ref", "table_rows"),
            "produced_handoff_type": "Capability Run Output",
            "search_retrieval_hints": ("structured table source", "table-like rows"),
            "quality_gate": "human_review_required_before_trusted_use",
            "review_destination": "Capability Run Output",
        },
        {
            "stage_id": "stage_2_data_profile_route_review",
            "title": "Data profile route review",
            "capability_id": "data-profile-route-review",
            "depends_on": ("stage_1_data_table_profiler",),
            "input_expectations": (),
            "produced_handoff_type": "Follow-Up Route",
            "search_retrieval_hints": ("Capability Run Output", "Packet Field Action Matrix"),
            "quality_gate": "review_before_packet_or_research_route",
            "review_destination": "Follow-Up Route",
        },
    ),
    "award_history_competitive_gap_packet_implication": (
        {
            "stage_id": "stage_1_incumbent_award_history_brief",
            "title": "Incumbent award history brief",
            "capability_id": "incumbent-award-history-brief",
            "input_expectations": ("opportunity_id", "piid_profile_ref"),
            "produced_handoff_type": "Capture Research candidate",
            "search_retrieval_hints": (
                "USAspending PIID profile",
                "source-profile refs",
            ),
            "quality_gate": "cites_source_profile_and_limitations",
            "review_destination": "Capture Research candidate",
        },
        {
            "stage_id": "stage_2_competitive_gap_route_hint",
            "title": "Competitive gap route hint",
            "capability_id": "competitive-gap-route-hint",
            "depends_on": ("stage_1_incumbent_award_history_brief",),
            "input_expectations": ("seller_baseline_ref",),
            "produced_handoff_type": "Packet Field Answer candidate",
            "search_retrieval_hints": ("seller baseline", "competitive gap notes"),
            "quality_gate": "states_assumptions_and_evidence_gaps",
            "review_destination": "Packet Field Answer candidate",
        },
        {
            "stage_id": "stage_3_packet_implication_review",
            "title": "Packet implication review",
            "capability_id": "packet-implication-review",
            "depends_on": ("stage_2_competitive_gap_route_hint",),
            "input_expectations": (),
            "produced_handoff_type": "Packet Field Answer candidate",
            "search_retrieval_hints": ("Packet Field Action Matrix",),
            "quality_gate": "review_before_packet_promotion",
            "review_destination": "Packet Field Answer candidate",
        },
    )
}


_PACKET_FIELD_ROUTE_TEMPLATES: dict[
    PacketFieldRouteKind,
    tuple[dict[str, object], ...],
] = {
    PacketFieldRouteKind.RESEARCH_OR_MCP: (
        {
            "stage_id": "stage_1_capture_research_brief_planner",
            "title": "Capture research brief planner",
            "capability_id": "capture-research-brief-planner",
            "input_expectations": ("opportunity_id", "packet_field_key", "source_limit_refs"),
            "produced_handoff_type": "Capture Research candidate",
            "search_retrieval_hints": (
                "Packet Field Action Matrix",
                "source-provider readiness",
            ),
            "quality_gate": "research_scope_and_source_limits_present",
            "review_destination": "Capture Research candidate",
        },
        {
            "stage_id": "stage_2_source_collection_approval_check",
            "title": "Source collection approval check",
            "capability_id": "source-collection-approval-check",
            "depends_on": ("stage_1_capture_research_brief_planner",),
            "input_expectations": (),
            "produced_handoff_type": "Capability Run Output",
            "search_retrieval_hints": ("approved source providers",),
            "quality_gate": "approval_required_before_live_collection",
            "review_destination": "Capability Run Output",
        },
        {
            "stage_id": "stage_3_packet_answer_candidate_review",
            "title": "Packet answer candidate review",
            "capability_id": "packet-answer-candidate-review",
            "depends_on": ("stage_2_source_collection_approval_check",),
            "input_expectations": (),
            "produced_handoff_type": "Packet Field Answer candidate",
            "search_retrieval_hints": ("Packet Field Action Matrix",),
            "quality_gate": "review_before_packet_promotion",
            "review_destination": "Packet Field Answer candidate",
        },
    ),
    PacketFieldRouteKind.SOURCE_PROFILE_LOOKUP: (
        {
            "stage_id": "stage_1_source_profile_context_lookup",
            "title": "Source profile context lookup",
            "capability_id": "source-profile-context-lookup",
            "input_expectations": ("opportunity_id", "source_profile_ref"),
            "produced_handoff_type": "Capture Research candidate",
            "search_retrieval_hints": ("PIID Profile", "SAM.gov Enrichment Profile"),
            "quality_gate": "source_profile_limitations_visible",
            "review_destination": "Capture Research candidate",
        },
        {
            "stage_id": "stage_2_packet_implication_review",
            "title": "Packet implication review",
            "capability_id": "packet-implication-review",
            "depends_on": ("stage_1_source_profile_context_lookup",),
            "input_expectations": (),
            "produced_handoff_type": "Packet Field Answer candidate",
            "search_retrieval_hints": ("Packet Field Action Matrix",),
            "quality_gate": "review_before_packet_promotion",
            "review_destination": "Packet Field Answer candidate",
        },
    ),
    PacketFieldRouteKind.MODEL_SYNTHESIS: (
        {
            "stage_id": "stage_1_evidence_context_check",
            "title": "Evidence context check",
            "capability_id": "evidence-context-check",
            "input_expectations": ("opportunity_id", "accepted_evidence_ref"),
            "produced_handoff_type": "Capability Run Output",
            "search_retrieval_hints": ("Opportunity Knowledge Context",),
            "quality_gate": "accepted_evidence_or_explicit_assumption_present",
            "review_destination": "Capability Run Output",
        },
        {
            "stage_id": "stage_2_model_synthesis_prompt_plan",
            "title": "Model synthesis prompt plan",
            "capability_id": "model-synthesis-prompt-plan",
            "depends_on": ("stage_1_evidence_context_check",),
            "input_expectations": (),
            "produced_handoff_type": "Capability Run Output",
            "search_retrieval_hints": ("model role contract",),
            "quality_gate": "model_not_invoked_without_approval",
            "review_destination": "Capability Run Output",
        },
    ),
    PacketFieldRouteKind.CUSTOMER_CALL_PLAN: (
        {
            "stage_id": "stage_1_customer_question_framer",
            "title": "Customer question framer",
            "capability_id": "customer-question-framer",
            "input_expectations": ("opportunity_id", "packet_field_key"),
            "produced_handoff_type": "Call Plan signal",
            "search_retrieval_hints": ("Call Plan data elements",),
            "quality_gate": "question_is_not_treated_as_answer",
            "review_destination": "Call Plan signal",
        },
    ),
    PacketFieldRouteKind.SOURCE_BACKED_ANSWER: (
        {
            "stage_id": "stage_1_source_ref_review",
            "title": "Source ref review",
            "capability_id": "source-ref-review",
            "input_expectations": ("opportunity_id", "source_ref"),
            "produced_handoff_type": "Packet Field Answer candidate",
            "search_retrieval_hints": ("Evidence Store", "Document Intake source spans"),
            "quality_gate": "source_refs_reviewed_before_packet_promotion",
            "review_destination": "Packet Field Answer candidate",
        },
    ),
}
