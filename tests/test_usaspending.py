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
    assert result.diagnostic_summary == "No contracts or IDVs found matching 'MISSING-PIID'."


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