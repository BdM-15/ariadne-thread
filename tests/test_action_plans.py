from ariadne.action_plans import (
    ActionPlanItemStatus,
    AutonomyTier,
    ExecutionDetailStatus,
    add_packet_gap_actions,
    attach_execution_detail,
    build_action_plan_item_detail_view,
    build_action_plan_view,
    create_capture_action_plan,
    create_execution_detail,
)
from ariadne.opportunities import (
    CoreCaptureWorkstream,
    EntryContext,
    EntryReason,
    LifecycleState,
    create_opportunity,
)
from ariadne.packets import (
    CanonicalPacketSection,
    EvidenceStatus,
    create_living_briefing_packet,
    update_packet_section_coverage,
)


def test_capture_action_plan_creates_outcome_actions_from_backfill_needs() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
            missing_or_stale_workstreams={
                CoreCaptureWorkstream.COMPETITIVE_INTELLIGENCE,
                CoreCaptureWorkstream.PARTNER_STRATEGY,
            },
        ),
    )

    plan = create_capture_action_plan(opportunity)

    assert plan.opportunity_name == "AFLCMC recompete support"
    assert len(plan.items) == 2

    competitive_action = next(
        item
        for item in plan.items
        if item.related_workstream is CoreCaptureWorkstream.COMPETITIVE_INTELLIGENCE
    )
    assert competitive_action.action == "Resolve competitive intelligence backfill"
    assert competitive_action.rationale == (
        "Missing or stale workstream from opportunity entry context."
    )
    assert competitive_action.related_lifecycle_state is LifecycleState.PURSUING
    assert competitive_action.status is ActionPlanItemStatus.PENDING
    assert competitive_action.autonomy_tier is AutonomyTier.ASK_BEFORE_RUNNING
    assert competitive_action.execution_details == ()


def test_capture_action_plan_adds_outcome_actions_from_packet_gaps() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
        ),
    )
    packet = create_living_briefing_packet(opportunity)
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.CUSTOMER_CONTEXT,
        evidence_status=EvidenceStatus.GAP,
        gap_summary="Need validated customer pain and decision-maker map.",
    )

    plan = add_packet_gap_actions(create_capture_action_plan(opportunity), packet)

    assert len(plan.items) == 1
    gap_action = plan.items[0]
    assert gap_action.action == "Close customer context evidence gap"
    assert gap_action.rationale == "Need validated customer pain and decision-maker map."
    assert gap_action.related_packet_section is CanonicalPacketSection.CUSTOMER_CONTEXT
    assert gap_action.related_evidence_ids == ()
    assert gap_action.gap_summary == "Need validated customer pain and decision-maker map."


def test_packet_gap_actions_preserve_related_evidence_ids() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
        ),
    )
    packet = create_living_briefing_packet(opportunity)
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.SOLUTION_STRATEGY,
        evidence_status=EvidenceStatus.PARTIAL,
        evidence_ids=["ev_solution_note"],
        gap_summary="Need solution validation from the technical lead.",
    )

    plan = add_packet_gap_actions(create_capture_action_plan(opportunity), packet)

    assert len(plan.items) == 1
    assert plan.items[0].related_packet_section is CanonicalPacketSection.SOLUTION_STRATEGY
    assert plan.items[0].related_evidence_ids == ("ev_solution_note",)
    assert plan.items[0].gap_summary == "Need solution validation from the technical lead."


def test_execution_details_attach_without_cluttering_primary_action_view() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
            missing_or_stale_workstreams={
                CoreCaptureWorkstream.PARTNER_STRATEGY,
            },
        ),
    )
    plan = create_capture_action_plan(opportunity)
    detail = create_execution_detail(
        description="Draft a target partner list from incumbent and agency history.",
        proposed_by_capability="partner-research",
    )

    item_with_detail = attach_execution_detail(plan.items[0], detail)
    plan_with_detail = plan.model_copy(update={"items": (item_with_detail,)})

    primary_view = build_action_plan_view(plan_with_detail)
    detail_view = build_action_plan_item_detail_view(item_with_detail)

    assert item_with_detail.status is ActionPlanItemStatus.PENDING
    assert item_with_detail.execution_details[0].status is ExecutionDetailStatus.PROPOSED
    assert primary_view.items[0].action == item_with_detail.action
    assert not hasattr(primary_view.items[0], "execution_details")
    assert detail_view.execution_details[0].description == (
        "Draft a target partner list from incumbent and agency history."
    )