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


class WinThemeSynthesizerRequest(BaseModel):
    opportunity_id: str | None = None
    customer_priorities: tuple[str, ...]
    seller_strengths: tuple[str, ...]
    competitive_gaps: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()


class WinThemeCandidate(BaseModel):
    title: str
    theme_statement: str
    rationale: str
    supporting_inputs: tuple[str, ...]
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]


class WinThemeSynthesis(BaseModel):
    candidates: tuple[WinThemeCandidate, ...]
    review_destination: str = "Capability Run Output"
    review_state: str = "pending_review"
    source_refs: tuple[str, ...]
    trusted_downstream_writes: bool = False


class CompetitiveGapRouteHintRequest(BaseModel):
    opportunity_id: str | None = None
    incumbent_signals: tuple[str, ...]
    seller_baseline_summary: str
    source_refs: tuple[str, ...] = ()
    field_key: str = "competition"


class CompetitiveGapRouteHint(BaseModel):
    field_key: str
    packet_implication: str
    recommended_route: str
    rationale: str
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]
    review_destination: str = "Packet Field Answer candidate"
    review_state: str = "pending_review"
    source_refs: tuple[str, ...]
    trusted_downstream_writes: bool = False


class SubcontractorAssumptionListRequest(BaseModel):
    opportunity_id: str | None = None
    partner_scope_gaps: tuple[str, ...]
    partner_strategy_notes: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()


class SubcontractorAssumptionList(BaseModel):
    assumptions: tuple[str, ...]
    questions: tuple[str, ...]
    route_note: str
    review_destination: str = "Call Plan signal"
    review_state: str = "pending_review"
    source_refs: tuple[str, ...]
    trusted_downstream_writes: bool = False


def build_win_theme_synthesis(
    request: WinThemeSynthesizerRequest,
) -> WinThemeSynthesis:
    priorities = _non_empty(request.customer_priorities)
    strengths = _non_empty(request.seller_strengths)
    gaps = _non_empty(request.competitive_gaps)
    candidates: list[WinThemeCandidate] = []
    for index, priority in enumerate(priorities[:3], start=1):
        strength = strengths[(index - 1) % len(strengths)] if strengths else "seller proof"
        gap = gaps[(index - 1) % len(gaps)] if gaps else "competitive proof gap"
        candidates.append(
            WinThemeCandidate(
                title=f"Theme {index}: {priority[:48]}",
                theme_statement=(
                    f"Position {strength} as direct proof for {priority}, while closing {gap}."
                ),
                rationale=(
                    "Theme pairs one customer priority with one seller strength and one explicit gap."
                ),
                supporting_inputs=(priority, strength, gap),
                assumptions=("Inputs are accepted or reviewable Ariadne context.",),
                gaps=("Reviewer must confirm proof strength before external use.",),
            )
        )
    if not candidates:
        candidates.append(
            WinThemeCandidate(
                title="Theme 1: capture context needed",
                theme_statement="Collect customer priority and seller proof before drafting win themes.",
                rationale="No usable priority input was supplied.",
                supporting_inputs=(),
                assumptions=("No model or broad proposal generator was used.",),
                gaps=("Customer priorities and seller strengths are required.",),
            )
        )
    return WinThemeSynthesis(
        candidates=tuple(candidates),
        source_refs=request.source_refs,
    )


def build_competitive_gap_route_hint(
    request: CompetitiveGapRouteHintRequest,
) -> CompetitiveGapRouteHint:
    signals = _non_empty(request.incumbent_signals)
    signal_summary = signals[0] if signals else "incumbent or competitor signal missing"
    seller_summary = request.seller_baseline_summary.strip() or "seller baseline missing"
    gaps = []
    if not signals:
        gaps.append("Incumbent or competitor signals are missing.")
    if not request.seller_baseline_summary.strip():
        gaps.append("Seller baseline summary is missing.")
    gaps.append("Reviewer must decide whether this implication becomes a packet candidate.")
    return CompetitiveGapRouteHint(
        field_key=request.field_key,
        packet_implication=(
            f"Competition field should compare {signal_summary} against seller baseline: {seller_summary}."
        ),
        recommended_route="Route as packet-field candidate after capture lead review.",
        rationale="Hint converts one competitive signal and seller baseline into one reviewable packet implication.",
        assumptions=("Input signals are reviewable; no live competitor research was run.",),
        gaps=tuple(dict.fromkeys(gaps)),
        source_refs=request.source_refs,
    )


def build_subcontractor_assumption_list(
    request: SubcontractorAssumptionListRequest,
) -> SubcontractorAssumptionList:
    gaps = _non_empty(request.partner_scope_gaps)
    notes = _non_empty(request.partner_strategy_notes)
    assumptions = tuple(
        f"Assume partner input needed for: {gap}." for gap in gaps
    ) or ("Partner scope gaps are not yet defined.",)
    questions = tuple(
        f"Who owns partner answer for {gap}?" for gap in gaps
    ) or ("Which scope areas need partner or subcontractor confirmation?",)
    route_note = "Route assumptions into call-plan prep before SOW or teaming use."
    if notes:
        route_note += f" Strategy note context: {notes[0]}."
    return SubcontractorAssumptionList(
        assumptions=assumptions,
        questions=questions,
        route_note=route_note,
        source_refs=request.source_refs,
    )


def run_win_theme_synthesizer_capability(
    *,
    request: WinThemeSynthesizerRequest,
    store: CapabilityRunStore,
) -> CapabilityRun:
    synthesis = build_win_theme_synthesis(request)
    return _write_skill_run(
        store=store,
        capability_id="win-theme-synthesizer",
        output_id_prefix="output_win_theme_synthesis",
        output_type="win_theme_candidates",
        title="Win theme candidates",
        summary=f"Drafted {len(synthesis.candidates)} reviewable win theme candidate(s).",
        payload_key="win_theme_synthesis",
        payload=synthesis,
        opportunity_id=request.opportunity_id,
        product_workflow="proposal_support",
        review_destination=synthesis.review_destination,
        source_refs=synthesis.source_refs,
        request_payload=request.model_dump(mode="json"),
    )


def run_competitive_gap_route_hint_capability(
    *,
    request: CompetitiveGapRouteHintRequest,
    store: CapabilityRunStore,
) -> CapabilityRun:
    hint = build_competitive_gap_route_hint(request)
    return _write_skill_run(
        store=store,
        capability_id="competitive-gap-route-hint",
        output_id_prefix="output_competitive_gap_route_hint",
        output_type="competitive_gap_route_hint",
        title="Competitive gap route hint",
        summary="Created one reviewable competitive packet implication route.",
        payload_key="competitive_gap_route_hint",
        payload=hint,
        opportunity_id=request.opportunity_id,
        product_workflow="packet_field_routing",
        review_destination=hint.review_destination,
        source_refs=hint.source_refs,
        request_payload=request.model_dump(mode="json"),
    )


def run_subcontractor_assumption_list_capability(
    *,
    request: SubcontractorAssumptionListRequest,
    store: CapabilityRunStore,
) -> CapabilityRun:
    assumption_list = build_subcontractor_assumption_list(request)
    return _write_skill_run(
        store=store,
        capability_id="subcontractor-assumption-list",
        output_id_prefix="output_subcontractor_assumption_list",
        output_type="subcontractor_assumption_list",
        title="Subcontractor assumption list",
        summary=f"Created {len(assumption_list.assumptions)} partner assumption(s) for review.",
        payload_key="subcontractor_assumption_list",
        payload=assumption_list,
        opportunity_id=request.opportunity_id,
        product_workflow="call_plan",
        review_destination=assumption_list.review_destination,
        source_refs=assumption_list.source_refs,
        request_payload=request.model_dump(mode="json"),
    )


def _write_skill_run(
    *,
    store: CapabilityRunStore,
    capability_id: str,
    output_id_prefix: str,
    output_type: str,
    title: str,
    summary: str,
    payload_key: str,
    payload: BaseModel,
    opportunity_id: str | None,
    product_workflow: str,
    review_destination: str,
    source_refs: tuple[str, ...],
    request_payload: dict[str, object],
) -> CapabilityRun:
    completed_at = datetime.now(UTC)
    digest = _digest(capability_id, request_payload)
    output = CapabilityRunOutput(
        output_id=f"{output_id_prefix}_{digest}",
        output_type=output_type,
        title=title,
        summary=summary,
        gaps=tuple(payload.model_dump(mode="json").get("gaps", ())),
        review_state=CapabilityRunOutputReviewState.PENDING,
        autonomy_recommendation=CapabilityRunAutonomyRecommendation.REVIEW_REQUIRED,
        recommended_destination=review_destination,
        provenance={
            "capability_id": capability_id,
            payload_key: payload.model_dump(mode="json"),
            "source_refs": list(source_refs),
            "review_gate_required": True,
            "trusted_downstream_writes": False,
        },
    )
    run = CapabilityRun(
        run_id=f"caprun_{capability_id.replace('-', '_')}_{digest}",
        capability_id=capability_id,
        capability_type=CapabilityRunCapabilityType.SKILL,
        executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
        session_context=CapabilityRunSessionContext.STUDIO,
        opportunity_id=opportunity_id,
        product_workflow=product_workflow,
        status=CapabilityRunStatus.NEEDS_REVIEW,
        inputs_summary=summary,
        input_refs=source_refs,
        outputs=(output,),
        provenance={
            "capability_id": capability_id,
            "executor": CapabilityRunExecutorKind.DETERMINISTIC_PYTHON.value,
            "source_refs": list(source_refs),
            "model_required": False,
            "network_required": False,
            "trusted_downstream_writes": False,
            "completed_at": completed_at.isoformat(),
        },
        completed_at=completed_at,
    )
    return store.write(run)


def _digest(capability_id: str, payload: dict[str, object]) -> str:
    raw = {"capability_id": capability_id, "payload": payload}
    return sha256(json.dumps(raw, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _non_empty(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(value).strip() for value in values if str(value).strip())