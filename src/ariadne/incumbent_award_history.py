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
from ariadne.piid_profiles import PiidContractIntelligenceProfile


class IncumbentAwardHistoryBriefRequest(BaseModel):
    piid_profile: PiidContractIntelligenceProfile
    opportunity_id: str | None = None
    packet_field_key: str | None = None
    approval_basis: str = "operator_selected_source_profile"


class IncumbentAwardRouteOption(BaseModel):
    route_id: str
    destination: str
    rationale: str


class IncumbentAwardHistoryBrief(BaseModel):
    source_family: str
    source_profile_id: str
    normalized_piid: str
    incumbent_name: str
    award_summary: str
    obligation_summary: str
    recompete_signals: tuple[str, ...]
    source_refs: tuple[str, ...]
    source_limitations: tuple[str, ...]
    approval_basis: str
    route_options: tuple[IncumbentAwardRouteOption, ...]
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]
    review_state: str = "pending_review"
    trusted_downstream_writes: bool = False


def build_incumbent_award_history_brief(
    request: IncumbentAwardHistoryBriefRequest,
) -> IncumbentAwardHistoryBrief:
    profile = request.piid_profile
    incumbent_name = profile.award_baseline.recipient_name or "Unknown incumbent"
    award_summary = _award_summary(profile)
    obligation_summary = _obligation_summary(profile)
    source_limitations = _source_limitations(profile)
    return IncumbentAwardHistoryBrief(
        source_family="usaspending",
        source_profile_id=profile.id,
        normalized_piid=profile.normalized_piid,
        incumbent_name=incumbent_name,
        award_summary=award_summary,
        obligation_summary=obligation_summary,
        recompete_signals=_recompete_signals(profile),
        source_refs=_source_refs(profile),
        source_limitations=source_limitations,
        approval_basis=request.approval_basis,
        route_options=_route_options(request),
        assumptions=(
            "Award recipient is treated as the incumbent signal until reviewed.",
            "Obligation and burn posture come from the selected PIID profile only.",
            "No live federal-data call was made while creating this brief.",
        ),
        gaps=_gaps(profile, source_limitations),
    )


def run_incumbent_award_history_brief_capability(
    *,
    request: IncumbentAwardHistoryBriefRequest,
    store: CapabilityRunStore,
    product_workflow: str = "competitive_intel",
) -> CapabilityRun:
    brief = build_incumbent_award_history_brief(request)
    completed_at = datetime.now(UTC)
    digest = _request_digest(request)
    output = CapabilityRunOutput(
        output_id=f"output_incumbent_award_history_{digest}",
        output_type="incumbent_award_history_brief",
        title=f"Incumbent award-history brief: {brief.normalized_piid}",
        summary=(
            f"{brief.incumbent_name} award-history signal for "
            f"{brief.normalized_piid}; route after review."
        ),
        gaps=brief.gaps,
        review_state=CapabilityRunOutputReviewState.PENDING,
        autonomy_recommendation=CapabilityRunAutonomyRecommendation.REVIEW_REQUIRED,
        recommended_destination="Packet Field Answer candidate",
        provenance={
            "capability_id": "incumbent-award-history-brief",
            "incumbent_award_history_brief": brief.model_dump(mode="json"),
            "source_family": brief.source_family,
            "source_refs": list(brief.source_refs),
            "source_limitations": list(brief.source_limitations),
            "approval_basis": brief.approval_basis,
            "review_gate_required": True,
            "trusted_downstream_writes": False,
        },
    )
    run = CapabilityRun(
        run_id=f"caprun_incumbent_award_history_{digest}",
        capability_id="incumbent-award-history-brief",
        capability_type=CapabilityRunCapabilityType.SKILL,
        executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
        session_context=CapabilityRunSessionContext.STUDIO,
        opportunity_id=request.opportunity_id,
        product_workflow=product_workflow,
        status=CapabilityRunStatus.NEEDS_REVIEW,
        inputs_summary=(
            f"Built incumbent award-history brief from PIID profile {brief.source_profile_id}."
        ),
        input_refs=brief.source_refs,
        outputs=(output,),
        provenance={
            "capability_id": "incumbent-award-history-brief",
            "executor": CapabilityRunExecutorKind.DETERMINISTIC_PYTHON.value,
            "source_family": brief.source_family,
            "source_profile_id": brief.source_profile_id,
            "source_refs": list(brief.source_refs),
            "source_limitations": list(brief.source_limitations),
            "approval_basis": brief.approval_basis,
            "network_required": False,
            "model_required": False,
            "live_federal_data_call": False,
            "trusted_downstream_writes": False,
            "completed_at": completed_at.isoformat(),
        },
        completed_at=completed_at,
    )
    return store.write(run)


def _award_summary(profile: PiidContractIntelligenceProfile) -> str:
    baseline = profile.award_baseline
    agency = baseline.awarding_agency_name or "unknown agency"
    amount = _money(baseline.award_amount)
    period = _period_label(baseline.start_date, baseline.end_date)
    return (
        f"{baseline.recipient_name or 'Unknown recipient'} holds {profile.normalized_piid} "
        f"with {agency}; award amount {amount}; POP {period}."
    )


def _obligation_summary(profile: PiidContractIntelligenceProfile) -> str:
    burn = profile.burn_posture
    if burn.net_obligations is None:
        return "Net obligations unavailable in selected PIID profile."
    return (
        f"Net obligations {_money(burn.net_obligations)} across "
        f"{burn.transaction_count} transaction(s); modifications "
        f"{burn.modification_count}; completeness {burn.completeness}."
    )


def _recompete_signals(profile: PiidContractIntelligenceProfile) -> tuple[str, ...]:
    baseline = profile.award_baseline
    burn = profile.burn_posture
    signals: list[str] = []
    if baseline.end_date:
        signals.append(f"POP ends {baseline.end_date}; verify recompete timing.")
    if baseline.solicitation_id:
        signals.append(f"Prior solicitation id {baseline.solicitation_id} is a search pivot.")
    if baseline.parent_idv:
        signals.append(f"Parent vehicle {baseline.parent_idv} may shape recompete route.")
    if burn.modification_count:
        signals.append(
            f"{burn.modification_count} modification(s) may indicate scope or funding changes."
        )
    signals.extend(burn.option_signals)
    if not signals:
        return ("No deterministic recompete signal beyond the selected PIID profile.",)
    return tuple(signals)


def _source_refs(profile: PiidContractIntelligenceProfile) -> tuple[str, ...]:
    refs = [profile.id, profile.normalized_piid]
    if profile.award_baseline.generated_internal_id:
        refs.append(profile.award_baseline.generated_internal_id)
    if profile.award_baseline.permalink:
        refs.append(profile.award_baseline.permalink)
    return tuple(dict.fromkeys(refs))


def _source_limitations(profile: PiidContractIntelligenceProfile) -> tuple[str, ...]:
    limitations = [gap.source_limitation for gap in profile.gaps]
    limitations.append(
        "USAspending source profile does not prove future recompete scope, customer intent, or evaluation strategy."
    )
    return tuple(dict.fromkeys(limitations))


def _route_options(
    request: IncumbentAwardHistoryBriefRequest,
) -> tuple[IncumbentAwardRouteOption, ...]:
    packet_destination = (
        f"Packet Field Answer candidate:{request.packet_field_key}"
        if request.packet_field_key
        else "Packet Field Answer candidate"
    )
    return (
        IncumbentAwardRouteOption(
            route_id="packet_field_answer_candidate",
            destination="Packet Field Answer candidate",
            rationale=f"Use reviewed incumbent facts to support {packet_destination}.",
        ),
        IncumbentAwardRouteOption(
            route_id="capture_research_candidate",
            destination="Capture Research candidate",
            rationale="Route unresolved competitor or customer questions into research.",
        ),
        IncumbentAwardRouteOption(
            route_id="action_plan_recommendation",
            destination="Action Plan recommendation",
            rationale="Create a follow-up to validate incumbent and recompete assumptions.",
        ),
        IncumbentAwardRouteOption(
            route_id="capability_run_output",
            destination="Capability Run Output",
            rationale="Keep as reviewable capability output without downstream writes.",
        ),
    )


def _gaps(
    profile: PiidContractIntelligenceProfile,
    source_limitations: tuple[str, ...],
) -> tuple[str, ...]:
    gaps = [f"Source limitation: {limitation}" for limitation in source_limitations]
    if not profile.award_baseline.recipient_name:
        gaps.append("Incumbent recipient missing from selected PIID profile.")
    return tuple(gaps)


def _period_label(start_date: str | None, end_date: str | None) -> str:
    if start_date and end_date:
        return f"{start_date} to {end_date}"
    if start_date:
        return f"starts {start_date}; end unknown"
    if end_date:
        return f"end {end_date}; start unknown"
    return "unknown"


def _money(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"${value:,.2f}"


def _request_digest(request: IncumbentAwardHistoryBriefRequest) -> str:
    payload = {
        "profile_id": request.piid_profile.id,
        "opportunity_id": request.opportunity_id,
        "packet_field_key": request.packet_field_key,
        "approval_basis": request.approval_basis,
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]