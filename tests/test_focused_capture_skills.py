from ariadne.capability_runs import (
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutputReviewState,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.focused_capture_skills import (
    CompetitiveGapRouteHintRequest,
    SubcontractorAssumptionListRequest,
    WinThemeSynthesizerRequest,
    build_competitive_gap_route_hint,
    build_subcontractor_assumption_list,
    build_win_theme_synthesis,
    run_competitive_gap_route_hint_capability,
    run_subcontractor_assumption_list_capability,
    run_win_theme_synthesizer_capability,
)


def test_win_theme_synthesizer_creates_reviewable_candidates() -> None:
    synthesis = build_win_theme_synthesis(_win_theme_request())

    assert len(synthesis.candidates) == 2
    assert synthesis.review_destination == "Capability Run Output"
    assert synthesis.trusted_downstream_writes is False
    assert "mission continuity" in synthesis.candidates[0].theme_statement
    assert synthesis.candidates[0].gaps == (
        "Reviewer must confirm proof strength before external use.",
    )


def test_competitive_gap_route_hint_creates_packet_candidate_route() -> None:
    hint = build_competitive_gap_route_hint(_competitive_gap_request())

    assert hint.field_key == "competition"
    assert hint.review_destination == "Packet Field Answer candidate"
    assert hint.trusted_downstream_writes is False
    assert "Incumbent has strong transition story" in hint.packet_implication
    assert "Reviewer must decide" in hint.gaps[-1]


def test_subcontractor_assumption_list_creates_call_plan_signal() -> None:
    assumption_list = build_subcontractor_assumption_list(_subcontractor_request())

    assert assumption_list.review_destination == "Call Plan signal"
    assert assumption_list.trusted_downstream_writes is False
    assert assumption_list.assumptions == (
        "Assume partner input needed for: cleared help desk staffing.",
        "Assume partner input needed for: CONUS site coverage.",
    )
    assert assumption_list.questions[0] == (
        "Who owns partner answer for cleared help desk staffing?"
    )


def test_focused_capture_skill_runs_stay_review_gated(tmp_path) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    win_run = run_win_theme_synthesizer_capability(
        request=_win_theme_request(),
        store=store,
    )
    gap_run = run_competitive_gap_route_hint_capability(
        request=_competitive_gap_request(),
        store=store,
    )
    subcontractor_run = run_subcontractor_assumption_list_capability(
        request=_subcontractor_request(),
        store=store,
    )

    assert {run.capability_id for run in (win_run, gap_run, subcontractor_run)} == {
        "win-theme-synthesizer",
        "competitive-gap-route-hint",
        "subcontractor-assumption-list",
    }
    for run in (win_run, gap_run, subcontractor_run):
        assert run.capability_type is CapabilityRunCapabilityType.SKILL
        assert run.executor_kind is CapabilityRunExecutorKind.DETERMINISTIC_PYTHON
        assert run.status is CapabilityRunStatus.NEEDS_REVIEW
        assert run.outputs[0].review_state is CapabilityRunOutputReviewState.PENDING
        assert run.provenance["model_required"] is False
        assert run.provenance["network_required"] is False
        assert run.provenance["trusted_downstream_writes"] is False
    assert len(store.list()) == 3


def _win_theme_request() -> WinThemeSynthesizerRequest:
    return WinThemeSynthesizerRequest(
        opportunity_id="opp-focused-skills",
        customer_priorities=("mission continuity", "fast transition"),
        seller_strengths=("incumbent transition team", "ISO-certified delivery"),
        competitive_gaps=("weak proof for surge staffing",),
        source_refs=("packet://customer-priorities",),
    )


def _competitive_gap_request() -> CompetitiveGapRouteHintRequest:
    return CompetitiveGapRouteHintRequest(
        opportunity_id="opp-focused-skills",
        incumbent_signals=("Incumbent has strong transition story",),
        seller_baseline_summary="Seller has stronger automation proof but needs staffing proof.",
        source_refs=("source-profile://piid/FA123",),
    )


def _subcontractor_request() -> SubcontractorAssumptionListRequest:
    return SubcontractorAssumptionListRequest(
        opportunity_id="opp-focused-skills",
        partner_scope_gaps=("cleared help desk staffing", "CONUS site coverage"),
        partner_strategy_notes=("Prefer small-business partner for regional coverage",),
        source_refs=("packet://partner-strategy",),
    )