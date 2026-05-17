from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

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
    return PiidContractIntelligenceProfile(
        id=profile_id or _profile_id_for_piid(lookup.normalized_piid),
        input_contract_number=lookup.input_contract_number,
        normalized_piid=lookup.normalized_piid,
        scenario=classify_piid_scenario(baseline, vehicle_context),
        provenance=PiidProfileProvenance(
            source_capability_id=lookup.provenance.source_capability_id,
            source_tool_name=lookup.provenance.source_tool_name,
            source_package=lookup.provenance.source_package,
            source_package_version=lookup.provenance.source_package_version,
            checked_at=lookup.provenance.checked_at,
            lookup_status=lookup.status.value,
        ),
        award_baseline=baseline,
        transaction_history=_transactions_from_history(award_history),
        modification_history=_modifications_from_history(award_history),
        burn_posture=_burn_posture_from_history(baseline, award_history),
        vehicle_context=vehicle_context,
        deterministic_pivots=_deterministic_pivots_from_baseline(baseline),
        gaps=_gaps_from_baseline(baseline),
        created_at=timestamp,
        updated_at=timestamp,
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
    safe_piid = "".join(
        character if character.isalnum() else "_" for character in normalized_piid
    ).strip("_")
    return f"piid_profile_{safe_piid}"
