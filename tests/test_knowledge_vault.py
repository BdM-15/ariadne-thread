from ariadne.knowledge_vault import (
    ensure_knowledge_vault_scaffold,
    validate_knowledge_vault_pages,
)


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
        "opportunity_projection",
        "mirror_update_proposal",
        "hermes_learning_proposal",
    }
    assert {relationship_type["id"] for relationship_type in body["relationship_types"]} == {
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