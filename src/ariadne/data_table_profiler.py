from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
import re
from typing import Any

from pydantic import BaseModel, Field

from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunAutonomyRecommendation,
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutput,
    CapabilityRunOutputReviewState,
    CapabilityRunSessionContext,
    CapabilityRunStatus,
    CapabilityRunStore,
)


class DataTableProfileRequest(BaseModel):
    table_label: str
    source_ref: str
    rows: tuple[dict[str, Any], ...]
    source_refs: tuple[str, ...] = ()
    max_sample_values: int = Field(default=3, ge=1, le=10)


class DataTableShape(BaseModel):
    row_count: int
    column_count: int


class DataTableFieldProfile(BaseModel):
    name: str
    value_kind: str
    non_null_count: int
    missing_count: int
    missing_ratio: float
    distinct_count: int
    sample_values: tuple[str, ...]


class DataTableAnomaly(BaseModel):
    kind: str
    severity: str
    summary: str
    field_name: str | None = None


class DataTableRecommendedRoute(BaseModel):
    route_id: str
    label: str
    rationale: str
    review_destination: str = "Capability Run Output"


class DataTableProfile(BaseModel):
    table_label: str
    source_ref: str
    source_refs: tuple[str, ...]
    shape: DataTableShape
    fields: tuple[DataTableFieldProfile, ...]
    key_fields: tuple[DataTableFieldProfile, ...]
    anomalies: tuple[DataTableAnomaly, ...]
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]
    recommended_next_route: DataTableRecommendedRoute
    review_state: str = "pending_review"
    trusted_downstream_writes: bool = False


def build_data_table_profile(request: DataTableProfileRequest) -> DataTableProfile:
    columns = _ordered_columns(request.rows)
    fields = tuple(
        _field_profile(
            column=column,
            rows=request.rows,
            row_count=len(request.rows),
            max_sample_values=request.max_sample_values,
        )
        for column in columns
    )
    anomalies = _profile_anomalies(fields, row_count=len(request.rows))
    gaps = _profile_gaps(anomalies=anomalies, row_count=len(request.rows))
    return DataTableProfile(
        table_label=request.table_label,
        source_ref=request.source_ref,
        source_refs=_unique_refs((request.source_ref, *request.source_refs)),
        shape=DataTableShape(row_count=len(request.rows), column_count=len(columns)),
        fields=fields,
        key_fields=_key_fields(fields),
        anomalies=anomalies,
        assumptions=(
            "Input rows were treated as one rectangular table-like source.",
            "Empty strings and null values were treated as missing.",
            "No live model, network, or external file access was used.",
        ),
        gaps=gaps,
        recommended_next_route=_recommended_route(anomalies),
    )


def run_data_table_profile_capability(
    *,
    request: DataTableProfileRequest,
    store: CapabilityRunStore,
    opportunity_id: str | None = None,
    product_workflow: str = "data_table_profile",
) -> CapabilityRun:
    profile = build_data_table_profile(request)
    completed_at = datetime.now(UTC)
    digest = _request_digest(request)
    output = CapabilityRunOutput(
        output_id=f"output_data_table_profile_{digest}",
        output_type="data_table_profile",
        title=f"Data table profile: {request.table_label}",
        summary=(
            f"Profiled {profile.shape.row_count} rows and "
            f"{profile.shape.column_count} columns from {request.source_ref}; "
            f"found {len(profile.anomalies)} review item(s)."
        ),
        gaps=profile.gaps,
        review_state=CapabilityRunOutputReviewState.PENDING,
        autonomy_recommendation=CapabilityRunAutonomyRecommendation.REVIEW_REQUIRED,
        recommended_destination="Capability Run Output",
        provenance={
            "capability_id": "data-table-profiler",
            "data_table_profile": profile.model_dump(mode="json"),
            "source_refs": list(profile.source_refs),
            "review_gate_required": True,
            "trusted_downstream_writes": False,
        },
    )
    run = CapabilityRun(
        run_id=f"caprun_data_table_profile_{digest}",
        capability_id="data-table-profiler",
        capability_type=CapabilityRunCapabilityType.SKILL,
        executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
        session_context=CapabilityRunSessionContext.STUDIO,
        opportunity_id=opportunity_id,
        product_workflow=product_workflow,
        status=CapabilityRunStatus.NEEDS_REVIEW,
        inputs_summary=(
            f"Profiled table-like source {request.source_ref} with "
            f"{len(request.rows)} supplied row(s)."
        ),
        input_refs=profile.source_refs,
        outputs=(output,),
        provenance={
            "capability_id": "data-table-profiler",
            "executor": CapabilityRunExecutorKind.DETERMINISTIC_PYTHON.value,
            "source_ref": request.source_ref,
            "source_refs": list(profile.source_refs),
            "row_count": profile.shape.row_count,
            "column_count": profile.shape.column_count,
            "network_required": False,
            "model_required": False,
            "external_file_access": False,
            "trusted_downstream_writes": False,
            "completed_at": completed_at.isoformat(),
        },
        completed_at=completed_at,
    )
    return store.write(run)


def _ordered_columns(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column in seen:
                continue
            seen.add(column)
            columns.append(column)
    return tuple(columns)


def _field_profile(
    *,
    column: str,
    rows: tuple[dict[str, Any], ...],
    row_count: int,
    max_sample_values: int,
) -> DataTableFieldProfile:
    values = [row.get(column) for row in rows]
    present_values = [value for value in values if not _is_missing(value)]
    missing_count = row_count - len(present_values)
    distinct_values = {_stable_value(value) for value in present_values}
    return DataTableFieldProfile(
        name=column,
        value_kind=_value_kind(present_values),
        non_null_count=len(present_values),
        missing_count=missing_count,
        missing_ratio=round(missing_count / row_count, 3) if row_count else 0.0,
        distinct_count=len(distinct_values),
        sample_values=tuple(sorted(distinct_values)[:max_sample_values]),
    )


def _profile_anomalies(
    fields: tuple[DataTableFieldProfile, ...],
    *,
    row_count: int,
) -> tuple[DataTableAnomaly, ...]:
    if row_count == 0:
        return (
            DataTableAnomaly(
                kind="empty_table",
                severity="high",
                summary="No rows were supplied for profiling.",
            ),
        )

    anomalies: list[DataTableAnomaly] = []
    for field in fields:
        if field.missing_count:
            anomalies.append(
                DataTableAnomaly(
                    kind="missing_values",
                    severity="medium",
                    field_name=field.name,
                    summary=(
                        f"{field.name} is missing {field.missing_count} of "
                        f"{row_count} value(s)."
                    ),
                )
            )
        if field.value_kind == "mixed":
            anomalies.append(
                DataTableAnomaly(
                    kind="mixed_value_types",
                    severity="medium",
                    field_name=field.name,
                    summary=f"{field.name} mixes value types and needs review.",
                )
            )
        if _looks_like_identifier(field.name) and field.distinct_count < field.non_null_count:
            anomalies.append(
                DataTableAnomaly(
                    kind="duplicate_identifier",
                    severity="high",
                    field_name=field.name,
                    summary=f"{field.name} has duplicate non-empty identifier values.",
                )
            )
    return tuple(anomalies)


def _profile_gaps(
    *,
    anomalies: tuple[DataTableAnomaly, ...],
    row_count: int,
) -> tuple[str, ...]:
    if row_count == 0:
        return ("Supply rows before using this table as capture evidence.",)
    if anomalies:
        return (
            "Review missing or anomalous table fields before trusted use.",
            "Confirm whether the table should route to packet, research, or source-profile review.",
        )
    return ("Confirm field meanings and source freshness before routing.",)


def _recommended_route(
    anomalies: tuple[DataTableAnomaly, ...],
) -> DataTableRecommendedRoute:
    if anomalies:
        return DataTableRecommendedRoute(
            route_id="review_data_quality_before_packet_or_research_route",
            label="Review data quality before routing",
            rationale="Missing, duplicate, or mixed fields should be reviewed before capture use.",
        )
    return DataTableRecommendedRoute(
        route_id="route_profile_to_packet_or_research_review",
        label="Route profile to packet or research review",
        rationale="No obvious table-quality anomalies were found in the supplied rows.",
    )


def _key_fields(
    fields: tuple[DataTableFieldProfile, ...],
) -> tuple[DataTableFieldProfile, ...]:
    likely_keys = tuple(
        field
        for field in fields
        if _looks_like_identifier(field.name) or field.missing_ratio <= 0.1
    )
    if likely_keys:
        return likely_keys[:3]
    return fields[:3]


def _value_kind(values: list[Any]) -> str:
    if not values:
        return "empty"
    kinds = {_single_value_kind(value) for value in values}
    if kinds == {"integer", "number"}:
        return "number"
    if len(kinds) == 1:
        return next(iter(kinds))
    return "mixed"


def _single_value_kind(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return "date"
    if isinstance(value, str):
        return "text"
    return type(value).__name__


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _looks_like_identifier(field_name: str) -> bool:
    normalized = field_name.lower()
    return "id" in normalized or "contract" in normalized or "piid" in normalized


def _stable_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, sort_keys=True, default=str)


def _unique_refs(refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def _request_digest(request: DataTableProfileRequest) -> str:
    payload = request.model_dump(mode="json")
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]