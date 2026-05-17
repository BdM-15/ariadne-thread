from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field, model_validator

from ariadne.federal_data import run_mcp_tool_command


class SamGovSourceMode(StrEnum):
    LIVE_SAM_GOV = "live_sam_gov"
    FAKE_ADAPTER_TEST = "fake_adapter_test"
    DEMO_FIXTURE = "demo_fixture"


class SamGovEntityLookupStatus(StrEnum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    TOOL_ERROR = "tool_error"


class SamGovOpportunityDiscoveryStatus(StrEnum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    TOOL_ERROR = "tool_error"


class SamGovKnownOpportunityStatus(StrEnum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    TOOL_ERROR = "tool_error"


class SamGovKnownOpportunityPivotType(StrEnum):
    SOLICITATION_NUMBER = "solicitation_number"
    NOTICE_ID = "notice_id"


class SamGovMcpToolResult(BaseModel):
    ok: bool
    payload: dict[str, Any] | None = None
    error_message: str | None = None


class SamGovMcpToolRunner(Protocol):
    def __call__(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> SamGovMcpToolResult: ...


class SamGovReviewCandidateType(StrEnum):
    SOURCE_EVIDENCE = "source_evidence"
    DERIVED_EVIDENCE = "derived_evidence"
    PACKET_FIELD_ANSWER = "packet_field_answer"
    ACTION_PLAN_ITEM = "action_plan_item"
    RISK_REGISTER_SIGNAL = "risk_register_signal"
    CALL_PLAN_SIGNAL = "call_plan_signal"
    FOLLOW_UP_ROUTE = "follow_up_route"


class SamGovReviewState(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"
    ROUTED = "routed"


class SamGovHermesEventType(StrEnum):
    PROFILE_STARTED = "profile_started"
    ENTITY_RECORD_RESOLVED = "entity_record_resolved"
    KNOWN_OPPORTUNITY_RESOLVED = "known_opportunity_resolved"
    OPPORTUNITY_DISCOVERY_RUN = "opportunity_discovery_run"
    SOURCE_LIMITATION_DETECTED = "source_limitation_detected"
    REVIEW_CANDIDATES_CREATED = "review_candidates_created"
    REVIEW_DECISION_RECORDED = "review_decision_recorded"


class SamGovEntityLookupProvenance(BaseModel):
    source_capability_id: str = "sam_gov"
    source_tool_name: str = "lookup_entity_by_uei"
    source_package: str
    source_package_version: str
    checked_at: str
    source_mode: SamGovSourceMode


class SamGovOpportunityDiscoveryQuery(BaseModel):
    customer_agency: str | None = None
    office: str | None = None
    program_name: str | None = None
    old_program_name: str | None = None
    keywords: tuple[str, ...] = ()
    notice_type: str | None = None
    naics_code: str | None = None
    psc_code: str | None = None
    set_aside: str | None = None
    posted_from: str
    posted_to: str
    response_deadline_from: str | None = None
    response_deadline_to: str | None = None
    state: str | None = None
    zip_code: str | None = None
    limit: int = Field(default=100, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SamGovKnownOpportunityQuery(BaseModel):
    input_pivot: str
    pivot_type: SamGovKnownOpportunityPivotType = (
        SamGovKnownOpportunityPivotType.SOLICITATION_NUMBER
    )
    posted_from: str
    posted_to: str
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SamGovOpportunityRecord(BaseModel):
    notice_id: str | None = None
    solicitation_number: str | None = None
    title: str | None = None
    notice_type: str | None = None
    organization_path: str | None = None
    posted_date: str | None = None
    response_deadline: str | None = None
    set_aside: str | None = None
    naics_code: str | None = None
    psc_code: str | None = None
    place_of_performance: str | None = None
    description_url: str | None = None
    ui_link: str | None = None
    active: bool | None = None
    archive_type: str | None = None
    archive_date: str | None = None
    point_of_contact: tuple[str, ...] = ()
    match_rationale: tuple[str, ...] = ()
    match_confidence: float = Field(default=0.0, ge=0, le=1)
    ambiguity_notes: tuple[str, ...] = ()
    raw_record: dict[str, object] = Field(default_factory=dict)


class SamGovOpportunityDiscoveryResult(BaseModel):
    query: SamGovOpportunityDiscoveryQuery
    normalized_query: str
    status: SamGovOpportunityDiscoveryStatus
    provenance: SamGovEntityLookupProvenance
    records: tuple[SamGovOpportunityRecord, ...] = ()
    total_records: int | None = None
    source_limitations: tuple[str, ...] = ()
    diagnostic_summary: str


class SamGovKnownOpportunityResult(BaseModel):
    input_pivot: str
    normalized_pivot: str
    pivot_type: SamGovKnownOpportunityPivotType
    status: SamGovKnownOpportunityStatus
    provenance: SamGovEntityLookupProvenance
    records: tuple[SamGovOpportunityRecord, ...] = ()
    total_records: int | None = None
    source_limitations: tuple[str, ...] = ()
    diagnostic_summary: str


class SamGovEntityMatch(BaseModel):
    uei: str | None = None
    legal_business_name: str | None = None
    cage_code: str | None = None
    registration_status: str | None = None
    parent_uei: str | None = None
    parent_legal_business_name: str | None = None
    business_types: tuple[str, ...] = ()
    naics_codes: tuple[str, ...] = ()
    psc_codes: tuple[str, ...] = ()
    responsibility_notes: tuple[str, ...] = ()
    raw_record: dict[str, object] = Field(default_factory=dict)


class SamGovEntityLookupResult(BaseModel):
    input_pivot: str
    normalized_pivot: str
    pivot_type: str
    status: SamGovEntityLookupStatus
    provenance: SamGovEntityLookupProvenance
    matches: tuple[SamGovEntityMatch, ...] = ()
    source_limitations: tuple[str, ...] = ()
    diagnostic_summary: str


class SamGovEntityLane(BaseModel):
    input_pivot: str
    normalized_pivot: str
    pivot_type: str
    lookup_status: SamGovEntityLookupStatus
    provenance: SamGovEntityLookupProvenance
    matches: tuple[SamGovEntityMatch, ...] = ()
    source_limitations: tuple[str, ...] = ()
    diagnostic_summary: str


class SamGovOpportunityDiscoveryLane(BaseModel):
    query: SamGovOpportunityDiscoveryQuery
    normalized_query: str
    discovery_status: SamGovOpportunityDiscoveryStatus
    provenance: SamGovEntityLookupProvenance
    records: tuple[SamGovOpportunityRecord, ...] = ()
    total_records: int | None = None
    source_limitations: tuple[str, ...] = ()
    diagnostic_summary: str


class SamGovKnownOpportunityLane(BaseModel):
    input_pivot: str
    normalized_pivot: str
    pivot_type: SamGovKnownOpportunityPivotType
    lookup_status: SamGovKnownOpportunityStatus
    provenance: SamGovEntityLookupProvenance
    records: tuple[SamGovOpportunityRecord, ...] = ()
    total_records: int | None = None
    source_limitations: tuple[str, ...] = ()
    diagnostic_summary: str


class SamGovReviewCandidate(BaseModel):
    id: str
    candidate_type: SamGovReviewCandidateType
    title: str
    content: str
    target_workflow: str
    recommendation: str
    rationale: str
    source_profile_id: str
    normalized_pivot: str
    source_mode: SamGovSourceMode
    source_fields: tuple[str, ...]
    source_values: tuple[str, ...]
    field_key: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    review_state: SamGovReviewState = SamGovReviewState.PENDING_REVIEW
    trusted_output_written: bool = False
    created_at: str

    @model_validator(mode="after")
    def validate_review_gate(self) -> SamGovReviewCandidate:
        if not self.source_fields:
            raise ValueError("SAM.gov review candidate requires source_fields")
        if self.trusted_output_written and self.review_state is not (
            SamGovReviewState.ACCEPTED
        ):
            raise ValueError("trusted output requires accepted review state")
        if (
            self.trusted_output_written
            and self.source_mode is not SamGovSourceMode.LIVE_SAM_GOV
        ):
            raise ValueError("trusted output requires live SAM.gov source mode")
        return self


class SamGovHermesEvent(BaseModel):
    id: str
    event_type: SamGovHermesEventType
    profile_id: str
    normalized_pivot: str
    occurred_at: str
    summary: str
    payload: dict[str, object] = Field(default_factory=dict)
    source_capability_id: str = "sam_gov"
    observable_only: bool = True


class SamGovEnrichmentProfile(BaseModel):
    id: str
    input_pivot: str
    normalized_pivot: str
    entity_lane: SamGovEntityLane | None = None
    known_opportunity_lane: SamGovKnownOpportunityLane | None = None
    opportunity_discovery_lane: SamGovOpportunityDiscoveryLane | None = None
    review_candidates: tuple[SamGovReviewCandidate, ...] = ()
    hermes_events: tuple[SamGovHermesEvent, ...] = ()
    created_at: str
    updated_at: str


def resolve_sam_gov_entity_lookup(
    input_pivot: str,
    *,
    runner: SamGovMcpToolRunner,
    source_mode: SamGovSourceMode = SamGovSourceMode.LIVE_SAM_GOV,
    lookup_limit: int = 10,
    checked_at: str | None = None,
) -> SamGovEntityLookupResult:
    normalized_pivot = input_pivot.strip().upper()
    provenance = SamGovEntityLookupProvenance(
        source_tool_name=(
            "lookup_entity_by_uei"
            if _looks_like_uei(normalized_pivot)
            else "search_entities"
        ),
        source_package="sam-gov-mcp",
        source_package_version="0.4.1",
        checked_at=checked_at or datetime.now(UTC).isoformat(),
        source_mode=source_mode,
    )
    tool_arguments = _entity_lookup_arguments(
        normalized_pivot,
        source_tool_name=provenance.source_tool_name,
        lookup_limit=lookup_limit,
    )
    tool_result = runner(provenance.source_tool_name, tool_arguments)
    if not tool_result.ok:
        return SamGovEntityLookupResult(
            input_pivot=input_pivot,
            normalized_pivot=normalized_pivot,
            pivot_type=_entity_pivot_type(provenance.source_tool_name),
            status=SamGovEntityLookupStatus.TOOL_ERROR,
            provenance=provenance,
            source_limitations=(
                tool_result.error_message or "SAM.gov entity lookup failed.",
            ),
            diagnostic_summary=tool_result.error_message
            or "SAM.gov entity lookup failed.",
        )

    matches = tuple(
        _entity_match_from_row(row)
        for row in _entity_rows_from_payload(tool_result.payload)
    )
    if not matches:
        status = SamGovEntityLookupStatus.NOT_FOUND
        diagnostic_summary = "No SAM.gov entity match found."
    elif len(matches) == 1:
        status = SamGovEntityLookupStatus.SUCCESS
        diagnostic_summary = "Resolved one SAM.gov entity record."
    else:
        status = SamGovEntityLookupStatus.AMBIGUOUS
        diagnostic_summary = f"SAM.gov returned {len(matches)} possible entity matches."
    return SamGovEntityLookupResult(
        input_pivot=input_pivot,
        normalized_pivot=normalized_pivot,
        pivot_type=_entity_pivot_type(provenance.source_tool_name),
        status=status,
        provenance=provenance,
        matches=matches,
        source_limitations=_entity_source_limitations(matches, status),
        diagnostic_summary=diagnostic_summary,
    )


def resolve_sam_gov_opportunity_discovery(
    query: SamGovOpportunityDiscoveryQuery,
    *,
    runner: SamGovMcpToolRunner,
    source_mode: SamGovSourceMode = SamGovSourceMode.LIVE_SAM_GOV,
    checked_at: str | None = None,
) -> SamGovOpportunityDiscoveryResult:
    provenance = SamGovEntityLookupProvenance(
        source_tool_name="search_opportunities",
        source_package="sam-gov-mcp",
        source_package_version="0.4.1",
        checked_at=checked_at or datetime.now(UTC).isoformat(),
        source_mode=source_mode,
    )
    tool_arguments = _opportunity_discovery_arguments(query)
    tool_result = runner(provenance.source_tool_name, tool_arguments)
    normalized_query = _normalized_discovery_query(query)
    if not tool_result.ok:
        return SamGovOpportunityDiscoveryResult(
            query=query,
            normalized_query=normalized_query,
            status=SamGovOpportunityDiscoveryStatus.TOOL_ERROR,
            provenance=provenance,
            source_limitations=(
                tool_result.error_message or "SAM.gov opportunity discovery failed.",
            ),
            diagnostic_summary=tool_result.error_message
            or "SAM.gov opportunity discovery failed.",
        )

    rows = _opportunity_rows_from_payload(tool_result.payload)
    records = tuple(_opportunity_record_from_row(row, query) for row in rows)
    total_records = _total_records_from_payload(tool_result.payload, len(records))
    if records:
        status = SamGovOpportunityDiscoveryStatus.SUCCESS
        diagnostic_summary = (
            f"SAM.gov opportunity discovery returned {len(records)} records."
        )
    else:
        status = SamGovOpportunityDiscoveryStatus.NOT_FOUND
        diagnostic_summary = (
            "SAM.gov opportunity discovery returned no official matches."
        )
    return SamGovOpportunityDiscoveryResult(
        query=query,
        normalized_query=normalized_query,
        status=status,
        provenance=provenance,
        records=records,
        total_records=total_records,
        source_limitations=_opportunity_source_limitations(query, records, status),
        diagnostic_summary=diagnostic_summary,
    )


def resolve_sam_gov_known_opportunity(
    query: SamGovKnownOpportunityQuery,
    *,
    runner: SamGovMcpToolRunner,
    source_mode: SamGovSourceMode = SamGovSourceMode.LIVE_SAM_GOV,
    checked_at: str | None = None,
) -> SamGovKnownOpportunityResult:
    normalized_pivot = _normalized_known_opportunity_pivot(query)
    provenance = SamGovEntityLookupProvenance(
        source_tool_name="search_opportunities",
        source_package="sam-gov-mcp",
        source_package_version="0.4.1",
        checked_at=checked_at or datetime.now(UTC).isoformat(),
        source_mode=source_mode,
    )
    tool_arguments = _known_opportunity_arguments(query, normalized_pivot)
    tool_result = runner(provenance.source_tool_name, tool_arguments)
    if not tool_result.ok:
        return SamGovKnownOpportunityResult(
            input_pivot=query.input_pivot,
            normalized_pivot=normalized_pivot,
            pivot_type=query.pivot_type,
            status=SamGovKnownOpportunityStatus.TOOL_ERROR,
            provenance=provenance,
            source_limitations=(
                tool_result.error_message or "SAM.gov known opportunity lookup failed.",
            ),
            diagnostic_summary=tool_result.error_message
            or "SAM.gov known opportunity lookup failed.",
        )

    rows = _opportunity_rows_from_payload(tool_result.payload)
    records = tuple(_known_opportunity_record_from_row(row, query) for row in rows)
    total_records = _total_records_from_payload(tool_result.payload, len(records))
    if not records:
        status = SamGovKnownOpportunityStatus.NOT_FOUND
        diagnostic_summary = (
            "SAM.gov known opportunity lookup returned no official matches."
        )
    elif len(records) == 1:
        status = SamGovKnownOpportunityStatus.SUCCESS
        diagnostic_summary = "Resolved one SAM.gov opportunity record."
    else:
        status = SamGovKnownOpportunityStatus.AMBIGUOUS
        diagnostic_summary = (
            f"SAM.gov returned {len(records)} possible opportunity records."
        )
    return SamGovKnownOpportunityResult(
        input_pivot=query.input_pivot,
        normalized_pivot=normalized_pivot,
        pivot_type=query.pivot_type,
        status=status,
        provenance=provenance,
        records=records,
        total_records=total_records,
        source_limitations=_known_opportunity_source_limitations(
            query,
            records,
            status,
        ),
        diagnostic_summary=diagnostic_summary,
    )


def create_sam_gov_lookup_runner(
    *,
    command: str,
    timeout_seconds: int,
    env: dict[str, str],
) -> SamGovMcpToolRunner:
    def runner(tool_name: str, arguments: dict[str, Any]) -> SamGovMcpToolResult:
        result = run_mcp_tool_command(
            command,
            tool_name,
            arguments,
            timeout_seconds,
            env,
        )
        return SamGovMcpToolResult(
            ok=result.ok,
            payload=result.payload,
            error_message=result.error_message,
        )

    return runner


class SamGovProfileStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, profile: SamGovEnrichmentProfile) -> SamGovEnrichmentProfile:
        self._profile_root.mkdir(parents=True, exist_ok=True)
        self._path(profile.id).write_text(
            profile.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return profile

    def read(self, profile_id: str) -> SamGovEnrichmentProfile:
        return SamGovEnrichmentProfile.model_validate_json(
            self._path(profile_id).read_text(encoding="utf-8")
        )

    def list(self) -> list[SamGovEnrichmentProfile]:
        if not self._profile_root.exists():
            return []
        return [
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self._profile_root.glob("*.json"))
        ]

    def find_by_normalized_pivot(
        self,
        normalized_pivot: str,
    ) -> list[SamGovEnrichmentProfile]:
        requested_pivot = normalized_pivot.strip().upper()
        return [
            profile
            for profile in self.list()
            if profile.normalized_pivot.strip().upper() == requested_pivot
        ]

    @property
    def _profile_root(self) -> Path:
        return self.root / "profiles"

    def _path(self, profile_id: str) -> Path:
        if not profile_id or profile_id != Path(profile_id).name:
            raise ValueError("profile_id must be a file-safe identifier")
        return self._profile_root / f"{profile_id}.json"


def create_sam_gov_enrichment_profile(
    lookup: SamGovEntityLookupResult,
    *,
    profile_id: str | None = None,
    created_at: str | None = None,
) -> SamGovEnrichmentProfile:
    timestamp = created_at or datetime.now(UTC).isoformat()
    resolved_profile_id = profile_id or _profile_id_for_pivot(lookup.normalized_pivot)
    entity_lane = SamGovEntityLane(
        input_pivot=lookup.input_pivot,
        normalized_pivot=lookup.normalized_pivot,
        pivot_type=lookup.pivot_type,
        lookup_status=lookup.status,
        provenance=lookup.provenance,
        matches=lookup.matches,
        source_limitations=lookup.source_limitations,
        diagnostic_summary=lookup.diagnostic_summary,
    )
    review_candidates = _review_candidates_from_entity_lane(
        profile_id=resolved_profile_id,
        normalized_pivot=lookup.normalized_pivot,
        entity_lane=entity_lane,
        created_at=timestamp,
    )
    hermes_events = _hermes_events_from_entity_lane(
        profile_id=resolved_profile_id,
        normalized_pivot=lookup.normalized_pivot,
        entity_lane=entity_lane,
        review_candidates=review_candidates,
        occurred_at=timestamp,
    )
    return SamGovEnrichmentProfile(
        id=resolved_profile_id,
        input_pivot=lookup.input_pivot,
        normalized_pivot=lookup.normalized_pivot,
        entity_lane=entity_lane,
        review_candidates=review_candidates,
        hermes_events=hermes_events,
        created_at=timestamp,
        updated_at=timestamp,
    )


def create_sam_gov_opportunity_discovery_profile(
    discovery: SamGovOpportunityDiscoveryResult,
    *,
    profile_id: str | None = None,
    created_at: str | None = None,
) -> SamGovEnrichmentProfile:
    timestamp = created_at or datetime.now(UTC).isoformat()
    resolved_profile_id = profile_id or _profile_id_for_pivot(
        f"DISCOVERY_{discovery.normalized_query}"
    )
    lane = SamGovOpportunityDiscoveryLane(
        query=discovery.query,
        normalized_query=discovery.normalized_query,
        discovery_status=discovery.status,
        provenance=discovery.provenance,
        records=discovery.records,
        total_records=discovery.total_records,
        source_limitations=discovery.source_limitations,
        diagnostic_summary=discovery.diagnostic_summary,
    )
    review_candidates = _review_candidates_from_discovery_lane(
        profile_id=resolved_profile_id,
        normalized_pivot=discovery.normalized_query,
        lane=lane,
        created_at=timestamp,
    )
    hermes_events = _hermes_events_from_discovery_lane(
        profile_id=resolved_profile_id,
        normalized_pivot=discovery.normalized_query,
        lane=lane,
        review_candidates=review_candidates,
        occurred_at=timestamp,
    )
    return SamGovEnrichmentProfile(
        id=resolved_profile_id,
        input_pivot=discovery.normalized_query,
        normalized_pivot=discovery.normalized_query,
        opportunity_discovery_lane=lane,
        review_candidates=review_candidates,
        hermes_events=hermes_events,
        created_at=timestamp,
        updated_at=timestamp,
    )


def add_sam_gov_known_opportunity_lane(
    profile: SamGovEnrichmentProfile,
    lookup: SamGovKnownOpportunityResult,
    *,
    updated_at: str | None = None,
) -> SamGovEnrichmentProfile:
    timestamp = updated_at or datetime.now(UTC).isoformat()
    lane = SamGovKnownOpportunityLane(
        input_pivot=lookup.input_pivot,
        normalized_pivot=lookup.normalized_pivot,
        pivot_type=lookup.pivot_type,
        lookup_status=lookup.status,
        provenance=lookup.provenance,
        records=lookup.records,
        total_records=lookup.total_records,
        source_limitations=lookup.source_limitations,
        diagnostic_summary=lookup.diagnostic_summary,
    )
    review_candidates = _review_candidates_from_known_opportunity_lane(
        profile_id=profile.id,
        normalized_pivot=lookup.normalized_pivot,
        lane=lane,
        created_at=timestamp,
    )
    hermes_events = _hermes_events_from_known_opportunity_lane(
        profile_id=profile.id,
        normalized_pivot=lookup.normalized_pivot,
        lane=lane,
        review_candidates=review_candidates,
        occurred_at=timestamp,
        starting_event_count=len(profile.hermes_events),
    )
    return profile.model_copy(
        update={
            "known_opportunity_lane": lane,
            "review_candidates": (*profile.review_candidates, *review_candidates),
            "hermes_events": (*profile.hermes_events, *hermes_events),
            "updated_at": timestamp,
        }
    )


def record_sam_gov_review_decision(
    profile: SamGovEnrichmentProfile,
    *,
    candidate_id: str,
    review_state: SamGovReviewState,
    reviewer_rationale: str,
    decided_at: str | None = None,
) -> SamGovEnrichmentProfile:
    if review_state is SamGovReviewState.PENDING_REVIEW:
        raise ValueError("review decision must accept, discard, or route a candidate")
    if not reviewer_rationale.strip():
        raise ValueError("review decision requires reviewer_rationale")
    timestamp = decided_at or datetime.now(UTC).isoformat()
    updated_candidates = []
    matched_candidate: SamGovReviewCandidate | None = None
    for candidate in profile.review_candidates:
        if candidate.id != candidate_id:
            updated_candidates.append(candidate)
            continue
        matched_candidate = candidate.model_copy(
            update={
                "review_state": review_state,
                "trusted_output_written": False,
            }
        )
        updated_candidates.append(matched_candidate)
    if matched_candidate is None:
        raise ValueError("SAM.gov review candidate not found")
    review_event = SamGovHermesEvent(
        id=(
            f"sam_gov_event_{_safe_identifier(profile.id)}_"
            f"{len(profile.hermes_events) + 1:03d}_"
            f"{SamGovHermesEventType.REVIEW_DECISION_RECORDED.value}"
        ),
        event_type=SamGovHermesEventType.REVIEW_DECISION_RECORDED,
        profile_id=profile.id,
        normalized_pivot=profile.normalized_pivot,
        occurred_at=timestamp,
        summary=f"Review decision recorded for {matched_candidate.candidate_type.value}.",
        payload={
            "candidate_id": candidate_id,
            "candidate_type": matched_candidate.candidate_type.value,
            "review_state": review_state.value,
            "reviewer_rationale": reviewer_rationale,
            "source_mode": matched_candidate.source_mode.value,
            "trusted_output_written": False,
        },
    )
    return profile.model_copy(
        update={
            "review_candidates": tuple(updated_candidates),
            "hermes_events": (*profile.hermes_events, review_event),
            "updated_at": timestamp,
        }
    )


def _looks_like_uei(value: str) -> bool:
    return len(value) == 12 and value.isalnum()


def _entity_lookup_arguments(
    normalized_pivot: str,
    *,
    source_tool_name: str,
    lookup_limit: int,
) -> dict[str, Any]:
    include_sections = ["entityRegistration", "coreData", "assertions"]
    if source_tool_name == "lookup_entity_by_uei":
        return {
            "uei": normalized_pivot,
            "include_sections": include_sections,
            "sam_registered": "Yes",
        }
    return {
        "legal_business_name": normalized_pivot,
        "include_sections": include_sections,
        "page": 0,
        "size": min(max(lookup_limit, 1), 10),
    }


def _entity_pivot_type(source_tool_name: str) -> str:
    if source_tool_name == "lookup_entity_by_uei":
        return "uei"
    return "legal_business_name"


def _opportunity_discovery_arguments(
    query: SamGovOpportunityDiscoveryQuery,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "posted_from": query.posted_from,
        "posted_to": query.posted_to,
        "limit": query.limit,
        "offset": query.offset,
    }
    if notice_type := _sam_notice_type_code(query.notice_type):
        arguments["notice_type"] = notice_type
    if title := _opportunity_title_query(query):
        arguments["title"] = title
    if query.naics_code:
        arguments["naics_code"] = query.naics_code
    if query.psc_code:
        arguments["psc_code"] = query.psc_code
    if query.set_aside:
        arguments["set_aside"] = query.set_aside
    if query.response_deadline_from:
        arguments["response_deadline_from"] = query.response_deadline_from
    if query.response_deadline_to:
        arguments["response_deadline_to"] = query.response_deadline_to
    if query.state:
        arguments["state"] = query.state
    if query.zip_code:
        arguments["zip_code"] = query.zip_code
    if agency_keyword := _agency_keyword_query(query):
        arguments["agency_keyword"] = agency_keyword
    return arguments


def _known_opportunity_arguments(
    query: SamGovKnownOpportunityQuery,
    normalized_pivot: str,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "posted_from": query.posted_from,
        "posted_to": query.posted_to,
        "limit": query.limit,
        "offset": query.offset,
    }
    if query.pivot_type is SamGovKnownOpportunityPivotType.NOTICE_ID:
        arguments["notice_id"] = normalized_pivot
    else:
        arguments["solicitation_number"] = normalized_pivot
    return arguments


def _normalized_known_opportunity_pivot(query: SamGovKnownOpportunityQuery) -> str:
    pivot = query.input_pivot.strip()
    if query.pivot_type is SamGovKnownOpportunityPivotType.SOLICITATION_NUMBER:
        return pivot.upper()
    return pivot


def _sam_notice_type_code(notice_type: str | None) -> str | None:
    if not notice_type:
        return None
    normalized = notice_type.strip().lower().replace(" ", "_").replace("-", "_")
    if len(normalized) == 1:
        return normalized
    return {
        "presolicitation": "p",
        "solicitation": "o",
        "combined_synopsis_solicitation": "k",
        "sources_sought": "r",
        "source_sought": "r",
        "rfi": "r",
        "special_notice": "s",
        "intent_to_bundle": "i",
        "award_notice": "a",
        "justification": "u",
    }.get(normalized)


def _opportunity_title_query(query: SamGovOpportunityDiscoveryQuery) -> str | None:
    pieces = _populated_texts(
        query.program_name, query.old_program_name, *query.keywords
    )
    return " ".join(pieces) if pieces else None


def _agency_keyword_query(query: SamGovOpportunityDiscoveryQuery) -> str | None:
    pieces = _populated_texts(query.customer_agency, query.office)
    return " ".join(pieces) if pieces else None


def _normalized_discovery_query(query: SamGovOpportunityDiscoveryQuery) -> str:
    pieces = _populated_texts(
        query.customer_agency,
        query.office,
        query.program_name,
        query.old_program_name,
        *query.keywords,
        query.notice_type,
        query.naics_code,
        query.psc_code,
        query.set_aside,
    )
    if not pieces:
        pieces = (f"{query.posted_from}_{query.posted_to}",)
    return " ".join(pieces).upper()


def _opportunity_rows_from_payload(
    payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], ...]:
    if not payload:
        return ()
    for key in ("opportunitiesData", "results", "data", "opportunities"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return tuple(row for row in rows if isinstance(row, dict))
    if _string_from_keys(payload, "noticeId", "notice_id", "solicitationNumber"):
        return (payload,)
    return ()


def _total_records_from_payload(
    payload: dict[str, Any] | None,
    fallback: int,
) -> int | None:
    if not payload:
        return fallback
    for key in ("totalRecords", "total_records", "total", "count"):
        value = payload.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except TypeError, ValueError:
            return fallback
    return fallback


def _opportunity_record_from_row(
    row: dict[str, Any],
    query: SamGovOpportunityDiscoveryQuery,
) -> SamGovOpportunityRecord:
    fields = _base_opportunity_record_from_row(row)
    rationale = _opportunity_match_rationale(fields, query)
    ambiguity_notes = _opportunity_ambiguity_notes(fields, query, rationale)
    return fields.model_copy(
        update={
            "match_rationale": rationale,
            "match_confidence": _opportunity_match_confidence(fields, query, rationale),
            "ambiguity_notes": ambiguity_notes,
        }
    )


def _known_opportunity_record_from_row(
    row: dict[str, Any],
    query: SamGovKnownOpportunityQuery,
) -> SamGovOpportunityRecord:
    fields = _base_opportunity_record_from_row(row)
    rationale = _known_opportunity_match_rationale(fields, query)
    return fields.model_copy(
        update={
            "match_rationale": rationale,
            "match_confidence": 0.9 if rationale else 0.55,
            "ambiguity_notes": _known_opportunity_ambiguity_notes(fields, query),
        }
    )


def _base_opportunity_record_from_row(row: dict[str, Any]) -> SamGovOpportunityRecord:
    title = _string_from_keys(row, "title", "opportunityTitle")
    organization_path = _string_from_keys(
        row,
        "fullParentPathName",
        "organizationPath",
        "agency",
        "department",
    )
    notice_type = _string_from_keys(row, "type", "noticeType", "baseType")
    return SamGovOpportunityRecord(
        notice_id=_string_from_keys(row, "noticeId", "notice_id", "id"),
        solicitation_number=_string_from_keys(
            row,
            "solicitationNumber",
            "solicitation_number",
        ),
        title=title,
        notice_type=notice_type,
        organization_path=organization_path,
        posted_date=_string_from_keys(row, "postedDate", "posted_date"),
        response_deadline=_string_from_keys(
            row,
            "responseDeadLine",
            "responseDeadline",
            "response_deadline",
        ),
        set_aside=_string_from_keys(row, "setAside", "set_aside"),
        naics_code=_string_from_keys(row, "naicsCode", "naics_code"),
        psc_code=_string_from_keys(
            row,
            "classificationCode",
            "pscCode",
            "psc_code",
        ),
        place_of_performance=_place_of_performance_from_row(row),
        description_url=_string_from_keys(row, "description", "descriptionUrl"),
        ui_link=_string_from_keys(row, "uiLink", "samLink", "url"),
        active=_bool_from_keys(row, "active", "isActive", "activeFlag"),
        archive_type=_string_from_keys(row, "archiveType", "archive_type"),
        archive_date=_string_from_keys(row, "archiveDate", "archive_date"),
        point_of_contact=_point_of_contact_from_row(row),
        raw_record=row,
    )


def _place_of_performance_from_row(row: dict[str, Any]) -> str | None:
    place = row.get("placeOfPerformance") or row.get("place_of_performance")
    if isinstance(place, dict):
        return ", ".join(_populated_texts(*[str(value) for value in place.values()]))
    if place is None:
        return None
    text = str(place).strip()
    return text or None


def _point_of_contact_from_row(row: dict[str, Any]) -> tuple[str, ...]:
    value = row.get("pointOfContact") or row.get("point_of_contact") or row.get("poc")
    if isinstance(value, list):
        return tuple(_point_of_contact_label(item) for item in value if item)
    if isinstance(value, dict):
        return (_point_of_contact_label(value),)
    if value is None:
        return ()
    text = str(value).strip()
    return (text,) if text else ()


def _point_of_contact_label(item: object) -> str:
    if not isinstance(item, dict):
        return str(item).strip()
    name = _string_from_keys(item, "fullName", "name", "contactName")
    email = _string_from_keys(item, "email", "emailAddress")
    phone = _string_from_keys(item, "phone", "phoneNumber")
    if name and email:
        return f"{name} <{email}>"
    return " - ".join(_populated_texts(name, email, phone))


def _bool_from_keys(row: dict[str, Any], *keys: str) -> bool | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"yes", "true", "1", "active"}:
            return True
        if text in {"no", "false", "0", "inactive", "archived"}:
            return False
    return None


def _known_opportunity_match_rationale(
    record: SamGovOpportunityRecord,
    query: SamGovKnownOpportunityQuery,
) -> tuple[str, ...]:
    if (
        query.pivot_type is SamGovKnownOpportunityPivotType.SOLICITATION_NUMBER
        and record.solicitation_number
        and record.solicitation_number.upper() == query.input_pivot.strip().upper()
    ):
        return ("solicitation_number matched official SAM.gov record",)
    if (
        query.pivot_type is SamGovKnownOpportunityPivotType.NOTICE_ID
        and record.notice_id
        and record.notice_id == query.input_pivot.strip()
    ):
        return ("notice_id matched official SAM.gov record",)
    return ()


def _known_opportunity_ambiguity_notes(
    record: SamGovOpportunityRecord,
    query: SamGovKnownOpportunityQuery,
) -> tuple[str, ...]:
    notes = []
    if not _known_opportunity_match_rationale(record, query):
        notes.append("official record did not echo requested clean pivot")
    if record.active is False or record.archive_type or record.archive_date:
        notes.append("official record appears archived or inactive")
    if not record.response_deadline:
        notes.append("response deadline not exposed in known opportunity result")
    return tuple(notes)


def _opportunity_match_rationale(
    record: SamGovOpportunityRecord,
    query: SamGovOpportunityDiscoveryQuery,
) -> tuple[str, ...]:
    rationale = []
    title = (record.title or "").lower()
    organization_path = (record.organization_path or "").lower()
    if query.program_name and query.program_name.lower() in title:
        rationale.append("program_name matched title")
    if query.old_program_name and query.old_program_name.lower() in title:
        rationale.append("old_program_name matched title")
    for keyword in query.keywords:
        if keyword.lower() in title:
            rationale.append(f"keyword matched title: {keyword}")
    if query.customer_agency and query.customer_agency.lower() in organization_path:
        rationale.append("customer_agency matched organization path")
    if query.office and query.office.lower() in organization_path:
        rationale.append("office matched organization path")
    if query.notice_type and _notice_type_matches(
        record.notice_type, query.notice_type
    ):
        rationale.append("notice_type matched requested phase")
    if query.naics_code and query.naics_code == record.naics_code:
        rationale.append("naics_code matched")
    if query.psc_code and query.psc_code == record.psc_code:
        rationale.append("psc_code matched")
    if query.set_aside and query.set_aside == record.set_aside:
        rationale.append("set_aside matched")
    return tuple(
        rationale or ("official SAM.gov result matched requested date window",)
    )


def _notice_type_matches(record_notice_type: str | None, requested: str) -> bool:
    if record_notice_type is None:
        return False
    requested_code = _sam_notice_type_code(requested)
    text = record_notice_type.lower().replace(" ", "_").replace("/", "_")
    if requested_code == "r":
        return "source" in text or "rfi" in text
    if requested_code == "s":
        return "special" in text
    if requested_code == "o":
        return "solicitation" in text and "combined" not in text
    if requested_code == "k":
        return "combined" in text
    if requested_code == "p":
        return "presolicitation" in text or "pre_solicitation" in text
    return requested_code == text


def _opportunity_ambiguity_notes(
    record: SamGovOpportunityRecord,
    query: SamGovOpportunityDiscoveryQuery,
    rationale: tuple[str, ...],
) -> tuple[str, ...]:
    notes = []
    if query.old_program_name and record.title:
        title = record.title.lower()
        if query.old_program_name.lower() in title:
            notes.append("renamed-program clue")
    if not any("program_name" in item for item in rationale) and query.program_name:
        notes.append("requested program_name did not exactly match title")
    if not record.response_deadline:
        notes.append("response deadline not exposed in discovery result")
    return tuple(notes)


def _opportunity_match_confidence(
    record: SamGovOpportunityRecord,
    query: SamGovOpportunityDiscoveryQuery,
    rationale: tuple[str, ...],
) -> float:
    confidence = 0.45
    confidence += 0.15 * sum("program_name" in item for item in rationale)
    confidence += 0.12 * sum("old_program_name" in item for item in rationale)
    confidence += 0.1 * sum("customer_agency" in item for item in rationale)
    confidence += 0.08 * sum("office" in item for item in rationale)
    confidence += 0.08 * sum("notice_type" in item for item in rationale)
    confidence += 0.05 * sum("naics_code" in item for item in rationale)
    confidence += 0.05 * sum("psc_code" in item for item in rationale)
    confidence += 0.04 * sum("set_aside" in item for item in rationale)
    if record.notice_id:
        confidence += 0.05
    if query.keywords and any("keyword" in item for item in rationale):
        confidence += 0.05
    if query.program_name and not any("program_name" in item for item in rationale):
        confidence -= 0.15
    return round(min(confidence, 0.95), 2)


def _opportunity_source_limitations(
    query: SamGovOpportunityDiscoveryQuery,
    records: tuple[SamGovOpportunityRecord, ...],
    status: SamGovOpportunityDiscoveryStatus,
) -> tuple[str, ...]:
    limitations = [
        "SAM.gov opportunity discovery is official-source search, not broad web research."
    ]
    if status is SamGovOpportunityDiscoveryStatus.NOT_FOUND:
        limitations.append(
            "SAM.gov opportunity discovery returned no official matches."
        )
    if query.keywords:
        limitations.append(
            "SAM.gov search_opportunities does not search full description text in this lane."
        )
    if records and any(record.match_confidence < 0.65 for record in records):
        limitations.append(
            "Some discovery matches are weak or ambiguous and need review."
        )
    return tuple(limitations)


def _known_opportunity_source_limitations(
    query: SamGovKnownOpportunityQuery,
    records: tuple[SamGovOpportunityRecord, ...],
    status: SamGovKnownOpportunityStatus,
) -> tuple[str, ...]:
    limitations = [
        "SAM.gov known opportunity lookup is scoped to the submitted identifier and posted-date window."
    ]
    if status is SamGovKnownOpportunityStatus.NOT_FOUND:
        limitations.append(
            "SAM.gov known opportunity lookup returned no official matches."
        )
    if status is SamGovKnownOpportunityStatus.AMBIGUOUS:
        limitations.append(
            "Multiple SAM.gov opportunity records matched the clean pivot and require review."
        )
    if records and any(
        record.active is False or record.archive_type or record.archive_date
        for record in records
    ):
        limitations.append(
            "SAM.gov opportunity record appears inactive, archived, or stale; verify current status before capture action."
        )
    if records and any(not record.response_deadline for record in records):
        limitations.append(
            "SAM.gov opportunity response did not expose a response deadline for every matched record."
        )
    if query.pivot_type is SamGovKnownOpportunityPivotType.SOLICITATION_NUMBER:
        limitations.append(
            "Solicitation-number lookup depends on SAM.gov search_opportunities date-window coverage."
        )
    return tuple(limitations)


def _populated_texts(*values: str | None) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value and value.strip())


def _entity_rows_from_payload(
    payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], ...]:
    if not payload:
        return ()
    for key in ("results", "entities", "entityData", "entityList", "data"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return tuple(row for row in rows if isinstance(row, dict))
    if "entityRegistration" in payload or _string_from_keys(
        payload,
        "uei",
        "ueiSAM",
        "legalBusinessName",
        "entityName",
    ):
        return (payload,)
    return ()


def _entity_match_from_row(row: dict[str, Any]) -> SamGovEntityMatch:
    entity_registration = _dict_from_key(row, "entityRegistration") or row
    core_data = _dict_from_key(row, "coreData")
    assertions = _dict_from_key(row, "assertions")
    hierarchy = (
        _dict_from_key(core_data, "entityHierarchy")
        or _dict_from_key(core_data, "entityHierarchyInformation")
        or _dict_from_key(row, "entityHierarchy")
        or _dict_from_key(row, "entityHierarchyInformation")
    )
    immediate_parent = _dict_from_key(hierarchy, "immediateParent") or hierarchy
    return SamGovEntityMatch(
        uei=_string_from_keys(
            entity_registration,
            "uei",
            "ueiSAM",
            "ueiSam",
            "uniqueEntityId",
        ),
        legal_business_name=_string_from_keys(
            entity_registration,
            "legalBusinessName",
            "entityName",
            "businessName",
            "legal_business_name",
        ),
        cage_code=_string_from_keys(
            entity_registration,
            "cageCode",
            "cage_code",
            "cage",
        ),
        registration_status=_string_from_keys(
            entity_registration,
            "registrationStatus",
            "samRegistrationStatus",
            "registration_status",
        ),
        parent_uei=_string_from_keys(
            immediate_parent,
            "parentUei",
            "parentUEI",
            "uei",
            "ueiSAM",
        ),
        parent_legal_business_name=_string_from_keys(
            immediate_parent,
            "parentLegalBusinessName",
            "legalBusinessName",
            "entityName",
        ),
        business_types=_business_types_from_core_data(core_data or row),
        naics_codes=_codes_from_assertions(assertions, "naics"),
        psc_codes=_codes_from_assertions(assertions, "psc"),
        responsibility_notes=_responsibility_notes_from_row(row),
        raw_record=row,
    )


def _dict_from_key(row: dict[str, Any] | None, key: str) -> dict[str, Any] | None:
    if row is None:
        return None
    value = row.get(key)
    return value if isinstance(value, dict) else None


def _string_from_keys(row: dict[str, Any] | None, *keys: str) -> str | None:
    if row is None:
        return None
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _business_types_from_core_data(row: dict[str, Any]) -> tuple[str, ...]:
    value = row.get("businessTypes") or row.get("businessTypeList")
    if isinstance(value, list):
        return tuple(_label_from_code_item(item, "businessTypeDesc") for item in value)
    business_types = _dict_from_key(row, "businessTypes")
    if business_types is None:
        return ()
    business_type_list = business_types.get("businessTypeList")
    if isinstance(business_type_list, list):
        return tuple(
            _label_from_code_item(item, "businessTypeDesc")
            for item in business_type_list
        )
    return ()


def _codes_from_assertions(
    assertions: dict[str, Any] | None,
    code_family: str,
) -> tuple[str, ...]:
    if assertions is None:
        return ()
    direct_key = "naicsCodes" if code_family == "naics" else "pscCodes"
    direct_codes = assertions.get(direct_key)
    if isinstance(direct_codes, list):
        return tuple(str(code).strip() for code in direct_codes if str(code).strip())
    goods_and_services = _dict_from_key(assertions, "goodsAndServices") or assertions
    list_key = "naicsList" if code_family == "naics" else "pscList"
    code_key = "naicsCode" if code_family == "naics" else "pscCode"
    code_list = goods_and_services.get(list_key)
    if isinstance(code_list, list):
        return tuple(_label_from_code_item(item, code_key) for item in code_list)
    return ()


def _responsibility_notes_from_row(row: dict[str, Any]) -> tuple[str, ...]:
    notes = row.get("responsibilityNotes") or row.get("responsibility_notes")
    if isinstance(notes, list):
        return tuple(str(note).strip() for note in notes if str(note).strip())
    exclusion_status = _string_from_keys(row, "exclusionStatus", "exclusion_status")
    if exclusion_status:
        return (f"Exclusion status: {exclusion_status}",)
    return ()


def _label_from_code_item(item: object, preferred_key: str) -> str:
    if isinstance(item, dict):
        return str(
            item.get(preferred_key)
            or item.get("description")
            or item.get("code")
            or item
        ).strip()
    return str(item).strip()


def _entity_source_limitations(
    matches: tuple[SamGovEntityMatch, ...],
    status: SamGovEntityLookupStatus,
) -> tuple[str, ...]:
    limitations = [
        "SAM.gov entity data is an official registration signal, not a complete capability picture."
    ]
    if status is SamGovEntityLookupStatus.NOT_FOUND:
        limitations.append("SAM.gov entity lookup returned no official matches.")
    if status is SamGovEntityLookupStatus.AMBIGUOUS:
        limitations.append("Multiple SAM.gov entity matches require review.")
    if matches and not any(match.parent_uei for match in matches):
        limitations.append(
            "SAM.gov entity response did not expose parent UEI or hierarchy context."
        )
    return tuple(limitations)


def _review_candidates_from_entity_lane(
    *,
    profile_id: str,
    normalized_pivot: str,
    entity_lane: SamGovEntityLane,
    created_at: str,
) -> tuple[SamGovReviewCandidate, ...]:
    candidates: list[SamGovReviewCandidate] = []
    match = entity_lane.matches[0] if entity_lane.matches else None
    if match is not None:
        source_fields = _match_source_fields(match)
        if source_fields:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=entity_lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.SOURCE_EVIDENCE,
                    candidate_key="source_evidence_entity_record",
                    title="Source Evidence: SAM.gov entity record",
                    content=_entity_source_content(source_fields),
                    target_workflow="evidence_store",
                    recommendation="Review before accepting official SAM.gov entity facts as Source Evidence.",
                    rationale="SAM.gov supplied entity registration fields; blanks remain source limitations.",
                    source_fields=tuple(field for field, value in source_fields),
                    source_values=tuple(value for field, value in source_fields),
                    confidence=0.78,
                    created_at=created_at,
                )
            )
        if match.legal_business_name:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=entity_lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.PACKET_FIELD_ANSWER,
                    candidate_key="packet_field_incumbent",
                    title="Packet Field Answer: incumbent",
                    content=f"SAM.gov entity signal: {match.legal_business_name}",
                    target_workflow="living_briefing_packet",
                    recommendation="Review before accepting as a packet field answer.",
                    rationale="The SAM.gov Entity Record can support incumbent or vendor identity fields.",
                    source_fields=("entity_lane.matches.legal_business_name",),
                    source_values=(match.legal_business_name,),
                    field_key="incumbent",
                    confidence=0.72,
                    created_at=created_at,
                )
            )
        if match.parent_uei or match.business_types or match.responsibility_notes:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=entity_lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.RISK_REGISTER_SIGNAL,
                    candidate_key="risk_register_vendor_ecosystem",
                    title="Risk Register signal: vendor ecosystem",
                    content="Review entity hierarchy, business types, and responsibility notes for capture risk.",
                    target_workflow="risk_register",
                    recommendation="Review before treating entity registration context as a pursuit risk.",
                    rationale="Entity hierarchy and responsibility signals can affect teaming, eligibility, or follow-up research.",
                    source_fields=_entity_ecosystem_fields(match),
                    source_values=_entity_ecosystem_values(match),
                    confidence=0.61,
                    created_at=created_at,
                )
            )
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=entity_lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.CALL_PLAN_SIGNAL,
                    candidate_key="call_plan_vendor_follow_up",
                    title="Call Plan signal: vendor follow-up",
                    content="Prepare follow-up around entity hierarchy, teaming fit, or responsibility context.",
                    target_workflow="call_plan",
                    recommendation="Review before preparing customer, partner, or vendor outreach.",
                    rationale="SAM.gov entity data can seed follow-up questions but is not a complete capability picture.",
                    source_fields=_entity_ecosystem_fields(match),
                    source_values=_entity_ecosystem_values(match),
                    confidence=0.6,
                    created_at=created_at,
                )
            )
    candidates.append(
        _review_candidate(
            profile_id=profile_id,
            normalized_pivot=normalized_pivot,
            source_mode=entity_lane.provenance.source_mode,
            candidate_type=SamGovReviewCandidateType.ACTION_PLAN_ITEM,
            candidate_key="action_plan_entity_follow_up",
            title="Action Plan: review SAM.gov entity enrichment",
            content="Review official entity record signals and source limitations before routing capture work.",
            target_workflow="capture_action_plan",
            recommendation="Create an action only after review confirms the next capture outcome.",
            rationale="The SAM.gov Entity Record lane has reviewable facts, gaps, or follow-up needs.",
            source_fields=("profile_id",),
            source_values=(profile_id,),
            confidence=0.68,
            created_at=created_at,
        )
    )
    return tuple(candidates)


def _review_candidates_from_discovery_lane(
    *,
    profile_id: str,
    normalized_pivot: str,
    lane: SamGovOpportunityDiscoveryLane,
    created_at: str,
) -> tuple[SamGovReviewCandidate, ...]:
    candidates: list[SamGovReviewCandidate] = []
    record = lane.records[0] if lane.records else None
    if record is not None:
        source_fields = _opportunity_source_fields(record)
        if source_fields:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.SOURCE_EVIDENCE,
                    candidate_key="source_evidence_opportunity_discovery",
                    title="Source Evidence: SAM.gov opportunity notice",
                    content=_opportunity_source_content(source_fields),
                    target_workflow="evidence_store",
                    recommendation="Review before accepting official SAM.gov opportunity fields as Source Evidence.",
                    rationale="SAM.gov supplied opportunity notice fields with retrieved-at provenance.",
                    source_fields=tuple(field for field, value in source_fields),
                    source_values=tuple(value for field, value in source_fields),
                    confidence=record.match_confidence,
                    created_at=created_at,
                )
            )
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_pivot=normalized_pivot,
                source_mode=lane.provenance.source_mode,
                candidate_type=SamGovReviewCandidateType.DERIVED_EVIDENCE,
                candidate_key="derived_evidence_opportunity_match_rationale",
                title="Derived Evidence: opportunity match rationale",
                content="; ".join(record.match_rationale),
                target_workflow="evidence_store",
                recommendation="Review rationale before using it to support a capture decision.",
                rationale="Match confidence is Ariadne interpretation layered on official SAM.gov fields.",
                source_fields=(
                    "opportunity_discovery_lane.records.match_rationale",
                    "opportunity_discovery_lane.records.match_confidence",
                ),
                source_values=(
                    "; ".join(record.match_rationale),
                    str(record.match_confidence),
                ),
                confidence=record.match_confidence,
                created_at=created_at,
            )
        )
        if record.title or record.solicitation_number:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.PACKET_FIELD_ANSWER,
                    candidate_key="packet_field_opportunity_notice",
                    title="Packet Field Answer: opportunity notice",
                    content=_opportunity_packet_content(record),
                    target_workflow="living_briefing_packet",
                    recommendation="Review before updating packet opportunity fields.",
                    rationale="Discovery results can seed opportunity identity and phase fields.",
                    source_fields=_opportunity_packet_fields(record),
                    source_values=_opportunity_packet_values(record),
                    field_key="opportunity_notice",
                    confidence=min(record.match_confidence, 0.8),
                    created_at=created_at,
                )
            )
        if record.notice_type or record.response_deadline:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.CALL_PLAN_SIGNAL,
                    candidate_key="call_plan_opportunity_timing",
                    title="Call Plan signal: opportunity timing",
                    content="Review notice phase and response timing before outreach.",
                    target_workflow="call_plan",
                    recommendation="Review before using discovery timing for customer or partner calls.",
                    rationale="Notice type and deadline can shape outreach sequence.",
                    source_fields=_opportunity_timing_fields(record),
                    source_values=_opportunity_timing_values(record),
                    confidence=min(record.match_confidence, 0.72),
                    created_at=created_at,
                )
            )
    candidates.append(
        _review_candidate(
            profile_id=profile_id,
            normalized_pivot=normalized_pivot,
            source_mode=lane.provenance.source_mode,
            candidate_type=SamGovReviewCandidateType.ACTION_PLAN_ITEM,
            candidate_key="action_plan_opportunity_discovery_follow_up",
            title="Action Plan: review SAM.gov opportunity discovery",
            content=lane.diagnostic_summary,
            target_workflow="capture_action_plan",
            recommendation="Review official notices, weak matches, and gaps before routing capture work.",
            rationale="Opportunity discovery can identify next research and capture steps without writing trusted outputs.",
            source_fields=("opportunity_discovery_lane.normalized_query",),
            source_values=(lane.normalized_query,),
            confidence=0.66 if lane.records else 0.45,
            created_at=created_at,
        )
    )
    if _needs_web_enrichment_support(lane):
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_pivot=normalized_pivot,
                source_mode=lane.provenance.source_mode,
                candidate_type=SamGovReviewCandidateType.FOLLOW_UP_ROUTE,
                candidate_key="follow_up_web_enrichment_support",
                title="Follow-up Route: Web Enrichment Support",
                content="Route to deferred Web Enrichment Support when official SAM.gov discovery is insufficient.",
                target_workflow="web_enrichment_support",
                recommendation="Use only as a reviewed follow-up route; this slice does not invoke web crawling.",
                rationale="No-result, weak, or ambiguous official results may need web enrichment later.",
                source_fields=(
                    "opportunity_discovery_lane.discovery_status",
                    "opportunity_discovery_lane.source_limitations",
                ),
                source_values=(
                    lane.discovery_status.value,
                    "; ".join(lane.source_limitations),
                ),
                confidence=0.55,
                created_at=created_at,
            )
        )
    return tuple(candidates)


def _review_candidates_from_known_opportunity_lane(
    *,
    profile_id: str,
    normalized_pivot: str,
    lane: SamGovKnownOpportunityLane,
    created_at: str,
) -> tuple[SamGovReviewCandidate, ...]:
    candidates: list[SamGovReviewCandidate] = []
    record = lane.records[0] if lane.records else None
    if record is not None:
        source_fields = _known_opportunity_source_fields(record)
        if source_fields:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.SOURCE_EVIDENCE,
                    candidate_key="source_evidence_known_opportunity_record",
                    title="Source Evidence: SAM.gov known opportunity record",
                    content=_opportunity_source_content(source_fields),
                    target_workflow="evidence_store",
                    recommendation="Review before accepting official SAM.gov opportunity fields as Source Evidence.",
                    rationale="SAM.gov matched a clean solicitation or notice pivot with retrieved-at provenance.",
                    source_fields=tuple(field for field, value in source_fields),
                    source_values=tuple(value for field, value in source_fields),
                    confidence=record.match_confidence,
                    created_at=created_at,
                )
            )
        if record.title or record.solicitation_number or record.notice_id:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.PACKET_FIELD_ANSWER,
                    candidate_key="packet_field_known_opportunity_record",
                    title="Packet Field Answer: known opportunity record",
                    content=_opportunity_packet_content(record),
                    target_workflow="living_briefing_packet",
                    recommendation="Review before updating packet opportunity fields.",
                    rationale="Known SAM.gov opportunity data can support opportunity identity, customer, timing, and phase fields.",
                    source_fields=_known_opportunity_packet_fields(record),
                    source_values=_known_opportunity_packet_values(record),
                    field_key="known_opportunity_record",
                    confidence=min(record.match_confidence, 0.86),
                    created_at=created_at,
                )
            )
        if record.notice_type or record.response_deadline or record.point_of_contact:
            candidates.append(
                _review_candidate(
                    profile_id=profile_id,
                    normalized_pivot=normalized_pivot,
                    source_mode=lane.provenance.source_mode,
                    candidate_type=SamGovReviewCandidateType.CALL_PLAN_SIGNAL,
                    candidate_key="call_plan_known_opportunity_timing",
                    title="Call Plan signal: known opportunity timing",
                    content="Review notice phase, response timing, and point-of-contact fields before outreach.",
                    target_workflow="call_plan",
                    recommendation="Review before using known opportunity fields for customer or partner calls.",
                    rationale="Known SAM.gov notice fields can shape outreach sequence and timing.",
                    source_fields=_known_opportunity_timing_fields(record),
                    source_values=_known_opportunity_timing_values(record),
                    confidence=min(record.match_confidence, 0.78),
                    created_at=created_at,
                )
            )
    candidates.append(
        _review_candidate(
            profile_id=profile_id,
            normalized_pivot=normalized_pivot,
            source_mode=lane.provenance.source_mode,
            candidate_type=SamGovReviewCandidateType.ACTION_PLAN_ITEM,
            candidate_key="action_plan_known_opportunity_review",
            title="Action Plan: review SAM.gov known opportunity record",
            content=lane.diagnostic_summary,
            target_workflow="capture_action_plan",
            recommendation="Review official opportunity fields, stale-data clues, and gaps before routing capture work.",
            rationale="Known opportunity lookup can confirm timing and identifiers without writing trusted outputs.",
            source_fields=("known_opportunity_lane.normalized_pivot",),
            source_values=(lane.normalized_pivot,),
            confidence=0.72 if lane.records else 0.45,
            created_at=created_at,
        )
    )
    return tuple(candidates)


def _review_candidate(
    *,
    profile_id: str,
    normalized_pivot: str,
    source_mode: SamGovSourceMode,
    candidate_type: SamGovReviewCandidateType,
    candidate_key: str,
    title: str,
    content: str,
    target_workflow: str,
    recommendation: str,
    rationale: str,
    source_fields: tuple[str, ...],
    source_values: tuple[str, ...],
    created_at: str,
    field_key: str | None = None,
    confidence: float | None = None,
) -> SamGovReviewCandidate:
    return SamGovReviewCandidate(
        id=f"sam_gov_candidate_{_safe_identifier(profile_id)}_{_safe_identifier(candidate_key)}",
        candidate_type=candidate_type,
        title=title,
        content=content,
        target_workflow=target_workflow,
        recommendation=recommendation,
        rationale=rationale,
        source_profile_id=profile_id,
        normalized_pivot=normalized_pivot,
        source_mode=source_mode,
        source_fields=source_fields,
        source_values=source_values,
        field_key=field_key,
        confidence=confidence,
        created_at=created_at,
    )


def _hermes_events_from_discovery_lane(
    *,
    profile_id: str,
    normalized_pivot: str,
    lane: SamGovOpportunityDiscoveryLane,
    review_candidates: tuple[SamGovReviewCandidate, ...],
    occurred_at: str,
) -> tuple[SamGovHermesEvent, ...]:
    events: list[SamGovHermesEvent] = []

    def append_event(
        event_type: SamGovHermesEventType,
        *,
        summary: str,
        payload: dict[str, object],
    ) -> None:
        events.append(
            SamGovHermesEvent(
                id=(
                    f"sam_gov_event_{_safe_identifier(profile_id)}_"
                    f"{len(events) + 1:03d}_{event_type.value}"
                ),
                event_type=event_type,
                profile_id=profile_id,
                normalized_pivot=normalized_pivot,
                occurred_at=occurred_at,
                summary=summary,
                payload=payload,
            )
        )

    append_event(
        SamGovHermesEventType.PROFILE_STARTED,
        summary="SAM.gov Enrichment Profile started.",
        payload={
            "profile_id": profile_id,
            "normalized_pivot": normalized_pivot,
            "source_mode": lane.provenance.source_mode.value,
        },
    )
    append_event(
        SamGovHermesEventType.OPPORTUNITY_DISCOVERY_RUN,
        summary="SAM.gov Opportunity Discovery lane searched official notices.",
        payload={
            "record_count": len(lane.records),
            "total_records": lane.total_records,
            "discovery_status": lane.discovery_status.value,
            "source_tool_name": lane.provenance.source_tool_name,
        },
    )
    if lane.source_limitations:
        append_event(
            SamGovHermesEventType.SOURCE_LIMITATION_DETECTED,
            summary="SAM.gov Opportunity Discovery lane source limitations detected.",
            payload={"source_limitations": list(lane.source_limitations)},
        )
    if review_candidates:
        append_event(
            SamGovHermesEventType.REVIEW_CANDIDATES_CREATED,
            summary="SAM.gov review candidates created.",
            payload={
                "candidate_count": len(review_candidates),
                "candidate_types": [
                    candidate.candidate_type.value for candidate in review_candidates
                ],
            },
        )
    return tuple(events)


def _hermes_events_from_known_opportunity_lane(
    *,
    profile_id: str,
    normalized_pivot: str,
    lane: SamGovKnownOpportunityLane,
    review_candidates: tuple[SamGovReviewCandidate, ...],
    occurred_at: str,
    starting_event_count: int,
) -> tuple[SamGovHermesEvent, ...]:
    events: list[SamGovHermesEvent] = []

    def append_event(
        event_type: SamGovHermesEventType,
        *,
        summary: str,
        payload: dict[str, object],
    ) -> None:
        events.append(
            SamGovHermesEvent(
                id=(
                    f"sam_gov_event_{_safe_identifier(profile_id)}_"
                    f"{starting_event_count + len(events) + 1:03d}_{event_type.value}"
                ),
                event_type=event_type,
                profile_id=profile_id,
                normalized_pivot=normalized_pivot,
                occurred_at=occurred_at,
                summary=summary,
                payload=payload,
            )
        )

    append_event(
        SamGovHermesEventType.KNOWN_OPPORTUNITY_RESOLVED,
        summary="SAM.gov Known Opportunity lane resolved official opportunity records.",
        payload={
            "record_count": len(lane.records),
            "total_records": lane.total_records,
            "lookup_status": lane.lookup_status.value,
            "pivot_type": lane.pivot_type.value,
            "source_tool_name": lane.provenance.source_tool_name,
        },
    )
    if lane.source_limitations:
        append_event(
            SamGovHermesEventType.SOURCE_LIMITATION_DETECTED,
            summary="SAM.gov Known Opportunity lane source limitations detected.",
            payload={"source_limitations": list(lane.source_limitations)},
        )
    if review_candidates:
        append_event(
            SamGovHermesEventType.REVIEW_CANDIDATES_CREATED,
            summary="SAM.gov review candidates created.",
            payload={
                "candidate_count": len(review_candidates),
                "candidate_types": [
                    candidate.candidate_type.value for candidate in review_candidates
                ],
            },
        )
    return tuple(events)


def _hermes_events_from_entity_lane(
    *,
    profile_id: str,
    normalized_pivot: str,
    entity_lane: SamGovEntityLane,
    review_candidates: tuple[SamGovReviewCandidate, ...],
    occurred_at: str,
) -> tuple[SamGovHermesEvent, ...]:
    events: list[SamGovHermesEvent] = []

    def append_event(
        event_type: SamGovHermesEventType,
        *,
        summary: str,
        payload: dict[str, object],
    ) -> None:
        events.append(
            SamGovHermesEvent(
                id=(
                    f"sam_gov_event_{_safe_identifier(profile_id)}_"
                    f"{len(events) + 1:03d}_{event_type.value}"
                ),
                event_type=event_type,
                profile_id=profile_id,
                normalized_pivot=normalized_pivot,
                occurred_at=occurred_at,
                summary=summary,
                payload=payload,
            )
        )

    append_event(
        SamGovHermesEventType.PROFILE_STARTED,
        summary="SAM.gov Enrichment Profile started.",
        payload={
            "profile_id": profile_id,
            "normalized_pivot": normalized_pivot,
            "source_mode": entity_lane.provenance.source_mode.value,
        },
    )
    if entity_lane.matches:
        append_event(
            SamGovHermesEventType.ENTITY_RECORD_RESOLVED,
            summary="SAM.gov Entity Record lane resolved entity matches.",
            payload={
                "match_count": len(entity_lane.matches),
                "lookup_status": entity_lane.lookup_status.value,
            },
        )
    if entity_lane.source_limitations:
        append_event(
            SamGovHermesEventType.SOURCE_LIMITATION_DETECTED,
            summary="SAM.gov Entity Record lane source limitations detected.",
            payload={"source_limitations": list(entity_lane.source_limitations)},
        )
    if review_candidates:
        append_event(
            SamGovHermesEventType.REVIEW_CANDIDATES_CREATED,
            summary="SAM.gov review candidates created.",
            payload={
                "candidate_count": len(review_candidates),
                "candidate_types": [
                    candidate.candidate_type.value for candidate in review_candidates
                ],
            },
        )
    return tuple(events)


def _match_source_fields(match: SamGovEntityMatch) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("entity_lane.matches.uei", match.uei),
        ("entity_lane.matches.legal_business_name", match.legal_business_name),
        ("entity_lane.matches.cage_code", match.cage_code),
        ("entity_lane.matches.registration_status", match.registration_status),
        ("entity_lane.matches.parent_uei", match.parent_uei),
        (
            "entity_lane.matches.parent_legal_business_name",
            match.parent_legal_business_name,
        ),
        ("entity_lane.matches.business_types", "; ".join(match.business_types)),
        ("entity_lane.matches.naics_codes", "; ".join(match.naics_codes)),
        ("entity_lane.matches.psc_codes", "; ".join(match.psc_codes)),
        (
            "entity_lane.matches.responsibility_notes",
            "; ".join(match.responsibility_notes),
        ),
    )


def _opportunity_source_fields(
    record: SamGovOpportunityRecord,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("opportunity_discovery_lane.records.notice_id", record.notice_id),
        (
            "opportunity_discovery_lane.records.solicitation_number",
            record.solicitation_number,
        ),
        ("opportunity_discovery_lane.records.title", record.title),
        ("opportunity_discovery_lane.records.notice_type", record.notice_type),
        (
            "opportunity_discovery_lane.records.organization_path",
            record.organization_path,
        ),
        ("opportunity_discovery_lane.records.posted_date", record.posted_date),
        (
            "opportunity_discovery_lane.records.response_deadline",
            record.response_deadline,
        ),
        ("opportunity_discovery_lane.records.naics_code", record.naics_code),
        ("opportunity_discovery_lane.records.psc_code", record.psc_code),
        ("opportunity_discovery_lane.records.set_aside", record.set_aside),
    )


def _opportunity_packet_fields(record: SamGovOpportunityRecord) -> tuple[str, ...]:
    return tuple(field for field, value in _opportunity_packet_field_values(record))


def _opportunity_packet_values(record: SamGovOpportunityRecord) -> tuple[str, ...]:
    return tuple(value for field, value in _opportunity_packet_field_values(record))


def _opportunity_packet_field_values(
    record: SamGovOpportunityRecord,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("opportunity_discovery_lane.records.title", record.title),
        (
            "opportunity_discovery_lane.records.solicitation_number",
            record.solicitation_number,
        ),
        ("opportunity_discovery_lane.records.notice_id", record.notice_id),
        ("opportunity_discovery_lane.records.notice_type", record.notice_type),
    )


def _opportunity_timing_fields(record: SamGovOpportunityRecord) -> tuple[str, ...]:
    return tuple(field for field, value in _opportunity_timing_field_values(record))


def _opportunity_timing_values(record: SamGovOpportunityRecord) -> tuple[str, ...]:
    return tuple(value for field, value in _opportunity_timing_field_values(record))


def _opportunity_timing_field_values(
    record: SamGovOpportunityRecord,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("opportunity_discovery_lane.records.notice_type", record.notice_type),
        (
            "opportunity_discovery_lane.records.response_deadline",
            record.response_deadline,
        ),
        ("opportunity_discovery_lane.records.posted_date", record.posted_date),
    )


def _known_opportunity_source_fields(
    record: SamGovOpportunityRecord,
) -> tuple[tuple[str, str], ...]:
    return _opportunity_fields_for_prefix(record, "known_opportunity_lane.records")


def _known_opportunity_packet_fields(
    record: SamGovOpportunityRecord,
) -> tuple[str, ...]:
    return tuple(field for field, value in _known_opportunity_packet_values_raw(record))


def _known_opportunity_packet_values(
    record: SamGovOpportunityRecord,
) -> tuple[str, ...]:
    return tuple(value for field, value in _known_opportunity_packet_values_raw(record))


def _known_opportunity_packet_values_raw(
    record: SamGovOpportunityRecord,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("known_opportunity_lane.records.title", record.title),
        (
            "known_opportunity_lane.records.solicitation_number",
            record.solicitation_number,
        ),
        ("known_opportunity_lane.records.notice_id", record.notice_id),
        ("known_opportunity_lane.records.notice_type", record.notice_type),
        ("known_opportunity_lane.records.organization_path", record.organization_path),
    )


def _known_opportunity_timing_fields(
    record: SamGovOpportunityRecord,
) -> tuple[str, ...]:
    return tuple(field for field, value in _known_opportunity_timing_values_raw(record))


def _known_opportunity_timing_values(
    record: SamGovOpportunityRecord,
) -> tuple[str, ...]:
    return tuple(value for field, value in _known_opportunity_timing_values_raw(record))


def _known_opportunity_timing_values_raw(
    record: SamGovOpportunityRecord,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("known_opportunity_lane.records.notice_type", record.notice_type),
        (
            "known_opportunity_lane.records.response_deadline",
            record.response_deadline,
        ),
        ("known_opportunity_lane.records.posted_date", record.posted_date),
        (
            "known_opportunity_lane.records.point_of_contact",
            "; ".join(record.point_of_contact),
        ),
    )


def _opportunity_fields_for_prefix(
    record: SamGovOpportunityRecord,
    prefix: str,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        (f"{prefix}.notice_id", record.notice_id),
        (f"{prefix}.solicitation_number", record.solicitation_number),
        (f"{prefix}.title", record.title),
        (f"{prefix}.notice_type", record.notice_type),
        (f"{prefix}.organization_path", record.organization_path),
        (f"{prefix}.posted_date", record.posted_date),
        (f"{prefix}.response_deadline", record.response_deadline),
        (f"{prefix}.naics_code", record.naics_code),
        (f"{prefix}.psc_code", record.psc_code),
        (f"{prefix}.set_aside", record.set_aside),
        (f"{prefix}.point_of_contact", "; ".join(record.point_of_contact)),
        (f"{prefix}.archive_type", record.archive_type),
        (f"{prefix}.archive_date", record.archive_date),
    )


def _entity_ecosystem_fields(match: SamGovEntityMatch) -> tuple[str, ...]:
    return tuple(field for field, value in _entity_ecosystem_field_values(match))


def _entity_ecosystem_values(match: SamGovEntityMatch) -> tuple[str, ...]:
    return tuple(value for field, value in _entity_ecosystem_field_values(match))


def _entity_ecosystem_field_values(
    match: SamGovEntityMatch,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("entity_lane.matches.parent_uei", match.parent_uei),
        (
            "entity_lane.matches.parent_legal_business_name",
            match.parent_legal_business_name,
        ),
        ("entity_lane.matches.business_types", "; ".join(match.business_types)),
        (
            "entity_lane.matches.responsibility_notes",
            "; ".join(match.responsibility_notes),
        ),
    )


def _entity_source_content(field_values: tuple[tuple[str, str], ...]) -> str:
    return "SAM.gov entity record: " + "; ".join(
        f"{field.removeprefix('entity_lane.matches.')}: {value}"
        for field, value in field_values
    )


def _opportunity_source_content(field_values: tuple[tuple[str, str], ...]) -> str:
    return "SAM.gov opportunity notice: " + "; ".join(
        f"{field.removeprefix('opportunity_discovery_lane.records.').removeprefix('known_opportunity_lane.records.')}: {value}"
        for field, value in field_values
    )


def _opportunity_packet_content(record: SamGovOpportunityRecord) -> str:
    pieces = _populated_texts(
        record.title, record.solicitation_number, record.notice_id
    )
    return "SAM.gov opportunity signal: " + "; ".join(pieces)


def _needs_web_enrichment_support(lane: SamGovOpportunityDiscoveryLane) -> bool:
    return (
        lane.discovery_status is SamGovOpportunityDiscoveryStatus.NOT_FOUND
        or any(record.match_confidence < 0.65 for record in lane.records)
        or any(record.ambiguity_notes for record in lane.records)
    )


def _populated_fields(
    *field_values: tuple[str, object | None],
) -> tuple[tuple[str, str], ...]:
    populated_fields = []
    for field, value in field_values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            populated_fields.append((field, text))
    return tuple(populated_fields)


def _profile_id_for_pivot(normalized_pivot: str) -> str:
    return f"sam_gov_profile_{_safe_identifier(normalized_pivot).upper()}"


def _safe_identifier(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_" for character in value
    ).strip("_")
