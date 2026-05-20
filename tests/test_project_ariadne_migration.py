from pathlib import Path

from ariadne.knowledge_vault import validate_knowledge_vault_pages
from ariadne.project_ariadne_migration import migrate_project_ariadne_slice


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_project_ariadne_migration_tracer_writes_native_vault_page_and_coverage(
    tmp_path,
) -> None:
    corpus_root = tmp_path / "project-ariadne" / "knowledge"
    vault_root = tmp_path / "vault"
    source_path = "global_wiki/capture/customer-hot-button-identification.md"
    pending_path = "global_wiki/capture/bid-no-bid-decision-framework.md"

    _write(
        corpus_root / source_path,
        """---
auto_generated: true
entity_type: customer_priority
source_module: capture
title: Customer Hot Button Identification
updated: '2026-04-22T23:01:16'
---

> **Entity type:** `customer_priority`

Hot buttons are customer's highest-priority concerns driving evaluation decisions.
Validate hot button assumptions through customer engagement.
""",
    )
    _write(
        corpus_root / pending_path,
        """---
title: Bid No-Bid Decision Framework
entity_type: concept
---

Structured decision process for opportunity qualification.
""",
    )

    report = migrate_project_ariadne_slice(
        corpus_root,
        vault_root,
        source_relative_paths=(source_path, "global_wiki/capture/missing.md"),
    )

    migrated_page = vault_root / "source-summaries" / "project-ariadne" / "customer-hot-button-identification.md"
    migrated_text = migrated_page.read_text(encoding="utf-8")
    coverage_text = (vault_root / report.coverage_report_path).read_text(
        encoding="utf-8"
    )

    assert report.incorporated_count == 1
    assert report.skipped_count == 1
    assert report.pending_count == 1
    assert report.incorporated[0].source_path == source_path
    assert report.skipped[0].source_path == "global_wiki/capture/missing.md"
    assert report.pending[0].source_path == pending_path

    assert "page_type: source_summary" in migrated_text
    assert "title: Customer Hot Button Identification" in migrated_text
    assert (
        "source_refs: [project-ariadne:global_wiki/capture/customer-hot-button-identification.md]"
        in migrated_text
    )
    assert "migration_status: incorporated" in migrated_text
    assert "derived_from:project-ariadne/global_wiki/capture/customer-hot-button-identification.md" in migrated_text
    assert "informs:data-elements/customer" in migrated_text
    assert "candidate_reusable_insight:reusable-insights/customer-hot-button-identification" in migrated_text
    assert "Hot buttons are customer's highest-priority concerns" in migrated_text
    assert "## Migration Status" in migrated_text
    assert "## Source Summary" in migrated_text
    assert "## Relationship Links" in migrated_text
    assert "## Reusable Insight Candidate Status" in migrated_text
    assert "not opportunity-specific Evidence" in migrated_text

    assert "incorporated: 1" in coverage_text
    assert "skipped: 1" in coverage_text
    assert "pending: 1" in coverage_text
    assert source_path in coverage_text
    assert pending_path in coverage_text
    assert "global_wiki/capture/missing.md" in coverage_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True
