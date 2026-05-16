from ariadne.config import RuntimeSettings
from ariadne.evidence import LocalEvidenceStore
from ariadne.server import create_app


def test_quick_capture_reference_influences_api_exposes_wiki_matches(tmp_path) -> None:
    wiki_root = tmp_path / "knowledge"
    _write_reference_note(
        wiki_root / "global_wiki" / "capture" / "incumbent-analysis-strategy.md",
        """---
title: Incumbent Analysis Strategy
entity_type: concept
---

# Incumbent Analysis Strategy

Incumbent transition risk and response-time weaknesses should influence capture
strategy and follow-up actions.
""",
    )
    _write_reference_note(
        wiki_root / "global_wiki" / "capture" / "customer-hot-buttons.md",
        """---
title: Customer Hot Button Identification
entity_type: concept
---

# Customer Hot Buttons

Customer complaints and decision-maker priorities shape capture strategy.
""",
    )
    _write_reference_note(
        wiki_root / "global_wiki" / "shipley" / "capture-planning-phase.md",
        """---
title: Capture Planning Phase
entity_type: concept
---

# Capture Planning Phase

Follow-up actions after customer calls should become capture-plan inputs.
""",
    )

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_REFERENCE_WIKI_DIR": str(wiki_root)}
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).post(
        "/api/quick-capture/reference-influences",
        json={
            "content": "Customer says incumbent response times are weak and "
            "transition risk needs follow up.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["influences"]) == 3
    assert body["influences"][0]["title"] == "Incumbent Analysis Strategy"
    assert body["influences"][0]["source_path"] == (
        "global_wiki/capture/incumbent-analysis-strategy.md"
    )
    assert body["influences"][0]["influence_type"] == "capture_methodology"


def test_quick_capture_intelligence_draft_api_returns_reviewable_draft(tmp_path) -> None:
    wiki_root = tmp_path / "knowledge"
    _write_reference_note(
        wiki_root / "global_wiki" / "capture" / "incumbent-analysis-strategy.md",
        """---
title: Incumbent Analysis Strategy
entity_type: concept
---

Incumbent transition risk, weak response times, customer complaints, proof points,
and ghost strategy should shape capture follow-up.
""",
    )
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_REFERENCE_WIKI_DIR": str(wiki_root)}
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).post(
        "/api/quick-capture/intelligence-drafts",
        json={
            "content": "Customer says incumbent response times are weak. "
            "Transition risk needs proof points and PM follow up.",
            "opportunity_id": "opp-aflcmc-recompete",
        },
    )

    assert response.status_code == 200
    draft = response.json()["draft"]
    assert draft["status"] == "pending_review"
    assert draft["opportunity_id"] == "opp-aflcmc-recompete"
    assert "Transition risk" in draft["likely_risks"][0]
    assert "Proof points" in draft["discriminator_candidates"][0]
    assert draft["reference_influences"][0]["title"] == "Incumbent Analysis Strategy"
    assert draft["trusted_opportunity_knowledge_updated"] is False


def test_quick_capture_draft_api_does_not_write_evidence_before_review(tmp_path) -> None:
    evidence_root = tmp_path / "evidence"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_EVIDENCE_DIR": str(evidence_root)}
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).post(
        "/api/quick-capture/intelligence-drafts",
        json={
            "content": "Customer says transition risk needs PM follow up.",
            "opportunity_id": "opp-aflcmc-recompete",
        },
    )

    assert response.status_code == 200
    assert LocalEvidenceStore(evidence_root).list() == []


def test_quick_capture_review_decision_api_writes_evidence_after_acceptance(
    tmp_path,
) -> None:
    evidence_root = tmp_path / "evidence"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_EVIDENCE_DIR": str(evidence_root)}
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).post(
        "/api/quick-capture/review-decisions",
        json={
            "content": "Customer says incumbent response times are weak.",
            "opportunity_id": "opp-aflcmc-recompete",
            "raw_item_id": "raw_api_customer_response_note",
            "action": "accept_evidence",
            "reviewer_rationale": "Accepted from customer call notes.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["status"] == "accepted"
    assert body["decision"]["trusted_evidence_written"] is True
    assert body["decision"]["evidence"]["raw_item_id"] == (
        "raw_api_customer_response_note"
    )
    assert body["decision"]["evidence"]["draft_id"] == body["decision"]["draft_id"]
    assert body["evidence_store_count"] == 1
    assert len(LocalEvidenceStore(evidence_root).list()) == 1


def test_runtime_settings_load_host_port_and_app_name_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "HOST=0.0.0.0\nPORT=9622\nPUBLIC_APP_NAME=Ariadne Local\n",
        encoding="utf-8",
    )

    settings = RuntimeSettings.from_env_file(env_file)

    assert settings.host == "0.0.0.0"
    assert settings.port == 9622
    assert settings.public_app_name == "Ariadne Local"
    assert settings.local_url == "http://127.0.0.1:9622"


def test_runtime_api_reports_configured_app_status() -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "HOST": "127.0.0.1",
            "PORT": "9622",
            "PUBLIC_APP_NAME": "Ariadne Local",
            "ARIADNE_WORKSPACE": "capture-dev",
        }
    )
    app = create_app(settings)

    from fastapi.testclient import TestClient

    response = TestClient(app).get("/api/runtime")

    assert response.status_code == 200
    assert response.json() == {
        "app_name": "Ariadne Local",
        "environment": "development",
        "workspace": "capture-dev",
        "host": "127.0.0.1",
        "port": 9622,
        "local_url": "http://127.0.0.1:9622",
        "status": "online",
    }


def test_root_serves_command_center_shell() -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "PORT": "9622",
            "PUBLIC_APP_NAME": "Ariadne Local",
        }
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Ariadne Local" in response.text
    assert "Capture Command Center" in response.text
    assert "Opportunity" in response.text
    assert "Quick Capture" in response.text
    assert "Living Briefing Packet" in response.text
    assert "Capture Action Plan" in response.text
    assert "Capability Studio" in response.text
    assert "Reference Wiki influences" in response.text
    assert "Incumbent Analysis Strategy" in response.text
    assert "Capture Intelligence Draft" in response.text
    assert "Per-Piece Intelligence Review" in response.text
    assert "Accept as Evidence" in response.text
    assert "Recommend Route" in response.text
    assert "Plan Skill Chain" in response.text
    assert "Discard Piece" in response.text
    assert "Suggested Skill Chain" in response.text
    assert "Trusted writes require reviewer action" in response.text
    assert "Inferred Claim" in response.text
    assert "Likely Risk" in response.text
    assert "Follow Up Question" in response.text
    assert "Advanced / read-only" in response.text
    assert "/api/capabilities/catalog" in response.text
    assert "AFLCMC recompete support" in response.text
    assert "Need validated customer pain" in response.text
    assert "http://127.0.0.1:9622" in response.text


def test_packet_review_page_serves_deck_shaped_packet_workspace() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/packets/review")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Living Briefing Packet" in response.text
    assert "AFLCMC recompete support" in response.text
    assert "Briefing View" in response.text
    assert "Coverage View" in response.text
    assert "Slide Navigator" in response.text
    assert "Evidence Inspector" in response.text
    assert "Opportunity Synopsis" in response.text
    assert "Visible Data Elements" in response.text
    assert "CRM / Salesforce ID" in response.text
    assert "Required for MS2" in response.text


def test_packet_review_page_can_select_stage_and_slide() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/packets/review?stage=MS4&slide=18")

    assert response.status_code == 200
    assert "MS3 / MS4 Approval Decision" in response.text
    assert "Required for MS4" in response.text
    assert "Bid/no-bid answers" in response.text
    assert "Execution-risk acceptance" in response.text


def test_packet_review_api_exposes_briefing_and_coverage_views() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app())

    briefing_response = client.get("/api/packets/review/briefing")
    coverage_response = client.get("/api/packets/review/coverage")

    assert briefing_response.status_code == 200
    assert briefing_response.json()["opportunity_name"] == "AFLCMC recompete support"
    assert briefing_response.json()["readiness"] == "draft_ready"
    assert len(briefing_response.json()["sections"]) == 8

    assert coverage_response.status_code == 200
    customer_context = next(
        section
        for section in coverage_response.json()["sections"]
        if section["section"] == "customer_context"
    )
    assert customer_context["evidence_status"] == "partial"
    assert customer_context["evidence_ids"] == ["ev_customer_call"]
    assert customer_context["gap_summary"] == (
        "Need validated customer pain and decision-maker map."
    )


def test_capability_catalog_api_exposes_local_workspace_skills() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/api/capabilities/catalog")

    assert response.status_code == 200
    entries = response.json()["entries"]
    caveman = next(entry for entry in entries if entry["id"] == "caveman")
    assert caveman["name"] == "caveman"
    assert caveman["capability_type"] == "workspace_skill"
    assert caveman["maturity"] == "experimental"
    assert caveman["validation_status"] == "unvalidated"
    assert caveman["source_path"] == ".github/skills/caveman/SKILL.md"


def test_packet_review_api_exposes_knowledge_slot_connections() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/api/packets/review/knowledge-slots")

    assert response.status_code == 200
    body = response.json()
    assert body["opportunity_id"] == "opp-aflcmc-recompete"
    customer = next(item for item in body["items"] if item["field_key"] == "customer")
    assert customer["answer"]["value"] == "AFLCMC"
    assert customer["connections"][0]["validity_scope"] == "opportunity_specific"
    assert "context only" in customer["scope_note"]


def test_app_py_builds_runtime_app_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "HOST=127.0.0.1\nPORT=9622\nPUBLIC_APP_NAME=Ariadne App\n",
        encoding="utf-8",
    )

    import importlib.util
    from pathlib import Path

    from fastapi.testclient import TestClient

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    spec = importlib.util.spec_from_file_location("ariadne_app_entrypoint", app_path)
    assert spec is not None
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)

    response = TestClient(app_module.build_app(env_file)).get("/api/runtime")

    assert response.status_code == 200
    assert response.json()["app_name"] == "Ariadne App"
    assert response.json()["port"] == 9622


def _write_reference_note(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
