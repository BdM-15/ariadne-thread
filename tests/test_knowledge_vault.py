from ariadne.knowledge_vault import (
    ensure_knowledge_vault_scaffold,
    ensure_packet_data_element_pages,
    ensure_reference_data_dictionary_pages,
    generate_knowledge_vault_health_report,
    validate_knowledge_vault_pages,
)
from ariadne.opportunities import MilestoneGate
from ariadne.packet_knowledge import build_default_packet_field_definitions
from ariadne.project_ariadne_migration import migrate_project_ariadne_slice


def test_knowledge_vault_scaffold_creates_required_wiki_shape(tmp_path) -> None:
    vault_root = tmp_path / "knowledge" / "ariadnes-thread"

    status = ensure_knowledge_vault_scaffold(vault_root)

    assert status.ready is True
    assert status.vault_root == str(vault_root)
    assert status.missing_required_paths == ()
    assert "Ariadne Thread Knowledge Vault" in (vault_root / "index.md").read_text(
        encoding="utf-8"
    )
    assert "## [" in (vault_root / "log.md").read_text(encoding="utf-8")
    assert "Ariadne wiki maintainer" in (vault_root / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    assert "typed relationships" in (
        vault_root / "foundation" / "ariadne-wiki-schema.md"
    ).read_text(encoding="utf-8")
    schema_text = (vault_root / "foundation" / "ariadne-wiki-schema.md").read_text(
        encoding="utf-8"
    )
    assert "Project Theseus" in schema_text
    assert "complementary capability context" in schema_text
    assert "page_type: global_data_element" in schema_text
    assert "relationships: [suggests_route:workflow/capture-research]" in schema_text

    for folder in (
        "inbox",
        "foundation",
        "data-elements",
        "entities",
        "relationships",
        "sources",
        "opportunities",
        "workflows",
        "skills-capabilities",
        "reusable-insights",
        "artifact-patterns",
        "capture-concepts",
        "milestones",
        "proposals",
        "generated-projections",
        "reports",
        "hermes-learning",
    ):
        assert (vault_root / folder).is_dir()


def test_knowledge_vault_scaffold_preserves_existing_user_authored_files(
    tmp_path,
) -> None:
    vault_root = tmp_path / "knowledge" / "ariadnes-thread"
    vault_root.mkdir(parents=True)
    (vault_root / "index.md").write_text("# My Existing Index\n", encoding="utf-8")
    (vault_root / "log.md").write_text("# My Existing Log\n", encoding="utf-8")

    status = ensure_knowledge_vault_scaffold(vault_root)

    assert status.ready is True
    assert (vault_root / "index.md").read_text(encoding="utf-8") == (
        "# My Existing Index\n"
    )
    assert (vault_root / "log.md").read_text(encoding="utf-8") == (
        "# My Existing Log\n"
    )
    assert (vault_root / "foundation" / "ariadne-wiki-schema.md").exists()


def test_knowledge_vault_api_reports_readiness_and_can_create_scaffold(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    from ariadne.config import RuntimeSettings
    from ariadne.server import create_app

    vault_root = tmp_path / "knowledge" / "ariadnes-thread"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_OBSIDIAN_VAULT_DIR": str(vault_root)}
    )
    client = TestClient(create_app(settings))

    initial_response = client.get("/api/knowledge-vault/readiness")

    assert initial_response.status_code == 200
    initial_body = initial_response.json()
    assert initial_body["vault_root"] == str(vault_root)
    assert initial_body["ready"] is False
    assert "index.md" in initial_body["missing_required_paths"]

    scaffold_response = client.post("/api/knowledge-vault/scaffold")

    assert scaffold_response.status_code == 200
    scaffold_body = scaffold_response.json()
    assert scaffold_body["ready"] is True
    assert scaffold_body["missing_required_paths"] == []

    ready_response = client.get("/api/knowledge-vault/readiness")
    assert ready_response.json()["ready"] is True


def test_knowledge_vault_api_exposes_page_types_and_relationship_vocabulary(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    from ariadne.config import RuntimeSettings
    from ariadne.server import create_app

    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_OBSIDIAN_VAULT_DIR": str(tmp_path / "vault")}
    )
    response = TestClient(create_app(settings)).get("/api/knowledge-vault/schema")

    assert response.status_code == 200
    body = response.json()
    assert {page_type["id"] for page_type in body["page_types"]} == {
        "global_data_element",
        "capture_concept",
        "source_summary",
        "entity",
        "relationship",
        "workflow_capability",
        "reusable_insight_candidate",
        "artifact_pattern",
        "source_manifest",
        "opportunity_projection",
        "mirror_update_proposal",
        "hermes_learning_proposal",
    }
    assert {
        relationship_type["id"] for relationship_type in body["relationship_types"]
    } == {
        "supports",
        "answers",
        "informs",
        "blocks",
        "contradicts",
        "derived_from",
        "evidence_for",
        "fills_gap_in",
        "suggests_route",
        "uses_capability",
        "applies_to_gate",
        "produces_artifact_block",
        "candidate_reusable_insight",
        "expects_data_element",
        "maps_to_artifact_block",
        "uses_source",
    }


def test_knowledge_vault_validation_reports_page_and_relationship_errors(
    tmp_path,
) -> None:
    vault_root = tmp_path / "vault"
    ensure_knowledge_vault_scaffold(vault_root)
    (vault_root / "data-elements" / "customer-insight.md").write_text(
        """---
page_type: global_data_element
title: Customer Insight
source_refs: [packet-field:customer_insight]
relationships: [applies_to_gate:milestone-1, suggests_route:workflow/capture-research]
---

# Customer Insight
""",
        encoding="utf-8",
    )
    (vault_root / "relationships" / "bad-link.md").write_text(
        """---
page_type: mystery_page
title: Bad Link
relationships: [teleports_to:somewhere]
---

# Bad Link
""",
        encoding="utf-8",
    )

    report = validate_knowledge_vault_pages(vault_root)

    assert report.valid is False
    assert {issue.code for issue in report.issues} == {
        "unknown_page_type",
        "missing_source_refs",
        "unknown_relationship_type",
    }
    assert all("customer-insight.md" not in issue.path for issue in report.issues)


def test_packet_data_element_page_tracer_creates_current_gate_page_from_definition(
    tmp_path,
) -> None:
    vault_root = tmp_path / "vault"
    definitions = build_default_packet_field_definitions()

    report = ensure_packet_data_element_pages(
        vault_root,
        definitions,
        current_milestone_gate=MilestoneGate.MILESTONE_1,
    )

    customer_page = vault_root / "data-elements" / "briefing-packet" / "customer.md"
    customer_text = customer_page.read_text(encoding="utf-8")
    customer_status = next(
        page for page in report.pages if page.field_key == "customer"
    )

    assert customer_status.exists is True
    assert customer_status.connected is True
    assert customer_status.path == "data-elements/briefing-packet/customer.md"
    assert "page_type: global_data_element" in customer_text
    assert "title: Customer" in customer_text
    assert "source_refs: [packet-field-definition:customer]" in customer_text
    assert "dictionary_id: briefing_packet" in customer_text
    assert "applies_to_gate:milestone_1" in customer_text
    assert "derived_from:packet-field-definitions/briefing-packet" in customer_text
    assert "suggests_route:workflow/opportunity-activation" in customer_text
    assert "suggests_route:workflow/packet-field-action-matrix" in customer_text
    assert (
        "maps_to_artifact_block:artifact-block/living-briefing-packet" in customer_text
    )
    assert "Which customer or buying command owns the need?" in customer_text
    assert "notice or call-note extraction" in customer_text
    assert "Evidence Standards" in customer_text
    assert "Common Source Types" in customer_text
    assert "Packet Field Answers live in Ariadne structured stores" in customer_text

    index_text = (vault_root / "data-elements" / "dictionary-index.md").read_text(
        encoding="utf-8"
    )
    assert "Briefing Packet Data Dictionary" in index_text
    assert "data-elements/briefing-packet/customer" in index_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_packet_data_element_api_reports_missing_and_connected_pages(
    tmp_path,
) -> None:
    from fastapi.testclient import TestClient

    from ariadne.config import RuntimeSettings
    from ariadne.server import create_app

    vault_root = tmp_path / "vault"
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_OBSIDIAN_VAULT_DIR": str(vault_root)}
    )
    client = TestClient(create_app(settings))

    missing_response = client.get(
        "/api/knowledge-vault/packet-data-elements",
        params={"current_milestone_gate": "milestone_1"},
    )

    assert missing_response.status_code == 200
    missing_body = missing_response.json()
    assert missing_body["current_milestone_gate"] == "milestone_1"
    assert missing_body["missing_count"] > 0
    assert any(page["field_key"] == "customer" for page in missing_body["pages"])

    scaffold_response = client.post(
        "/api/knowledge-vault/packet-data-elements/scaffold",
        params={"current_milestone_gate": "milestone_1"},
    )

    assert scaffold_response.status_code == 200
    scaffold_body = scaffold_response.json()
    assert scaffold_body["created_count"] > 0
    assert scaffold_body["missing_count"] == 0
    assert scaffold_body["unconnected_count"] == 0
    assert all(page["connected"] for page in scaffold_body["pages"])


def test_reference_data_dictionary_pages_group_fields_by_workflow_dictionary(
    tmp_path,
) -> None:
    vault_root = tmp_path / "vault"
    reference_root = tmp_path / "docs" / "reference"
    risk_dictionary = (
        reference_root / "risk_register" / "RISK_REGISTER_DATA_DICTIONARY.md"
    )
    call_dictionary = reference_root / "call_plan" / "CALL_PLAN_DATA_DICTIONARY.md"
    risk_dictionary.parent.mkdir(parents=True)
    call_dictionary.parent.mkdir(parents=True)
    risk_dictionary.write_text(
        """# Risk Register Data Dictionary Draft

| Field key | Workbook concept | Kind | Likely source | Connected packet fields |
| --------- | ---------------- | ---- | ------------- | ----------------------- |
| `risk_short_title` | Risk Short Title | scalar/prose | human input | risk summary |
| `risk_response` | Risk Response | prose | model draft | action plan |
""",
        encoding="utf-8",
    )
    call_dictionary.write_text(
        """# Call Plan Data Dictionary Draft

| Field key | Template concept | Kind | Likely source | Connected packet fields |
| --------- | ---------------- | ---- | ------------- | ----------------------- |
| `meeting_purpose` | Purpose of customer meeting | prose | human input | `opportunity_context` |
| `customer_hot_buttons` | Hot Buttons | prose/list | notes | `customer_need_funding_status` |
""",
        encoding="utf-8",
    )

    report = ensure_reference_data_dictionary_pages(vault_root, reference_root)

    assert report.created_count == 5
    assert report.field_count == 4
    assert {page.path for page in report.pages} == {
        "data-elements/risk-register/risk_short_title.md",
        "data-elements/risk-register/risk_response.md",
        "data-elements/call-plan/meeting_purpose.md",
        "data-elements/call-plan/customer_hot_buttons.md",
        "data-elements/dictionary-index.md",
    }

    risk_text = (
        vault_root / "data-elements" / "risk-register" / "risk_response.md"
    ).read_text(encoding="utf-8")
    call_text = (
        vault_root / "data-elements" / "call-plan" / "customer_hot_buttons.md"
    ).read_text(encoding="utf-8")
    index_text = (vault_root / "data-elements" / "dictionary-index.md").read_text(
        encoding="utf-8"
    )

    assert "page_type: global_data_element" in risk_text
    assert "source_refs: [reference-data-dictionary:risk_register]" in risk_text
    assert "suggests_route:workflow/risk-register" in risk_text
    assert "maps_to_artifact_block:artifact-block/risk-register" in risk_text
    assert "action plan" in risk_text

    assert "source_refs: [reference-data-dictionary:call_plan]" in call_text
    assert "suggests_route:workflow/call-plan" in call_text
    assert "maps_to_artifact_block:artifact-block/call-plan" in call_text
    assert "customer_need_funding_status" in call_text

    assert "Risk Register Data Dictionary" in index_text
    assert "Call Plan Data Dictionary" in index_text
    assert "data-elements/risk-register/risk_response" in index_text
    assert "data-elements/call-plan/customer_hot_buttons" in index_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_dictionary_index_combines_packet_and_reference_dictionaries(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    reference_root = tmp_path / "docs" / "reference"
    risk_dictionary = (
        reference_root / "risk_register" / "RISK_REGISTER_DATA_DICTIONARY.md"
    )
    call_dictionary = reference_root / "call_plan" / "CALL_PLAN_DATA_DICTIONARY.md"
    risk_dictionary.parent.mkdir(parents=True)
    call_dictionary.parent.mkdir(parents=True)
    risk_dictionary.write_text(
        """# Risk Register Data Dictionary Draft

| Field key | Workbook concept | Kind | Likely source | Connected packet fields |
| --------- | ---------------- | ---- | ------------- | ----------------------- |
| `risk_short_title` | Risk Short Title | scalar/prose | human input | risk summary |
""",
        encoding="utf-8",
    )
    call_dictionary.write_text(
        """# Call Plan Data Dictionary Draft

| Field key | Template concept | Kind | Likely source | Connected packet fields |
| --------- | ---------------- | ---- | ------------- | ----------------------- |
| `meeting_purpose` | Purpose of customer meeting | prose | human input | `opportunity_context` |
""",
        encoding="utf-8",
    )

    ensure_packet_data_element_pages(
        vault_root,
        build_default_packet_field_definitions(),
    )
    ensure_reference_data_dictionary_pages(vault_root, reference_root)

    index_text = (vault_root / "data-elements" / "dictionary-index.md").read_text(
        encoding="utf-8"
    )

    assert "Briefing Packet Data Dictionary" in index_text
    assert "Risk Register Data Dictionary" in index_text
    assert "Call Plan Data Dictionary" in index_text
    assert "data-elements/briefing-packet/customer" in index_text
    assert "data-elements/risk-register/risk_short_title" in index_text
    assert "data-elements/call-plan/meeting_purpose" in index_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_knowledge_vault_health_report_passes_connected_fixture(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    corpus_root = tmp_path / "project-ariadne" / "knowledge"
    source_path = "global_wiki/capture/customer-hot-button-identification.md"
    pending_path = "global_wiki/capture/bid-no-bid-decision-framework.md"
    (corpus_root / source_path).parent.mkdir(parents=True)
    (corpus_root / source_path).write_text(
        """---
title: Customer Hot Button Identification
entity_type: customer_priority
---

Hot buttons drive customer evaluation decisions.
""",
        encoding="utf-8",
    )
    (corpus_root / pending_path).write_text(
        """---
title: Bid No-Bid Decision Framework
---

Qualification discipline.
""",
        encoding="utf-8",
    )
    ensure_packet_data_element_pages(
        vault_root,
        build_default_packet_field_definitions(),
        current_milestone_gate=MilestoneGate.MILESTONE_1,
    )
    migrate_project_ariadne_slice(
        corpus_root,
        vault_root,
        source_relative_paths=(source_path,),
    )

    report = generate_knowledge_vault_health_report(vault_root)
    report_text = (vault_root / report.report_path).read_text(encoding="utf-8")

    assert report.healthy is True
    assert report.issue_count == 0
    assert report.migration_coverage.incorporated_count == 1
    assert report.migration_coverage.pending_count == 1
    assert report.migration_coverage.skipped_count == 0
    assert "old corpus remains temporary" in report_text
    assert "orphan_pages: 0" in report_text
    assert "weakly_sourced_pages: 0" in report_text
    assert "missing_source_refs: 0" in report_text
    assert "unconnected_data_elements: 0" in report_text


def test_knowledge_vault_health_report_flags_unhealthy_fixture(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    ensure_knowledge_vault_scaffold(vault_root)
    (vault_root / "capture-concepts" / "orphan.md").parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    (vault_root / "capture-concepts" / "orphan.md").write_text(
        """---
page_type: capture_concept
title: Orphan Concept
source_refs: [project-ariadne:orphan]
relationships: []
---

# Orphan Concept
""",
        encoding="utf-8",
    )
    (vault_root / "source-summaries").mkdir(parents=True)
    (vault_root / "source-summaries" / "weak-source.md").write_text(
        """---
page_type: source_summary
title: Weak Source
source_refs: [manual:unknown]
relationships: [informs:data-elements/briefing-packet/customer]
---

# Weak Source
""",
        encoding="utf-8",
    )
    (vault_root / "source-summaries" / "missing-source.md").write_text(
        """---
page_type: source_summary
title: Missing Source
relationships: [informs:data-elements/briefing-packet/customer]
---

# Missing Source
""",
        encoding="utf-8",
    )
    (vault_root / "data-elements" / "customer.md").write_text(
        """---
page_type: global_data_element
title: Customer
source_refs: [packet-field-definition:customer]
relationships: []
---

# Customer
""",
        encoding="utf-8",
    )
    (vault_root / "relationships" / "weak-provenance.md").write_text(
        """---
page_type: relationship
title: Weak Relationship Provenance
source_refs: [manual:unknown]
relationships: [supports:data-elements/briefing-packet/customer]
---

# Weak Relationship Provenance
""",
        encoding="utf-8",
    )

    report = generate_knowledge_vault_health_report(vault_root)

    assert report.healthy is False
    assert {issue.code for issue in report.issues} >= {
        "orphan_page",
        "weak_source_refs",
        "missing_source_refs",
        "unconnected_data_element",
        "weak_relationship_provenance",
    }
    assert report.orphan_pages_count >= 1
    assert report.weakly_sourced_pages_count >= 1
    assert report.missing_source_refs_count >= 1
    assert report.unconnected_data_elements_count >= 1
    assert report.weak_relationship_provenance_count >= 1


def test_knowledge_vault_health_report_api_writes_report(tmp_path) -> None:
    from fastapi.testclient import TestClient

    from ariadne.config import RuntimeSettings
    from ariadne.server import create_app

    vault_root = tmp_path / "vault"
    ensure_knowledge_vault_scaffold(vault_root)
    (vault_root / "source-summaries").mkdir(parents=True)
    (vault_root / "source-summaries" / "missing-source.md").write_text(
        """---
page_type: source_summary
title: Missing Source
relationships: [informs:data-elements/briefing-packet/customer]
---

# Missing Source
""",
        encoding="utf-8",
    )
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_OBSIDIAN_VAULT_DIR": str(vault_root)}
    )

    response = TestClient(create_app(settings)).post(
        "/api/knowledge-vault/health-report"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["healthy"] is False
    assert body["missing_source_refs_count"] == 1
    assert (vault_root / body["report_path"]).exists()
