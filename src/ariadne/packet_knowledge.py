from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, computed_field

from ariadne.packets import CanonicalPacketSection, EvidenceStatus


class PacketFieldValueKind(StrEnum):
    TEXT = "text"
    PROSE = "prose"
    ENTITY = "entity"
    ENTITY_LIST = "entity_list"
    DATE = "date"
    MONEY = "money"
    PERCENTAGE = "percentage"
    DECISION = "decision"


class PacketFieldAnswerStatus(StrEnum):
    UNANSWERED = "unanswered"
    ANSWERED = "answered"
    NEEDS_REVIEW = "needs_review"
    GAP = "gap"
    ASSUMPTION = "assumption"


class AnswerPathKind(StrEnum):
    HUMAN_INPUT = "human_input"
    IMPORTED_DATA = "imported_data"
    EVIDENCE_EXTRACTION = "evidence_extraction"
    MODEL_SYNTHESIS = "model_synthesis"
    CAPABILITY_MODULE = "capability_module"


class KnowledgeAuthority(StrEnum):
    ARIADNE_SOURCE_OF_TRUTH = "ariadne_source_of_truth"
    KNOWLEDGE_MIRROR_PROJECTION = "knowledge_mirror_projection"


class KnowledgeEntityKind(StrEnum):
    CUSTOMER = "customer"
    AGENCY = "agency"
    COMPETITOR = "competitor"
    INCUMBENT = "incumbent"
    CONTRACT_VEHICLE = "contract_vehicle"
    CONTRACT_TYPE = "contract_type"
    SCOPE_AREA = "scope_area"
    EVALUATION_METHOD = "evaluation_method"
    SOURCE_DOCUMENT = "source_document"
    REUSABLE_INSIGHT = "reusable_insight"
    CAPTURE_PATTERN = "capture_pattern"


class AnswerPath(BaseModel):
    kind: AnswerPathKind
    label: str
    capability_id: str | None = None


class PacketFieldDefinition(BaseModel):
    key: str
    label: str
    question: str
    section: CanonicalPacketSection
    value_kind: PacketFieldValueKind
    answer_paths: tuple[AnswerPath, ...] = ()
    related_entity_kinds: tuple[KnowledgeEntityKind, ...] = ()
    authority: KnowledgeAuthority = KnowledgeAuthority.ARIADNE_SOURCE_OF_TRUTH


class SharedKnowledgeEntity(BaseModel):
    id: str
    kind: KnowledgeEntityKind
    label: str
    authority: KnowledgeAuthority = KnowledgeAuthority.ARIADNE_SOURCE_OF_TRUTH
    source_ref: str | None = None

    @computed_field
    @property
    def is_source_of_truth(self) -> bool:
        return self.authority is KnowledgeAuthority.ARIADNE_SOURCE_OF_TRUTH


class PacketFieldAnswer(BaseModel):
    field_key: str
    opportunity_id: str
    value: str | None = None
    status: PacketFieldAnswerStatus = PacketFieldAnswerStatus.UNANSWERED
    evidence_status: EvidenceStatus = EvidenceStatus.GAP
    evidence_ids: tuple[str, ...] = ()
    assumption: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    gap_summary: str | None = None
    action_item_ids: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    provenance_note: str | None = None
    authority: KnowledgeAuthority = KnowledgeAuthority.ARIADNE_SOURCE_OF_TRUTH


class PacketFieldConnection(BaseModel):
    opportunity_id: str
    field_key: str
    value: str | None = None
    shared_entity_id: str
    shared_entity_label: str
    shared_entity_kind: KnowledgeEntityKind
    validity_scope: str = "opportunity_specific"


class PacketFieldReviewItem(BaseModel):
    field_key: str
    label: str
    question: str
    answer: PacketFieldAnswer | None = None
    answer_paths: tuple[AnswerPath, ...]
    connections: tuple[PacketFieldConnection, ...]
    scope_note: str = "Connections are context only; each answer remains valid only for its own Opportunity."


class PacketFieldReview(BaseModel):
    opportunity_id: str
    items: tuple[PacketFieldReviewItem, ...]
    authority: KnowledgeAuthority = KnowledgeAuthority.ARIADNE_SOURCE_OF_TRUTH


def build_default_packet_field_definitions() -> tuple[PacketFieldDefinition, ...]:
    return (
        PacketFieldDefinition(
            key="customer",
            label="Customer",
            question="Which customer or buying command owns the need?",
            section=CanonicalPacketSection.CUSTOMER_CONTEXT,
            value_kind=PacketFieldValueKind.ENTITY,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.HUMAN_INPUT, label="capture lead confirmation"
                ),
                AnswerPath(
                    kind=AnswerPathKind.IMPORTED_DATA, label="CRM or opportunity import"
                ),
                AnswerPath(
                    kind=AnswerPathKind.EVIDENCE_EXTRACTION,
                    label="notice or call-note extraction",
                ),
            ),
            related_entity_kinds=(
                KnowledgeEntityKind.CUSTOMER,
                KnowledgeEntityKind.AGENCY,
            ),
        ),
        PacketFieldDefinition(
            key="prime_name",
            label="Prime Name",
            question="Who is expected to prime the pursuit or contract?",
            section=CanonicalPacketSection.OPPORTUNITY_OVERVIEW,
            value_kind=PacketFieldValueKind.ENTITY,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.HUMAN_INPUT, label="capture lead confirmation"
                ),
                AnswerPath(
                    kind=AnswerPathKind.IMPORTED_DATA, label="CRM or contract import"
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.INCUMBENT,),
        ),
        PacketFieldDefinition(
            key="rfp_release_date",
            label="RFP Release Date",
            question="When is the RFP expected or released?",
            section=CanonicalPacketSection.REQUIREMENTS_AND_SCOPE,
            value_kind=PacketFieldValueKind.DATE,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.IMPORTED_DATA, label="opportunity feed import"
                ),
                AnswerPath(
                    kind=AnswerPathKind.EVIDENCE_EXTRACTION,
                    label="notice date extraction",
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.SOURCE_DOCUMENT,),
        ),
        PacketFieldDefinition(
            key="total_contract_value",
            label="Total Contract Value",
            question="What total value should frame the pursuit decision?",
            section=CanonicalPacketSection.PRICE_TO_WIN,
            value_kind=PacketFieldValueKind.MONEY,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.IMPORTED_DATA, label="CRM or award import"
                ),
                AnswerPath(
                    kind=AnswerPathKind.MODEL_SYNTHESIS,
                    label="range synthesis from evidence",
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.CONTRACT_TYPE,),
        ),
        PacketFieldDefinition(
            key="primary_scope",
            label="Primary Scope",
            question="What work is the customer buying?",
            section=CanonicalPacketSection.REQUIREMENTS_AND_SCOPE,
            value_kind=PacketFieldValueKind.PROSE,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.EVIDENCE_EXTRACTION,
                    label="SOW or PWS extraction",
                ),
                AnswerPath(
                    kind=AnswerPathKind.MODEL_SYNTHESIS, label="scope synthesis"
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.SCOPE_AREA,),
        ),
        PacketFieldDefinition(
            key="competition",
            label="Competition",
            question="Which competitors or incumbents shape the win strategy?",
            section=CanonicalPacketSection.COMPETITIVE_POSITION,
            value_kind=PacketFieldValueKind.ENTITY_LIST,
            answer_paths=(
                AnswerPath(kind=AnswerPathKind.HUMAN_INPUT, label="capture lead intel"),
                AnswerPath(
                    kind=AnswerPathKind.CAPABILITY_MODULE,
                    label="competitor research capability",
                ),
            ),
            related_entity_kinds=(
                KnowledgeEntityKind.COMPETITOR,
                KnowledgeEntityKind.INCUMBENT,
            ),
        ),
        PacketFieldDefinition(
            key="pwin",
            label="pWin",
            question="What is the current win-probability judgment and why?",
            section=CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
            value_kind=PacketFieldValueKind.PERCENTAGE,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.HUMAN_INPUT, label="capture lead judgment"
                ),
                AnswerPath(
                    kind=AnswerPathKind.MODEL_SYNTHESIS,
                    label="evidence-backed pWin rationale",
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.CAPTURE_PATTERN,),
        ),
        PacketFieldDefinition(
            key="evaluation_methodology",
            label="Evaluation Methodology",
            question="How will the customer score proposals and tradeoffs?",
            section=CanonicalPacketSection.REQUIREMENTS_AND_SCOPE,
            value_kind=PacketFieldValueKind.PROSE,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.EVIDENCE_EXTRACTION,
                    label="Section M extraction",
                ),
                AnswerPath(
                    kind=AnswerPathKind.MODEL_SYNTHESIS,
                    label="evaluation implication synthesis",
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.EVALUATION_METHOD,),
        ),
        PacketFieldDefinition(
            key="risks",
            label="Risks",
            question="Which pursuit or execution risks could change the decision?",
            section=CanonicalPacketSection.RISKS_AND_GAPS,
            value_kind=PacketFieldValueKind.PROSE,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.HUMAN_INPUT, label="capture team risk review"
                ),
                AnswerPath(
                    kind=AnswerPathKind.MODEL_SYNTHESIS,
                    label="risk synthesis from gaps",
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.CAPTURE_PATTERN,),
        ),
        PacketFieldDefinition(
            key="approval_criteria",
            label="Approval Criteria",
            question="What must be true for the gate decision to proceed?",
            section=CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
            value_kind=PacketFieldValueKind.DECISION,
            answer_paths=(
                AnswerPath(
                    kind=AnswerPathKind.HUMAN_INPUT, label="review authority input"
                ),
                AnswerPath(
                    kind=AnswerPathKind.MODEL_SYNTHESIS,
                    label="readiness and gap synthesis",
                ),
            ),
            related_entity_kinds=(KnowledgeEntityKind.REUSABLE_INSIGHT,),
        ),
    )


def get_packet_field_definition(
    definitions: tuple[PacketFieldDefinition, ...],
    key: str,
) -> PacketFieldDefinition:
    for definition in definitions:
        if definition.key == key:
            return definition
    raise KeyError(f"unknown packet field definition: {key}")


def create_packet_field_answer(
    *,
    field_key: str,
    opportunity_id: str,
    value: str | None = None,
    status: PacketFieldAnswerStatus = PacketFieldAnswerStatus.UNANSWERED,
    evidence_status: EvidenceStatus = EvidenceStatus.GAP,
    evidence_ids: tuple[str, ...] = (),
    assumption: str | None = None,
    confidence: float | None = None,
    gap_summary: str | None = None,
    action_item_ids: tuple[str, ...] = (),
    entity_ids: tuple[str, ...] = (),
    provenance_note: str | None = None,
    authority: KnowledgeAuthority = KnowledgeAuthority.ARIADNE_SOURCE_OF_TRUTH,
) -> PacketFieldAnswer:
    return PacketFieldAnswer(
        field_key=field_key,
        opportunity_id=opportunity_id,
        value=value,
        status=status,
        evidence_status=evidence_status,
        evidence_ids=evidence_ids,
        assumption=assumption,
        confidence=confidence,
        gap_summary=gap_summary,
        action_item_ids=action_item_ids,
        entity_ids=entity_ids,
        provenance_note=provenance_note,
        authority=authority,
    )


def build_packet_field_review(
    *,
    opportunity_id: str,
    definitions: tuple[PacketFieldDefinition, ...],
    answers: tuple[PacketFieldAnswer, ...],
    entities: dict[str, SharedKnowledgeEntity],
) -> PacketFieldReview:
    items = tuple(
        PacketFieldReviewItem(
            field_key=definition.key,
            label=definition.label,
            question=definition.question,
            answer=_find_answer(answers, opportunity_id, definition.key),
            answer_paths=definition.answer_paths,
            connections=_find_connections(
                definition=definition,
                opportunity_id=opportunity_id,
                answers=answers,
                entities=entities,
            ),
        )
        for definition in definitions
    )
    return PacketFieldReview(opportunity_id=opportunity_id, items=items)


def build_demo_packet_field_review() -> PacketFieldReview:
    definitions = build_default_packet_field_definitions()
    entities = {
        "entity_aflcmc": SharedKnowledgeEntity(
            id="entity_aflcmc",
            kind=KnowledgeEntityKind.CUSTOMER,
            label="AFLCMC",
        ),
        "entity_recompete_pattern": SharedKnowledgeEntity(
            id="entity_recompete_pattern",
            kind=KnowledgeEntityKind.CAPTURE_PATTERN,
            label="Incumbent recompete transition risk",
        ),
    }
    answers = (
        create_packet_field_answer(
            field_key="customer",
            opportunity_id="opp-aflcmc-recompete",
            value="AFLCMC",
            status=PacketFieldAnswerStatus.ANSWERED,
            evidence_status=EvidenceStatus.ANSWERED,
            evidence_ids=("ev_customer_call",),
            confidence=0.82,
            action_item_ids=("ap_validate_customer",),
            entity_ids=("entity_aflcmc",),
            provenance_note="Captured from customer call and CRM import draft.",
        ),
        create_packet_field_answer(
            field_key="customer",
            opportunity_id="opp-aflcmc-archive",
            value="AFLCMC",
            status=PacketFieldAnswerStatus.ANSWERED,
            evidence_status=EvidenceStatus.ANSWERED,
            evidence_ids=("ev_prior_customer_note",),
            entity_ids=("entity_aflcmc",),
            provenance_note="Prior opportunity answer for context only.",
        ),
        create_packet_field_answer(
            field_key="pwin",
            opportunity_id="opp-aflcmc-recompete",
            value="62%",
            status=PacketFieldAnswerStatus.NEEDS_REVIEW,
            evidence_status=EvidenceStatus.PARTIAL,
            evidence_ids=("ev_capture_notes",),
            confidence=0.55,
            gap_summary="Need competitor and customer pain validation before decision use.",
            action_item_ids=("ap_close_customer_context_gap",),
            entity_ids=("entity_recompete_pattern",),
            provenance_note="Draft pWin from current packet evidence and known recompete pattern.",
        ),
    )
    return build_packet_field_review(
        opportunity_id="opp-aflcmc-recompete",
        definitions=definitions,
        answers=answers,
        entities=entities,
    )


def _find_answer(
    answers: tuple[PacketFieldAnswer, ...],
    opportunity_id: str,
    field_key: str,
) -> PacketFieldAnswer | None:
    for answer in answers:
        if answer.opportunity_id == opportunity_id and answer.field_key == field_key:
            return answer
    return None


def _find_connections(
    *,
    definition: PacketFieldDefinition,
    opportunity_id: str,
    answers: tuple[PacketFieldAnswer, ...],
    entities: dict[str, SharedKnowledgeEntity],
) -> tuple[PacketFieldConnection, ...]:
    current = _find_answer(answers, opportunity_id, definition.key)
    if current is None:
        return ()

    connections: list[PacketFieldConnection] = []
    current_entities = set(current.entity_ids)
    for answer in answers:
        if (
            answer.opportunity_id == opportunity_id
            or answer.field_key != definition.key
        ):
            continue
        for entity_id in sorted(current_entities.intersection(answer.entity_ids)):
            entity = entities.get(entity_id)
            if entity is None:
                continue
            connections.append(
                PacketFieldConnection(
                    opportunity_id=answer.opportunity_id,
                    field_key=answer.field_key,
                    value=answer.value,
                    shared_entity_id=entity.id,
                    shared_entity_label=entity.label,
                    shared_entity_kind=entity.kind,
                )
            )
    return tuple(connections)
