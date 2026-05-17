from ariadne.config import RuntimeSettings
from ariadne.document_intake import DocumentIntakeStore
from ariadne.evidence import LocalEvidenceStore
from ariadne.federal_data import FederalDataInitializeRunnerResult
from ariadne.local_admin_model import (
    LocalAdminDraftAssist,
    LocalAdminDraftSuggestion,
    LocalAdminModelAssistStatus,
)
from ariadne.server import create_app
from ariadne.usaspending import USAspendingMcpToolResult


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


def test_document_intake_runtime_lists_document_derived_draft_parts(tmp_path) -> None:
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
                b"Customer needs transition proof. Risk needs PM follow up.",
                "text/markdown",
            )
        },
    )
    record = upload_response.json()["record"]

    response = client.get("/api/document-intake/extraction-drafts")

    assert response.status_code == 200
    drafts = response.json()["drafts"]
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft["raw_item_id"] == record["id"]
    assert draft["extraction_bundle_id"] == record["extraction_bundle_id"]
    assert draft["extraction_document_id"] == record["id"]
    assert draft["trusted_opportunity_knowledge_updated"] is False
    assert draft["intelligence_pieces"]
    first_piece = draft["intelligence_pieces"][0]
    assert first_piece["source_intake_record_id"] == record["id"]
    assert first_piece["source_extraction_bundle_id"] == record["extraction_bundle_id"]
    assert first_piece["source_span_ids"]
    assert first_piece["recommended_route"]
    assert first_piece["suggested_skill_chain"]
    assert first_piece["review_required"] is True
    assert LocalEvidenceStore(evidence_root).list() == []


def test_document_intake_review_decision_api_accepts_spans_as_evidence(
    tmp_path,
) -> None:
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
                b"Customer needs transition proof. Risk needs PM follow up.",
                "text/markdown",
            )
        },
    )
    record = upload_response.json()["record"]
    draft = client.get("/api/document-intake/extraction-drafts").json()["drafts"][0]
    draft_part = draft["intelligence_pieces"][0]

    assert LocalEvidenceStore(evidence_root).list() == []

    response = client.post(
        "/api/document-intake/review-decisions",
        json={
            "action": "accept_evidence",
            "extraction_bundle_id": record["extraction_bundle_id"],
            "source_span_ids": draft_part["source_span_ids"],
            "draft_part_id": draft_part["id"],
            "reviewer_rationale": "Reviewer accepted source span as trusted evidence.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["duplicate"] is False
    assert body["evidence_store_count"] == 1
    assert body["evidence"]["source_intake_record_id"] == record["id"]
    assert (
        body["evidence"]["source_extraction_bundle_id"]
        == (record["extraction_bundle_id"])
    )
    assert body["evidence"]["source_span_ids"] == draft_part["source_span_ids"]
    assert body["evidence"]["parser_adapter"] == "ariadne.generic_text_extractor"
    assert body["evidence"]["source_confidence"] is not None
    assert "Reviewer accepted source span" in body["evidence"]["rationale"][0]
    assert body["accepted_link"]["draft_part_id"] == draft_part["id"]
    assert body["accepted_link"]["evidence_id"] == body["evidence"]["id"]

    duplicate_response = client.post(
        "/api/document-intake/review-decisions",
        json={
            "action": "accept_evidence",
            "extraction_bundle_id": record["extraction_bundle_id"],
            "source_span_ids": draft_part["source_span_ids"],
            "reviewer_rationale": "Reviewer clicked accept again.",
        },
    )

    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["duplicate"] is True
    assert duplicate_response.json()["evidence_store_count"] == 1
    assert len(DocumentIntakeStore(intake_root).list_accepted_evidence_links()) == 1


def test_document_intake_runtime_generates_knowledge_note_projection(
    tmp_path,
) -> None:
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
                b"Customer needs transition proof. Risk needs PM follow up.",
                "text/markdown",
            )
        },
    )
    record = upload_response.json()["record"]
    draft = client.get("/api/document-intake/extraction-drafts").json()["drafts"][0]
    draft_part = draft["intelligence_pieces"][0]
    accept_response = client.post(
        "/api/document-intake/review-decisions",
        json={
            "action": "accept_evidence",
            "extraction_bundle_id": record["extraction_bundle_id"],
            "source_span_ids": draft_part["source_span_ids"],
            "draft_part_id": draft_part["id"],
            "reviewer_rationale": "Reviewer accepted source span as trusted evidence.",
        },
    )

    generate_response = client.post(
        "/api/document-intake/knowledge-note-projections",
        json={"extraction_bundle_id": record["extraction_bundle_id"]},
    )

    assert accept_response.status_code == 200
    assert generate_response.status_code == 200
    projection = generate_response.json()["projection"]
    assert projection["title"] == "Knowledge Note Projection: customer-brief.md"
    assert projection["source_intake_record_id"] == record["id"]
    assert projection["source_extraction_bundle_id"] == record["extraction_bundle_id"]
    assert projection["evidence_ids"] == [accept_response.json()["evidence"]["id"]]
    assert projection["is_source_of_truth"] is False
    assert projection["can_overwrite_structured_knowledge"] is False
    assert (
        "Structured Ariadne records remain the source of truth."
        in (projection["markdown_content"])
    )

    list_response = client.get(
        "/api/document-intake/knowledge-note-projections",
        params={"intake_record_id": record["id"]},
    )
    assert list_response.status_code == 200
    assert list_response.json()["projections"] == [projection]
    assert DocumentIntakeStore(intake_root).list_knowledge_note_projections(
        intake_record_id=record["id"]
    )


def test_document_intake_runtime_reports_adapter_capabilities() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/api/document-intake/capabilities")

    assert response.status_code == 200
    body = response.json()
    capabilities = body["capabilities"]
    by_id = {capability["id"]: capability for capability in capabilities}
    assert body["available_count"] == 1
    assert body["deferred_count"] >= 6
    assert by_id["ariadne.generic_text_extractor"]["status"] == "available"
    assert by_id["ariadne.generic_text_extractor"]["expected_output_contract"] == (
        "ExtractionBundle"
    )
    assert by_id["project_theseus.solicitation_parser"]["status"] == "deferred"
    assert (
        "solicitation_document"
        in by_id["project_theseus.solicitation_parser"]["supported_material_types"]
    )
    assert by_id["opendatalab.mineru"]["status"] == "deferred"
    assert by_id["hkuds.raganything"]["adapter_kind"] == "retrieval"
    assert by_id["hkuds.lightrag"]["adapter_kind"] == "retrieval"
    assert all(
        capability["external_tool_invocation_allowed"] is False
        for capability in capabilities
    )


def test_federal_data_runtime_reports_registered_mcp_capabilities() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/api/federal-data/capabilities")

    assert response.status_code == 200
    body = response.json()
    capabilities = body["capabilities"]
    by_id = {capability["id"]: capability for capability in capabilities}

    assert len(capabilities) == 8
    assert body["registered_count"] == 7
    assert body["product_integrated_count"] == 1
    assert body["smoke_tested_count"] == 0
    assert body["deferred_product_workflow_count"] == 0
    assert body["safe_smoke_check_method"] == "json_rpc_initialize_only"
    assert body["smoke_check_endpoint_template"] == (
        "/api/federal-data/capabilities/{capability_id}/smoke-check"
    )
    assert by_id["usaspending"]["product_status"] == "product_integrated"
    assert by_id["usaspending"]["package"] == "usaspending-gov-mcp"
    assert by_id["sam_gov"]["required_env_vars"] == ["SAM_GOV_API_KEY"]
    assert by_id["sam_gov"]["upstream_env_vars"] == ["SAM_API_KEY"]
    assert all(
        "=" not in env_var
        for capability in capabilities
        for env_var in (
            capability["required_env_vars"]
            + capability["optional_env_vars"]
            + capability["upstream_env_vars"]
        )
    )


def test_federal_data_smoke_check_api_reports_missing_env_without_runner_call() -> None:
    from fastapi.testclient import TestClient

    calls = []

    def runner(command, request, timeout_seconds, env):
        calls.append((command, request, timeout_seconds, env))
        return FederalDataInitializeRunnerResult(
            return_code=0,
            initialized=True,
            diagnostic_summary="should not run",
        )

    response = TestClient(
        create_app(
            RuntimeSettings.from_mapping({}),
            federal_data_smoke_runner=runner,
        )
    ).post("/api/federal-data/capabilities/sam_gov/smoke-check")

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["capability_id"] == "sam_gov"
    assert result["status"] == "missing_env"
    assert result["missing_env_vars"] == ["SAM_GOV_API_KEY"]
    assert result["diagnostic_summary"] == "Missing required env vars: SAM_GOV_API_KEY"
    assert calls == []


def test_federal_data_smoke_check_api_uses_safe_initialize_runner() -> None:
    from fastapi.testclient import TestClient

    calls = []

    def runner(command, request, timeout_seconds, env):
        calls.append((command, request, timeout_seconds, env))
        return FederalDataInitializeRunnerResult(
            return_code=0,
            initialized=True,
            diagnostic_summary="initialize accepted with live-sam-secret-value",
        )

    response = TestClient(
        create_app(
            RuntimeSettings.from_mapping(
                {
                    "SAM_GOV_API_KEY": "live-sam-secret-value",
                    "MCP_TOOL_TIMEOUT_SECONDS": "7",
                }
            ),
            federal_data_smoke_runner=runner,
        )
    ).post("/api/federal-data/capabilities/sam_gov/smoke-check")

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "success"
    assert result["data_tool_calls_invoked"] == []
    assert result["diagnostic_summary"] == "initialize accepted with <redacted>"
    assert "live-sam-secret-value" not in response.text
    command, request, timeout_seconds, env = calls[0]
    assert "sam-gov-mcp==0.4.1" in command
    assert request["method"] == "initialize"
    assert timeout_seconds == 7
    assert env["SAM_GOV_API_KEY"] == "live-sam-secret-value"
    assert env["SAM_API_KEY"] == "live-sam-secret-value"


def test_usaspending_piid_lookup_api_returns_structured_success_result() -> None:
    from fastapi.testclient import TestClient

    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return USAspendingMcpToolResult(
            ok=True,
            payload={
                "award_type": "contract",
                "results": [
                    {
                        "Award ID": "FA8650-23-C-0001",
                        "Recipient Name": "ACME FEDERAL LLC",
                        "Awarding Agency": "Department of the Air Force",
                        "generated_internal_id": "CONT_AWD_FA865023C0001_9700",
                    }
                ],
            },
        )

    response = TestClient(create_app(usaspending_lookup_runner=runner)).post(
        "/api/federal-data/usaspending/piid-lookup",
        json={"contract_number": " fa8650-23-c-0001 ", "limit": 5},
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "success"
    assert result["normalized_piid"] == "FA8650-23-C-0001"
    assert result["resolved_award_id"] == "FA8650-23-C-0001"
    assert result["generated_internal_id"] == "CONT_AWD_FA865023C0001_9700"
    assert result["recipient_name"] == "ACME FEDERAL LLC"
    assert result["awarding_agency_name"] == "Department of the Air Force"
    assert result["provenance"]["source_capability_id"] == "usaspending"
    assert result["provenance"]["source_tool_name"] == "lookup_piid"
    assert "uvx --from" not in response.text
    assert calls == [("lookup_piid", {"piid": "FA8650-23-C-0001", "limit": 5})]


def test_usaspending_piid_lookup_api_returns_tool_error_result() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(
        create_app(
            usaspending_lookup_runner=lambda tool_name, arguments: (
                USAspendingMcpToolResult(
                    ok=False,
                    error_message="lookup_piid failed: HTTP 429: rate limited",
                )
            )
        )
    ).post(
        "/api/federal-data/usaspending/piid-lookup",
        json={"contract_number": "FA8650-23-C-0001"},
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "tool_error"
    assert result["diagnostic_summary"] == "lookup_piid failed: HTTP 429: rate limited"


def test_usaspending_piid_profile_api_creates_and_persists_profile(tmp_path) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_PIID_PROFILES_DIR": str(tmp_path / "piid-profiles")}
    )

    def runner(tool_name, arguments):
        return USAspendingMcpToolResult(
            ok=True,
            payload={
                "award_type": "contract",
                "results": [
                    {
                        "Award ID": "FA8650-23-F-0001",
                        "Recipient Name": "ACME FEDERAL LLC",
                        "Recipient UEI": "UEIACME12345",
                        "Awarding Agency": "Department of the Air Force",
                        "Awarding Sub Agency": "Air Force Materiel Command",
                        "Award Amount": 1250000,
                        "Start Date": "2023-05-01",
                        "End Date": "2026-04-30",
                        "NAICS Code": "541715",
                        "PSC Code": "AC13",
                        "Solicitation ID": "FA8650-22-R-0001",
                        "generated_internal_id": "CONT_AWD_FA865023F0001_9700",
                    }
                ],
            },
        )

    client = TestClient(create_app(settings, usaspending_lookup_runner=runner))
    response = client.post(
        "/api/federal-data/usaspending/piid-profiles",
        json={"contract_number": " fa8650-23-f-0001 "},
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["normalized_piid"] == "FA8650-23-F-0001"
    assert profile["scenario"] == "standalone_contract"
    assert profile["award_baseline"]["recipient_uei"] == "UEIACME12345"
    assert profile["award_baseline"]["award_amount"] == 1250000
    assert profile["provenance"]["source_capability_id"] == "usaspending"

    profile_id = profile["id"]
    read_response = client.get(
        f"/api/federal-data/usaspending/piid-profiles/{profile_id}"
    )
    assert read_response.status_code == 200
    assert read_response.json()["profile"] == profile

    list_response = client.get("/api/federal-data/usaspending/piid-profiles")
    assert list_response.status_code == 200
    assert list_response.json()["profiles"] == [profile]


def test_usaspending_piid_profile_api_includes_burn_posture_and_vehicle_context(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_PIID_PROFILES_DIR": str(tmp_path / "piid-profiles")}
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        if tool_name == "lookup_piid":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "award_type": "contract",
                    "results": [
                        {
                            "Award ID": "FA8650-23-F-0001",
                            "Award Amount": 1200000,
                            "Start Date": "2023-05-01",
                            "End Date": "2025-04-30",
                            "generated_internal_id": "CONT_AWD_FA865023F0001_9700_CONT_IDV_FA865020D0001_9700",
                        }
                    ],
                },
            )
        if tool_name == "get_award_detail":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "parent_award_piid": "FA8650-20-D-0001",
                    "parent_award_generated_internal_id": "CONT_IDV_FA865020D0001_9700",
                },
            )
        if tool_name == "get_transactions":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "results": [
                        {
                            "id": "txn_base",
                            "action_date": "2023-05-01",
                            "fiscal_year": 2023,
                            "modification_number": "0",
                            "action_type": "Base Award",
                            "federal_action_obligation": 900000,
                            "description": "Base award",
                        },
                        {
                            "id": "txn_deob",
                            "action_date": "2024-09-15",
                            "fiscal_year": 2024,
                            "modification_number": "P00001",
                            "action_type": "Funding Modification",
                            "federal_action_obligation": -50000,
                            "description": "Partial deobligation",
                        },
                    ]
                },
            )
        if tool_name == "get_award_funding":
            return USAspendingMcpToolResult(ok=True, payload={"results": []})
        raise AssertionError(f"unexpected tool {tool_name}")

    response = TestClient(create_app(settings, usaspending_lookup_runner=runner)).post(
        "/api/federal-data/usaspending/piid-profiles",
        json={"contract_number": "FA8650-23-F-0001", "transaction_limit": 25},
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["scenario"] == "idiq_order"
    assert profile["burn_posture"]["net_obligations"] == 850000
    assert profile["burn_posture"]["transaction_count"] == 2
    assert profile["burn_posture"]["deobligation_warnings"] == [
        "P00001 on 2024-09-15 deobligated $50,000.00"
    ]
    assert profile["vehicle_context"]["parent_idv"] == "FA8650-20-D-0001"
    assert profile["vehicle_context"]["linkage_confidence"] == "linked"
    assert (
        "get_transactions",
        {
            "generated_award_id": profile["award_baseline"]["generated_internal_id"],
            "limit": 25,
        },
    ) in calls


def test_usaspending_piid_profile_api_exposes_review_candidates_and_events(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    piid_root = tmp_path / "piid-profiles"
    evidence_root = tmp_path / "evidence"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_PIID_PROFILES_DIR": str(piid_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
        }
    )

    def runner(tool_name, arguments):
        if tool_name == "lookup_piid":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "award_type": "contract",
                    "results": [
                        {
                            "Award ID": "FA8650-23-F-0001",
                            "Recipient Name": "ACME FEDERAL LLC",
                            "Recipient UEI": "UEIACME12345",
                            "Awarding Agency": "Department of the Air Force",
                            "Award Amount": 1250000,
                            "Start Date": "2023-05-01",
                            "End Date": "2026-04-30",
                            "NAICS Code": "541715",
                            "PSC Code": "AC13",
                            "Solicitation ID": "FA8650-22-R-0001",
                            "generated_internal_id": "CONT_AWD_FA865023F0001_9700",
                        }
                    ],
                },
            )
        if tool_name in {"get_award_detail", "get_award_funding"}:
            return USAspendingMcpToolResult(ok=True, payload={"results": []})
        if tool_name == "get_transactions":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "results": [
                        {
                            "id": "txn_base",
                            "action_date": "2023-05-01",
                            "fiscal_year": 2023,
                            "modification_number": "0",
                            "action_type": "Base Award",
                            "federal_action_obligation": 1250000,
                            "description": "Base award",
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected tool {tool_name}")

    response = TestClient(create_app(settings, usaspending_lookup_runner=runner)).post(
        "/api/federal-data/usaspending/piid-profiles",
        json={"contract_number": "FA8650-23-F-0001"},
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    candidate_types = {
        candidate["candidate_type"] for candidate in profile["review_candidates"]
    }
    assert {
        "source_evidence",
        "derived_evidence",
        "packet_field_answer",
        "action_plan_item",
        "risk_register_signal",
        "call_plan_signal",
        "follow_up_route",
    } <= candidate_types
    assert all(
        candidate["review_state"] == "pending_review"
        for candidate in profile["review_candidates"]
    )
    assert all(
        candidate["trusted_output_written"] is False
        for candidate in profile["review_candidates"]
    )
    event_types = {event["event_type"] for event in profile["hermes_events"]}
    assert {
        "profile_started",
        "award_resolved",
        "scenario_classified",
        "burn_posture_computed",
        "pivots_identified",
        "gap_detected",
        "next_enrichment_recommended",
    } <= event_types
    assert LocalEvidenceStore(evidence_root).list() == []


def test_usaspending_piid_profile_review_decision_api_records_event_without_promotion(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    piid_root = tmp_path / "piid-profiles"
    evidence_root = tmp_path / "evidence"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_PIID_PROFILES_DIR": str(piid_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
        }
    )

    def runner(tool_name, arguments):
        if tool_name == "lookup_piid":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "award_type": "contract",
                    "results": [
                        {
                            "Award ID": "FA8650-23-F-0001",
                            "Recipient Name": "ACME FEDERAL LLC",
                            "Recipient UEI": "UEIACME12345",
                            "Awarding Agency": "Department of the Air Force",
                            "Award Amount": 1250000,
                            "generated_internal_id": "CONT_AWD_FA865023F0001_9700",
                        }
                    ],
                },
            )
        if tool_name in {"get_award_detail", "get_transactions", "get_award_funding"}:
            return USAspendingMcpToolResult(ok=True, payload={"results": []})
        raise AssertionError(f"unexpected tool {tool_name}")

    client = TestClient(create_app(settings, usaspending_lookup_runner=runner))
    create_response = client.post(
        "/api/federal-data/usaspending/piid-profiles",
        json={"contract_number": "FA8650-23-F-0001"},
    )
    profile = create_response.json()["profile"]
    source_candidate = next(
        candidate
        for candidate in profile["review_candidates"]
        if candidate["candidate_type"] == "source_evidence"
    )

    response = client.post(
        f"/api/federal-data/usaspending/piid-profiles/{profile['id']}/review-decisions",
        json={
            "candidate_id": source_candidate["id"],
            "review_state": "accepted",
            "reviewer_rationale": "Baseline facts are ready to route later.",
        },
    )

    assert response.status_code == 200
    updated_profile = response.json()["profile"]
    accepted_candidate = next(
        candidate
        for candidate in updated_profile["review_candidates"]
        if candidate["id"] == source_candidate["id"]
    )
    assert accepted_candidate["review_state"] == "accepted"
    assert accepted_candidate["trusted_output_written"] is False
    assert updated_profile["hermes_events"][-1]["event_type"] == (
        "review_decision_recorded"
    )
    assert updated_profile["hermes_events"][-1]["payload"]["candidate_id"] == (
        source_candidate["id"]
    )
    assert LocalEvidenceStore(evidence_root).list() == []


def test_usaspending_piid_profile_api_requires_resolved_award(tmp_path) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_PIID_PROFILES_DIR": str(tmp_path / "piid-profiles")}
    )
    client = TestClient(
        create_app(
            settings,
            usaspending_lookup_runner=lambda tool_name, arguments: (
                USAspendingMcpToolResult(
                    ok=True,
                    payload={"award_type": None, "results": []},
                )
            ),
        )
    )

    response = client.post(
        "/api/federal-data/usaspending/piid-profiles",
        json={"contract_number": "missing-piid"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "resolved USAspending award is required"


def test_document_intake_runtime_lists_review_gated_capture_candidates(
    tmp_path,
) -> None:
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
                (
                    b"Customer needs transition proof and PM follow up.\n"
                    b"Response-time risk could affect the recompete.\n"
                    b"Decision maker expects a customer meeting before the next milestone."
                ),
                "text/markdown",
            )
        },
    )
    record = upload_response.json()["record"]

    response = client.get("/api/document-intake/capture-candidates")

    assert response.status_code == 200
    candidates = response.json()["candidates"]
    candidate_types = {candidate["candidate_type"] for candidate in candidates}
    assert candidate_types >= {
        "action_plan_item",
        "packet_field_answer",
        "risk_register_item",
        "call_plan_signal",
    }
    risk_candidate = next(
        candidate
        for candidate in candidates
        if candidate["candidate_type"] == "risk_register_item"
    )
    assert risk_candidate["review_state"] == "pending_review"
    assert risk_candidate["trusted_output_written"] is False
    assert risk_candidate["target_workflow"] == "risk_register"
    assert risk_candidate["source_intake_record_id"] == record["id"]
    assert (
        risk_candidate["source_extraction_bundle_id"]
        == (record["extraction_bundle_id"])
    )
    assert risk_candidate["source_draft_part_id"].startswith(
        f"draft_{record['extraction_bundle_id']}_"
    )
    assert risk_candidate["source_span_ids"]
    assert risk_candidate["recommendation"]
    assert risk_candidate["rationale"]
    assert LocalEvidenceStore(evidence_root).list() == []
    assert len(DocumentIntakeStore(intake_root).list_capture_candidates()) == len(
        candidates
    )


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


def test_runtime_settings_expose_piid_profile_store_path(tmp_path) -> None:
    profile_root = tmp_path / "profiles"

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_PIID_PROFILES_DIR": str(profile_root)}
    )

    assert settings.ariadne_piid_profiles_dir == profile_root


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


def test_command_center_shell_shows_document_derived_draft_parts(tmp_path) -> None:
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
    assert "Document-Derived Draft Parts" in response.text
    assert "Document extraction flags risk candidate" in response.text
    assert "Source spans:" in response.text
    assert "Recommendation:" in response.text
    assert "Document Bundle:" in response.text
    assert "Trusted writes still require reviewer action" in response.text


def test_command_center_shell_shows_document_intake_accepted_evidence_status(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
            "ARIADNE_EVIDENCE_DIR": str(tmp_path / "evidence"),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    upload_response = client.post(
        "/api/document-intake/uploads",
        files={
            "file": (
                "customer-brief.md",
                b"Customer needs transition proof. Risk needs PM follow up.",
                "text/markdown",
            )
        },
    )
    record = upload_response.json()["record"]
    draft = client.get("/api/document-intake/extraction-drafts").json()["drafts"][0]
    draft_part = draft["intelligence_pieces"][0]
    accept_response = client.post(
        "/api/document-intake/review-decisions",
        json={
            "action": "accept_evidence",
            "extraction_bundle_id": record["extraction_bundle_id"],
            "source_span_ids": draft_part["source_span_ids"],
            "draft_part_id": draft_part["id"],
            "reviewer_rationale": "Reviewer accepted source span as trusted evidence.",
        },
    )

    response = client.get("/")

    assert accept_response.status_code == 200
    assert response.status_code == 200
    assert "Accepted Evidence: 1" in response.text
    assert "Evidence accepted" in response.text
    assert accept_response.json()["evidence"]["id"] in response.text
    assert "Reviewer accepted source span as trusted evidence." in response.text


def test_command_center_shell_shows_review_gated_capture_candidates(
    tmp_path,
) -> None:
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
                (
                    b"Customer needs transition proof and PM follow up.\n"
                    b"Response-time risk could affect the recompete.\n"
                    b"Decision maker expects a customer meeting before the next milestone."
                ),
                "text/markdown",
            )
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Review-Gated Capture Candidates" in response.text
    assert "Suggested next actions" in response.text
    assert "Capture Action Plan" in response.text
    assert "Living Briefing Packet" in response.text
    assert "Risk Register" in response.text
    assert "Call Plan" in response.text
    assert "Review Candidate" in response.text
    assert "Route Candidate" in response.text
    assert "Ignore Candidate" in response.text
    assert "Trusted outputs still require acceptance" in response.text


def test_command_center_shell_shows_knowledge_note_projections(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
            "ARIADNE_EVIDENCE_DIR": str(tmp_path / "evidence"),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    upload_response = client.post(
        "/api/document-intake/uploads",
        files={
            "file": (
                "customer-brief.md",
                b"Customer needs transition proof. Risk needs PM follow up.",
                "text/markdown",
            )
        },
    )
    record = upload_response.json()["record"]
    draft = client.get("/api/document-intake/extraction-drafts").json()["drafts"][0]
    draft_part = draft["intelligence_pieces"][0]
    accept_response = client.post(
        "/api/document-intake/review-decisions",
        json={
            "action": "accept_evidence",
            "extraction_bundle_id": record["extraction_bundle_id"],
            "source_span_ids": draft_part["source_span_ids"],
            "draft_part_id": draft_part["id"],
            "reviewer_rationale": "Reviewer accepted source span as trusted evidence.",
        },
    )
    projection_response = client.post(
        "/api/document-intake/knowledge-note-projections",
        json={"extraction_bundle_id": record["extraction_bundle_id"]},
    )

    response = client.get("/")

    assert accept_response.status_code == 200
    assert projection_response.status_code == 200
    assert response.status_code == 200
    assert "Knowledge Note Projections" in response.text
    assert "Human-readable one-way notes" in response.text
    assert "Knowledge Note Projection: customer-brief.md" in response.text
    assert accept_response.json()["evidence"]["id"] in response.text
    assert "Structured Ariadne records remain source of truth" in response.text
    assert "Open Markdown Projection" in response.text
    assert "Cannot overwrite structured knowledge" in response.text


def test_command_center_shell_shows_document_intake_adapter_hooks() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert "Document Intake Capabilities" in response.text
    assert "Ariadne Generic Text Extractor" in response.text
    assert "Project Theseus Solicitation Parser Hook" in response.text
    assert "MinerU Layout Extraction Hook" in response.text
    assert "RAGAnything Retrieval Hook" in response.text
    assert "LightRAG Knowledge Layer Hook" in response.text
    assert "Deferred hooks do not invoke external tools" in response.text
    assert "ExtractionBundle boundary" in response.text
    assert "/api/document-intake/capabilities" in response.text


def test_command_center_shell_shows_federal_data_capability_registry() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert "Federal Data Capabilities" in response.text
    assert "USAspending" in response.text
    assert "SAM.gov" in response.text
    assert "GSA CALC+" in response.text
    assert "BLS OEWS" in response.text
    assert "GSA Per Diem" in response.text
    assert "eCFR" in response.text
    assert "Federal Register" in response.text
    assert "Regulations.gov" in response.text
    assert "product integrated" in response.text
    assert "registered" in response.text
    assert "No upstream MCP source is vendored into Ariadne" in response.text
    assert "Initialize smoke checks use JSON-RPC initialize only" in response.text
    assert "/api/federal-data/capabilities/{capability_id}/smoke-check" in response.text
    assert "/api/federal-data/capabilities" in response.text


def test_command_center_shell_shows_piid_profile_command_surface(tmp_path) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_PIID_PROFILES_DIR": str(tmp_path / "piid-profiles"),
            "ARIADNE_EVIDENCE_DIR": str(tmp_path / "evidence"),
        }
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        if tool_name == "lookup_piid":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "award_type": "contract",
                    "results": [
                        {
                            "Award ID": "FA8650-23-F-0001",
                            "Recipient Name": "ACME FEDERAL LLC",
                            "Recipient UEI": "UEIACME12345",
                            "Awarding Agency": "Department of the Air Force",
                            "Awarding Sub Agency": "Air Force Materiel Command",
                            "Award Amount": 1250000,
                            "Start Date": "2023-05-01",
                            "End Date": "2026-04-30",
                            "NAICS Code": "541715",
                            "PSC Code": "AC13",
                            "Solicitation ID": "FA8650-22-R-0001",
                            "generated_internal_id": "CONT_AWD_FA865023F0001_9700",
                        }
                    ],
                },
            )
        if tool_name in {"get_award_detail", "get_award_funding"}:
            return USAspendingMcpToolResult(ok=True, payload={"results": []})
        if tool_name == "get_transactions":
            return USAspendingMcpToolResult(
                ok=True,
                payload={
                    "results": [
                        {
                            "id": "txn_base",
                            "action_date": "2023-05-01",
                            "fiscal_year": 2023,
                            "modification_number": "0",
                            "action_type": "Base Award",
                            "federal_action_obligation": 1250000,
                            "description": "Base award",
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected tool {tool_name}")

    client = TestClient(create_app(settings, usaspending_lookup_runner=runner))
    create_response = client.post(
        "/api/federal-data/usaspending/piid-profiles",
        json={"contract_number": "FA8650-23-F-0001"},
    )
    profile = create_response.json()["profile"]
    candidate = next(
        candidate
        for candidate in profile["review_candidates"]
        if candidate["candidate_type"] == "follow_up_route"
    )
    review_response = client.post(
        f"/api/federal-data/usaspending/piid-profiles/{profile['id']}/review-decisions",
        json={
            "candidate_id": candidate["id"],
            "review_state": "routed",
            "reviewer_rationale": "Route solicitation pivot to next enrichment.",
        },
    )
    call_count_after_profile_actions = len(calls)

    response = client.get("/")

    assert create_response.status_code == 200
    assert review_response.status_code == 200
    assert response.status_code == 200
    assert len(calls) == call_count_after_profile_actions
    assert "PIID Profile Command Surface" in response.text
    assert "FA8650-23-F-0001" in response.text
    assert "ACME FEDERAL LLC" in response.text
    assert "Award baseline" in response.text
    assert "Burn posture" in response.text
    assert "Vehicle context" in response.text
    assert "Deterministic pivots" in response.text
    assert "Recommended enrichments" in response.text
    assert "PIID review candidates" in response.text
    assert "Provenance" in response.text
    assert "SAM.gov opportunity enrichment" in response.text
    assert "Review State: Routed" in response.text
    assert "trusted output not written" in response.text
    assert "Draft report" in response.text
    assert "Export XLSX" in response.text
    assert "Export DOCX" in response.text
    assert "Prepare visual briefing" in response.text
    assert "Deferred until Artifact Renderer work exists" in response.text
    assert LocalEvidenceStore(tmp_path / "evidence").list() == []


def test_command_center_shell_shows_document_intake_demo_thread() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert "Document Intake Demo Thread" in response.text
    assert "customer-capture-brief.md" in response.text
    assert "Classification: Ready For Quick Capture - Generic Source Material" in (
        response.text
    )
    assert "Extraction Bundle: Complete - Pending Review" in response.text
    assert "Source spans:" in response.text
    assert "Extraction warnings: 0" in response.text
    assert "Document extraction flags risk candidate" in response.text
    assert "Skill-chain options" in response.text
    assert "Accepted source-span evidence" in response.text
    assert "ev_demo_document_transition_risk" in response.text
    assert "Review-gated next actions" in response.text
    assert "Capture Action Plan" in response.text
    assert "Living Briefing Packet" in response.text
    assert "Risk Register" in response.text
    assert "Call Plan" in response.text
    assert "Knowledge Note Projection: customer-capture-brief.md" in response.text
    assert "Open Markdown Projection" in response.text


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
