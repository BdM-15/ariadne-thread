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
        _entity_match_from_row(row) for row in _entity_rows_from_payload(tool_result.payload)
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


def _entity_rows_from_payload(payload: dict[str, Any] | None) -> tuple[dict[str, Any], ...]:
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