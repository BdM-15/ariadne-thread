from ariadne.config import RuntimeSettings
from ariadne.server import create_app


def _command_center_settings(tmp_path):
    return RuntimeSettings.from_mapping(
        {
            "ARIADNE_EVIDENCE_DIR": str(tmp_path / "evidence"),
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
            "ARIADNE_CAPABILITY_RUNS_DIR": str(tmp_path / "capability-runs"),
            "ARIADNE_NEXT_ACTION_RECOMMENDATIONS_DIR": str(
                tmp_path / "next-action-recommendations"
            ),
            "ARIADNE_WORKFLOW_ROUTING_DIR": str(tmp_path / "workflow-routing"),
        }
    )


def test_production_command_center_workspace_api_exposes_opportunity_context(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = _command_center_settings(tmp_path)

    response = TestClient(create_app(settings)).get(
        "/api/production-command-center/workspace"
    )

    assert response.status_code == 200
    workspace = response.json()["workspace"]
    assert workspace["production_ui_contract"] == "nextjs_command_center_shell"
    assert workspace["scaffold_role"] == "fallback_debug_only"
    assert workspace["opportunity"]["id"] == "opp-aflcmc-recompete"
    assert workspace["opportunity"]["lifecycle_state"] == "pursuing"
    assert workspace["packet"]["title"] == "Living Milestone Decision Briefing Packet"
    assert workspace["packet"]["readiness_label"] in {
        "not_ready",
        "draft_ready",
        "review_ready",
        "decision_ready",
    }
    assert workspace["context_summary"]["trusted_count"] >= 1
    assert workspace["context_summary"]["reviewable_count"] >= 1
    assert workspace["context_summary"]["gap_count"] >= 1
    assert [region["id"] for region in workspace["layout_regions"]] == [
        "left_rail",
        "packet_workspace",
        "command_review_rail",
        "provenance_drawer",
    ]
    assert [mode["id"] for mode in workspace["work_modes"]] == [
        "packet",
        "actions",
        "engagement",
        "research",
        "documents",
        "artifacts",
        "capability_studio",
    ]
    assert [goal["id"] for goal in workspace["assisted_capture_goals"]] == [
        "prepare_customer_call",
        "close_packet_gap",
        "build_capture_action_plan",
    ]


def test_assisted_capture_goal_selection_returns_reviewable_routes(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))

    response = client.post(
        "/api/production-command-center/opportunities/"
        "opp-aflcmc-recompete/route-recommendations",
        json={"goal_id": "prepare_customer_call"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["selection_prompt"] == {
        "kind": "goal_selector",
        "label": "What do you want Ariadne to help prepare next?",
    }
    assert body["goal"]["id"] == "prepare_customer_call"
    assert body["goal"]["primary_work_product"] == "call_plan"
    assert len(body["recommendations"]) >= 2

    primary_route = body["recommendations"][0]
    assert primary_route["id"] == (
        "route_opp-aflcmc-recompete_prepare_customer_call_customer-call-plan"
    )
    assert primary_route["opportunity_id"] == "opp-aflcmc-recompete"
    assert primary_route["route_label"] == "Customer call plan route"
    assert primary_route["autonomy_tier"] == "human_approval_required"
    assert primary_route["requires_review"] is True
    assert primary_route["work_product_targets"] == [
        "call_plan",
        "living_packet",
        "action_plan",
    ]
    assert primary_route["recommended_capability_chain"] == [
        "knowledge_context_review",
        "capture_research_enrichment",
        "call_plan_draft",
    ]
    route_card = primary_route["capability_route_card"]
    assert route_card["id"] == f"card_{primary_route['id']}"
    assert route_card["capability_count"] == 3
    assert [step["capability_id"] for step in route_card["steps"]] == [
        "knowledge_context_review",
        "capture_research_enrichment",
        "call_plan_draft",
    ]
    assert [step["status"] for step in route_card["steps"]] == [
        "planned",
        "planned",
        "planned",
    ]
    assert "Customer context gap" in primary_route["reasoning"][0]


def test_assisted_capture_route_execution_creates_reviewable_output(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    recommendation_response = client.post(
        "/api/production-command-center/opportunities/"
        "opp-aflcmc-recompete/route-recommendations",
        json={"goal_id": "prepare_customer_call"},
    )
    recommendation_id = recommendation_response.json()["recommendations"][0]["id"]

    response = client.post(
        f"/api/production-command-center/routes/{recommendation_id}/runs",
        json={"approved": True},
    )

    assert response.status_code == 200
    run = response.json()["run"]
    assert run["id"] == f"run_{recommendation_id}_deterministic-draft"
    assert run["recommendation_id"] == recommendation_id
    assert run["opportunity_id"] == "opp-aflcmc-recompete"
    assert run["status"] == "needs_review"
    assert run["executor_kind"] == "deterministic_python"
    assert run["network_required"] is False
    assert run["model_required"] is False
    assert run["capability_progress"]["percent_complete"] == 100
    assert [step["status"] for step in run["capability_progress"]["steps"]] == [
        "succeeded",
        "succeeded",
        "succeeded",
    ]
    assert [stage["status"] for stage in run["stages"]] == [
        "succeeded",
        "succeeded",
        "succeeded",
    ]
    assert run["output"]["id"] == f"output_{recommendation_id}_reviewable-draft"
    assert run["output"]["review_state"] == "pending_review"
    assert run["output"]["recommended_destination"] == "call_plan"
    assert "Customer call plan" in run["output"]["title"]
    assert "knowledge_context_review" in run["output"]["capability_chain"]


def test_assisted_capture_route_output_acceptance_projects_work_updates(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    recommendation_response = client.post(
        "/api/production-command-center/opportunities/"
        "opp-aflcmc-recompete/route-recommendations",
        json={"goal_id": "prepare_customer_call"},
    )
    recommendation_id = recommendation_response.json()["recommendations"][0]["id"]
    run_response = client.post(
        f"/api/production-command-center/routes/{recommendation_id}/runs",
        json={"approved": True},
    )
    output_id = run_response.json()["run"]["output"]["id"]

    response = client.post(
        f"/api/production-command-center/route-outputs/{output_id}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Accepted for call prep after source review.",
            "accepted_destination": "call_plan",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["decision"] == "accept"
    assert body["decision"]["review_gate"] == "human_accepted"
    assert body["output"]["review_state"] == "accepted"
    assert [update["destination"] for update in body["accepted_updates"]] == [
        "call_plan",
        "living_packet",
        "action_plan",
    ]
    assert all(
        update["state"] == "ready_for_apply"
        for update in body["accepted_updates"]
    )
    assert body["accepted_updates"][0]["source_output_id"] == output_id
    assert "Accepted for call prep" in body["decision"]["reviewer_rationale"]


def test_assisted_capture_route_provenance_includes_reasoning_and_review_trace(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    recommendation_response = client.post(
        "/api/production-command-center/opportunities/"
        "opp-aflcmc-recompete/route-recommendations",
        json={"goal_id": "prepare_customer_call"},
    )
    recommendation = recommendation_response.json()["recommendations"][0]
    run_response = client.post(
        f"/api/production-command-center/routes/{recommendation['id']}/runs",
        json={"approved": True},
    )
    run = run_response.json()["run"]
    review_response = client.post(
        "/api/production-command-center/route-outputs/"
        f"{run['output']['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Accepted for provenance test.",
            "accepted_destination": "call_plan",
        },
    )

    response = client.get(
        f"/api/production-command-center/routes/{recommendation['id']}/provenance"
    )

    assert review_response.status_code == 200
    assert response.status_code == 200
    provenance = response.json()["provenance"]
    assert provenance["recommendation"]["id"] == recommendation["id"]
    assert provenance["input_refs"] == recommendation["input_refs"]
    assert provenance["capability_chain"] == recommendation[
        "recommended_capability_chain"
    ]
    assert "Customer context gap" in provenance["reasoning"][0]
    assert provenance["run"]["id"] == run["id"]
    assert provenance["run"]["network_required"] is False
    assert provenance["run"]["model_required"] is False
    assert provenance["output"]["id"] == run["output"]["id"]
    assert provenance["output"]["review_state"] == "accepted"
    assert provenance["output"]["assumptions"]
    assert provenance["output"]["gaps"]
    assert provenance["review_decisions"][0]["review_gate"] == "human_accepted"
    assert provenance["work_product_updates"][0]["destination"] == "call_plan"


def test_assisted_capture_route_output_rejection_keeps_updates_empty(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    recommendation_response = client.post(
        "/api/production-command-center/opportunities/"
        "opp-aflcmc-recompete/route-recommendations",
        json={"goal_id": "prepare_customer_call"},
    )
    recommendation_id = recommendation_response.json()["recommendations"][0]["id"]
    run_response = client.post(
        f"/api/production-command-center/routes/{recommendation_id}/runs",
        json={"approved": True},
    )
    output_id = run_response.json()["run"]["output"]["id"]

    response = client.post(
        f"/api/production-command-center/route-outputs/{output_id}/review-decisions",
        json={
            "decision": "reject",
            "reviewer_rationale": "Rejected because the customer premise needs rework.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["decision"] == "reject"
    assert body["decision"]["review_gate"] == "human_rejected"
    assert body["output"]["review_state"] == "rejected"
    assert body["accepted_updates"] == []


def test_work_product_updates_api_lists_before_after_projection_surfaces(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    recommendation_response = client.post(
        "/api/production-command-center/opportunities/"
        "opp-aflcmc-recompete/route-recommendations",
        json={"goal_id": "prepare_customer_call"},
    )
    recommendation_id = recommendation_response.json()["recommendations"][0]["id"]
    run_response = client.post(
        f"/api/production-command-center/routes/{recommendation_id}/runs",
        json={"approved": True},
    )
    output_id = run_response.json()["run"]["output"]["id"]
    client.post(
        f"/api/production-command-center/route-outputs/{output_id}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Accepted for before/after review.",
            "accepted_destination": "call_plan",
        },
    )

    response = client.get("/api/production-command-center/work-product-updates")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {
        "call_plan": 1,
        "living_packet": 1,
        "action_plan": 1,
    }
    updates_by_destination = {
        update["destination"]: update for update in body["updates"]
    }
    assert updates_by_destination["call_plan"]["before_summary"].startswith(
        "No accepted call-plan draft"
    )
    assert "Draft call objective" in updates_by_destination["call_plan"][
        "after_summary"
    ]
    assert updates_by_destination["living_packet"]["state"] == "ready_for_apply"


def test_production_command_center_health_reports_hardened_contract(tmp_path) -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app(_command_center_settings(tmp_path))).get(
        "/api/production-command-center/health"
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ready",
        "ui_contract": "nextjs_command_center_shell",
        "api_contract_version": "v1",
        "route_execution": "deterministic_local",
        "review_gate_required": True,
        "external_network_required": False,
        "external_model_required": False,
    }