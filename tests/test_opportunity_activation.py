from datetime import UTC, datetime

from ariadne.opportunity_activation import (
    OpportunityActivationReviewState,
    OpportunityActivationRunStore,
    OpportunityActivationRunTrigger,
    PacketFieldActionState,
    run_opportunity_activation,
)
from ariadne.packet_knowledge import (
    PacketFieldAnswerStatus,
    build_default_packet_field_definitions,
    create_packet_field_answer,
)
from ariadne.packets import EvidenceStatus


def test_activation_run_covers_all_packet_field_definitions() -> None:
    definitions = build_default_packet_field_definitions()

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    matrix = run.packet_field_action_matrix
    assert run.packet_field_count == len(definitions)
    assert len(matrix.fields) == len(definitions)
    assert matrix.blocked_field_count == len(definitions)
    assert matrix.review_ready_count == 0
    assert all(
        field.action_state is PacketFieldActionState.BLOCKED
        for field in matrix.fields
    )
    assert all(field.recommended_route for field in matrix.fields)


def test_activation_run_respects_answered_and_review_ready_fields() -> None:
    definitions = build_default_packet_field_definitions()
    answers = (
        create_packet_field_answer(
            field_key="customer",
            opportunity_id="opp-disa-cloud",
            value="DISA",
            status=PacketFieldAnswerStatus.ANSWERED,
            evidence_status=EvidenceStatus.ANSWERED,
            evidence_ids=("ev_customer",),
        ),
        create_packet_field_answer(
            field_key="primary_scope",
            opportunity_id="opp-disa-cloud",
            value="Cloud sustainment scope draft",
            status=PacketFieldAnswerStatus.NEEDS_REVIEW,
            evidence_status=EvidenceStatus.PARTIAL,
            evidence_ids=("ev_scope_draft",),
        ),
    )

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        answers=answers,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    matrix = run.packet_field_action_matrix
    assert matrix.answered_field_count == 1
    assert matrix.review_ready_count == 1
    assert matrix.blocked_field_count == len(definitions) - 2
    customer = next(field for field in matrix.fields if field.field_key == "customer")
    scope = next(field for field in matrix.fields if field.field_key == "primary_scope")
    assert customer.action_state is PacketFieldActionState.ANSWERED
    assert customer.requires_review is False
    assert customer.source_refs == ("ev_customer",)
    assert scope.action_state is PacketFieldActionState.REVIEW_READY
    assert scope.requires_review is True


def test_activation_run_keeps_outputs_review_gated() -> None:
    definitions = build_default_packet_field_definitions()

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert run.status == "needs_review"
    assert run.review_state is OpportunityActivationReviewState.PENDING_REVIEW
    assert run.outputs
    assert all(
        output.review_state is OpportunityActivationReviewState.PENDING_REVIEW
        for output in run.outputs
    )
    assert run.provenance["trusted_downstream_writes"] is False
    assert run.provenance["network_required"] is False
    assert run.provenance["model_required"] is False


def test_activation_run_store_round_trips_by_opportunity(tmp_path) -> None:
    store = OpportunityActivationRunStore(tmp_path / "activation")
    definitions = build_default_packet_field_definitions()

    first = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        trigger=OpportunityActivationRunTrigger.INITIAL_SCAFFOLD,
        store=store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )
    run_opportunity_activation(
        opportunity_id="opp-navy-training",
        definitions=definitions,
        store=store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert store.read(first.run_id) == first
    assert store.list(opportunity_id="opp-disa-cloud") == (first,)
    assert len(store.list()) == 2