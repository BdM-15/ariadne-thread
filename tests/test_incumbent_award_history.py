from ariadne.capability_runs import (
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutputReviewState,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.incumbent_award_history import (
    IncumbentAwardHistoryBriefRequest,
    build_incumbent_award_history_brief,
    run_incumbent_award_history_brief_capability,
)
from ariadne.piid_profiles import create_piid_contract_intelligence_profile
from ariadne.usaspending import (
    USAspendingAwardHistoryResult,
    USAspendingAwardLookupResult,
    USAspendingAwardLookupStatus,
    USAspendingAwardTransaction,
    USAspendingLookupProvenance,
)


def test_incumbent_award_history_brief_uses_piid_profile_without_live_calls() -> None:
    request = IncumbentAwardHistoryBriefRequest(
        opportunity_id="opp-recompete",
        packet_field_key="competition",
        piid_profile=_sample_piid_profile(),
        approval_basis="operator_selected_piid_profile_fixture",
    )

    brief = build_incumbent_award_history_brief(request)

    assert brief.source_family == "usaspending"
    assert brief.source_profile_id == "piid_profile_FA8650_23_C_0001"
    assert brief.normalized_piid == "FA8650-23-C-0001"
    assert brief.incumbent_name == "ACME FEDERAL LLC"
    assert "Department of the Air Force" in brief.award_summary
    assert "$1,000,000.00" in brief.obligation_summary
    assert any("POP ends 2024-04-30" in signal for signal in brief.recompete_signals)
    assert any("USAspending" in limitation for limitation in brief.source_limitations)
    assert brief.approval_basis == "operator_selected_piid_profile_fixture"
    assert {route.destination for route in brief.route_options} == {
        "Packet Field Answer candidate",
        "Capture Research candidate",
        "Action Plan recommendation",
        "Capability Run Output",
    }
    assert "No live federal-data call was made" in brief.assumptions[-1]
    assert brief.review_state == "pending_review"
    assert brief.trusted_downstream_writes is False


def test_incumbent_award_history_capability_run_stays_review_gated(tmp_path) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")
    request = IncumbentAwardHistoryBriefRequest(
        opportunity_id="opp-recompete",
        packet_field_key="competition",
        piid_profile=_sample_piid_profile(),
        approval_basis="operator_selected_piid_profile_fixture",
    )

    run = run_incumbent_award_history_brief_capability(
        request=request,
        store=store,
    )

    assert run.capability_id == "incumbent-award-history-brief"
    assert run.capability_type is CapabilityRunCapabilityType.SKILL
    assert run.executor_kind is CapabilityRunExecutorKind.DETERMINISTIC_PYTHON
    assert run.status is CapabilityRunStatus.NEEDS_REVIEW
    assert run.provenance["network_required"] is False
    assert run.provenance["live_federal_data_call"] is False
    assert run.provenance["trusted_downstream_writes"] is False
    output = run.outputs[0]
    assert output.review_state is CapabilityRunOutputReviewState.PENDING
    assert output.recommended_destination == "Packet Field Answer candidate"
    payload = output.provenance["incumbent_award_history_brief"]
    assert payload["source_family"] == "usaspending"
    assert payload["source_profile_id"] == "piid_profile_FA8650_23_C_0001"
    assert payload["approval_basis"] == "operator_selected_piid_profile_fixture"
    assert payload["trusted_downstream_writes"] is False
    assert any("USAspending" in limitation for limitation in payload["source_limitations"])
    assert store.read(run.run_id) == run


def _sample_piid_profile():
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-C-0001",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        recipient_name="ACME FEDERAL LLC",
        awarding_agency_name="Department of the Air Force",
        awarding_sub_agency_name="Air Force Materiel Command",
        award_amount=1000000.0,
        start_date="2023-05-01",
        end_date="2024-04-30",
        solicitation_id="FA8650-22-R-0001",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_AWD_FA865023C0001_9700",
        transaction_history=(
            USAspendingAwardTransaction(
                transaction_id="txn_base",
                action_date="2023-05-01",
                fiscal_year=2023,
                modification_number="0",
                action_type="Base Award",
                obligation=800000.0,
                description="Base award",
            ),
            USAspendingAwardTransaction(
                transaction_id="txn_p00001",
                action_date="2023-11-15",
                fiscal_year=2024,
                modification_number="P00001",
                action_type="Funding Modification",
                obligation=200000.0,
                description="Incremental funding",
            ),
        ),
        derivation_notes=("Fetched transaction history from fake fixture.",),
    )
    return create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
        profile_id="piid_profile_FA8650_23_C_0001",
        created_at="2026-05-16T14:20:00Z",
    )