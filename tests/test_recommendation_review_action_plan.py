import pytest

from ariadne.action_plans import ActionPlanItem, CaptureActionPlan
from ariadne.next_action_recommendations import (
    ActionCapabilityRoute,
    ActionCapabilityRouteSupport,
    NextActionRecommendation,
    NextActionRecommendationReviewState,
    NextActionRecommendationStore,
    RecommendationAutonomyHint,
    RecommendationContextSnapshot,
    accept_next_action_recommendation,
    discard_next_action_recommendation,
    edit_next_action_recommendation,
    refresh_stale_next_action_recommendation,
    route_next_action_recommendation,
    suggest_duplicate_action_plan_items,
)


def test_accept_next_action_recommendation_creates_action_plan_item_with_provenance(
    tmp_path,
) -> None:
    store = NextActionRecommendationStore(tmp_path / "recommendations")
    recommendation = store.write(_pending_packet_gap_recommendation())
    action_plan = CaptureActionPlan(opportunity_name="opp-aflcmc-recompete")

    result = accept_next_action_recommendation(
        store=store,
        recommendation_id=recommendation.id,
        action_plan=action_plan,
        reviewer_rationale="Accepted as next capture action.",
        decided_at="2026-05-18T16:45:00Z",
        action_item_id="ap_from_recommendation",
    )

    updated_recommendation = result.recommendation
    updated_plan = result.action_plan
    action_item = updated_plan.items[0]

    assert updated_recommendation.review_state is NextActionRecommendationReviewState.ACCEPTED
    assert updated_recommendation.created_action_plan_item_ids == (action_item.id,)
    assert updated_recommendation.review_decisions[0].decision == "accept"
    assert updated_recommendation.review_decisions[0].reviewer_rationale == (
        "Accepted as next capture action."
    )
    assert store.read(recommendation.id) == updated_recommendation

    assert action_item.id == "ap_from_recommendation"
    assert action_item.action == recommendation.title
    assert action_item.rationale == recommendation.description
    assert action_item.related_packet_field_key == "primary_scope"
    assert action_item.related_evidence_ids == ("ev_transition_risk",)
    assert action_item.gap_summary == "Need validated transition scope before gate review."
    assert action_item.review_status == "accepted"
    assert action_item.source_recommendation_id == recommendation.id
    assert action_item.recommendation_context_refs == (
        "ev_transition_risk",
        "packet_field_answer:opp-aflcmc-recompete:primary_scope",
    )
    assert action_item.recommendation_capability_route == "packet-gap-review"
    assert action_item.recommendation_review_decision_id == (
        updated_recommendation.review_decisions[0].decision_id
    )


def test_route_discard_and_edit_recommendations_preserve_review_history(tmp_path) -> None:
    store = NextActionRecommendationStore(tmp_path / "recommendations")
    routed = store.write(
        _pending_packet_gap_recommendation(recommendation_id="next_action_route")
    )
    discarded = store.write(
        _pending_packet_gap_recommendation(recommendation_id="next_action_discard")
    )
    edited = store.write(
        _pending_packet_gap_recommendation(recommendation_id="next_action_edit")
    )

    routed = route_next_action_recommendation(
        store=store,
        recommendation_id=routed.id,
        routed_destination="Document Intake Queue",
        reviewer_rationale="Needs source document review first.",
        decided_at="2026-05-18T16:50:00Z",
    )
    discarded = discard_next_action_recommendation(
        store=store,
        recommendation_id=discarded.id,
        reviewer_rationale="Not useful for this pursuit.",
        decided_at="2026-05-18T16:51:00Z",
    )
    edited = edit_next_action_recommendation(
        store=store,
        recommendation_id=edited.id,
        title="Validate transition scope with PM",
        description="Ask PM to confirm transition boundaries before gate review.",
        reviewer_rationale="Use user-facing wording.",
        decided_at="2026-05-18T16:52:00Z",
    )

    assert routed.review_state is NextActionRecommendationReviewState.ROUTED
    assert routed.review_decisions[0].decision == "route"
    assert routed.review_decisions[0].routed_destination == "Document Intake Queue"
    assert discarded.review_state is NextActionRecommendationReviewState.DISCARDED
    assert discarded.review_decisions[0].decision == "discard"
    assert edited.review_state is NextActionRecommendationReviewState.PENDING
    assert edited.title == "Validate transition scope with PM"
    assert edited.description == "Ask PM to confirm transition boundaries before gate review."
    assert edited.generated_title == "Resolve packet gap: primary_scope"
    assert edited.generated_description == "Need validated transition scope before gate review."
    assert edited.review_decisions[0].decision == "edit"


def test_stale_recommendation_refreshes_as_new_version_and_blocks_acceptance(
    tmp_path,
) -> None:
    store = NextActionRecommendationStore(tmp_path / "recommendations")
    recommendation = store.write(_pending_packet_gap_recommendation())
    stale = refresh_stale_next_action_recommendation(
        store=store,
        recommendation_id=recommendation.id,
        stale_reason="Packet field gained new evidence.",
        title="Resolve refreshed packet gap: primary_scope",
        description="Re-check transition scope after new evidence.",
        generated_at="2026-05-18T17:00:00Z",
    )

    old_version = store.read(recommendation.id)
    refreshed = store.read(stale.refreshed_recommendation.id)
    assert old_version.is_stale is True
    assert old_version.stale_reason == "Packet field gained new evidence."
    assert refreshed.version == 2
    assert refreshed.family_id == recommendation.id
    assert refreshed.supersedes_recommendation_id == recommendation.id
    assert refreshed.review_state is NextActionRecommendationReviewState.PENDING

    with pytest.raises(ValueError, match="stale recommendation must be refreshed"):
        accept_next_action_recommendation(
            store=store,
            recommendation_id=recommendation.id,
            action_plan=CaptureActionPlan(opportunity_name="opp-aflcmc-recompete"),
            reviewer_rationale="Trying old stale action.",
            decided_at="2026-05-18T17:01:00Z",
        )


def test_accept_recommendation_updates_existing_action_and_duplicate_suggestions_use_refs(
    tmp_path,
) -> None:
    store = NextActionRecommendationStore(tmp_path / "recommendations")
    recommendation = store.write(_pending_packet_gap_recommendation())
    matching_action = ActionPlanItem(
        id="ap_existing_scope",
        action="Different wording should still match by refs",
        rationale="Old rationale.",
        related_packet_field_key="primary_scope",
        related_evidence_ids=("ev_transition_risk",),
    )
    same_title_no_refs = ActionPlanItem(
        id="ap_same_title_no_refs",
        action=recommendation.title,
        rationale="Same title is not enough.",
    )
    plan = CaptureActionPlan(
        opportunity_name="opp-aflcmc-recompete",
        items=(matching_action, same_title_no_refs),
    )

    duplicate_suggestions = suggest_duplicate_action_plan_items(
        recommendation,
        plan,
    )
    assert [suggestion.action_item_id for suggestion in duplicate_suggestions] == [
        matching_action.id
    ]
    assert duplicate_suggestions[0].shared_refs == (
        "packet_field:primary_scope",
        "ev_transition_risk",
    )

    result = accept_next_action_recommendation(
        store=store,
        recommendation_id=recommendation.id,
        action_plan=plan,
        reviewer_rationale="Attach to existing scoped action.",
        decided_at="2026-05-18T17:05:00Z",
        existing_action_item_id=matching_action.id,
        update_existing_action=True,
    )

    updated_action = result.action_item
    assert len(result.action_plan.items) == 2
    assert updated_action.id == matching_action.id
    assert updated_action.action == recommendation.title
    assert updated_action.rationale == recommendation.description
    assert updated_action.review_edits == (
        "Previous action: Different wording should still match by refs",
        "Previous rationale: Old rationale.",
    )
    assert updated_action.source_recommendation_id == recommendation.id
    assert result.recommendation.created_action_plan_item_ids == (matching_action.id,)


def _pending_packet_gap_recommendation(
    *,
    recommendation_id: str = "next_action_packet_gap",
) -> NextActionRecommendation:
    return NextActionRecommendation(
        id=recommendation_id,
        opportunity_id="opp-aflcmc-recompete",
        title="Resolve packet gap: primary_scope",
        description="Need validated transition scope before gate review.",
        cause="packet_gap",
        rationale="Generated from deterministic Opportunity Knowledge Context gaps.",
        capability_route=ActionCapabilityRoute(
            support=ActionCapabilityRouteSupport.AVAILABLE_TOOL,
            next_command_id="review_packet_gap",
            next_command_label="Review packet gap",
            capability_id="packet-gap-review",
            product_workflow="living_briefing_packet",
            rationale="Capability Catalog contains a tested workflow fit.",
        ),
        context_snapshot=RecommendationContextSnapshot(
            opportunity_id="opp-aflcmc-recompete",
            trusted_refs=("ev_transition_risk",),
            reviewable_refs=("packet_field_answer:opp-aflcmc-recompete:primary_scope",),
            gap_refs=("packet_field_answer:opp-aflcmc-recompete:primary_scope",),
            recommendation_cause="packet_gap",
            capability_route_id="packet-gap-review",
            autonomy_hint=RecommendationAutonomyHint.REVIEW_REQUIRED,
        ),
        autonomy_hint=RecommendationAutonomyHint.REVIEW_REQUIRED,
        generated_at="2026-05-18T16:15:00Z",
    )