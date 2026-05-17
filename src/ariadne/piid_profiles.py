from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from ariadne.usaspending import USAspendingAwardLookupResult


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


class PiidContractIntelligenceProfile(BaseModel):
    id: str
    input_contract_number: str
    normalized_piid: str
    scenario: PiidScenarioClassification
    provenance: PiidProfileProvenance
    award_baseline: PiidAwardBaseline
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
    return PiidContractIntelligenceProfile(
        id=profile_id or _profile_id_for_piid(lookup.normalized_piid),
        input_contract_number=lookup.input_contract_number,
        normalized_piid=lookup.normalized_piid,
        scenario=classify_piid_scenario(baseline),
        provenance=PiidProfileProvenance(
            source_capability_id=lookup.provenance.source_capability_id,
            source_tool_name=lookup.provenance.source_tool_name,
            source_package=lookup.provenance.source_package,
            source_package_version=lookup.provenance.source_package_version,
            checked_at=lookup.provenance.checked_at,
            lookup_status=lookup.status.value,
        ),
        award_baseline=baseline,
        deterministic_pivots=_deterministic_pivots_from_baseline(baseline),
        gaps=_gaps_from_baseline(baseline),
        created_at=timestamp,
        updated_at=timestamp,
    )


def classify_piid_scenario(
    baseline: PiidAwardBaseline,
) -> PiidScenarioClassification:
    if baseline.parent_idv:
        return PiidScenarioClassification.IDIQ_ORDER
    if baseline.award_type == "idv":
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
