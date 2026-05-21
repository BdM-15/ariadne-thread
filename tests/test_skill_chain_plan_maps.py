from ariadne.opportunity_activation import (
    PacketFieldActionItem,
    PacketFieldActionState,
    PacketFieldRouteKind,
)
from ariadne.skill_chain_plan_maps import (
    SkillChainPlanStore,
    build_skill_chain_plan_from_capture_goal,
    build_skill_chain_plan_from_packet_field_route,
)


def test_chain_plan_from_capture_goal_has_stable_stages_and_missing_input_prompt() -> None:
    plan = build_skill_chain_plan_from_capture_goal(
        capture_goal="award-history -> competitive gap -> packet implication",
        available_inputs=("opportunity_id", "seller_baseline_ref"),
    )

    assert plan.plan_id == "chain_plan_award_history_competitive_gap_packet_implication"
    assert plan.execution_mode == "deterministic_plan_map"
    assert plan.langgraph_runtime_used is False
    assert plan.network_required is False
    assert plan.model_required is False
    assert plan.trusted_downstream_writes is False
    assert tuple(stage.stage_id for stage in plan.stages) == (
        "stage_1_incumbent_award_history_brief",
        "stage_2_competitive_gap_route_hint",
        "stage_3_packet_implication_review",
    )

    first_stage = plan.stages[0]
    assert first_stage.capability_id == "incumbent-award-history-brief"
    assert first_stage.depends_on == ()
    assert first_stage.input_expectations == ("opportunity_id", "piid_profile_ref")
    assert first_stage.accepted_inputs == ("opportunity_id",)
    assert first_stage.produced_handoff_type == "Capture Research candidate"
    assert first_stage.search_retrieval_hints == (
        "USAspending PIID profile",
        "source-profile refs",
    )
    assert first_stage.quality_gate == "cites_source_profile_and_limitations"
    assert first_stage.review_destination == "Capture Research candidate"
    assert "PIID profile" in first_stage.missing_input_question
    assert plan.missing_inputs[0].input_key == "piid_profile_ref"


def test_data_table_profile_can_appear_in_chain_plan() -> None:
    plan = build_skill_chain_plan_from_capture_goal(
        capture_goal="data table profile -> next route",
        available_inputs=("table_source_ref", "table_rows"),
    )

    assert plan.plan_id == "chain_plan_data_table_profile_next_route"
    assert tuple(stage.capability_id for stage in plan.stages) == (
        "data-table-profiler",
        "anomaly-route-recommender",
    )
    assert plan.stages[0].input_expectations == ("table_source_ref", "table_rows")
    assert plan.stages[0].produced_handoff_type == "Capability Run Output"
    assert plan.stages[0].review_destination == "Capability Run Output"
    assert plan.stages[1].depends_on == ("stage_1_data_table_profiler",)
    assert plan.stages[1].review_destination == "Action Plan recommendation"
    assert plan.trusted_downstream_writes is False
    assert plan.missing_inputs == ()


def test_compliance_spine_planner_can_appear_as_one_chain_stage() -> None:
    plan = build_skill_chain_plan_from_capture_goal(
        capture_goal="compliance spine planner",
        available_inputs=("opportunity_id", "requirement_refs", "proposal_sections"),
    )

    assert plan.plan_id == "chain_plan_compliance_spine_planner"
    assert tuple(stage.capability_id for stage in plan.stages) == (
        "compliance-spine-planner",
        "artifact-block-review",
    )
    assert plan.stages[0].input_expectations == (
        "opportunity_id",
        "requirement_refs",
        "proposal_sections",
    )
    assert plan.stages[0].produced_handoff_type == "Artifact Content Block"
    assert plan.stages[0].quality_gate == (
        "requirements_mapped_to_sections_with_source_refs"
    )
    assert plan.execution_mode == "deterministic_plan_map"
    assert plan.model_required is False
    assert plan.trusted_downstream_writes is False


def test_chain_plan_from_packet_field_route_can_be_persisted(tmp_path) -> None:
    item = PacketFieldActionItem(
        field_key="competition",
        label="Competition",
        question="Who are likely competitors?",
        section="competitive_position",
        value_kind="text",
        current_status="unanswered",
        evidence_status="gap",
        action_state=PacketFieldActionState.BLOCKED,
        answer_paths=("Capability-backed research", "Capture lead input"),
        route_kind=PacketFieldRouteKind.RESEARCH_OR_MCP,
        recommended_route="Use Capture Research Enrichment before packet answer.",
        route_rationale="Competitive context needs source-backed research.",
        route_steps=(
            "Approve capability-backed research route.",
            "Review packet candidate before trusted use.",
        ),
        approval_required=True,
        gap_summary="Competition is not answered for this Opportunity.",
    )

    plan = build_skill_chain_plan_from_packet_field_route(
        item,
        available_inputs=("opportunity_id", "packet_field_key"),
    )

    assert plan.plan_id == "chain_plan_packet_field_competition_research_or_mcp"
    assert plan.source == "packet_field_action_matrix"
    assert plan.provenance["packet_field_key"] == "competition"
    assert plan.provenance["route_kind"] == "research_or_mcp"
    assert tuple(stage.stage_id for stage in plan.stages) == (
        "stage_1_capture_research_brief_planner",
        "stage_2_source_collection_approval_check",
        "stage_3_packet_answer_candidate_review",
    )
    assert plan.stages[-1].review_destination == "Packet Field Answer candidate"
    assert plan.stages[-1].produced_handoff_type == "Packet Field Answer candidate"
    assert plan.missing_inputs[0].input_key == "source_limit_refs"

    store = SkillChainPlanStore(tmp_path / "skill-chain-plans")
    store.save(plan)

    assert store.read(plan.plan_id) == plan
    assert store.list() == [plan]