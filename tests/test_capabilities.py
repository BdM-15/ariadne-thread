from ariadne.capabilities import (
    CapabilityMaturity,
    CapabilityType,
    CapabilityValidationStatus,
    discover_local_capability_catalog,
)


def test_discovers_workspace_skills_from_canonical_location(tmp_path) -> None:
    skill_dir = tmp_path / ".github" / "skills" / "customer-intel"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: customer-intel\n"
        "description: Finds customer context for a pursuit.\n"
        "---\n"
        "# Customer Intel\n",
        encoding="utf-8",
    )

    catalog = discover_local_capability_catalog(tmp_path)

    assert len(catalog.entries) == 1
    entry = catalog.entries[0]
    assert entry.id == "customer-intel"
    assert entry.name == "customer-intel"
    assert entry.description == "Finds customer context for a pursuit."
    assert entry.capability_type is CapabilityType.WORKSPACE_SKILL
    assert entry.source_path == ".github/skills/customer-intel/SKILL.md"


def test_catalog_entries_expose_routing_metadata_from_skill_frontmatter(
    tmp_path,
) -> None:
    skill_dir = tmp_path / ".github" / "skills" / "partner-research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: partner-research\n"
        "description: Finds likely partners and teammate gaps.\n"
        "capability_type: cli_harness\n"
        "maturity: stable\n"
        "lifecycle_fit: pursuing, bidding\n"
        "workstream_fit: partner_strategy, competitive_intelligence\n"
        "product_workflow_fit: living_briefing_packet, action_plan\n"
        "validation_status: tested\n"
        "---\n"
        "# Partner Research\n",
        encoding="utf-8",
    )

    catalog = discover_local_capability_catalog(tmp_path)

    entry = catalog.entries[0]
    assert entry.capability_type is CapabilityType.CLI_HARNESS
    assert entry.maturity is CapabilityMaturity.STABLE
    assert entry.validation_status is CapabilityValidationStatus.TESTED
    assert entry.lifecycle_fit == ("pursuing", "bidding")
    assert entry.workstream_fit == ("partner_strategy", "competitive_intelligence")
    assert entry.product_workflow_fit == ("living_briefing_packet", "action_plan")
    assert entry.provenance_note == "Discovered from local skill metadata."


def test_catalog_is_read_only_and_reports_canonical_locations(tmp_path) -> None:
    catalog = discover_local_capability_catalog(tmp_path)

    assert catalog.entries == ()
    assert catalog.read_only is True
    assert catalog.canonical_locations == (".github/skills",)
    assert not (tmp_path / ".github").exists()
