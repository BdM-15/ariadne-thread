from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, Field

from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunOutput,
    CapabilityRunStore,
)
from ariadne.focused_capture_skills import CompetitiveGapRouteHint


class WorkProductDeltaDestination(StrEnum):
    LIVING_PACKET = "living_packet"
    ACTION_PLAN = "action_plan"
    CALL_PLAN = "call_plan"
    RISK_REGISTER = "risk_register"
    FOLLOW_UP_ROUTE = "follow_up_route"
    ARTIFACT_CONTEXT = "artifact_context"


class WorkProductDeltaReviewState(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    EDITED = "edited"
    DISCARDED = "discarded"
    ROUTED = "routed"


class WorkProductDelta(BaseModel):
    id: str
    opportunity_id: str
    destination: WorkProductDeltaDestination
    title: str
    field_key: str | None = None
    source_capability_run_id: str
    source_output_id: str
    source_capability_id: str
    review_state: WorkProductDeltaReviewState = (
        WorkProductDeltaReviewState.PENDING_REVIEW
    )
    before_summary: str
    after_summary: str
    source_refs: tuple[str, ...] = ()
    capability_output_refs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    provenance: dict[str, object] = Field(default_factory=dict)


class WorkProductDeltaCreateFromCapabilityOutputRequest(BaseModel):
    opportunity_id: str
    capability_run_id: str
    output_id: str


class WorkProductDeltaListResponse(BaseModel):
    deltas: tuple[WorkProductDelta, ...]
    summary: dict[str, int]


class WorkProductDeltaDetailResponse(BaseModel):
    delta: WorkProductDelta


class WorkProductDeltaStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, delta: WorkProductDelta) -> WorkProductDelta:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(delta.id).write_text(
            delta.model_dump_json(indent=2), encoding="utf-8"
        )
        return delta

    def read(self, delta_id: str) -> WorkProductDelta:
        return WorkProductDelta.model_validate_json(
            self._path(delta_id).read_text(encoding="utf-8")
        )

    def list(
        self,
        *,
        opportunity_id: str | None = None,
        destination: WorkProductDeltaDestination | None = None,
        source_output_id: str | None = None,
    ) -> tuple[WorkProductDelta, ...]:
        if not self.root.exists():
            return ()
        deltas = tuple(
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        )
        if opportunity_id is not None:
            deltas = tuple(
                delta for delta in deltas if delta.opportunity_id == opportunity_id
            )
        if destination is not None:
            deltas = tuple(
                delta for delta in deltas if delta.destination is destination
            )
        if source_output_id is not None:
            deltas = tuple(
                delta for delta in deltas if delta.source_output_id == source_output_id
            )
        return deltas

    def _path(self, delta_id: str) -> Path:
        if not delta_id or delta_id != Path(delta_id).name:
            raise ValueError("delta_id must be a file-safe identifier")
        return self.root / f"{delta_id}.json"


def create_work_product_deltas_from_capability_output(
    *,
    capability_store: CapabilityRunStore,
    delta_store: WorkProductDeltaStore,
    request: WorkProductDeltaCreateFromCapabilityOutputRequest,
) -> WorkProductDeltaListResponse:
    run = capability_store.read(request.capability_run_id)
    output = _find_run_output(run, request.output_id)
    deltas = build_competitive_gap_work_product_deltas(
        run=run,
        output=output,
        opportunity_id=request.opportunity_id,
    )
    stored_deltas = tuple(delta_store.write(delta) for delta in deltas)
    return WorkProductDeltaListResponse(
        deltas=_ordered_deltas(stored_deltas),
        summary=_delta_summary(stored_deltas),
    )


def list_work_product_deltas(
    *,
    store: WorkProductDeltaStore,
    opportunity_id: str | None = None,
    destination: WorkProductDeltaDestination | None = None,
) -> WorkProductDeltaListResponse:
    deltas = store.list(opportunity_id=opportunity_id, destination=destination)
    return WorkProductDeltaListResponse(
        deltas=_ordered_deltas(deltas),
        summary=_delta_summary(deltas),
    )


def get_work_product_delta(
    *,
    store: WorkProductDeltaStore,
    delta_id: str,
) -> WorkProductDeltaDetailResponse:
    return WorkProductDeltaDetailResponse(delta=store.read(delta_id))


def build_competitive_gap_work_product_deltas(
    *,
    run: CapabilityRun,
    output: CapabilityRunOutput,
    opportunity_id: str,
) -> tuple[WorkProductDelta, WorkProductDelta]:
    if run.capability_id != "competitive-gap-route-hint":
        raise ValueError("Capability Run is not a competitive-gap-route-hint run")
    if run.opportunity_id is not None and run.opportunity_id != opportunity_id:
        raise ValueError("Capability Run does not match the requested Opportunity")
    hint_payload = output.provenance.get("competitive_gap_route_hint")
    if hint_payload is None:
        raise ValueError(
            "Capability Run Output is missing competitive gap route hint provenance"
        )
    hint = CompetitiveGapRouteHint.model_validate(hint_payload)
    capability_output_ref = f"capability-run://{run.run_id}/outputs/{output.output_id}"
    shared = {
        "opportunity_id": opportunity_id,
        "field_key": hint.field_key,
        "source_capability_run_id": run.run_id,
        "source_output_id": output.output_id,
        "source_capability_id": run.capability_id,
        "source_refs": hint.source_refs,
        "capability_output_refs": (capability_output_ref,),
        "assumptions": hint.assumptions,
        "gaps": hint.gaps,
        "provenance": {
            "capability_id": run.capability_id,
            "capability_run_id": run.run_id,
            "capability_output_id": output.output_id,
            "capability_output_type": output.output_type,
            "recommended_route": hint.recommended_route,
            "rationale": hint.rationale,
            "review_destination": hint.review_destination,
            "source_output_review_state": output.review_state.value,
            "trusted_downstream_writes": False,
        },
    }
    return (
        WorkProductDelta(
            id=_delta_id(
                opportunity_id=opportunity_id,
                output_id=output.output_id,
                destination=WorkProductDeltaDestination.LIVING_PACKET,
            ),
            destination=WorkProductDeltaDestination.LIVING_PACKET,
            title="Living Packet competition update candidate",
            before_summary=(
                f"{_field_label(hint.field_key)} field remains unchanged until this "
                "Work Product Delta is reviewed."
            ),
            after_summary=hint.packet_implication,
            **shared,
        ),
        WorkProductDelta(
            id=_delta_id(
                opportunity_id=opportunity_id,
                output_id=output.output_id,
                destination=WorkProductDeltaDestination.ACTION_PLAN,
            ),
            destination=WorkProductDeltaDestination.ACTION_PLAN,
            title="Action Plan competitive proof-gap implication",
            before_summary=(
                "Action Plan has no reviewed proof-gap follow-up from this "
                "competitive gap route hint."
            ),
            after_summary=(
                "Review proof gaps and customer-validation follow-up before this "
                f"packet implication changes the Action Plan: {hint.recommended_route}"
            ),
            **shared,
        ),
    )


def _find_run_output(run: CapabilityRun, output_id: str) -> CapabilityRunOutput:
    for output in run.outputs:
        if output.output_id == output_id:
            return output
    raise FileNotFoundError(f"Capability Run Output not found: {output_id}")


def _delta_id(
    *,
    opportunity_id: str,
    output_id: str,
    destination: WorkProductDeltaDestination,
) -> str:
    digest = sha256(
        f"{opportunity_id}:{output_id}:{destination.value}".encode("utf-8")
    ).hexdigest()[:12]
    return f"delta_{digest}_{destination.value}"


def _field_label(field_key: str) -> str:
    return field_key.replace("_", " ").title()


def _delta_summary(deltas: tuple[WorkProductDelta, ...]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for delta in deltas:
        summary[delta.destination.value] = summary.get(delta.destination.value, 0) + 1
    return summary


def _ordered_deltas(
    deltas: tuple[WorkProductDelta, ...],
) -> tuple[WorkProductDelta, ...]:
    destination_order = {
        WorkProductDeltaDestination.LIVING_PACKET: 0,
        WorkProductDeltaDestination.ACTION_PLAN: 1,
        WorkProductDeltaDestination.CALL_PLAN: 2,
        WorkProductDeltaDestination.RISK_REGISTER: 3,
        WorkProductDeltaDestination.FOLLOW_UP_ROUTE: 4,
        WorkProductDeltaDestination.ARTIFACT_CONTEXT: 5,
    }
    return tuple(
        sorted(
            deltas,
            key=lambda delta: (destination_order.get(delta.destination, 99), delta.id),
        )
    )
