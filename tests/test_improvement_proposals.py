import pytest

from ariadne.capability_runs import (
    CapabilityRunReviewDecisionType,
    CapabilityRunStore,
    record_capability_run_output_review,
)
from ariadne.data_table_profiler import DataTableProfileRequest
from ariadne.improvement_proposals import (
    ImprovementProposalEvidenceRef,
    ImprovementProposalKind,
    ImprovementProposalReviewDecisionType,
    ImprovementProposalReviewState,
    ImprovementProposalStore,
    HermesImprovementProposal,
    propose_skill_improvement_from_capability_run,
    record_improvement_proposal_review,
)
from ariadne.thin_orchestration_chains import run_data_table_profile_next_route_chain


def test_improvement_proposal_model_covers_mvp2_suggestion_types() -> None:
    assert {kind.value for kind in ImprovementProposalKind} >= {
        "skill_decomposition",
        "skill_merge_split",
        "eval_gap",
        "chain_order_change",
        "quality_gate_update",
        "autonomy_candidate",
    }


def test_hermes_proposal_from_chain_run_cites_stage_and_rejected_output(tmp_path) -> None:
    capability_store = CapabilityRunStore(tmp_path / "capability-runs")
    run = run_data_table_profile_next_route_chain(
        request=_sample_profile_request(),
        store=capability_store,
        opportunity_id="opp-proposal",
        approval_basis="operator_approved_fixture_chain",
    )
    reviewed_run = record_capability_run_output_review(
        store=capability_store,
        run_id=run.run_id,
        output_id=run.outputs[0].output_id,
        decision=CapabilityRunReviewDecisionType.DISCARD,
        reviewer_rationale="Route summary missed workload assumptions.",
    )

    proposal = propose_skill_improvement_from_capability_run(
        run=reviewed_run,
        kind=ImprovementProposalKind.CHAIN_ORDER_CHANGE,
        target_ref="skill-chain:data-table-profile-next-route",
        title="Add workload-assumption review after data profiling",
        proposed_change=(
            "Insert a workload-assumption review stage before the next-route summary."
        ),
    )

    assert proposal.kind is ImprovementProposalKind.CHAIN_ORDER_CHANGE
    assert proposal.review_state is ImprovementProposalReviewState.SUGGESTION
    assert proposal.proposal_id.startswith("improvement_")
    assert proposal.trusted_downstream_writes is False
    assert proposal.mutates_skills is False
    assert proposal.mutates_chain_maps is False
    assert proposal.mutates_autonomy_settings is False
    assert proposal.mutates_trusted_records is False
    assert "review before editing skills" in proposal.guardrail_summary.lower()
    assert {evidence.evidence_type for evidence in proposal.evidence_refs} >= {
        "capability_run",
        "capability_run_output",
        "chain_stage",
        "review_decision",
    }
    assert any(
        evidence.ref_id == "stage_1_data_table_profiler"
        for evidence in proposal.evidence_refs
    )
    assert any(
        "missed workload assumptions" in evidence.summary
        for evidence in proposal.evidence_refs
    )


def test_proposal_store_review_changes_only_proposal_state(tmp_path) -> None:
    skill_file = tmp_path / ".github" / "skills" / "demo-skill" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("# Demo Skill\n", encoding="utf-8")
    store = ImprovementProposalStore(tmp_path / "improvement-proposals")
    proposal = HermesImprovementProposal(
        proposal_id="improvement_demo_skill_eval_gap",
        kind=ImprovementProposalKind.EVAL_GAP,
        title="Add eval for missing source limitations",
        target_ref=".github/skills/demo-skill/SKILL.md",
        proposed_change="Add an eval prompt that checks source limitation wording.",
        rationale="A rejected output missed source limitation language.",
        evidence_refs=(
            ImprovementProposalEvidenceRef(
                evidence_type="capability_run_output",
                ref_id="output_demo",
                summary="Output rejected for missing source limitations.",
            ),
        ),
    )

    store.write(proposal)
    reviewed = record_improvement_proposal_review(
        store=store,
        proposal_id=proposal.proposal_id,
        decision=ImprovementProposalReviewDecisionType.ACCEPT,
        reviewer_rationale="Good candidate for later skill-creator work.",
    )

    assert reviewed.review_state is ImprovementProposalReviewState.ACCEPTED
    assert reviewed.review_decisions[0].decision is ImprovementProposalReviewDecisionType.ACCEPT
    assert reviewed.mutates_skills is False
    assert skill_file.read_text(encoding="utf-8") == "# Demo Skill\n"
    assert store.read(proposal.proposal_id).review_state is ImprovementProposalReviewState.ACCEPTED


def test_improvement_proposal_requires_supporting_evidence() -> None:
    with pytest.raises(ValueError, match="supporting evidence"):
        HermesImprovementProposal(
            proposal_id="improvement_no_evidence",
            kind=ImprovementProposalKind.SKILL_DECOMPOSITION,
            title="Split broad skill",
            target_ref="skill:broad-skill",
            proposed_change="Split into smaller skills.",
            rationale="Hermes should not make unsupported proposals.",
            evidence_refs=(),
        )


def _sample_profile_request() -> DataTableProfileRequest:
    return DataTableProfileRequest(
        table_label="Workload table",
        source_ref="fixture://workload-table",
        source_refs=("fixture://workload-table",),
        rows=(
            {"Workload ID": "WL-1", "Labor Category": "Analyst", "Hours": 120},
            {"Workload ID": "WL-1", "Labor Category": "", "Hours": None},
        ),
    )