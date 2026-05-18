from ariadne.capability_runs import (
    CapabilityRunStatus,
    CapabilityRunStore,
    run_capability_catalog_validation,
)


def test_catalog_validation_run_persists_reviewable_gap_output(tmp_path) -> None:
    skill_dir = tmp_path / ".github" / "skills" / "thin-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: thin-skill\n"
        "---\n"
        "# Thin Skill\n",
        encoding="utf-8",
    )
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_capability_catalog_validation(workspace_root=tmp_path, store=store)

    assert run.status is CapabilityRunStatus.NEEDS_REVIEW
    assert run.input_refs == (".github/skills",)
    assert run.provenance["network_required"] is False
    assert run.provenance["model_required"] is False
    assert run.outputs[0].review_state == "pending"
    assert run.outputs[0].autonomy_recommendation == "review_required"
    assert run.outputs[0].gaps == (
        "Missing capability description metadata.",
        "Capability validation status is still unvalidated.",
    )
    assert store.read(run.run_id) == run
    assert store.list() == [run]


def test_catalog_validation_run_records_summary_when_no_gaps(tmp_path) -> None:
    skill_dir = tmp_path / ".github" / "skills" / "validated-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: validated-skill\n"
        "description: Validated local capability.\n"
        "validation_status: validated\n"
        "---\n"
        "# Validated Skill\n",
        encoding="utf-8",
    )
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_capability_catalog_validation(workspace_root=tmp_path, store=store)

    assert run.outputs[0].output_id == "catalog_validation_summary"
    assert run.outputs[0].gaps == ()
    assert run.outputs[0].recommended_destination == "Capability Studio"