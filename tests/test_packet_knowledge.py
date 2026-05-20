from ariadne.action_plans import (
    ActionPlanItem,
    CaptureActionPlan,
    build_action_plan_item_detail_view,
    build_action_plan_view,
)
from ariadne.packet_knowledge import (
    AnswerPathKind,
    KnowledgeAuthority,
    KnowledgeEntityKind,
    PacketFieldAnswerStatus,
    PacketFieldAnswerStore,
    PacketFieldDefinition,
    PacketFieldValueKind,
    SharedKnowledgeEntity,
    build_default_packet_field_definitions,
    build_packet_field_review,
    create_packet_field_answer,
    get_packet_field_definition,
)
from ariadne.opportunities import MilestoneGate
from ariadne.packets import CanonicalPacketSection, EvidenceStatus


def test_packet_field_definition_represents_reusable_strategic_question() -> None:
    definitions = build_default_packet_field_definitions()

    customer = get_packet_field_definition(definitions, "customer")

    assert customer.key == "customer"
    assert customer.label == "Customer"
    assert customer.question == "Which customer or buying command owns the need?"
    assert customer.section is CanonicalPacketSection.CUSTOMER_CONTEXT
    assert customer.value_kind is PacketFieldValueKind.ENTITY
    assert KnowledgeEntityKind.CUSTOMER in customer.related_entity_kinds
    assert {path.kind for path in customer.answer_paths} >= {
        AnswerPathKind.HUMAN_INPUT,
        AnswerPathKind.IMPORTED_DATA,
        AnswerPathKind.EVIDENCE_EXTRACTION,
    }
    assert customer.authority is KnowledgeAuthority.ARIADNE_SOURCE_OF_TRUTH
    assert customer.required_milestone_gates == (
        MilestoneGate.MILESTONE_1,
        MilestoneGate.MILESTONE_2,
        MilestoneGate.MILESTONE_3,
        MilestoneGate.MILESTONE_4,
    )


def test_default_packet_field_definitions_are_milestone_scoped() -> None:
    definitions = build_default_packet_field_definitions()

    assert all(definition.required_milestone_gates for definition in definitions)
    evaluation = get_packet_field_definition(definitions, "evaluation_methodology")
    competition = get_packet_field_definition(definitions, "competition")

    assert MilestoneGate.MILESTONE_1 not in evaluation.required_milestone_gates
    assert MilestoneGate.MILESTONE_3 in evaluation.required_milestone_gates
    assert MilestoneGate.MILESTONE_1 not in competition.required_milestone_gates
    assert MilestoneGate.MILESTONE_2 in competition.required_milestone_gates


def test_field_answer_carries_opportunity_specific_provenance_and_gap_links() -> None:
    answer = create_packet_field_answer(
        field_key="customer",
        opportunity_id="opp-aflcmc-recompete",
        value="AFLCMC",
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=EvidenceStatus.ANSWERED,
        evidence_ids=("ev_customer_call",),
        assumption="Buying command inferred from recompete notes.",
        confidence=0.82,
        action_item_ids=("ap_validate_customer",),
        entity_ids=("entity_aflcmc",),
        provenance_note="Captured from customer call and CRM import draft.",
    )

    assert answer.field_key == "customer"
    assert answer.opportunity_id == "opp-aflcmc-recompete"
    assert answer.value == "AFLCMC"
    assert answer.evidence_ids == ("ev_customer_call",)
    assert answer.assumption == "Buying command inferred from recompete notes."
    assert answer.confidence == 0.82
    assert answer.action_item_ids == ("ap_validate_customer",)
    assert answer.entity_ids == ("entity_aflcmc",)
    assert answer.provenance_note == "Captured from customer call and CRM import draft."


def test_packet_field_answer_store_round_trips_by_opportunity(tmp_path) -> None:
    store = PacketFieldAnswerStore(tmp_path / "packet-field-answers")
    first = create_packet_field_answer(
        field_key="customer",
        opportunity_id="opp-current",
        value="AFLCMC",
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=EvidenceStatus.ASSUMPTION,
    )
    second = create_packet_field_answer(
        field_key="customer",
        opportunity_id="opp-prior",
        value="AFLCMC",
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=EvidenceStatus.ANSWERED,
    )

    store.write(first)
    store.write(second)

    assert store.read(opportunity_id="opp-current", field_key="customer") == first
    assert store.list(opportunity_id="opp-current") == (first,)
    assert len(store.list()) == 2


def test_field_review_connections_are_context_not_answer_reuse() -> None:
    definitions = (
        PacketFieldDefinition(
            key="customer",
            label="Customer",
            question="Which customer or buying command owns the need?",
            section=CanonicalPacketSection.CUSTOMER_CONTEXT,
            value_kind=PacketFieldValueKind.ENTITY,
            related_entity_kinds=(KnowledgeEntityKind.CUSTOMER,),
        ),
    )
    entities = {
        "entity_aflcmc": SharedKnowledgeEntity(
            id="entity_aflcmc",
            kind=KnowledgeEntityKind.CUSTOMER,
            label="AFLCMC",
        )
    }
    current = create_packet_field_answer(
        field_key="customer",
        opportunity_id="opp-current",
        value="AFLCMC",
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=EvidenceStatus.ANSWERED,
        entity_ids=("entity_aflcmc",),
    )
    related = create_packet_field_answer(
        field_key="customer",
        opportunity_id="opp-prior",
        value="AFLCMC",
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=EvidenceStatus.ANSWERED,
        entity_ids=("entity_aflcmc",),
    )

    review = build_packet_field_review(
        opportunity_id="opp-current",
        definitions=definitions,
        answers=(current, related),
        entities=entities,
    )

    item = review.items[0]
    assert item.answer == current
    assert item.connections[0].opportunity_id == "opp-prior"
    assert item.connections[0].shared_entity_label == "AFLCMC"
    assert item.connections[0].validity_scope == "opportunity_specific"
    assert "context only" in item.scope_note


def test_knowledge_mirror_projection_is_not_source_of_truth() -> None:
    mirror_entity = SharedKnowledgeEntity(
        id="mirror_aflcmc",
        kind=KnowledgeEntityKind.CUSTOMER,
        label="AFLCMC",
        authority=KnowledgeAuthority.KNOWLEDGE_MIRROR_PROJECTION,
        source_ref="obsidian://Ariadne/Customers/AFLCMC",
    )

    assert mirror_entity.authority is KnowledgeAuthority.KNOWLEDGE_MIRROR_PROJECTION
    assert mirror_entity.is_source_of_truth is False


def test_action_plan_item_can_link_to_packet_field_answer() -> None:
    item = ActionPlanItem(
        id="ap_validate_customer",
        action="Validate customer buying command",
        rationale="Customer field answer is still assumption-backed.",
        related_packet_field_key="customer",
    )
    plan = CaptureActionPlan(
        opportunity_name="AFLCMC recompete support",
        items=(item,),
    )

    primary_view = build_action_plan_view(plan)
    detail_view = build_action_plan_item_detail_view(item)

    assert primary_view.items[0].related_packet_field_key == "customer"
    assert detail_view.related_packet_field_key == "customer"
