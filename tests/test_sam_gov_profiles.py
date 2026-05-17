from ariadne.sam_gov_profiles import (
    SamGovEntityLookupProvenance,
    SamGovEntityLookupResult,
    SamGovEntityLookupStatus,
    SamGovEntityMatch,
    SamGovHermesEventType,
    SamGovMcpToolResult,
    SamGovProfileStore,
    SamGovReviewCandidateType,
    SamGovReviewState,
    SamGovSourceMode,
    create_sam_gov_enrichment_profile,
    record_sam_gov_review_decision,
    resolve_sam_gov_entity_lookup,
)


def test_creates_sam_gov_profile_from_fake_entity_lookup_result() -> None:
    lookup = SamGovEntityLookupResult(
        input_pivot=" UEIACME12345 ",
        normalized_pivot="UEIACME12345",
        pivot_type="uei",
        status=SamGovEntityLookupStatus.SUCCESS,
        provenance=SamGovEntityLookupProvenance(
            source_package="sam-gov-mcp",
            source_package_version="0.4.1",
            checked_at="2026-05-17T15:00:00Z",
            source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        ),
        matches=(
            SamGovEntityMatch(
                uei="UEIACME12345",
                legal_business_name="ACME FEDERAL LLC",
                cage_code="1ABC2",
                registration_status="Active",
                parent_uei="UEIPARENT9999",
                parent_legal_business_name="ACME HOLDING CORPORATION",
                business_types=("Small Business", "Woman Owned Business"),
                naics_codes=("541715",),
                psc_codes=("AC13",),
                responsibility_notes=("No active exclusion reported by fixture.",),
            ),
        ),
        source_limitations=(
            "SAM.gov entity data is an official registration signal, not a complete capability picture.",
        ),
        diagnostic_summary="Fake adapter resolved one SAM.gov entity record.",
    )

    profile = create_sam_gov_enrichment_profile(
        lookup,
        profile_id="sam_profile_UEIACME12345",
        created_at="2026-05-17T15:05:00Z",
    )

    assert profile.id == "sam_profile_UEIACME12345"
    assert profile.input_pivot == " UEIACME12345 "
    assert profile.normalized_pivot == "UEIACME12345"
    assert profile.entity_lane is not None
    assert profile.entity_lane.provenance.source_mode is SamGovSourceMode.FAKE_ADAPTER_TEST
    assert profile.entity_lane.matches[0].legal_business_name == "ACME FEDERAL LLC"
    assert profile.entity_lane.matches[0].parent_uei == "UEIPARENT9999"
    assert profile.entity_lane.source_limitations == lookup.source_limitations

    candidate_types = {candidate.candidate_type for candidate in profile.review_candidates}
    assert {
        SamGovReviewCandidateType.SOURCE_EVIDENCE,
        SamGovReviewCandidateType.PACKET_FIELD_ANSWER,
        SamGovReviewCandidateType.ACTION_PLAN_ITEM,
        SamGovReviewCandidateType.RISK_REGISTER_SIGNAL,
        SamGovReviewCandidateType.CALL_PLAN_SIGNAL,
    } <= candidate_types
    assert all(
        candidate.review_state is SamGovReviewState.PENDING_REVIEW
        for candidate in profile.review_candidates
    )
    assert all(
        candidate.trusted_output_written is False
        for candidate in profile.review_candidates
    )

    event_types = {event.event_type for event in profile.hermes_events}
    assert {
        SamGovHermesEventType.PROFILE_STARTED,
        SamGovHermesEventType.ENTITY_RECORD_RESOLVED,
        SamGovHermesEventType.REVIEW_CANDIDATES_CREATED,
    } <= event_types


def test_sam_gov_profile_store_persists_and_finds_profiles_by_pivot(tmp_path) -> None:
    lookup = SamGovEntityLookupResult(
        input_pivot="Acme Federal",
        normalized_pivot="ACME FEDERAL",
        pivot_type="legal_business_name",
        status=SamGovEntityLookupStatus.AMBIGUOUS,
        provenance=SamGovEntityLookupProvenance(
            source_tool_name="search_entities",
            source_package="sam-gov-mcp",
            source_package_version="0.4.1",
            checked_at="2026-05-17T15:10:00Z",
            source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        ),
        matches=(
            SamGovEntityMatch(
                uei="UEIACME12345",
                legal_business_name="ACME FEDERAL LLC",
            ),
            SamGovEntityMatch(
                uei="UEIACMESUB9",
                legal_business_name="ACME FEDERAL SUBSIDIARY LLC",
            ),
        ),
        source_limitations=("Multiple SAM.gov entity matches require review.",),
        diagnostic_summary="Fake adapter returned two possible entity matches.",
    )
    profile = create_sam_gov_enrichment_profile(
        lookup,
        profile_id="sam_profile_ACME_FEDERAL",
        created_at="2026-05-17T15:12:00Z",
    )

    store = SamGovProfileStore(tmp_path / "sam-gov-profiles")
    stored = store.write(profile)

    assert stored == profile
    assert store.read("sam_profile_ACME_FEDERAL") == profile
    assert store.list() == [profile]
    assert store.find_by_normalized_pivot(" acme federal ") == [profile]


def test_sam_gov_review_decision_records_event_without_trusted_write() -> None:
    profile = create_sam_gov_enrichment_profile(
        SamGovEntityLookupResult(
            input_pivot="UEIACME12345",
            normalized_pivot="UEIACME12345",
            pivot_type="uei",
            status=SamGovEntityLookupStatus.SUCCESS,
            provenance=SamGovEntityLookupProvenance(
                source_package="sam-gov-mcp",
                source_package_version="0.4.1",
                checked_at="2026-05-17T15:20:00Z",
                source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
            ),
            matches=(
                SamGovEntityMatch(
                    uei="UEIACME12345",
                    legal_business_name="ACME FEDERAL LLC",
                ),
            ),
            diagnostic_summary="Fake adapter resolved one SAM.gov entity record.",
        ),
        profile_id="sam_profile_UEIACME12345",
        created_at="2026-05-17T15:22:00Z",
    )
    source_candidate = next(
        candidate
        for candidate in profile.review_candidates
        if candidate.candidate_type is SamGovReviewCandidateType.SOURCE_EVIDENCE
    )

    updated_profile = record_sam_gov_review_decision(
        profile,
        candidate_id=source_candidate.id,
        review_state=SamGovReviewState.ACCEPTED,
        reviewer_rationale="Entity identity is useful, but fake data cannot become trusted evidence.",
        decided_at="2026-05-17T15:25:00Z",
    )

    accepted_candidate = next(
        candidate
        for candidate in updated_profile.review_candidates
        if candidate.id == source_candidate.id
    )
    assert accepted_candidate.review_state is SamGovReviewState.ACCEPTED
    assert accepted_candidate.trusted_output_written is False
    assert updated_profile.updated_at == "2026-05-17T15:25:00Z"
    assert updated_profile.hermes_events[-1].event_type is (
        SamGovHermesEventType.REVIEW_DECISION_RECORDED
    )
    assert updated_profile.hermes_events[-1].payload["candidate_id"] == (
        source_candidate.id
    )
    assert updated_profile.hermes_events[-1].payload["trusted_output_written"] is False


def test_resolves_sam_gov_entity_lookup_by_uei_with_fake_runner() -> None:
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "entityRegistration": {
                    "uei": "UEIACME12345",
                    "legalBusinessName": "ACME FEDERAL LLC",
                    "cageCode": "1ABC2",
                    "registrationStatus": "Active",
                },
                "coreData": {
                    "businessTypes": ["Small Business", "Woman Owned Business"],
                    "entityHierarchy": {
                        "parentUei": "UEIPARENT9999",
                        "parentLegalBusinessName": "ACME HOLDING CORPORATION",
                    },
                },
                "assertions": {
                    "naicsCodes": ["541715"],
                    "pscCodes": ["AC13"],
                },
            },
        )

    lookup = resolve_sam_gov_entity_lookup(
        " ueiacme12345 ",
        runner=runner,
        source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        checked_at="2026-05-17T15:30:00Z",
    )

    assert lookup.status is SamGovEntityLookupStatus.SUCCESS
    assert lookup.normalized_pivot == "UEIACME12345"
    assert lookup.pivot_type == "uei"
    assert lookup.provenance.source_tool_name == "lookup_entity_by_uei"
    assert lookup.provenance.source_mode is SamGovSourceMode.FAKE_ADAPTER_TEST
    assert lookup.matches[0].legal_business_name == "ACME FEDERAL LLC"
    assert lookup.matches[0].business_types == (
        "Small Business",
        "Woman Owned Business",
    )
    assert lookup.matches[0].parent_uei == "UEIPARENT9999"
    assert calls == [
        (
            "lookup_entity_by_uei",
            {
                "uei": "UEIACME12345",
                "include_sections": ["entityRegistration", "coreData", "assertions"],
                "sam_registered": "Yes",
            },
        )
    ]


def test_resolves_sam_gov_entity_lookup_by_vendor_name_with_multiple_matches() -> None:
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return SamGovMcpToolResult(
            ok=True,
            payload={
                "results": [
                    {
                        "entityRegistration": {
                            "uei": "UEIACME12345",
                            "legalBusinessName": "ACME FEDERAL LLC",
                        },
                    },
                    {
                        "entityRegistration": {
                            "uei": "UEIACMESUB9",
                            "legalBusinessName": "ACME FEDERAL SUBSIDIARY LLC",
                        },
                    },
                ]
            },
        )

    lookup = resolve_sam_gov_entity_lookup(
        "Acme Federal",
        runner=runner,
        source_mode=SamGovSourceMode.FAKE_ADAPTER_TEST,
        lookup_limit=8,
        checked_at="2026-05-17T15:35:00Z",
    )

    assert lookup.status is SamGovEntityLookupStatus.AMBIGUOUS
    assert lookup.normalized_pivot == "ACME FEDERAL"
    assert lookup.pivot_type == "legal_business_name"
    assert [match.uei for match in lookup.matches] == [
        "UEIACME12345",
        "UEIACMESUB9",
    ]
    assert "Multiple SAM.gov entity matches require review." in lookup.source_limitations
    assert calls == [
        (
            "search_entities",
            {
                "legal_business_name": "ACME FEDERAL",
                "include_sections": ["entityRegistration", "coreData", "assertions"],
                "page": 0,
                "size": 8,
            },
        )
    ]