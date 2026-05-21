from ariadne.capability_runs import (
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutputReviewState,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.data_table_profiler import (
    DataTableProfileRequest,
    build_data_table_profile,
    run_data_table_profile_capability,
)


def test_data_table_profile_has_narrow_reviewable_output_contract() -> None:
    request = _sample_profile_request()

    profile = build_data_table_profile(request)

    assert profile.source_ref == "fixture://award-history-table"
    assert profile.shape.row_count == 3
    assert profile.shape.column_count == 4
    fields_by_name = {field.name: field for field in profile.fields}
    assert fields_by_name["Vendor"].missing_count == 1
    assert fields_by_name["Obligated"].value_kind == "number"
    assert any(field.name == "Contract ID" for field in profile.key_fields)
    assert any(anomaly.kind == "missing_values" for anomaly in profile.anomalies)
    assert any(anomaly.kind == "duplicate_identifier" for anomaly in profile.anomalies)
    assert "No live model, network, or external file access was used." in profile.assumptions
    assert profile.recommended_next_route.route_id == (
        "review_data_quality_before_packet_or_research_route"
    )
    assert profile.trusted_downstream_writes is False


def test_data_table_profile_capability_run_stays_pending_review(tmp_path) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_data_table_profile_capability(
        request=_sample_profile_request(),
        store=store,
        opportunity_id="opp-data-profiler",
    )

    assert run.capability_id == "data-table-profiler"
    assert run.capability_type is CapabilityRunCapabilityType.SKILL
    assert run.executor_kind is CapabilityRunExecutorKind.DETERMINISTIC_PYTHON
    assert run.status is CapabilityRunStatus.NEEDS_REVIEW
    assert run.opportunity_id == "opp-data-profiler"
    assert run.provenance["network_required"] is False
    assert run.provenance["model_required"] is False
    assert run.provenance["trusted_downstream_writes"] is False
    output = run.outputs[0]
    assert output.review_state is CapabilityRunOutputReviewState.PENDING
    assert output.recommended_destination == "Capability Run Output"
    assert output.provenance["data_table_profile"]["shape"] == {
        "row_count": 3,
        "column_count": 4,
    }
    assert "recommended_next_route" in output.provenance["data_table_profile"]
    assert any("missing" in gap for gap in output.gaps)
    assert store.read(run.run_id) == run


def _sample_profile_request() -> DataTableProfileRequest:
    return DataTableProfileRequest(
        table_label="Award history fixture",
        source_ref="fixture://award-history-table",
        source_refs=("fixture://award-history-table",),
        rows=(
            {
                "Contract ID": "FA123",
                "Vendor": "Acme Systems",
                "Obligated": 1000,
                "POP End": "2026-09-30",
            },
            {
                "Contract ID": "FA124",
                "Vendor": "",
                "Obligated": None,
                "POP End": "2026-10-31",
            },
            {
                "Contract ID": "FA124",
                "Vendor": "Beta Analytics",
                "Obligated": 1200.5,
                "POP End": "",
            },
        ),
    )