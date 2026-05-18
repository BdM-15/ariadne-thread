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
from ariadne.evidence import LocalEvidenceStore, create_source_evidence
from ariadne.opportunities import EntryContext, EntryReason, LifecycleState, create_opportunity
from ariadne.packet_knowledge import PacketFieldAnswerStatus, create_packet_field_answer
from ariadne.packets import EvidenceStatus
from ariadne.piid_profiles import (
    PiidAwardBaseline,
    PiidContractIntelligenceProfile,
    PiidGapCategory,
    PiidProfileGap,
    PiidProfileProvenance,
    PiidProfileStore,
    PiidScenarioClassification,
)
from ariadne.structured_knowledge import (
    KnowledgeRecordKind,
    KnowledgeTrustState,
    get_opportunity_knowledge_context,
)


def test_opportunity_knowledge_context_view_separates_context_and_summarizes_commands(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs a composed knowledge view.",
        ),
    )
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    evidence = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_transition_risk",
            content="Customer flagged transition risk on the recompete.",
            source_ref="meeting:2026-05-15",
            opportunity_id=opportunity.name,
        )
    )
    packet_gap = create_packet_field_answer(
        field_key="primary_scope",
        opportunity_id=opportunity.name,
        status=PacketFieldAnswerStatus.GAP,
        evidence_status=EvidenceStatus.GAP,
        gap_summary="Need validated transition scope before gate review.",
    )
    piid_store = PiidProfileStore(tmp_path / "piid-profiles")
    piid_profile = piid_store.write(_piid_profile_with_source_limitation())
    capability_store = CapabilityRunStore(tmp_path / "capability-runs")
    run = capability_store.write(
        CapabilityRun(
            run_id="caprun_context_gap_check",
            capability_id="capability_catalog_validation",
            capability_type=CapabilityRunCapabilityType.ADAPTER,
            executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
            session_context=CapabilityRunSessionContext.PRODUCT,
            opportunity_id=opportunity.name,
            product_workflow="knowledge_context",
            status=CapabilityRunStatus.NEEDS_REVIEW,
            inputs_summary="Checked profile-backed context for capture gaps.",
            input_refs=(evidence.id, piid_profile.id),
            outputs=(
                CapabilityRunOutput(
                    output_id="output_transition_gap",
                    output_type="gap_summary",
                    title="Transition scope still needs review",
                    summary="Confirm transition scope before using it in packet work.",
                    gaps=("Need customer validation for transition scope.",),
                    review_state=CapabilityRunOutputReviewState.PENDING,
                ),
            ),
        )
    )

    context = get_opportunity_knowledge_context(
        opportunity_id=opportunity.name,
        opportunities=(opportunity,),
        evidence_store=evidence_store,
        packet_field_answers=(packet_gap,),
        piid_profile_store=piid_store,
        capability_run_store=capability_store,
    )

    trusted_ids = {item.record_id for item in context.trusted_context.items}
    reviewable_ids = {item.record_id for item in context.reviewable_context.items}
    assert evidence.id in trusted_ids
    assert "packet_field_answer:opp-aflcmc-recompete:primary_scope" in reviewable_ids
    assert run.run_id in reviewable_ids
    assert "capability_run_output:caprun_context_gap_check:output_transition_gap" in reviewable_ids
    assert context.trusted_context.count == len(context.trusted_context.items)
    assert context.reviewable_context.count == len(context.reviewable_context.items)
    assert context.gaps[0].record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER
    assert context.gaps[0].summary == "Need validated transition scope before gate review."
    assert context.source_limitations[0].record_id == piid_profile.id
    assert context.source_limitations[0].summary == (
        "USAspending does not identify current transition scope."
    )
    assert context.related_profile_ids == (piid_profile.id,)
    assert context.related_capability_run_ids == (run.run_id,)
    assert {link.command_id for link in context.next_command_links} >= {
        "review_packet_gap",
        "review_capability_run_output",
    }
    assert all(item.trust_state is KnowledgeTrustState.TRUSTED for item in context.trusted_context.items)
    assert all(
        item.trust_state is KnowledgeTrustState.REVIEWABLE
        for item in context.reviewable_context.items
    )
    assert all("<" not in item.summary and "class=" not in item.summary for item in context.trusted_context.items)


def test_opportunity_knowledge_context_view_does_not_leak_unrelated_records(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Selected opportunity.",
        ),
    )
    unrelated = create_opportunity(
        name="opp-unrelated",
        entry_context=EntryContext(
            reason=EntryReason.NEW_LEAD,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Different opportunity.",
        ),
    )
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    selected_evidence = evidence_store.write(
        create_source_evidence(
            evidence_id="ev_selected",
            content="Selected opportunity evidence.",
            source_ref="note:selected",
            opportunity_id=opportunity.name,
        )
    )
    evidence_store.write(
        create_source_evidence(
            evidence_id="ev_unrelated",
            content="Unrelated opportunity evidence.",
            source_ref="note:unrelated",
            opportunity_id=unrelated.name,
        )
    )
    packet_gap = create_packet_field_answer(
        field_key="customer",
        opportunity_id=opportunity.name,
        status=PacketFieldAnswerStatus.GAP,
        evidence_status=EvidenceStatus.GAP,
        gap_summary="Selected customer gap.",
    )
    unrelated_packet_gap = create_packet_field_answer(
        field_key="customer",
        opportunity_id=unrelated.name,
        status=PacketFieldAnswerStatus.GAP,
        evidence_status=EvidenceStatus.GAP,
        gap_summary="Unrelated customer gap.",
    )
    piid_store = PiidProfileStore(tmp_path / "piid-profiles")
    unrelated_profile = piid_store.write(
        _piid_profile_with_source_limitation(
            profile_id="piid_profile_UNRELATED",
            limitation="Unrelated source limitation.",
        )
    )
    capability_store = CapabilityRunStore(tmp_path / "capability-runs")
    capability_store.write(
        CapabilityRun(
            run_id="caprun_unrelated",
            capability_id="capability_catalog_validation",
            capability_type=CapabilityRunCapabilityType.ADAPTER,
            executor_kind=CapabilityRunExecutorKind.DETERMINISTIC_PYTHON,
            session_context=CapabilityRunSessionContext.PRODUCT,
            opportunity_id=unrelated.name,
            product_workflow="knowledge_context",
            status=CapabilityRunStatus.NEEDS_REVIEW,
            inputs_summary="Unrelated run.",
            input_refs=(unrelated_profile.id,),
        )
    )

    context = get_opportunity_knowledge_context(
        opportunity_id=opportunity.name,
        opportunities=(opportunity, unrelated),
        evidence_store=evidence_store,
        packet_field_answers=(packet_gap, unrelated_packet_gap),
        piid_profile_store=piid_store,
        capability_run_store=capability_store,
    )

    context_json = context.model_dump_json()
    assert selected_evidence.id in context_json
    assert "ev_unrelated" not in context_json
    assert "Unrelated customer gap." not in context_json
    assert unrelated_profile.id not in context_json
    assert "caprun_unrelated" not in context_json


def _piid_profile_with_source_limitation(
    *,
    profile_id: str = "piid_profile_FA8650_23_C_0001",
    limitation: str = "USAspending does not identify current transition scope.",
) -> PiidContractIntelligenceProfile:
    return PiidContractIntelligenceProfile(
        id=profile_id,
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
        award_baseline=PiidAwardBaseline(resolved_award_id="FA8650-23-C-0001"),
        gaps=(
            PiidProfileGap(
                field_key="transition_scope",
                category=PiidGapCategory.SOURCE_LIMITATION,
                source_limitation=limitation,
                recommended_enrichment_route="Review SAM.gov opportunity and source documents.",
            ),
        ),
        created_at="2026-05-18T10:01:00Z",
        updated_at="2026-05-18T10:01:00Z",
    )