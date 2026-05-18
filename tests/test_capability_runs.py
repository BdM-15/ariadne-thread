import pytest

from ariadne.capability_runs import (
    CapabilityRunOutputReviewState,
    CapabilityRunReviewDecisionType,
    CapabilityRunStatus,
    CapabilityRunStore,
    record_capability_run_output_review,
    run_capability_catalog_validation,
    run_local_admin_model_readiness_probe,
)
from ariadne.config import LocalAdminModelSettings


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


def test_records_discard_review_decision_on_capability_run_output(tmp_path) -> None:
    store, run = _catalog_validation_run_with_gap(tmp_path)

    reviewed_run = record_capability_run_output_review(
        store=store,
        run_id=run.run_id,
        output_id=run.outputs[0].output_id,
        decision=CapabilityRunReviewDecisionType.DISCARD,
        reviewer_rationale="Not useful for this pass.",
    )

    reviewed_output = reviewed_run.outputs[0]
    assert reviewed_output.review_state is CapabilityRunOutputReviewState.DISCARDED
    assert reviewed_output.review_decisions[0].decision == "discard"
    assert reviewed_output.review_decisions[0].reviewer_rationale == (
        "Not useful for this pass."
    )
    assert store.read(run.run_id).outputs[0].review_state == "discarded"


def test_routes_review_decision_requires_destination(tmp_path) -> None:
    store, run = _catalog_validation_run_with_gap(tmp_path)

    with pytest.raises(ValueError, match="routed review requires routed_destination"):
        record_capability_run_output_review(
            store=store,
            run_id=run.run_id,
            output_id=run.outputs[0].output_id,
            decision=CapabilityRunReviewDecisionType.ROUTE,
        )


def test_rejects_second_review_decision_for_same_output(tmp_path) -> None:
    store, run = _catalog_validation_run_with_gap(tmp_path)
    record_capability_run_output_review(
        store=store,
        run_id=run.run_id,
        output_id=run.outputs[0].output_id,
        decision=CapabilityRunReviewDecisionType.ACCEPT,
    )

    with pytest.raises(ValueError, match="Capability Run Output already reviewed"):
        record_capability_run_output_review(
            store=store,
            run_id=run.run_id,
            output_id=run.outputs[0].output_id,
            decision=CapabilityRunReviewDecisionType.DISCARD,
        )


def test_local_admin_model_readiness_probe_records_success_with_fake_client(
    tmp_path,
) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_local_admin_model_readiness_probe(
        settings=LocalAdminModelSettings(enabled=True),
        store=store,
        client=_FakeLocalAdminModelClient(
            {"confidence_notes": ["Probe response shape valid."]}
        ),
    )

    assert run.status is CapabilityRunStatus.NEEDS_REVIEW
    assert run.provenance["source_mode"] == "local_admin_model_probe"
    assert run.provenance["model_status"] == "used"
    assert run.outputs[0].output_type == "local_admin_model_readiness"
    assert run.outputs[0].gaps == ()
    assert run.outputs[0].provenance["response_shape_valid"] is True
    assert store.read(run.run_id) == run


def test_local_admin_model_readiness_probe_records_unavailable_with_fake_client(
    tmp_path,
) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_local_admin_model_readiness_probe(
        settings=LocalAdminModelSettings(enabled=True),
        store=store,
        client=_UnavailableLocalAdminModelClient(),
    )

    assert run.status is CapabilityRunStatus.UNAVAILABLE
    assert run.provenance["model_status"] == "unavailable"
    assert run.outputs[0].provenance["response_shape_valid"] is False
    assert "Local Admin Model unavailable" in run.outputs[0].gaps[0]


def test_local_admin_model_readiness_probe_records_invalid_response_with_fake_client(
    tmp_path,
) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_local_admin_model_readiness_probe(
        settings=LocalAdminModelSettings(enabled=True),
        store=store,
        client=_FakeLocalAdminModelClient({"confidence_notes": "not an array"}),
    )

    assert run.status is CapabilityRunStatus.UNAVAILABLE
    assert run.provenance["model_status"] == "invalid_response"
    assert run.outputs[0].provenance["response_shape_valid"] is False
    assert "invalid JSON or schema" in run.outputs[0].gaps[0]


def _catalog_validation_run_with_gap(tmp_path):
    skill_dir = tmp_path / ".github" / "skills" / "review-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: review-skill\n"
        "---\n"
        "# Review Skill\n",
        encoding="utf-8",
    )
    store = CapabilityRunStore(tmp_path / "capability-runs")
    run = run_capability_catalog_validation(workspace_root=tmp_path, store=store)
    return store, run


class _FakeLocalAdminModelClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response

    def generate_json(self, **kwargs):
        return self.response


class _UnavailableLocalAdminModelClient:
    def generate_json(self, **kwargs):
        raise TimeoutError("Ollama probe timed out")