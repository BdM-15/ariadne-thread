from datetime import UTC, datetime

from ariadne.capability_runs import CapabilityRunStore
from ariadne.data_table_profiler import DataTableProfileRequest
from ariadne.opportunities import MilestoneGate
from ariadne.opportunity_activation import (
    OpportunityActivationCapabilityRouteStatus,
    run_opportunity_activation,
)
from ariadne.packet_knowledge import build_default_packet_field_definitions


CHAIN_ROUTE_ID = "actroute_competition_data_table_profile_next_route_chain"


def test_activation_queues_chain_route_until_approved(tmp_path) -> None:
    capability_store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_opportunity_activation(
        opportunity_id="opp-chain-activation",
        definitions=build_default_packet_field_definitions(),
        current_milestone_gate=MilestoneGate.MILESTONE_2,
        capability_run_store=capability_store,
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )

    competition = next(
        field
        for field in run.packet_field_action_matrix.fields
        if field.field_key == "competition"
    )
    route = competition.capability_routes[0]

    assert route.route_id == CHAIN_ROUTE_ID
    assert route.capability_id == "data-table-profile-next-route-chain"
    assert route.capability_type == "skill_chain"
    assert route.status is OpportunityActivationCapabilityRouteStatus.APPROVAL_REQUIRED
    assert route.approval_required is True
    assert route.network_required is False
    assert route.model_required is False
    assert route.trusted_downstream_writes is False
    assert route.invoked_run_id is None
    assert capability_store.list() == []
    assert any(CHAIN_ROUTE_ID in queued for queued in run.activation_digest.queued_approval_routes)
    assert any("approval" in queued.lower() for queued in run.activation_digest.queued_approval_routes)
    assert run.activation_digest.invoked_routes == ()
    assert run.provenance["trusted_downstream_writes"] is False


def test_activation_invokes_approved_low_risk_chain_as_reviewable_output(tmp_path) -> None:
    capability_store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_opportunity_activation(
        opportunity_id="opp-chain-activation",
        definitions=build_default_packet_field_definitions(),
        current_milestone_gate=MilestoneGate.MILESTONE_2,
        capability_run_store=capability_store,
        approved_capability_route_ids=(CHAIN_ROUTE_ID,),
        capability_route_inputs={CHAIN_ROUTE_ID: _chain_input()},
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )

    competition = next(
        field
        for field in run.packet_field_action_matrix.fields
        if field.field_key == "competition"
    )
    route = competition.capability_routes[0]

    assert route.status is OpportunityActivationCapabilityRouteStatus.EXECUTED
    assert route.invoked_run_id is not None
    assert route.invoked_output_ids
    assert route.review_destination == "Capability Run Output"
    assert route.trusted_downstream_writes is False
    assert any(CHAIN_ROUTE_ID in invoked for invoked in run.activation_digest.invoked_routes)
    assert any(route.invoked_output_ids[0] in output for output in run.activation_digest.reviewable_outputs)
    assert any(
        "hosted_packet_synthesis" in queued
        for queued in run.activation_digest.queued_approval_routes
    )
    assert not any(
        queued.startswith(f"{CHAIN_ROUTE_ID}:")
        for queued in run.activation_digest.queued_approval_routes
    )
    assert run.provenance["network_required"] is False
    assert run.provenance["model_required"] is False
    assert run.provenance["trusted_downstream_writes"] is False
    assert route.invoked_run_id in run.provenance["invoked_capability_run_ids"]

    activation_output = next(
        output
        for output in run.outputs
        if output.output_id == f"actout_capability_{CHAIN_ROUTE_ID}"
    )
    assert activation_output.recommended_destination == "Capability Run Output"
    assert activation_output.review_state.value == "pending_review"
    assert activation_output.provenance["capability_run_id"] == route.invoked_run_id
    assert activation_output.provenance["trusted_downstream_writes"] is False

    persisted_runs = capability_store.list()
    assert {persisted.capability_id for persisted in persisted_runs} == {
        "anomaly-route-recommender",
        "data-table-profiler",
        "data-table-profile-next-route-chain",
    }


def test_activation_queues_approved_chain_when_inputs_are_source_limited(tmp_path) -> None:
    capability_store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_opportunity_activation(
        opportunity_id="opp-chain-activation",
        definitions=build_default_packet_field_definitions(),
        current_milestone_gate=MilestoneGate.MILESTONE_2,
        capability_run_store=capability_store,
        approved_capability_route_ids=(CHAIN_ROUTE_ID,),
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )

    competition = next(
        field
        for field in run.packet_field_action_matrix.fields
        if field.field_key == "competition"
    )
    route = competition.capability_routes[0]

    assert route.status is OpportunityActivationCapabilityRouteStatus.SOURCE_LIMITED
    assert route.invoked_run_id is None
    assert route.source_limitations == (
        "Approved chain route lacks required data-table profile inputs.",
    )
    assert capability_store.list() == []
    assert any(
        "data-table profile inputs" in limitation
        for limitation in run.activation_digest.source_limitations
    )
    assert any(CHAIN_ROUTE_ID in queued for queued in run.activation_digest.queued_approval_routes)


def _chain_input() -> DataTableProfileRequest:
    return DataTableProfileRequest(
        table_label="Competition workload table",
        source_ref="fixture://competition-workload-table",
        source_refs=("fixture://competition-workload-table",),
        rows=(
            {"Competitor ID": "C-1", "Vendor": "Acme Federal", "Signal": "incumbent"},
            {"Competitor ID": "C-1", "Vendor": "", "Signal": "duplicate"},
            {"Competitor ID": "C-2", "Vendor": "Beta Analytics", "Signal": "teaming"},
        ),
    )