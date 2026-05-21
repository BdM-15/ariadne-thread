from fastapi.testclient import TestClient

from ariadne.capability_runs import (
    CapabilityRunOutputReviewState,
    CapabilityRunReviewDecisionType,
    CapabilityRunStore,
    record_capability_run_output_review,
)
from ariadne.config import RuntimeSettings
from ariadne.data_table_profiler import DataTableProfileRequest
from ariadne.server import create_app
from ariadne.thin_orchestration_chains import run_data_table_profile_next_route_chain


def test_data_table_profile_chain_runs_with_stage_progression(tmp_path) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_data_table_profile_next_route_chain(
        request=_sample_profile_request(),
        store=store,
        opportunity_id="opp-thin-chain",
        approval_basis="operator_approved_fixture_chain",
    )

    assert run.capability_id == "data-table-profile-next-route-chain"
    assert run.capability_type.value == "skill_chain"
    assert run.executor_kind.value == "deterministic_python"
    assert run.status.value == "needs_review"
    assert run.opportunity_id == "opp-thin-chain"
    assert run.provenance["execution_mode"] == "deterministic_plan_map"
    assert run.provenance["approval_basis"] == "operator_approved_fixture_chain"
    assert run.provenance["langgraph_runtime_used"] is False
    assert run.provenance["network_required"] is False
    assert run.provenance["model_required"] is False
    assert run.provenance["broad_hermes_autonomy_used"] is False
    assert run.provenance["trusted_downstream_writes"] is False

    output = run.outputs[0]
    assert output.output_type == "thin_orchestration_chain_summary"
    assert output.review_state is CapabilityRunOutputReviewState.PENDING
    assert output.recommended_destination == "Capability Run Output"
    assert output.provenance["trusted_downstream_writes"] is False

    chain = output.provenance["thin_orchestration_chain"]
    assert chain["plan"]["plan_id"] == "chain_plan_data_table_profile_next_route"
    assert chain["status"] == "needs_review"
    assert chain["output_summary"].startswith("Thin chain produced")

    stages = chain["stage_records"]
    assert [stage["stage_id"] for stage in stages] == [
        "stage_1_data_table_profiler",
        "stage_2_anomaly_route_recommender",
    ]
    first_stage = stages[0]
    assert first_stage["capability_id"] == "data-table-profiler"
    assert first_stage["status"] == "needs_review"
    assert first_stage["input_refs"] == ["fixture://workload-table"]
    assert first_stage["produced_handoff"].startswith("output_data_table_profile_")
    assert first_stage["quality_gate_result"] == "passed_pending_human_review"
    assert first_stage["assumptions"]
    assert first_stage["gaps"]
    assert first_stage["provenance"]["capability_run_id"].startswith(
        "caprun_data_table_profile_"
    )

    second_stage = stages[1]
    assert second_stage["capability_id"] == "anomaly-route-recommender"
    assert second_stage["status"] == "needs_review"
    assert second_stage["input_refs"] == [first_stage["produced_handoff"]]
    assert second_stage["review_destination"] == "Action Plan recommendation"
    assert second_stage["quality_gate_result"] == "passed_pending_human_review"
    assert second_stage["provenance"]["route_id"] == (
        "create_data_quality_action_before_packet_use"
    )
    assert second_stage["provenance"]["capability_run_id"].startswith(
        "caprun_anomaly_route_recommendation_"
    )

    persisted_runs = store.list()
    assert {persisted.capability_id for persisted in persisted_runs} == {
        "anomaly-route-recommender",
        "data-table-profiler",
        "data-table-profile-next-route-chain",
    }


def test_chain_review_keeps_trusted_writes_human_gated(tmp_path) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")
    run = run_data_table_profile_next_route_chain(
        request=_sample_profile_request(),
        store=store,
        opportunity_id="opp-thin-chain",
        approval_basis="operator_approved_fixture_chain",
    )

    reviewed_run = record_capability_run_output_review(
        store=store,
        run_id=run.run_id,
        output_id=run.outputs[0].output_id,
        decision=CapabilityRunReviewDecisionType.ACCEPT,
        reviewer_rationale="Good reviewable route summary.",
    )

    assert reviewed_run.outputs[0].review_state is CapabilityRunOutputReviewState.ACCEPTED
    assert reviewed_run.provenance["trusted_downstream_writes"] is False
    assert reviewed_run.outputs[0].provenance["trusted_downstream_writes"] is False
    assert {persisted.capability_id for persisted in store.list()} == {
        "anomaly-route-recommender",
        "data-table-profiler",
        "data-table-profile-next-route-chain",
    }


def test_data_table_profile_chain_api_returns_visible_progression(tmp_path) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(tmp_path / "capability-runs")}
    )
    client = TestClient(create_app(settings))

    response = client.post(
        "/api/skill-chains/data-table-profile-next-route",
        json={
            "opportunity_id": "opp-api-chain",
            "approval_basis": "api_operator_approval",
            "table_label": "Workload table",
            "source_ref": "fixture://workload-table",
            "source_refs": ["fixture://workload-table"],
            "rows": [
                {"Workload ID": "WL-1", "Labor Category": "Analyst", "Hours": 120},
                {"Workload ID": "WL-1", "Labor Category": "", "Hours": None},
            ],
        },
    )

    assert response.status_code == 200
    run = response.json()["run"]
    assert run["capability_id"] == "data-table-profile-next-route-chain"
    assert run["provenance"]["network_required"] is False
    assert run["provenance"]["model_required"] is False
    assert run["provenance"]["langgraph_runtime_used"] is False

    stage_progression = run["provenance"]["stage_progression"]
    assert [stage["status"] for stage in stage_progression] == [
        "needs_review",
        "needs_review",
    ]
    assert stage_progression[0]["quality_gate_result"] == (
        "passed_pending_human_review"
    )
    assert stage_progression[1]["capability_id"] == "anomaly-route-recommender"
    assert stage_progression[1]["review_destination"] == "Action Plan recommendation"
    assert run["outputs"][0]["provenance"]["thin_orchestration_chain"][
        "output_summary"
    ].startswith("Thin chain produced")

    detail = client.get(f"/api/capability-runs/{run['run_id']}")
    assert detail.status_code == 200
    assert detail.json()["run"]["run_id"] == run["run_id"]


def _sample_profile_request() -> DataTableProfileRequest:
    return DataTableProfileRequest(
        table_label="Workload table",
        source_ref="fixture://workload-table",
        source_refs=("fixture://workload-table",),
        rows=(
            {"Workload ID": "WL-1", "Labor Category": "Analyst", "Hours": 120},
            {"Workload ID": "WL-1", "Labor Category": "", "Hours": None},
            {"Workload ID": "WL-2", "Labor Category": "Engineer", "Hours": 240},
        ),
    )