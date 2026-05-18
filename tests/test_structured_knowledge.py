from ariadne.action_plans import ActionPlanItem, CaptureActionPlan
from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutput,
    CapabilityRunOutputReviewState,
    CapabilityRunSessionContext,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.document_intake import AcceptedDocumentEvidenceLink, DocumentIntakeStore
from ariadne.evidence import (
    LocalEvidenceStore,
    create_derived_evidence,
    create_source_evidence,
)
from ariadne.opportunities import (
    EntryContext,
    EntryReason,
    LifecycleState,
    create_opportunity,
)
from ariadne.packet_knowledge import PacketFieldAnswerStatus, create_packet_field_answer
from ariadne.packets import EvidenceStatus
from ariadne.piid_profiles import (
    PiidAwardBaseline,
    PiidContractIntelligenceProfile,
    PiidProfileProvenance,
    PiidProfileStore,
    PiidScenarioClassification,
)
from ariadne.sam_gov_profiles import SamGovEnrichmentProfile, SamGovProfileStore
from ariadne.structured_knowledge import (
    KnowledgeRecordKind,
    KnowledgeTrustState,
    build_structured_knowledge_index,
)


def test_structured_knowledge_index_projects_one_opportunity_trusted_evidence(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs initial capture context.",
        ),
    )
    unrelated_opportunity = create_opportunity(
        name="opp-unrelated",
        entry_context=EntryContext(
            reason=EntryReason.NEW_LEAD,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Separate lead should not leak into this context.",
        ),
    )
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    trusted_evidence = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_transition_risk",
            content="Customer flagged transition risk on the recompete.",
            source_ref="meeting:2026-05-15",
            opportunity_id=opportunity.name,
        )
    )
    unrelated_evidence = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_other_customer",
            content="Different customer needs pricing research.",
            source_ref="meeting:2026-05-16",
            opportunity_id=unrelated_opportunity.name,
        )
    )

    index = build_structured_knowledge_index(
        opportunities=(opportunity, unrelated_opportunity),
        evidence_store=evidence_store,
    )
    projection = index.for_opportunity(opportunity.name)

    assert projection.opportunity_id == opportunity.name
    assert {
        record.record_id
        for record in index.records
        if record.kind is KnowledgeRecordKind.EVIDENCE_ITEM
    } == {trusted_evidence.id, unrelated_evidence.id}
    assert [
        record.record_id
        for record in projection.trusted_records
        if record.kind is KnowledgeRecordKind.EVIDENCE_ITEM
    ] == [trusted_evidence.id]
    assert all(
        record.record_id != unrelated_evidence.id
        for record in projection.trusted_records + projection.reviewable_records
    )
    trusted_record = next(
        record
        for record in projection.trusted_records
        if record.kind is KnowledgeRecordKind.EVIDENCE_ITEM
    )
    assert trusted_record.trust_state is KnowledgeTrustState.TRUSTED


def test_structured_knowledge_index_connects_packet_fields_and_action_plan_items(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs initial capture context.",
        ),
    )
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    evidence = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_customer_need",
            content="Customer needs transition proof.",
            source_ref="call:2026-05-15",
            opportunity_id=opportunity.name,
        )
    )
    answer = create_packet_field_answer(
        field_key="primary_scope",
        opportunity_id=opportunity.name,
        value="Transition support",
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=EvidenceStatus.ANSWERED,
        evidence_ids=(evidence.id,),
        action_item_ids=("ap_validate_scope",),
    )
    unrelated_answer = create_packet_field_answer(
        field_key="primary_scope",
        opportunity_id="opp-unrelated",
        value="Pricing analysis",
        status=PacketFieldAnswerStatus.ANSWERED,
        evidence_status=EvidenceStatus.ANSWERED,
        evidence_ids=("ev_unrelated",),
    )
    action_item = ActionPlanItem(
        id="ap_validate_scope",
        action="Validate transition scope",
        rationale="Packet answer needs customer confirmation.",
        related_packet_field_key="primary_scope",
        related_evidence_ids=(evidence.id,),
    )
    unrelated_action = ActionPlanItem(
        id="ap_unrelated",
        action="Research unrelated pricing",
        rationale="Different opportunity work.",
        related_packet_field_key="primary_scope",
    )

    index = build_structured_knowledge_index(
        opportunities=(opportunity,),
        evidence_store=evidence_store,
        packet_field_answers=(answer, unrelated_answer),
        action_plans=(
            CaptureActionPlan(opportunity_name=opportunity.name, items=(action_item,)),
            CaptureActionPlan(opportunity_name="opp-unrelated", items=(unrelated_action,)),
        ),
    )
    projection = index.for_opportunity(opportunity.name)

    projected_record_ids = {record.record_id for record in projection.trusted_records}
    assert "packet_field_answer:opp-aflcmc-recompete:primary_scope" in projected_record_ids
    assert action_item.id in projected_record_ids
    assert "packet_field_answer:opp-unrelated:primary_scope" not in projected_record_ids
    assert unrelated_action.id not in projected_record_ids

    connection_keys = {
        (
            connection.source_kind,
            connection.source_id,
            connection.relationship,
            connection.target_kind,
            connection.target_id,
        )
        for connection in projection.connections
    }
    assert (
        KnowledgeRecordKind.PACKET_FIELD_ANSWER,
        "packet_field_answer:opp-aflcmc-recompete:primary_scope",
        "supported_by_evidence",
        KnowledgeRecordKind.EVIDENCE_ITEM,
        evidence.id,
    ) in connection_keys
    assert (
        KnowledgeRecordKind.ACTION_PLAN_ITEM,
        action_item.id,
        "addresses_packet_field",
        KnowledgeRecordKind.PACKET_FIELD_ANSWER,
        "packet_field_answer:opp-aflcmc-recompete:primary_scope",
    ) in connection_keys


def test_structured_knowledge_index_connects_derived_evidence_lineage(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs evidence lineage.",
        ),
    )
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    source = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_source_note",
            content="Customer said transition is risky.",
            source_ref="call:2026-05-15",
            opportunity_id=opportunity.name,
        )
    )
    derived = evidence_store.write(
        create_derived_evidence(
            evidence_id="ev_derived_transition_gap",
            content="Transition risk should become a packet gap.",
            derived_from_ids=(source.id,),
            opportunity_id=opportunity.name,
        )
    )

    index = build_structured_knowledge_index(
        opportunities=(opportunity,),
        evidence_store=evidence_store,
    )
    projection = index.for_opportunity(opportunity.name)

    assert {record.record_id for record in projection.trusted_records} >= {
        source.id,
        derived.id,
    }
    assert (
        KnowledgeRecordKind.EVIDENCE_ITEM,
        derived.id,
        "derived_from_evidence",
        KnowledgeRecordKind.EVIDENCE_ITEM,
        source.id,
    ) in {
        (
            connection.source_kind,
            connection.source_id,
            connection.relationship,
            connection.target_kind,
            connection.target_id,
        )
        for connection in projection.connections
    }


def test_structured_knowledge_index_connects_accepted_document_intake_evidence_links(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs document-backed context.",
        ),
    )
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    evidence = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_doc_transition_risk",
            content="Source span says transition risk is material.",
            source_ref="upload:customer-brief.md",
            opportunity_id=opportunity.name,
            source_intake_record_id="intake_customer_brief",
            source_extraction_bundle_id="bundle_customer_brief",
            source_span_ids=("span_transition_risk",),
        )
    )
    document_intake_store = DocumentIntakeStore(tmp_path / "document-intake")
    accepted_link = document_intake_store.write_accepted_evidence_link(
        AcceptedDocumentEvidenceLink(
            id="accepted_link_transition_risk",
            intake_record_id="intake_customer_brief",
            extraction_bundle_id="bundle_customer_brief",
            source_span_ids=("span_transition_risk",),
            evidence_id=evidence.id,
            source_ref="upload:customer-brief.md",
            parser_adapter="ariadne.generic_text_extractor",
            parser_version="0.1",
            parser_method="deterministic_text_split",
            confidence=0.84,
            reviewer_rationale="Span directly supports transition risk evidence.",
        )
    )
    document_intake_store.write_accepted_evidence_link(
        AcceptedDocumentEvidenceLink(
            id="accepted_link_unrelated",
            intake_record_id="intake_other",
            extraction_bundle_id="bundle_other",
            source_span_ids=("span_other",),
            evidence_id="ev_other_customer",
            source_ref="upload:other.md",
            parser_adapter="ariadne.generic_text_extractor",
            parser_version="0.1",
            parser_method="deterministic_text_split",
            confidence=0.8,
            reviewer_rationale="Different accepted source span.",
        )
    )

    index = build_structured_knowledge_index(
        opportunities=(opportunity,),
        evidence_store=evidence_store,
        document_intake_store=document_intake_store,
    )
    projection = index.for_opportunity(opportunity.name)

    assert accepted_link.id in {
        record.record_id
        for record in projection.trusted_records
        if record.kind is KnowledgeRecordKind.DOCUMENT_INTAKE_EVIDENCE_LINK
    }
    assert "accepted_link_unrelated" not in {
        record.record_id for record in projection.trusted_records
    }
    assert (
        KnowledgeRecordKind.DOCUMENT_INTAKE_EVIDENCE_LINK,
        accepted_link.id,
        "accepted_source_span_for_evidence",
        KnowledgeRecordKind.EVIDENCE_ITEM,
        evidence.id,
    ) in {
        (
            connection.source_kind,
            connection.source_id,
            connection.relationship,
            connection.target_kind,
            connection.target_id,
        )
        for connection in projection.connections
    }


def test_structured_knowledge_index_includes_profile_records_without_leaking_them(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs public-data context.",
        ),
    )
    piid_store = PiidProfileStore(tmp_path / "piid-profiles")
    sam_gov_store = SamGovProfileStore(tmp_path / "sam-gov-profiles")
    piid_profile = piid_store.write(
        PiidContractIntelligenceProfile(
            id="piid_profile_FA8650_23_C_0001",
            input_contract_number="FA8650-23-C-0001",
            normalized_piid="FA8650-23-C-0001",
            scenario=PiidScenarioClassification.STANDALONE_CONTRACT,
            provenance=PiidProfileProvenance(
                source_capability_id="usaspending",
                source_tool_name="lookup_piid",
                source_package="usaspending-gov-mcp",
                source_package_version="0.3.2",
                checked_at="2026-05-18T10:00:00Z",
                lookup_status="success",
            ),
            award_baseline=PiidAwardBaseline(
                resolved_award_id="FA8650-23-C-0001"
            ),
            created_at="2026-05-18T10:01:00Z",
            updated_at="2026-05-18T10:01:00Z",
        )
    )
    sam_gov_profile = sam_gov_store.write(
        SamGovEnrichmentProfile(
            id="sam_profile_FA8650_23_C_0001",
            input_pivot="FA8650-23-C-0001",
            normalized_pivot="FA8650-23-C-0001",
            created_at="2026-05-18T10:02:00Z",
            updated_at="2026-05-18T10:02:00Z",
        )
    )

    index = build_structured_knowledge_index(
        opportunities=(opportunity,),
        piid_profile_store=piid_store,
        sam_gov_profile_store=sam_gov_store,
    )
    projection = index.for_opportunity(opportunity.name)

    assert (
        KnowledgeRecordKind.PIID_PROFILE,
        piid_profile.id,
    ) in {(record.kind, record.record_id) for record in index.records}
    assert (
        KnowledgeRecordKind.SAM_GOV_PROFILE,
        sam_gov_profile.id,
    ) in {(record.kind, record.record_id) for record in index.records}
    assert piid_profile.id not in {
        record.record_id for record in projection.trusted_records
    }
    assert sam_gov_profile.id not in {
        record.record_id for record in projection.trusted_records
    }


def test_structured_knowledge_index_projects_capability_runs_outputs_and_input_refs(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs capability-run context.",
        ),
    )
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    evidence = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_capability_input",
            content="Capability run used this accepted note.",
            source_ref="note:capability-input",
            opportunity_id=opportunity.name,
        )
    )
    piid_store = PiidProfileStore(tmp_path / "piid-profiles")
    sam_gov_store = SamGovProfileStore(tmp_path / "sam-gov-profiles")
    piid_profile = piid_store.write(
        PiidContractIntelligenceProfile(
            id="piid_profile_FA8650_23_C_0001",
            input_contract_number="FA8650-23-C-0001",
            normalized_piid="FA8650-23-C-0001",
            scenario=PiidScenarioClassification.STANDALONE_CONTRACT,
            provenance=PiidProfileProvenance(
                source_capability_id="usaspending",
                source_tool_name="lookup_piid",
                source_package="usaspending-gov-mcp",
                source_package_version="0.3.2",
                checked_at="2026-05-18T10:00:00Z",
                lookup_status="success",
            ),
            award_baseline=PiidAwardBaseline(
                resolved_award_id="FA8650-23-C-0001"
            ),
            created_at="2026-05-18T10:01:00Z",
            updated_at="2026-05-18T10:01:00Z",
        )
    )
    sam_gov_profile = sam_gov_store.write(
        SamGovEnrichmentProfile(
            id="sam_profile_FA8650_23_C_0001",
            input_pivot="FA8650-23-C-0001",
            normalized_pivot="FA8650-23-C-0001",
            created_at="2026-05-18T10:02:00Z",
            updated_at="2026-05-18T10:02:00Z",
        )
    )
    capability_run_store = CapabilityRunStore(tmp_path / "capability-runs")
    run = capability_run_store.write(
        CapabilityRun(
            run_id="caprun_context_check",
            capability_id="capability_catalog_validation",
            capability_type=CapabilityRunCapabilityType.ADAPTER,
            executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
            session_context=CapabilityRunSessionContext.PRODUCT,
            opportunity_id=opportunity.name,
            product_workflow="knowledge_context",
            status=CapabilityRunStatus.NEEDS_REVIEW,
            inputs_summary="Checked available context before next capture actions.",
            input_refs=(evidence.id, piid_profile.id, sam_gov_profile.id),
            outputs=(
                CapabilityRunOutput(
                    output_id="output_context_gap",
                    output_type="gap_summary",
                    title="Transition evidence gap",
                    summary="Transition proof needs one more customer source.",
                    review_state=CapabilityRunOutputReviewState.PENDING,
                ),
            ),
        )
    )

    index = build_structured_knowledge_index(
        opportunities=(opportunity,),
        evidence_store=evidence_store,
        piid_profile_store=piid_store,
        sam_gov_profile_store=sam_gov_store,
        capability_run_store=capability_run_store,
    )
    projection = index.for_opportunity(opportunity.name)

    reviewable_ids = {record.record_id for record in projection.reviewable_records}
    assert run.run_id in reviewable_ids
    assert "capability_run_output:caprun_context_check:output_context_gap" in reviewable_ids
    assert piid_profile.id in reviewable_ids
    assert sam_gov_profile.id in reviewable_ids
    assert (
        KnowledgeRecordKind.CAPABILITY_RUN,
        run.run_id,
        "used_input_ref",
        KnowledgeRecordKind.PIID_PROFILE,
        piid_profile.id,
    ) in {
        (
            connection.source_kind,
            connection.source_id,
            connection.relationship,
            connection.target_kind,
            connection.target_id,
        )
        for connection in projection.connections
    }
    assert (
        KnowledgeRecordKind.CAPABILITY_RUN,
        run.run_id,
        "produced_output",
        KnowledgeRecordKind.CAPABILITY_RUN_OUTPUT,
        "capability_run_output:caprun_context_check:output_context_gap",
    ) in {
        (
            connection.source_kind,
            connection.source_id,
            connection.relationship,
            connection.target_kind,
            connection.target_id,
        )
        for connection in projection.connections
    }