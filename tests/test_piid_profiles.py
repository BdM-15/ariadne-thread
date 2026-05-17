from ariadne.piid_profiles import (
    PiidGapCategory,
    PiidProfileStore,
    PiidPivotType,
    PiidScenarioClassification,
    create_piid_contract_intelligence_profile,
)
from ariadne.usaspending import (
    USAspendingAwardLookupResult,
    USAspendingAwardLookupStatus,
    USAspendingLookupProvenance,
)


def test_creates_piid_profile_from_resolved_usaspending_award() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number=" fa8650-23-c-0001 ",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        recipient_name="ACME FEDERAL LLC",
        awarding_agency_name="Department of the Air Force",
        awarding_sub_agency_name="Air Force Materiel Command",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        profile_id="piid_profile_FA8650_23_C_0001",
        created_at="2026-05-16T14:00:00Z",
    )

    assert profile.id == "piid_profile_FA8650_23_C_0001"
    assert profile.input_contract_number == " fa8650-23-c-0001 "
    assert profile.normalized_piid == "FA8650-23-C-0001"
    assert profile.scenario is PiidScenarioClassification.STANDALONE_CONTRACT
    assert profile.created_at == "2026-05-16T14:00:00Z"
    assert profile.updated_at == "2026-05-16T14:00:00Z"
    assert profile.provenance.source_capability_id == "usaspending"
    assert profile.provenance.source_tool_name == "lookup_piid"
    assert profile.provenance.source_package == "usaspending-gov-mcp"
    assert profile.provenance.source_package_version == "0.3.2"
    assert profile.award_baseline.award_type == "contract"
    assert profile.award_baseline.resolved_award_id == "FA8650-23-C-0001"
    assert profile.award_baseline.generated_internal_id == "CONT_AWD_FA865023C0001_9700"
    assert profile.award_baseline.recipient_name == "ACME FEDERAL LLC"
    assert profile.award_baseline.awarding_agency_name == "Department of the Air Force"
    assert (
        profile.award_baseline.awarding_sub_agency_name == "Air Force Materiel Command"
    )
    assert {
        (pivot.pivot_type, pivot.value) for pivot in profile.deterministic_pivots
    } >= {
        (PiidPivotType.GENERATED_INTERNAL_ID, "CONT_AWD_FA865023C0001_9700"),
        (PiidPivotType.AWARDING_AGENCY, "Department of the Air Force"),
        (PiidPivotType.AWARDING_SUB_AGENCY, "Air Force Materiel Command"),
    }
    gap_fields = {gap.field_key for gap in profile.gaps}
    assert {
        "uei",
        "naics_code",
        "psc_code",
        "solicitation_id",
        "award_amount",
        "start_date",
        "end_date",
    } <= gap_fields
    assert all(
        gap.category is PiidGapCategory.SOURCE_LIMITATION for gap in profile.gaps
    )


def test_profile_captures_available_baseline_fields_and_pivots() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-F-0001",
        normalized_piid="FA8650-23-F-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-F-0001",
        generated_internal_id="CONT_AWD_FA865023F0001_9700",
        recipient_name="ACME FEDERAL LLC",
        recipient_uei="UEIACME12345",
        parent_recipient_uei="UEIPARENT9999",
        awarding_agency_name="Department of the Air Force",
        awarding_sub_agency_name="Air Force Materiel Command",
        awarding_office_name="AFLCMC/PZ",
        funding_agency_name="Department of the Air Force",
        funding_sub_agency_name="Air Force Research Laboratory",
        funding_office_name="AFRL/RQ",
        award_amount=1250000.0,
        start_date="2023-05-01",
        end_date="2026-04-30",
        naics_code="541715",
        psc_code="AC13",
        solicitation_id="FA8650-22-R-0001",
        parent_idv="FA8650-20-D-0001",
        permalink="https://www.usaspending.gov/award/CONT_AWD_FA865023F0001_9700",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        created_at="2026-05-16T14:10:00Z",
    )

    assert profile.scenario is PiidScenarioClassification.IDIQ_ORDER
    assert profile.award_baseline.recipient_uei == "UEIACME12345"
    assert profile.award_baseline.parent_recipient_uei == "UEIPARENT9999"
    assert profile.award_baseline.awarding_office_name == "AFLCMC/PZ"
    assert profile.award_baseline.funding_agency_name == "Department of the Air Force"
    assert (
        profile.award_baseline.funding_sub_agency_name
        == "Air Force Research Laboratory"
    )
    assert profile.award_baseline.funding_office_name == "AFRL/RQ"
    assert profile.award_baseline.award_amount == 1250000.0
    assert profile.award_baseline.start_date == "2023-05-01"
    assert profile.award_baseline.end_date == "2026-04-30"
    assert profile.award_baseline.naics_code == "541715"
    assert profile.award_baseline.psc_code == "AC13"
    assert profile.award_baseline.solicitation_id == "FA8650-22-R-0001"
    assert profile.award_baseline.parent_idv == "FA8650-20-D-0001"
    assert profile.award_baseline.permalink == (
        "https://www.usaspending.gov/award/CONT_AWD_FA865023F0001_9700"
    )
    pivot_values = {
        (pivot.pivot_type, pivot.value) for pivot in profile.deterministic_pivots
    }
    assert (PiidPivotType.UEI, "UEIACME12345") in pivot_values
    assert (PiidPivotType.PARENT_UEI, "UEIPARENT9999") in pivot_values
    assert (PiidPivotType.NAICS_CODE, "541715") in pivot_values
    assert (PiidPivotType.PSC_CODE, "AC13") in pivot_values
    assert (PiidPivotType.SOLICITATION_ID, "FA8650-22-R-0001") in pivot_values
    assert (PiidPivotType.PARENT_IDV, "FA8650-20-D-0001") in pivot_values
    assert "naics_code" not in {gap.field_key for gap in profile.gaps}


def test_profile_classifies_idv_lookup_as_parent_idiq() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-20-D-0001",
        normalized_piid="FA8650-20-D-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="idv",
        resolved_award_id="FA8650-20-D-0001",
        generated_internal_id="CONT_IDV_FA865020D0001_9700",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )

    profile = create_piid_contract_intelligence_profile(lookup)

    assert profile.scenario is PiidScenarioClassification.PARENT_IDIQ


def test_profile_classifies_sparse_unknown_lookup_as_unknown() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="UNKNOWN",
        normalized_piid="UNKNOWN",
        status=USAspendingAwardLookupStatus.NOT_FOUND,
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="No USAspending award match found.",
    )

    profile = create_piid_contract_intelligence_profile(lookup)

    assert profile.scenario is PiidScenarioClassification.UNKNOWN


def test_piid_profile_store_round_trips_profiles(tmp_path) -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-C-0001",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    profile = create_piid_contract_intelligence_profile(
        lookup,
        profile_id="piid_profile_FA8650_23_C_0001",
        created_at="2026-05-16T14:00:00Z",
    )
    store = PiidProfileStore(tmp_path / "piid-profiles")

    store.write(profile)

    reloaded = PiidProfileStore(tmp_path / "piid-profiles")
    assert reloaded.read(profile.id).model_dump(mode="json") == profile.model_dump(
        mode="json"
    )
    assert reloaded.list() == [profile]
    assert reloaded.find_by_normalized_piid("FA8650-23-C-0001") == [profile]


def test_piid_profile_store_rejects_path_unsafe_ids(tmp_path) -> None:
    store = PiidProfileStore(tmp_path / "piid-profiles")

    try:
        store.read("../profile")
    except ValueError as error:
        assert "file-safe identifier" in str(error)
    else:
        raise AssertionError("expected path-unsafe profile id to fail")
