from ariadne.piid_profiles import (
    PiidEnrichmentRouteType,
    PiidGapCategory,
    PiidHermesEventType,
    PiidProfileStore,
    PiidPivotType,
    PiidReviewCandidateType,
    PiidReviewState,
    PiidScenarioClassification,
    create_piid_contract_intelligence_profile,
    record_piid_review_decision,
)
from ariadne.usaspending import (
    USAspendingAwardHistoryResult,
    USAspendingAwardLookupResult,
    USAspendingAwardLookupStatus,
    USAspendingAwardTransaction,
    USAspendingVehicleChildAward,
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


def test_profile_computes_burn_posture_from_transaction_history() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-C-0001",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        award_amount=1000000.0,
        start_date="2023-05-01",
        end_date="2024-04-30",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_AWD_FA865023C0001_9700",
        transaction_history=(
            USAspendingAwardTransaction(
                transaction_id="txn_base",
                action_date="2023-05-01",
                fiscal_year=2023,
                modification_number="0",
                action_type="Base Award",
                obligation=800000.0,
                description="Base award",
            ),
            USAspendingAwardTransaction(
                transaction_id="txn_p00001",
                action_date="2023-11-15",
                fiscal_year=2024,
                modification_number="P00001",
                action_type="Funding Modification",
                obligation=200000.0,
                description="Incremental funding",
            ),
        ),
        derivation_notes=("Fetched transaction history from get_transactions.",),
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
        created_at="2026-05-16T14:20:00Z",
    )

    assert profile.burn_posture.net_obligations == 1000000.0
    assert profile.burn_posture.transaction_count == 2
    assert profile.burn_posture.modification_count == 1
    assert profile.burn_posture.period_start == "2023-05-01"
    assert profile.burn_posture.period_end == "2024-04-30"
    assert profile.burn_posture.period_days == 366
    assert profile.burn_posture.monthly_burn_rate == 83333.33
    assert profile.burn_posture.daily_burn_rate == 2732.24
    assert profile.burn_posture.completeness == "complete"
    assert profile.burn_posture.fiscal_year_obligations == {
        2023: 800000.0,
        2024: 200000.0,
    }
    assert profile.modification_history[0].modification_number == "P00001"
    assert "Base award" in profile.transaction_history[0].description


def test_profile_flags_deobligations_and_option_signals() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-C-0001",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        start_date="2023-05-01",
        end_date="2025-04-30",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_AWD_FA865023C0001_9700",
        transaction_history=(
            USAspendingAwardTransaction(
                transaction_id="txn_base",
                action_date="2023-05-01",
                fiscal_year=2023,
                modification_number="0",
                action_type="Base Award",
                obligation=900000.0,
                description="Base period",
            ),
            USAspendingAwardTransaction(
                transaction_id="txn_option",
                action_date="2024-05-01",
                fiscal_year=2024,
                modification_number="P00002",
                action_type="Option Exercise",
                obligation=300000.0,
                description="Exercise option year one",
            ),
            USAspendingAwardTransaction(
                transaction_id="txn_deob",
                action_date="2024-09-15",
                fiscal_year=2024,
                modification_number="P00003",
                action_type="Funding Modification",
                obligation=-50000.0,
                description="Partial deobligation",
            ),
        ),
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
    )

    assert profile.burn_posture.net_obligations == 1150000.0
    assert profile.burn_posture.option_signals == (
        "P00002 on 2024-05-01: Exercise option year one",
    )
    assert profile.burn_posture.deobligation_warnings == (
        "P00003 on 2024-09-15 deobligated $50,000.00",
    )


def test_profile_uses_baseline_amount_when_transactions_are_sparse() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-C-0001",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        award_amount=500000.0,
        start_date="2023-10-01",
        end_date="2024-09-30",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_AWD_FA865023C0001_9700",
        derivation_notes=("get_transactions unavailable: HTTP 429",),
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
    )

    assert profile.burn_posture.net_obligations == 500000.0
    assert profile.burn_posture.transaction_count == 0
    assert profile.burn_posture.completeness == "partial"
    assert profile.burn_posture.daily_burn_rate == 1366.12
    assert profile.burn_posture.derivation_notes == (
        "get_transactions unavailable: HTTP 429",
        "Used award baseline award_amount because transaction history was empty.",
    )


def test_profile_uses_award_detail_parent_linkage_for_order_classification() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-F-0001",
        normalized_piid="FA8650-23-F-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-F-0001",
        generated_internal_id="CONT_AWD_FA865023F0001_9700_CONT_IDV_FA865020D0001_9700",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_AWD_FA865023F0001_9700_CONT_IDV_FA865020D0001_9700",
        award_detail={
            "parent_award_piid": "FA8650-20-D-0001",
            "parent_award_generated_internal_id": "CONT_IDV_FA865020D0001_9700",
        },
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
    )

    assert profile.scenario is PiidScenarioClassification.IDIQ_ORDER
    assert profile.vehicle_context.parent_idv == "FA8650-20-D-0001"
    assert profile.vehicle_context.parent_generated_internal_id == (
        "CONT_IDV_FA865020D0001_9700"
    )
    assert profile.vehicle_context.linkage_confidence == "linked"
    assert profile.vehicle_context.derivation_notes == (
        "Parent vehicle linkage came from get_award_detail.",
    )


def test_profile_records_parent_idiq_child_order_context() -> None:
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
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_IDV_FA865020D0001_9700",
        idv_children=(
            USAspendingVehicleChildAward(
                piid="FA8650-23-F-0001",
                generated_internal_id="CONT_AWD_FA865023F0001_9700_CONT_IDV_FA865020D0001_9700",
                recipient_name="ACME FEDERAL LLC",
                obligated_amount=1250000.0,
                period_start="2023-05-01",
                period_end="2026-04-30",
            ),
        ),
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
    )

    assert profile.scenario is PiidScenarioClassification.PARENT_IDIQ
    assert profile.vehicle_context.child_orders[0].piid == "FA8650-23-F-0001"
    assert profile.vehicle_context.child_orders[0].obligated_amount == 1250000.0
    assert profile.vehicle_context.linkage_confidence == "linked"
    assert profile.vehicle_context.derivation_notes == (
        "Child order context came from get_idv_children.",
    )


def test_profile_marks_partial_vehicle_linkage_when_parent_id_is_incomplete() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-F-0001",
        normalized_piid="FA8650-23-F-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-F-0001",
        generated_internal_id="CONT_AWD_FA865023F0001_9700",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_AWD_FA865023F0001_9700",
        award_detail={"parent_award_piid": "FA8650-20-D-0001"},
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
    )

    assert profile.scenario is PiidScenarioClassification.IDIQ_ORDER
    assert profile.vehicle_context.parent_idv == "FA8650-20-D-0001"
    assert profile.vehicle_context.parent_generated_internal_id is None
    assert profile.vehicle_context.linkage_confidence == "partial"


def test_profile_recommends_enrichment_routes_from_populated_pivots_only() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-F-0001",
        normalized_piid="FA8650-23-F-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-F-0001",
        generated_internal_id="CONT_AWD_FA865023F0001_9700",
        recipient_name="ACME FEDERAL LLC",
        recipient_uei="UEIACME12345",
        awarding_agency_name="Department of the Air Force",
        awarding_sub_agency_name="Air Force Materiel Command",
        award_amount=1250000.0,
        start_date="2023-05-01",
        end_date="2026-04-30",
        naics_code="541715",
        psc_code="AC13",
        solicitation_id="FA8650-22-R-0001",
        permalink="https://www.usaspending.gov/award/CONT_AWD_FA865023F0001_9700",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )

    profile = create_piid_contract_intelligence_profile(lookup)

    routes_by_type = {
        route.route_type: route for route in profile.recommended_enrichment_routes
    }
    assert set(routes_by_type) >= {
        PiidEnrichmentRouteType.SAM_GOV_ENTITY,
        PiidEnrichmentRouteType.SAM_GOV_OPPORTUNITY,
        PiidEnrichmentRouteType.BLS_GSA_PRICING_CONTEXT,
        PiidEnrichmentRouteType.WEB_SOURCE_COLLECTION,
        PiidEnrichmentRouteType.SUBAWARD_PROFILE,
        PiidEnrichmentRouteType.COMPETITOR_PROFILE,
        PiidEnrichmentRouteType.CUSTOMER_PROFILE,
        PiidEnrichmentRouteType.ARTIFACT_PREPARATION,
    }
    assert routes_by_type[PiidEnrichmentRouteType.SAM_GOV_ENTITY].source_fields == (
        "recipient_uei",
    )
    assert routes_by_type[PiidEnrichmentRouteType.SAM_GOV_ENTITY].source_values == (
        "UEIACME12345",
    )
    assert routes_by_type[
        PiidEnrichmentRouteType.BLS_GSA_PRICING_CONTEXT
    ].source_fields == ("naics_code", "psc_code")
    assert all(
        "parent_recipient_uei" not in route.source_fields
        for route in profile.recommended_enrichment_routes
    )
    assert all(route.review_required for route in profile.recommended_enrichment_routes)


def test_profile_projects_review_gated_candidates_without_trusted_outputs() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-C-0001",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        recipient_name="ACME FEDERAL LLC",
        recipient_uei="UEIACME12345",
        awarding_agency_name="Department of the Air Force",
        awarding_sub_agency_name="Air Force Materiel Command",
        award_amount=1200000.0,
        start_date="2023-05-01",
        end_date="2025-04-30",
        naics_code="541715",
        psc_code="AC13",
        solicitation_id="FA8650-22-R-0001",
        provenance=USAspendingLookupProvenance(
            source_package="usaspending-gov-mcp",
            source_package_version="0.3.2",
            checked_at="2026-05-16T13:00:00Z",
        ),
        diagnostic_summary="Resolved one USAspending award match.",
    )
    history = USAspendingAwardHistoryResult(
        generated_award_id="CONT_AWD_FA865023C0001_9700",
        transaction_history=(
            USAspendingAwardTransaction(
                transaction_id="txn_base",
                action_date="2023-05-01",
                fiscal_year=2023,
                modification_number="0",
                action_type="Base Award",
                obligation=900000.0,
                description="Base award",
            ),
            USAspendingAwardTransaction(
                transaction_id="txn_deob",
                action_date="2024-09-15",
                fiscal_year=2024,
                modification_number="P00001",
                action_type="Funding Modification",
                obligation=-50000.0,
                description="Partial deobligation",
            ),
        ),
    )

    profile = create_piid_contract_intelligence_profile(
        lookup,
        award_history=history,
        profile_id="piid_profile_FA8650_23_C_0001",
        created_at="2026-05-16T14:30:00Z",
    )

    candidate_types = {candidate.candidate_type for candidate in profile.review_candidates}
    assert {
        PiidReviewCandidateType.SOURCE_EVIDENCE,
        PiidReviewCandidateType.DERIVED_EVIDENCE,
        PiidReviewCandidateType.PACKET_FIELD_ANSWER,
        PiidReviewCandidateType.ACTION_PLAN_ITEM,
        PiidReviewCandidateType.RISK_REGISTER_SIGNAL,
        PiidReviewCandidateType.CALL_PLAN_SIGNAL,
        PiidReviewCandidateType.FOLLOW_UP_ROUTE,
    } <= candidate_types
    packet_fields = {
        candidate.field_key
        for candidate in profile.review_candidates
        if candidate.candidate_type is PiidReviewCandidateType.PACKET_FIELD_ANSWER
    }
    assert {"incumbent", "customer", "value", "timing", "risk"} <= packet_fields
    assert all(
        candidate.review_state is PiidReviewState.PENDING_REVIEW
        for candidate in profile.review_candidates
    )
    assert all(
        not candidate.trusted_output_written for candidate in profile.review_candidates
    )

    source_candidate = next(
        candidate
        for candidate in profile.review_candidates
        if candidate.candidate_type is PiidReviewCandidateType.SOURCE_EVIDENCE
    )
    derived_candidate = next(
        candidate
        for candidate in profile.review_candidates
        if candidate.candidate_type is PiidReviewCandidateType.DERIVED_EVIDENCE
    )
    assert source_candidate.target_workflow == "evidence_store"
    assert "ACME FEDERAL LLC" in source_candidate.content
    assert "award_baseline.recipient_name" in source_candidate.source_fields
    assert derived_candidate.target_workflow == "evidence_store"
    assert "net obligations" in derived_candidate.content
    assert "burn_posture.net_obligations" in derived_candidate.source_fields


def test_profile_emits_hermes_events_and_records_review_decisions() -> None:
    lookup = USAspendingAwardLookupResult(
        input_contract_number="FA8650-23-C-0001",
        normalized_piid="FA8650-23-C-0001",
        status=USAspendingAwardLookupStatus.SUCCESS,
        award_type="contract",
        resolved_award_id="FA8650-23-C-0001",
        generated_internal_id="CONT_AWD_FA865023C0001_9700",
        recipient_name="ACME FEDERAL LLC",
        recipient_uei="UEIACME12345",
        award_amount=1200000.0,
        start_date="2023-05-01",
        end_date="2025-04-30",
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
        created_at="2026-05-16T14:40:00Z",
    )

    event_types = {event.event_type for event in profile.hermes_events}
    assert {
        PiidHermesEventType.PROFILE_STARTED,
        PiidHermesEventType.AWARD_RESOLVED,
        PiidHermesEventType.SCENARIO_CLASSIFIED,
        PiidHermesEventType.BURN_POSTURE_COMPUTED,
        PiidHermesEventType.PIVOTS_IDENTIFIED,
        PiidHermesEventType.GAP_DETECTED,
        PiidHermesEventType.NEXT_ENRICHMENT_RECOMMENDED,
    } <= event_types
    assert PiidHermesEventType.REVIEW_DECISION_RECORDED not in event_types

    source_candidate = next(
        candidate
        for candidate in profile.review_candidates
        if candidate.candidate_type is PiidReviewCandidateType.SOURCE_EVIDENCE
    )
    updated_profile = record_piid_review_decision(
        profile,
        candidate_id=source_candidate.id,
        review_state=PiidReviewState.ACCEPTED,
        reviewer_rationale="Baseline fields match the capture research spine.",
        decided_at="2026-05-16T14:45:00Z",
    )

    accepted_candidate = next(
        candidate
        for candidate in updated_profile.review_candidates
        if candidate.id == source_candidate.id
    )
    assert accepted_candidate.review_state is PiidReviewState.ACCEPTED
    assert accepted_candidate.trusted_output_written is False
    assert updated_profile.updated_at == "2026-05-16T14:45:00Z"
    review_event = updated_profile.hermes_events[-1]
    assert review_event.event_type is PiidHermesEventType.REVIEW_DECISION_RECORDED
    assert review_event.payload["candidate_id"] == source_candidate.id
    assert review_event.payload["review_state"] == "accepted"
    assert review_event.payload["trusted_output_written"] is False


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
