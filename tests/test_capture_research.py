from ariadne.capture_research import (
    CaptureResearchLens,
    CaptureResearchRunStatus,
    CaptureResearchStore,
    create_user_prompted_research_run,
)


def test_creates_user_prompted_research_run_from_bounded_prompt(tmp_path) -> None:
    run = create_user_prompted_research_run(
        "Research the customer's historical use of this contract vehicle.",
        opportunity_id="opp_aflcmc_recompete",
        selected_lenses=(
            CaptureResearchLens.CUSTOMER_RESEARCH,
            CaptureResearchLens.CALL_PLAN_CRO,
        ),
        source_targets=("public customer website",),
        source_limits=("public_web_only", "no_linkedin"),
        evidence_goals=("Find customer hot buttons and engagement questions.",),
        created_at="2026-05-18T10:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")

    store.write(run)
    reloaded = CaptureResearchStore(tmp_path / "capture-research").read(
        run.research_run_id
    )

    assert reloaded.research_run_id == run.research_run_id
    assert reloaded.status is CaptureResearchRunStatus.PLANNED
    assert reloaded.opportunity_id == "opp_aflcmc_recompete"
    assert reloaded.user_prompt is not None
    assert reloaded.user_prompt.prompt == (
        "Research the customer's historical use of this contract vehicle."
    )
    assert reloaded.user_prompt.source_limits == ("public_web_only", "no_linkedin")
    assert reloaded.research_trigger_context.trigger_type == (
        "user_prompted_research_request"
    )
    assert reloaded.research_brief.research_question == reloaded.user_prompt.prompt
    assert reloaded.research_brief.selected_lenses == (
        CaptureResearchLens.CUSTOMER_RESEARCH,
        CaptureResearchLens.CALL_PLAN_CRO,
    )
    assert reloaded.research_brief.source_targets == ("public customer website",)
    assert reloaded.research_brief.source_limits == (
        "public_web_only",
        "no_linkedin",
    )
    assert reloaded.research_brief.evidence_goals == (
        "Find customer hot buttons and engagement questions.",
    )
    assert reloaded.created_at == "2026-05-18T10:00:00+00:00"
    assert reloaded.updated_at == "2026-05-18T10:00:00+00:00"
    assert reloaded.source_collection_records == ()
    assert reloaded.source_findings == ()
    assert reloaded.capability_run_refs == ()