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
    assert "Customer context gap" in primary_route["reasoning"][0]