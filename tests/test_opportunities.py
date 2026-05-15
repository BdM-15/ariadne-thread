from ariadne.opportunities import (
    CoreCaptureWorkstream,
    EntryContext,
    EntryReason,
    LifecycleState,
    WorkstreamStatus,
    create_opportunity,
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
