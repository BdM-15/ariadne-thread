from ariadne.config import RuntimeSettings
from ariadne.server import create_app


def _command_center_settings(tmp_path):
    return RuntimeSettings.from_mapping(
        {
            "ARIADNE_EVIDENCE_DIR": str(tmp_path / "evidence"),
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
            "ARIADNE_CAPABILITY_RUNS_DIR": str(tmp_path / "capability-runs"),
            "ARIADNE_ARTIFACT_ASSEMBLY_DIR": str(tmp_path / "artifact-assembly"),
            "ARIADNE_NEXT_ACTION_RECOMMENDATIONS_DIR": str(
                tmp_path / "next-action-recommendations"
            ),
            "ARIADNE_OPPORTUNITIES_DIR": str(tmp_path / "opportunities"),
            "ARIADNE_PACKET_FIELD_ANSWERS_DIR": str(tmp_path / "packet-field-answers"),
            "ARIADNE_OPPORTUNITY_ACTIVATION_DIR": str(
                tmp_path / "opportunity-activation"
            ),
            "ARIADNE_WORKFLOW_ROUTING_DIR": str(tmp_path / "workflow-routing"),
        }
    )


def _seed_competitive_gap_packet_delta(settings: RuntimeSettings):
    from fastapi.testclient import TestClient

    from ariadne.capability_runs import CapabilityRunStore
    from ariadne.focused_capture_skills import (
        CompetitiveGapRouteHintRequest,
        run_competitive_gap_route_hint_capability,
    )

    run = run_competitive_gap_route_hint_capability(
        request=CompetitiveGapRouteHintRequest(
            opportunity_id="opp-aflcmc-recompete",
            incumbent_signals=("Incumbent owns transition proof.",),
            seller_baseline_summary="Seller has cleared staff and onboarding proof.",
            source_refs=("source://incumbent-profile",),
            field_key="competition",
        ),
        store=CapabilityRunStore(settings.ariadne_capability_runs_dir),
    )
    client = TestClient(create_app(settings))
    intake_response = client.post(
        "/api/production-command-center/work-product-deltas/from-capability-output",
        json={
            "opportunity_id": "opp-aflcmc-recompete",
            "capability_run_id": run.run_id,
            "output_id": run.outputs[0].output_id,
        },
    )
    assert intake_response.status_code == 200, intake_response.text
    packet_delta = next(
        delta
        for delta in intake_response.json()["deltas"]
        if delta["destination"] == "living_packet"
    )
    return client, packet_delta


def _seed_competitive_gap_delta_for_destination(
    settings: RuntimeSettings,
    destination: str,
):
    client, _ = _seed_competitive_gap_packet_delta(settings)
    deltas_response = client.get(
        "/api/production-command-center/work-product-deltas",
        params={"opportunity_id": "opp-aflcmc-recompete"},
    )
    assert deltas_response.status_code == 200, deltas_response.text
    target_delta = next(
        delta
        for delta in deltas_response.json()["deltas"]
        if delta["destination"] == destination
    )
    return client, target_delta


def test_production_command_center_workspace_api_exposes_opportunity_context(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = _command_center_settings(tmp_path)

    response = TestClient(create_app(settings)).get(
        "/api/production-command-center/workspace"
    )

    assert response.status_code == 200, response.text
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
        "opportunity_portfolio",
        "packet_workspace",
        "embedded_action_paths",
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


def test_production_command_center_can_create_standard_opportunity_scaffold(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))

    response = client.post(
        "/api/production-command-center/opportunities",
        json={
            "name": "DISA cloud sustainment watch",
            "entry_reason": "new_lead",
            "starting_lifecycle_state": "identified",
            "rationale": "Analyst spotted a future recompete signal.",
            "missing_or_stale_workstreams": [
                "customer_insight",
                "competitive_intelligence",
            ],
        },
    )

    assert response.status_code == 200
    scaffold = response.json()["scaffold"]
    assert scaffold["opportunity"]["id"].startswith("opp-disa-cloud-sustainment-watch-")
    assert scaffold["opportunity"]["name"] == "DISA cloud sustainment watch"
    assert scaffold["opportunity"]["lifecycle_state"] == "identified"
    assert scaffold["opportunity"]["gate_status"] == "milestone_1"
    assert scaffold["opportunity"]["portfolio_status"] == "watchlist"
    assert scaffold["entry_reason"] == "new_lead"
    assert len(scaffold["workstreams"]) == 10
    assert {need["workstream_id"] for need in scaffold["backfill_needs"]} == {
        "customer_insight",
        "competitive_intelligence",
    }
    assert scaffold["packet"]["title"] == "Living Milestone Decision Briefing Packet"
    assert scaffold["packet"]["readiness_label"] == "not_ready"
    assert scaffold["packet"]["gap_section_count"] == 8
    assert len(scaffold["packet_sections"]) == 8
    assert len(scaffold["packet_fields"]) >= 8
    assert all(field["status"] == "unanswered" for field in scaffold["packet_fields"])
    assert all(field["evidence_status"] == "gap" for field in scaffold["packet_fields"])
    current_gate_fields = [
        field for field in scaffold["packet_fields"] if field["current_gate_required"]
    ]
    future_gate_fields = [
        field
        for field in scaffold["packet_fields"]
        if not field["current_gate_required"]
    ]
    assert 0 < len(current_gate_fields) < len(scaffold["packet_fields"])
    assert {field["key"] for field in future_gate_fields} >= {
        "competition",
        "evaluation_methodology",
    }
    digest = scaffold["activation_digest"]
    assert digest["blocked_field_count"] == len(scaffold["packet_fields"])
    assert digest["review_ready_count"] == 0
    assert "Created 10 standard capture workstreams." in digest["coverage_gained"]
    assert "Analyzed 10 packet fields for answer paths." in digest["coverage_gained"]
    assert digest["recommended_skill_chains"]
    assert digest["approval_required_routes"]
    assert digest["next_best_actions"]


def test_production_command_center_accepts_explicit_milestone_gate(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))

    response = client.post(
        "/api/production-command-center/opportunities",
        json={
            "name": "DISA cloud sustainment watch",
            "starting_lifecycle_state": "pursuing",
            "current_milestone_gate": "milestone_4",
        },
    )

    assert response.status_code == 200
    scaffold = response.json()["scaffold"]
    assert scaffold["opportunity"]["lifecycle_state"] == "pursuing"
    assert scaffold["opportunity"]["gate_status"] == "milestone_4"
    assert all(field["current_gate_required"] for field in scaffold["packet_fields"])


def test_production_command_center_updates_portfolio_state_and_gate(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={
            "name": "DISA cloud sustainment watch",
            "portfolio_status": "future",
        },
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    assert (
        create_response.json()["scaffold"]["opportunity"]["portfolio_status"]
        == "future"
    )

    active_response = client.patch(
        f"/api/production-command-center/opportunities/{opportunity_id}",
        json={
            "lifecycle_state": "pursuing",
            "current_milestone_gate": "milestone_3",
            "portfolio_status": "active",
            "rationale": "Capture lead moved this into active pursuit.",
        },
    )

    assert active_response.status_code == 200, active_response.text
    active_body = active_response.json()
    active_scaffold = active_body["scaffold"]
    assert active_scaffold["opportunity"]["lifecycle_state"] == "pursuing"
    assert active_scaffold["opportunity"]["gate_status"] == "milestone_3"
    assert active_scaffold["opportunity"]["portfolio_status"] == "active"
    fields_by_key = {field["key"]: field for field in active_scaffold["packet_fields"]}
    assert fields_by_key["rfp_release_date"]["current_gate_required"] is True
    assert fields_by_key["evaluation_methodology"]["current_gate_required"] is True
    assert active_body["activation_run"]["trigger"] == "material_refresh"
    assert (
        active_body["activation_run"]["packet_field_action_matrix"][
            "current_milestone_gate"
        ]
        == "milestone_3"
    )

    archive_response = client.patch(
        f"/api/production-command-center/opportunities/{opportunity_id}",
        json={"portfolio_status": "archived"},
    )

    assert archive_response.status_code == 200, archive_response.text
    archived = archive_response.json()["scaffold"]["opportunity"]
    assert archived["lifecycle_state"] == "archived"
    assert archived["gate_status"] == "milestone_4"
    assert archived["portfolio_status"] == "archived"

    portfolio_response = client.get("/api/production-command-center/opportunities")
    portfolio_item = next(
        opportunity
        for opportunity in portfolio_response.json()["opportunities"]
        if opportunity["id"] == opportunity_id
    )
    assert portfolio_item["portfolio_status"] == "archived"
    assert portfolio_item["lifecycle_state"] == "archived"
    assert portfolio_item["next_action_urgency"] == "steady"
    assert portfolio_item["attention_reason"] == (
        "Archived Opportunity. Open roadmap for trace and lessons."
    )
    assert portfolio_item["attention_route_mode"] == "packet"
    assert portfolio_item["attention_field_key"] is None


def test_portfolio_lists_representative_lifecycle_statuses(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    expected = {
        "Future recompete watch": "future",
        "Active cyber pursuit": "active",
        "Archived cloud pursuit": "archived",
    }
    client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Future recompete watch", "portfolio_status": "future"},
    )
    client.post(
        "/api/production-command-center/opportunities",
        json={
            "name": "Active cyber pursuit",
            "starting_lifecycle_state": "pursuing",
        },
    )
    client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Archived cloud pursuit", "portfolio_status": "archived"},
    )

    response = client.get("/api/production-command-center/opportunities")

    assert response.status_code == 200
    portfolio_by_name = {
        opportunity["name"]: opportunity
        for opportunity in response.json()["opportunities"]
        if opportunity["name"] in expected
    }
    assert {
        name: opportunity["portfolio_status"]
        for name, opportunity in portfolio_by_name.items()
    } == expected
    assert portfolio_by_name["Archived cloud pursuit"]["lifecycle_state"] == "archived"


def test_portfolio_uses_stored_activation_runs_without_recomputing(
    tmp_path,
    monkeypatch,
) -> None:
    from ariadne.opportunity_activation import OpportunityActivationRunStore
    from ariadne.production_command_center import (
        OpportunityScaffoldStore,
        ProductionOpportunityIntakeRequest,
        create_standard_opportunity_scaffold,
        list_production_opportunity_portfolio,
    )

    opportunity_store = OpportunityScaffoldStore(tmp_path / "opportunities")
    activation_store = OpportunityActivationRunStore(tmp_path / "activation-runs")
    scaffold = create_standard_opportunity_scaffold(
        request=ProductionOpportunityIntakeRequest(name="Fast portfolio watch"),
        store=opportunity_store,
        activation_store=activation_store,
    )

    def fail_recompute(**_kwargs):
        raise AssertionError("portfolio listing should reuse stored activation runs")

    monkeypatch.setattr(
        "ariadne.production_command_center.run_opportunity_activation",
        fail_recompute,
    )

    response = list_production_opportunity_portfolio(
        store=opportunity_store,
        activation_store=activation_store,
    )

    item = next(
        opportunity
        for opportunity in response.opportunities
        if opportunity.id == scaffold.opportunity.id
    )
    assert item.name == "Fast portfolio watch"
    assert item.blocked_field_count > 0
    assert item.attention_route_label.startswith("Open roadmap:")


def test_portfolio_skips_vault_refresh_for_missing_stored_activation_run(
    tmp_path,
    monkeypatch,
) -> None:
    from ariadne.opportunity_activation import OpportunityActivationRunStore
    from ariadne import production_command_center
    from ariadne.production_command_center import (
        OpportunityScaffoldStore,
        ProductionOpportunityIntakeRequest,
        create_standard_opportunity_scaffold,
        list_production_opportunity_portfolio,
    )

    opportunity_store = OpportunityScaffoldStore(tmp_path / "opportunities")
    scaffold = create_standard_opportunity_scaffold(
        request=ProductionOpportunityIntakeRequest(name="Legacy portfolio watch"),
        store=opportunity_store,
    )
    original_run_opportunity_activation = (
        production_command_center.run_opportunity_activation
    )

    def assert_no_vault_refresh(**kwargs):
        assert kwargs["vault_root"] is None
        return original_run_opportunity_activation(**kwargs)

    monkeypatch.setattr(
        production_command_center,
        "run_opportunity_activation",
        assert_no_vault_refresh,
    )

    response = list_production_opportunity_portfolio(
        store=opportunity_store,
        activation_store=OpportunityActivationRunStore(tmp_path / "activation-runs"),
        vault_root=tmp_path / "vault",
    )

    assert any(
        opportunity.id == scaffold.opportunity.id
        for opportunity in response.opportunities
    )


def test_created_opportunity_stores_initial_activation_run(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    response = client.get(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )

    assert response.status_code == 200
    runs = response.json()["runs"]
    assert len(runs) == 1
    run = runs[0]
    assert run["trigger"] == "initial_scaffold"
    assert run["status"] == "needs_review"
    assert run["packet_field_count"] == len(
        create_response.json()["scaffold"]["packet_fields"]
    )
    assert run["packet_field_action_matrix"]["blocked_field_count"] == len(
        create_response.json()["scaffold"]["packet_fields"]
    )
    assert run["packet_field_action_matrix"]["current_milestone_gate"] == "milestone_1"
    assert (
        run["packet_field_gaps"]
        == run["packet_field_action_matrix"]["current_gate_blocked_count"]
    )
    assert run["provenance"]["trusted_downstream_writes"] is False


def test_production_command_center_can_run_activation_on_request(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Space Force cyber sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )

    assert response.status_code == 200
    run = response.json()
    assert run["trigger"] == "user_request"
    assert run["opportunity_id"] == opportunity_id
    assert run["packet_field_action_matrix"]["fields"]
    assert run["packet_field_action_matrix"]["current_milestone_gate"] == "milestone_1"
    assert run["activation_digest"]["next_best_actions"]


def test_production_command_center_promotes_activation_field_answer(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Space Force cyber sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    runs_response = client.get(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )
    run_id = runs_response.json()["runs"][0]["run_id"]

    response = client.post(
        f"/api/production-command-center/activation-runs/{run_id}/"
        "fields/customer/review-decisions",
        json={
            "decision": "accept",
            "value": "Space Force",
            "reviewer_rationale": "Capture lead confirmed the customer.",
            "confidence": 0.8,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["decision"] == "accept"
    assert body["decision"]["promoted_answer_created"] is True
    assert body["packet_field_answer"]["value"] == "Space Force"
    assert body["packet_field_answer"]["status"] == "answered"
    assert body["packet_field_answer"]["evidence_status"] == "assumption"
    customer = next(
        field
        for field in body["run"]["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "customer"
    )
    assert customer["action_state"] == "answered"
    assert customer["current_value"] == "Space Force"
    assert customer["gap_summary"] is None

    rerun_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )
    rerun_customer = next(
        field
        for field in rerun_response.json()["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "customer"
    )
    assert rerun_customer["action_state"] == "answered"
    assert rerun_customer["current_value"] == "Space Force"
    assert rerun_customer["gap_summary"] is None

    workspace_response = client.get(
        f"/api/production-command-center/workspace?opportunity_id={opportunity_id}"
    )
    workspace = workspace_response.json()["workspace"]
    assert workspace["context_summary"]["trusted_count"] == 1
    assert workspace["packet"]["readiness_label"] == "draft_ready"

    portfolio_response = client.get("/api/production-command-center/opportunities")
    portfolio_item = next(
        opportunity
        for opportunity in portfolio_response.json()["opportunities"]
        if opportunity["id"] == opportunity_id
    )
    assert portfolio_item["packet_readiness_label"] == "draft_ready"
    assert portfolio_item["next_action_urgency"] == "needs_action"
    assert portfolio_item["source_freshness_label"] == "no_accepted_sources"
    current_gate_field_count = sum(
        1
        for field in create_response.json()["scaffold"]["packet_fields"]
        if field["current_gate_required"]
    )
    assert portfolio_item["blocked_field_count"] == current_gate_field_count - 1
    assert portfolio_item["attention_field_key"] != "customer"
    assert portfolio_item["attention_route_label"].startswith("Open roadmap:")


def test_activation_field_acceptance_with_evidence_ids_is_source_backed(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Space Force source backed watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    runs_response = client.get(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )
    run_id = runs_response.json()["runs"][0]["run_id"]
    customer_field = next(
        field
        for field in runs_response.json()["runs"][0]["packet_field_action_matrix"][
            "fields"
        ]
        if field["field_key"] == "customer"
    )
    assert customer_field["route_kind"] == "source_backed_answer"

    response = client.post(
        f"/api/production-command-center/activation-runs/{run_id}/"
        "fields/customer/review-decisions",
        json={
            "decision": "accept",
            "value": "Space Force",
            "evidence_ids": ["evidence.notice.customer"],
            "reviewer_rationale": "Source notice names the customer.",
            "confidence": 0.92,
        },
    )

    assert response.status_code == 200, response.text
    answer = response.json()["packet_field_answer"]
    assert answer["evidence_status"] == "answered"
    assert answer["evidence_ids"] == ["evidence.notice.customer"]
    assert answer["confidence"] == 0.92
    accepted_field = next(
        field
        for field in response.json()["run"]["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "customer"
    )
    assert accepted_field["action_state"] == "answered"
    assert accepted_field["source_refs"] == ["evidence.notice.customer"]

    portfolio_response = client.get("/api/production-command-center/opportunities")
    portfolio_item = next(
        opportunity
        for opportunity in portfolio_response.json()["opportunities"]
        if opportunity["id"] == opportunity_id
    )
    assert portfolio_item["source_freshness_label"] == "source_limited"


def test_production_command_center_routes_activation_field_without_answer(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Navy training modernization watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    runs_response = client.get(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )
    run_id = runs_response.json()["runs"][0]["run_id"]

    response = client.post(
        f"/api/production-command-center/activation-runs/{run_id}/"
        "fields/competition/review-decisions",
        json={
            "decision": "route",
            "reviewer_rationale": "Needs approved competitor research.",
            "routed_destination": "capture_research",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["packet_field_answer"] is None
    assert body["decision"]["decision"] == "route"
    assert body["decision"]["routed_destination"] == "capture_research"
    output = next(
        output
        for output in body["run"]["outputs"]
        if output["field_key"] == "competition"
    )
    assert output["review_state"] == "routed"


def test_created_opportunity_can_receive_route_recommendations(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "close_packet_gap"},
    )

    assert response.status_code == 200
    recommendation = response.json()["recommendations"][0]
    assert recommendation["opportunity_id"] == opportunity_id
    assert recommendation["id"].startswith(f"route_{opportunity_id}_close_packet_gap")


def test_packet_field_card_can_request_field_specific_route(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "close_packet_gap", "packet_field_key": "competition"},
    )

    assert response.status_code == 200
    recommendation = response.json()["recommendations"][0]
    assert recommendation["packet_field_key"] == "competition"
    assert recommendation["route_kind"] == "research_or_mcp"
    assert recommendation["route_label"] == "Close packet gap: Competition"
    assert "packet_field.competition" in recommendation["input_refs"]
    assert (
        "capture_research_enrichment" in recommendation["recommended_capability_chain"]
    )
    assert "Recommended route:" in recommendation["reasoning"][2]


def test_packet_field_can_request_customer_call_plan_route(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud customer call watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "prepare_customer_call", "packet_field_key": "primary_scope"},
    )

    assert response.status_code == 200, response.text
    recommendation = response.json()["recommendations"][0]
    assert recommendation["packet_field_key"] == "primary_scope"
    assert recommendation["route_kind"] == "customer_call_plan"
    assert recommendation["route_label"] == (
        "Prepare call plan for packet field: Primary Scope"
    )
    assert recommendation["work_product_targets"] == [
        "call_plan",
        "living_packet",
        "action_plan",
    ]
    assert recommendation["recommended_capability_chain"] == [
        "knowledge_context_review",
        "packet_gap_review",
        "call_plan_draft",
    ]
    assert "packet_field.primary_scope" in recommendation["input_refs"]
    assert "not safe to treat as answered" in recommendation["reasoning"][0]


def test_field_specific_route_rejects_unknown_packet_field(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "close_packet_gap", "packet_field_key": "missing"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported packet field: missing"


def test_production_command_center_lists_created_opportunities(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    first_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud sustainment watch"},
    )
    second_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Navy training modernization watch"},
    )

    response = client.get("/api/production-command-center/opportunities")

    assert response.status_code == 200
    opportunities = response.json()["opportunities"]
    opportunity_ids = {opportunity["id"] for opportunity in opportunities}
    assert "opp-aflcmc-recompete" in opportunity_ids
    assert first_response.json()["scaffold"]["opportunity"]["id"] in opportunity_ids
    assert second_response.json()["scaffold"]["opportunity"]["id"] in opportunity_ids
    created = next(
        opportunity
        for opportunity in opportunities
        if opportunity["id"] == first_response.json()["scaffold"]["opportunity"]["id"]
    )
    assert created["name"] == "DISA cloud sustainment watch"
    assert created["packet_readiness_label"] == "not_ready"
    assert created["blocked_field_count"] >= 6
    assert created["next_action_urgency"] == "needs_action"
    assert created["source_freshness_label"] == "no_accepted_sources"
    assert created["attention_reason"]
    assert created["attention_route_label"].startswith("Open roadmap:")
    assert created["attention_route_mode"] in {
        "activation",
        "artifacts",
        "documents",
        "engagement",
        "packet",
        "research",
    }
    assert created["attention_field_key"]
    assert created["is_demo"] is False


def test_workspace_api_loads_selected_created_opportunity(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Space Force cyber sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    response = client.get(
        f"/api/production-command-center/workspace?opportunity_id={opportunity_id}"
    )

    assert response.status_code == 200
    workspace = response.json()["workspace"]
    assert workspace["scaffold_role"] == "standard_opportunity_scaffold"
    assert workspace["opportunity"]["id"] == opportunity_id
    assert workspace["opportunity"]["name"] == "Space Force cyber sustainment watch"
    assert workspace["context_summary"]["gap_count"] == sum(
        1
        for field in create_response.json()["scaffold"]["packet_fields"]
        if field["current_gate_required"]
    )


def test_workspace_work_mode_badges_reflect_review_queues(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "Space Force review queue watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    document_response = client.post(
        "/api/document-intake/source-material",
        json={
            "filename": "customer-brief.md",
            "mime_type": "text/markdown",
            "content": "Customer needs transition proof and PM follow up.",
            "opportunity_id": opportunity_id,
        },
    )
    capability_response = client.post(
        "/api/capability-runs/local-admin-model-readiness-probe"
    )

    response = client.get(
        f"/api/production-command-center/workspace?opportunity_id={opportunity_id}"
    )

    assert document_response.status_code == 200, document_response.text
    assert capability_response.status_code == 200, capability_response.text
    assert response.status_code == 200, response.text
    modes = {mode["id"]: mode for mode in response.json()["workspace"]["work_modes"]}
    assert modes["documents"]["pending_count"] >= 1
    assert modes["capability_studio"]["pending_count"] == 1


def test_workspace_api_rejects_unknown_selected_opportunity(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))

    response = client.get(
        "/api/production-command-center/workspace?opportunity_id=opp-missing"
    )

    assert response.status_code == 404


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
    assert primary_route["route_label"] == "Prepare customer call plan"
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
    assert run["provenance"]["approval_basis"] == "human_approval_required"
    assert run["provenance"]["external_execution"] is False


def test_field_route_execution_reflects_packet_route_kind(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA packet route execution watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    route_cases = {
        "customer": {
            "route_kind": "source_backed_answer",
            "title": "Source-backed packet answer draft",
            "summary": "source-span evidence still needs human review",
            "gap": "source-span evidence before the packet answer is trusted",
        },
        "competition": {
            "route_kind": "research_or_mcp",
            "title": "Research route packet answer draft",
            "summary": "external collection remains queued for explicit approval",
            "gap": "source-provider calls still require explicit approval",
        },
        "prime_name": {
            "route_kind": "source_profile_lookup",
            "title": "Source-profile lookup packet answer draft",
            "summary": "source-profile lookup route",
            "gap": "source-profile data is not loaded",
        },
        "pwin": {
            "route_kind": "model_synthesis",
            "title": "Model synthesis packet answer draft",
            "summary": "without invoking a model yet",
            "gap": "explicit reviewer assumption is required",
        },
    }

    for field_key, expectation in route_cases.items():
        recommendation_response = client.post(
            f"/api/production-command-center/opportunities/{opportunity_id}/"
            "route-recommendations",
            json={"goal_id": "close_packet_gap", "packet_field_key": field_key},
        )
        recommendation = recommendation_response.json()["recommendations"][0]
        run_response = client.post(
            f"/api/production-command-center/routes/{recommendation['id']}/runs",
            json={
                "approved": True,
                "approval_basis": "operator_reviewed_route_kind",
                "operator_rationale": "Reviewed route kind before execution.",
            },
        )

        assert recommendation_response.status_code == 200
        assert run_response.status_code == 200, run_response.text
        assert recommendation["route_kind"] == expectation["route_kind"]
        run = run_response.json()["run"]
        output = run["output"]
        assert output["route_kind"] == expectation["route_kind"]
        assert output["title"] == expectation["title"]
        assert expectation["summary"] in output["summary"]
        assert any(expectation["gap"] in gap for gap in output["gaps"])
        assert run["provenance"]["approval_basis"] == ("operator_reviewed_route_kind")
        assert run["provenance"]["operator_rationale"] == (
            "Reviewed route kind before execution."
        )
        assert run["provenance"]["external_execution"] is False


def test_packet_field_routes_expose_model_role_contracts(tmp_path) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA model role contract watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]

    source_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "close_packet_gap", "packet_field_key": "customer"},
    )
    synthesis_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "close_packet_gap", "packet_field_key": "pwin"},
    )

    source_route = source_response.json()["recommendations"][0]
    synthesis_route = synthesis_response.json()["recommendations"][0]
    assert source_route["model_role_contract"]["model_role"] == "local_admin_model"
    assert (
        "source-backed draft prep"
        in source_route["model_role_contract"]["allowed_uses"]
    )
    assert source_route["model_role_contract"]["approval_requirement"] == (
        "human_approval_required"
    )
    assert (
        source_route["capability_route_card"]["model_role_contract"]
        == (source_route["model_role_contract"])
    )
    assert synthesis_route["model_role_contract"]["model_role"] == (
        "frontier_reasoning_model"
    )
    assert (
        "strategy synthesis" in synthesis_route["model_role_contract"]["allowed_uses"]
    )
    assert synthesis_route["model_role_contract"]["expected_output"] == (
        "Reviewable model-assisted packet synthesis draft."
    )
    assert synthesis_route["capability_route_card"]["steps"][-1]["model_role"] == (
        "frontier_reasoning_model"
    )


def test_model_synthesis_route_uses_fake_runner_and_stays_review_gated(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA fake model runner watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    recommendation_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "close_packet_gap", "packet_field_key": "pwin"},
    )
    recommendation = recommendation_response.json()["recommendations"][0]

    run_response = client.post(
        f"/api/production-command-center/routes/{recommendation['id']}/runs",
        json={"approved": True, "approval_basis": "fake_model_runner_contract_test"},
    )

    assert run_response.status_code == 200, run_response.text
    run = run_response.json()["run"]
    output = run["output"]
    assert run["executor_kind"] == "fake_model_runner"
    assert run["model_required"] is True
    assert run["network_required"] is False
    assert run["provenance"]["model_role"] == "frontier_reasoning_model"
    assert run["provenance"]["fake_model_runner"] is True
    assert run["provenance"]["trusted_downstream_writes"] is False
    assert output["review_state"] == "pending_review"
    assert output["model_role_contract"]["model_role"] == "frontier_reasoning_model"
    assert "fake model runner" in output["assumptions"][-1]
    assert any("explicit review" in gap for gap in output["gaps"])


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
        update["state"] == "ready_for_apply" for update in body["accepted_updates"]
    )
    assert body["accepted_updates"][0]["source_output_id"] == output_id
    assert "Accepted for call prep" in body["decision"]["reviewer_rationale"]
    assert body["packet_field_answer"] is None


def test_field_specific_route_acceptance_promotes_packet_field_answer(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud sustainment watch"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    recommendation_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "close_packet_gap", "packet_field_key": "customer"},
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
            "reviewer_rationale": "Accepted as current customer packet answer.",
            "accepted_destination": "living_packet",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    packet_field_answer = body["packet_field_answer"]
    assert packet_field_answer["field_key"] == "customer"
    assert packet_field_answer["opportunity_id"] == opportunity_id
    assert packet_field_answer["status"] == "answered"
    assert packet_field_answer["evidence_status"] == "assumption"
    assert packet_field_answer["source_draft_id"] == output_id
    activation_run = body["activation_run"]
    assert activation_run["trigger"] == "material_refresh"
    response_customer = next(
        field
        for field in activation_run["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "customer"
    )
    assert response_customer["action_state"] == "answered"
    assert response_customer["gap_summary"] is None

    stored_runs_response = client.get(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )
    stored_runs = stored_runs_response.json()["runs"]
    assert stored_runs[-1]["trigger"] == "material_refresh"

    rerun_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )
    customer = next(
        field
        for field in rerun_response.json()["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "customer"
    )
    assert customer["action_state"] == "answered"
    assert customer["current_value"] == packet_field_answer["value"]


def test_field_call_plan_route_acceptance_does_not_promote_packet_answer(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app(_command_center_settings(tmp_path)))
    create_response = client.post(
        "/api/production-command-center/opportunities",
        json={"name": "DISA cloud call plan fallback"},
    )
    opportunity_id = create_response.json()["scaffold"]["opportunity"]["id"]
    recommendation_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/"
        "route-recommendations",
        json={"goal_id": "prepare_customer_call", "packet_field_key": "primary_scope"},
    )
    recommendation = recommendation_response.json()["recommendations"][0]
    run_response = client.post(
        f"/api/production-command-center/routes/{recommendation['id']}/runs",
        json={"approved": True},
    )
    output = run_response.json()["run"]["output"]

    assert output["packet_field_key"] == "primary_scope"
    assert output["route_kind"] == "customer_call_plan"
    assert output["recommended_destination"] == "call_plan"

    response = client.post(
        f"/api/production-command-center/route-outputs/{output['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Accepted as call-plan fallback, not packet answer.",
            "accepted_destination": "call_plan",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["packet_field_answer"] is None
    assert body["activation_run"] is None
    assert [update["destination"] for update in body["accepted_updates"]] == [
        "call_plan",
        "living_packet",
        "action_plan",
    ]

    rerun_response = client.post(
        f"/api/production-command-center/opportunities/{opportunity_id}/activation-runs"
    )
    primary_scope = next(
        field
        for field in rerun_response.json()["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "primary_scope"
    )
    assert primary_scope["action_state"] == "blocked"


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
    assert (
        provenance["capability_chain"] == recommendation["recommended_capability_chain"]
    )
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
    assert (
        "Draft call objective" in updates_by_destination["call_plan"]["after_summary"]
    )
    assert updates_by_destination["living_packet"]["state"] == "ready_for_apply"

    action_response = client.get(
        "/api/production-command-center/work-product-updates",
        params={
            "opportunity_id": "opp-aflcmc-recompete",
            "destination": "action_plan",
        },
    )
    assert action_response.status_code == 200
    action_body = action_response.json()
    assert action_body["summary"] == {"action_plan": 1}
    assert len(action_body["updates"]) == 1
    assert action_body["updates"][0]["destination"] == "action_plan"

    call_plan_response = client.get(
        "/api/production-command-center/work-product-updates",
        params={
            "opportunity_id": "opp-aflcmc-recompete",
            "destination": "call_plan",
        },
    )
    assert call_plan_response.status_code == 200
    call_plan_body = call_plan_response.json()
    assert call_plan_body["summary"] == {"call_plan": 1}
    assert len(call_plan_body["updates"]) == 1
    assert call_plan_body["updates"][0]["destination"] == "call_plan"

    other_opportunity_response = client.get(
        "/api/production-command-center/work-product-updates",
        params={"opportunity_id": "opp-other", "destination": "action_plan"},
    )
    assert other_opportunity_response.status_code == 200
    assert other_opportunity_response.json() == {"updates": [], "summary": {}}


def test_work_product_delta_intake_from_competitive_gap_output_creates_reviewable_deltas_only(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    from ariadne.artifact_assembly import ArtifactAssemblyStore
    from ariadne.capability_runs import CapabilityRunStore
    from ariadne.focused_capture_skills import (
        CompetitiveGapRouteHintRequest,
        run_competitive_gap_route_hint_capability,
    )
    from ariadne.next_action_recommendations import NextActionRecommendationStore
    from ariadne.packet_knowledge import PacketFieldAnswerStore

    settings = _command_center_settings(tmp_path)
    capability_store = CapabilityRunStore(settings.ariadne_capability_runs_dir)
    run = run_competitive_gap_route_hint_capability(
        request=CompetitiveGapRouteHintRequest(
            opportunity_id="opp-aflcmc-recompete",
            incumbent_signals=("Incumbent likely has transition proof advantage.",),
            seller_baseline_summary="Seller has cleared staff and rapid onboarding proof.",
            source_refs=("source://incumbent-profile", "source://seller-baseline"),
            field_key="competition",
        ),
        store=capability_store,
    )
    output = run.outputs[0]

    client = TestClient(create_app(settings))
    response = client.post(
        "/api/production-command-center/work-product-deltas/from-capability-output",
        json={
            "opportunity_id": "opp-aflcmc-recompete",
            "capability_run_id": run.run_id,
            "output_id": output.output_id,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"] == {"living_packet": 1, "action_plan": 1}
    deltas_by_destination = {delta["destination"]: delta for delta in body["deltas"]}
    packet_delta = deltas_by_destination["living_packet"]
    assert packet_delta["opportunity_id"] == "opp-aflcmc-recompete"
    assert packet_delta["field_key"] == "competition"
    assert packet_delta["source_capability_run_id"] == run.run_id
    assert packet_delta["source_output_id"] == output.output_id
    assert packet_delta["review_state"] == "pending_review"
    assert packet_delta["source_refs"] == [
        "source://incumbent-profile",
        "source://seller-baseline",
    ]
    assert packet_delta["capability_output_refs"] == [
        f"capability-run://{run.run_id}/outputs/{output.output_id}"
    ]
    assert packet_delta["before_summary"].startswith("Competition field")
    assert "rapid onboarding proof" in packet_delta["after_summary"]
    assert packet_delta["assumptions"] == [
        "Input signals are reviewable; no live competitor research was run."
    ]
    assert "Reviewer must decide" in packet_delta["gaps"][-1]
    assert deltas_by_destination["action_plan"]["after_summary"].startswith(
        "Review proof gaps and customer-validation follow-up"
    )

    list_response = client.get(
        "/api/production-command-center/work-product-deltas",
        params={"opportunity_id": "opp-aflcmc-recompete"},
    )
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["summary"] == {"living_packet": 1, "action_plan": 1}

    detail_response = client.get(
        f"/api/production-command-center/work-product-deltas/{packet_delta['id']}"
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["delta"] == packet_delta

    assert (
        PacketFieldAnswerStore(settings.ariadne_packet_field_answers_dir).list(
            opportunity_id="opp-aflcmc-recompete"
        )
        == ()
    )
    assert (
        NextActionRecommendationStore(
            settings.ariadne_next_action_recommendations_dir
        ).list(opportunity_id="opp-aflcmc-recompete")
        == []
    )
    assert (
        ArtifactAssemblyStore(
            settings.ariadne_artifact_assembly_dir
        ).list_source_packages(opportunity_id="opp-aflcmc-recompete")
        == []
    )


def test_packet_delta_acceptance_creates_packet_answer_and_activation_refresh(
    tmp_path,
) -> None:
    from ariadne.artifact_assembly import ArtifactAssemblyStore
    from ariadne.next_action_recommendations import NextActionRecommendationStore
    from ariadne.packet_knowledge import PacketFieldAnswerStore

    settings = _command_center_settings(tmp_path)
    client, packet_delta = _seed_competitive_gap_packet_delta(settings)

    review_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{packet_delta['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Competition answer is good enough for gate refresh.",
        },
    )

    assert review_response.status_code == 200, review_response.text
    body = review_response.json()
    assert body["decision"]["decision"] == "accept"
    assert body["decision"]["reviewer_rationale"] == (
        "Competition answer is good enough for gate refresh."
    )
    assert body["decision"]["packet_field_answer_created"] is True
    assert body["delta"]["review_state"] == "accepted"
    assert body["delta"]["review_decisions"][0]["decision"] == "accept"
    assert body["delta"]["review_decisions"][0]["review_gate"] == (
        "work_product_delta_packet_acceptance"
    )
    answer = body["packet_field_answer"]
    assert answer["opportunity_id"] == "opp-aflcmc-recompete"
    assert answer["field_key"] == "competition"
    assert answer["value"] == packet_delta["after_summary"]
    assert answer["status"] == "answered"
    assert answer["evidence_status"] == "assumption"
    assert answer["evidence_ids"] == ["source://incumbent-profile"]
    assert answer["review_status"] == "accept"
    assert answer["source_draft_id"] == packet_delta["id"]
    assert packet_delta["source_output_id"] in answer["provenance_note"]
    assert body["activation_run"]["trigger"] == "material_refresh"
    competition_field = next(
        field
        for field in body["activation_run"]["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "competition"
    )
    assert competition_field["action_state"] == "answered"
    assert competition_field["current_value"] == packet_delta["after_summary"]
    assert competition_field["source_refs"] == ["source://incumbent-profile"]

    stored_answer = PacketFieldAnswerStore(
        settings.ariadne_packet_field_answers_dir
    ).read(opportunity_id="opp-aflcmc-recompete", field_key="competition")
    assert stored_answer.value == packet_delta["after_summary"]
    assert NextActionRecommendationStore(
        settings.ariadne_next_action_recommendations_dir
    ).list(opportunity_id="opp-aflcmc-recompete") == []
    assert ArtifactAssemblyStore(
        settings.ariadne_artifact_assembly_dir
    ).list_source_packages(opportunity_id="opp-aflcmc-recompete") == []


def test_packet_delta_edit_creates_edited_packet_answer_and_activation_refresh(
    tmp_path,
) -> None:
    from ariadne.packet_knowledge import PacketFieldAnswerStore

    settings = _command_center_settings(tmp_path)
    client, packet_delta = _seed_competitive_gap_packet_delta(settings)
    edited_value = (
        "Edited competition answer: seller can offset incumbent transition proof "
        "with named onboarding evidence."
    )

    review_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{packet_delta['id']}/review-decisions",
        json={
            "decision": "edit",
            "reviewer_rationale": "Tightened before applying to packet.",
            "edited_value": edited_value,
        },
    )

    assert review_response.status_code == 200, review_response.text
    body = review_response.json()
    assert body["decision"]["decision"] == "edit"
    assert body["decision"]["packet_field_answer_created"] is True
    assert body["delta"]["review_state"] == "edited"
    assert body["delta"]["after_summary"] == edited_value
    assert body["delta"]["review_decisions"][0]["review_gate"] == (
        "work_product_delta_packet_edit"
    )
    assert body["packet_field_answer"]["value"] == edited_value
    assert body["packet_field_answer"]["review_status"] == "edit"
    assert body["activation_run"]["trigger"] == "material_refresh"
    competition_field = next(
        field
        for field in body["activation_run"]["packet_field_action_matrix"]["fields"]
        if field["field_key"] == "competition"
    )
    assert competition_field["action_state"] == "answered"
    assert competition_field["current_value"] == edited_value

    stored_answer = PacketFieldAnswerStore(
        settings.ariadne_packet_field_answers_dir
    ).read(opportunity_id="opp-aflcmc-recompete", field_key="competition")
    assert stored_answer.value == edited_value


def test_packet_delta_discard_and_route_do_not_write_trusted_records(
    tmp_path,
) -> None:
    from ariadne.opportunity_activation import OpportunityActivationRunStore
    from ariadne.packet_knowledge import PacketFieldAnswerStore

    cases = (
        (
            "discard",
            {"decision": "discard", "reviewer_rationale": "Not enough support yet."},
            "discarded",
            None,
            "work_product_delta_packet_discard",
        ),
        (
            "route",
            {
                "decision": "route",
                "reviewer_rationale": "Needs BD follow-up before packet write.",
                "routed_destination": "customer-call-plan",
            },
            "routed",
            "customer-call-plan",
            "work_product_delta_packet_route",
        ),
    )
    for case_name, payload, expected_state, routed_destination, review_gate in cases:
        settings = _command_center_settings(tmp_path / case_name)
        client, packet_delta = _seed_competitive_gap_packet_delta(settings)

        review_response = client.post(
            "/api/production-command-center/work-product-deltas/"
            f"{packet_delta['id']}/review-decisions",
            json=payload,
        )

        assert review_response.status_code == 200, review_response.text
        body = review_response.json()
        assert body["delta"]["review_state"] == expected_state
        assert body["delta"]["review_decisions"][0]["decision"] == payload["decision"]
        assert body["delta"]["review_decisions"][0]["review_gate"] == review_gate
        assert (
            body["delta"]["review_decisions"][0]["routed_destination"]
            == routed_destination
        )
        assert body["decision"]["packet_field_answer_created"] is False
        assert body["packet_field_answer"] is None
        assert body["activation_run"] is None
        assert PacketFieldAnswerStore(
            settings.ariadne_packet_field_answers_dir
        ).list(opportunity_id="opp-aflcmc-recompete") == ()
        assert OpportunityActivationRunStore(
            settings.ariadne_opportunity_activation_dir
        ).list(opportunity_id="opp-aflcmc-recompete") == ()


def test_action_plan_delta_accept_creates_recommendation_not_action_plan_item(
    tmp_path,
) -> None:
    from ariadne.next_action_recommendations import NextActionRecommendationStore

    settings = _command_center_settings(tmp_path)
    client, action_delta = _seed_competitive_gap_delta_for_destination(
        settings, "action_plan"
    )

    review_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{action_delta['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Queue this implication as recommendation first.",
        },
    )

    assert review_response.status_code == 200, review_response.text
    body = review_response.json()
    assert body["delta"]["review_state"] == "accepted"
    recommendation = body["next_action_recommendation"]
    assert recommendation["opportunity_id"] == "opp-aflcmc-recompete"
    assert recommendation["review_state"] == "pending"
    assert recommendation["created_action_plan_item_ids"] == []
    assert action_delta["id"] in recommendation["cause"]
    assert recommendation["context_snapshot"]["recommendation_cause"] == (
        recommendation["cause"]
    )
    assert recommendation["context_snapshot"]["trusted_refs"] == []
    assert recommendation["context_snapshot"]["reviewable_refs"] == (
        action_delta["source_refs"] + action_delta["capability_output_refs"]
    )
    assert recommendation["context_snapshot"]["gap_refs"] == action_delta["gaps"]
    assert recommendation["context_snapshot"]["capability_route_id"] == (
        action_delta["source_capability_id"]
    )
    assert recommendation["capability_route"]["capability_id"] == (
        action_delta["source_capability_id"]
    )
    assert recommendation["capability_route"]["next_command_id"] == (
        "review_action_plan_recommendation"
    )
    assert body["packet_field_answer"] is None
    assert body["activation_run"] is None
    assert body["decision"]["next_action_recommendation_created"] is True

    stored = NextActionRecommendationStore(
        settings.ariadne_next_action_recommendations_dir
    ).read(recommendation["id"])
    assert stored.created_action_plan_item_ids == ()


def test_action_plan_delta_edit_creates_edited_recommendation(
    tmp_path,
) -> None:
    from ariadne.next_action_recommendations import NextActionRecommendationStore

    settings = _command_center_settings(tmp_path)
    client, action_delta = _seed_competitive_gap_delta_for_destination(
        settings, "action_plan"
    )
    edited_summary = "Edited recommendation summary for operator review queue."

    review_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{action_delta['id']}/review-decisions",
        json={
            "decision": "edit",
            "reviewer_rationale": "Sharper phrasing before recommendation gate.",
            "edited_value": edited_summary,
        },
    )

    assert review_response.status_code == 200, review_response.text
    body = review_response.json()
    assert body["delta"]["review_state"] == "edited"
    assert body["delta"]["after_summary"] == edited_summary
    assert body["delta"]["review_decisions"][0]["review_gate"] == (
        "work_product_delta_action_plan_edit"
    )
    assert body["next_action_recommendation"]["description"] == edited_summary
    assert body["decision"]["next_action_recommendation_created"] is True
    stored = NextActionRecommendationStore(
        settings.ariadne_next_action_recommendations_dir
    ).read(body["next_action_recommendation"]["id"])
    assert stored.description == edited_summary


def test_action_plan_delta_discard_and_route_preserve_provenance_only(
    tmp_path,
) -> None:
    from ariadne.next_action_recommendations import NextActionRecommendationStore

    cases = (
        (
            "discard",
            {"decision": "discard", "reviewer_rationale": "No action yet."},
            "discarded",
            None,
            "work_product_delta_action_plan_discard",
        ),
        (
            "route",
            {
                "decision": "route",
                "reviewer_rationale": "Route to call-plan queue.",
                "routed_destination": "call_plan",
            },
            "routed",
            "call_plan",
            "work_product_delta_action_plan_route",
        ),
    )
    for case_name, payload, expected_state, routed_destination, review_gate in cases:
        settings = _command_center_settings(tmp_path / case_name)
        client, action_delta = _seed_competitive_gap_delta_for_destination(
            settings, "action_plan"
        )

        review_response = client.post(
            "/api/production-command-center/work-product-deltas/"
            f"{action_delta['id']}/review-decisions",
            json=payload,
        )

        assert review_response.status_code == 200, review_response.text
        body = review_response.json()
        assert body["delta"]["review_state"] == expected_state
        assert body["delta"]["review_decisions"][0]["review_gate"] == review_gate
        assert (
            body["delta"]["review_decisions"][0]["routed_destination"]
            == routed_destination
        )
        assert body["packet_field_answer"] is None
        assert body["next_action_recommendation"] is None
        assert body["activation_run"] is None
        assert body["decision"]["next_action_recommendation_created"] is False
        assert NextActionRecommendationStore(
            settings.ariadne_next_action_recommendations_dir
        ).list(opportunity_id="opp-aflcmc-recompete") == []


def test_action_plan_delta_cannot_be_reviewed_twice(
    tmp_path,
) -> None:
    settings = _command_center_settings(tmp_path)
    client, action_delta = _seed_competitive_gap_delta_for_destination(
        settings, "action_plan"
    )

    first_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{action_delta['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "First pass accepted into recommendation queue.",
        },
    )
    assert first_response.status_code == 200, first_response.text

    second_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{action_delta['id']}/review-decisions",
        json={
            "decision": "edit",
            "reviewer_rationale": "Attempt duplicate review.",
            "edited_value": "Should fail",
        },
    )
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Work Product Delta already reviewed"


def test_production_command_center_lists_next_action_recommendations(
    tmp_path,
) -> None:
    settings = _command_center_settings(tmp_path)
    client, action_delta = _seed_competitive_gap_delta_for_destination(
        settings, "action_plan"
    )
    review_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{action_delta['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Queue recommendation for action plan gate.",
        },
    )
    assert review_response.status_code == 200, review_response.text
    recommendation_id = review_response.json()["next_action_recommendation"]["id"]

    list_response = client.get(
        "/api/production-command-center/next-action-recommendations",
        params={"opportunity_id": "opp-aflcmc-recompete"},
    )
    assert list_response.status_code == 200, list_response.text
    recommendations = list_response.json()["recommendations"]
    assert len(recommendations) == 1
    assert recommendations[0]["id"] == recommendation_id
    assert recommendations[0]["review_state"] == "pending"


def test_engagement_prep_delta_can_be_created_from_action_plan_link(
    tmp_path,
) -> None:
    settings = _command_center_settings(tmp_path)
    client, action_delta = _seed_competitive_gap_delta_for_destination(
        settings, "action_plan"
    )
    accepted_action = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{action_delta['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Queue recommendation before trusted action write.",
        },
    )
    assert accepted_action.status_code == 200, accepted_action.text

    create_response = client.post(
        "/api/production-command-center/work-product-deltas/engagement-prep",
        json={
            "opportunity_id": "opp-aflcmc-recompete",
            "source_preference": "action_plan_link",
        },
    )
    assert create_response.status_code == 200, create_response.text
    body = create_response.json()
    assert body["summary"] == {"call_plan": 1}
    assert len(body["deltas"]) == 1
    delta = body["deltas"][0]
    assert delta["destination"] == "call_plan"
    assert delta["review_state"] == "pending_review"
    assert delta["provenance"]["source_mode"] == "action_plan_link"
    assert delta["provenance"]["linked_recommendation_id"] is not None
    assert delta["provenance"]["trusted_downstream_writes"] is False
    assert "Engagement objective:" in delta["after_summary"]
    assert "Suggested validation prompts:" in delta["after_summary"]


def test_engagement_prep_delta_fallback_and_review_keeps_no_trusted_writes(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    from ariadne.artifact_assembly import ArtifactAssemblyStore
    from ariadne.next_action_recommendations import NextActionRecommendationStore
    from ariadne.packet_knowledge import PacketFieldAnswerStore

    settings = _command_center_settings(tmp_path)
    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/production-command-center/work-product-deltas/engagement-prep",
        json={
            "opportunity_id": "opp-aflcmc-recompete",
            "source_preference": "customer_call_plan_fallback",
        },
    )
    assert create_response.status_code == 200, create_response.text
    created = create_response.json()["deltas"][0]
    assert created["provenance"]["source_mode"] == "customer_call_plan_fallback"

    accept_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{created['id']}/review-decisions",
        json={
            "decision": "accept",
            "reviewer_rationale": "Reviewed engagement prep candidate only.",
        },
    )
    assert accept_response.status_code == 200, accept_response.text
    accepted = accept_response.json()
    assert accepted["delta"]["review_state"] == "accepted"
    assert accepted["decision"]["review_gate"] == "work_product_delta_call_plan_acceptance"
    assert accepted["packet_field_answer"] is None
    assert accepted["next_action_recommendation"] is None
    assert accepted["activation_run"] is None

    route_response = client.post(
        "/api/production-command-center/work-product-deltas/"
        f"{created['id']}/review-decisions",
        json={
            "decision": "route",
            "reviewer_rationale": "Route to research follow-up.",
            "routed_destination": "research",
        },
    )
    assert route_response.status_code == 400
    assert route_response.json()["detail"] == "Work Product Delta already reviewed"

    assert (
        PacketFieldAnswerStore(settings.ariadne_packet_field_answers_dir).list(
            opportunity_id="opp-aflcmc-recompete"
        )
        == ()
    )
    assert (
        NextActionRecommendationStore(
            settings.ariadne_next_action_recommendations_dir
        ).list(opportunity_id="opp-aflcmc-recompete")
        == []
    )
    assert (
        ArtifactAssemblyStore(
            settings.ariadne_artifact_assembly_dir
        ).list_source_packages(opportunity_id="opp-aflcmc-recompete")
        == []
    )


def test_engagement_prep_delta_can_be_created_from_packet_gap(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = _command_center_settings(tmp_path)
    client = TestClient(create_app(settings))
    activation_response = client.post(
        "/api/production-command-center/opportunities/opp-aflcmc-recompete/activation-runs"
    )
    assert activation_response.status_code == 200, activation_response.text

    create_response = client.post(
        "/api/production-command-center/work-product-deltas/engagement-prep",
        json={
            "opportunity_id": "opp-aflcmc-recompete",
            "source_preference": "packet_gap",
        },
    )
    assert create_response.status_code == 200, create_response.text
    delta = create_response.json()["deltas"][0]
    assert delta["destination"] == "call_plan"
    assert delta["provenance"]["source_mode"] == "packet_gap"
    assert delta["field_key"] is not None
    assert delta["source_capability_run_id"].startswith("actrun_")
    assert "Suggested validation prompts:" in delta["after_summary"]


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


def test_renderer_readiness_api_selects_living_packet_export_paths(tmp_path) -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app(_command_center_settings(tmp_path))).get(
        "/api/production-command-center/renderer-readiness"
    )

    assert response.status_code == 200
    readiness = response.json()["readiness"]
    assert readiness["target_artifact"] == ("living_milestone_decision_briefing_packet")
    assert readiness["target_label"] == "Living Milestone Decision Briefing Packet"
    assert [renderer["id"] for renderer in readiness["renderers"]] == [
        "huashu_design_pptx",
        "pandoc_docx",
        "xlsx_export",
    ]
    assert readiness["renderers"][0]["engine"] == "huashu-design"
    assert readiness["renderers"][0]["output_formats"] == ["pptx"]
    assert readiness["renderers"][1]["engine"] == "pandoc"
    assert readiness["renderers"][1]["output_formats"] == ["docx"]
    assert readiness["renderers"][2]["output_formats"] == ["xlsx"]
    assert [action["output_format"] for action in readiness["export_actions"]] == [
        "pptx",
        "docx",
        "xlsx",
    ]
    assert all(action["review_required"] for action in readiness["export_actions"])
    assert readiness["backend_blockers"] == [
        "Renderer execution adapters are not wired in this UI epic.",
        "Exports stay disabled until renderer adapters produce reviewable artifact drafts.",
    ]
