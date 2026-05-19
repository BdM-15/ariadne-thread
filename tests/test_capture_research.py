import pytest

from ariadne.capture_research import (
    CapabilityProvenance,
    CaptureResearchLens,
    CaptureResearchRunStatus,
    CaptureResearchStore,
    CaptureResearchSourceMode,
    FakeWebSourceCollectionAdapter,
    SourceCollectionProviderManifest,
    SourceCollectionQualityStatus,
    SourceProviderSmokeCheckStatus,
    SourceProviderSmokeRunnerResult,
    SourceProfileRef,
    SourceProfileType,
    SellerBaselineRefType,
    SourceFinding,
    WebSourceCollectionRecord,
    build_source_provider_registry,
    create_source_provider_adapter,
    create_source_context_research_run,
    create_user_prompted_research_run,
    run_approved_source_provider_collection,
    run_requirements_fit_analysis,
    run_source_provider_smoke_check,
    run_web_source_collection,
)
from ariadne.evidence import create_source_evidence
from ariadne.reference_wiki import ReferenceInfluenceType, ReferenceWikiInfluence


class _ProviderFixtureAdapter:
    source_mode = CaptureResearchSourceMode.LIVE_OLOSTEP
    provider_ids = ("serpapi_live", "olostep_live")

    def collect(
        self,
        run,
        *,
        collected_at: str,
    ) -> tuple[tuple[WebSourceCollectionRecord, ...], tuple[SourceFinding, ...]]:
        provenance = CapabilityProvenance(
            source_capability_id="serpapi_live+olostep_live",
            source_tool_name="collect_provider_backed_public_sources",
            source_package="ariadne.capture_research",
            source_package_version="local",
        )
        limitations = (
            "SerpApi supplies search discovery; Olostep supplies crawl/extraction fallback.",
            "Automated test uses injected provider fixture data.",
        )
        findings = tuple(
            SourceFinding(
                id=f"source_finding_fixture_{index}",
                source_target=source_target,
                url=f"https://example.test/{index}",
                title=f"Provider finding for {source_target}",
                source_type="provider_backed_public_web",
                collected_at=collected_at,
                excerpt=f"Provider-backed excerpt for {source_target}.",
                confidence=0.74,
                source_limitations=limitations,
                source_mode=self.source_mode,
                capability_provenance=provenance,
                provider_ids=self.provider_ids,
                approval_basis=run.research_brief.approval_basis,
            )
            for index, source_target in enumerate(
                run.research_brief.source_targets, start=1
            )
        )
        records = tuple(
            WebSourceCollectionRecord(
                id=f"web_collection_fixture_{index}",
                source_target=finding.source_target,
                source_mode=self.source_mode,
                collected_at=collected_at,
                capability_provenance=provenance,
                source_limitations=limitations,
                finding_ids=(finding.id,),
                provider_ids=self.provider_ids,
                approval_basis=run.research_brief.approval_basis,
            )
            for index, finding in enumerate(findings, start=1)
        )
        return records, findings


class _ProviderHttpFixture:
    def __init__(self) -> None:
        self.get_urls: list[str] = []
        self.post_payloads: list[dict[str, object]] = []

    def get_json(self, url: str, *, headers: dict[str, str]) -> dict[str, object]:
        self.get_urls.append(url)
        assert headers == {}
        return {
            "organic_results": [
                {
                    "title": "Program office modernization page",
                    "link": "https://example.gov/program-office",
                    "snippet": "Public agency page discovered by search.",
                }
            ]
        }

    def post_json(
        self, url: str, *, headers: dict[str, str], payload: dict[str, object]
    ) -> dict[str, object]:
        self.post_payloads.append(payload)
        assert url == "https://api.olostep.com/v1/scrapes"
        assert headers["Authorization"] == "Bearer olostep-secret"
        return {
            "result": {
                "markdown_content": "# Program Office\n\nMission needs and public buying context.",
                "page_metadata": {"title": "Program Office"},
            }
        }


class _SmokeRunnerFixture:
    def __init__(self) -> None:
        self.provider_ids: list[str] = []

    def __call__(
        self,
        manifest: SourceCollectionProviderManifest,
        *,
        env: dict[str, str],
        smoke_target: str,
        timeout_seconds: int,
    ) -> SourceProviderSmokeRunnerResult:
        self.provider_ids.append(manifest.id)
        return SourceProviderSmokeRunnerResult(
            ok=True,
            diagnostic_summary="smoke ok " + " ".join(env.values()),
            endpoint_label=f"{manifest.id}_smoke",
            observed_result_count=1,
        )


def test_source_provider_registry_reports_quality_without_secret_values() -> None:
    registry = build_source_provider_registry(
        {
            "SERPAPI_API_KEY": "serpapi-secret",
            "OLOSTEP_API_KEY": "olostep-secret",
        }
    )

    assert registry.quality_status is SourceCollectionQualityStatus.FULL_READY
    assert registry.recommended_provider_ids == ("serpapi_live", "olostep_live")
    available_provider_ids = tuple(
        provider.provider_id
        for provider in registry.providers
        if provider.status == "available"
    )
    assert available_provider_ids == ("serpapi_live", "olostep_live")
    dumped = registry.model_dump_json()
    assert "serpapi-secret" not in dumped
    assert "olostep-secret" not in dumped
    assert "SERPAPI_API_KEY" in dumped
    assert "OLOSTEP_API_KEY" in dumped


def test_source_provider_smoke_check_covers_all_providers_without_secret_values() -> None:
    env = {
        "CRAWL4AI_BASE_URL": "http://localhost:11235/private",
        "SEARXNG_BASE_URL": "http://localhost:8080/private",
        "SERPAPI_API_KEY": "serpapi-secret",
        "OLOSTEP_API_KEY": "olostep-secret",
        "FIRECRAWL_API_KEY": "firecrawl-secret",
    }
    runner = _SmokeRunnerFixture()

    results = tuple(
        run_source_provider_smoke_check(
            provider_id=provider_id,
            env=env,
            approved=True,
            smoke_target="https://example.com",
            runner=runner,
            checked_at="2026-05-19T10:00:00+00:00",
        )
        for provider_id in (
            "crawl4ai_local",
            "searxng_local",
            "serpapi_live",
            "olostep_live",
            "firecrawl_live",
        )
    )

    assert runner.provider_ids == [
        "crawl4ai_local",
        "searxng_local",
        "serpapi_live",
        "olostep_live",
        "firecrawl_live",
    ]
    assert all(result.status is SourceProviderSmokeCheckStatus.SUCCESS for result in results)
    dumped = "\n".join(result.model_dump_json() for result in results)
    assert "http://localhost:11235/private" not in dumped
    assert "http://localhost:8080/private" not in dumped
    assert "serpapi-secret" not in dumped
    assert "olostep-secret" not in dumped
    assert "firecrawl-secret" not in dumped
    assert "CRAWL4AI_BASE_URL" in dumped
    assert "FIRECRAWL_API_KEY" in dumped


def test_source_provider_smoke_check_requires_config_and_approval() -> None:
    runner = _SmokeRunnerFixture()

    missing_config = run_source_provider_smoke_check(
        provider_id="crawl4ai_local",
        env={},
        approved=True,
        smoke_target="https://example.com",
        runner=runner,
        checked_at="2026-05-19T10:00:00+00:00",
    )
    requires_approval = run_source_provider_smoke_check(
        provider_id="serpapi_live",
        env={"SERPAPI_API_KEY": "serpapi-secret"},
        approved=False,
        smoke_target="https://example.com",
        runner=runner,
        checked_at="2026-05-19T10:00:00+00:00",
    )

    assert missing_config.status is SourceProviderSmokeCheckStatus.MISSING_ENV
    assert missing_config.missing_env_vars == ("CRAWL4AI_BASE_URL",)
    assert requires_approval.status is SourceProviderSmokeCheckStatus.REQUIRES_APPROVAL
    assert runner.provider_ids == []
    assert "serpapi-secret" not in requires_approval.model_dump_json()


def test_approved_source_provider_collection_records_provider_provenance(
    tmp_path,
) -> None:
    run = create_user_prompted_research_run(
        "Research public customer context with provider-backed collection.",
        opportunity_id="opp_aflcmc_recompete",
        selected_lenses=(CaptureResearchLens.CUSTOMER_RESEARCH,),
        source_targets=("https://example.gov/program-office",),
        source_limits=("public_web_only",),
        evidence_goals=("Find customer mission and incumbent signals.",),
        created_at="2026-05-18T12:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")
    store.write(run)
    registry = build_source_provider_registry(
        {
            "SERPAPI_API_KEY": "serpapi-secret",
            "OLOSTEP_API_KEY": "olostep-secret",
        }
    )

    collected = run_approved_source_provider_collection(
        store=store,
        research_run_id=run.research_run_id,
        registry=registry,
        adapter=_ProviderFixtureAdapter(),
        approved=True,
        collected_at="2026-05-18T12:05:00+00:00",
    )

    assert collected.status is CaptureResearchRunStatus.NEEDS_REVIEW
    record = collected.source_collection_records[0]
    finding = collected.source_findings[0]
    assert record.source_mode is CaptureResearchSourceMode.LIVE_OLOSTEP
    assert record.provider_ids == ("serpapi_live", "olostep_live")
    assert record.approval_basis == "user_triggered"
    assert finding.provider_ids == ("serpapi_live", "olostep_live")
    assert finding.approval_basis == "user_triggered"
    assert finding.capability_provenance.source_capability_id == (
        "serpapi_live+olostep_live"
    )
    dumped = collected.model_dump_json()
    assert "serpapi-secret" not in dumped
    assert "olostep-secret" not in dumped


def test_default_provider_adapter_composes_search_and_extraction_without_live_network(
    tmp_path,
) -> None:
    run = create_user_prompted_research_run(
        "Research public customer context with provider-backed collection.",
        opportunity_id="opp_aflcmc_recompete",
        selected_lenses=(CaptureResearchLens.CUSTOMER_RESEARCH,),
        source_targets=("example agency program office modernization",),
        source_limits=("public_web_only",),
        evidence_goals=("Find customer mission and incumbent signals.",),
        created_at="2026-05-18T12:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")
    store.write(run)
    env = {
        "SERPAPI_API_KEY": "serpapi-secret",
        "OLOSTEP_API_KEY": "olostep-secret",
    }
    registry = build_source_provider_registry(env)
    http_fixture = _ProviderHttpFixture()

    collected = run_approved_source_provider_collection(
        store=store,
        research_run_id=run.research_run_id,
        registry=registry,
        adapter=create_source_provider_adapter(
            env=env,
            registry=registry,
            http_client=http_fixture,
        ),
        approved=True,
        collected_at="2026-05-18T12:05:00+00:00",
    )

    assert "serpapi-secret" in http_fixture.get_urls[0]
    assert http_fixture.post_payloads == [
        {
            "url_to_scrape": "https://example.gov/program-office",
            "formats": ["markdown"],
            "remove_css_selectors": "default",
        }
    ]
    finding = collected.source_findings[0]
    assert finding.source_mode is CaptureResearchSourceMode.LIVE_OLOSTEP
    assert finding.provider_ids == ("serpapi_live", "olostep_live")
    assert finding.title == "Program Office"
    assert finding.excerpt == "# Program Office Mission needs and public buying context."
    assert finding.source_type == "serpapi_discovered_olostep_scraped_public_web"
    dumped = collected.model_dump_json()
    assert "serpapi-secret" not in dumped
    assert "olostep-secret" not in dumped


def test_source_provider_collection_rejects_missing_approval_and_config(
    tmp_path,
) -> None:
    run = create_user_prompted_research_run(
        "Research public customer context with provider-backed collection.",
        opportunity_id="opp_aflcmc_recompete",
        selected_lenses=(CaptureResearchLens.CUSTOMER_RESEARCH,),
        source_targets=("https://example.gov/program-office",),
        source_limits=("public_web_only",),
        evidence_goals=("Find customer mission and incumbent signals.",),
        created_at="2026-05-18T12:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")
    store.write(run)

    with pytest.raises(ValueError, match="requires explicit approval"):
        run_approved_source_provider_collection(
            store=store,
            research_run_id=run.research_run_id,
            registry=build_source_provider_registry(
                {
                    "SERPAPI_API_KEY": "serpapi-secret",
                    "OLOSTEP_API_KEY": "olostep-secret",
                }
            ),
            adapter=_ProviderFixtureAdapter(),
            approved=False,
        )

    with pytest.raises(ValueError, match="no eligible source collection provider"):
        run_approved_source_provider_collection(
            store=store,
            research_run_id=run.research_run_id,
            registry=build_source_provider_registry({}),
            adapter=_ProviderFixtureAdapter(),
            approved=True,
        )


def test_source_provider_collection_rejects_restricted_targets(tmp_path) -> None:
    run = create_user_prompted_research_run(
        "Research customer chatter in a restricted platform.",
        opportunity_id="opp_aflcmc_recompete",
        selected_lenses=(CaptureResearchLens.CUSTOMER_RESEARCH,),
        source_targets=("https://linkedin.com/company/example-agency",),
        source_limits=("public_web_only",),
        evidence_goals=("Find public customer signals.",),
        created_at="2026-05-18T12:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")
    store.write(run)

    with pytest.raises(ValueError, match="restricted or logged-in"):
        run_approved_source_provider_collection(
            store=store,
            research_run_id=run.research_run_id,
            registry=build_source_provider_registry(
                {
                    "SERPAPI_API_KEY": "serpapi-secret",
                    "OLOSTEP_API_KEY": "olostep-secret",
                }
            ),
            adapter=_ProviderFixtureAdapter(),
            approved=True,
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
    assert "Fake adapter test data is not live source-provider success." in (
        first_finding.source_limitations
    )
    assert "live_firecrawl" not in reloaded.model_dump_json()


def test_requirements_fit_attaches_seller_baseline_refs_and_candidates(
    tmp_path,
) -> None:
    run = create_user_prompted_research_run(
        "Research customer transition and modernization requirements.",
        opportunity_id="opp_aflcmc_recompete",
        selected_lenses=(
            CaptureResearchLens.CUSTOMER_RESEARCH,
            CaptureResearchLens.COMPETITIVE_POSITIONING,
        ),
        source_targets=("public agency modernization page",),
        source_limits=("public_web_only",),
        evidence_goals=("Compare customer transition needs with seller proof.",),
        created_at="2026-05-18T12:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")
    store.write(
        run.model_copy(
            update={
                "source_findings": (
                    _requirements_fit_source_finding(
                        "Customer requires transition proof and cyber modernization support."
                    ),
                ),
            }
        )
    )
    evidence = create_source_evidence(
        evidence_id="ev_seller_transition_proof",
        content=(
            "Seller capability evidence: Air Force transition past performance, "
            "cyber modernization capability, and relevant contract vehicle proof."
        ),
        source_ref="accepted seller capability note",
        opportunity_id="opp_aflcmc_recompete",
    )
    reference = ReferenceWikiInfluence(
        title="Project Ariadne seller baseline",
        reference_id="seller/baseline",
        source_path="seller/baseline.md",
        excerpt="Reference note about transition and modernization proof.",
        why_it_matters="Shows reusable seller proof for transition and modernization.",
        influence_type=ReferenceInfluenceType.DOMAIN_INTEL,
        score=8.0,
        matched_terms=("transition", "modernization"),
    )

    analyzed = run_requirements_fit_analysis(
        store=store,
        research_run_id=run.research_run_id,
        evidence_items=(evidence,),
        reference_influences=(reference,),
        analyzed_at="2026-05-18T12:10:00+00:00",
    )

    assert analyzed.status is CaptureResearchRunStatus.NEEDS_REVIEW
    assert [ref.ref_type for ref in analyzed.seller_baseline_refs] == [
        SellerBaselineRefType.ACCEPTED_EVIDENCE,
        SellerBaselineRefType.REFERENCE_WIKI_NOTE,
    ]
    assert analyzed.seller_baseline_refs[0].source_ref == "ev_seller_transition_proof"
    assert analyzed.seller_baseline_refs[0].summarized_support
    assert analyzed.seller_baseline_refs[0].assumptions
    assert analyzed.seller_baseline_refs[1].baseline_gaps
    assert analyzed.requirements_fit_analysis is not None
    analysis = analyzed.requirements_fit_analysis
    assert analysis.strengths
    assert analysis.proof_needs
    assert analysis.seller_baseline_ref_ids == tuple(
        ref.id for ref in analyzed.seller_baseline_refs
    )
    assert analysis.source_finding_ids == ("source_finding_customer_transition",)
    assert analyzed.insight_candidates
    assert all(
        candidate["review_state"] == "pending_review"
        for candidate in analyzed.insight_candidates
    )
    assert all(
        candidate["autonomy_tier"] == "review_required"
        for candidate in analyzed.insight_candidates
    )
    dumped = analyzed.model_dump_json()
    assert "derived_from_ids" not in dumped
    assert "trusted_output_written" not in dumped


def test_requirements_fit_surfaces_missing_seller_baseline_gap(tmp_path) -> None:
    run = create_user_prompted_research_run(
        "Research customer requirements before seller proof exists.",
        opportunity_id="opp_new_customer",
        selected_lenses=(CaptureResearchLens.CUSTOMER_RESEARCH,),
        source_targets=("public customer page",),
        source_limits=("public_web_only",),
        evidence_goals=("Find mission needs and proof gaps.",),
        created_at="2026-05-18T12:00:00+00:00",
    )
    store = CaptureResearchStore(tmp_path / "capture-research")
    store.write(run)

    analyzed = run_requirements_fit_analysis(
        store=store,
        research_run_id=run.research_run_id,
        evidence_items=(),
        reference_influences=(),
        analyzed_at="2026-05-18T12:10:00+00:00",
    )

    assert analyzed.seller_baseline_refs[0].ref_type is SellerBaselineRefType.BASELINE_GAP
    assert analyzed.seller_baseline_refs[0].baseline_gaps
    assert analyzed.requirements_fit_analysis is not None
    analysis = analyzed.requirements_fit_analysis
    assert not analysis.strengths
    assert analysis.weaknesses
    assert analysis.qualification_risks
    assert analysis.proof_needs
    assert {candidate["target_workflow"] for candidate in analyzed.insight_candidates} >= {
        "action_plan",
        "risk_register",
    }


def _requirements_fit_source_finding(excerpt: str) -> SourceFinding:
    return SourceFinding(
        id="source_finding_customer_transition",
        source_target="public agency modernization page",
        url="https://example.gov/modernization",
        title="Customer modernization page",
        source_type="fake_public_web",
        collected_at="2026-05-18T12:05:00+00:00",
        excerpt=excerpt,
        confidence=0.7,
        source_limitations=("Fake adapter test data is not live source-provider success.",),
        source_mode=CaptureResearchSourceMode.FAKE_ADAPTER_TEST,
        capability_provenance=CapabilityProvenance(
            source_capability_id="fake_web_source_collection",
            source_tool_name="collect_fake_public_sources",
            source_package="ariadne.capture_research",
            source_package_version="local",
        ),
    )