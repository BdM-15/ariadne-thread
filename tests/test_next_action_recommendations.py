from ariadne.capabilities import (
    CapabilityCatalog,
    CapabilityCatalogEntry,
    CapabilityMaturity,
    CapabilityType,
    CapabilityValidationStatus,
)
from ariadne.evidence import LocalEvidenceStore, create_source_evidence
from ariadne.next_action_recommendations import (
    ActionCapabilityRouteSupport,
    NextActionRecommendationReviewState,
    NextActionRecommendationStore,
    RecommendationAutonomyHint,
    recommend_next_capture_actions,
)
from ariadne.opportunities import EntryContext, EntryReason, LifecycleState, create_opportunity
from ariadne.packet_knowledge import PacketFieldAnswerStatus, create_packet_field_answer
from ariadne.packets import EvidenceStatus
from ariadne.structured_knowledge import get_opportunity_knowledge_context
from ariadne.structured_knowledge import (
    KnowledgeContextSection,
    KnowledgeRecordKind,
    KnowledgeSourceLimitation,
    OpportunityKnowledgeContextView,
)


def test_recommend_next_capture_actions_persists_gap_recommendation_with_route_and_snapshot(
    tmp_path,
) -> None:
    opportunity = create_opportunity(
        name="opp-aflcmc-recompete",
        entry_context=EntryContext(
            reason=EntryReason.RECOMPETE,
            starting_lifecycle_state=LifecycleState.IDENTIFIED,
            rationale="Known recompete needs deterministic next actions.",
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
        evidence_ids=(evidence.id,),
        gap_summary="Need validated transition scope before gate review.",
    )
    context = get_opportunity_knowledge_context(
        opportunity_id=opportunity.name,
        opportunities=(opportunity,),
        evidence_store=evidence_store,
        packet_field_answers=(packet_gap,),
    )
    catalog = CapabilityCatalog(
        entries=(
            CapabilityCatalogEntry(
                id="packet-gap-review",
                name="Packet Gap Review",
                description="Helps close packet gaps from trusted evidence.",
                capability_type=CapabilityType.WORKSPACE_SKILL,
                source_path=".github/skills/packet-gap-review/SKILL.md",
                maturity=CapabilityMaturity.STABLE,
                validation_status=CapabilityValidationStatus.TESTED,
                product_workflow_fit=("living_briefing_packet", "action_plan"),
            ),
        )
    )
    store = NextActionRecommendationStore(tmp_path / "recommendations")

    recommendations = recommend_next_capture_actions(
        context=context,
        capability_catalog=catalog,
        store=store,
        generated_at="2026-05-18T16:15:00Z",
    )

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.opportunity_id == opportunity.name
    assert recommendation.review_state is NextActionRecommendationReviewState.PENDING
    assert recommendation.autonomy_hint is RecommendationAutonomyHint.REVIEW_REQUIRED
    assert recommendation.title == "Resolve packet gap: primary_scope"
    assert recommendation.cause == "packet_gap"
    assert recommendation.capability_route.support is ActionCapabilityRouteSupport.AVAILABLE_TOOL
    assert recommendation.capability_route.capability_id == "packet-gap-review"
    assert recommendation.capability_route.next_command_id == "review_packet_gap"
    assert recommendation.context_snapshot.opportunity_id == opportunity.name
    assert recommendation.context_snapshot.gap_refs == (
        "packet_field_answer:opp-aflcmc-recompete:primary_scope",
    )
    assert recommendation.context_snapshot.trusted_refs == (evidence.id,)
    assert recommendation.context_snapshot.reviewable_refs == (
        "packet_field_answer:opp-aflcmc-recompete:primary_scope",
    )
    snapshot_json = recommendation.context_snapshot.model_dump_json()
    assert "StructuredKnowledgeIndex" not in snapshot_json
    assert "Customer flagged transition risk on the recompete." not in snapshot_json
    assert recommendation.created_action_plan_item_ids == ()
    assert recommendation.review_decisions == ()
    assert store.read(recommendation.id) == recommendation
    assert store.list(opportunity_id=opportunity.name) == [recommendation]


def test_recommend_next_capture_actions_routes_source_limitation_to_capability_gap(
    tmp_path,
) -> None:
    context = OpportunityKnowledgeContextView(
        opportunity_id="opp-aflcmc-recompete",
        trusted_context=KnowledgeContextSection(count=0),
        reviewable_context=KnowledgeContextSection(count=0),
        source_limitations=(
            KnowledgeSourceLimitation(
                record_kind=KnowledgeRecordKind.PIID_PROFILE,
                record_id="piid_profile_FA8650_23_C_0001",
                summary="USAspending does not identify current transition scope.",
            ),
        ),
    )
    store = NextActionRecommendationStore(tmp_path / "recommendations")

    recommendations = recommend_next_capture_actions(
        context=context,
        capability_catalog=CapabilityCatalog(entries=()),
        store=store,
        generated_at="2026-05-18T16:20:00Z",
    )

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.cause == "source_limitation"
    assert recommendation.title == "Review source limitation: piid_profile_FA8650_23_C_0001"
    assert recommendation.capability_route.support is ActionCapabilityRouteSupport.CAPABILITY_GAP
    assert recommendation.capability_route.capability_id is None
    assert recommendation.capability_route.next_command_id == "review_source_limitation"
    assert recommendation.context_snapshot.source_limitation_refs == (
        "piid_profile_FA8650_23_C_0001",
    )
    assert recommendation.context_snapshot.recommendation_cause == "source_limitation"
    assert recommendation.autonomy_hint is RecommendationAutonomyHint.REVIEW_REQUIRED
    assert store.list(review_state=NextActionRecommendationReviewState.PENDING) == [
        recommendation
    ]