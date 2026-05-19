from ariadne.config import RuntimeSettings
from ariadne.capture_research import (
    CapabilityProvenance,
    CaptureResearchSourceMode,
    SourceCollectionProviderManifest,
    SourceFinding,
    SourceProviderSmokeRunnerResult,
    WebSourceCollectionRecord,
)
from ariadne.document_intake import DocumentIntakeStore
from ariadne.evidence import LocalEvidenceStore, create_source_evidence
from ariadne.federal_data import FederalDataInitializeRunnerResult
from ariadne.local_admin_model import (
    LocalAdminDraftAssist,
    LocalAdminDraftSuggestion,
    LocalAdminModelAssistStatus,
)
from ariadne.next_action_recommendations import (
    NextActionRecommendationReviewState,
    NextActionRecommendationStore,
    discard_next_action_recommendation,
    refresh_stale_next_action_recommendation,
)
from ariadne.sam_gov_profiles import (
    SamGovAttachmentFetchResult,
    SamGovMcpToolResult,
    SamGovSourceMode,
)
from ariadne.server import create_app
from ariadne.usaspending import USAspendingMcpToolResult


class _RuntimeProviderFixtureAdapter:
    source_mode = CaptureResearchSourceMode.LIVE_OLOSTEP
    provider_ids = ("serpapi_live", "olostep_live")

    def collect(
        self,
        run,
        *,
        collected_at: str,
    ) -> tuple[tuple[WebSourceCollectionRecord, ...], tuple[SourceFinding, ...]]:
        provenance = CapabilityProvenance(
            source_capability_id="serpapi_live+olostep_live",
            source_tool_name="collect_provider_backed_public_sources",
            source_package="ariadne.capture_research",
            source_package_version="local",
        )
        limitations = (
            "SerpApi supplies search discovery; Olostep supplies crawl/extraction fallback.",
            "Automated test uses injected provider fixture data.",
        )
        finding = SourceFinding(
            id="source_finding_runtime_fixture_1",
            source_target=run.research_brief.source_targets[0],
            url="https://example.test/provider-result",
            title="Provider-backed fixture finding",
            source_type="provider_backed_public_web",
            collected_at=collected_at,
            excerpt="Provider-backed fixture excerpt.",
            confidence=0.74,
            source_limitations=limitations,
            source_mode=self.source_mode,
            capability_provenance=provenance,
            provider_ids=self.provider_ids,
            approval_basis=run.research_brief.approval_basis,
        )
        record = WebSourceCollectionRecord(
            id="web_collection_runtime_fixture_1",
            source_target=finding.source_target,
            source_mode=self.source_mode,
            collected_at=collected_at,
            capability_provenance=provenance,
            source_limitations=limitations,
            finding_ids=(finding.id,),
            provider_ids=self.provider_ids,
            approval_basis=run.research_brief.approval_basis,
        )
        return (record,), (finding,)


class _RuntimeSmokeRunnerFixture:
    def __init__(self) -> None:
        self.provider_ids: list[str] = []

    def __call__(
        self,
        manifest: SourceCollectionProviderManifest,
        *,
        env: dict[str, str],
        smoke_target: str,
        timeout_seconds: int,
    ) -> SourceProviderSmokeRunnerResult:
        self.provider_ids.append(manifest.id)
        return SourceProviderSmokeRunnerResult(
            ok=True,
            diagnostic_summary="runtime smoke ok " + " ".join(env.values()),
            endpoint_label=f"{manifest.id}_smoke",
            observed_result_count=1,
        )


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
    assert body["registered_count"] == 6
    assert body["product_integrated_count"] == 2
    assert body["smoke_tested_count"] == 0
    assert body["deferred_product_workflow_count"] == 0
    assert body["safe_smoke_check_method"] == "json_rpc_initialize_only"
    assert body["smoke_check_endpoint_template"] == (
        "/api/federal-data/capabilities/{capability_id}/smoke-check"
    )
    assert by_id["usaspending"]["product_status"] == "product_integrated"
    assert by_id["usaspending"]["package"] == "usaspending-gov-mcp"
    assert by_id["sam_gov"]["product_status"] == "product_integrated"
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


def test_sam_gov_entity_profile_api_creates_and_persists_profile(tmp_path) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "entityRegistration": {
                    "uei": "UEIACME12345",
                    "legalBusinessName": "ACME FEDERAL LLC",
                    "cageCode": "1ABC2",
                    "registrationStatus": "Active",
                },
                "coreData": {
                    "businessTypes": ["Small Business"],
                    "entityHierarchy": {
                        "parentUei": "UEIPARENT9999",
                        "parentLegalBusinessName": "ACME HOLDING CORPORATION",
                    },
                },
                "assertions": {"naicsCodes": ["541715"], "pscCodes": ["AC13"]},
            },
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    response = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": " ueiacme12345 "},
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["normalized_pivot"] == "UEIACME12345"
    assert profile["entity_lane"]["provenance"]["source_mode"] == "fake_adapter_test"
    assert profile["entity_lane"]["matches"][0]["legal_business_name"] == (
        "ACME FEDERAL LLC"
    )
    assert profile["entity_lane"]["matches"][0]["parent_uei"] == "UEIPARENT9999"
    assert all(
        candidate["review_state"] == "pending_review"
        for candidate in profile["review_candidates"]
    )
    assert all(
        candidate["trusted_output_written"] is False
        for candidate in profile["review_candidates"]
    )

    read_response = client.get(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}"
    )
    assert read_response.status_code == 200
    assert read_response.json()["profile"] == profile

    list_response = client.get("/api/federal-data/sam-gov/enrichment-profiles")
    assert list_response.status_code == 200
    assert list_response.json()["profiles"] == [profile]
    assert calls == [
        (
            "lookup_entity_by_uei",
            {
                "uei": "UEIACME12345",
                "include_sections": ["entityRegistration", "coreData", "assertions"],
                "sam_registered": "Yes",
            },
        )
    ]


def test_sam_gov_entity_profile_api_uses_live_runner_factory_when_configured(
    tmp_path,
    monkeypatch,
) -> None:
    from fastapi.testclient import TestClient

    factory_calls = []
    tool_calls = []

    def fake_runner_factory(command, timeout_seconds, env):
        factory_calls.append((command, timeout_seconds, env))

        def runner(tool_name, arguments):
            tool_calls.append((tool_name, arguments))
            return SamGovMcpToolResult(
                ok=True,
                payload={
                    "entityRegistration": {
                        "uei": "UEIACME12345",
                        "legalBusinessName": "ACME FEDERAL LLC",
                    },
                },
            )

        return runner

    monkeypatch.setattr(
        "ariadne.server.create_sam_gov_lookup_runner",
        fake_runner_factory,
    )
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles"),
            "SAM_GOV_API_KEY": "live-sam-secret-value",
            "MCP_TOOL_TIMEOUT_SECONDS": "9",
        }
    )

    response = TestClient(create_app(settings)).post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["entity_lane"]["provenance"]["source_mode"] == "live_sam_gov"
    assert "live-sam-secret-value" not in response.text
    assert tool_calls[0][0] == "lookup_entity_by_uei"
    command, timeout_seconds, env = factory_calls[0]
    assert "sam-gov-mcp==0.4.1" in command
    assert timeout_seconds == 9
    assert env["SAM_GOV_API_KEY"] == "live-sam-secret-value"
    assert env["SAM_API_KEY"] == "live-sam-secret-value"


def test_sam_gov_entity_profile_api_requires_key_for_live_action(tmp_path) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )

    response = TestClient(create_app(settings)).post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "SAM.gov API key is required for live SAM.gov entity enrichment"
    )


def test_sam_gov_opportunity_discovery_api_creates_and_persists_profile(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "totalRecords": 1,
                "opportunitiesData": [
                    {
                        "noticeId": "notice-rfi-001",
                        "solicitationNumber": "FA8650-26-RFI-PHOENIX",
                        "title": "Project Phoenix Sources Sought",
                        "type": "Sources Sought",
                        "fullParentPathName": "Department of the Air Force.AFLCMC/PZ",
                        "postedDate": "05/10/2026",
                        "responseDeadLine": "06/10/2026",
                        "naicsCode": "541715",
                        "classificationCode": "AC13",
                    },
                ],
            },
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_opportunity_runner=runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    response = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles/opportunity-discovery",
        json={
            "customer_agency": "Department of the Air Force",
            "office": "AFLCMC/PZ",
            "program_name": "Project Phoenix",
            "notice_type": "sources_sought",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
            "naics_code": "541715",
            "psc_code": "AC13",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    lane = profile["opportunity_discovery_lane"]
    assert lane["discovery_status"] == "success"
    assert lane["provenance"]["source_mode"] == "fake_adapter_test"
    assert lane["records"][0]["notice_id"] == "notice-rfi-001"
    assert "program_name matched title" in lane["records"][0]["match_rationale"]
    assert any(
        candidate["candidate_type"] == "derived_evidence"
        for candidate in profile["review_candidates"]
    )
    assert all(
        candidate["trusted_output_written"] is False
        for candidate in profile["review_candidates"]
    )

    list_response = client.get("/api/federal-data/sam-gov/enrichment-profiles")
    assert list_response.status_code == 200
    assert list_response.json()["profiles"] == [profile]
    assert calls == [
        (
            "search_opportunities",
            {
                "posted_from": "05/01/2026",
                "posted_to": "05/31/2026",
                "notice_type": "r",
                "title": "Project Phoenix",
                "naics_code": "541715",
                "psc_code": "AC13",
                "agency_keyword": "Department of the Air Force AFLCMC/PZ",
                "limit": 10,
                "offset": 0,
            },
        )
    ]


def test_sam_gov_opportunity_discovery_api_requires_key_for_live_action(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )

    response = TestClient(create_app(settings)).post(
        "/api/federal-data/sam-gov/enrichment-profiles/opportunity-discovery",
        json={
            "program_name": "Project Phoenix",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "SAM.gov API key is required for live SAM.gov opportunity discovery"
    )


def test_sam_gov_opportunity_discovery_api_adds_lane_to_existing_profile(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    opportunity_calls = []

    def entity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "entityRegistration": {
                    "uei": "UEIACME12345",
                    "legalBusinessName": "ACME FEDERAL LLC",
                }
            },
        )

    def opportunity_runner(tool_name, arguments):
        opportunity_calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-discovery-001",
                        "solicitationNumber": "FA8650-26-RFI-PHOENIX",
                        "title": "Project Phoenix Sources Sought",
                        "type": "Sources Sought",
                        "fullParentPathName": "Department of the Air Force.AFLCMC/PZ",
                    }
                ]
            },
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=entity_runner,
            sam_gov_opportunity_runner=opportunity_runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]

    response = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/opportunity-discovery",
        json={
            "customer_agency": "Department of the Air Force",
            "office": "AFLCMC/PZ",
            "program_name": "Project Phoenix",
            "notice_type": "sources_sought",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    )

    assert response.status_code == 200
    updated_profile = response.json()["profile"]
    assert updated_profile["entity_lane"]["matches"][0]["legal_business_name"] == (
        "ACME FEDERAL LLC"
    )
    assert updated_profile["opportunity_discovery_lane"]["discovery_status"] == (
        "success"
    )
    assert updated_profile["opportunity_discovery_lane"]["records"][0]["title"] == (
        "Project Phoenix Sources Sought"
    )
    assert any(
        candidate["target_workflow"] == "capture_action_plan"
        for candidate in updated_profile["review_candidates"]
    )
    assert opportunity_calls == [
        (
            "search_opportunities",
            {
                "posted_from": "05/01/2026",
                "posted_to": "05/31/2026",
                "notice_type": "r",
                "title": "Project Phoenix",
                "agency_keyword": "Department of the Air Force AFLCMC/PZ",
                "limit": 100,
                "offset": 0,
            },
        )
    ]


def test_sam_gov_known_opportunity_api_adds_lane_to_existing_profile(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    entity_calls = []
    opportunity_calls = []

    def entity_runner(tool_name, arguments):
        entity_calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "entityRegistration": {
                    "uei": "UEIACME12345",
                    "legalBusinessName": "ACME FEDERAL LLC",
                }
            },
        )

    def opportunity_runner(tool_name, arguments):
        opportunity_calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-known-001",
                        "solicitationNumber": "FA8650-26-R-0001",
                        "title": "Project Phoenix final RFP",
                        "type": "Solicitation",
                        "fullParentPathName": "Department of the Air Force.AFLCMC/PZ",
                        "postedDate": "05/15/2026",
                        "responseDeadLine": "06/20/2026",
                    }
                ]
            },
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=entity_runner,
            sam_gov_opportunity_runner=opportunity_runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]

    response = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "fa8650-26-r-0001",
            "pivot_type": "solicitation_number",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    updated_profile = response.json()["profile"]
    assert updated_profile["entity_lane"]["matches"][0]["legal_business_name"] == (
        "ACME FEDERAL LLC"
    )
    lane = updated_profile["known_opportunity_lane"]
    assert lane["lookup_status"] == "success"
    assert lane["provenance"]["source_mode"] == "fake_adapter_test"
    assert lane["records"][0]["solicitation_number"] == "FA8650-26-R-0001"
    assert any(
        candidate["candidate_type"] == "packet_field_answer"
        for candidate in updated_profile["review_candidates"]
    )
    assert all(
        candidate["trusted_output_written"] is False
        for candidate in updated_profile["review_candidates"]
    )
    assert opportunity_calls == [
        (
            "search_opportunities",
            {
                "posted_from": "05/01/2026",
                "posted_to": "05/31/2026",
                "solicitation_number": "FA8650-26-R-0001",
                "limit": 5,
                "offset": 0,
            },
        )
    ]


def test_sam_gov_known_opportunity_api_requires_key_for_live_action(tmp_path) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )

    def entity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={"entityRegistration": {"uei": "UEIACME12345"}},
        )

    profile = (
        TestClient(
            create_app(
                settings,
                sam_gov_entity_runner=entity_runner,
                sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
            )
        )
        .post(
            "/api/federal-data/sam-gov/enrichment-profiles",
            json={"input_pivot": "UEIACME12345"},
        )
        .json()["profile"]
    )

    response = TestClient(create_app(settings)).post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "FA8650-26-R-0001",
            "pivot_type": "solicitation_number",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "SAM.gov API key is required for live SAM.gov known opportunity enrichment"
    )


def test_sam_gov_attachment_download_api_requires_approval_and_routes_to_document_intake(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles"),
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
        }
    )
    fetch_calls = []

    def entity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={"entityRegistration": {"uei": "UEIACME12345"}},
        )

    def opportunity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-known-001",
                        "solicitationNumber": "FA8650-26-R-0001",
                        "title": "Project Phoenix final RFP",
                        "type": "Solicitation",
                        "resourceLinks": [
                            {
                                "title": "Project Phoenix notes",
                                "url": "https://sam.gov/api/prod/opps/v3/resources/files/notice-known-001/project-phoenix-notes.txt",
                                "filename": "project-phoenix-notes.txt",
                                "mimeType": "text/plain",
                            }
                        ],
                    }
                ]
            },
        )

    def attachment_fetcher(url):
        fetch_calls.append(url)
        return SamGovAttachmentFetchResult(
            ok=True,
            content=b"Customer needs transition proof. Response deadline drives capture actions.",
            filename="project-phoenix-notes.txt",
            mime_type="text/plain",
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=entity_runner,
            sam_gov_opportunity_runner=opportunity_runner,
            sam_gov_attachment_fetcher=attachment_fetcher,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]
    enriched_profile = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "FA8650-26-R-0001",
            "pivot_type": "solicitation_number",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    ).json()["profile"]
    attachment = enriched_profile["attachment_intake_lane"]["attachments"][0]
    assert attachment["download_status"] == "pending_approval"
    assert fetch_calls == []

    response = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/attachments/{attachment['id']}/approve-download",
        json={
            "reviewer_rationale": "Official SAM.gov attachment is approved for Document Intake."
        },
    )

    assert response.status_code == 200
    body = response.json()
    intake_record = body["intake_record"]
    updated_attachment = body["profile"]["attachment_intake_lane"]["attachments"][0]
    assert fetch_calls == [attachment["url"]]
    assert updated_attachment["download_status"] == "downloaded"
    assert updated_attachment["intake_record_id"] == intake_record["id"]
    assert intake_record["filename"] == "project-phoenix-notes.txt"
    assert intake_record["status"] == "ready_for_quick_capture"
    assert intake_record["material_type"] == "generic_source_material"
    assert intake_record["source_provenance"] == {
        "source_system": "sam.gov",
        "sam_gov_profile_id": profile["id"],
        "sam_gov_attachment_id": attachment["id"],
        "sam_gov_attachment_url": attachment["url"],
        "sam_gov_source_mode": "fake_adapter_test",
        "sam_gov_source_notice_id": "notice-known-001",
        "sam_gov_source_solicitation_number": "FA8650-26-R-0001",
    }
    store = DocumentIntakeStore(tmp_path / "document-intake")
    assert (
        store.read(intake_record["id"]).source_provenance
        == (intake_record["source_provenance"])
    )
    assert store.list_extraction_bundles(document_id=intake_record["id"])


def test_sam_gov_attachment_download_api_records_inaccessible_source_limitation(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles"),
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
        }
    )

    def entity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={"entityRegistration": {"uei": "UEIACME12345"}},
        )

    def opportunity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-known-001",
                        "solicitationNumber": "FA8650-26-R-0001",
                        "title": "Project Phoenix final RFP",
                        "resourceLinks": [
                            "https://sam.gov/api/prod/opps/v3/resources/files/notice-known-001/missing.pdf"
                        ],
                    }
                ]
            },
        )

    def attachment_fetcher(url):
        return SamGovAttachmentFetchResult(
            ok=False,
            error_message="SAM.gov fixture returned 404 for archived attachment.",
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=entity_runner,
            sam_gov_opportunity_runner=opportunity_runner,
            sam_gov_attachment_fetcher=attachment_fetcher,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]
    enriched_profile = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "FA8650-26-R-0001",
            "pivot_type": "solicitation_number",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    ).json()["profile"]
    attachment = enriched_profile["attachment_intake_lane"]["attachments"][0]

    response = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/attachments/{attachment['id']}/approve-download",
        json={"reviewer_rationale": "Approved archive retrieval attempt."},
    )

    assert response.status_code == 200
    body = response.json()
    failed_attachment = body["profile"]["attachment_intake_lane"]["attachments"][0]
    assert body["intake_record"] is None
    assert failed_attachment["download_status"] == "inaccessible"
    assert (
        "SAM.gov fixture returned 404 for archived attachment."
        in (failed_attachment["source_limitations"])
    )
    assert (
        "SAM.gov fixture returned 404 for archived attachment."
        in (body["profile"]["attachment_intake_lane"]["source_limitations"])
    )
    assert DocumentIntakeStore(tmp_path / "document-intake").list() == []


def test_sam_gov_attachment_download_routes_solicitation_family_to_parser_required_intake(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles"),
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
        }
    )

    def entity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={"entityRegistration": {"uei": "UEIACME12345"}},
        )

    def opportunity_runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-known-001",
                        "solicitationNumber": "FA8650-26-R-0001",
                        "title": "Project Phoenix final RFP",
                        "resourceLinks": [
                            {
                                "title": "Final RFP package",
                                "url": "https://sam.gov/api/prod/opps/v3/resources/files/notice-known-001/final-rfp.pdf",
                                "filename": "final-rfp.pdf",
                                "mimeType": "application/pdf",
                            }
                        ],
                    }
                ]
            },
        )

    def attachment_fetcher(url):
        return SamGovAttachmentFetchResult(
            ok=True,
            content=b"%PDF-1.4\n...",
            filename="final-rfp.pdf",
            mime_type="application/pdf",
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=entity_runner,
            sam_gov_opportunity_runner=opportunity_runner,
            sam_gov_attachment_fetcher=attachment_fetcher,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]
    enriched_profile = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "FA8650-26-R-0001",
            "pivot_type": "solicitation_number",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    ).json()["profile"]
    attachment = enriched_profile["attachment_intake_lane"]["attachments"][0]

    response = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/attachments/{attachment['id']}/approve-download",
        json={
            "reviewer_rationale": "Official solicitation package approved for queueing."
        },
    )

    assert response.status_code == 200
    body = response.json()
    intake_record = body["intake_record"]
    updated_attachment = body["profile"]["attachment_intake_lane"]["attachments"][0]
    assert intake_record["status"] == "parser_required"
    assert intake_record["material_type"] == "solicitation_document"
    assert "Solicitation Parser Capability" in intake_record["capability_hint"]
    assert updated_attachment["download_status"] == "downloaded"
    assert updated_attachment["intake_status"] == "parser_required"
    store = DocumentIntakeStore(tmp_path / "document-intake")
    assert (
        store.read(intake_record["id"]).material_type.value == "solicitation_document"
    )
    assert store.list_extraction_bundles(document_id=intake_record["id"]) == []


def test_sam_gov_entity_profile_review_decision_api_records_event(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )

    def runner(tool_name, arguments):
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "entityRegistration": {
                    "uei": "UEIACME12345",
                    "legalBusinessName": "ACME FEDERAL LLC",
                },
            },
        )

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]
    source_candidate = next(
        candidate
        for candidate in profile["review_candidates"]
        if candidate["candidate_type"] == "source_evidence"
    )

    response = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/review-decisions",
        json={
            "candidate_id": source_candidate["id"],
            "review_state": "accepted",
            "reviewer_rationale": "Entity identity is ready for later routing.",
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
    assert (
        updated_profile["hermes_events"][-1]["payload"]["candidate_id"]
        == (source_candidate["id"])
    )


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
    assert (
        updated_profile["hermes_events"][-1]["payload"]["candidate_id"]
        == (source_candidate["id"])
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


def test_runtime_settings_expose_sam_gov_profile_store_path(tmp_path) -> None:
    profile_root = tmp_path / "sam-gov-profiles"

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(profile_root)}
    )

    assert settings.ariadne_sam_gov_profiles_dir == profile_root


def test_runtime_settings_expose_capability_run_store_path(tmp_path) -> None:
    run_root = tmp_path / "capability-runs"

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(run_root)}
    )

    assert settings.ariadne_capability_runs_dir == run_root


def test_prompted_capture_research_api_creates_lists_and_reads_runs(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research the customer's historical use of this contract vehicle.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["customer_research", "call_plan_cro"],
            "source_targets": ["public customer website"],
            "source_limits": ["public_web_only", "no_linkedin"],
            "evidence_goals": ["Find customer hot buttons and engagement questions."],
        },
    )

    assert create_response.status_code == 200
    run = create_response.json()["run"]
    assert run["status"] == "planned"
    assert run["opportunity_id"] == "opp_aflcmc_recompete"
    assert run["user_prompt"]["prompt"] == (
        "Research the customer's historical use of this contract vehicle."
    )
    assert run["research_trigger_context"]["trigger_type"] == (
        "user_prompted_research_request"
    )
    assert run["research_brief"]["selected_lenses"] == [
        "customer_research",
        "call_plan_cro",
    ]
    assert run["research_brief"]["source_limits"] == [
        "public_web_only",
        "no_linkedin",
    ]
    assert run["source_collection_records"] == []
    assert run["source_findings"] == []
    assert run["capability_run_refs"] == []

    list_response = client.get("/api/capture-research/runs")

    assert list_response.status_code == 200
    assert [item["research_run_id"] for item in list_response.json()["runs"]] == [
        run["research_run_id"]
    ]

    detail_response = client.get(f"/api/capture-research/runs/{run['research_run_id']}")

    assert detail_response.status_code == 200
    assert detail_response.json()["run"]["research_run_id"] == run["research_run_id"]
    assert len(list(research_root.glob("*.json"))) == 1


def test_command_center_shell_shows_prompted_capture_research_runs(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research the customer's historical use of this contract vehicle.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["customer_research", "call_plan_cro"],
            "source_targets": ["public customer website"],
            "source_limits": ["public_web_only", "no_linkedin"],
            "evidence_goals": ["Find customer hot buttons and engagement questions."],
        },
    )

    response = client.get("/")

    assert create_response.status_code == 200
    assert response.status_code == 200
    assert "Capture Research Enrichment" in response.text
    assert "1 persisted" in response.text
    assert "Research the customer&#x27;s historical use of this contract vehicle." in (
        response.text
    )
    assert "Status: Planned" in response.text
    assert "Lenses: customer research, call plan cro" in response.text
    assert "Source limits: public_web_only, no_linkedin" in response.text
    assert "No source collection has run for this brief." in response.text


def test_capture_research_api_and_shell_show_source_profile_refs(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research which public sources clarify incumbent and buyer office.",
            "trigger_summary": "SAM.gov ambiguity and PIID source limitation need research.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["customer_research"],
            "source_targets": ["public agency pages", "public award notices"],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Clarify buyer office and incumbent signals."],
            "source_profile_refs": [
                {
                    "source_profile_type": "piid_contract_intelligence_profile",
                    "source_profile_id": "piid_profile_FA8650_23_F_0001",
                    "source_element_key": "gaps.prime_recipient",
                    "source_element_summary": "PIID profile cannot resolve PRIME recipient.",
                },
                {
                    "source_profile_type": "sam_gov_enrichment_profile",
                    "source_profile_id": "sam_profile_PROJECT_PHOENIX",
                    "source_element_key": "opportunity_discovery.ambiguous_program_name",
                    "source_element_summary": "SAM.gov discovery found ambiguous Project Phoenix notices.",
                },
            ],
        },
    )

    assert create_response.status_code == 200
    run = create_response.json()["run"]
    assert run["research_trigger_context"]["trigger_type"] == "source_profile_context"
    assert run["research_trigger_context"]["summary"] == (
        "SAM.gov ambiguity and PIID source limitation need research."
    )
    assert run["user_prompt"]["prompt"] == (
        "Research which public sources clarify incumbent and buyer office."
    )
    assert [ref["source_profile_id"] for ref in run["source_profile_refs"]] == [
        "piid_profile_FA8650_23_F_0001",
        "sam_profile_PROJECT_PHOENIX",
    ]
    response_json = create_response.text
    assert "award_baseline" not in response_json
    assert "burn_posture" not in response_json
    assert "entity_matches" not in response_json
    assert "opportunity_records" not in response_json
    assert "attachment_metadata" not in response_json

    shell_response = client.get("/")

    assert shell_response.status_code == 200
    assert "Trigger: source_profile_context" in shell_response.text
    assert "PIID Contract Intelligence Profile" in shell_response.text
    assert "piid_profile_FA8650_23_F_0001" in shell_response.text
    assert "gaps.prime_recipient" in shell_response.text
    assert "SAM.gov Enrichment Profile" in shell_response.text
    assert "sam_profile_PROJECT_PHOENIX" in shell_response.text


def test_fake_web_source_collection_api_and_shell_show_findings(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research public customer and incumbent context.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["customer_research"],
            "source_targets": ["public agency pages", "public award notices"],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Find customer and incumbent signals."],
        },
    )
    research_run_id = create_response.json()["run"]["research_run_id"]

    collect_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/fake-web-source-collection",
        json={"collected_at": "2026-05-18T12:05:00+00:00"},
    )

    assert collect_response.status_code == 200
    run = collect_response.json()["run"]
    assert run["status"] == "needs_review"
    assert [record["source_target"] for record in run["source_collection_records"]] == [
        "public agency pages",
        "public award notices",
    ]
    assert all(
        record["source_mode"] == "fake_adapter_test"
        for record in run["source_collection_records"]
    )
    assert len(run["source_findings"]) == 2
    assert run["source_findings"][0]["url"] == (
        "fake://capture-research/public-agency-pages"
    )
    assert run["source_findings"][0]["source_mode"] == "fake_adapter_test"
    assert run["source_findings"][0]["capability_provenance"][
        "source_capability_id"
    ] == "fake_web_source_collection"
    assert "Fake adapter test data is not live source-provider success." in (
        run["source_findings"][0]["source_limitations"]
    )
    assert "live_firecrawl" not in collect_response.text

    shell_response = client.get("/")

    assert shell_response.status_code == 200
    assert "Source collection records: 2" in shell_response.text
    assert "public agency pages" in shell_response.text
    assert "Fake source finding for public agency pages" in shell_response.text
    assert "fake://capture-research/public-agency-pages" in shell_response.text
    assert "fake adapter test" in shell_response.text
    assert "Fake adapter test data is not live source-provider success." in (
        shell_response.text
    )


def test_requirements_fit_api_and_shell_show_seller_baseline_refs(
    tmp_path,
) -> None:
    research_root = tmp_path / "capture-research"
    evidence_root = tmp_path / "evidence"
    reference_root = tmp_path / "reference-wiki"
    reference_root.mkdir()
    (reference_root / "seller-baseline.md").write_text(
        "---\n"
        "title: Seller Baseline Proof\n"
        "---\n\n"
        "# Seller Baseline Proof\n\n"
        "Seller transition proof, cyber modernization capability, and vehicle experience.\n",
        encoding="utf-8",
    )
    LocalEvidenceStore(evidence_root).write(
        create_source_evidence(
            evidence_id="ev_runtime_seller_baseline",
            content=(
                "Accepted seller evidence: transition past performance, cyber "
                "modernization capability, and contract vehicle proof."
            ),
            source_ref="accepted seller proof note",
            opportunity_id="opp_aflcmc_recompete",
        )
    )
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
            "ARIADNE_REFERENCE_WIKI_DIR": str(reference_root),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research customer transition modernization needs.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["customer_research", "competitive_positioning"],
            "source_targets": ["public agency modernization page"],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Compare transition need against seller proof."],
        },
    )
    research_run_id = create_response.json()["run"]["research_run_id"]
    collect_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/fake-web-source-collection",
        json={"collected_at": "2026-05-18T12:05:00+00:00"},
    )

    fit_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/requirements-fit-analysis",
        json={"analyzed_at": "2026-05-18T12:10:00+00:00"},
    )

    assert collect_response.status_code == 200
    assert fit_response.status_code == 200
    run = fit_response.json()["run"]
    assert run["status"] == "needs_review"
    assert [ref["ref_type"] for ref in run["seller_baseline_refs"]] == [
        "accepted_evidence",
        "reference_wiki_note",
    ]
    assert run["seller_baseline_refs"][0]["source_ref"] == (
        "ev_runtime_seller_baseline"
    )
    assert run["requirements_fit_analysis"]["strengths"]
    assert run["requirements_fit_analysis"]["proof_needs"]
    assert run["insight_candidates"]
    assert all(
        candidate["review_state"] == "pending_review"
        for candidate in run["insight_candidates"]
    )
    assert "trusted_output_written" not in fit_response.text

    shell_response = client.get("/")

    assert shell_response.status_code == 200
    assert "Seller Capability Baseline" in shell_response.text
    assert "Accepted Evidence ev_runtime_seller_baseline" in shell_response.text
    assert "Seller Baseline Proof" in shell_response.text
    assert "Requirements Fit Analysis" in shell_response.text
    assert "Strengths" in shell_response.text
    assert "Proof needs" in shell_response.text
    assert "Reviewable outputs only" in shell_response.text


def test_competitive_gap_api_and_shell_show_bcc_ready_notes(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    evidence_root = tmp_path / "evidence"
    reference_root = tmp_path / "reference-wiki"
    reference_root.mkdir()
    LocalEvidenceStore(evidence_root).write(
        create_source_evidence(
            evidence_id="ev_runtime_competitive_baseline",
            content=(
                "Accepted seller evidence: transition past performance, cyber "
                "modernization capability, vehicle proof, and staffing constraints."
            ),
            source_ref="accepted competitive baseline note",
            opportunity_id="opp_aflcmc_recompete",
        )
    )
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
            "ARIADNE_REFERENCE_WIKI_DIR": str(reference_root),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research incumbent competitive posture.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["competitive_positioning"],
            "source_targets": ["incumbent vendor cyber staffing vehicle partner profile"],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Find competitor notes and BCC-ready inputs."],
        },
    )
    research_run_id = create_response.json()["run"]["research_run_id"]
    collect_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/fake-web-source-collection",
        json={"collected_at": "2026-05-18T12:05:00+00:00"},
    )
    fit_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/requirements-fit-analysis",
        json={"analyzed_at": "2026-05-18T12:10:00+00:00"},
    )

    gap_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/competitive-gap-analysis",
        json={"analyzed_at": "2026-05-18T12:15:00+00:00"},
    )

    assert collect_response.status_code == 200
    assert fit_response.status_code == 200
    assert gap_response.status_code == 200
    run = gap_response.json()["run"]
    analysis = run["competitive_gap_analysis"]
    assert analysis["discriminator_candidates"]
    assert analysis["vulnerabilities"]
    assert analysis["competitor_incumbent_notes"]
    assert analysis["teaming_partner_needs"]
    assert analysis["bcc_ready_notes"]
    assert analysis["bcc_ready_notes"][0]["bcc_ready_input"] is True
    assert analysis["bcc_artifact_generated"] is False
    assert any(
        candidate["candidate_type"] == "competitive_gap_bcc_ready_note"
        and candidate["target_workflow"] == "bcc_ready_input"
        and candidate["bcc_artifact_generated"] is False
        for candidate in run["insight_candidates"]
    )
    assert "bcc_rows" not in run
    assert "bcc_slides" not in run
    assert "bcc_artifact" not in run

    shell_response = client.get("/")

    assert shell_response.status_code == 200
    assert "Competitive Gap Analysis" in shell_response.text
    assert "Discriminator candidates" in shell_response.text
    assert "Competitor/incumbent notes" in shell_response.text
    assert "Teaming Partner Needs" in shell_response.text
    assert "BCC-ready notes" in shell_response.text
    assert "No BCC artifact generated" in shell_response.text
    assert "later Bidder Comparison Chart work only" in shell_response.text


def test_selected_lens_api_and_shell_show_outputs_by_lens(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    evidence_root = tmp_path / "evidence"
    reference_root = tmp_path / "reference-wiki"
    reference_root.mkdir()
    LocalEvidenceStore(evidence_root).write(
        create_source_evidence(
            evidence_id="ev_runtime_lens_baseline",
            content=(
                "Accepted seller evidence: pricing discipline, staffing model, transition proof, and customer proof points."
            ),
            source_ref="accepted lens baseline note",
            opportunity_id="opp_aflcmc_recompete",
        )
    )
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
            "ARIADNE_REFERENCE_WIKI_DIR": str(reference_root),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research price, burn, workload, and engagement assumptions.",
            "opportunity_id": "opp_aflcmc_recompete",
            "source_profile_refs": [
                {
                    "source_profile_type": "piid_contract_intelligence_profile",
                    "source_profile_id": "piid_profile_FAKE1234",
                    "source_element_key": "burn_posture",
                    "source_element_summary": "PIID profile shows net obligations, monthly burn rate, remaining value, staffing workload, and recompete timing.",
                }
            ],
            "selected_lenses": [
                "price_to_win",
                "burn_rate_analysis",
                "workload_analysis",
                "call_plan_cro",
            ],
            "source_targets": [
                "budget ceiling price FTE staffing workload value proof friction next action"
            ],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Find pricing, burn, workload, and engagement signals."],
        },
    )
    research_run_id = create_response.json()["run"]["research_run_id"]
    collect_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/fake-web-source-collection",
        json={"collected_at": "2026-05-18T12:05:00+00:00"},
    )
    fit_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/requirements-fit-analysis",
        json={"analyzed_at": "2026-05-18T12:10:00+00:00"},
    )
    lens_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/selected-lens-analysis",
        json={"analyzed_at": "2026-05-18T12:20:00+00:00"},
    )

    assert collect_response.status_code == 200
    assert fit_response.status_code == 200
    assert lens_response.status_code == 200
    run = lens_response.json()["run"]
    analyses = {analysis["lens"]: analysis for analysis in run["capture_lens_analyses"]}
    assert set(analyses) == {
        "price_to_win",
        "burn_rate_analysis",
        "workload_analysis",
        "call_plan_cro",
    }
    assert analyses["price_to_win"]["signals"][0]["target_workflow"] == "price_to_win"
    assert analyses["burn_rate_analysis"]["signals"][0]["supporting_source_profile_refs"]
    assert analyses["workload_analysis"]["signals"][0]["supporting_source_finding_ids"]
    assert analyses["call_plan_cro"]["signals"][0]["target_workflow"] == "call_plan"
    assert any(
        "not the primary burn-rate or price-to-win lens" in limitation
        for limitation in analyses["call_plan_cro"]["signals"][0]["source_limitations"]
    )
    assert {candidate.get("lens") for candidate in run["insight_candidates"] if candidate.get("capture_lens_analysis_id")} == {
        "price_to_win",
        "burn_rate_analysis",
        "workload_analysis",
        "call_plan_cro",
    }
    assert "trusted_output_written" not in lens_response.text

    shell_response = client.get("/")

    assert shell_response.status_code == 200
    assert "Selected Capture Lens Analysis" in shell_response.text
    assert "Price-to-Win" in shell_response.text
    assert "Burn Rate Analysis" in shell_response.text
    assert "Workload Analysis" in shell_response.text
    assert "Call Plan CRO" in shell_response.text
    assert "outputs are shown separately by lens" in shell_response.text


def test_capture_research_candidate_projection_review_api_and_shell(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    evidence_root = tmp_path / "evidence"
    reference_root = tmp_path / "reference-wiki"
    reference_root.mkdir()
    LocalEvidenceStore(evidence_root).write(
        create_source_evidence(
            evidence_id="ev_runtime_candidate_baseline",
            content=(
                "Accepted seller evidence: pricing discipline, staffing model, transition proof, and customer proof points."
            ),
            source_ref="accepted candidate baseline note",
            opportunity_id="opp_aflcmc_recompete",
        )
    )
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
            "ARIADNE_REFERENCE_WIKI_DIR": str(reference_root),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research downstream candidate routing.",
            "opportunity_id": "opp_aflcmc_recompete",
            "source_profile_refs": [
                {
                    "source_profile_type": "piid_contract_intelligence_profile",
                    "source_profile_id": "piid_profile_FAKE1234",
                    "source_element_key": "burn_posture",
                    "source_element_summary": "PIID profile shows net obligations, monthly burn rate, remaining value, staffing workload, and recompete timing.",
                }
            ],
            "selected_lenses": [
                "competitive_positioning",
                "price_to_win",
                "burn_rate_analysis",
                "workload_analysis",
                "call_plan_cro",
            ],
            "source_targets": [
                "incumbent vendor budget ceiling price FTE staffing partner vehicle proof friction next action"
            ],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Find routed downstream candidates."],
        },
    )
    research_run_id = create_response.json()["run"]["research_run_id"]
    client.post(
        f"/api/capture-research/runs/{research_run_id}/fake-web-source-collection",
        json={"collected_at": "2026-05-18T12:05:00+00:00"},
    )
    client.post(
        f"/api/capture-research/runs/{research_run_id}/requirements-fit-analysis",
        json={"analyzed_at": "2026-05-18T12:10:00+00:00"},
    )
    client.post(
        f"/api/capture-research/runs/{research_run_id}/competitive-gap-analysis",
        json={"analyzed_at": "2026-05-18T12:15:00+00:00"},
    )
    client.post(
        f"/api/capture-research/runs/{research_run_id}/selected-lens-analysis",
        json={"analyzed_at": "2026-05-18T12:20:00+00:00"},
    )

    projection_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/downstream-candidates",
        json={"projected_at": "2026-05-18T12:30:00+00:00"},
    )

    assert projection_response.status_code == 200
    run = projection_response.json()["run"]
    candidates = run["downstream_candidates"]
    groups = {candidate["candidate_group"] for candidate in candidates}
    assert groups >= {
        "evidence",
        "packet",
        "risk_register",
        "call_plan",
        "follow_up_route",
        "price_workload",
        "teaming",
        "bcc_ready",
    }
    assert all(candidate["trusted_output_written"] is False for candidate in candidates)
    candidate = next(
        item for item in candidates if item["candidate_group"] == "price_workload"
    )
    assert candidate["provenance"]["research_run_id"] == research_run_id
    assert candidate["provenance"]["research_brief"]
    assert candidate["provenance"]["trigger_context"]

    review_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/downstream-candidates/{candidate['id']}/review-decisions",
        json={
            "decision": "route",
            "reviewer_rationale": "Route pricing assumption to price review.",
            "routed_destination": "Price-to-Win Review",
            "decided_at": "2026-05-18T12:35:00+00:00",
        },
    )

    assert review_response.status_code == 200
    reviewed_run = review_response.json()["run"]
    reviewed_candidate = next(
        item for item in reviewed_run["downstream_candidates"] if item["id"] == candidate["id"]
    )
    assert reviewed_candidate["review_state"] == "routed"
    assert reviewed_candidate["routed_destination"] == "Price-to-Win Review"
    assert reviewed_candidate["trusted_output_written"] is False
    assert reviewed_run["review_decisions"][0]["candidate_provenance"]["research_run_id"] == research_run_id
    assert reviewed_run["review_decisions"][0]["trusted_output_written"] is False

    shell_response = client.get("/")

    assert shell_response.status_code == 200
    assert "Reviewable Downstream Candidates" in shell_response.text
    assert "No automatic trusted downstream writes" in shell_response.text
    assert "Price/Workload Assumptions" in shell_response.text
    assert "BCC-Ready Notes" in shell_response.text
    assert "Review decisions" in shell_response.text
    assert "Trusted write: false" in shell_response.text


def test_source_provider_readiness_api_exposes_registry_without_secrets(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "SERPAPI_API_KEY": "serpapi-secret",
            "OLOSTEP_API_KEY": "olostep-secret",
        }
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).get(
        "/api/capture-research/source-providers"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["registry"]["quality_status"] == "full_ready"
    assert body["registry"]["recommended_provider_ids"] == [
        "serpapi_live",
        "olostep_live",
    ]
    assert "serpapi-secret" not in response.text
    assert "olostep-secret" not in response.text
    assert "SERPAPI_API_KEY" in response.text
    assert "OLOSTEP_API_KEY" in response.text


def test_source_provider_smoke_check_api_covers_provider_without_secret_values(
    tmp_path,
) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "FIRECRAWL_API_KEY": "firecrawl-secret",
        }
    )
    runner = _RuntimeSmokeRunnerFixture()

    from fastapi.testclient import TestClient

    response = TestClient(
        create_app(settings, source_provider_smoke_runner=runner)
    ).post(
        "/api/capture-research/source-providers/firecrawl_live/smoke-check",
        json={
            "approved": True,
            "smoke_target": "https://example.com",
            "checked_at": "2026-05-19T10:00:00+00:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["provider_id"] == "firecrawl_live"
    assert body["result"]["status"] == "success"
    assert body["result"]["endpoint_label"] == "firecrawl_live_smoke"
    assert runner.provider_ids == ["firecrawl_live"]
    assert "firecrawl-secret" not in response.text
    assert "FIRECRAWL_API_KEY" in response.text


def test_source_provider_smoke_check_api_requires_approval_without_runner_call(
    tmp_path,
) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "SERPAPI_API_KEY": "serpapi-secret",
        }
    )
    runner = _RuntimeSmokeRunnerFixture()

    from fastapi.testclient import TestClient

    response = TestClient(
        create_app(settings, source_provider_smoke_runner=runner)
    ).post(
        "/api/capture-research/source-providers/serpapi_live/smoke-check",
        json={"approved": False, "smoke_target": "https://example.com"},
    )

    assert response.status_code == 200
    assert response.json()["result"]["status"] == "requires_approval"
    assert runner.provider_ids == []
    assert "serpapi-secret" not in response.text


def test_source_provider_collection_api_requires_approval(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "SERPAPI_API_KEY": "serpapi-secret",
            "OLOSTEP_API_KEY": "olostep-secret",
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(
        create_app(settings, source_provider_adapter=_RuntimeProviderFixtureAdapter())
    )
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research public customer context.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["customer_research"],
            "source_targets": ["https://example.gov/program-office"],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Find customer and incumbent signals."],
        },
    )
    research_run_id = create_response.json()["run"]["research_run_id"]

    collect_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/source-provider-collection",
        json={"approved": False},
    )

    assert collect_response.status_code == 400
    assert "requires explicit approval" in collect_response.text


def test_source_provider_collection_api_records_provider_findings(tmp_path) -> None:
    research_root = tmp_path / "capture-research"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPTURE_RESEARCH_DIR": str(research_root),
            "SERPAPI_API_KEY": "serpapi-secret",
            "OLOSTEP_API_KEY": "olostep-secret",
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(
        create_app(settings, source_provider_adapter=_RuntimeProviderFixtureAdapter())
    )
    create_response = client.post(
        "/api/capture-research/runs",
        json={
            "prompt": "Research public customer context.",
            "opportunity_id": "opp_aflcmc_recompete",
            "selected_lenses": ["customer_research"],
            "source_targets": ["https://example.gov/program-office"],
            "source_limits": ["public_web_only"],
            "evidence_goals": ["Find customer and incumbent signals."],
        },
    )
    research_run_id = create_response.json()["run"]["research_run_id"]

    collect_response = client.post(
        f"/api/capture-research/runs/{research_run_id}/source-provider-collection",
        json={"approved": True, "collected_at": "2026-05-18T12:05:00+00:00"},
    )

    assert collect_response.status_code == 200
    run = collect_response.json()["run"]
    assert run["status"] == "needs_review"
    assert run["source_collection_records"][0]["source_mode"] == "live_olostep"
    assert run["source_collection_records"][0]["provider_ids"] == [
        "serpapi_live",
        "olostep_live",
    ]
    assert run["source_findings"][0]["url"] == "https://example.test/provider-result"
    assert run["source_findings"][0]["capability_provenance"][
        "source_capability_id"
    ] == "serpapi_live+olostep_live"
    assert "serpapi-secret" not in collect_response.text
    assert "olostep-secret" not in collect_response.text


def test_capability_catalog_validation_api_creates_persisted_run(tmp_path) -> None:
    run_root = tmp_path / "capability-runs"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(run_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    create_response = client.post("/api/capability-runs/catalog-validation")

    assert create_response.status_code == 200
    run = create_response.json()["run"]
    assert run["capability_id"] == "capability_catalog_validation"
    assert run["executor_kind"] == "deterministic_python"
    assert run["status"] == "needs_review"
    assert run["outputs"]
    assert run["outputs"][0]["review_state"] == "pending"
    assert run["outputs"][0]["autonomy_recommendation"] == "review_required"
    assert "sources" in run["provenance"]

    list_response = client.get("/api/capability-runs")

    assert list_response.status_code == 200
    assert [item["run_id"] for item in list_response.json()["runs"]] == [
        run["run_id"]
    ]

    detail_response = client.get(f"/api/capability-runs/{run['run_id']}")

    assert detail_response.status_code == 200
    assert detail_response.json()["run"]["run_id"] == run["run_id"]
    assert len(list(run_root.glob("*.json"))) == 1


def test_local_admin_model_readiness_probe_api_records_disabled_outcome(
    tmp_path,
) -> None:
    run_root = tmp_path / "capability-runs"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPABILITY_RUNS_DIR": str(run_root),
            "LOCAL_ADMIN_MODEL_ENABLED": "false",
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    response = client.post("/api/capability-runs/local-admin-model-readiness-probe")

    assert response.status_code == 200
    run = response.json()["run"]
    assert run["capability_id"] == "local_admin_model_readiness_probe"
    assert run["executor_kind"] == "local_admin_model"
    assert run["status"] == "unavailable"
    assert run["provenance"]["model_name"] == "qwen3.5:9b"
    assert run["provenance"]["model_status"] == "disabled"
    assert run["provenance"]["source_mode"] == "local_admin_model_probe"
    assert run["outputs"][0]["output_type"] == "local_admin_model_readiness"
    assert run["outputs"][0]["review_state"] == "pending"
    assert run["outputs"][0]["provenance"]["ollama_required"] is False
    assert len(list(run_root.glob("*.json"))) == 1

    detail_response = client.get(f"/capability-studio/runs/{run['run_id']}")

    assert detail_response.status_code == 200
    assert "local_admin_model_probe" in detail_response.text
    assert "qwen3.5:9b" in detail_response.text
    assert "disabled" in detail_response.text


def test_capability_run_output_review_api_records_decision_without_trusted_writes(
    tmp_path,
) -> None:
    run_root = tmp_path / "capability-runs"
    evidence_root = tmp_path / "evidence"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_CAPABILITY_RUNS_DIR": str(run_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    created_run = client.post("/api/capability-runs/catalog-validation").json()["run"]
    output_id = created_run["outputs"][0]["output_id"]

    review_response = client.post(
        f"/api/capability-runs/{created_run['run_id']}/outputs/{output_id}/review",
        json={
            "decision": "accept",
            "reviewer_rationale": "Catalog finding reviewed; keep as work item.",
        },
    )

    assert review_response.status_code == 200
    reviewed_run = review_response.json()["run"]
    reviewed_output = reviewed_run["outputs"][0]
    assert reviewed_output["review_state"] == "accepted"
    assert reviewed_output["review_decisions"][0]["decision"] == "accept"
    assert reviewed_output["review_decisions"][0]["reviewer_rationale"] == (
        "Catalog finding reviewed; keep as work item."
    )

    detail_response = client.get(f"/api/capability-runs/{created_run['run_id']}")

    assert detail_response.json()["run"]["outputs"][0]["review_state"] == "accepted"
    assert LocalEvidenceStore(evidence_root).list() == []


def test_capability_studio_page_shows_run_history_and_reasoning_view(
    tmp_path,
    monkeypatch,
) -> None:
    run_root = tmp_path / "capability-runs"
    skill_dir = tmp_path / ".github" / "skills" / "thin-studio-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: thin-studio-skill\n"
        "---\n"
        "# Thin Studio Skill\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(run_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    run = client.post("/api/capability-runs/catalog-validation").json()["run"]

    history_response = client.get("/capability-studio")

    assert history_response.status_code == 200
    assert "text/html" in history_response.headers["content-type"]
    assert "Capability Studio" in history_response.text
    assert "Run History" in history_response.text
    assert run["run_id"] in history_response.text
    assert "capability_catalog_validation" in history_response.text

    detail_response = client.get(f"/capability-studio/runs/{run['run_id']}")

    assert detail_response.status_code == 200
    assert "Capability Reasoning View" in detail_response.text
    assert "Capability Provenance" in detail_response.text
    assert "deterministic_python" in detail_response.text
    assert "review_required" in detail_response.text
    assert "Missing capability description metadata" in detail_response.text
    assert "discover_local_capability_catalog" in detail_response.text


def test_capability_studio_page_handles_empty_failed_and_unavailable_states(
    tmp_path,
) -> None:
    run_root = tmp_path / "capability-runs"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(run_root)}
    )

    from ariadne.capability_runs import (
        CapabilityRun,
        CapabilityRunCapabilityType,
        CapabilityRunExecutorKind,
        CapabilityRunOutput,
        CapabilityRunStatus,
        CapabilityRunStore,
    )
    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    empty_response = client.get("/capability-studio")

    assert empty_response.status_code == 200
    assert "No Capability Runs yet" in empty_response.text

    store = CapabilityRunStore(run_root)
    for status in (CapabilityRunStatus.FAILED, CapabilityRunStatus.UNAVAILABLE):
        run = CapabilityRun(
            run_id=f"caprun_{status.value}",
            capability_id=f"{status.value}_capability",
            capability_type=CapabilityRunCapabilityType.ADAPTER,
            executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
            product_workflow="capability_catalog",
            status=status,
            inputs_summary=f"{status.value} run summary",
            outputs=(
                CapabilityRunOutput(
                    output_id=f"{status.value}_output",
                    output_type="capability_catalog_validation_finding",
                    title=f"{status.value.title()} output",
                    summary=f"{status.value} output summary",
                ),
            ),
        )
        store.write(run)

        detail_response = client.get(f"/capability-studio/runs/{run.run_id}")

        assert detail_response.status_code == 200
        assert status.value in detail_response.text
        assert f"Run status is {status.value}." in detail_response.text


def test_capability_studio_reasoning_view_shows_review_decision_history(
    tmp_path,
    monkeypatch,
) -> None:
    run_root = tmp_path / "capability-runs"
    skill_dir = tmp_path / ".github" / "skills" / "reviewed-studio-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: reviewed-studio-skill\n"
        "---\n"
        "# Reviewed Studio Skill\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(run_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    run = client.post("/api/capability-runs/catalog-validation").json()["run"]
    output_id = run["outputs"][0]["output_id"]
    client.post(
        f"/api/capability-runs/{run['run_id']}/outputs/{output_id}/review",
        json={
            "decision": "route",
            "reviewer_rationale": "Send to improvement proposal queue.",
            "routed_destination": "Improvement Proposal",
        },
    )

    detail_response = client.get(f"/capability-studio/runs/{run['run_id']}")

    assert detail_response.status_code == 200
    assert "Review history" in detail_response.text
    assert "route -&gt; Improvement Proposal" in detail_response.text
    assert "Send to improvement proposal queue." in detail_response.text


def test_command_center_surfaces_capability_run_launch_and_review_entries(
    tmp_path,
) -> None:
    run_root = tmp_path / "capability-runs"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(run_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    run = client.post("/api/capability-runs/catalog-validation").json()["run"]
    response = client.get("/")

    assert response.status_code == 200
    assert "Run Capability Catalog Validation" in response.text
    assert "/capability-studio/actions/catalog-validation" in response.text
    assert "Capability Run Outputs Needing Review" in response.text
    assert run["run_id"] in response.text
    assert "needs_review" in response.text
    assert "pending" in response.text
    assert f"/capability-studio/runs/{run['run_id']}" in response.text


def test_command_center_capability_validation_action_opens_studio_detail(
    tmp_path,
    monkeypatch,
) -> None:
    run_root = tmp_path / "capability-runs"
    skill_dir = tmp_path / ".github" / "skills" / "command-center-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: command-center-skill\n"
        "---\n"
        "# Command Center Skill\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_CAPABILITY_RUNS_DIR": str(run_root)}
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).post(
        "/capability-studio/actions/catalog-validation"
    )

    assert response.status_code == 200
    assert "Capability Reasoning View" in response.text
    assert "command-center-skill" in response.text
    assert len(list(run_root.glob("*.json"))) == 1


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


def test_command_center_shell_shows_sam_gov_profiles_without_live_call(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "entityRegistration": {
                    "uei": "UEIACME12345",
                    "legalBusinessName": "ACME FEDERAL LLC",
                },
                "coreData": {"businessTypes": ["Small Business"]},
            },
        )

    from fastapi.testclient import TestClient

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    )
    response = client.get("/")

    assert response.status_code == 200
    assert "SAM.gov Enrichment Profiles" in response.text
    assert "ACME FEDERAL LLC" in response.text
    assert "fake adapter test" in response.text
    assert "Live readiness: missing SAM.gov API key" in response.text
    assert len(calls) == 1


def test_command_center_shell_shows_sam_gov_opportunity_discovery_without_live_call(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-rfi-001",
                        "solicitationNumber": "FA8650-26-RFI-PHOENIX",
                        "title": "Project Phoenix Sources Sought",
                        "type": "Sources Sought",
                        "fullParentPathName": "Department of the Air Force.AFLCMC/PZ",
                        "postedDate": "05/10/2026",
                    }
                ]
            },
        )

    from fastapi.testclient import TestClient

    client = TestClient(
        create_app(
            settings,
            sam_gov_opportunity_runner=runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    client.post(
        "/api/federal-data/sam-gov/enrichment-profiles/opportunity-discovery",
        json={
            "customer_agency": "Department of the Air Force",
            "program_name": "Project Phoenix",
            "notice_type": "sources_sought",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    )
    response = client.get("/")

    assert response.status_code == 200
    assert "Opportunity Discovery lane" in response.text
    assert "Project Phoenix Sources Sought" in response.text
    assert "Sources Sought" in response.text
    assert "Derived Evidence: opportunity match rationale" in response.text
    assert len(calls) == 1


def test_command_center_shell_shows_sam_gov_known_opportunity_without_live_call(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        if tool_name == "lookup_entity_by_uei":
            return SamGovMcpToolResult(
                ok=True,
                payload={
                    "entityRegistration": {
                        "uei": "UEIACME12345",
                        "legalBusinessName": "ACME FEDERAL LLC",
                    }
                },
            )
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-known-001",
                        "solicitationNumber": "FA8650-26-R-0001",
                        "title": "Project Phoenix final RFP",
                        "type": "Solicitation",
                        "fullParentPathName": "Department of the Air Force.AFLCMC/PZ",
                        "postedDate": "05/15/2026",
                    }
                ]
            },
        )

    from fastapi.testclient import TestClient

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=runner,
            sam_gov_opportunity_runner=runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]
    client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "FA8650-26-R-0001",
            "pivot_type": "solicitation_number",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    )
    response = client.get("/")

    assert response.status_code == 200
    assert "Known Opportunity lane" in response.text
    assert "Project Phoenix final RFP" in response.text
    assert "Solicitation" in response.text
    assert "Source Evidence: SAM.gov known opportunity record" in response.text
    assert len(calls) == 2


def test_command_center_shell_shows_sam_gov_attachment_intake_without_download(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles")}
    )
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        if tool_name == "lookup_entity_by_uei":
            return SamGovMcpToolResult(
                ok=True,
                payload={"entityRegistration": {"uei": "UEIACME12345"}},
            )
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-known-001",
                        "solicitationNumber": "FA8650-26-R-0001",
                        "title": "Project Phoenix final RFP",
                        "resourceLinks": [
                            {
                                "title": "Project Phoenix RFP package",
                                "url": "https://sam.gov/api/prod/opps/v3/resources/files/notice-known-001/rfp-package.pdf",
                                "filename": "project-phoenix-rfp.pdf",
                            }
                        ],
                    }
                ]
            },
        )

    from fastapi.testclient import TestClient

    client = TestClient(
        create_app(
            settings,
            sam_gov_entity_runner=runner,
            sam_gov_opportunity_runner=runner,
            sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        )
    )
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]
    client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "FA8650-26-R-0001",
            "pivot_type": "solicitation_number",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    )
    response = client.get("/")

    assert response.status_code == 200
    assert "Attachment Intake lane" in response.text
    assert "Project Phoenix RFP package" in response.text
    assert "pending approval" in response.text
    assert "Document Intake" in response.text
    assert len(calls) == 2


def test_sam_gov_command_surface_api_summarizes_four_lane_profile(tmp_path) -> None:
    client, calls = _four_lane_sam_gov_client(tmp_path)
    profile = _create_four_lane_sam_gov_profile(client)
    call_count = len(calls)

    response = client.get(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/command-surface"
    )

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["profile_id"] == profile["id"]
    assert summary["live_ready"] is False
    assert summary["source_mode_labels"] == ["fake adapter test"]
    assert {lane["lane_name"] for lane in summary["lane_states"]} == {
        "Entity Record lane",
        "Known Opportunity lane",
        "Opportunity Discovery lane",
        "Attachment Intake lane",
    }
    assert summary["review_summary"]["trusted_output_written_count"] == 0
    assert set(summary["review_summary"]["target_workflows"]) >= {
        "evidence_store",
        "living_briefing_packet",
        "capture_action_plan",
        "risk_register",
        "call_plan",
        "document_intake",
        "web_enrichment_support",
    }
    assert summary["linked_document_intake_record_ids"] == [
        profile["attachment_intake_lane"]["attachments"][0]["intake_record_id"]
    ]
    assert (
        "Provider-backed Web Enrichment Support implementation deferred."
        in (summary["explicit_deferrals"])
    )
    assert len(calls) == call_count


def test_sam_gov_profile_command_surface_page_shows_four_lane_workflow(
    tmp_path,
) -> None:
    client, calls = _four_lane_sam_gov_client(tmp_path)
    profile = _create_four_lane_sam_gov_profile(client)
    call_count = len(calls)

    home_response = client.get("/")
    response = client.get(f"/federal-data/sam-gov/enrichment-profiles/{profile['id']}")

    assert home_response.status_code == 200
    assert f"/federal-data/sam-gov/enrichment-profiles/{profile['id']}" in (
        home_response.text
    )
    assert response.status_code == 200
    assert "SAM.gov Enrichment Profile Command Surface" in response.text
    assert "Entity Record lane" in response.text
    assert "Known Opportunity lane" in response.text
    assert "Opportunity Discovery lane" in response.text
    assert "Attachment Intake lane" in response.text
    assert "ACME FEDERAL LLC" in response.text
    assert "Project Phoenix final RFP" in response.text
    assert "Project Phoenix Sources Sought" in response.text
    assert "Project Phoenix notes" in response.text
    assert "Document Intake record" in response.text
    assert "fake adapter test" in response.text
    assert "Fake adapter test data is not live SAM.gov source success." in response.text
    assert "Evidence Store" in response.text
    assert "Living Briefing Packet" in response.text
    assert "Capture Action Plan" in response.text
    assert "Risk Register" in response.text
    assert "Call Plan" in response.text
    assert "Follow-up Route" in response.text
    assert "Trusted writes: none" in response.text
    assert "Provider-backed Web Enrichment Support deferred" in response.text
    assert "Specialized Solicitation Parser deferred" in response.text
    assert "Project Theseus parser integration deferred" in response.text
    assert "Artifact export deferred" in response.text
    assert "Hermes/LangGraph deferred" in response.text
    assert "Additional federal data sources deferred" in response.text
    assert len(calls) == call_count


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


def test_command_center_shell_shows_compact_knowledge_context_panel() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert "Knowledge Context" in response.text
    assert "Context health" in response.text
    assert "Trusted Context" in response.text
    assert "Reviewable Context" in response.text
    assert "Top gaps and limitations" in response.text
    assert "Pending recommendations" in response.text
    assert "Recommend Next Capture Actions" in response.text
    assert (
        "/knowledge-context/opportunities/opp-aflcmc-recompete/"
        "recommend-next-capture-actions"
    ) in response.text
    assert "Review packet gap" in response.text
    assert "Supporting refs and provenance" in response.text


def test_knowledge_context_panel_generates_and_accepts_recommendation(
    tmp_path,
) -> None:
    recommendation_root = tmp_path / "recommendations"
    evidence_root = tmp_path / "evidence"
    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_NEXT_ACTION_RECOMMENDATIONS_DIR": str(recommendation_root),
            "ARIADNE_EVIDENCE_DIR": str(evidence_root),
        }
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    generate_response = client.post(
        "/knowledge-context/opportunities/opp-aflcmc-recompete/"
        "recommend-next-capture-actions"
    )
    store = NextActionRecommendationStore(recommendation_root)
    recommendations = store.list(opportunity_id="opp-aflcmc-recompete")
    recommendation = recommendations[0]
    pending_shell = client.get("/")

    accept_response = client.post(
        f"/knowledge-context/recommendations/{recommendation.id}/accept"
    )
    accepted = store.read(recommendation.id)
    accepted_shell = client.get("/")

    assert generate_response.status_code == 200
    assert recommendation.review_state is NextActionRecommendationReviewState.PENDING
    assert recommendation.title in pending_shell.text
    assert "Accept to Action Plan" in pending_shell.text
    assert accept_response.status_code == 200
    assert accepted.review_state is NextActionRecommendationReviewState.ACCEPTED
    assert accepted.created_action_plan_item_ids
    assert accepted.review_decisions[0].reviewer_rationale == (
        "Accepted from Knowledge Context Panel."
    )
    assert "State: accepted" in accepted_shell.text
    assert recommendation.title in accepted_shell.text
    assert LocalEvidenceStore(evidence_root).list() == []


def test_knowledge_context_panel_shows_stale_and_discarded_recommendation_detail(
    tmp_path,
) -> None:
    recommendation_root = tmp_path / "recommendations"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_NEXT_ACTION_RECOMMENDATIONS_DIR": str(recommendation_root)}
    )

    from fastapi.testclient import TestClient

    client = TestClient(create_app(settings))
    client.post(
        "/knowledge-context/opportunities/opp-aflcmc-recompete/"
        "recommend-next-capture-actions"
    )
    store = NextActionRecommendationStore(recommendation_root)
    recommendation = store.list(opportunity_id="opp-aflcmc-recompete")[0]
    refresh_result = refresh_stale_next_action_recommendation(
        store=store,
        recommendation_id=recommendation.id,
        stale_reason="Packet field gained new evidence.",
        title="Resolve refreshed packet gap: primary_scope",
        description="Re-check transition scope after new evidence.",
        generated_at="2026-05-18T17:00:00Z",
    )
    discard_next_action_recommendation(
        store=store,
        recommendation_id=refresh_result.refreshed_recommendation.id,
        reviewer_rationale="Not the right next action after review.",
        decided_at="2026-05-18T17:05:00Z",
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Stale snapshot: Packet field gained new evidence." in response.text
    assert "Refresh needed" in response.text
    assert "Rejected/discarded recommendation history" in response.text
    assert "State: discarded" in response.text
    assert "Not the right next action after review." in response.text


def test_runtime_settings_expose_next_action_recommendation_store_path(
    tmp_path,
) -> None:
    recommendation_root = tmp_path / "recommendations"

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_NEXT_ACTION_RECOMMENDATIONS_DIR": str(recommendation_root)}
    )

    assert settings.ariadne_next_action_recommendations_dir == recommendation_root


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


def _four_lane_sam_gov_client(tmp_path):
    from fastapi.testclient import TestClient

    settings = RuntimeSettings.from_mapping(
        {
            "ARIADNE_SAM_GOV_PROFILES_DIR": str(tmp_path / "sam-gov-profiles"),
            "ARIADNE_DOCUMENT_INTAKE_DIR": str(tmp_path / "document-intake"),
        }
    )
    calls = []

    def entity_runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "entityRegistration": {
                    "uei": "UEIACME12345",
                    "legalBusinessName": "ACME FEDERAL LLC",
                    "physicalAddress": {
                        "city": "Dayton",
                        "stateOrProvinceCode": "OH",
                    },
                },
                "entityHierarchy": {
                    "immediateParent": {
                        "parentUei": "PARENTUEI1234",
                        "parentLegalBusinessName": "ACME HOLDINGS LLC",
                    }
                },
                "coreData": {
                    "businessTypes": [{"businessTypeDesc": "Veteran Owned Business"}]
                },
            },
        )

    def opportunity_runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        if arguments.get("solicitation_number"):
            return SamGovMcpToolResult(
                ok=True,
                payload={
                    "opportunitiesData": [
                        {
                            "noticeId": "notice-known-001",
                            "solicitationNumber": "FA8650-26-R-0001",
                            "title": "Project Phoenix final RFP",
                            "type": "Solicitation",
                            "fullParentPathName": (
                                "Department of the Air Force.AFLCMC/PZ"
                            ),
                            "resourceLinks": [
                                {
                                    "title": "Project Phoenix notes",
                                    "filename": "project-phoenix-notes.txt",
                                    "url": "https://sam.gov/api/prod/opps/v3/opportunities/resources/files/project-phoenix-notes.txt?api_key=null&token=",
                                }
                            ],
                        }
                    ]
                },
            )
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "opportunitiesData": [
                    {
                        "noticeId": "notice-discovery-001",
                        "solicitationNumber": "FA8650-26-RFI-PHOENIX",
                        "title": "Project Phoenix Sources Sought",
                        "type": "Sources Sought",
                        "fullParentPathName": "Department of the Air Force.AFLCMC/PZ",
                    }
                ]
            },
        )

    def attachment_fetcher(url):
        calls.append(("fetch_attachment", {"url": url}))
        return SamGovAttachmentFetchResult(
            ok=True,
            filename="project-phoenix-notes.txt",
            mime_type="text/plain",
            content=b"Project Phoenix notes for capture review.",
        )

    return (
        TestClient(
            create_app(
                settings,
                sam_gov_entity_runner=entity_runner,
                sam_gov_opportunity_runner=opportunity_runner,
                sam_gov_attachment_fetcher=attachment_fetcher,
                sam_gov_source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
            )
        ),
        calls,
    )


def _create_four_lane_sam_gov_profile(client):
    profile = client.post(
        "/api/federal-data/sam-gov/enrichment-profiles",
        json={"input_pivot": "UEIACME12345"},
    ).json()["profile"]
    profile = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/known-opportunity",
        json={
            "input_pivot": "FA8650-26-R-0001",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    ).json()["profile"]
    profile = client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/opportunity-discovery",
        json={
            "customer_agency": "Department of the Air Force",
            "office": "AFLCMC/PZ",
            "program_name": "Project Phoenix",
            "notice_type": "sources_sought",
            "posted_from": "05/01/2026",
            "posted_to": "05/31/2026",
        },
    ).json()["profile"]
    attachment_id = profile["attachment_intake_lane"]["attachments"][0]["id"]
    return client.post(
        f"/api/federal-data/sam-gov/enrichment-profiles/{profile['id']}/attachments/{attachment_id}/approve-download",
        json={
            "reviewer_rationale": "Official SAM.gov attachment is approved for review."
        },
    ).json()["profile"]
