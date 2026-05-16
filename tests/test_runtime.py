from ariadne.config import RuntimeSettings
from ariadne.document_intake import DocumentIntakeStore
from ariadne.evidence import LocalEvidenceStore
from ariadne.local_admin_model import (
    LocalAdminDraftAssist,
    LocalAdminDraftSuggestion,
    LocalAdminModelAssistStatus,
)
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


def test_quick_capture_intelligence_draft_api_returns_reviewable_draft(
    tmp_path,
) -> None:
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


def test_quick_capture_source_material_api_creates_pasted_text_raw_item() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).post(
        "/api/quick-capture/source-material",
        json={
            "content": "Customer pasted note says transition proof needs PM follow up.",
            "opportunity_id": "opp-aflcmc-recompete",
            "raw_item_id": "raw_api_pasted_note",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["raw_item"]["id"] == "raw_api_pasted_note"
    assert body["raw_item"]["source_metadata"]["source_type"] == "pasted_text"
    assert body["review"]["raw_item_id"] == "raw_api_pasted_note"
    assert body["review"]["intelligence_draft"]["raw_source_content"] == (
        "Customer pasted note says transition proof needs PM follow up."
    )
    assert body["review"]["intelligence_draft"]["polished_capture"].startswith(
        "Interpreted signal:"
    )


def test_quick_capture_upload_api_processes_markdown_as_raw_capture_material() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).post(
        "/api/quick-capture/uploads",
        data={"opportunity_id": "opp-aflcmc-recompete"},
        files={
            "file": (
                "customer-call.md",
                b"# Call note\n\nCustomer says transition risk needs packet gap.",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready_for_quick_capture"
    assert body["raw_item"]["source_metadata"]["filename"] == "customer-call.md"
    assert body["raw_item"]["source_metadata"]["content_type"] == "markdown"
    assert body["review"]["intelligence_draft"]["raw_item_id"] == body["raw_item"]["id"]
    assert body["intake_candidate"] is None


def test_quick_capture_upload_api_records_unsupported_document_intake_candidate() -> (
    None
):
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).post(
        "/api/quick-capture/uploads",
        files={"file": ("draft-rfp.pdf", b"%PDF-1.4\n...", "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "parser_required"
    assert body["raw_item"] is None
    assert body["review"] is None
    assert body["intake_candidate"]["filename"] == "draft-rfp.pdf"
    assert body["intake_candidate"]["status"] == "parser_required"


def test_document_intake_upload_api_persists_generic_source_material(tmp_path) -> None:
    intake_root = tmp_path / "document-intake"
    evidence_root = tmp_path / "evidence"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(intake_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    upload_response = client.post(
        "/api/document-intake/uploads",
        data={"opportunity_id": "opp-aflcmc-recompete"},
        files={
            "file": (
                "customer-brief.md",
                b"# Brief\n\nCustomer says transition proof needs follow up.",
                "text/markdown",
            )
        },
    )

    assert upload_response.status_code == 200
    uploaded = upload_response.json()["record"]
    assert uploaded["filename"] == "customer-brief.md"
    assert uploaded["content_type"] == "markdown"
    assert uploaded["status"] == "ready_for_quick_capture"
    assert uploaded["queue_state"] == "ready"
    assert uploaded["opportunity_id"] == "opp-aflcmc-recompete"

    queue_response = client.get("/api/document-intake/queue")
    assert queue_response.status_code == 200
    queue = queue_response.json()["records"]
    assert [record["id"] for record in queue] == [uploaded["id"]]
    assert LocalEvidenceStore(evidence_root).list() == []


def test_document_intake_upload_api_creates_extraction_bundle_for_generic_material(
    tmp_path,
) -> None:
    intake_root = tmp_path / "document-intake"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_DOCUMENT_INTAKE_DIR": str(intake_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    response = client.post(
        "/api/document-intake/uploads",
        data={"opportunity_id": "opp-aflcmc-recompete"},
        files={
            "file": (
                "customer-brief.md",
                b"# Brief\n\nCustomer needs transition proof.\nRisk needs PM follow up.",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 200
    record = response.json()["record"]
    assert record["extraction_bundle_id"] is not None
    assert record["extraction_status"] == "complete"
    assert record["extraction_review_status"] == "pending_review"
    assert record["extraction_warning_count"] == 0

    store = DocumentIntakeStore(intake_root)
    bundle = store.read_extraction_bundle(record["extraction_bundle_id"])
    assert bundle.document_id == record["id"]
    assert bundle.source_ref == record["source_ref"]
    assert bundle.parser_provenance.adapter_name == "ariadne.generic_text_extractor"
    assert bundle.source_spans
    assert bundle.entity_candidates
    assert bundle.relationship_candidates

    queue_record = client.get("/api/document-intake/queue").json()["records"][0]
    assert queue_record["extraction_bundle_id"] == record["extraction_bundle_id"]
    assert queue_record["extraction_review_status"] == "pending_review"


def test_document_intake_source_material_api_registers_generic_text(tmp_path) -> None:
    intake_root = tmp_path / "document-intake"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_DOCUMENT_INTAKE_DIR": str(intake_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    response = client.post(
        "/api/document-intake/source-material",
        json={
            "content": "Customer says response-time proof needs follow up.",
            "filename": "customer-note.txt",
            "mime_type": "text/plain",
            "opportunity_id": "opp-aflcmc-recompete",
        },
    )

    assert response.status_code == 200
    record = response.json()["record"]
    assert record["filename"] == "customer-note.txt"
    assert record["content_type"] == "text"
    assert record["status"] == "ready_for_quick_capture"
    assert record["queue_state"] == "ready"
    assert record["extraction_status"] == "complete"
    assert record["extraction_review_status"] == "pending_review"

    queue = client.get("/api/document-intake/queue").json()["records"]
    assert queue == [record]


def test_document_intake_upload_api_persists_deferred_material_buckets(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake")}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    uploads = [
        ("whiteboard-photo.png", b"\x89PNG\r\n\x1a\n", "image/png"),
        ("draft-rfp-amendment-001.pdf", b"%PDF-1.4\n...", "application/pdf"),
        ("mystery.bundle", b"\x00\x01\x02", "application/octet-stream"),
    ]
    for filename, content, mime_type in uploads:
        response = client.post(
            "/api/document-intake/uploads",
            files={"file": (filename, content, mime_type)},
        )
        assert response.status_code == 200

    records = client.get("/api/document-intake/queue").json()["records"]
    by_filename = {record["filename"]: record for record in records}

    assert by_filename["whiteboard-photo.png"]["material_type"] == (
        "visual_source_material"
    )
    assert (
        "multimodal" in by_filename["whiteboard-photo.png"]["capability_hint"].lower()
    )
    assert by_filename["draft-rfp-amendment-001.pdf"]["material_type"] == (
        "solicitation_document"
    )
    assert (
        "solicitation parser"
        in by_filename["draft-rfp-amendment-001.pdf"]["capability_hint"].lower()
    )
    assert by_filename["mystery.bundle"]["material_type"] == "unsupported_document"
    assert (
        "readability adapter"
        in by_filename["mystery.bundle"]["capability_hint"].lower()
    )
    assert {record["queue_state"] for record in records} == {"waiting"}


def test_quick_capture_draft_api_does_not_write_evidence_before_review(
    tmp_path,
) -> None:
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
    assert body["decision"]["evidence"]["content"] != (
        "Customer says incumbent response times are weak."
    )
    assert body["decision"]["evidence"]["content"].startswith("Interpreted signal:")
    assert body["evidence_store_count"] == 1
    assert len(LocalEvidenceStore(evidence_root).list()) == 1


def test_quick_capture_promotion_api_creates_action_plan_item() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).post(
        "/api/quick-capture/promotions",
        json={
            "content": "Need follow up with PM to validate transition proof points.",
            "opportunity_id": "opp-aflcmc-recompete",
            "raw_item_id": "raw_api_action_promotion",
            "promotion_type": "action_plan_item",
            "reviewer_rationale": "Reviewer accepted PM follow-up as next action.",
            "evidence_ids": ["ev_customer_transition_note"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action_item"]["review_status"] == "accepted"
    assert body["action_item"]["source_raw_item_id"] == "raw_api_action_promotion"
    assert body["action_item"]["related_evidence_ids"] == [
        "ev_customer_transition_note"
    ]
    assert body["packet_answer"] is None


def test_quick_capture_promotion_api_creates_packet_field_answer_with_edit() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).post(
        "/api/quick-capture/promotions",
        json={
            "content": "Customer says transition risk needs packet gap.",
            "opportunity_id": "opp-aflcmc-recompete",
            "raw_item_id": "raw_api_packet_promotion",
            "promotion_type": "packet_field_answer",
            "field_key": "risks",
            "reviewer_rationale": "Reviewer accepted as risk field update.",
            "edited_content": "Transition risk needs mitigation evidence.",
            "evidence_ids": ["ev_transition_risk"],
            "confidence": 0.61,
        },
    )

    assert response.status_code == 200
    answer = response.json()["packet_answer"]
    assert answer["field_key"] == "risks"
    assert answer["value"] == "Transition risk needs mitigation evidence."
    assert answer["review_status"] == "accepted"
    assert answer["review_edits"]


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


def test_runtime_settings_default_to_ariadne_port_not_theseus_port() -> None:
    settings = RuntimeSettings.from_mapping({})

    assert settings.port == 9622
    assert settings.local_url == "http://127.0.0.1:9622"


def test_runtime_settings_expose_optional_local_admin_model_config() -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "LOCAL_ADMIN_MODEL_ENABLED": "true",
            "OLLAMA_HOST": "http://127.0.0.1:11434",
            "LOCAL_DAILY_MODEL": "qwen3.5:9b",
            "LOCAL_ADMIN_MODEL_TIMEOUT_SECONDS": "5",
        }
    )

    assert settings.local_admin_model.enabled is True
    assert settings.local_admin_model.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.local_admin_model.model == "qwen3.5:9b"
    assert settings.local_admin_model.timeout_seconds == 5


def test_local_admin_model_config_reuses_central_local_model_settings() -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "LOCAL_ADMIN_MODEL_ENABLED": "true",
            "OLLAMA_HOST": "http://127.0.0.1:11434",
            "LOCAL_DAILY_MODEL": "qwen3.5:9b",
            "LOCAL_ADMIN_MODEL": "redundant-model-ignored",
            "LOCAL_ADMIN_MODEL_OLLAMA_BASE_URL": "http://ignored:11434",
        }
    )

    assert settings.local_admin_model.enabled is True
    assert settings.local_admin_model.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.local_admin_model.model == "qwen3.5:9b"


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
        "local_admin_model": {
            "enabled": False,
            "model": "qwen3.5:9b",
            "ollama_base_url": "http://localhost:11434",
            "timeout_seconds": 30,
        },
        "status": "online",
    }


def test_quick_capture_api_can_use_local_admin_model_assist(monkeypatch) -> None:
    def fake_assist(content, *, settings, client=None):
        return LocalAdminDraftAssist(
            status=LocalAdminModelAssistStatus.USED,
            used=True,
            model=settings.model,
            reason="fake adapter used",
            suggestion=LocalAdminDraftSuggestion(
                inferred_claims=("Model claim: local adapter shaped draft.",),
            ),
        )

    monkeypatch.setattr("ariadne.server.request_local_admin_draft_assist", fake_assist)
    settings = RuntimeSettings.from_mapping({"LOCAL_ADMIN_MODEL_ENABLED": "true"})

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).post(
        "/api/quick-capture/intelligence-drafts",
        json={"content": "Customer says transition risk needs proof."},
    )

    assert response.status_code == 200
    draft = response.json()["draft"]
    assert draft["local_admin_model_assist_used"] is True
    assert draft["local_admin_model_assist_status"] == "used"
    assert draft["inferred_claims"][0] == "Model claim: local adapter shaped draft."


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
    assert "Polished Capture" in response.text
    assert "Trace/Admin Raw Note" in response.text
    assert "Local Admin Model Assist" in response.text
    assert "Accepted Draft Promotions" in response.text
    assert "Accepted Evidence" in response.text
    assert "Saved content: polished capture, not raw note" in response.text
    assert "Accepted Action" in response.text
    assert "Accepted Packet Update" in response.text
    assert "Discarded Output" in response.text
    assert "raw_demo_rushed_capture_note" in response.text
    assert "Draft Rationale" in response.text
    assert "Reviewer accepted rushed customer note as source evidence" in response.text
    assert (
        "Reviewer discarded discriminator claim until proof points exist"
        in response.text
    )
    assert "Review Status: accepted" in response.text
    assert "Per-Piece Intelligence Review" in response.text
    assert "Text / Markdown Upload" in response.text
    assert "Document Intake Candidate" in response.text
    assert "Parser Required" in response.text
    assert "Parser required before this source can enter Quick Capture" in response.text
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


def test_command_center_shell_shows_persisted_document_intake_queue(tmp_path) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake")}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    client.post(
        "/api/document-intake/source-material",
        json={
            "content": "Customer says transition proof needs follow up.",
            "filename": "customer-queue-note.txt",
            "mime_type": "text/plain",
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Document Intake Queue" in response.text
    assert "customer-queue-note.txt" in response.text
    assert "Queue: Ready" in response.text
    assert "Ready For Quick Capture" in response.text
    assert "Backed by persisted intake records" in response.text


def test_command_center_shell_shows_extraction_bundle_queue_status(tmp_path) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake")}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    client.post(
        "/api/document-intake/uploads",
        files={
            "file": (
                "customer-brief.md",
                b"Customer needs transition proof. Risk needs PM follow up.",
                "text/markdown",
            )
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Extraction: Complete" in response.text
    assert "Review: Pending Review" in response.text
    assert "Review needed" in response.text
    assert "Extraction warnings: 0" in response.text


def test_command_center_shell_shows_deferred_bucket_hints(tmp_path) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake")}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    for filename, content, mime_type in (
        ("whiteboard-photo.png", b"\x89PNG\r\n\x1a\n", "image/png"),
        ("draft-rfp-amendment-001.pdf", b"%PDF-1.4\n...", "application/pdf"),
        ("mystery.bundle", b"\x00\x01\x02", "application/octet-stream"),
    ):
        client.post(
            "/api/document-intake/uploads",
            files={"file": (filename, content, mime_type)},
        )

    response = client.get("/")

    assert response.status_code == 200
    assert "Visual Source Material" in response.text
    assert "OCR and multimodal extraction remain deferred" in response.text
    assert "Solicitation Document" in response.text
    assert "Solicitation Parser Capability" in response.text
    assert "Unsupported Document" in response.text
    assert "Parser or readability adapter required" in response.text


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
