from ariadne.capture_research import (
    CaptureResearchLens,
    CaptureResearchRunStatus,
    CaptureResearchStore,
    CaptureResearchSourceMode,
    FakeWebSourceCollectionAdapter,
    SourceProfileRef,
    SourceProfileType,
    create_source_context_research_run,
    create_user_prompted_research_run,
    run_web_source_collection,
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


def test_creates_source_profile_research_run_with_refs_not_snapshots(tmp_path) -> None:
    piid_ref = SourceProfileRef(
        source_profile_type=SourceProfileType.PIID_CONTRACT_INTELLIGENCE_PROFILE,
        source_profile_id="piid_profile_FA8650_23_F_0001",
        source_element_key="gaps.prime_recipient",
        source_element_summary="PIID profile cannot resolve PRIME recipient from USAspending fixture.",
    )
    sam_ref = SourceProfileRef(
        source_profile_type=SourceProfileType.SAM_GOV_ENRICHMENT_PROFILE,
        source_profile_id="sam_profile_PROJECT_PHOENIX",
        source_element_key="opportunity_discovery.ambiguous_program_name",
        source_element_summary="SAM.gov discovery found ambiguous Project Phoenix notices.",
    )
    run = create_source_context_research_run(
        "Resolve incumbent/customer ambiguity before packet update.",
        opportunity_id="opp_aflcmc_recompete",
        source_profile_refs=(piid_ref, sam_ref),
        prompt="Research which public sources clarify the incumbent and buyer office.",
        selected_lenses=(CaptureResearchLens.CUSTOMER_RESEARCH,),
        source_targets=("public agency pages", "public award notices"),
        source_limits=("public_web_only",),
        evidence_goals=("Clarify buyer office and incumbent signals.",),
        created_at="2026-05-18T11:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")

    store.write(run)
    reloaded = store.read(run.research_run_id)

    assert reloaded.research_trigger_context.trigger_type == "source_profile_context"
    assert reloaded.research_trigger_context.summary == (
        "Resolve incumbent/customer ambiguity before packet update."
    )
    assert reloaded.user_prompt is not None
    assert reloaded.user_prompt.prompt == (
        "Research which public sources clarify the incumbent and buyer office."
    )
    assert reloaded.source_profile_refs == (piid_ref, sam_ref)
    assert reloaded.research_brief.source_targets == (
        "public agency pages",
        "public award notices",
    )
    dumped = reloaded.model_dump_json()
    assert "award_baseline" not in dumped
    assert "burn_posture" not in dumped
    assert "entity_matches" not in dumped
    assert "opportunity_records" not in dumped
    assert "attachment_metadata" not in dumped


def test_fake_web_source_collection_persists_records_and_findings(tmp_path) -> None:
    run = create_user_prompted_research_run(
        "Research public customer and incumbent context.",
        opportunity_id="opp_aflcmc_recompete",
        selected_lenses=(CaptureResearchLens.CUSTOMER_RESEARCH,),
        source_targets=("public agency pages", "public award notices"),
        source_limits=("public_web_only",),
        evidence_goals=("Find customer and incumbent signals.",),
        created_at="2026-05-18T12:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")
    store.write(run)

    collected = run_web_source_collection(
        store=store,
        research_run_id=run.research_run_id,
        adapter=FakeWebSourceCollectionAdapter(),
        collected_at="2026-05-18T12:05:00+00:00",
    )
    reloaded = store.read(run.research_run_id)

    assert collected == reloaded
    assert reloaded.status is CaptureResearchRunStatus.NEEDS_REVIEW
    assert [record.source_target for record in reloaded.source_collection_records] == [
        "public agency pages",
        "public award notices",
    ]
    assert all(
        record.source_mode is CaptureResearchSourceMode.FAKE_ADAPTER_TEST
        for record in reloaded.source_collection_records
    )
    assert len(reloaded.source_findings) == 2
    first_finding = reloaded.source_findings[0]
    assert first_finding.source_target == "public agency pages"
    assert first_finding.url == "fake://capture-research/public-agency-pages"
    assert first_finding.title == "Fake source finding for public agency pages"
    assert first_finding.source_type == "fake_public_web"
    assert first_finding.collected_at == "2026-05-18T12:05:00+00:00"
    assert first_finding.confidence == 0.42
    assert first_finding.source_mode is CaptureResearchSourceMode.FAKE_ADAPTER_TEST
    assert first_finding.capability_provenance.source_capability_id == (
        "fake_web_source_collection"
    )
    assert first_finding.capability_provenance.source_tool_name == (
        "collect_fake_public_sources"
    )
    assert "Fake adapter test data is not live Firecrawl source success." in (
        first_finding.source_limitations
    )
    assert "live_firecrawl" not in reloaded.model_dump_json()