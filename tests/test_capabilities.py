from pathlib import Path

from ariadne.capabilities import (
    CapabilityAutonomyTier,
    CapabilityModelRole,
    CapabilityMaturity,
    CapabilityStatus,
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
    assert entry.capability_status is CapabilityStatus.RUNNABLE
    assert entry.source_path == ".github/skills/customer-intel/SKILL.md"
    assert entry.contract.review_destination == "Capability Studio"
    assert entry.contract.autonomy_tier is CapabilityAutonomyTier.HUMAN_APPROVAL_REQUIRED
    assert entry.contract.model_role is CapabilityModelRole.NONE
    assert entry.contract.fake_runner_supported is False
    assert entry.contract.provenance_requirements == (
        "capability_id",
        "source_path",
        "input_refs",
    )


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


def test_catalog_entries_expose_mvp2_capability_contracts_from_frontmatter(
    tmp_path,
) -> None:
    skill_dir = tmp_path / ".github" / "skills" / "award-history-chain"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: award-history-chain\n"
        "description: Builds a reviewable award history route.\n"
        "capability_type: skill_chain\n"
        "capability_status: dependency_gated\n"
        "persona_fit: capture_manager, proposal_manager\n"
        "source_family: usaspending\n"
        "input_expectations: opportunity_id, piid_profile_ref\n"
        "output_summary_shape: Award history brief with gaps and limitations.\n"
        "quality_gate: cites_source_profile_and_limitations\n"
        "review_destination: packet_field_answer_candidate\n"
        "autonomy_tier: ask_before_running\n"
        "model_role: local_admin_model\n"
        "fake_runner_supported: true\n"
        "provenance_requirements: capability_id, input_refs, source_profile_refs\n"
        "---\n"
        "# Award History Chain\n",
        encoding="utf-8",
    )

    catalog = discover_local_capability_catalog(tmp_path)

    entry = catalog.entries[0]
    assert entry.capability_type is CapabilityType.SKILL_CHAIN
    assert entry.capability_status is CapabilityStatus.DEPENDENCY_GATED
    assert entry.contract.persona_fit == ("capture_manager", "proposal_manager")
    assert entry.contract.source_family == "usaspending"
    assert entry.contract.input_expectations == (
        "opportunity_id",
        "piid_profile_ref",
    )
    assert (
        entry.contract.output_summary_shape
        == "Award history brief with gaps and limitations."
    )
    assert entry.contract.quality_gate == "cites_source_profile_and_limitations"
    assert entry.contract.review_destination == "packet_field_answer_candidate"
    assert entry.contract.autonomy_tier is CapabilityAutonomyTier.ASK_BEFORE_RUNNING
    assert entry.contract.model_role is CapabilityModelRole.LOCAL_ADMIN_MODEL
    assert entry.contract.fake_runner_supported is True
    assert entry.contract.provenance_requirements == (
        "capability_id",
        "input_refs",
        "source_profile_refs",
    )


def test_capability_taxonomy_covers_mvp2_route_families() -> None:
    assert {
        CapabilityType.WORKSPACE_SKILL.value,
        CapabilityType.MODEL_WORKFLOW.value,
        CapabilityType.SOURCE_PROFILE_ROUTE.value,
        CapabilityType.MCP_TOOL.value,
        CapabilityType.SKILL_CHAIN.value,
    } == {
        "workspace_skill",
        "model_workflow",
        "source_profile_route",
        "mcp_tool",
        "skill_chain",
    }
    assert {
        CapabilityStatus.RUNNABLE.value,
        CapabilityStatus.DEPENDENCY_GATED.value,
        CapabilityStatus.DEFERRED.value,
        CapabilityStatus.UTILITY_META.value,
        CapabilityStatus.INSPIRATION_ONLY.value,
    } == {
        "runnable",
        "dependency_gated",
        "deferred",
        "utility_meta",
        "inspiration_only",
    }


def test_data_table_profiler_skill_is_discoverable_through_mvp2_contract() -> None:
    workspace_root = Path(__file__).resolve().parents[1]

    catalog = discover_local_capability_catalog(workspace_root)

    entry = next(entry for entry in catalog.entries if entry.id == "data-table-profiler")
    assert entry.capability_type is CapabilityType.WORKSPACE_SKILL
    assert entry.capability_status is CapabilityStatus.RUNNABLE
    assert entry.validation_status is CapabilityValidationStatus.TESTED
    assert entry.contract.source_family == "structured_table"
    assert entry.contract.input_expectations == ("table_source_ref", "table_rows")
    assert entry.contract.output_summary_shape == (
        "Data table profile with shape, key fields, missing values, anomalies, "
        "assumptions, gaps, and recommended next route."
    )
    assert entry.contract.quality_gate == "human_review_required_before_trusted_use"
    assert entry.contract.review_destination == "Capability Run Output"
    assert entry.contract.model_role is CapabilityModelRole.NONE
    assert entry.contract.fake_runner_supported is True


def test_catalog_is_read_only_and_reports_canonical_locations(tmp_path) -> None:
    catalog = discover_local_capability_catalog(tmp_path)

    assert catalog.entries == ()
    assert catalog.read_only is True
    assert catalog.canonical_locations == (".github/skills",)
    assert not (tmp_path / ".github").exists()
