"use client";

import { Route, ShieldCheck, Target } from "lucide-react";
import { useState, useTransition } from "react";

export type AssistedCaptureGoal = {
  id: string;
  label: string;
  description: string;
  primary_work_product: string;
  work_product_targets: string[];
};

type AssistedRouteRecommendation = {
  id: string;
  opportunity_id: string;
  goal_id: string;
  route_label: string;
  route_summary: string;
  autonomy_tier: string;
  requires_review: boolean;
  work_product_targets: string[];
  recommended_capability_chain: string[];
  input_refs: string[];
  reasoning: string[];
  status: string;
};

type AssistedRouteRun = {
  id: string;
  status: string;
  executor_kind: string;
  network_required: boolean;
  model_required: boolean;
  output: {
    id: string;
    title: string;
    summary: string;
    recommended_destination: string;
    review_state: string;
  };
};

type WorkProductUpdateProjection = {
  id: string;
  destination: string;
  state: string;
  before_summary: string;
  after_summary: string;
};

type RecommendationResponse = {
  goal: AssistedCaptureGoal;
  recommendations: AssistedRouteRecommendation[];
};

type RouteRunResponse = {
  run: AssistedRouteRun;
};

type ReviewDecisionResponse = {
  accepted_updates: WorkProductUpdateProjection[];
  output: AssistedRouteRun["output"];
};

type ProvenanceView = {
  input_refs: string[];
  capability_chain: string[];
  reasoning: string[];
  run: AssistedRouteRun | null;
  output: AssistedRouteRun["output"] | null;
  review_decisions: Array<{ id: string; review_gate: string }>;
  work_product_updates: WorkProductUpdateProjection[];
};

type ProvenanceResponse = {
  provenance: ProvenanceView;
};

export function AssistedCapturePanel({
  goals,
  opportunityId,
}: {
  goals: AssistedCaptureGoal[];
  opportunityId: string;
}) {
  const [selectedGoalId, setSelectedGoalId] = useState(goals[0]?.id ?? "");
  const [routes, setRoutes] = useState<AssistedRouteRecommendation[]>([]);
  const [runsByRouteId, setRunsByRouteId] = useState<Record<string, AssistedRouteRun>>({});
  const [updatesByOutputId, setUpdatesByOutputId] = useState<Record<string, WorkProductUpdateProjection[]>>({});
  const [provenanceByRouteId, setProvenanceByRouteId] = useState<Record<string, ProvenanceView>>({});
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function requestRoutes(goalId: string) {
    setSelectedGoalId(goalId);
    setError(null);
    startTransition(async () => {
      const response = await fetch(
        `/api/production-command-center/opportunities/${opportunityId}/route-recommendations`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ goal_id: goalId }),
        },
      );
      if (!response.ok) {
        setError("Route recommendations are unavailable.");
        setRoutes([]);
        return;
      }
      const body = (await response.json()) as RecommendationResponse;
      setRoutes(body.recommendations);
      setRunsByRouteId({});
      setUpdatesByOutputId({});
      setProvenanceByRouteId({});
    });
  }

  function runRoute(recommendationId: string) {
    setError(null);
    startTransition(async () => {
      const response = await fetch(
        `/api/production-command-center/routes/${recommendationId}/runs`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ approved: true }),
        },
      );
      if (!response.ok) {
        setError("Route execution is unavailable.");
        return;
      }
      const body = (await response.json()) as RouteRunResponse;
      setRunsByRouteId((currentRuns) => ({
        ...currentRuns,
        [recommendationId]: body.run,
      }));
    });
  }

  function acceptOutput(outputId: string) {
    setError(null);
    startTransition(async () => {
      const response = await fetch(
        `/api/production-command-center/route-outputs/${outputId}/review-decisions`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            decision: "accept",
            accepted_destination: "call_plan",
            reviewer_rationale: "Accepted from Command Center review gate.",
          }),
        },
      );
      if (!response.ok) {
        setError("Route output review is unavailable.");
        return;
      }
      const body = (await response.json()) as ReviewDecisionResponse;
      setUpdatesByOutputId((currentUpdates) => ({
        ...currentUpdates,
        [outputId]: body.accepted_updates,
      }));
    });
  }

  function inspectProvenance(recommendationId: string) {
    setError(null);
    startTransition(async () => {
      const response = await fetch(
        `/api/production-command-center/routes/${recommendationId}/provenance`,
        { cache: "no-store" },
      );
      if (!response.ok) {
        setError("Route provenance is unavailable.");
        return;
      }
      const body = (await response.json()) as ProvenanceResponse;
      setProvenanceByRouteId((currentProvenance) => ({
        ...currentProvenance,
        [recommendationId]: body.provenance,
      }));
    });
  }

  return (
    <section className="mt-7 border-t border-ariadne-line pt-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Route</p>
          <h3 className="text-base font-semibold">Assisted Capture</h3>
        </div>
        <Target className="text-ariadne-cyan" size={20} aria-hidden />
      </div>

      <div className="mt-4 space-y-2" role="listbox" aria-label="Assisted capture goals">
        {goals.map((goal) => (
          <button
            aria-selected={selectedGoalId === goal.id}
            className="goal-button"
            key={goal.id}
            onClick={() => requestRoutes(goal.id)}
            type="button"
          >
            <span>{goal.label}</span>
            <span>{formatLabel(goal.primary_work_product)}</span>
          </button>
        ))}
      </div>

      {isPending ? <p className="mt-4 text-sm text-ariadne-signal">Routing...</p> : null}
      {error !== null ? <p className="mt-4 text-sm text-ariadne-rose">{error}</p> : null}

      <div className="mt-4 space-y-3">
        {routes.map((routeRecommendation) => (
          <article className="route-card" key={routeRecommendation.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-ariadne-cyan">Recommended</p>
                <h4 className="mt-1 text-sm font-semibold text-slate-100">
                  {routeRecommendation.route_label}
                </h4>
              </div>
              <Route size={18} className="text-ariadne-copper" aria-hidden />
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {routeRecommendation.route_summary}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {routeRecommendation.work_product_targets.map((target) => (
                <span className="chip" key={target}>{formatLabel(target)}</span>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
              <ShieldCheck size={14} aria-hidden />
              <span>{formatLabel(routeRecommendation.autonomy_tier)}</span>
            </div>
            <button
              className="command-button route-run-button"
              onClick={() => runRoute(routeRecommendation.id)}
              type="button"
            >
              Run deterministic route
            </button>
            <button
              className="command-button route-run-button"
              onClick={() => inspectProvenance(routeRecommendation.id)}
              type="button"
            >
              Inspect provenance
            </button>
            {runsByRouteId[routeRecommendation.id] !== undefined ? (
              <div className="run-output">
                <p className="text-xs uppercase tracking-[0.16em] text-ariadne-cyan">
                  {formatLabel(runsByRouteId[routeRecommendation.id].status)}
                </p>
                <h5 className="mt-1 text-sm font-semibold">
                  {runsByRouteId[routeRecommendation.id].output.title}
                </h5>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {runsByRouteId[routeRecommendation.id].output.summary}
                </p>
                <button
                  className="command-button route-run-button"
                  onClick={() => acceptOutput(runsByRouteId[routeRecommendation.id].output.id)}
                  type="button"
                >
                  Accept into work products
                </button>
                {updatesByOutputId[runsByRouteId[routeRecommendation.id].output.id] !== undefined ? (
                  <div className="mt-3 space-y-2">
                    {updatesByOutputId[runsByRouteId[routeRecommendation.id].output.id].map((update) => (
                      <div className="update-projection" key={update.id}>
                        <span>{formatLabel(update.destination)}</span>
                        <span>{formatLabel(update.state)}</span>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
            {provenanceByRouteId[routeRecommendation.id] !== undefined ? (
              <div className="provenance-panel">
                <p className="text-xs uppercase tracking-[0.16em] text-ariadne-cyan">
                  Provenance
                </p>
                <dl className="mt-2 space-y-2 text-xs text-slate-300">
                  <div>
                    <dt>Inputs</dt>
                    <dd>{provenanceByRouteId[routeRecommendation.id].input_refs.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>Capability chain</dt>
                    <dd>{provenanceByRouteId[routeRecommendation.id].capability_chain.join(" -> ")}</dd>
                  </div>
                  <div>
                    <dt>Reasoning</dt>
                    <dd>{provenanceByRouteId[routeRecommendation.id].reasoning[0]}</dd>
                  </div>
                </dl>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}