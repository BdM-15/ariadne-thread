from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from ariadne.usaspending import (
    USAspendingAwardHistoryResult,
    USAspendingAwardLookupResult,
)


class PiidScenarioClassification(StrEnum):
    STANDALONE_CONTRACT = "standalone_contract"
    PARENT_IDIQ = "parent_idiq"
    IDIQ_ORDER = "idiq_order"
    UNKNOWN = "unknown"


class PiidPivotType(StrEnum):
    UEI = "uei"
    PARENT_UEI = "parent_uei"
    SOLICITATION_ID = "solicitation_id"
    NAICS_CODE = "naics_code"
    PSC_CODE = "psc_code"
    AWARDING_AGENCY = "awarding_agency"
    AWARDING_SUB_AGENCY = "awarding_sub_agency"
    PARENT_IDV = "parent_idv"
    GENERATED_INTERNAL_ID = "generated_internal_id"
    SUBAWARD_HOOK = "subaward_hook"
    PERMALINK = "permalink"


class PiidGapCategory(StrEnum):
    SOURCE_LIMITATION = "source_limitation"


class PiidEnrichmentRouteType(StrEnum):
    SAM_GOV_ENTITY = "sam_gov_entity"
    SAM_GOV_OPPORTUNITY = "sam_gov_opportunity"
    BLS_GSA_PRICING_CONTEXT = "bls_gsa_pricing_context"
    FIRECRAWL_WEB_ENRICHMENT = "firecrawl_web_enrichment"
    SUBAWARD_PROFILE = "subaward_profile"
    COMPETITOR_PROFILE = "competitor_profile"
    CUSTOMER_PROFILE = "customer_profile"
    ARTIFACT_PREPARATION = "artifact_preparation"


class PiidReviewCandidateType(StrEnum):
    SOURCE_EVIDENCE = "source_evidence"
    DERIVED_EVIDENCE = "derived_evidence"
    PACKET_FIELD_ANSWER = "packet_field_answer"
    ACTION_PLAN_ITEM = "action_plan_item"
    RISK_REGISTER_SIGNAL = "risk_register_signal"
    CALL_PLAN_SIGNAL = "call_plan_signal"
    FOLLOW_UP_ROUTE = "follow_up_route"


class PiidReviewState(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"
    ROUTED = "routed"


class PiidHermesEventType(StrEnum):
    PROFILE_STARTED = "profile_started"
    AWARD_RESOLVED = "award_resolved"
    SCENARIO_CLASSIFIED = "scenario_classified"
    BURN_POSTURE_COMPUTED = "burn_posture_computed"
    PIVOTS_IDENTIFIED = "pivots_identified"
    GAP_DETECTED = "gap_detected"
    NEXT_ENRICHMENT_RECOMMENDED = "next_enrichment_recommended"
    REVIEW_DECISION_RECORDED = "review_decision_recorded"


class PiidProfileProvenance(BaseModel):
    source_capability_id: str
    source_tool_name: str
    source_package: str
    source_package_version: str
    checked_at: str
    lookup_status: str


class PiidAwardBaseline(BaseModel):
    award_type: str | None = None
    resolved_award_id: str | None = None
    generated_internal_id: str | None = None
    recipient_name: str | None = None
    recipient_uei: str | None = None
    parent_recipient_uei: str | None = None
    awarding_agency_name: str | None = None
    awarding_sub_agency_name: str | None = None
    awarding_office_name: str | None = None
    funding_agency_name: str | None = None
    funding_sub_agency_name: str | None = None
    funding_office_name: str | None = None
    naics_code: str | None = None
    psc_code: str | None = None
    solicitation_id: str | None = None
    award_amount: float | None = None
    start_date: str | None = None
    end_date: str | None = None
    parent_idv: str | None = None
    permalink: str | None = None


class PiidDeterministicPivot(BaseModel):
    pivot_type: PiidPivotType
    value: str
    source_field: str


class PiidProfileGap(BaseModel):
    field_key: str
    category: PiidGapCategory = PiidGapCategory.SOURCE_LIMITATION
    source_limitation: str
    recommended_enrichment_route: str


class PiidEnrichmentRoute(BaseModel):
    id: str
    route_type: PiidEnrichmentRouteType
    title: str
    target_capability: str
    recommendation: str
    rationale: str
    source_fields: tuple[str, ...]
    source_values: tuple[str, ...]
    review_required: bool = True
    deferred_product_workflow: bool = True


class PiidReviewCandidate(BaseModel):
    id: str
    candidate_type: PiidReviewCandidateType
    title: str
    content: str
    target_workflow: str
    recommendation: str
    rationale: str
    source_profile_id: str
    normalized_piid: str
    source_fields: tuple[str, ...]
    source_values: tuple[str, ...]
    field_key: str | None = None
    route_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    review_state: PiidReviewState = PiidReviewState.PENDING_REVIEW
    trusted_output_written: bool = False
    created_at: str

    @model_validator(mode="after")
    def validate_review_gate(self) -> PiidReviewCandidate:
        if not self.source_fields:
            raise ValueError("PIID review candidate requires source_fields")
        if self.trusted_output_written and self.review_state is not (
            PiidReviewState.ACCEPTED
        ):
            raise ValueError("trusted output requires accepted review state")
        return self


class PiidHermesEvent(BaseModel):
    id: str
    event_type: PiidHermesEventType
    profile_id: str
    normalized_piid: str
    occurred_at: str
    summary: str
    payload: dict[str, object] = Field(default_factory=dict)
    source_capability_id: str = "usaspending"
    observable_only: bool = True


class PiidAwardTransaction(BaseModel):
    transaction_id: str | None = None
    action_date: str | None = None
    fiscal_year: int | None = None
    modification_number: str | None = None
    action_type: str | None = None
    obligation: float | None = None
    description: str | None = None


class PiidBurnPosture(BaseModel):
    net_obligations: float | None = None
    fiscal_year_obligations: dict[int, float] = Field(default_factory=dict)
    period_start: str | None = None
    period_end: str | None = None
    period_days: int | None = None
    monthly_burn_rate: float | None = None
    daily_burn_rate: float | None = None
    transaction_count: int = 0
    modification_count: int = 0
    option_signals: tuple[str, ...] = ()
    deobligation_warnings: tuple[str, ...] = ()
    derivation_notes: tuple[str, ...] = ()
    completeness: str = "unavailable"


class PiidVehicleRelatedAward(BaseModel):
    piid: str | None = None
    generated_internal_id: str | None = None
    recipient_name: str | None = None
    obligated_amount: float | None = None
    period_start: str | None = None
    period_end: str | None = None


class PiidVehicleContext(BaseModel):
    parent_idv: str | None = None
    parent_generated_internal_id: str | None = None
    child_orders: tuple[PiidVehicleRelatedAward, ...] = ()
    sibling_or_related_orders: tuple[PiidVehicleRelatedAward, ...] = ()
    linkage_confidence: str = "none"
    derivation_notes: tuple[str, ...] = ()


class PiidContractIntelligenceProfile(BaseModel):
    id: str
    input_contract_number: str
    normalized_piid: str
    scenario: PiidScenarioClassification
    provenance: PiidProfileProvenance
    award_baseline: PiidAwardBaseline
    transaction_history: tuple[PiidAwardTransaction, ...] = ()
    modification_history: tuple[PiidAwardTransaction, ...] = ()
    burn_posture: PiidBurnPosture = Field(default_factory=PiidBurnPosture)
    vehicle_context: PiidVehicleContext = Field(default_factory=PiidVehicleContext)
    deterministic_pivots: tuple[PiidDeterministicPivot, ...] = ()
    gaps: tuple[PiidProfileGap, ...] = ()
    recommended_enrichment_routes: tuple[PiidEnrichmentRoute, ...] = ()
    review_candidates: tuple[PiidReviewCandidate, ...] = ()
    hermes_events: tuple[PiidHermesEvent, ...] = ()
    created_at: str
    updated_at: str


class PiidProfileStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(
        self,
        profile: PiidContractIntelligenceProfile,
    ) -> PiidContractIntelligenceProfile:
        self._profile_root.mkdir(parents=True, exist_ok=True)
        self._path(profile.id).write_text(
            profile.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return profile

    def read(self, profile_id: str) -> PiidContractIntelligenceProfile:
        return PiidContractIntelligenceProfile.model_validate_json(
            self._path(profile_id).read_text(encoding="utf-8")
        )

    def list(self) -> list[PiidContractIntelligenceProfile]:
        if not self._profile_root.exists():
            return []
        return [
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self._profile_root.glob("*.json"))
        ]

    def find_by_normalized_piid(
        self,
        normalized_piid: str,
    ) -> list[PiidContractIntelligenceProfile]:
        return [
            profile
            for profile in self.list()
            if profile.normalized_piid == normalized_piid.strip().upper()
        ]

    @property
    def _profile_root(self) -> Path:
        return self.root / "profiles"

    def _path(self, profile_id: str) -> Path:
        if not profile_id or profile_id != Path(profile_id).name:
            raise ValueError("profile_id must be a file-safe identifier")
        return self._profile_root / f"{profile_id}.json"


def create_piid_contract_intelligence_profile(
    lookup: USAspendingAwardLookupResult,
    *,
    award_history: USAspendingAwardHistoryResult | None = None,
    profile_id: str | None = None,
    created_at: str | None = None,
) -> PiidContractIntelligenceProfile:
    timestamp = created_at or datetime.now(UTC).isoformat()
    resolved_profile_id = profile_id or _profile_id_for_piid(lookup.normalized_piid)
    baseline = PiidAwardBaseline(
        award_type=lookup.award_type,
        resolved_award_id=lookup.resolved_award_id,
        generated_internal_id=lookup.generated_internal_id,
        recipient_name=lookup.recipient_name,
        recipient_uei=lookup.recipient_uei,
        parent_recipient_uei=lookup.parent_recipient_uei,
        awarding_agency_name=lookup.awarding_agency_name,
        awarding_sub_agency_name=lookup.awarding_sub_agency_name,
        awarding_office_name=lookup.awarding_office_name,
        funding_agency_name=lookup.funding_agency_name,
        funding_sub_agency_name=lookup.funding_sub_agency_name,
        funding_office_name=lookup.funding_office_name,
        award_amount=lookup.award_amount,
        start_date=lookup.start_date,
        end_date=lookup.end_date,
        naics_code=lookup.naics_code,
        psc_code=lookup.psc_code,
        solicitation_id=lookup.solicitation_id,
        parent_idv=lookup.parent_idv,
        permalink=lookup.permalink,
    )
    vehicle_context = _vehicle_context_from_history(baseline, award_history)
    transaction_history = _transactions_from_history(award_history)
    modification_history = _modifications_from_history(award_history)
    burn_posture = _burn_posture_from_history(baseline, award_history)
    scenario = classify_piid_scenario(baseline, vehicle_context)
    deterministic_pivots = _deterministic_pivots_from_baseline(baseline)
    gaps = _gaps_from_baseline(baseline)
    recommended_enrichment_routes = _recommended_enrichment_routes_from_baseline(
        baseline,
        resolved_profile_id,
    )
    review_candidates = _review_candidates_from_profile_parts(
        profile_id=resolved_profile_id,
        normalized_piid=lookup.normalized_piid,
        scenario=scenario,
        baseline=baseline,
        burn_posture=burn_posture,
        gaps=gaps,
        recommended_enrichment_routes=recommended_enrichment_routes,
        created_at=timestamp,
    )
    hermes_events = _hermes_events_from_profile_parts(
        profile_id=resolved_profile_id,
        normalized_piid=lookup.normalized_piid,
        source_capability_id=lookup.provenance.source_capability_id,
        scenario=scenario,
        baseline=baseline,
        burn_posture=burn_posture,
        deterministic_pivots=deterministic_pivots,
        gaps=gaps,
        recommended_enrichment_routes=recommended_enrichment_routes,
        occurred_at=timestamp,
    )
    return PiidContractIntelligenceProfile(
        id=resolved_profile_id,
        input_contract_number=lookup.input_contract_number,
        normalized_piid=lookup.normalized_piid,
        scenario=scenario,
        provenance=PiidProfileProvenance(
            source_capability_id=lookup.provenance.source_capability_id,
            source_tool_name=lookup.provenance.source_tool_name,
            source_package=lookup.provenance.source_package,
            source_package_version=lookup.provenance.source_package_version,
            checked_at=lookup.provenance.checked_at,
            lookup_status=lookup.status.value,
        ),
        award_baseline=baseline,
        transaction_history=transaction_history,
        modification_history=modification_history,
        burn_posture=burn_posture,
        vehicle_context=vehicle_context,
        deterministic_pivots=deterministic_pivots,
        gaps=gaps,
        recommended_enrichment_routes=recommended_enrichment_routes,
        review_candidates=review_candidates,
        hermes_events=hermes_events,
        created_at=timestamp,
        updated_at=timestamp,
    )


def record_piid_review_decision(
    profile: PiidContractIntelligenceProfile,
    *,
    candidate_id: str,
    review_state: PiidReviewState,
    reviewer_rationale: str,
    decided_at: str | None = None,
) -> PiidContractIntelligenceProfile:
    if review_state is PiidReviewState.PENDING_REVIEW:
        raise ValueError("review decision must accept, discard, or route a candidate")
    if not reviewer_rationale.strip():
        raise ValueError("review decision requires reviewer_rationale")
    timestamp = decided_at or datetime.now(UTC).isoformat()
    updated_candidates = []
    matched_candidate: PiidReviewCandidate | None = None
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
        raise ValueError("PIID review candidate not found")
    review_event = _hermes_event(
        event_type=PiidHermesEventType.REVIEW_DECISION_RECORDED,
        profile_id=profile.id,
        normalized_piid=profile.normalized_piid,
        source_capability_id=profile.provenance.source_capability_id,
        occurred_at=timestamp,
        sequence=len(profile.hermes_events) + 1,
        summary=f"Review decision recorded for {matched_candidate.candidate_type.value}.",
        payload={
            "candidate_id": candidate_id,
            "candidate_type": matched_candidate.candidate_type.value,
            "review_state": review_state.value,
            "reviewer_rationale": reviewer_rationale,
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


def _recommended_enrichment_routes_from_baseline(
    baseline: PiidAwardBaseline,
    profile_id: str,
) -> tuple[PiidEnrichmentRoute, ...]:
    routes: list[PiidEnrichmentRoute] = []
    if baseline.recipient_uei:
        routes.append(
            _enrichment_route(
                PiidEnrichmentRouteType.SAM_GOV_ENTITY,
                title="SAM.gov entity enrichment",
                target_capability="sam_gov_entity",
                recommendation="Review the recipient UEI before routing to SAM.gov entity enrichment.",
                rationale="Recipient UEI is populated by USAspending and can seed entity research.",
                source_fields=("recipient_uei",),
                source_values=(baseline.recipient_uei,),
            )
        )
    if baseline.solicitation_id:
        routes.append(
            _enrichment_route(
                PiidEnrichmentRouteType.SAM_GOV_OPPORTUNITY,
                title="SAM.gov opportunity enrichment",
                target_capability="sam_gov_opportunity",
                recommendation="Review the solicitation ID before routing to SAM.gov opportunity or document intake work.",
                rationale="Solicitation ID is populated and can seed opportunity history research.",
                source_fields=("solicitation_id",),
                source_values=(baseline.solicitation_id,),
            )
        )
    pricing_fields = tuple(
        field
        for field, value in (
            ("naics_code", baseline.naics_code),
            ("psc_code", baseline.psc_code),
        )
        if value
    )
    pricing_values = tuple(
        value
        for value in (baseline.naics_code, baseline.psc_code)
        if value
    )
    if pricing_fields:
        routes.append(
            _enrichment_route(
                PiidEnrichmentRouteType.BLS_GSA_PRICING_CONTEXT,
                title="BLS/GSA pricing context",
                target_capability="pricing_context",
                recommendation="Review NAICS or PSC values before routing to wage, labor, or rate context.",
                rationale="Populated NAICS or PSC values can seed future BLS and GSA pricing workflows.",
                source_fields=pricing_fields,
                source_values=pricing_values,
            )
        )
    web_fields = _populated_fields(
        ("recipient_name", baseline.recipient_name),
        ("awarding_agency_name", baseline.awarding_agency_name),
        ("awarding_sub_agency_name", baseline.awarding_sub_agency_name),
    )
    if web_fields:
        routes.append(
            _enrichment_route(
                PiidEnrichmentRouteType.FIRECRAWL_WEB_ENRICHMENT,
                title="Web enrichment",
                target_capability="firecrawl_web_enrichment",
                recommendation="Review populated organization names before routing to web enrichment.",
                rationale="USAspending populated organization names that can seed future web research.",
                source_fields=tuple(field for field, value in web_fields),
                source_values=tuple(value for field, value in web_fields),
            )
        )
    if baseline.generated_internal_id or baseline.permalink:
        subaward_fields = _populated_fields(
            ("generated_internal_id", baseline.generated_internal_id),
            ("permalink", baseline.permalink),
        )
        routes.append(
            _enrichment_route(
                PiidEnrichmentRouteType.SUBAWARD_PROFILE,
                title="Subaward profile",
                target_capability="subaward_profile",
                recommendation="Review the award identifier before routing to subaward profile enrichment.",
                rationale="USAspending award identifiers can seed future subaward checks.",
                source_fields=tuple(field for field, value in subaward_fields),
                source_values=tuple(value for field, value in subaward_fields),
            )
        )
    if baseline.recipient_name:
        routes.append(
            _enrichment_route(
                PiidEnrichmentRouteType.COMPETITOR_PROFILE,
                title="Competitor profile",
                target_capability="competitor_profile",
                recommendation="Review the recipient name as an incumbent or competitor profile seed.",
                rationale="Recipient name is populated and can seed future incumbent or competitor research.",
                source_fields=("recipient_name",),
                source_values=(baseline.recipient_name,),
            )
        )
    customer_fields = _populated_fields(
        ("awarding_agency_name", baseline.awarding_agency_name),
        ("awarding_sub_agency_name", baseline.awarding_sub_agency_name),
        ("funding_agency_name", baseline.funding_agency_name),
        ("funding_sub_agency_name", baseline.funding_sub_agency_name),
    )
    if customer_fields:
        routes.append(
            _enrichment_route(
                PiidEnrichmentRouteType.CUSTOMER_PROFILE,
                title="Customer profile",
                target_capability="customer_profile",
                recommendation="Review the agency and office values before routing to customer profile enrichment.",
                rationale="Populated agency values can seed future customer research.",
                source_fields=tuple(field for field, value in customer_fields),
                source_values=tuple(value for field, value in customer_fields),
            )
        )
    routes.append(
        _enrichment_route(
            PiidEnrichmentRouteType.ARTIFACT_PREPARATION,
            title="Artifact preparation",
            target_capability="artifact_preparation",
            recommendation="Review the structured profile before preparing downstream artifacts.",
            rationale="The PIID profile is structured enough to seed future renderer-ready artifact work.",
            source_fields=("profile_id",),
            source_values=(profile_id,),
        )
    )
    return tuple(routes)


def _enrichment_route(
    route_type: PiidEnrichmentRouteType,
    *,
    title: str,
    target_capability: str,
    recommendation: str,
    rationale: str,
    source_fields: tuple[str, ...],
    source_values: tuple[str, ...],
) -> PiidEnrichmentRoute:
    return PiidEnrichmentRoute(
        id=f"piid_route_{route_type.value}",
        route_type=route_type,
        title=title,
        target_capability=target_capability,
        recommendation=recommendation,
        rationale=rationale,
        source_fields=source_fields,
        source_values=source_values,
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


def _review_candidates_from_profile_parts(
    *,
    profile_id: str,
    normalized_piid: str,
    scenario: PiidScenarioClassification,
    baseline: PiidAwardBaseline,
    burn_posture: PiidBurnPosture,
    gaps: tuple[PiidProfileGap, ...],
    recommended_enrichment_routes: tuple[PiidEnrichmentRoute, ...],
    created_at: str,
) -> tuple[PiidReviewCandidate, ...]:
    candidates: list[PiidReviewCandidate] = []
    baseline_fields = _baseline_candidate_fields(baseline)
    if baseline_fields:
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                candidate_type=PiidReviewCandidateType.SOURCE_EVIDENCE,
                candidate_key="source_evidence_award_baseline",
                title="Source Evidence: USAspending award baseline",
                content=_baseline_candidate_content(baseline_fields),
                target_workflow="evidence_store",
                recommendation="Review before accepting award baseline facts as Source Evidence.",
                rationale="USAspending supplied populated award baseline fields; blanks remain source limitations.",
                source_fields=tuple(field for field, value in baseline_fields),
                source_values=tuple(value for field, value in baseline_fields),
                confidence=0.82,
                created_at=created_at,
            )
        )

    burn_fields = _burn_posture_candidate_fields(burn_posture)
    if burn_fields:
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                candidate_type=PiidReviewCandidateType.DERIVED_EVIDENCE,
                candidate_key="derived_evidence_burn_posture",
                title="Derived Evidence: burn posture",
                content=_burn_posture_candidate_content(burn_posture),
                target_workflow="evidence_store",
                recommendation="Review before accepting burn posture as Derived Evidence.",
                rationale="Burn posture is computed from populated transaction or baseline values.",
                source_fields=tuple(field for field, value in burn_fields),
                source_values=tuple(value for field, value in burn_fields),
                confidence=_burn_posture_confidence(burn_posture),
                created_at=created_at,
            )
        )

    candidates.extend(
        _packet_field_candidates(
            profile_id=profile_id,
            normalized_piid=normalized_piid,
            scenario=scenario,
            baseline=baseline,
            burn_posture=burn_posture,
            gaps=gaps,
            created_at=created_at,
        )
    )

    if recommended_enrichment_routes or gaps:
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                candidate_type=PiidReviewCandidateType.ACTION_PLAN_ITEM,
                candidate_key="action_plan_next_enrichment",
                title="Action Plan: route PIID enrichment",
                content="Review PIID profile gaps and route the next enrichment step.",
                target_workflow="capture_action_plan",
                recommendation="Create an action only after review confirms the next capture outcome.",
                rationale="The profile has reviewable gaps or enrichment routes, but no task is trusted yet.",
                source_fields=("profile_id",),
                source_values=(profile_id,),
                confidence=0.68,
                created_at=created_at,
            )
        )

    risk_fields = _risk_candidate_fields(burn_posture, gaps)
    if risk_fields:
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                candidate_type=PiidReviewCandidateType.RISK_REGISTER_SIGNAL,
                candidate_key="risk_register_burn_and_gap_signal",
                title="Risk Register signal: burn posture and gaps",
                content=_risk_candidate_content(burn_posture, gaps),
                target_workflow="risk_register",
                recommendation="Review before treating this as a pursuit risk.",
                rationale="Burn warnings and source limitations can affect recompete posture.",
                source_fields=tuple(field for field, value in risk_fields),
                source_values=tuple(value for field, value in risk_fields),
                confidence=0.62,
                created_at=created_at,
            )
        )

    customer_fields = _customer_candidate_fields(baseline)
    if customer_fields:
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                candidate_type=PiidReviewCandidateType.CALL_PLAN_SIGNAL,
                candidate_key="call_plan_customer_validation",
                title="Call Plan signal: validate recompete posture",
                content="Prepare customer engagement around agency, incumbent, value, and timing signals.",
                target_workflow="call_plan",
                recommendation="Review before preparing customer engagement from this profile.",
                rationale="Populated agency fields can guide future call plan preparation.",
                source_fields=tuple(field for field, value in customer_fields),
                source_values=tuple(value for field, value in customer_fields),
                confidence=0.66,
                created_at=created_at,
            )
        )

    for route in recommended_enrichment_routes:
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                candidate_type=PiidReviewCandidateType.FOLLOW_UP_ROUTE,
                candidate_key=f"follow_up_{route.route_type.value}",
                title=f"Follow-up route: {route.title}",
                content=route.recommendation,
                target_workflow="follow_up_routes",
                recommendation="Review before routing this enrichment through another capability.",
                rationale=route.rationale,
                source_fields=route.source_fields,
                source_values=route.source_values,
                route_id=route.id,
                confidence=0.7,
                created_at=created_at,
            )
        )
    return tuple(candidates)


def _review_candidate(
    *,
    profile_id: str,
    normalized_piid: str,
    candidate_type: PiidReviewCandidateType,
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
    route_id: str | None = None,
    confidence: float | None = None,
) -> PiidReviewCandidate:
    return PiidReviewCandidate(
        id=f"piid_candidate_{_safe_identifier(profile_id)}_{_safe_identifier(candidate_key)}",
        candidate_type=candidate_type,
        title=title,
        content=content,
        target_workflow=target_workflow,
        recommendation=recommendation,
        rationale=rationale,
        source_profile_id=profile_id,
        normalized_piid=normalized_piid,
        source_fields=source_fields,
        source_values=source_values,
        field_key=field_key,
        route_id=route_id,
        confidence=confidence,
        created_at=created_at,
    )


def _packet_field_candidates(
    *,
    profile_id: str,
    normalized_piid: str,
    scenario: PiidScenarioClassification,
    baseline: PiidAwardBaseline,
    burn_posture: PiidBurnPosture,
    gaps: tuple[PiidProfileGap, ...],
    created_at: str,
) -> tuple[PiidReviewCandidate, ...]:
    candidates = []
    packet_specs = (
        (
            "incumbent",
            _populated_fields(("award_baseline.recipient_name", baseline.recipient_name)),
            f"Incumbent or awardee signal: {baseline.recipient_name}",
        ),
        (
            "customer",
            _customer_candidate_fields(baseline),
            "Customer signal from awarding or funding agency fields.",
        ),
        (
            "value",
            _value_candidate_fields(baseline, burn_posture),
            "Value signal from award amount or computed net obligations.",
        ),
        (
            "timing",
            _populated_fields(
                ("award_baseline.start_date", baseline.start_date),
                ("award_baseline.end_date", baseline.end_date),
            ),
            "Timing signal from period of performance dates.",
        ),
        (
            "competition",
            _competition_candidate_fields(scenario, baseline),
            f"Competition signal from {scenario.value} profile context.",
        ),
        (
            "risk",
            _risk_candidate_fields(burn_posture, gaps),
            "Risk signal from burn posture warnings or profile gaps.",
        ),
    )
    for field_key, field_values, content in packet_specs:
        if not field_values:
            continue
        candidates.append(
            _review_candidate(
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                candidate_type=PiidReviewCandidateType.PACKET_FIELD_ANSWER,
                candidate_key=f"packet_field_{field_key}",
                title=f"Packet Field Answer: {field_key}",
                content=content,
                target_workflow="living_briefing_packet",
                recommendation="Review before accepting as a packet field answer.",
                rationale="The PIID profile supports this packet field, but the answer is not trusted yet.",
                source_fields=tuple(field for field, value in field_values),
                source_values=tuple(value for field, value in field_values),
                field_key=field_key,
                confidence=0.7,
                created_at=created_at,
            )
        )
    return tuple(candidates)


def _baseline_candidate_fields(
    baseline: PiidAwardBaseline,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("award_baseline.resolved_award_id", baseline.resolved_award_id),
        ("award_baseline.generated_internal_id", baseline.generated_internal_id),
        ("award_baseline.recipient_name", baseline.recipient_name),
        ("award_baseline.recipient_uei", baseline.recipient_uei),
        ("award_baseline.awarding_agency_name", baseline.awarding_agency_name),
        ("award_baseline.awarding_sub_agency_name", baseline.awarding_sub_agency_name),
        ("award_baseline.award_amount", baseline.award_amount),
        ("award_baseline.start_date", baseline.start_date),
        ("award_baseline.end_date", baseline.end_date),
        ("award_baseline.naics_code", baseline.naics_code),
        ("award_baseline.psc_code", baseline.psc_code),
        ("award_baseline.solicitation_id", baseline.solicitation_id),
        ("award_baseline.parent_idv", baseline.parent_idv),
        ("award_baseline.permalink", baseline.permalink),
    )


def _burn_posture_candidate_fields(
    burn_posture: PiidBurnPosture,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("burn_posture.net_obligations", burn_posture.net_obligations),
        ("burn_posture.monthly_burn_rate", burn_posture.monthly_burn_rate),
        ("burn_posture.daily_burn_rate", burn_posture.daily_burn_rate),
        ("burn_posture.transaction_count", burn_posture.transaction_count),
        ("burn_posture.modification_count", burn_posture.modification_count),
        ("burn_posture.completeness", burn_posture.completeness),
    )


def _customer_candidate_fields(
    baseline: PiidAwardBaseline,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("award_baseline.awarding_agency_name", baseline.awarding_agency_name),
        ("award_baseline.awarding_sub_agency_name", baseline.awarding_sub_agency_name),
        ("award_baseline.awarding_office_name", baseline.awarding_office_name),
        ("award_baseline.funding_agency_name", baseline.funding_agency_name),
        ("award_baseline.funding_sub_agency_name", baseline.funding_sub_agency_name),
        ("award_baseline.funding_office_name", baseline.funding_office_name),
    )


def _value_candidate_fields(
    baseline: PiidAwardBaseline,
    burn_posture: PiidBurnPosture,
) -> tuple[tuple[str, str], ...]:
    return _populated_fields(
        ("award_baseline.award_amount", baseline.award_amount),
        ("burn_posture.net_obligations", burn_posture.net_obligations),
    )


def _competition_candidate_fields(
    scenario: PiidScenarioClassification,
    baseline: PiidAwardBaseline,
) -> tuple[tuple[str, str], ...]:
    if scenario is PiidScenarioClassification.UNKNOWN and not baseline.recipient_name:
        return ()
    return _populated_fields(
        ("profile.scenario", scenario.value),
        ("award_baseline.recipient_name", baseline.recipient_name),
        ("award_baseline.parent_idv", baseline.parent_idv),
    )


def _risk_candidate_fields(
    burn_posture: PiidBurnPosture,
    gaps: tuple[PiidProfileGap, ...],
) -> tuple[tuple[str, str], ...]:
    fields = list(
        _populated_fields(
            (
                "burn_posture.deobligation_warnings",
                "; ".join(burn_posture.deobligation_warnings),
            ),
            ("burn_posture.completeness", burn_posture.completeness),
        )
    )
    fields.extend((f"gaps.{gap.field_key}", gap.source_limitation) for gap in gaps)
    return tuple(fields)


def _baseline_candidate_content(field_values: tuple[tuple[str, str], ...]) -> str:
    return "USAspending award baseline: " + "; ".join(
        f"{field.removeprefix('award_baseline.')}: {value}"
        for field, value in field_values
    )


def _burn_posture_candidate_content(burn_posture: PiidBurnPosture) -> str:
    pieces = [f"net obligations {burn_posture.net_obligations}"]
    if burn_posture.monthly_burn_rate is not None:
        pieces.append(f"monthly burn rate {burn_posture.monthly_burn_rate}")
    if burn_posture.deobligation_warnings:
        pieces.append(
            "deobligation warnings " + "; ".join(burn_posture.deobligation_warnings)
        )
    pieces.append(f"completeness {burn_posture.completeness}")
    return "Burn posture: " + "; ".join(pieces)


def _risk_candidate_content(
    burn_posture: PiidBurnPosture,
    gaps: tuple[PiidProfileGap, ...],
) -> str:
    pieces = []
    if burn_posture.deobligation_warnings:
        pieces.append("; ".join(burn_posture.deobligation_warnings))
    if gaps:
        pieces.append("source limitations: " + ", ".join(gap.field_key for gap in gaps))
    return "Risk signals: " + "; ".join(pieces)


def _burn_posture_confidence(burn_posture: PiidBurnPosture) -> float:
    if burn_posture.completeness == "complete":
        return 0.8
    if burn_posture.completeness == "partial":
        return 0.58
    return 0.3


def _hermes_events_from_profile_parts(
    *,
    profile_id: str,
    normalized_piid: str,
    source_capability_id: str,
    scenario: PiidScenarioClassification,
    baseline: PiidAwardBaseline,
    burn_posture: PiidBurnPosture,
    deterministic_pivots: tuple[PiidDeterministicPivot, ...],
    gaps: tuple[PiidProfileGap, ...],
    recommended_enrichment_routes: tuple[PiidEnrichmentRoute, ...],
    occurred_at: str,
) -> tuple[PiidHermesEvent, ...]:
    events: list[PiidHermesEvent] = []

    def append_event(
        event_type: PiidHermesEventType,
        *,
        summary: str,
        payload: dict[str, object],
    ) -> None:
        events.append(
            _hermes_event(
                event_type=event_type,
                profile_id=profile_id,
                normalized_piid=normalized_piid,
                source_capability_id=source_capability_id,
                occurred_at=occurred_at,
                sequence=len(events) + 1,
                summary=summary,
                payload=payload,
            )
        )

    append_event(
        PiidHermesEventType.PROFILE_STARTED,
        summary="PIID Contract Intelligence Profile started.",
        payload={"profile_id": profile_id, "normalized_piid": normalized_piid},
    )
    if baseline.resolved_award_id or baseline.generated_internal_id:
        append_event(
            PiidHermesEventType.AWARD_RESOLVED,
            summary="USAspending award resolved for PIID profile.",
            payload={
                "resolved_award_id": baseline.resolved_award_id,
                "generated_internal_id": baseline.generated_internal_id,
            },
        )
    append_event(
        PiidHermesEventType.SCENARIO_CLASSIFIED,
        summary=f"PIID scenario classified as {scenario.value}.",
        payload={"scenario": scenario.value},
    )
    append_event(
        PiidHermesEventType.BURN_POSTURE_COMPUTED,
        summary="Burn posture computed for PIID profile.",
        payload={
            "net_obligations": burn_posture.net_obligations,
            "transaction_count": burn_posture.transaction_count,
            "modification_count": burn_posture.modification_count,
            "completeness": burn_posture.completeness,
        },
    )
    if deterministic_pivots:
        append_event(
            PiidHermesEventType.PIVOTS_IDENTIFIED,
            summary="Deterministic enrichment pivots identified.",
            payload={
                "pivot_count": len(deterministic_pivots),
                "pivot_types": [pivot.pivot_type.value for pivot in deterministic_pivots],
            },
        )
    if gaps:
        append_event(
            PiidHermesEventType.GAP_DETECTED,
            summary="PIID profile source limitations detected.",
            payload={
                "gap_count": len(gaps),
                "gap_fields": [gap.field_key for gap in gaps],
            },
        )
    if recommended_enrichment_routes:
        append_event(
            PiidHermesEventType.NEXT_ENRICHMENT_RECOMMENDED,
            summary="Next enrichment routes recommended for review.",
            payload={
                "route_count": len(recommended_enrichment_routes),
                "route_types": [
                    route.route_type.value for route in recommended_enrichment_routes
                ],
            },
        )
    return tuple(events)


def _hermes_event(
    *,
    event_type: PiidHermesEventType,
    profile_id: str,
    normalized_piid: str,
    source_capability_id: str,
    occurred_at: str,
    sequence: int,
    summary: str,
    payload: dict[str, object],
) -> PiidHermesEvent:
    return PiidHermesEvent(
        id=(
            f"piid_event_{_safe_identifier(profile_id)}_"
            f"{sequence:03d}_{event_type.value}"
        ),
        event_type=event_type,
        profile_id=profile_id,
        normalized_piid=normalized_piid,
        occurred_at=occurred_at,
        summary=summary,
        payload=payload,
        source_capability_id=source_capability_id,
    )


def _transactions_from_history(
    award_history: USAspendingAwardHistoryResult | None,
) -> tuple[PiidAwardTransaction, ...]:
    if award_history is None:
        return ()
    return tuple(
        PiidAwardTransaction(
            transaction_id=transaction.transaction_id,
            action_date=transaction.action_date,
            fiscal_year=transaction.fiscal_year,
            modification_number=transaction.modification_number,
            action_type=transaction.action_type,
            obligation=transaction.obligation,
            description=transaction.description,
        )
        for transaction in award_history.transaction_history
    )


def _modifications_from_history(
    award_history: USAspendingAwardHistoryResult | None,
) -> tuple[PiidAwardTransaction, ...]:
    return tuple(
        transaction
        for transaction in _transactions_from_history(award_history)
        if transaction.modification_number
        and transaction.modification_number.strip().upper() not in {"0", "00", "000"}
    )


def _burn_posture_from_history(
    baseline: PiidAwardBaseline,
    award_history: USAspendingAwardHistoryResult | None,
) -> PiidBurnPosture:
    transactions = _transactions_from_history(award_history)
    obligations = [
        transaction.obligation
        for transaction in transactions
        if transaction.obligation is not None
    ]
    net_obligations = round(sum(obligations), 2) if obligations else None
    derivation_notes = list(award_history.derivation_notes if award_history else ())
    if net_obligations is None and baseline.award_amount is not None:
        net_obligations = baseline.award_amount
        derivation_notes.append(
            "Used award baseline award_amount because transaction history was empty."
        )
    fiscal_year_obligations: dict[int, float] = {}
    for transaction in transactions:
        if transaction.fiscal_year is None or transaction.obligation is None:
            continue
        fiscal_year_obligations[transaction.fiscal_year] = round(
            fiscal_year_obligations.get(transaction.fiscal_year, 0.0)
            + transaction.obligation,
            2,
        )
    period_days = _inclusive_period_days(baseline.start_date, baseline.end_date)
    daily_burn_rate = None
    monthly_burn_rate = None
    if net_obligations is not None and period_days:
        daily_burn_rate = round(net_obligations / period_days, 2)
        monthly_burn_rate = round(net_obligations / (period_days / 30.5), 2)
    if obligations and period_days:
        completeness = "complete"
    elif net_obligations is not None or period_days is not None:
        completeness = "partial"
    else:
        completeness = "unavailable"
    return PiidBurnPosture(
        net_obligations=net_obligations,
        fiscal_year_obligations=fiscal_year_obligations,
        period_start=baseline.start_date,
        period_end=baseline.end_date,
        period_days=period_days,
        monthly_burn_rate=monthly_burn_rate,
        daily_burn_rate=daily_burn_rate,
        transaction_count=len(transactions),
        modification_count=len(_modifications_from_history(award_history)),
        option_signals=_option_signals_from_transactions(transactions),
        deobligation_warnings=_deobligation_warnings_from_transactions(transactions),
        derivation_notes=tuple(derivation_notes),
        completeness=completeness,
    )


def _option_signals_from_transactions(
    transactions: tuple[PiidAwardTransaction, ...],
) -> tuple[str, ...]:
    signals = []
    for transaction in transactions:
        text = " ".join(
            piece
            for piece in (transaction.action_type, transaction.description)
            if piece
        ).lower()
        if "option" in text:
            signals.append(_transaction_summary(transaction))
    return tuple(signals)


def _deobligation_warnings_from_transactions(
    transactions: tuple[PiidAwardTransaction, ...],
) -> tuple[str, ...]:
    warnings = []
    for transaction in transactions:
        if transaction.obligation is not None and transaction.obligation < 0:
            warnings.append(
                f"{_transaction_label(transaction)} deobligated "
                f"${abs(transaction.obligation):,.2f}"
            )
    return tuple(warnings)


def _transaction_summary(transaction: PiidAwardTransaction) -> str:
    description = transaction.description or transaction.action_type or "transaction"
    return f"{_transaction_label(transaction)}: {description}"


def _transaction_label(transaction: PiidAwardTransaction) -> str:
    modification = (
        transaction.modification_number or transaction.transaction_id or "transaction"
    )
    if transaction.action_date:
        return f"{modification} on {transaction.action_date}"
    return modification


def _inclusive_period_days(
    period_start: str | None,
    period_end: str | None,
) -> int | None:
    if not period_start or not period_end:
        return None
    try:
        return (
            date.fromisoformat(period_end) - date.fromisoformat(period_start)
        ).days + 1
    except ValueError:
        return None


def classify_piid_scenario(
    baseline: PiidAwardBaseline,
    vehicle_context: PiidVehicleContext | None = None,
) -> PiidScenarioClassification:
    if vehicle_context and (
        vehicle_context.parent_idv or vehicle_context.parent_generated_internal_id
    ):
        return PiidScenarioClassification.IDIQ_ORDER
    if baseline.parent_idv:
        return PiidScenarioClassification.IDIQ_ORDER
    if baseline.award_type == "idv" or (
        vehicle_context is not None and vehicle_context.child_orders
    ):
        return PiidScenarioClassification.PARENT_IDIQ
    if baseline.award_type == "contract":
        return PiidScenarioClassification.STANDALONE_CONTRACT
    return PiidScenarioClassification.UNKNOWN


def _deterministic_pivots_from_baseline(
    baseline: PiidAwardBaseline,
) -> tuple[PiidDeterministicPivot, ...]:
    pivot_specs = (
        (PiidPivotType.UEI, baseline.recipient_uei, "recipient_uei"),
        (
            PiidPivotType.PARENT_UEI,
            baseline.parent_recipient_uei,
            "parent_recipient_uei",
        ),
        (PiidPivotType.SOLICITATION_ID, baseline.solicitation_id, "solicitation_id"),
        (PiidPivotType.NAICS_CODE, baseline.naics_code, "naics_code"),
        (PiidPivotType.PSC_CODE, baseline.psc_code, "psc_code"),
        (
            PiidPivotType.AWARDING_AGENCY,
            baseline.awarding_agency_name,
            "awarding_agency_name",
        ),
        (
            PiidPivotType.AWARDING_SUB_AGENCY,
            baseline.awarding_sub_agency_name,
            "awarding_sub_agency_name",
        ),
        (PiidPivotType.PARENT_IDV, baseline.parent_idv, "parent_idv"),
        (
            PiidPivotType.GENERATED_INTERNAL_ID,
            baseline.generated_internal_id,
            "generated_internal_id",
        ),
        (PiidPivotType.PERMALINK, baseline.permalink, "permalink"),
    )
    return tuple(
        PiidDeterministicPivot(
            pivot_type=pivot_type,
            value=value,
            source_field=source_field,
        )
        for pivot_type, value, source_field in pivot_specs
        if value
    )


def _vehicle_context_from_history(
    baseline: PiidAwardBaseline,
    award_history: USAspendingAwardHistoryResult | None,
) -> PiidVehicleContext:
    detail = award_history.award_detail if award_history else {}
    child_orders = _child_orders_from_history(award_history)
    parent_idv = baseline.parent_idv or _string_from_keys(
        detail,
        "parent_award_piid",
        "parent_piid",
        "parent_idv",
    )
    parent_generated_internal_id = _string_from_keys(
        detail,
        "parent_award_generated_internal_id",
        "parent_generated_internal_id",
        "parent_award_id",
    )
    notes = []
    if parent_idv or parent_generated_internal_id:
        notes.append("Parent vehicle linkage came from get_award_detail.")
    if child_orders:
        notes.append("Child order context came from get_idv_children.")
    linkage_confidence = "none"
    if (parent_idv and parent_generated_internal_id) or child_orders:
        linkage_confidence = "linked"
    elif parent_idv or parent_generated_internal_id:
        linkage_confidence = "partial"
    return PiidVehicleContext(
        parent_idv=parent_idv,
        parent_generated_internal_id=parent_generated_internal_id,
        child_orders=child_orders,
        linkage_confidence=linkage_confidence,
        derivation_notes=tuple(notes),
    )


def _child_orders_from_history(
    award_history: USAspendingAwardHistoryResult | None,
) -> tuple[PiidVehicleRelatedAward, ...]:
    if award_history is None:
        return ()
    return tuple(
        PiidVehicleRelatedAward(
            piid=child.piid,
            generated_internal_id=child.generated_internal_id,
            recipient_name=child.recipient_name,
            obligated_amount=child.obligated_amount,
            period_start=child.period_start,
            period_end=child.period_end,
        )
        for child in award_history.idv_children
    )


def _string_from_keys(row: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _gaps_from_baseline(baseline: PiidAwardBaseline) -> tuple[PiidProfileGap, ...]:
    missing_fields = {
        "uei": "SAM.gov entity enrichment",
        "parent_uei": "SAM.gov parent entity enrichment",
        "naics_code": "USAspending award detail or SAM.gov enrichment",
        "psc_code": "USAspending award detail or market research enrichment",
        "solicitation_id": "SAM.gov opportunity enrichment",
        "award_amount": "USAspending award detail enrichment",
        "start_date": "USAspending award detail enrichment",
        "end_date": "USAspending award detail enrichment",
        "parent_idv": "USAspending vehicle context enrichment",
        "permalink": "USAspending award detail enrichment",
    }
    gaps = []
    for field_key, route in missing_fields.items():
        baseline_field = {
            "uei": "recipient_uei",
            "parent_uei": "parent_recipient_uei",
        }.get(field_key, field_key)
        if getattr(baseline, baseline_field) is None:
            gaps.append(
                PiidProfileGap(
                    field_key=field_key,
                    source_limitation=(
                        f"USAspending lookup_piid did not provide {field_key}."
                    ),
                    recommended_enrichment_route=route,
                )
            )
    return tuple(gaps)


def _profile_id_for_piid(normalized_piid: str) -> str:
    safe_piid = _safe_identifier(normalized_piid).upper()
    return f"piid_profile_{safe_piid}"


def _safe_identifier(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_" for character in value
    ).strip("_")
