from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json

from pydantic import BaseModel

from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunAutonomyRecommendation,
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutput,
    CapabilityRunOutputReviewState,
    CapabilityRunSessionContext,
    CapabilityRunStatus,
    CapabilityRunStore,
)


class ComplianceRequirementRef(BaseModel):
    requirement_id: str
    text: str
    source_ref: str
    review_state: str = "reviewable"


class ComplianceSpinePlannerRequest(BaseModel):
    opportunity_id: str | None = None
    requirement_refs: tuple[ComplianceRequirementRef, ...]
    proposal_sections: tuple[str, ...]
    source_refs: tuple[str, ...] = ()


class ComplianceSpineItem(BaseModel):
    requirement_id: str
    source_ref: str
    requirement_summary: str
    proposed_section: str
    response_prompt: str
    compliance_risk: str
    review_state: str


class ComplianceSpinePlan(BaseModel):
    covered_proposal_generator_piece: str = "compliance_spine_planner"
    future_separate_skills: tuple[str, ...]
    input_contract: str = "accepted_or_reviewable_requirement_refs"
    output_contract: str = "reviewable_compliance_spine_plan"
    quality_gate: str = "requirements_mapped_to_sections_with_source_refs"
    review_destination: str = "Artifact Content Block"
    provenance_requirements: tuple[str, ...]
    items: tuple[ComplianceSpineItem, ...]
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]
    source_refs: tuple[str, ...]
    review_state: str = "pending_review"
    trusted_downstream_writes: bool = False


def build_compliance_spine_plan(
    request: ComplianceSpinePlannerRequest,
) -> ComplianceSpinePlan:
    source_refs = _source_refs(request)
    items = tuple(
        _spine_item(requirement, request.proposal_sections)
        for requirement in request.requirement_refs
    )
    return ComplianceSpinePlan(
        future_separate_skills=(
            "win-theme-synthesizer",
            "fab-chain-builder",
            "proposal-outline-drafter",
            "executive-summary-drafter",
            "pricing-volume-planner",
        ),
        provenance_requirements=(
            "capability_id",
            "requirement_refs",
            "source_refs",
            "review_state",
        ),
        items=items,
        assumptions=(
            "Requirements are explicit accepted or reviewable Ariadne context.",
            "Section mapping is a deterministic planning aid, not a proposal outline.",
            "No model, network, or proposal generator runtime was used.",
        ),
        gaps=_gaps(request, items),
        source_refs=source_refs,
    )


def run_compliance_spine_planner_capability(
    *,
    request: ComplianceSpinePlannerRequest,
    store: CapabilityRunStore,
    product_workflow: str = "proposal_support",
) -> CapabilityRun:
    plan = build_compliance_spine_plan(request)
    completed_at = datetime.now(UTC)
    digest = _request_digest(request)
    output = CapabilityRunOutput(
        output_id=f"output_compliance_spine_{digest}",
        output_type="compliance_spine_plan",
        title="Compliance spine plan",
        summary=(
            f"Mapped {len(plan.items)} requirement(s) into a reviewable compliance spine."
        ),
        gaps=plan.gaps,
        review_state=CapabilityRunOutputReviewState.PENDING,
        autonomy_recommendation=CapabilityRunAutonomyRecommendation.REVIEW_REQUIRED,
        recommended_destination=plan.review_destination,
        provenance={
            "capability_id": "compliance-spine-planner",
            "compliance_spine_plan": plan.model_dump(mode="json"),
            "source_refs": list(plan.source_refs),
            "review_gate_required": True,
            "trusted_downstream_writes": False,
        },
    )
    run = CapabilityRun(
        run_id=f"caprun_compliance_spine_{digest}",
        capability_id="compliance-spine-planner",
        capability_type=CapabilityRunCapabilityType.SKILL,
        executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
        session_context=CapabilityRunSessionContext.STUDIO,
        opportunity_id=request.opportunity_id,
        product_workflow=product_workflow,
        status=CapabilityRunStatus.NEEDS_REVIEW,
        inputs_summary=(
            f"Mapped {len(request.requirement_refs)} requirement ref(s) across "
            f"{len(request.proposal_sections)} proposal section(s)."
        ),
        input_refs=plan.source_refs,
        outputs=(output,),
        provenance={
            "capability_id": "compliance-spine-planner",
            "executor": CapabilityRunExecutorKind.DETERMINISTIC_PYTHON.value,
            "source_refs": list(plan.source_refs),
            "quality_gate": plan.quality_gate,
            "review_destination": plan.review_destination,
            "model_required": False,
            "network_required": False,
            "trusted_downstream_writes": False,
            "completed_at": completed_at.isoformat(),
        },
        completed_at=completed_at,
    )
    return store.write(run)


def _spine_item(
    requirement: ComplianceRequirementRef,
    proposal_sections: tuple[str, ...],
) -> ComplianceSpineItem:
    proposed_section = _section_for_requirement(requirement.text, proposal_sections)
    return ComplianceSpineItem(
        requirement_id=requirement.requirement_id,
        source_ref=requirement.source_ref,
        requirement_summary=_summary(requirement.text),
        proposed_section=proposed_section,
        response_prompt=(
            f"In {proposed_section}, address {requirement.requirement_id} with "
            f"explicit source support from {requirement.source_ref}."
        ),
        compliance_risk=_compliance_risk(requirement),
        review_state=requirement.review_state,
    )


def _section_for_requirement(text: str, proposal_sections: tuple[str, ...]) -> str:
    lowered = text.lower()
    section_keywords = (
        (("technical", "cloud", "solution", "migration"), "technical"),
        (("staff", "personnel", "management", "controls"), "management"),
        (("past performance", "relevant", "examples"), "past"),
        (("price", "cost"), "price"),
    )
    for keywords, section_hint in section_keywords:
        if any(keyword in lowered for keyword in keywords):
            matched = _section_with_hint(proposal_sections, section_hint)
            if matched:
                return matched
    return proposal_sections[0] if proposal_sections else "Unassigned review bucket"


def _section_with_hint(proposal_sections: tuple[str, ...], hint: str) -> str | None:
    for section in proposal_sections:
        if hint in section.lower():
            return section
    return None


def _compliance_risk(requirement: ComplianceRequirementRef) -> str:
    if requirement.review_state != "accepted":
        return "medium_review_state_not_accepted"
    if not requirement.source_ref.strip():
        return "high_missing_source_ref"
    return "low"


def _gaps(
    request: ComplianceSpinePlannerRequest,
    items: tuple[ComplianceSpineItem, ...],
) -> tuple[str, ...]:
    gaps: list[str] = []
    reviewable_count = sum(
        item.review_state != "accepted"
        for item in items
    )
    if reviewable_count:
        gaps.append(
            f"{reviewable_count} reviewable requirement(s) need acceptance before proposal use."
        )
    if not request.proposal_sections:
        gaps.append("Proposal sections are missing; planner used an unassigned review bucket.")
    if not request.requirement_refs:
        gaps.append("No requirement refs were supplied for the compliance spine.")
    return tuple(gaps) or ("Review section mapping before artifact or proposal use.",)


def _source_refs(request: ComplianceSpinePlannerRequest) -> tuple[str, ...]:
    refs = [requirement.source_ref for requirement in request.requirement_refs]
    refs.extend(request.source_refs)
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def _summary(text: str) -> str:
    stripped = " ".join(text.split())
    return stripped if len(stripped) <= 140 else f"{stripped[:137]}..."


def _request_digest(request: ComplianceSpinePlannerRequest) -> str:
    payload = request.model_dump(mode="json")
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]