from ariadne.usaspending import (
    USAspendingAwardLookupStatus,
    USAspendingMcpToolResult,
    resolve_usaspending_piid,
)


def test_resolves_single_usaspending_piid_match_with_provenance() -> None:
    calls = []

    def runner(tool_name, arguments):
        calls.append((tool_name, arguments))
        return USAspendingMcpToolResult(
            ok=True,
            payload={
                "award_type": "contract",
                "results": [
                    {
                        "Award ID": "FA8650-23-C-0001",
                        "Recipient Name": "ACME FEDERAL LLC",
                        "Awarding Agency": "Department of the Air Force",
                        "Awarding Sub Agency": "Air Force Materiel Command",
                        "generated_internal_id": "CONT_AWD_FA865023C0001_9700",
                    }
                ],
            },
        )

    result = resolve_usaspending_piid(
        " fa8650-23-c-0001 ",
        runner=runner,
        checked_at="2026-05-16T13:00:00Z",
    )

    assert result.status is USAspendingAwardLookupStatus.SUCCESS
    assert result.input_contract_number == " fa8650-23-c-0001 "
    assert result.normalized_piid == "FA8650-23-C-0001"
    assert result.award_type == "contract"
    assert result.resolved_award_id == "FA8650-23-C-0001"
    assert result.generated_internal_id == "CONT_AWD_FA865023C0001_9700"
    assert result.recipient_name == "ACME FEDERAL LLC"
    assert result.awarding_agency_name == "Department of the Air Force"
    assert result.awarding_sub_agency_name == "Air Force Materiel Command"
    assert result.provenance.source_capability_id == "usaspending"
    assert result.provenance.source_tool_name == "lookup_piid"
    assert result.provenance.source_package == "usaspending-gov-mcp"
    assert result.provenance.source_package_version == "0.3.2"
    assert result.provenance.checked_at == "2026-05-16T13:00:00Z"
    assert result.diagnostic_summary == "Resolved one USAspending award match."
    assert calls == [("lookup_piid", {"piid": "FA8650-23-C-0001", "limit": 5})]


def test_reports_not_found_when_usaspending_lookup_returns_no_results() -> None:
    result = resolve_usaspending_piid(
        "missing-piid",
        runner=lambda tool_name, arguments: USAspendingMcpToolResult(
            ok=True,
            payload={
                "award_type": None,
                "results": [],
                "message": "No contracts or IDVs found matching 'MISSING-PIID'.",
            },
        ),
        checked_at="2026-05-16T13:05:00Z",
    )

    assert result.status is USAspendingAwardLookupStatus.NOT_FOUND
    assert result.normalized_piid == "MISSING-PIID"
    assert result.candidates == ()
    assert (
        result.diagnostic_summary
        == "No contracts or IDVs found matching 'MISSING-PIID'."
    )


def test_reports_ambiguous_when_usaspending_lookup_returns_multiple_results() -> None:
    result = resolve_usaspending_piid(
        "FA8650",
        runner=lambda tool_name, arguments: USAspendingMcpToolResult(
            ok=True,
            payload={
                "award_type": "contract",
                "results": [
                    {
                        "Award ID": "FA8650-23-C-0001",
                        "Recipient Name": "ACME FEDERAL LLC",
                        "generated_internal_id": "CONT_AWD_1",
                    },
                    {
                        "Award ID": "FA8650-23-C-0002",
                        "Recipient Name": "BETA SYSTEMS INC",
                        "generated_internal_id": "CONT_AWD_2",
                    },
                ],
            },
        ),
        checked_at="2026-05-16T13:10:00Z",
    )

    assert result.status is USAspendingAwardLookupStatus.AMBIGUOUS
    assert result.resolved_award_id is None
    assert [candidate.resolved_award_id for candidate in result.candidates] == [
        "FA8650-23-C-0001",
        "FA8650-23-C-0002",
    ]
    assert result.diagnostic_summary == "USAspending returned 2 possible matches."


def test_reports_tool_error_without_exposing_command_details() -> None:
    result = resolve_usaspending_piid(
        "FA8650-23-C-0001",
        runner=lambda tool_name, arguments: USAspendingMcpToolResult(
            ok=False,
            error_message="lookup_piid failed: HTTP 429: rate limited",
        ),
        checked_at="2026-05-16T13:15:00Z",
    )

    assert result.status is USAspendingAwardLookupStatus.TOOL_ERROR
    assert result.diagnostic_summary == "lookup_piid failed: HTTP 429: rate limited"
    assert "uvx --from" not in result.diagnostic_summary
    assert result.resolved_award_id is None


def test_success_result_tolerates_sparse_usaspending_rows() -> None:
    result = resolve_usaspending_piid(
        "FA8650-23-C-0001",
        runner=lambda tool_name, arguments: USAspendingMcpToolResult(
            ok=True,
            payload={
                "award_type": "contract",
                "results": [{"generated_internal_id": "CONT_AWD_FA865023C0001"}],
            },
        ),
        checked_at="2026-05-16T13:20:00Z",
    )

    assert result.status is USAspendingAwardLookupStatus.SUCCESS
    assert result.generated_internal_id == "CONT_AWD_FA865023C0001"
    assert result.resolved_award_id is None
    assert result.recipient_name is None
    assert result.awarding_agency_name is None


def test_success_result_captures_optional_baseline_fields_from_lookup_row() -> None:
    result = resolve_usaspending_piid(
        "FA8650-23-F-0001",
        runner=lambda tool_name, arguments: USAspendingMcpToolResult(
            ok=True,
            payload={
                "award_type": "contract",
                "results": [
                    {
                        "Award ID": "FA8650-23-F-0001",
                        "Recipient Name": "ACME FEDERAL LLC",
                        "Recipient UEI": "UEIACME12345",
                        "Parent Recipient UEI": "UEIPARENT9999",
                        "Awarding Agency": "Department of the Air Force",
                        "Awarding Sub Agency": "Air Force Materiel Command",
                        "Awarding Office": "AFLCMC/PZ",
                        "Funding Agency": "Department of the Air Force",
                        "Funding Sub Agency": "Air Force Research Laboratory",
                        "Funding Office": "AFRL/RQ",
                        "Award Amount": "$1,250,000.00",
                        "Start Date": "2023-05-01",
                        "End Date": "2026-04-30",
                        "NAICS Code": "541715",
                        "PSC Code": "AC13",
                        "Solicitation ID": "FA8650-22-R-0001",
                        "Parent IDV": "FA8650-20-D-0001",
                        "generated_internal_id": "CONT_AWD_FA865023F0001_9700",
                        "permalink": "https://www.usaspending.gov/award/CONT_AWD_FA865023F0001_9700",
                    }
                ],
            },
        ),
        checked_at="2026-05-16T13:25:00Z",
    )

    assert result.recipient_uei == "UEIACME12345"
    assert result.parent_recipient_uei == "UEIPARENT9999"
    assert result.awarding_office_name == "AFLCMC/PZ"
    assert result.funding_agency_name == "Department of the Air Force"
    assert result.funding_sub_agency_name == "Air Force Research Laboratory"
    assert result.funding_office_name == "AFRL/RQ"
    assert result.award_amount == 1250000.0
    assert result.start_date == "2023-05-01"
    assert result.end_date == "2026-04-30"
    assert result.naics_code == "541715"
    assert result.psc_code == "AC13"
    assert result.solicitation_id == "FA8650-22-R-0001"
    assert result.parent_idv == "FA8650-20-D-0001"
    assert (
        result.permalink
        == "https://www.usaspending.gov/award/CONT_AWD_FA865023F0001_9700"
    )
