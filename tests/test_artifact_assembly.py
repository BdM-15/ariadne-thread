from ariadne.artifact_assembly import (
    ArtifactAssemblyStore,
    ArtifactBlockSupportClassification,
    ArtifactContentBlockKind,
    ArtifactDraftReadiness,
    ArtifactDraftType,
    ArtifactSourceUse,
    assemble_milestone_packet_draft,
    create_artifact_source_package_from_context,
    milestone_packet_draft_capability_contract,
    summarize_artifact_source_package,
)
from ariadne.evidence import LocalEvidenceStore, create_source_evidence
from ariadne.opportunities import EntryContext, EntryReason, LifecycleState, create_opportunity
from ariadne.packet_knowledge import PacketFieldAnswerStatus, create_packet_field_answer
from ariadne.packets import EvidenceStatus
from ariadne.structured_knowledge import (
    KnowledgeContextItem,
    KnowledgeContextSection,
    KnowledgeGapSummary,
    KnowledgeRecordKind,
    KnowledgeSourceLimitation,
    KnowledgeTrustState,
    OpportunityKnowledgeContextView,
    get_opportunity_knowledge_context,
)


def test_creates_source_package_from_opportunity_knowledge_context(tmp_path) -> None:
    context = OpportunityKnowledgeContextView(
        opportunity_id="opp-aflcmc-recompete",
        trusted_context=KnowledgeContextSection(
            count=1,
            items=(
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                    record_id="ev_transition_risk",
                    title="Transition risk evidence",
                    summary="Customer flagged transition risk on the recompete.",
                    trust_state=KnowledgeTrustState.TRUSTED,
                    status_label="trusted",
                    related_connection_count=2,
                ),
            ),
        ),
        reviewable_context=KnowledgeContextSection(
            count=1,
            items=(
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                    record_id="packet_field_answer:opp-aflcmc-recompete:primary_scope",
                    title="Packet field: primary_scope",
                    summary="Need validated transition scope before gate review.",
                    trust_state=KnowledgeTrustState.REVIEWABLE,
                    status_label="reviewable",
                ),
            ),
        ),
        gaps=(
            KnowledgeGapSummary(
                record_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                record_id="packet_field_answer:opp-aflcmc-recompete:primary_scope",
                summary="Need validated transition scope before gate review.",
                command_id="review_packet_gap",
            ),
        ),
        source_limitations=(
            KnowledgeSourceLimitation(
                record_kind=KnowledgeRecordKind.PIID_PROFILE,
                record_id="piid_profile_FA8650_23_C_0001",
                summary="USAspending does not identify current transition scope.",
            ),
        ),
    )
    store = ArtifactAssemblyStore(tmp_path / "artifact-assembly")

    package = create_artifact_source_package_from_context(
        context=context,
        store=store,
        created_at="2026-05-19T20:45:00Z",
    )

    assert package.opportunity_id == "opp-aflcmc-recompete"
    assert package.source_context == "opportunity_knowledge_context"
    assert package.trusted_refs[0].record_id == "ev_transition_risk"
    assert package.trusted_refs[0].trust_state is KnowledgeTrustState.TRUSTED
    assert package.trusted_refs[0].allowed_use is ArtifactSourceUse.DIRECT_SUPPORT
    assert package.reviewable_refs[0].record_id == (
        "packet_field_answer:opp-aflcmc-recompete:primary_scope"
    )
    assert package.reviewable_refs[0].trust_state is KnowledgeTrustState.REVIEWABLE
    assert package.reviewable_refs[0].allowed_use is ArtifactSourceUse.NEEDS_REVIEW
    assert package.gap_refs[0].allowed_use is ArtifactSourceUse.GAP
    assert package.source_limitations[0].allowed_use is ArtifactSourceUse.LIMITATION
    assert package.assumptions == ()
    assert package.pending_review_refs == (
        "packet_field_answer:opp-aflcmc-recompete:primary_scope",
        "piid_profile_FA8650_23_C_0001",
    )
    assert store.read_source_package(package.package_id) == package
    assert store.list_source_packages(opportunity_id="opp-aflcmc-recompete") == [
        package
    ]
    assert summarize_artifact_source_package(package).trusted_count == 1
    assert summarize_artifact_source_package(package).reviewable_count == 1
    assert "Customer flagged transition risk" in package.model_dump_json()
    assert "unrelated" not in package.model_dump_json()


def test_source_package_uses_filtered_opportunity_knowledge_context(tmp_path) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs an artifact source package.",
        ),
    )
    unrelated_opportunity = create_opportunity(
        name="opp-unrelated",
        entry_context=EntryContext(
            reason=EntryReason.NEW_LEAD,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Separate lead should not feed this artifact.",
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
    evidence_store.write(
        create_source_evidence(
            evidence_id="ev_unrelated_pricing",
            content="Unrelated opportunity needs pricing research.",
            source_ref="meeting:2026-05-16",
            opportunity_id=unrelated_opportunity.name,
        )
    )
    packet_gap = create_packet_field_answer(
        field_key="primary_scope",
        opportunity_id=opportunity.name,
        status=PacketFieldAnswerStatus.GAP,
        evidence_status=EvidenceStatus.GAP,
        evidence_ids=(trusted_evidence.id,),
        gap_summary="Need validated transition scope before gate review.",
    )
    unrelated_packet_gap = create_packet_field_answer(
        field_key="price_to_win",
        opportunity_id=unrelated_opportunity.name,
        status=PacketFieldAnswerStatus.GAP,
        evidence_status=EvidenceStatus.GAP,
        gap_summary="Unrelated price-to-win gap.",
    )
    context = get_opportunity_knowledge_context(
        opportunity_id=opportunity.name,
        opportunities=(opportunity, unrelated_opportunity),
        evidence_store=evidence_store,
        packet_field_answers=(packet_gap, unrelated_packet_gap),
    )
    store = ArtifactAssemblyStore(tmp_path / "artifact-assembly")

    package = create_artifact_source_package_from_context(
        context=context,
        store=store,
        created_at="2026-05-19T21:00:00Z",
    )

    package_json = package.model_dump_json()
    assert trusted_evidence.id in package_json
    assert "packet_field_answer:opp-aflcmc-recompete:primary_scope" in package_json
    assert "ev_unrelated_pricing" not in package_json
    assert "opp-unrelated" not in package_json
    assert "price_to_win" not in package_json


def test_assembles_milestone_packet_draft_shell_from_source_package(tmp_path) -> None:
    context = OpportunityKnowledgeContextView(
        opportunity_id="opp-aflcmc-recompete",
        trusted_context=KnowledgeContextSection(
            count=1,
            items=(
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                    record_id="ev_transition_risk",
                    title="Transition risk evidence",
                    summary="Customer flagged transition risk on the recompete.",
                    trust_state=KnowledgeTrustState.TRUSTED,
                    status_label="trusted",
                ),
            ),
        ),
        reviewable_context=KnowledgeContextSection(
            count=1,
            items=(
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                    record_id="packet_field_answer:opp-aflcmc-recompete:primary_scope",
                    title="Packet field: primary_scope",
                    summary="Need validated transition scope before gate review.",
                    trust_state=KnowledgeTrustState.REVIEWABLE,
                    status_label="reviewable",
                ),
            ),
        ),
        gaps=(
            KnowledgeGapSummary(
                record_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                record_id="packet_field_answer:opp-aflcmc-recompete:primary_scope",
                summary="Need validated transition scope before gate review.",
                command_id="review_packet_gap",
            ),
        ),
        source_limitations=(
            KnowledgeSourceLimitation(
                record_kind=KnowledgeRecordKind.PIID_PROFILE,
                record_id="piid_profile_FA8650_23_C_0001",
                summary="USAspending does not identify current transition scope.",
            ),
        ),
    )
    store = ArtifactAssemblyStore(tmp_path / "artifact-assembly")
    source_package = create_artifact_source_package_from_context(
        context=context,
        store=store,
        created_at="2026-05-19T20:45:00Z",
    )

    draft = assemble_milestone_packet_draft(
        source_package_id=source_package.package_id,
        store=store,
        assembled_at="2026-05-19T21:15:00Z",
    )

    assert draft.artifact_type is ArtifactDraftType.MILESTONE_DECISION_BRIEFING_PACKET
    assert draft.opportunity_id == "opp-aflcmc-recompete"
    assert draft.source_package_id == source_package.package_id
    assert draft.readiness_state is ArtifactDraftReadiness.NEEDS_REVIEW
    assert draft.provenance.source_package_id == source_package.package_id
    assert draft.provenance.capability_id == "artifact_assembly.milestone_packet_draft_shell"
    assert draft.provenance.assembly_mode == "deterministic_non_llm"
    assert draft.provenance.model_assist_used is False
    assert draft.renderer_readiness.preview_ready is False
    assert draft.renderer_readiness.export_ready is False
    assert draft.renderer_readiness.renderer_invoked is False
    assert len(draft.sections) == 8
    assert draft.sections[0].blocks[0].block_kind is ArtifactContentBlockKind.NARRATIVE
    assert "ev_transition_risk" in draft.model_dump_json()
    assert "packet_field_answer:opp-aflcmc-recompete:primary_scope" in draft.model_dump_json()
    assert "piid_profile_FA8650_23_C_0001" in draft.model_dump_json()
    assert store.read_artifact_draft(draft.draft_id) == draft


def test_refreshes_milestone_packet_draft_shell_without_new_identity(tmp_path) -> None:
    store = ArtifactAssemblyStore(tmp_path / "artifact-assembly")
    first_package = create_artifact_source_package_from_context(
        context=OpportunityKnowledgeContextView(
            opportunity_id="opp-aflcmc-recompete",
            trusted_context=KnowledgeContextSection(
                count=1,
                items=(
                    KnowledgeContextItem(
                        record_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                        record_id="ev_transition_risk",
                        title="Transition risk evidence",
                        summary="Customer flagged transition risk on the recompete.",
                        trust_state=KnowledgeTrustState.TRUSTED,
                        status_label="trusted",
                    ),
                ),
            ),
            reviewable_context=KnowledgeContextSection(count=0, items=()),
        ),
        store=store,
        created_at="2026-05-19T20:45:00Z",
    )
    first_draft = assemble_milestone_packet_draft(
        source_package_id=first_package.package_id,
        store=store,
        assembled_at="2026-05-19T21:15:00Z",
    )
    refreshed_package = create_artifact_source_package_from_context(
        context=OpportunityKnowledgeContextView(
            opportunity_id="opp-aflcmc-recompete",
            trusted_context=KnowledgeContextSection(
                count=2,
                items=(
                    KnowledgeContextItem(
                        record_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                        record_id="ev_transition_risk",
                        title="Transition risk evidence",
                        summary="Customer flagged transition risk on the recompete.",
                        trust_state=KnowledgeTrustState.TRUSTED,
                        status_label="trusted",
                    ),
                    KnowledgeContextItem(
                        record_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                        record_id="ev_validated_scope",
                        title="Validated scope evidence",
                        summary="Customer validated transition scope for the gate.",
                        trust_state=KnowledgeTrustState.TRUSTED,
                        status_label="trusted",
                    ),
                ),
            ),
            reviewable_context=KnowledgeContextSection(count=0, items=()),
        ),
        store=store,
        created_at="2026-05-19T22:00:00Z",
    )

    refreshed_draft = assemble_milestone_packet_draft(
        source_package_id=refreshed_package.package_id,
        store=store,
        assembled_at="2026-05-19T22:05:00Z",
    )

    assert refreshed_draft.draft_id == first_draft.draft_id
    assert refreshed_draft.created_at == first_draft.created_at
    assert refreshed_draft.refreshed_at == "2026-05-19T22:05:00Z"
    assert "ev_validated_scope" in refreshed_draft.model_dump_json()
    assert store.list_artifact_drafts(opportunity_id="opp-aflcmc-recompete") == [
        refreshed_draft
    ]


def test_milestone_packet_draft_contract_is_capability_contribution_boundary() -> None:
    contract = milestone_packet_draft_capability_contract()

    assert contract.capability_id == "artifact_assembly.milestone_packet_draft_shell"
    assert contract.product_workflow == "milestone_decision_briefing_packet"
    assert "renderer-neutral draft sections" in contract.contribution_boundary
    assert contract.third_party_installation_required is False
    assert contract.skill_chain_execution_required is False
    assert contract.renderer_execution_allowed is False


def test_populates_packet_sections_with_source_backed_content_blocks(tmp_path) -> None:
    context = OpportunityKnowledgeContextView(
        opportunity_id="opp-aflcmc-recompete",
        trusted_context=KnowledgeContextSection(
            count=3,
            items=(
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                    record_id="ev_transition_risk",
                    title="Transition risk evidence",
                    summary="Customer flagged transition risk on the recompete.",
                    trust_state=KnowledgeTrustState.TRUSTED,
                    status_label="trusted",
                ),
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.ACTION_PLAN_ITEM,
                    record_id="action_validate_scope",
                    title="Validate transition scope",
                    summary="Confirm transition workload with customer before gate.",
                    trust_state=KnowledgeTrustState.TRUSTED,
                    status_label="trusted",
                ),
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.CAPABILITY_RUN_OUTPUT,
                    record_id="capability_output_requirements_fit",
                    title="Requirements fit output",
                    summary="Capability run found strong incumbent-transition fit.",
                    trust_state=KnowledgeTrustState.TRUSTED,
                    status_label="trusted",
                ),
            ),
        ),
        reviewable_context=KnowledgeContextSection(
            count=3,
            items=(
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                    record_id="packet_field_answer:opp-aflcmc-recompete:primary_scope",
                    title="Packet field: primary_scope",
                    summary="Need validated transition scope before gate review.",
                    trust_state=KnowledgeTrustState.REVIEWABLE,
                    status_label="reviewable",
                ),
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.PIID_PROFILE,
                    record_id="piid_profile_FA8650_23_C_0001",
                    title="PIID profile",
                    summary="USAspending suggests recompete timing but not final scope.",
                    trust_state=KnowledgeTrustState.REVIEWABLE,
                    status_label="source limitation",
                ),
                KnowledgeContextItem(
                    record_kind=KnowledgeRecordKind.SAM_GOV_PROFILE,
                    record_id="sam_profile_aflcmc_transition",
                    title="SAM.gov profile",
                    summary="SAM.gov discovery found likely related notice.",
                    trust_state=KnowledgeTrustState.REVIEWABLE,
                    status_label="reviewable",
                ),
            ),
        ),
        gaps=(
            KnowledgeGapSummary(
                record_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                record_id="packet_field_answer:opp-aflcmc-recompete:primary_scope",
                summary="Need validated transition scope before gate review.",
                command_id="review_packet_gap",
            ),
        ),
        source_limitations=(
            KnowledgeSourceLimitation(
                record_kind=KnowledgeRecordKind.PIID_PROFILE,
                record_id="piid_profile_FA8650_23_C_0001",
                summary="USAspending does not identify current transition scope.",
            ),
        ),
    )
    store = ArtifactAssemblyStore(tmp_path / "artifact-assembly")
    source_package = create_artifact_source_package_from_context(
        context=context,
        store=store,
        created_at="2026-05-19T20:45:00Z",
        assumptions=("Transition workload remains comparable until customer validates scope.",),
    )

    draft = assemble_milestone_packet_draft(
        source_package_id=source_package.package_id,
        store=store,
        assembled_at="2026-05-19T21:15:00Z",
    )

    overview = draft.sections[0]
    blocks_by_kind = {block.block_kind: block for block in overview.blocks}
    assert set(blocks_by_kind) >= {
        ArtifactContentBlockKind.NARRATIVE,
        ArtifactContentBlockKind.DECISION_SUMMARY,
        ArtifactContentBlockKind.EVIDENCE_TABLE,
        ArtifactContentBlockKind.ACTION_LIST,
        ArtifactContentBlockKind.ASSUMPTION_LIST,
        ArtifactContentBlockKind.GAP_LIST,
        ArtifactContentBlockKind.SOURCE_APPENDIX,
    }
    evidence_table = blocks_by_kind[ArtifactContentBlockKind.EVIDENCE_TABLE]
    assert evidence_table.support_classification is ArtifactBlockSupportClassification.TRUSTED_SUPPORT
    assert evidence_table.source_ref_ids == (
        "ev_transition_risk",
        "action_validate_scope",
        "capability_output_requirements_fit",
    )
    assert evidence_table.reviewable_ref_ids == ()
    assert evidence_table.content_data["rows"][0]["record_kind"] == "evidence_item"
    source_appendix = blocks_by_kind[ArtifactContentBlockKind.SOURCE_APPENDIX]
    assert source_appendix.support_classification is ArtifactBlockSupportClassification.MIXED_SUPPORT
    assert "packet_field_answer:opp-aflcmc-recompete:primary_scope" in source_appendix.reviewable_ref_ids
    assert "sam_profile_aflcmc_transition" in source_appendix.reviewable_ref_ids
    gap_list = blocks_by_kind[ArtifactContentBlockKind.GAP_LIST]
    assert gap_list.support_classification is ArtifactBlockSupportClassification.NEEDS_REVIEW
    assert gap_list.gap_ref_ids == ("packet_field_answer:opp-aflcmc-recompete:primary_scope",)
    assert gap_list.source_limitation_ref_ids == ("piid_profile_FA8650_23_C_0001",)
    assumption_list = blocks_by_kind[ArtifactContentBlockKind.ASSUMPTION_LIST]
    assert assumption_list.assumptions == (
        "Transition workload remains comparable until customer validates scope.",
    )
    assert draft.renderer_readiness.renderer_invoked is False
    assert "accepted" not in draft.model_dump_json()
