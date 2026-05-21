from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from ariadne.capability_runs import CapabilityRun


class ImprovementProposalKind(StrEnum):
    SKILL_DECOMPOSITION = "skill_decomposition"
    SKILL_MERGE_SPLIT = "skill_merge_split"
    EVAL_GAP = "eval_gap"
    CHAIN_ORDER_CHANGE = "chain_order_change"
    QUALITY_GATE_UPDATE = "quality_gate_update"
    AUTONOMY_CANDIDATE = "autonomy_candidate"


class ImprovementProposalReviewState(StrEnum):
    SUGGESTION = "suggestion"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class ImprovementProposalReviewDecisionType(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"


class ImprovementProposalEvidenceRef(BaseModel):
    evidence_type: str
    ref_id: str
    summary: str
    source_path: str | None = None


class ImprovementProposalReviewDecision(BaseModel):
    decision_id: str
    proposal_id: str
    decision: ImprovementProposalReviewDecisionType
    reviewer_rationale: str = ""
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HermesImprovementProposal(BaseModel):
    proposal_id: str
    kind: ImprovementProposalKind
    title: str
    target_ref: str
    proposed_change: str
    rationale: str
    evidence_refs: tuple[ImprovementProposalEvidenceRef, ...]
    guardrail_summary: str = (
        "Review before editing skills, chain maps, trusted records, or autonomy settings."
    )
    review_state: ImprovementProposalReviewState = ImprovementProposalReviewState.SUGGESTION
    review_decisions: tuple[ImprovementProposalReviewDecision, ...] = ()
    mutates_skills: bool = False
    mutates_chain_maps: bool = False
    mutates_trusted_records: bool = False
    mutates_autonomy_settings: bool = False
    trusted_downstream_writes: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def require_supporting_evidence(self) -> HermesImprovementProposal:
        if not self.evidence_refs:
            raise ValueError("Improvement Proposal requires supporting evidence")
        return self


class ImprovementProposalStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, proposal: HermesImprovementProposal) -> HermesImprovementProposal:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(proposal.proposal_id).write_text(
            proposal.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return proposal

    def read(self, proposal_id: str) -> HermesImprovementProposal:
        return HermesImprovementProposal.model_validate_json(
            self._path(proposal_id).read_text(encoding="utf-8")
        )

    def list(self) -> tuple[HermesImprovementProposal, ...]:
        if not self.root.exists():
            return ()
        return tuple(
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        )

    def _path(self, proposal_id: str) -> Path:
        if not proposal_id or proposal_id != Path(proposal_id).name:
            raise ValueError("proposal_id must be a file-safe identifier")
        return self.root / f"{proposal_id}.json"


def propose_skill_improvement_from_capability_run(
    *,
    run: CapabilityRun,
    kind: ImprovementProposalKind,
    target_ref: str,
    title: str,
    proposed_change: str,
    rationale: str | None = None,
) -> HermesImprovementProposal:
    evidence_refs = _evidence_refs_from_capability_run(run)
    proposal_id = _proposal_id(
        kind=kind,
        target_ref=target_ref,
        proposed_change=proposed_change,
        evidence_refs=evidence_refs,
    )
    return HermesImprovementProposal(
        proposal_id=proposal_id,
        kind=kind,
        title=title,
        target_ref=target_ref,
        proposed_change=proposed_change,
        rationale=rationale or _default_rationale(run),
        evidence_refs=evidence_refs,
    )


def record_improvement_proposal_review(
    *,
    store: ImprovementProposalStore,
    proposal_id: str,
    decision: ImprovementProposalReviewDecisionType,
    reviewer_rationale: str = "",
) -> HermesImprovementProposal:
    proposal = store.read(proposal_id)
    if proposal.review_state is not ImprovementProposalReviewState.SUGGESTION:
        raise ValueError("Improvement Proposal already reviewed")
    review_decision = ImprovementProposalReviewDecision(
        decision_id=f"impreview_{uuid4().hex}",
        proposal_id=proposal_id,
        decision=decision,
        reviewer_rationale=reviewer_rationale,
    )
    updated = proposal.model_copy(
        update={
            "review_state": _review_state_for_decision(decision),
            "review_decisions": proposal.review_decisions + (review_decision,),
        }
    )
    return store.write(updated)


def _evidence_refs_from_capability_run(
    run: CapabilityRun,
) -> tuple[ImprovementProposalEvidenceRef, ...]:
    refs: list[ImprovementProposalEvidenceRef] = [
        ImprovementProposalEvidenceRef(
            evidence_type="capability_run",
            ref_id=run.run_id,
            summary=(
                f"Capability run {run.run_id} used {run.capability_id} with "
                f"status {run.status.value}."
            ),
        )
    ]
    for output in run.outputs:
        refs.append(
            ImprovementProposalEvidenceRef(
                evidence_type="capability_run_output",
                ref_id=output.output_id,
                summary=(
                    f"Output {output.output_id} review state "
                    f"{output.review_state.value}: {output.summary}"
                ),
            )
        )
        refs.extend(_chain_stage_refs(output.provenance))
        for decision in output.review_decisions:
            rationale = (
                f": {decision.reviewer_rationale}"
                if decision.reviewer_rationale
                else ""
            )
            refs.append(
                ImprovementProposalEvidenceRef(
                    evidence_type="review_decision",
                    ref_id=decision.decision_id,
                    summary=f"Review decision {decision.decision.value}{rationale}",
                )
            )
    return tuple(refs)


def _chain_stage_refs(
    provenance: dict[str, object],
) -> tuple[ImprovementProposalEvidenceRef, ...]:
    chain = provenance.get("thin_orchestration_chain")
    if not isinstance(chain, dict):
        return ()
    stages = chain.get("stage_records", ())
    if not isinstance(stages, list | tuple):
        return ()
    refs: list[ImprovementProposalEvidenceRef] = []
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        stage_id = str(stage.get("stage_id", "")).strip()
        if not stage_id:
            continue
        refs.append(
            ImprovementProposalEvidenceRef(
                evidence_type="chain_stage",
                ref_id=stage_id,
                summary=(
                    f"Chain stage {stage_id} used {stage.get('capability_id')} with "
                    f"quality gate result {stage.get('quality_gate_result')}."
                ),
            )
        )
    return tuple(refs)


def _default_rationale(run: CapabilityRun) -> str:
    rejected_outputs = tuple(
        output
        for output in run.outputs
        if output.review_state.value in {"discarded", "routed", "refined"}
    )
    if rejected_outputs:
        return "Observed rejected, routed, or refined output on a capability run."
    if any(output.gaps for output in run.outputs):
        return "Observed capability output gaps that may indicate an eval or quality-gate need."
    return "Observed capability run evidence suggests a reviewable improvement candidate."


def _review_state_for_decision(
    decision: ImprovementProposalReviewDecisionType,
) -> ImprovementProposalReviewState:
    if decision is ImprovementProposalReviewDecisionType.ACCEPT:
        return ImprovementProposalReviewState.ACCEPTED
    if decision is ImprovementProposalReviewDecisionType.REJECT:
        return ImprovementProposalReviewState.REJECTED
    return ImprovementProposalReviewState.DEFERRED


def _proposal_id(
    *,
    kind: ImprovementProposalKind,
    target_ref: str,
    proposed_change: str,
    evidence_refs: tuple[ImprovementProposalEvidenceRef, ...],
) -> str:
    raw_key = "|".join(
        (
            kind.value,
            target_ref,
            proposed_change,
            *(evidence.ref_id for evidence in evidence_refs),
        )
    )
    return f"improvement_{sha256(raw_key.encode()).hexdigest()[:12]}"