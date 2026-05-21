from fastapi.testclient import TestClient

from ariadne.config import RuntimeSettings
from ariadne.server import create_app


def test_mvp2_skills_review_surface_can_seed_visible_demo(tmp_path) -> None:
    client = TestClient(_review_app(tmp_path))

    initial = client.get("/mvp-2/skills-review")

    assert initial.status_code == 200
    assert "MVP-2 Skills Review" in initial.text
    assert "Create MVP-2 review demo" in initial.text
    assert "Dependency-gated capabilities" in initial.text

    response = client.post("/mvp-2/skills-review/actions/demo-run", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/mvp-2/skills-review"

    updated = client.get("/mvp-2/skills-review")

    assert updated.status_code == 200
    assert "actroute_competition_data_table_profile_next_route_chain" in updated.text
    assert "data-table-profile-next-route-chain" in updated.text
    assert "stage_1_data_table_profiler" in updated.text
    assert "stage_2_anomaly_route_recommender" in updated.text
    assert "passed_pending_human_review" in updated.text
    assert "Hermes Improvement Proposals" in updated.text
    assert "Add workload-assumption review after data profiling" in updated.text
    assert "No trusted downstream writes" in updated.text


def test_mvp2_skills_review_api_exposes_reviewable_contracts(tmp_path) -> None:
    client = TestClient(_review_app(tmp_path))
    client.post("/mvp-2/skills-review/actions/demo-run")

    response = client.get("/api/mvp-2/skills-review")

    body = response.json()

    assert response.status_code == 200
    assert body["review_status"] == "ready_for_human_review"
    assert body["trusted_downstream_writes"] is False
    assert body["focused_skill_count"] >= 7
    assert body["dependency_gated_count"] >= 5
    assert body["pending_output_count"] >= 1
    chain_route = next(
        route
        for route in body["route_cards"]
        if route["capability_id"] == "data-table-profile-next-route-chain"
    )
    model_route = next(
        route
        for route in body["route_cards"]
        if route["capability_id"] == "hosted-packet-synthesis-model"
    )
    assert chain_route["approval_required"] is True
    assert chain_route["review_destination"] == "Capability Run Output"
    assert model_route["approval_required"] is True
    assert model_route["review_destination"] == "Packet Field Answer candidate"
    assert body["chain_stages"][0]["quality_gate_result"] == (
        "passed_pending_human_review"
    )
    assert len(body["model_role_contracts"]) >= 7
    assert body["improvement_proposals"][0]["review_state"] == "suggestion"
    assert body["improvement_proposals"][0]["mutates_skills"] is False
    assert body["improvement_proposals"][0]["mutates_chain_maps"] is False
    assert body["improvement_proposals"][0]["mutates_autonomy_settings"] is False


def _review_app(tmp_path):
    return create_app(
        RuntimeSettings.from_mapping(
            {
                "ARIADNE_CAPABILITY_RUNS_DIR": str(tmp_path / "capability-runs"),
                "ARIADNE_OPPORTUNITY_ACTIVATION_DIR": str(tmp_path / "activation"),
            }
        )
    )