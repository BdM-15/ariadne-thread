from ariadne.capability_runs import (
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutputReviewState,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.proposal_support import (
    ComplianceRequirementRef,
    ComplianceSpinePlannerRequest,
    build_compliance_spine_plan,
    run_compliance_spine_planner_capability,
)


def test_compliance_spine_planner_documents_proposal_generator_decomposition() -> None:
    plan = build_compliance_spine_plan(_sample_request())

    assert plan.covered_proposal_generator_piece == "compliance_spine_planner"
    assert "win-theme-synthesizer" in plan.future_separate_skills
    assert "proposal-outline-drafter" in plan.future_separate_skills
    assert plan.quality_gate == "requirements_mapped_to_sections_with_source_refs"
    assert plan.review_destination == "Artifact Content Block"
    assert plan.provenance_requirements == (
        "capability_id",
        "requirement_refs",
        "source_refs",
        "review_state",
    )
    assert plan.input_contract == "accepted_or_reviewable_requirement_refs"
    assert plan.output_contract == "reviewable_compliance_spine_plan"
    assert len(plan.items) == 3
    assert plan.items[0].requirement_id == "C-1"
    assert plan.items[0].proposed_section == "Technical Approach"
    assert plan.items[1].proposed_section == "Management Approach"
    assert any("reviewable requirement" in gap for gap in plan.gaps)
    assert plan.trusted_downstream_writes is False


def test_compliance_spine_capability_run_stays_review_gated(tmp_path) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_compliance_spine_planner_capability(
        request=_sample_request(),
        store=store,
    )

    assert run.capability_id == "compliance-spine-planner"
    assert run.capability_type is CapabilityRunCapabilityType.SKILL
    assert run.executor_kind is CapabilityRunExecutorKind.DETERMINISTIC_PYTHON
    assert run.status is CapabilityRunStatus.NEEDS_REVIEW
    assert run.provenance["model_required"] is False
    assert run.provenance["network_required"] is False
    assert run.provenance["trusted_downstream_writes"] is False
    output = run.outputs[0]
    assert output.review_state is CapabilityRunOutputReviewState.PENDING
    assert output.recommended_destination == "Artifact Content Block"
    payload = output.provenance["compliance_spine_plan"]
    assert payload["covered_proposal_generator_piece"] == "compliance_spine_planner"
    assert payload["review_destination"] == "Artifact Content Block"
    assert payload["trusted_downstream_writes"] is False
    assert store.read(run.run_id) == run


def _sample_request() -> ComplianceSpinePlannerRequest:
    return ComplianceSpinePlannerRequest(
        opportunity_id="opp-proposal-spine",
        proposal_sections=(
            "Technical Approach",
            "Management Approach",
            "Past Performance",
        ),
        requirement_refs=(
            ComplianceRequirementRef(
                requirement_id="C-1",
                text="Offeror shall describe the cloud migration technical approach.",
                source_ref="doc://rfp/section-c#1",
                review_state="accepted",
            ),
            ComplianceRequirementRef(
                requirement_id="L-2",
                text="Proposal must identify staffing, key personnel, and management controls.",
                source_ref="doc://rfp/section-l#2",
                review_state="accepted",
            ),
            ComplianceRequirementRef(
                requirement_id="M-3",
                text="Evaluation will consider relevant past performance examples.",
                source_ref="doc://rfp/section-m#3",
                review_state="reviewable",
            ),
        ),
    )