from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from ariadne.knowledge_vault import (
    _frontmatter_list,
    _read_frontmatter,
    _relative_markdown_path,
)
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


class PacketFieldRouteKind(StrEnum):
    SOURCE_BACKED_ANSWER = "source_backed_answer"
    RESEARCH_OR_MCP = "research_or_mcp"
    SOURCE_PROFILE_LOOKUP = "source_profile_lookup"
    MODEL_SYNTHESIS = "model_synthesis"
    CUSTOMER_CALL_PLAN = "customer_call_plan"


class OpportunityActivationCapabilityRouteStatus(StrEnum):
    APPROVAL_REQUIRED = "approval_required"
    SOURCE_LIMITED = "source_limited"
    DEPENDENCY_GATED = "dependency_gated"
    LIVE_PROVIDER_QUEUED = "live_provider_queued"
    EXECUTED = "executed"


class OpportunityActivationCapabilityRoute(BaseModel):
    route_id: str
    field_key: str
    capability_id: str
    capability_type: str
    status: OpportunityActivationCapabilityRouteStatus
    approval_required: bool = True
    approval_gate: str | None = None
    queued_reason: str | None = None
    source_limitations: tuple[str, ...] = ()
    review_destination: str = "Capability Run Output"
    fake_runner_supported: bool = True
    network_required: bool = False
    model_required: bool = False
    trusted_downstream_writes: bool = False
    invoked_run_id: str | None = None
    invoked_output_ids: tuple[str, ...] = ()
    provenance: dict[str, Any] = Field(default_factory=dict)


class PacketFieldVaultRouteContext(BaseModel):
    page_refs: tuple[str, ...]
    relationship_refs: tuple[str, ...]
    titles: tuple[str, ...]
    source_refs: tuple[str, ...] = ()


class OpportunityActivationDigest(BaseModel):
    coverage_gained: tuple[str, ...]
    review_ready_count: int
    blocked_field_count: int
    recommended_skill_chains: tuple[str, ...]
    approval_required_routes: tuple[str, ...]
    queued_approval_routes: tuple[str, ...] = ()
    invoked_routes: tuple[str, ...] = ()
    reviewable_outputs: tuple[str, ...] = ()
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
    route_kind: PacketFieldRouteKind = PacketFieldRouteKind.SOURCE_BACKED_ANSWER
    recommended_route: str
    route_rationale: str
    route_steps: tuple[str, ...] = ()
    approval_gate: str | None = None
    requires_review: bool = True
    approval_required: bool = False
    source_refs: tuple[str, ...] = ()
    vault_context_refs: tuple[str, ...] = ()
    vault_relationship_refs: tuple[str, ...] = ()
    capability_routes: tuple[OpportunityActivationCapabilityRoute, ...] = ()
    gap_summary: str | None = None
    current_value: str | None = None

    @model_validator(mode="after")
    def hydrate_route_metadata(self) -> PacketFieldActionItem:
        inferred_route_kind = _route_kind_from_recommended_route(self.recommended_route)
        if (
            self.route_kind is PacketFieldRouteKind.SOURCE_BACKED_ANSWER
            and inferred_route_kind is not PacketFieldRouteKind.SOURCE_BACKED_ANSWER
        ):
            self.route_kind = inferred_route_kind
        if not self.route_steps:
            self.route_steps = _route_steps_from_labels(
                route_kind=self.route_kind,
                answer_path_labels=self.answer_paths,
            )
        if self.approval_gate is None:
            self.approval_gate = _approval_gate_for_route_kind(
                route_kind=self.route_kind,
                approval_required=self.approval_required,
            )
        return self


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
    provenance: dict[str, object] = Field(default_factory=dict)


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
    vault_root: Path | str | None = None,
    capability_run_store: Any | None = None,
    approved_capability_route_ids: tuple[str, ...] = (),
    capability_route_inputs: dict[str, object] | None = None,
) -> OpportunityActivationRun:
    milestone_gate = _coerce_milestone_gate(current_milestone_gate)
    completed_at = created_at or datetime.now(UTC)
    matrix = build_packet_field_action_matrix(
        opportunity_id=opportunity_id,
        definitions=definitions,
        answers=answers,
        current_milestone_gate=milestone_gate,
        vault_root=vault_root,
    )
    matrix = _matrix_with_activation_capability_route_status(
        matrix=matrix,
        opportunity_id=opportunity_id,
        capability_run_store=capability_run_store,
        approved_capability_route_ids=approved_capability_route_ids,
        capability_route_inputs=capability_route_inputs or {},
    )
    capability_routes = _capability_routes(matrix)
    digest = build_activation_digest(
        matrix=matrix,
        initial_coverage=initial_coverage,
        capability_routes=capability_routes,
    )
    outputs = tuple(
        _output_from_action_item(item)
        for item in matrix.fields
        if item.action_state is not PacketFieldActionState.ANSWERED
    ) + tuple(
        _output_from_capability_route(route)
        for route in capability_routes
        if route.status is OpportunityActivationCapabilityRouteStatus.EXECUTED
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
            "activation_capability_routes": [
                route.model_dump(mode="json") for route in capability_routes
            ],
            "invoked_capability_run_ids": [
                route.invoked_run_id
                for route in capability_routes
                if route.invoked_run_id is not None
            ],
            "queued_capability_routes": [
                route.model_dump(mode="json")
                for route in capability_routes
                if route.status is not OpportunityActivationCapabilityRouteStatus.EXECUTED
            ],
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
    vault_root: Path | str | None = None,
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
            vault_root=vault_root,
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
            1
            for item in actions
            if item.action_state is PacketFieldActionState.ANSWERED
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
    capability_routes: tuple[OpportunityActivationCapabilityRoute, ...] = (),
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
    invoked_routes = _invoked_route_summaries(capability_routes)
    queued_routes = _queued_route_summaries(capability_routes)
    reviewable_outputs = _reviewable_route_output_summaries(capability_routes)
    if invoked_routes:
        coverage += (f"Invoked {len(invoked_routes)} approved low-risk route(s).",)
    if queued_routes:
        coverage += (f"Queued {len(queued_routes)} capability route(s) for approval or missing inputs.",)
    return OpportunityActivationDigest(
        coverage_gained=coverage,
        review_ready_count=matrix.review_ready_count,
        blocked_field_count=matrix.blocked_field_count,
        recommended_skill_chains=_recommended_skill_chains(matrix),
        approval_required_routes=_approval_required_routes(matrix),
        queued_approval_routes=queued_routes,
        invoked_routes=invoked_routes,
        reviewable_outputs=reviewable_outputs,
        source_limitations=_source_limitations(
            matrix,
            capability_routes=capability_routes,
        ),
        next_best_actions=_next_best_actions(matrix),
    )


def recommend_packet_field_route(definition: PacketFieldDefinition) -> str:
    route_kind = recommend_packet_field_route_kind(definition)
    return {
        PacketFieldRouteKind.RESEARCH_OR_MCP: (
            "Recommend a capability or skill-backed research route."
        ),
        PacketFieldRouteKind.SOURCE_BACKED_ANSWER: (
            "Inspect source material and extract a reviewable answer candidate."
        ),
        PacketFieldRouteKind.SOURCE_PROFILE_LOOKUP: (
            "Import or lookup source-profile data before synthesis."
        ),
        PacketFieldRouteKind.MODEL_SYNTHESIS: (
            "Synthesize a reviewable answer from accepted evidence and gaps."
        ),
        PacketFieldRouteKind.CUSTOMER_CALL_PLAN: (
            "Prepare a customer call-plan question set before treating this field as answered."
        ),
    }[route_kind]


def recommend_packet_field_route_kind(
    definition: PacketFieldDefinition,
) -> PacketFieldRouteKind:
    kinds = {path.kind for path in definition.answer_paths}
    if AnswerPathKind.CAPABILITY_MODULE in kinds:
        return PacketFieldRouteKind.RESEARCH_OR_MCP
    if AnswerPathKind.EVIDENCE_EXTRACTION in kinds:
        return PacketFieldRouteKind.SOURCE_BACKED_ANSWER
    if AnswerPathKind.IMPORTED_DATA in kinds:
        return PacketFieldRouteKind.SOURCE_PROFILE_LOOKUP
    if AnswerPathKind.MODEL_SYNTHESIS in kinds:
        return PacketFieldRouteKind.MODEL_SYNTHESIS
    return PacketFieldRouteKind.CUSTOMER_CALL_PLAN


def _action_item_for_definition(
    *,
    opportunity_id: str,
    definition: PacketFieldDefinition,
    current_milestone_gate: MilestoneGate,
    answer: PacketFieldAnswer | None,
    vault_root: Path | str | None = None,
) -> PacketFieldActionItem:
    current_status = (
        answer.status if answer is not None else PacketFieldAnswerStatus.UNANSWERED
    )
    evidence_status = (
        answer.evidence_status if answer is not None else EvidenceStatus.GAP
    )
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
    vault_context = _vault_route_context_for_definition(
        vault_root=vault_root,
        definition=definition,
    )
    route_kind = recommend_packet_field_route_kind(definition)
    approval_required = _approval_required(definition)
    route_rationale = _route_rationale(definition)
    route_steps = _route_steps(definition)
    if vault_context is not None:
        route_rationale = _route_rationale_with_vault_context(
            route_rationale,
            vault_context,
        )
        route_steps = route_steps + (
            "Review vault context pages before route execution: "
            + ", ".join(vault_context.page_refs),
        )

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
        route_kind=route_kind,
        recommended_route=recommend_packet_field_route(definition),
        route_rationale=route_rationale,
        route_steps=route_steps,
        approval_gate=_approval_gate(definition),
        requires_review=action_state is not PacketFieldActionState.ANSWERED,
        approval_required=approval_required,
        source_refs=answer.evidence_ids if answer is not None else (),
        vault_context_refs=(
            vault_context.page_refs if vault_context is not None else ()
        ),
        vault_relationship_refs=(
            vault_context.relationship_refs if vault_context is not None else ()
        ),
        capability_routes=_capability_routes_for_definition(
            definition=definition,
            route_kind=route_kind,
            approval_required=approval_required,
        ),
        gap_summary=gap_summary,
        current_value=answer.value if answer is not None else None,
    )


def _vault_route_context_for_definition(
    *,
    vault_root: Path | str | None,
    definition: PacketFieldDefinition,
) -> PacketFieldVaultRouteContext | None:
    if vault_root is None:
        return None
    root = Path(vault_root)
    if not root.is_dir():
        return None

    field_targets = (
        f"data-elements/briefing-packet/{definition.key}",
        f"data-elements/{definition.key}",
    )
    field_page_path = (
        root / "data-elements" / "briefing-packet" / f"{definition.key}.md"
    )
    legacy_field_page_path = root / "data-elements" / f"{definition.key}.md"
    candidate_paths: list[Path] = []
    if field_page_path.is_file():
        candidate_paths.append(field_page_path)
    elif legacy_field_page_path.is_file():
        candidate_paths.append(legacy_field_page_path)

    for page_path in sorted(root.rglob("*.md")):
        if page_path in {field_page_path, legacy_field_page_path}:
            continue
        if (
            _relative_markdown_path(root, page_path)
            == "data-elements/dictionary-index.md"
        ):
            continue
        frontmatter = _read_frontmatter(page_path)
        if frontmatter is None:
            continue
        relationships = _frontmatter_list(frontmatter.get("relationships"))
        if any(
            _relationship_targets_data_element(relationship, field_targets)
            for relationship in relationships
        ):
            candidate_paths.append(page_path)

    page_refs: list[str] = []
    relationship_refs: list[str] = []
    titles: list[str] = []
    source_refs: list[str] = []
    for page_path in candidate_paths:
        frontmatter = _read_frontmatter(page_path)
        if frontmatter is None:
            continue
        relationships = _frontmatter_list(frontmatter.get("relationships"))
        matching_relationships = tuple(
            relationship
            for relationship in relationships
            if _relationship_targets_data_element(relationship, field_targets)
            or relationship.startswith("suggests_route:")
            or relationship.startswith("uses_capability:")
            or relationship.startswith("uses_source_provider:")
        )
        if page_path in {field_page_path, legacy_field_page_path}:
            matching_relationships = relationships
        if page_path != field_page_path and not matching_relationships:
            continue

        page_refs.append(_relative_markdown_path(root, page_path))
        relationship_refs.extend(matching_relationships)
        title = str(frontmatter.get("title", "")).strip()
        if title:
            titles.append(title)
        source_refs.extend(_frontmatter_list(frontmatter.get("source_refs")))

    if not page_refs:
        return None
    return PacketFieldVaultRouteContext(
        page_refs=tuple(dict.fromkeys(page_refs)),
        relationship_refs=tuple(dict.fromkeys(relationship_refs)),
        titles=tuple(dict.fromkeys(titles)),
        source_refs=tuple(dict.fromkeys(source_refs)),
    )


def _route_rationale_with_vault_context(
    base_rationale: str,
    vault_context: PacketFieldVaultRouteContext,
) -> str:
    title_context = ", ".join(vault_context.titles[:3])
    relationship_context = ", ".join(vault_context.relationship_refs[:4])
    page_context = ", ".join(vault_context.page_refs[:3])
    return (
        f"{base_rationale} Vault context: {title_context or page_context} "
        f"cites typed relationships {relationship_context or 'none'}; use it as "
        "route guidance only until a human review accepts a packet answer."
    )


def _relationship_targets_data_element(
    relationship: str,
    field_targets: tuple[str, ...],
) -> bool:
    if ":" not in relationship:
        return False
    _relationship_kind, target = relationship.split(":", 1)
    return _normalize_relationship_target(target) in field_targets


def _normalize_relationship_target(target: str) -> str:
    normalized = target.strip().strip('"').strip("'")
    if normalized.startswith("[[") and normalized.endswith("]]"):
        normalized = normalized[2:-2].split("|", 1)[0].strip()
    if normalized.endswith(".md"):
        normalized = normalized[:-3]
    return normalized.lstrip("/")


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
        EvidenceStatus.ANSWERED if request.evidence_ids else EvidenceStatus.ASSUMPTION
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
    if current_status is PacketFieldAnswerStatus.ANSWERED and evidence_status in {
        EvidenceStatus.ANSWERED,
        EvidenceStatus.PARTIAL,
        EvidenceStatus.ASSUMPTION,
    }:
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
    return (
        "Ariadne cannot safely infer this field without capture lead or customer input."
    )


def _route_steps(definition: PacketFieldDefinition) -> tuple[str, ...]:
    route_kind = recommend_packet_field_route_kind(definition)
    if route_kind is PacketFieldRouteKind.RESEARCH_OR_MCP:
        steps = (
            "Approve capability-backed research route.",
            _route_step_for_labels(
                prefix="Use",
                labels=_answer_path_labels(
                    definition, AnswerPathKind.CAPABILITY_MODULE
                ),
                fallback="available research capability",
            ),
        )
        human_labels = _answer_path_labels(definition, AnswerPathKind.HUMAN_INPUT)
        if human_labels:
            steps += (
                _route_step_for_labels(
                    prefix="Cross-check with",
                    labels=human_labels,
                    fallback="capture lead input",
                ),
            )
        return steps + ("Review packet candidate before trusted use.",)
    if route_kind is PacketFieldRouteKind.SOURCE_PROFILE_LOOKUP:
        return (
            _route_step_for_labels(
                prefix="Lookup",
                labels=_answer_path_labels(definition, AnswerPathKind.IMPORTED_DATA),
                fallback="source-profile or imported data",
            ),
            "Review packet implication before trusted use.",
        )
    if route_kind is PacketFieldRouteKind.MODEL_SYNTHESIS:
        return (
            "Collect accepted evidence or explicit assumptions.",
            _route_step_for_labels(
                prefix="Prepare",
                labels=_answer_path_labels(definition, AnswerPathKind.MODEL_SYNTHESIS),
                fallback="local synthesis candidate",
            ),
            "Review synthesized answer before trusted use.",
        )
    if route_kind is PacketFieldRouteKind.CUSTOMER_CALL_PLAN:
        return (
            _route_step_for_labels(
                prefix="Prepare",
                labels=_answer_path_labels(definition, AnswerPathKind.HUMAN_INPUT),
                fallback="capture lead or customer question",
            ),
            "Route the answer back through packet-field review.",
        )
    steps = (
        _route_step_for_labels(
            prefix="Extract from",
            labels=_answer_path_labels(definition, AnswerPathKind.EVIDENCE_EXTRACTION),
            fallback="source material",
        ),
    )
    context_labels = _answer_path_labels(
        definition, AnswerPathKind.HUMAN_INPUT
    ) + _answer_path_labels(
        definition,
        AnswerPathKind.IMPORTED_DATA,
    )
    if context_labels:
        steps += (
            _route_step_for_labels(
                prefix="Cross-check with",
                labels=context_labels,
                fallback="operator or imported context",
            ),
        )
    return steps + ("Review packet candidate before trusted use.",)


def _approval_gate(definition: PacketFieldDefinition) -> str | None:
    return _approval_gate_for_route_kind(
        route_kind=recommend_packet_field_route_kind(definition),
        approval_required=_approval_required(definition),
    )


def _approval_gate_for_route_kind(
    *,
    route_kind: PacketFieldRouteKind,
    approval_required: bool,
) -> str | None:
    if approval_required:
        return (
            "Operator approval required before capability-backed or external research."
        )
    if route_kind is PacketFieldRouteKind.MODEL_SYNTHESIS:
        return (
            "Human review required before synthesized content becomes a trusted answer."
        )
    return None


def _answer_path_labels(
    definition: PacketFieldDefinition,
    kind: AnswerPathKind,
) -> tuple[str, ...]:
    return tuple(path.label for path in definition.answer_paths if path.kind is kind)


def _route_step_for_labels(
    *,
    prefix: str,
    labels: tuple[str, ...],
    fallback: str,
) -> str:
    target = ", ".join(labels) if labels else fallback
    return f"{prefix} {target}."


def _route_kind_from_recommended_route(route: str) -> PacketFieldRouteKind:
    normalized_route = route.lower()
    if "capability" in normalized_route or "research" in normalized_route:
        return PacketFieldRouteKind.RESEARCH_OR_MCP
    if "source-profile" in normalized_route or "import or lookup" in normalized_route:
        return PacketFieldRouteKind.SOURCE_PROFILE_LOOKUP
    if "synthesize" in normalized_route:
        return PacketFieldRouteKind.MODEL_SYNTHESIS
    if "call-plan" in normalized_route or "customer call" in normalized_route:
        return PacketFieldRouteKind.CUSTOMER_CALL_PLAN
    return PacketFieldRouteKind.SOURCE_BACKED_ANSWER


def _route_steps_from_labels(
    *,
    route_kind: PacketFieldRouteKind,
    answer_path_labels: tuple[str, ...],
) -> tuple[str, ...]:
    if route_kind is PacketFieldRouteKind.RESEARCH_OR_MCP:
        capability_labels = _labels_matching(answer_path_labels, ("capability",))
        human_labels = tuple(
            label for label in answer_path_labels if label not in capability_labels
        )
        steps = (
            "Approve capability-backed research route.",
            _route_step_for_labels(
                prefix="Use",
                labels=capability_labels,
                fallback="available research capability",
            ),
        )
        if human_labels:
            steps += (
                _route_step_for_labels(
                    prefix="Cross-check with",
                    labels=human_labels,
                    fallback="capture lead input",
                ),
            )
        return steps + ("Review packet candidate before trusted use.",)
    if route_kind is PacketFieldRouteKind.SOURCE_PROFILE_LOOKUP:
        return (
            _route_step_for_labels(
                prefix="Lookup",
                labels=_labels_matching(
                    answer_path_labels,
                    ("import", "crm", "contract", "feed", "award"),
                ),
                fallback="source-profile or imported data",
            ),
            "Review packet implication before trusted use.",
        )
    if route_kind is PacketFieldRouteKind.MODEL_SYNTHESIS:
        return (
            "Collect accepted evidence or explicit assumptions.",
            _route_step_for_labels(
                prefix="Prepare",
                labels=_labels_matching(answer_path_labels, ("synthesis", "rationale")),
                fallback="local synthesis candidate",
            ),
            "Review synthesized answer before trusted use.",
        )
    if route_kind is PacketFieldRouteKind.CUSTOMER_CALL_PLAN:
        return (
            _route_step_for_labels(
                prefix="Prepare",
                labels=answer_path_labels,
                fallback="capture lead or customer question",
            ),
            "Route the answer back through packet-field review.",
        )
    evidence_labels = _labels_matching(
        answer_path_labels,
        ("extraction", "notice", "source", "sow", "pws", "section"),
    )
    context_labels = tuple(
        label for label in answer_path_labels if label not in evidence_labels
    )
    steps = (
        _route_step_for_labels(
            prefix="Extract from",
            labels=evidence_labels,
            fallback="source material",
        ),
    )
    if context_labels:
        steps += (
            _route_step_for_labels(
                prefix="Cross-check with",
                labels=context_labels,
                fallback="operator or imported context",
            ),
        )
    return steps + ("Review packet candidate before trusted use.",)


def _labels_matching(
    labels: tuple[str, ...],
    needles: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        label for label in labels if any(needle in label.lower() for needle in needles)
    )


def _approval_required(definition: PacketFieldDefinition) -> bool:
    return any(
        path.kind is AnswerPathKind.CAPABILITY_MODULE
        for path in definition.answer_paths
    )


def _capability_routes_for_definition(
    *,
    definition: PacketFieldDefinition,
    route_kind: PacketFieldRouteKind,
    approval_required: bool,
) -> tuple[OpportunityActivationCapabilityRoute, ...]:
    route_specs = {
        PacketFieldRouteKind.RESEARCH_OR_MCP: {
            "suffix": "data_table_profile_next_route_chain",
            "capability_id": "data-table-profile-next-route-chain",
            "capability_type": "skill_chain",
            "status": OpportunityActivationCapabilityRouteStatus.APPROVAL_REQUIRED,
            "approval_required": approval_required,
            "approval_gate": "Operator approval required before activation invokes this chain.",
            "queued_reason": "Approval required before activation can invoke this capability route.",
            "review_destination": "Capability Run Output",
            "network_required": False,
            "model_required": False,
            "execution_mode": "deterministic_plan_map",
        },
        PacketFieldRouteKind.SOURCE_BACKED_ANSWER: {
            "suffix": "source_backed_answer_review",
            "capability_id": "document-intake-source-backed-answer",
            "capability_type": "adapter",
            "status": OpportunityActivationCapabilityRouteStatus.SOURCE_LIMITED,
            "approval_required": False,
            "approval_gate": None,
            "queued_reason": "Source material or extraction bundle required before source-backed answer route.",
            "review_destination": "Packet Field Answer candidate",
            "network_required": False,
            "model_required": False,
            "execution_mode": "source_backed_review_route",
        },
        PacketFieldRouteKind.SOURCE_PROFILE_LOOKUP: {
            "suffix": "source_profile_lookup",
            "capability_id": "source-profile-lookup-route",
            "capability_type": "source_profile_route",
            "status": OpportunityActivationCapabilityRouteStatus.SOURCE_LIMITED,
            "approval_required": False,
            "approval_gate": None,
            "queued_reason": "Source-profile ref or imported data required before packet implication route.",
            "review_destination": "Packet Field Answer candidate",
            "network_required": False,
            "model_required": False,
            "execution_mode": "source_profile_route",
        },
        PacketFieldRouteKind.MODEL_SYNTHESIS: {
            "suffix": "hosted_packet_synthesis",
            "capability_id": "hosted-packet-synthesis-model",
            "capability_type": "model_workflow",
            "status": OpportunityActivationCapabilityRouteStatus.APPROVAL_REQUIRED,
            "approval_required": True,
            "approval_gate": "Operator approval required before hosted model synthesis.",
            "queued_reason": "Approval and accepted evidence or explicit assumptions required before model synthesis.",
            "review_destination": "Packet Field Answer candidate",
            "network_required": True,
            "model_required": True,
            "execution_mode": "hosted_model_review_route",
        },
        PacketFieldRouteKind.CUSTOMER_CALL_PLAN: {
            "suffix": "call_plan_question_prep",
            "capability_id": "call-plan-question-prep",
            "capability_type": "model_workflow",
            "status": OpportunityActivationCapabilityRouteStatus.APPROVAL_REQUIRED,
            "approval_required": True,
            "approval_gate": "Operator approval required before call-plan draft support.",
            "queued_reason": "Approval and customer/stakeholder context required before call-plan prep.",
            "review_destination": "Call Plan signal",
            "network_required": False,
            "model_required": True,
            "execution_mode": "local_or_hosted_model_review_route",
        },
    }
    spec = route_specs[route_kind]
    limitation = spec["queued_reason"] if spec["status"] is OpportunityActivationCapabilityRouteStatus.SOURCE_LIMITED else None
    return (
        OpportunityActivationCapabilityRoute(
            route_id=f"actroute_{definition.key}_{spec['suffix']}",
            field_key=definition.key,
            capability_id=str(spec["capability_id"]),
            capability_type=str(spec["capability_type"]),
            status=spec["status"],
            approval_required=bool(spec["approval_required"]),
            approval_gate=spec["approval_gate"],
            queued_reason=spec["queued_reason"],
            source_limitations=(str(limitation),) if limitation else (),
            review_destination=str(spec["review_destination"]),
            fake_runner_supported=True,
            network_required=bool(spec["network_required"]),
            model_required=bool(spec["model_required"]),
            trusted_downstream_writes=False,
            provenance={
                "route_family": "packet_field_action_matrix",
                "route_kind": route_kind.value,
                "low_risk_when_approved": route_kind is PacketFieldRouteKind.RESEARCH_OR_MCP,
                "execution_mode": spec["execution_mode"],
            },
        ),
    )


def _matrix_with_activation_capability_route_status(
    *,
    matrix: PacketFieldActionMatrix,
    opportunity_id: str,
    capability_run_store: Any | None,
    approved_capability_route_ids: tuple[str, ...],
    capability_route_inputs: dict[str, object],
) -> PacketFieldActionMatrix:
    if not any(item.capability_routes for item in matrix.fields):
        return matrix
    approved_routes = set(approved_capability_route_ids)
    updated_fields = tuple(
        item.model_copy(
            update={
                "capability_routes": tuple(
                    _activation_capability_route_after_policy(
                        route=route,
                        opportunity_id=opportunity_id,
                        capability_run_store=capability_run_store,
                        approved_routes=approved_routes,
                        capability_route_inputs=capability_route_inputs,
                    )
                    for route in item.capability_routes
                )
            }
        )
        if item.capability_routes
        else item
        for item in matrix.fields
    )
    return _matrix_with_fields(
        opportunity_id=matrix.opportunity_id,
        current_milestone_gate=matrix.current_milestone_gate,
        fields=updated_fields,
    )


def _activation_capability_route_after_policy(
    *,
    route: OpportunityActivationCapabilityRoute,
    opportunity_id: str,
    capability_run_store: Any | None,
    approved_routes: set[str],
    capability_route_inputs: dict[str, object],
) -> OpportunityActivationCapabilityRoute:
    if route.route_id not in approved_routes:
        return route
    if capability_run_store is None:
        return _source_limited_route(
            route,
            "Capability Run Store is required before activation can invoke this route.",
        )
    input_payload = capability_route_inputs.get(route.route_id)
    if input_payload is None:
        return _source_limited_route(
            route,
            _missing_input_limitation(route),
        )
    if route.capability_id != "data-table-profile-next-route-chain":
        return route.model_copy(
            update={
                "status": OpportunityActivationCapabilityRouteStatus.DEPENDENCY_GATED,
                "queued_reason": "Capability route has no MVP-2 activation runner yet.",
            }
        )
    return _execute_data_table_profile_chain_route(
        route=route,
        opportunity_id=opportunity_id,
        capability_run_store=capability_run_store,
        input_payload=input_payload,
    )


def _missing_input_limitation(route: OpportunityActivationCapabilityRoute) -> str:
    if route.capability_id == "data-table-profile-next-route-chain":
        return "Approved chain route lacks required data-table profile inputs."
    if route.capability_type == "model_workflow":
        return "Approved model route lacks accepted evidence, assumptions, or prompt input."
    if route.capability_type == "source_profile_route":
        return "Approved source-profile route lacks required source-profile ref."
    return "Approved capability route lacks required inputs."


def _source_limited_route(
    route: OpportunityActivationCapabilityRoute,
    limitation: str,
) -> OpportunityActivationCapabilityRoute:
    return route.model_copy(
        update={
            "status": OpportunityActivationCapabilityRouteStatus.SOURCE_LIMITED,
            "queued_reason": limitation,
            "source_limitations": (limitation,),
        }
    )


def _execute_data_table_profile_chain_route(
    *,
    route: OpportunityActivationCapabilityRoute,
    opportunity_id: str,
    capability_run_store: Any,
    input_payload: object,
) -> OpportunityActivationCapabilityRoute:
    from ariadne.data_table_profiler import DataTableProfileRequest
    from ariadne.thin_orchestration_chains import run_data_table_profile_next_route_chain

    request = (
        input_payload
        if isinstance(input_payload, DataTableProfileRequest)
        else DataTableProfileRequest.model_validate(input_payload)
    )
    capability_run = run_data_table_profile_next_route_chain(
        request=request,
        store=capability_run_store,
        opportunity_id=opportunity_id,
        approval_basis=f"activation_approved:{route.route_id}",
    )
    return route.model_copy(
        update={
            "status": OpportunityActivationCapabilityRouteStatus.EXECUTED,
            "queued_reason": None,
            "invoked_run_id": capability_run.run_id,
            "invoked_output_ids": tuple(
                output.output_id for output in capability_run.outputs
            ),
            "review_destination": "Capability Run Output",
            "provenance": {
                **route.provenance,
                "capability_run_id": capability_run.run_id,
                "capability_output_ids": [
                    output.output_id for output in capability_run.outputs
                ],
                "network_required": False,
                "model_required": False,
                "trusted_downstream_writes": False,
            },
        }
    )


def _capability_routes(
    matrix: PacketFieldActionMatrix,
) -> tuple[OpportunityActivationCapabilityRoute, ...]:
    return tuple(
        route
        for item in matrix.fields
        for route in item.capability_routes
    )


def _output_from_action_item(
    item: PacketFieldActionItem,
) -> OpportunityActivationRunOutput:
    return OpportunityActivationRunOutput(
        output_id=f"actout_{item.field_key}",
        field_key=item.field_key,
        title=f"Advance {item.label}",
        summary=f"{item.label}: {item.recommended_route}",
        recommended_route=item.recommended_route,
        provenance={
            "route_kind": item.route_kind.value,
            "approval_required": item.approval_required,
            "capability_route_ids": [
                route.route_id for route in item.capability_routes
            ],
            "trusted_downstream_writes": False,
        },
    )


def _output_from_capability_route(
    route: OpportunityActivationCapabilityRoute,
) -> OpportunityActivationRunOutput:
    return OpportunityActivationRunOutput(
        output_id=f"actout_capability_{route.route_id}",
        field_key=route.field_key,
        title=f"Review {route.capability_id}",
        summary=(
            f"Activation invoked {route.capability_id}; review Capability Run Output "
            "before any trusted workflow use."
        ),
        recommended_destination=route.review_destination,
        recommended_route=f"Review capability run {route.invoked_run_id}.",
        provenance={
            "route_id": route.route_id,
            "capability_id": route.capability_id,
            "capability_run_id": route.invoked_run_id,
            "capability_output_ids": list(route.invoked_output_ids),
            "trusted_downstream_writes": False,
        },
    )


def _recommended_skill_chains(
    matrix: PacketFieldActionMatrix,
) -> tuple[str, ...]:
    chains: list[str] = []
    if any(
        "source material" in item.recommended_route.lower() for item in matrix.fields
    ):
        chains.append("source extraction -> packet field review")
    if any(
        "source-profile" in item.recommended_route.lower() for item in matrix.fields
    ):
        chains.append("source-profile lookup -> packet implication")
    if any("capability" in item.recommended_route.lower() for item in matrix.fields):
        chains.append("capability route -> reviewable packet candidate")
    if any("capture lead" in item.recommended_route.lower() for item in matrix.fields):
        chains.append("customer question -> call-plan prep")
    return tuple(chains)


def _approval_required_routes(
    matrix: PacketFieldActionMatrix,
) -> tuple[str, ...]:
    field_routes = tuple(
        f"{item.label}: approve capability-backed work before live collection or external research."
        for item in matrix.fields
        if item.approval_required
    )
    capability_routes = tuple(
        f"{item.label}: approve {route.capability_id} before route execution."
        for item in matrix.fields
        for route in item.capability_routes
        if route.approval_required
    )
    routes = tuple(dict.fromkeys((*field_routes, *capability_routes)))
    if routes:
        return routes
    return (
        "Review generated packet-field candidates before any trusted answer changes.",
    )


def _invoked_route_summaries(
    capability_routes: tuple[OpportunityActivationCapabilityRoute, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{route.route_id}: invoked {route.capability_id} as {route.invoked_run_id}."
        for route in capability_routes
        if route.status is OpportunityActivationCapabilityRouteStatus.EXECUTED
    )


def _queued_route_summaries(
    capability_routes: tuple[OpportunityActivationCapabilityRoute, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{route.route_id}: {route.queued_reason or route.status.value}."
        for route in capability_routes
        if route.status is not OpportunityActivationCapabilityRouteStatus.EXECUTED
    )


def _reviewable_route_output_summaries(
    capability_routes: tuple[OpportunityActivationCapabilityRoute, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{route.route_id}: {output_id} pending in {route.review_destination}."
        for route in capability_routes
        if route.status is OpportunityActivationCapabilityRouteStatus.EXECUTED
        for output_id in route.invoked_output_ids
    )


def _source_limitations(
    matrix: PacketFieldActionMatrix,
    *,
    capability_routes: tuple[OpportunityActivationCapabilityRoute, ...] = (),
) -> tuple[str, ...]:
    limitations: list[str] = []
    if matrix.source_ref_count == 0:
        limitations.append(
            "No accepted source evidence is attached to these fields yet."
        )
    if matrix.current_gate_blocked_count:
        limitations.append(
            f"{matrix.current_gate_blocked_count} current-gate packet fields still need evidence, import, synthesis, or user input."
        )
    limitations.extend(
        limitation
        for route in capability_routes
        for limitation in route.source_limitations
    )
    return tuple(limitations)


def _next_best_actions(matrix: PacketFieldActionMatrix) -> tuple[str, ...]:
    blocked_fields = tuple(
        item
        for item in matrix.fields
        if item.action_state is PacketFieldActionState.BLOCKED
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
