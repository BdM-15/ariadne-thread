from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ariadne.opportunities import MilestoneGate
from ariadne.packet_knowledge import (
    AnswerPathKind,
    PacketFieldAnswer,
    PacketFieldAnswerStore,
    PacketFieldAnswerStatus,
    PacketFieldDefinition,
    create_packet_field_answer,
)
from ariadne.packets import EvidenceStatus


class OpportunityActivationRunTrigger(StrEnum):
    INITIAL_SCAFFOLD = "initial_scaffold"
    USER_REQUEST = "user_request"
    MATERIAL_REFRESH = "material_refresh"


class OpportunityActivationRunStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class OpportunityActivationReviewState(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"
    ROUTED = "routed"


class OpportunityActivationFieldReviewDecisionType(StrEnum):
    ACCEPT = "accept"
    EDIT = "edit"
    ROUTE = "route"
    DISCARD = "discard"


class PacketFieldActionState(StrEnum):
    ANSWERED = "answered"
    REVIEW_READY = "review_ready"
    BLOCKED = "blocked"


class OpportunityActivationDigest(BaseModel):
    coverage_gained: tuple[str, ...]
    review_ready_count: int
    blocked_field_count: int
    recommended_skill_chains: tuple[str, ...]
    approval_required_routes: tuple[str, ...]
    source_limitations: tuple[str, ...]
    next_best_actions: tuple[str, ...]


class PacketFieldActionItem(BaseModel):
    field_key: str
    label: str
    question: str
    section: str
    value_kind: str
    current_status: str
    evidence_status: str
    action_state: PacketFieldActionState
    answer_paths: tuple[str, ...]
    required_milestone_gates: tuple[str, ...] = ()
    current_gate_required: bool = True
    recommended_route: str
    route_rationale: str
    requires_review: bool = True
    approval_required: bool = False
    source_refs: tuple[str, ...] = ()
    gap_summary: str | None = None
    current_value: str | None = None


class PacketFieldActionMatrix(BaseModel):
    opportunity_id: str
    current_milestone_gate: str = MilestoneGate.MILESTONE_1.value
    fields: tuple[PacketFieldActionItem, ...]
    blocked_field_count: int
    review_ready_count: int
    answered_field_count: int
    current_gate_field_count: int = 0
    current_gate_blocked_count: int = 0
    current_gate_review_ready_count: int = 0
    current_gate_answered_count: int = 0
    approval_required_count: int
    source_ref_count: int


class OpportunityActivationRunOutput(BaseModel):
    output_id: str
    field_key: str
    title: str
    summary: str
    recommended_destination: str = "packet_field_action_surface"
    recommended_route: str
    review_state: OpportunityActivationReviewState = (
        OpportunityActivationReviewState.PENDING_REVIEW
    )


class OpportunityActivationFieldReviewRequest(BaseModel):
    decision: OpportunityActivationFieldReviewDecisionType
    reviewer_rationale: str = ""
    value: str | None = None
    evidence_ids: tuple[str, ...] = ()
    confidence: float | None = Field(default=None, ge=0, le=1)
    routed_destination: str | None = None


class OpportunityActivationFieldReviewDecision(BaseModel):
    decision_id: str
    run_id: str
    opportunity_id: str
    field_key: str
    decision: OpportunityActivationFieldReviewDecisionType
    reviewer_rationale: str
    review_gate: str
    promoted_answer_created: bool = False
    routed_destination: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OpportunityActivationFieldReviewResponse(BaseModel):
    run: OpportunityActivationRun
    decision: OpportunityActivationFieldReviewDecision
    packet_field_answer: PacketFieldAnswer | None = None


class OpportunityActivationRun(BaseModel):
    run_id: str
    opportunity_id: str
    trigger: OpportunityActivationRunTrigger
    status: OpportunityActivationRunStatus
    review_state: OpportunityActivationReviewState
    packet_field_count: int
    packet_field_gaps: int
    activation_digest: OpportunityActivationDigest
    packet_field_action_matrix: PacketFieldActionMatrix
    outputs: tuple[OpportunityActivationRunOutput, ...]
    provenance: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class OpportunityActivationRunListResponse(BaseModel):
    runs: tuple[OpportunityActivationRun, ...]


class OpportunityActivationRunStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, run: OpportunityActivationRun) -> OpportunityActivationRun:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(run.run_id).write_text(
            run.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return run

    def read(self, run_id: str) -> OpportunityActivationRun:
        return OpportunityActivationRun.model_validate_json(
            self._path(run_id).read_text(encoding="utf-8")
        )

    def list(
        self,
        *,
        opportunity_id: str | None = None,
    ) -> tuple[OpportunityActivationRun, ...]:
        if not self.root.exists():
            return ()
        runs = tuple(
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        )
        if opportunity_id is None:
            return runs
        return tuple(run for run in runs if run.opportunity_id == opportunity_id)

    def _path(self, run_id: str) -> Path:
        if not run_id or run_id != Path(run_id).name:
            raise ValueError("run_id must be a file-safe identifier")
        return self.root / f"{run_id}.json"


def run_opportunity_activation(
    *,
    opportunity_id: str,
    definitions: tuple[PacketFieldDefinition, ...],
    answers: tuple[PacketFieldAnswer, ...] = (),
    trigger: OpportunityActivationRunTrigger = OpportunityActivationRunTrigger.USER_REQUEST,
    store: OpportunityActivationRunStore | None = None,
    created_at: datetime | None = None,
    initial_coverage: tuple[str, ...] = (),
    run_id: str | None = None,
    current_milestone_gate: MilestoneGate | str = MilestoneGate.MILESTONE_1,
) -> OpportunityActivationRun:
    milestone_gate = _coerce_milestone_gate(current_milestone_gate)
    completed_at = created_at or datetime.now(UTC)
    matrix = build_packet_field_action_matrix(
        opportunity_id=opportunity_id,
        definitions=definitions,
        answers=answers,
        current_milestone_gate=milestone_gate,
    )
    digest = build_activation_digest(
        matrix=matrix,
        initial_coverage=initial_coverage,
    )
    outputs = tuple(
        _output_from_action_item(item)
        for item in matrix.fields
        if item.action_state is not PacketFieldActionState.ANSWERED
    )
    run = OpportunityActivationRun(
        run_id=run_id
        or _activation_run_id(
            opportunity_id=opportunity_id,
            trigger=trigger,
            matrix=matrix,
        ),
        opportunity_id=opportunity_id,
        trigger=trigger,
        status=OpportunityActivationRunStatus.NEEDS_REVIEW,
        review_state=OpportunityActivationReviewState.PENDING_REVIEW,
        packet_field_count=len(matrix.fields),
        packet_field_gaps=matrix.current_gate_blocked_count,
        activation_digest=digest,
        packet_field_action_matrix=matrix,
        outputs=outputs,
        provenance={
            "executor": "deterministic_python",
            "network_required": False,
            "model_required": False,
            "trusted_downstream_writes": False,
            "analyzed_at": completed_at.isoformat(),
        },
        created_at=completed_at,
        completed_at=completed_at,
    )
    if store is not None:
        return store.write(run)
    return run


def record_opportunity_activation_field_review(
    *,
    run_store: OpportunityActivationRunStore,
    answer_store: PacketFieldAnswerStore,
    run_id: str,
    field_key: str,
    request: OpportunityActivationFieldReviewRequest,
) -> OpportunityActivationFieldReviewResponse:
    run = run_store.read(run_id)
    action_item = _find_action_item(run, field_key)
    output = _find_output(run, field_key)
    if output.review_state is not OpportunityActivationReviewState.PENDING_REVIEW:
        raise ValueError("Activation field already reviewed")

    packet_field_answer: PacketFieldAnswer | None = None
    routed_destination = request.routed_destination
    if request.decision in {
        OpportunityActivationFieldReviewDecisionType.ACCEPT,
        OpportunityActivationFieldReviewDecisionType.EDIT,
    }:
        accepted_value = request.value.strip() if request.value else ""
        if not accepted_value:
            raise ValueError("accepted activation field review requires value")
        packet_field_answer = _answer_from_activation_review(
            run=run,
            action_item=action_item,
            request=request,
            accepted_value=accepted_value,
        )
        answer_store.write(packet_field_answer)
        action_item = action_item.model_copy(
            update={
                "current_status": PacketFieldAnswerStatus.ANSWERED.value,
                "evidence_status": packet_field_answer.evidence_status.value,
                "action_state": PacketFieldActionState.ANSWERED,
                "requires_review": False,
                "source_refs": packet_field_answer.evidence_ids,
                "gap_summary": packet_field_answer.gap_summary,
                "current_value": packet_field_answer.value,
            }
        )
    elif request.decision is OpportunityActivationFieldReviewDecisionType.ROUTE:
        if not routed_destination or not routed_destination.strip():
            raise ValueError("routed activation field review requires destination")
        routed_destination = routed_destination.strip()

    decision = OpportunityActivationFieldReviewDecision(
        decision_id=f"actreview_{uuid4().hex}",
        run_id=run.run_id,
        opportunity_id=run.opportunity_id,
        field_key=field_key,
        decision=request.decision,
        reviewer_rationale=request.reviewer_rationale.strip(),
        review_gate=_review_gate_for_field_decision(request.decision),
        promoted_answer_created=packet_field_answer is not None,
        routed_destination=routed_destination,
    )
    updated_run = _run_with_field_review(
        run=run,
        action_item=action_item,
        field_key=field_key,
        review_state=_review_state_for_field_decision(request.decision),
        decision=decision,
    )
    return OpportunityActivationFieldReviewResponse(
        run=run_store.write(updated_run),
        decision=decision,
        packet_field_answer=packet_field_answer,
    )


def build_packet_field_action_matrix(
    *,
    opportunity_id: str,
    definitions: tuple[PacketFieldDefinition, ...],
    answers: tuple[PacketFieldAnswer, ...] = (),
    current_milestone_gate: MilestoneGate | str = MilestoneGate.MILESTONE_1,
) -> PacketFieldActionMatrix:
    milestone_gate = _coerce_milestone_gate(current_milestone_gate)
    actions = tuple(
        _action_item_for_definition(
            opportunity_id=opportunity_id,
            definition=definition,
            current_milestone_gate=milestone_gate,
            answer=_answer_for_field(
                answers=answers,
                opportunity_id=opportunity_id,
                field_key=definition.key,
            ),
        )
        for definition in definitions
    )
    current_gate_actions = tuple(item for item in actions if item.current_gate_required)
    return PacketFieldActionMatrix(
        opportunity_id=opportunity_id,
        current_milestone_gate=milestone_gate.value,
        fields=actions,
        blocked_field_count=sum(
            1 for item in actions if item.action_state is PacketFieldActionState.BLOCKED
        ),
        review_ready_count=sum(
            1
            for item in actions
            if item.action_state is PacketFieldActionState.REVIEW_READY
        ),
        answered_field_count=sum(
            1 for item in actions if item.action_state is PacketFieldActionState.ANSWERED
        ),
        current_gate_field_count=len(current_gate_actions),
        current_gate_blocked_count=sum(
            1
            for item in current_gate_actions
            if item.action_state is PacketFieldActionState.BLOCKED
        ),
        current_gate_review_ready_count=sum(
            1
            for item in current_gate_actions
            if item.action_state is PacketFieldActionState.REVIEW_READY
        ),
        current_gate_answered_count=sum(
            1
            for item in current_gate_actions
            if item.action_state is PacketFieldActionState.ANSWERED
        ),
        approval_required_count=sum(1 for item in actions if item.approval_required),
        source_ref_count=sum(len(item.source_refs) for item in actions),
    )


def build_activation_digest(
    *,
    matrix: PacketFieldActionMatrix,
    initial_coverage: tuple[str, ...] = (),
) -> OpportunityActivationDigest:
    coverage = initial_coverage + (
        f"Analyzed {len(matrix.fields)} packet fields for answer paths.",
        f"Scoped {matrix.current_gate_field_count} fields to {matrix.current_milestone_gate}.",
        f"Mapped {matrix.blocked_field_count} blocked fields to recommended routes.",
    )
    if matrix.review_ready_count:
        coverage += (
            f"Found {matrix.review_ready_count} field candidates ready for review.",
        )
    return OpportunityActivationDigest(
        coverage_gained=coverage,
        review_ready_count=matrix.review_ready_count,
        blocked_field_count=matrix.blocked_field_count,
        recommended_skill_chains=_recommended_skill_chains(matrix),
        approval_required_routes=_approval_required_routes(matrix),
        source_limitations=_source_limitations(matrix),
        next_best_actions=_next_best_actions(matrix),
    )


def recommend_packet_field_route(definition: PacketFieldDefinition) -> str:
    kinds = {path.kind for path in definition.answer_paths}
    if AnswerPathKind.CAPABILITY_MODULE in kinds:
        return "Recommend a capability or skill-backed research route."
    if AnswerPathKind.EVIDENCE_EXTRACTION in kinds:
        return "Inspect source material and extract a reviewable answer candidate."
    if AnswerPathKind.IMPORTED_DATA in kinds:
        return "Import or lookup source-profile data before synthesis."
    if AnswerPathKind.MODEL_SYNTHESIS in kinds:
        return "Synthesize a reviewable answer from accepted evidence and gaps."
    return "Ask the capture lead or prepare a customer follow-up question."


def _action_item_for_definition(
    *,
    opportunity_id: str,
    definition: PacketFieldDefinition,
    current_milestone_gate: MilestoneGate,
    answer: PacketFieldAnswer | None,
) -> PacketFieldActionItem:
    current_status = (
        answer.status if answer is not None else PacketFieldAnswerStatus.UNANSWERED
    )
    evidence_status = answer.evidence_status if answer is not None else EvidenceStatus.GAP
    action_state = _action_state_for_answer(
        current_status=current_status,
        evidence_status=evidence_status,
    )
    answer_path_labels = tuple(path.label for path in definition.answer_paths)
    required_gates = tuple(gate.value for gate in definition.required_milestone_gates)
    current_gate_required = (
        not definition.required_milestone_gates
        or current_milestone_gate in definition.required_milestone_gates
    )
    gap_summary = None
    if answer is None:
        gap_summary = f"{definition.label} is not answered for this Opportunity."
    elif answer.gap_summary:
        gap_summary = answer.gap_summary

    return PacketFieldActionItem(
        field_key=definition.key,
        label=definition.label,
        question=definition.question,
        section=definition.section.value,
        value_kind=definition.value_kind.value,
        current_status=current_status.value,
        evidence_status=evidence_status.value,
        action_state=action_state,
        answer_paths=answer_path_labels,
        required_milestone_gates=required_gates,
        current_gate_required=current_gate_required,
        recommended_route=recommend_packet_field_route(definition),
        route_rationale=_route_rationale(definition),
        requires_review=action_state is not PacketFieldActionState.ANSWERED,
        approval_required=_approval_required(definition),
        source_refs=answer.evidence_ids if answer is not None else (),
        gap_summary=gap_summary,
        current_value=answer.value if answer is not None else None,
    )


def _coerce_milestone_gate(value: MilestoneGate | str) -> MilestoneGate:
    if isinstance(value, MilestoneGate):
        return value
    return MilestoneGate(value)


def _find_action_item(
    run: OpportunityActivationRun,
    field_key: str,
) -> PacketFieldActionItem:
    for item in run.packet_field_action_matrix.fields:
        if item.field_key == field_key:
            return item
    raise ValueError("Activation field not found")


def _find_output(
    run: OpportunityActivationRun,
    field_key: str,
) -> OpportunityActivationRunOutput:
    for output in run.outputs:
        if output.field_key == field_key:
            return output
    raise ValueError("Activation field has no reviewable output")


def _answer_from_activation_review(
    *,
    run: OpportunityActivationRun,
    action_item: PacketFieldActionItem,
    request: OpportunityActivationFieldReviewRequest,
    accepted_value: str,
) -> PacketFieldAnswer:
    evidence_status = (
        EvidenceStatus.ANSWERED
        if request.evidence_ids
        else EvidenceStatus.ASSUMPTION
    )
    rationale = request.reviewer_rationale.strip()
    provenance_note = (
        f"Accepted from activation run {run.run_id}: {rationale}"
        if rationale
        else f"Accepted from activation run {run.run_id}."
    )
    return create_packet_field_answer(
        field_key=action_item.field_key,
        opportunity_id=run.opportunity_id,
        value=accepted_value,
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=evidence_status,
        evidence_ids=request.evidence_ids,
        confidence=request.confidence,
        gap_summary=None,
        provenance_note=provenance_note,
        review_status=request.decision.value,
        source_draft_id=run.run_id,
        review_edits=(f"activation route: {action_item.recommended_route}",),
    )


def _run_with_field_review(
    *,
    run: OpportunityActivationRun,
    action_item: PacketFieldActionItem,
    field_key: str,
    review_state: OpportunityActivationReviewState,
    decision: OpportunityActivationFieldReviewDecision,
) -> OpportunityActivationRun:
    updated_outputs = tuple(
        output.model_copy(update={"review_state": review_state})
        if output.field_key == field_key
        else output
        for output in run.outputs
    )
    updated_fields = tuple(
        action_item if item.field_key == field_key else item
        for item in run.packet_field_action_matrix.fields
    )
    matrix = _matrix_with_fields(
        opportunity_id=run.opportunity_id,
        current_milestone_gate=run.packet_field_action_matrix.current_milestone_gate,
        fields=updated_fields,
    )
    digest = run.activation_digest.model_copy(
        update={
            "coverage_gained": run.activation_digest.coverage_gained
            + (f"Reviewed {action_item.label}: {decision.decision.value}.",),
            "review_ready_count": matrix.review_ready_count,
            "blocked_field_count": matrix.blocked_field_count,
            "source_limitations": _source_limitations(matrix),
            "next_best_actions": _next_best_actions(matrix),
        }
    )
    return run.model_copy(
        update={
            "packet_field_gaps": matrix.current_gate_blocked_count,
            "activation_digest": digest,
            "packet_field_action_matrix": matrix,
            "outputs": updated_outputs,
            "provenance": {
                **run.provenance,
                "field_review_decisions": [
                    *run.provenance.get("field_review_decisions", []),
                    decision.model_dump(mode="json"),
                ],
            },
        }
    )


def _matrix_with_fields(
    *,
    opportunity_id: str,
    current_milestone_gate: str,
    fields: tuple[PacketFieldActionItem, ...],
) -> PacketFieldActionMatrix:
    current_gate_fields = tuple(item for item in fields if item.current_gate_required)
    return PacketFieldActionMatrix(
        opportunity_id=opportunity_id,
        current_milestone_gate=current_milestone_gate,
        fields=fields,
        blocked_field_count=sum(
            1 for item in fields if item.action_state is PacketFieldActionState.BLOCKED
        ),
        review_ready_count=sum(
            1
            for item in fields
            if item.action_state is PacketFieldActionState.REVIEW_READY
        ),
        answered_field_count=sum(
            1 for item in fields if item.action_state is PacketFieldActionState.ANSWERED
        ),
        current_gate_field_count=len(current_gate_fields),
        current_gate_blocked_count=sum(
            1
            for item in current_gate_fields
            if item.action_state is PacketFieldActionState.BLOCKED
        ),
        current_gate_review_ready_count=sum(
            1
            for item in current_gate_fields
            if item.action_state is PacketFieldActionState.REVIEW_READY
        ),
        current_gate_answered_count=sum(
            1
            for item in current_gate_fields
            if item.action_state is PacketFieldActionState.ANSWERED
        ),
        approval_required_count=sum(1 for item in fields if item.approval_required),
        source_ref_count=sum(len(item.source_refs) for item in fields),
    )


def _review_state_for_field_decision(
    decision: OpportunityActivationFieldReviewDecisionType,
) -> OpportunityActivationReviewState:
    if decision in {
        OpportunityActivationFieldReviewDecisionType.ACCEPT,
        OpportunityActivationFieldReviewDecisionType.EDIT,
    }:
        return OpportunityActivationReviewState.ACCEPTED
    if decision is OpportunityActivationFieldReviewDecisionType.ROUTE:
        return OpportunityActivationReviewState.ROUTED
    return OpportunityActivationReviewState.DISCARDED


def _review_gate_for_field_decision(
    decision: OpportunityActivationFieldReviewDecisionType,
) -> str:
    return {
        OpportunityActivationFieldReviewDecisionType.ACCEPT: "human_accepted",
        OpportunityActivationFieldReviewDecisionType.EDIT: "human_edited",
        OpportunityActivationFieldReviewDecisionType.ROUTE: "human_routed",
        OpportunityActivationFieldReviewDecisionType.DISCARD: "human_discarded",
    }[decision]


def _answer_for_field(
    *,
    answers: tuple[PacketFieldAnswer, ...],
    opportunity_id: str,
    field_key: str,
) -> PacketFieldAnswer | None:
    for answer in answers:
        if answer.opportunity_id == opportunity_id and answer.field_key == field_key:
            return answer
    return None


def _action_state_for_answer(
    *,
    current_status: PacketFieldAnswerStatus,
    evidence_status: EvidenceStatus,
) -> PacketFieldActionState:
    if (
        current_status is PacketFieldAnswerStatus.ANSWERED
        and evidence_status
        in {EvidenceStatus.ANSWERED, EvidenceStatus.PARTIAL, EvidenceStatus.ASSUMPTION}
    ):
        return PacketFieldActionState.ANSWERED
    if current_status is PacketFieldAnswerStatus.NEEDS_REVIEW:
        return PacketFieldActionState.REVIEW_READY
    return PacketFieldActionState.BLOCKED


def _route_rationale(definition: PacketFieldDefinition) -> str:
    kinds = {path.kind for path in definition.answer_paths}
    if AnswerPathKind.CAPABILITY_MODULE in kinds:
        return "Capability-backed work can gather missing context, then return a reviewable field candidate."
    if AnswerPathKind.EVIDENCE_EXTRACTION in kinds:
        return "Source material can produce a traceable candidate before any packet answer changes."
    if AnswerPathKind.IMPORTED_DATA in kinds:
        return "Source-profile data should be loaded before synthesis or user judgment."
    if AnswerPathKind.MODEL_SYNTHESIS in kinds:
        return "Synthesis is useful only after accepted evidence or explicit assumptions exist."
    return "Ariadne cannot safely infer this field without capture lead or customer input."


def _approval_required(definition: PacketFieldDefinition) -> bool:
    return any(path.kind is AnswerPathKind.CAPABILITY_MODULE for path in definition.answer_paths)


def _output_from_action_item(
    item: PacketFieldActionItem,
) -> OpportunityActivationRunOutput:
    return OpportunityActivationRunOutput(
        output_id=f"actout_{item.field_key}",
        field_key=item.field_key,
        title=f"Advance {item.label}",
        summary=f"{item.label}: {item.recommended_route}",
        recommended_route=item.recommended_route,
    )


def _recommended_skill_chains(
    matrix: PacketFieldActionMatrix,
) -> tuple[str, ...]:
    chains: list[str] = []
    if any("source material" in item.recommended_route.lower() for item in matrix.fields):
        chains.append("source extraction -> packet field review")
    if any("source-profile" in item.recommended_route.lower() for item in matrix.fields):
        chains.append("source-profile lookup -> packet implication")
    if any("capability" in item.recommended_route.lower() for item in matrix.fields):
        chains.append("capability route -> reviewable packet candidate")
    if any("capture lead" in item.recommended_route.lower() for item in matrix.fields):
        chains.append("customer question -> call-plan prep")
    return tuple(chains)


def _approval_required_routes(
    matrix: PacketFieldActionMatrix,
) -> tuple[str, ...]:
    routes = tuple(
        f"{item.label}: approve capability-backed work before live collection or external research."
        for item in matrix.fields
        if item.approval_required
    )
    if routes:
        return routes
    return ("Review generated packet-field candidates before any trusted answer changes.",)


def _source_limitations(matrix: PacketFieldActionMatrix) -> tuple[str, ...]:
    limitations: list[str] = []
    if matrix.source_ref_count == 0:
        limitations.append("No accepted source evidence is attached to these fields yet.")
    if matrix.current_gate_blocked_count:
        limitations.append(
            f"{matrix.current_gate_blocked_count} current-gate packet fields still need evidence, import, synthesis, or user input."
        )
    return tuple(limitations)


def _next_best_actions(matrix: PacketFieldActionMatrix) -> tuple[str, ...]:
    blocked_fields = tuple(
        item for item in matrix.fields if item.action_state is PacketFieldActionState.BLOCKED
    )
    current_gate_blocked_fields = tuple(
        item for item in blocked_fields if item.current_gate_required
    )
    prioritized_fields = current_gate_blocked_fields or blocked_fields
    actions = tuple(
        f"Advance {item.label}: {item.recommended_route}"
        for item in prioritized_fields[:3]
    )
    if not actions:
        return ("Review field candidates and accept trusted packet answers.",)
    return actions + ("Review the Packet Field Action Matrix before trusted writes.",)


def _activation_run_id(
    *,
    opportunity_id: str,
    trigger: OpportunityActivationRunTrigger,
    matrix: PacketFieldActionMatrix,
) -> str:
    fingerprint = "|".join(
        f"{item.field_key}:{item.current_status}:{item.evidence_status}:{item.action_state}"
        for item in matrix.fields
    )
    digest = sha256(
        f"{opportunity_id}:{trigger.value}:{matrix.current_milestone_gate}:{fingerprint}".encode(
            "utf-8"
        )
    ).hexdigest()[:10]
    return f"actrun_{opportunity_id}_{trigger.value}_{digest}"