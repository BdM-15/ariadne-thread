from ariadne.opportunities import (
    CoreCaptureWorkstream,
    EntryContext,
    EntryReason,
    LifecycleState,
    MilestoneGate,
    WorkstreamStatus,
    create_opportunity,
    milestone_gate_for_lifecycle,
)


def test_create_opportunity_supports_later_entry_with_backfill_needs() -> None:
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

    assert opportunity.name == "AFLCMC recompete support"
    assert opportunity.lifecycle_state is LifecycleState.PURSUING
    assert opportunity.current_milestone_gate is MilestoneGate.MILESTONE_3
    assert opportunity.entry_context.reason is EntryReason.INCUMBENT_RECOMPETE
    assert set(opportunity.workstreams) == set(CoreCaptureWorkstream)
    assert {need.workstream for need in opportunity.backfill_needs} == {
        CoreCaptureWorkstream.COMPETITIVE_INTELLIGENCE,
        CoreCaptureWorkstream.PARTNER_STRATEGY,
    }


def test_later_entry_marks_backfill_without_completing_other_workstreams() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
            missing_or_stale_workstreams={
                CoreCaptureWorkstream.COMPETITIVE_INTELLIGENCE,
            },
        ),
    )

    assert (
        opportunity.workstreams[CoreCaptureWorkstream.COMPETITIVE_INTELLIGENCE].status
        is WorkstreamStatus.NEEDS_BACKFILL
    )
    assert (
        opportunity.workstreams[CoreCaptureWorkstream.CUSTOMER_INSIGHT].status
        is WorkstreamStatus.UNASSESSED
    )


def test_milestone_gate_defaults_follow_lifecycle_state() -> None:
    assert milestone_gate_for_lifecycle(LifecycleState.IDENTIFIED) is MilestoneGate.MILESTONE_1
    assert milestone_gate_for_lifecycle(LifecycleState.QUALIFIED) is MilestoneGate.MILESTONE_2
    assert milestone_gate_for_lifecycle(LifecycleState.PURSUING) is MilestoneGate.MILESTONE_3
    assert milestone_gate_for_lifecycle(LifecycleState.BID_DECIDED) is MilestoneGate.MILESTONE_4


def test_entry_context_can_override_current_milestone_gate() -> None:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.LEGACY_PURSUIT,
            starting_lifecycle_state=LifecycleState.PURSUING,
            current_milestone_gate=MilestoneGate.MILESTONE_4,
            rationale="Legacy pursuit already preparing for final bid decision.",
        ),
    )

    assert opportunity.current_milestone_gate is MilestoneGate.MILESTONE_4
