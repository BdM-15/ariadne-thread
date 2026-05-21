from ariadne.anomaly_route_recommender import (
    AnomalyRouteRecommendationRequest,
    build_anomaly_route_recommendation,
    run_anomaly_route_recommender_capability,
)
from ariadne.capability_runs import (
    CapabilityRunCapabilityType,
    CapabilityRunExecutorKind,
    CapabilityRunOutputReviewState,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.data_table_profiler import DataTableProfileRequest, build_data_table_profile


def test_anomaly_route_recommendation_creates_reviewable_action_route() -> None:
    profile = _sample_profile()

    recommendation = build_anomaly_route_recommendation(
        AnomalyRouteRecommendationRequest(
            data_table_profile=profile,
            source_output_id="output_data_table_profile_fixture",
            opportunity_id="opp-anomaly-route",
        )
    )

    assert recommendation.route_id == "create_data_quality_action_before_packet_use"
    assert recommendation.priority == "high"
    assert recommendation.review_destination == "Action Plan recommendation"
    assert recommendation.source_output_id == "output_data_table_profile_fixture"
    assert recommendation.anomalies
    assert recommendation.trusted_downstream_writes is False
    assert any("Reviewer must decide" in gap for gap in recommendation.gaps)


def test_anomaly_route_recommender_capability_run_stays_review_gated(tmp_path) -> None:
    store = CapabilityRunStore(tmp_path / "capability-runs")

    run = run_anomaly_route_recommender_capability(
        request=AnomalyRouteRecommendationRequest(
            data_table_profile=_sample_profile(),
            source_output_id="output_data_table_profile_fixture",
            opportunity_id="opp-anomaly-route",
            approval_basis="operator_approved_profile_followup",
        ),
        store=store,
    )

    assert run.capability_id == "anomaly-route-recommender"
    assert run.capability_type is CapabilityRunCapabilityType.SKILL
    assert run.executor_kind is CapabilityRunExecutorKind.DETERMINISTIC_PYTHON
    assert run.status is CapabilityRunStatus.NEEDS_REVIEW
    assert run.opportunity_id == "opp-anomaly-route"
    assert run.product_workflow == "action_plan"
    assert run.provenance["network_required"] is False
    assert run.provenance["model_required"] is False
    assert run.provenance["trusted_downstream_writes"] is False
    output = run.outputs[0]
    assert output.review_state is CapabilityRunOutputReviewState.PENDING
    assert output.recommended_destination == "Action Plan recommendation"
    assert output.provenance["anomaly_route_recommendation"]["priority"] == "high"
    assert output.provenance["trusted_downstream_writes"] is False
    assert store.read(run.run_id) == run


def _sample_profile():
    request = DataTableProfileRequest(
        table_label="Award history fixture",
        source_ref="fixture://award-history-table",
        source_refs=("fixture://award-history-table",),
        rows=(
            {"Contract ID": "FA123", "Vendor": "Acme Systems", "Obligated": 1000},
            {"Contract ID": "FA124", "Vendor": "", "Obligated": None},
            {"Contract ID": "FA124", "Vendor": "Beta Analytics", "Obligated": 1200.5},
        ),
    )
    return build_data_table_profile(request)