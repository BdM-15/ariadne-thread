from ariadne.capability_relationship_pages import (
    ensure_capability_relationship_pages,
    inspect_capability_relationship_pages,
)
from ariadne.knowledge_vault import validate_knowledge_vault_pages


def _write_skill(workspace_root):
    skill_path = workspace_root / ".github" / "skills" / "cli-anything" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text(
        """---
name: CLI Anything
summary: Build agent-native CLI harnesses.
description: Repeatable Ariadne capability harness builder.
capability_type: cli_harness
maturity: stable
validation_status: tested
product_workflow_fit: capability_studio,capture_research
---

# CLI Anything
""",
        encoding="utf-8",
    )


def test_capability_relationship_pages_cover_skill_capability_source_workflow_and_hermes(
    tmp_path,
) -> None:
    vault_root = tmp_path / "vault"
    workspace_root = tmp_path / "workspace"
    _write_skill(workspace_root)

    report = ensure_capability_relationship_pages(
        vault_root,
        workspace_root=workspace_root,
        env={"CRAWL4AI_BASE_URL": "http://localhost:11235"},
    )

    assert report.created_count == 5
    assert report.unconnected_count == 0
    assert report.weakly_sourced_count == 0
    assert {page.category for page in report.pages} == {
        "installed_skill",
        "capability_module",
        "source_provider",
        "product_workflow",
        "hermes_learning_role",
    }
    assert report.pages[0].connected is True

    skill_page = vault_root / "skills-capabilities" / "skill-cli-anything.md"
    capability_page = vault_root / "skills-capabilities" / "capability-document-intake.md"
    source_page = vault_root / "skills-capabilities" / "source-provider-crawl4ai-local.md"
    workflow_page = vault_root / "workflows" / "capture-research.md"
    hermes_page = vault_root / "hermes-learning" / "vault-maintainer-proposal-role.md"

    for page in (skill_page, capability_page, source_page, workflow_page, hermes_page):
        text = page.read_text(encoding="utf-8")
        assert "Maturity Or Readiness" in text
        assert "Likely Inputs" in text
        assert "Output And Review Destinations" in text
        assert "Route Fit" in text
        assert "Provenance Expectations" in text

    capability_text = capability_page.read_text(encoding="utf-8")
    assert "page_type: workflow_capability" in capability_text
    assert "uses_capability:capability/document-intake" in capability_text
    assert "produces_artifact_block:artifact-block/source-appendix" in capability_text
    assert "informs:data-elements/primary_scope" in capability_text

    source_text = source_page.read_text(encoding="utf-8")
    assert "source_refs: [source-provider-manifest:crawl4ai_local]" in source_text
    assert "readiness: available" in source_text
    assert "suggests_route:workflow/capture-research" in source_text

    workflow_text = workflow_page.read_text(encoding="utf-8")
    assert "uses_capability:capability/document-intake" in workflow_text
    assert "suggests_route:workflow/packet-field-action-matrix" in workflow_text
    assert "candidate_reusable_insight:reusable-insights/capture-research-routing" in workflow_text

    hermes_text = hermes_page.read_text(encoding="utf-8")
    assert "page_type: hermes_learning_proposal" in hermes_text
    assert "broad Hermes runtime behavior remains deferred" in hermes_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_capability_relationship_status_flags_weak_or_unconnected_pages(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    weak_page = vault_root / "skills-capabilities" / "weak-capability.md"
    weak_page.parent.mkdir(parents=True)
    weak_page.write_text(
        """---
page_type: workflow_capability
title: Weak Capability
source_refs: [manual:unknown]
relationships: []
category: capability_module
readiness: unknown
---

# Weak Capability
""",
        encoding="utf-8",
    )

    report = inspect_capability_relationship_pages(vault_root)

    assert report.unconnected_count == 1
    assert report.weakly_sourced_count == 1
    assert report.pages[0].connected is False
    assert report.pages[0].weakly_sourced is True


def test_capability_relationship_api_reports_and_creates_pages(tmp_path) -> None:
    from fastapi.testclient import TestClient

    from ariadne.config import RuntimeSettings
    from ariadne.server import create_app

    workspace_root = tmp_path / "workspace"
    vault_root = tmp_path / "vault"
    _write_skill(workspace_root)
    client = TestClient(
        create_app(
            RuntimeSettings.from_mapping(
                {"ARIADNE_OBSIDIAN_VAULT_DIR": str(vault_root)}
            ),
            workspace_root=workspace_root,
        )
    )

    missing_response = client.get("/api/knowledge-vault/capability-relationships")
    scaffold_response = client.post("/api/knowledge-vault/capability-relationships")

    assert missing_response.status_code == 200
    assert missing_response.json()["page_count"] == 0
    assert scaffold_response.status_code == 200
    body = scaffold_response.json()
    assert body["created_count"] == 5
    assert body["page_count"] == 5
    assert body["unconnected_count"] == 0
