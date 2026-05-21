from datetime import UTC, datetime

from ariadne.opportunity_activation import (
    OpportunityActivationFieldReviewDecisionType,
    OpportunityActivationFieldReviewRequest,
    OpportunityActivationReviewState,
    OpportunityActivationRunStore,
    OpportunityActivationRunTrigger,
    PacketFieldActionItem,
    PacketFieldActionState,
    PacketFieldRouteKind,
    build_packet_field_action_matrix,
    record_opportunity_activation_field_review,
    run_opportunity_activation,
)
from ariadne.knowledge_vault import ensure_packet_data_element_pages
from ariadne.opportunities import MilestoneGate
from ariadne.packet_knowledge import (
    PacketFieldAnswerStore,
    PacketFieldAnswerStatus,
    build_default_packet_field_definitions,
    create_packet_field_answer,
)
from ariadne.packets import EvidenceStatus


def test_activation_run_covers_all_packet_field_definitions() -> None:
    definitions = build_default_packet_field_definitions()

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    matrix = run.packet_field_action_matrix
    assert run.packet_field_count == len(definitions)
    assert len(matrix.fields) == len(definitions)
    assert matrix.blocked_field_count == len(definitions)
    assert matrix.review_ready_count == 0
    assert all(
        field.action_state is PacketFieldActionState.BLOCKED for field in matrix.fields
    )
    assert all(field.recommended_route for field in matrix.fields)


def test_activation_matrix_marks_current_milestone_gate_fields() -> None:
    definitions = build_default_packet_field_definitions()

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        current_milestone_gate=MilestoneGate.MILESTONE_1,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    matrix = run.packet_field_action_matrix
    evaluation = next(
        field for field in matrix.fields if field.field_key == "evaluation_methodology"
    )
    customer = next(field for field in matrix.fields if field.field_key == "customer")

    assert matrix.current_milestone_gate == MilestoneGate.MILESTONE_1.value
    assert matrix.current_gate_field_count < len(definitions)
    assert matrix.current_gate_blocked_count == matrix.current_gate_field_count
    assert customer.current_gate_required is True
    assert evaluation.current_gate_required is False
    assert evaluation.required_milestone_gates == (
        MilestoneGate.MILESTONE_3.value,
        MilestoneGate.MILESTONE_4.value,
    )


def test_activation_matrix_exposes_route_steps_and_approval_gates() -> None:
    definitions = build_default_packet_field_definitions()

    matrix = build_packet_field_action_matrix(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
    )

    customer = next(field for field in matrix.fields if field.field_key == "customer")
    competition = next(
        field for field in matrix.fields if field.field_key == "competition"
    )
    pwin = next(field for field in matrix.fields if field.field_key == "pwin")

    assert any(
        "notice or call-note extraction" in step for step in customer.route_steps
    )
    assert customer.approval_gate is None
    assert competition.route_kind is PacketFieldRouteKind.RESEARCH_OR_MCP
    assert competition.route_steps == (
        "Approve capability-backed research route.",
        "Use competitor research capability.",
        "Cross-check with capture lead intel.",
        "Review packet candidate before trusted use.",
    )
    assert competition.approval_gate == (
        "Operator approval required before capability-backed or external research."
    )
    assert pwin.route_kind is PacketFieldRouteKind.MODEL_SYNTHESIS
    assert pwin.route_steps[-1] == "Review synthesized answer before trusted use."
    assert pwin.approval_gate == (
        "Human review required before synthesized content becomes a trusted answer."
    )


def test_activation_matrix_exposes_capability_routes_for_each_route_kind() -> None:
    matrix = build_packet_field_action_matrix(
        opportunity_id="opp-disa-cloud",
        definitions=build_default_packet_field_definitions(),
    )

    routes_by_field = {
        field.field_key: field.capability_routes[0]
        for field in matrix.fields
        if field.capability_routes
    }

    assert set(routes_by_field) == {
        "customer",
        "prime_name",
        "rfp_release_date",
        "total_contract_value",
        "primary_scope",
        "competition",
        "pwin",
        "evaluation_methodology",
        "risks",
        "approval_criteria",
    }
    assert routes_by_field["competition"].capability_type == "skill_chain"
    assert routes_by_field["pwin"].capability_id == "hosted-packet-synthesis-model"
    assert routes_by_field["pwin"].model_required is True
    assert routes_by_field["total_contract_value"].capability_type == "source_profile_route"
    assert routes_by_field["customer"].capability_id == "document-intake-source-backed-answer"
    assert all(route.trusted_downstream_writes is False for route in routes_by_field.values())


def test_activation_matrix_uses_vault_context_for_customer_route(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    definitions = build_default_packet_field_definitions()
    ensure_packet_data_element_pages(
        vault_root,
        definitions,
        current_milestone_gate=MilestoneGate.MILESTONE_1,
    )
    source_page = (
        vault_root
        / "source-summaries"
        / "project-ariadne"
        / "customer-hot-button-identification.md"
    )
    source_page.parent.mkdir(parents=True)
    source_page.write_text(
        """---
page_type: source_summary
title: Customer Hot Button Identification
source_refs: [project-ariadne:global_wiki/capture/customer-hot-button-identification.md]
relationships: [informs:data-elements/briefing-packet/customer, suggests_route:workflow/customer-engagement]
---

# Customer Hot Button Identification

Hot buttons identify customer priorities and source expectations.
""",
        encoding="utf-8",
    )

    matrix = build_packet_field_action_matrix(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        current_milestone_gate=MilestoneGate.MILESTONE_1,
        vault_root=vault_root,
    )

    customer = next(field for field in matrix.fields if field.field_key == "customer")

    assert "data-elements/briefing-packet/customer.md" in customer.vault_context_refs
    assert (
        "source-summaries/project-ariadne/customer-hot-button-identification.md"
        in customer.vault_context_refs
    )
    assert (
        "informs:data-elements/briefing-packet/customer"
        in customer.vault_relationship_refs
    )
    assert "Customer Hot Button Identification" in customer.route_rationale
    assert any("vault context" in step.lower() for step in customer.route_steps)
    assert customer.action_state is PacketFieldActionState.BLOCKED


def test_activation_matrix_falls_back_when_vault_has_no_relevant_context(
    tmp_path,
) -> None:
    definitions = build_default_packet_field_definitions()
    vault_root = tmp_path / "vault"
    unrelated_page = vault_root / "source-summaries" / "unrelated.md"
    unrelated_page.parent.mkdir(parents=True)
    unrelated_page.write_text(
        """---
page_type: source_summary
title: Unrelated
source_refs: [manual:test]
relationships: [informs:data-elements/briefing-packet/pwin]
---

# Unrelated
""",
        encoding="utf-8",
    )
    (vault_root / "invalid.md").write_text(
        "# Invalid page without frontmatter\n",
        encoding="utf-8",
    )

    matrix = build_packet_field_action_matrix(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        current_milestone_gate=MilestoneGate.MILESTONE_1,
        vault_root=vault_root,
    )

    customer = next(field for field in matrix.fields if field.field_key == "customer")

    assert customer.vault_context_refs == ()
    assert customer.vault_relationship_refs == ()
    assert "Vault context" not in customer.route_rationale


def test_vault_informed_activation_run_does_not_write_packet_answer_until_review(
    tmp_path,
) -> None:
    definitions = build_default_packet_field_definitions()
    vault_root = tmp_path / "vault"
    ensure_packet_data_element_pages(
        vault_root,
        definitions,
        current_milestone_gate=MilestoneGate.MILESTONE_1,
    )
    run_store = OpportunityActivationRunStore(tmp_path / "activation-runs")
    answer_store = PacketFieldAnswerStore(tmp_path / "answers")

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        store=run_store,
        current_milestone_gate=MilestoneGate.MILESTONE_1,
        vault_root=vault_root,
    )

    customer = next(
        field
        for field in run.packet_field_action_matrix.fields
        if field.field_key == "customer"
    )
    assert customer.vault_context_refs == ("data-elements/briefing-packet/customer.md",)
    assert answer_store.list(opportunity_id="opp-disa-cloud") == ()

    response = record_opportunity_activation_field_review(
        run_store=run_store,
        answer_store=answer_store,
        run_id=run.run_id,
        field_key="customer",
        request=OpportunityActivationFieldReviewRequest(
            decision=OpportunityActivationFieldReviewDecisionType.ACCEPT,
            value="DISA",
            evidence_ids=("ev_customer",),
            confidence=0.9,
        ),
    )

    assert response.packet_field_answer is not None
    assert (
        answer_store.read(
            opportunity_id="opp-disa-cloud",
            field_key="customer",
        ).value
        == "DISA"
    )


def test_activation_matrix_hydrates_legacy_route_metadata() -> None:
    definitions = build_default_packet_field_definitions()
    matrix = build_packet_field_action_matrix(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
    )
    competition = next(
        field for field in matrix.fields if field.field_key == "competition"
    )
    legacy_payload = competition.model_dump(
        mode="json",
        exclude={"route_kind", "route_steps", "approval_gate"},
    )

    hydrated = PacketFieldActionItem.model_validate(legacy_payload)

    assert hydrated.route_kind is PacketFieldRouteKind.RESEARCH_OR_MCP
    assert hydrated.route_steps == (
        "Approve capability-backed research route.",
        "Use competitor research capability.",
        "Cross-check with capture lead intel.",
        "Review packet candidate before trusted use.",
    )
    assert hydrated.approval_gate == (
        "Operator approval required before capability-backed or external research."
    )


def test_activation_run_respects_answered_and_review_ready_fields() -> None:
    definitions = build_default_packet_field_definitions()
    answers = (
        create_packet_field_answer(
            field_key="customer",
            opportunity_id="opp-disa-cloud",
            value="DISA",
            status=PacketFieldAnswerStatus.ANSWERED,
            evidence_status=EvidenceStatus.ANSWERED,
            evidence_ids=("ev_customer",),
        ),
        create_packet_field_answer(
            field_key="primary_scope",
            opportunity_id="opp-disa-cloud",
            value="Cloud sustainment scope draft",
            status=PacketFieldAnswerStatus.NEEDS_REVIEW,
            evidence_status=EvidenceStatus.PARTIAL,
            evidence_ids=("ev_scope_draft",),
        ),
    )

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        answers=answers,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    matrix = run.packet_field_action_matrix
    assert matrix.answered_field_count == 1
    assert matrix.review_ready_count == 1
    assert matrix.blocked_field_count == len(definitions) - 2
    customer = next(field for field in matrix.fields if field.field_key == "customer")
    scope = next(field for field in matrix.fields if field.field_key == "primary_scope")
    assert customer.action_state is PacketFieldActionState.ANSWERED
    assert customer.requires_review is False
    assert customer.source_refs == ("ev_customer",)
    assert scope.action_state is PacketFieldActionState.REVIEW_READY
    assert scope.requires_review is True


def test_activation_run_keeps_outputs_review_gated() -> None:
    definitions = build_default_packet_field_definitions()

    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert run.status == "needs_review"
    assert run.review_state is OpportunityActivationReviewState.PENDING_REVIEW
    assert run.outputs
    assert all(
        output.review_state is OpportunityActivationReviewState.PENDING_REVIEW
        for output in run.outputs
    )
    assert run.provenance["trusted_downstream_writes"] is False
    assert run.provenance["network_required"] is False
    assert run.provenance["model_required"] is False


def test_activation_run_store_round_trips_by_opportunity(tmp_path) -> None:
    store = OpportunityActivationRunStore(tmp_path / "activation")
    definitions = build_default_packet_field_definitions()

    first = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=definitions,
        trigger=OpportunityActivationRunTrigger.INITIAL_SCAFFOLD,
        store=store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )
    run_opportunity_activation(
        opportunity_id="opp-navy-training",
        definitions=definitions,
        store=store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert store.read(first.run_id) == first
    assert store.list(opportunity_id="opp-disa-cloud") == (first,)
    assert len(store.list()) == 2


def test_activation_field_acceptance_promotes_packet_field_answer(tmp_path) -> None:
    run_store = OpportunityActivationRunStore(tmp_path / "activation")
    answer_store = PacketFieldAnswerStore(tmp_path / "packet-field-answers")
    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=build_default_packet_field_definitions(),
        store=run_store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    response = record_opportunity_activation_field_review(
        run_store=run_store,
        answer_store=answer_store,
        run_id=run.run_id,
        field_key="customer",
        request=OpportunityActivationFieldReviewRequest(
            decision=OpportunityActivationFieldReviewDecisionType.ACCEPT,
            value="DISA",
            reviewer_rationale="Capture lead confirmed customer.",
            confidence=0.8,
        ),
    )

    answer = response.packet_field_answer
    assert answer is not None
    assert answer.value == "DISA"
    assert answer.status is PacketFieldAnswerStatus.ANSWERED
    assert answer.evidence_status is EvidenceStatus.ASSUMPTION
    assert answer.review_status == "accept"
    assert answer.source_draft_id == run.run_id
    assert (
        answer_store.read(opportunity_id="opp-disa-cloud", field_key="customer")
        == answer
    )
    customer = next(
        field
        for field in response.run.packet_field_action_matrix.fields
        if field.field_key == "customer"
    )
    assert customer.action_state is PacketFieldActionState.ANSWERED
    assert customer.current_value == "DISA"
    assert response.decision.promoted_answer_created is True
    assert (
        response.run.outputs[0].review_state
        is OpportunityActivationReviewState.ACCEPTED
    )
    assert (
        response.run.provenance["field_review_decisions"][0]["field_key"] == "customer"
    )


def test_activation_field_route_records_review_without_trusted_answer(tmp_path) -> None:
    run_store = OpportunityActivationRunStore(tmp_path / "activation")
    answer_store = PacketFieldAnswerStore(tmp_path / "packet-field-answers")
    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=build_default_packet_field_definitions(),
        store=run_store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    response = record_opportunity_activation_field_review(
        run_store=run_store,
        answer_store=answer_store,
        run_id=run.run_id,
        field_key="competition",
        request=OpportunityActivationFieldReviewRequest(
            decision=OpportunityActivationFieldReviewDecisionType.ROUTE,
            reviewer_rationale="Needs research approval before answer.",
            routed_destination="capture_research",
        ),
    )

    assert response.packet_field_answer is None
    assert response.decision.routed_destination == "capture_research"
    assert response.decision.promoted_answer_created is False
    output = next(
        output for output in response.run.outputs if output.field_key == "competition"
    )
    assert output.review_state is OpportunityActivationReviewState.ROUTED
    assert answer_store.list(opportunity_id="opp-disa-cloud") == ()


def test_activation_field_edit_promotes_human_edited_answer(tmp_path) -> None:
    run_store = OpportunityActivationRunStore(tmp_path / "activation")
    answer_store = PacketFieldAnswerStore(tmp_path / "packet-field-answers")
    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=build_default_packet_field_definitions(),
        store=run_store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    response = record_opportunity_activation_field_review(
        run_store=run_store,
        answer_store=answer_store,
        run_id=run.run_id,
        field_key="customer",
        request=OpportunityActivationFieldReviewRequest(
            decision=OpportunityActivationFieldReviewDecisionType.EDIT,
            value="Defense Information Systems Agency",
            reviewer_rationale="Expanded the acronym before trusting the answer.",
        ),
    )

    assert response.packet_field_answer is not None
    assert response.packet_field_answer.value == "Defense Information Systems Agency"
    assert response.packet_field_answer.review_status == "edit"
    assert response.decision.review_gate == "human_edited"
    assert response.decision.promoted_answer_created is True


def test_activation_field_review_blocks_duplicate_decisions(tmp_path) -> None:
    run_store = OpportunityActivationRunStore(tmp_path / "activation")
    answer_store = PacketFieldAnswerStore(tmp_path / "packet-field-answers")
    run = run_opportunity_activation(
        opportunity_id="opp-disa-cloud",
        definitions=build_default_packet_field_definitions(),
        store=run_store,
        created_at=datetime(2026, 5, 19, tzinfo=UTC),
    )
    request = OpportunityActivationFieldReviewRequest(
        decision=OpportunityActivationFieldReviewDecisionType.ACCEPT,
        value="DISA",
        reviewer_rationale="Confirmed.",
    )

    record_opportunity_activation_field_review(
        run_store=run_store,
        answer_store=answer_store,
        run_id=run.run_id,
        field_key="customer",
        request=request,
    )

    try:
        record_opportunity_activation_field_review(
            run_store=run_store,
            answer_store=answer_store,
            run_id=run.run_id,
            field_key="customer",
            request=request,
        )
    except ValueError as error:
        assert str(error) == "Activation field already reviewed"
    else:
        raise AssertionError("duplicate activation field review should fail")
