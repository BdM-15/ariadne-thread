from pathlib import Path

from ariadne.knowledge_vault import validate_knowledge_vault_pages
from ariadne.project_ariadne_migration import (
    migrate_project_ariadne_corpus,
    migrate_project_ariadne_slice,
)


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

    migrated_page = (
        vault_root
        / "source-summaries"
        / "project-ariadne"
        / "global_wiki"
        / "capture"
        / "customer-hot-button-identification.md"
    )
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
    assert (
        "derived_from:project-ariadne/global_wiki/capture/customer-hot-button-identification.md"
        in migrated_text
    )
    assert "informs:data-elements/customer" in migrated_text
    assert (
        "candidate_reusable_insight:reusable-insights/customer-hot-button-identification"
        in migrated_text
    )
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


def test_project_ariadne_full_corpus_migration_preserves_paths_and_covers_all_md(
    tmp_path,
) -> None:
    corpus_root = tmp_path / "project-ariadne" / "knowledge"
    vault_root = tmp_path / "vault"
    source_paths = (
        "global_wiki/capture/customer-hot-button-identification.md",
        "global_wiki/shipley/win-theme-development.md",
        "domain_intel/milestones/ms1-qualification.md",
        "domain_intel/capabilities/kbr-inc.md",
        "pursuits/_template/01_capture/customer/profile.md",
        "pursuits/_template/01_capture/strategy/risk_register.md",
    )
    for source_path in source_paths:
        _write(
            corpus_root / source_path,
            f"""---
title: {Path(source_path).stem.replace("_", " ").replace("-", " ").title()}
entity_type: concept
updated: '2026-04-22T23:01:16'
---

Customer hot buttons, milestones, risk, and artifact fields for {source_path}.
""",
        )

    report = migrate_project_ariadne_corpus(corpus_root, vault_root)

    assert report.incorporated_count == len(source_paths)
    assert report.skipped_count == 0
    assert report.pending_count == 0
    assert {item.target_path for item in report.incorporated} == {
        f"source-summaries/project-ariadne/{source_path}"
        for source_path in source_paths
    }
    assert (
        vault_root
        / "source-summaries"
        / "project-ariadne"
        / "global_wiki"
        / "capture"
        / "customer-hot-button-identification.md"
    ).exists()
    assert (
        vault_root
        / "source-summaries"
        / "project-ariadne"
        / "pursuits"
        / "_template"
        / "01_capture"
        / "customer"
        / "profile.md"
    ).exists()

    coverage_text = (vault_root / report.coverage_report_path).read_text(
        encoding="utf-8"
    )
    assert "pending: 0" in coverage_text
    assert "old corpus retained until maintainer retirement approval" in coverage_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_project_ariadne_template_pages_create_artifact_expectations(tmp_path) -> None:
    corpus_root = tmp_path / "project-ariadne" / "knowledge"
    vault_root = tmp_path / "vault"
    source_path = "pursuits/_template/01_capture/customer/profile.md"
    _write(
        corpus_root / source_path,
        """# Customer Profile

Customer organization mission, budget cycle, org chart, acquisition history,
decision makers, hot buttons, and customer needs.
""",
    )

    report = migrate_project_ariadne_corpus(corpus_root, vault_root)

    artifact_path = (
        vault_root
        / "artifact-patterns"
        / "project-ariadne"
        / "pursuits"
        / "_template"
        / "01_capture"
        / "customer"
        / "profile.md"
    )
    artifact_text = artifact_path.read_text(encoding="utf-8")

    assert report.incorporated_count == 1
    assert report.incorporated[0].native_target_paths == (
        "artifact-patterns/project-ariadne/pursuits/_template/01_capture/customer/profile.md",
    )
    assert "page_type: artifact_pattern" in artifact_text
    assert "expects_data_element:data-elements/customer" in artifact_text
    assert "expects_data_element:data-elements/customer_hot_buttons" in artifact_text
    assert "maps_to_artifact_block:artifact-block/customer-profile" in artifact_text
    assert "Private source formats remain local or ignored" in artifact_text
    assert "not an opportunity-specific Packet Field Answer" in artifact_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_project_ariadne_full_migration_adds_theseus_complementary_context(
    tmp_path,
) -> None:
    corpus_root = tmp_path / "project-ariadne" / "knowledge"
    vault_root = tmp_path / "vault"
    _write(
        corpus_root / "global_wiki/capture/customer-hot-button-identification.md",
        """---
title: Customer Hot Button Identification
---

Hot buttons can be detected from RFP language and validated by engagement.
""",
    )

    migrate_project_ariadne_corpus(corpus_root, vault_root)

    theseus_page = (
        vault_root / "skills-capabilities" / "capability-theseus-solicitation-parser.md"
    )
    theseus_text = theseus_page.read_text(encoding="utf-8")

    assert "page_type: workflow_capability" in theseus_text
    assert "Project Theseus Solicitation Parser" in theseus_text
    assert "uses_capability:capability/theseus-solicitation-parser" in theseus_text
    assert "informs:data-elements/customer_hot_buttons" in theseus_text
    assert "informs:data-elements/evaluation_factors" in theseus_text
    assert "suggests_route:workflow/document-intake" in theseus_text
    assert "Extraction Bundle" in theseus_text
    assert "does not write trusted Ariadne records" in theseus_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_project_ariadne_full_migration_creates_native_concept_milestone_and_entity_pages(
    tmp_path,
) -> None:
    corpus_root = tmp_path / "project-ariadne" / "knowledge"
    vault_root = tmp_path / "vault"
    source_paths = (
        "global_wiki/capture/customer-hot-button-identification.md",
        "domain_intel/milestones/ms1-qualification.md",
        "domain_intel/capabilities/kbr-inc.md",
    )
    _write(
        corpus_root / source_paths[0],
        """---
title: Customer Hot Button Identification
entity_type: customer_priority
---

Customer hot buttons guide call planning and evaluation strategy.
""",
    )
    _write(
        corpus_root / source_paths[1],
        """---
title: MS1 Qualification
entity_type: milestone_gate
---

Qualification decision confirms customer, scope, value, timing, and bid decision fit.
""",
    )
    _write(
        corpus_root / source_paths[2],
        """---
title: KBR Inc
entity_type: seller
---

KBR capability baseline includes logistics, digital, cyber, and mission support proof.
""",
    )

    report = migrate_project_ariadne_corpus(corpus_root, vault_root)

    native_targets = {
        path for item in report.incorporated for path in item.native_target_paths
    }
    assert native_targets == {
        "capture-concepts/project-ariadne/global_wiki/capture/customer-hot-button-identification.md",
        "milestones/project-ariadne/domain_intel/milestones/ms1-qualification.md",
        "entities/project-ariadne/domain_intel/capabilities/kbr-inc.md",
    }

    concept_text = (
        vault_root
        / "capture-concepts"
        / "project-ariadne"
        / "global_wiki"
        / "capture"
        / "customer-hot-button-identification.md"
    ).read_text(encoding="utf-8")
    milestone_text = (
        vault_root
        / "milestones"
        / "project-ariadne"
        / "domain_intel"
        / "milestones"
        / "ms1-qualification.md"
    ).read_text(encoding="utf-8")
    entity_text = (
        vault_root
        / "entities"
        / "project-ariadne"
        / "domain_intel"
        / "capabilities"
        / "kbr-inc.md"
    ).read_text(encoding="utf-8")

    assert "page_type: capture_concept" in concept_text
    assert "informs:data-elements/customer_hot_buttons" in concept_text
    assert "suggests_route:workflow/capture-research" in concept_text
    assert (
        "uses_source:source-summaries/project-ariadne/global_wiki/capture/customer-hot-button-identification"
        in concept_text
    )

    assert "page_type: capture_concept" in milestone_text
    assert "applies_to_gate:milestone_1" in milestone_text
    assert "informs:data-elements/approval_criteria" in milestone_text
    assert "suggests_route:workflow/opportunity-activation" in milestone_text

    assert "page_type: entity" in entity_text
    assert "informs:data-elements/seller_capabilities" in entity_text
    assert "suggests_route:workflow/seller-capability-baseline" in entity_text
    assert (
        "uses_source:source-summaries/project-ariadne/domain_intel/capabilities/kbr-inc"
        in entity_text
    )

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_project_ariadne_full_migration_creates_relationship_map_page(tmp_path) -> None:
    corpus_root = tmp_path / "project-ariadne" / "knowledge"
    vault_root = tmp_path / "vault"
    _write(
        corpus_root / "global_wiki/evaluation/technical-approach-evaluation-factor.md",
        """---
title: Technical Approach Evaluation Factor
---

Evaluation criteria shape proposal proof, technical discriminators, and customer hot buttons.
""",
    )
    _write(
        corpus_root / "pursuits/_template/01_capture/strategy/risk_register.md",
        """# Risk Register

Capture risk register expects risk owners, mitigations, gate decisions, and customer impact.
""",
    )

    migrate_project_ariadne_corpus(corpus_root, vault_root)

    map_text = (
        vault_root / "relationships" / "project-ariadne-native-relationship-map.md"
    ).read_text(encoding="utf-8")

    assert "page_type: relationship" in map_text
    assert "Project Ariadne Native Relationship Map" in map_text
    assert "source summary pages" in map_text
    assert "native concept/entity/artifact pages" in map_text
    assert "informs:data-elements/evaluation_factors" in map_text
    assert "expects_data_element:data-elements/risks" in map_text
    assert "suggests_route:workflow/capture-research" in map_text
    assert "suggests_route:workflow/artifact-assembly" in map_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True
