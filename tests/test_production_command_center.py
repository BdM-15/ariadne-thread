from ariadne.config import RuntimeSettings
from ariadne.server import create_app


def test_production_command_center_workspace_api_exposes_opportunity_context(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_EVIDENCE_DIR": str(tmp_path / "evidence"),
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
            "ARIADNE_CAPABILITY_RUNS_DIR": str(tmp_path / "capability-runs"),
            "ARIADNE_NEXT_ACTION_RECOMMENDATIONS_DIR": str(
                tmp_path / "next-action-recommendations"
            ),
        }
    )

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