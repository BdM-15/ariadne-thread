from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel

from ariadne.federal_data import (
    list_federal_data_capability_manifests,
    run_mcp_tool_command,
)


class USAspendingAwardLookupStatus(StrEnum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    TOOL_ERROR = "tool_error"


class USAspendingMcpToolResult(BaseModel):
    ok: bool
    payload: dict[str, Any] | None = None
    error_message: str | None = None


class USAspendingMcpToolRunner(Protocol):
    def __call__(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> USAspendingMcpToolResult: ...


class USAspendingLookupProvenance(BaseModel):
    source_capability_id: str = "usaspending"
    source_tool_name: str = "lookup_piid"
    source_package: str
    source_package_version: str
    checked_at: str


class USAspendingAwardCandidate(BaseModel):
    resolved_award_id: str | None = None
    generated_internal_id: str | None = None
    recipient_name: str | None = None
    awarding_agency_name: str | None = None
    awarding_sub_agency_name: str | None = None


class USAspendingAwardLookupResult(BaseModel):
    input_contract_number: str
    normalized_piid: str
    status: USAspendingAwardLookupStatus
    provenance: USAspendingLookupProvenance
    award_type: str | None = None
    resolved_award_id: str | None = None
    generated_internal_id: str | None = None
    recipient_name: str | None = None
    awarding_agency_name: str | None = None
    awarding_sub_agency_name: str | None = None
    candidates: tuple[USAspendingAwardCandidate, ...] = ()
    diagnostic_summary: str


def resolve_usaspending_piid(
    input_contract_number: str,
    *,
    runner: USAspendingMcpToolRunner,
    lookup_limit: int = 5,
    checked_at: str | None = None,
) -> USAspendingAwardLookupResult:
    normalized_piid = input_contract_number.strip().upper()
    provenance = _lookup_provenance(checked_at)
    tool_result = runner(
        "lookup_piid",
        {"piid": normalized_piid, "limit": lookup_limit},
    )
    if not tool_result.ok:
        return USAspendingAwardLookupResult(
            input_contract_number=input_contract_number,
            normalized_piid=normalized_piid,
            status=USAspendingAwardLookupStatus.TOOL_ERROR,
            provenance=provenance,
            diagnostic_summary=tool_result.error_message or "USAspending lookup failed.",
        )

    payload = tool_result.payload or {}
    results = tuple(
        result for result in payload.get("results", ()) if isinstance(result, dict)
    )
    if len(results) == 1:
        candidate = _candidate_from_lookup_row(results[0])
        return USAspendingAwardLookupResult(
            input_contract_number=input_contract_number,
            normalized_piid=normalized_piid,
            status=USAspendingAwardLookupStatus.SUCCESS,
            provenance=provenance,
            award_type=payload.get("award_type"),
            resolved_award_id=candidate.resolved_award_id,
            generated_internal_id=candidate.generated_internal_id,
            recipient_name=candidate.recipient_name,
            awarding_agency_name=candidate.awarding_agency_name,
            awarding_sub_agency_name=candidate.awarding_sub_agency_name,
            candidates=(candidate,),
            diagnostic_summary="Resolved one USAspending award match.",
        )

    if not results:
        return USAspendingAwardLookupResult(
            input_contract_number=input_contract_number,
            normalized_piid=normalized_piid,
            status=USAspendingAwardLookupStatus.NOT_FOUND,
            provenance=provenance,
            award_type=payload.get("award_type"),
            diagnostic_summary=payload.get("message") or "No USAspending award match found.",
        )

    candidates = tuple(_candidate_from_lookup_row(result) for result in results)
    return USAspendingAwardLookupResult(
        input_contract_number=input_contract_number,
        normalized_piid=normalized_piid,
        status=USAspendingAwardLookupStatus.AMBIGUOUS,
        provenance=provenance,
        award_type=payload.get("award_type"),
        candidates=candidates,
        diagnostic_summary=f"USAspending returned {len(candidates)} possible matches.",
    )


def create_usaspending_lookup_runner(
    *,
    command: str,
    timeout_seconds: int,
    env: dict[str, str],
) -> USAspendingMcpToolRunner:
    def runner(tool_name: str, arguments: dict[str, Any]) -> USAspendingMcpToolResult:
        result = run_mcp_tool_command(
            command,
            tool_name,
            arguments,
            timeout_seconds,
            env,
        )
        return USAspendingMcpToolResult(
            ok=result.ok,
            payload=result.payload,
            error_message=result.error_message,
        )

    return runner


def _candidate_from_lookup_row(row: dict[str, Any]) -> USAspendingAwardCandidate:
    return USAspendingAwardCandidate(
        resolved_award_id=_string_or_none(row.get("Award ID")),
        generated_internal_id=_string_or_none(row.get("generated_internal_id")),
        recipient_name=_string_or_none(row.get("Recipient Name")),
        awarding_agency_name=_string_or_none(row.get("Awarding Agency")),
        awarding_sub_agency_name=_string_or_none(row.get("Awarding Sub Agency")),
    )


def _lookup_provenance(checked_at: str | None) -> USAspendingLookupProvenance:
    manifest = next(
        capability
        for capability in list_federal_data_capability_manifests().capabilities
        if capability.id == "usaspending"
    )
    return USAspendingLookupProvenance(
        source_package=manifest.package,
        source_package_version=manifest.version,
        checked_at=checked_at or datetime.now(UTC).isoformat(),
    )


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None