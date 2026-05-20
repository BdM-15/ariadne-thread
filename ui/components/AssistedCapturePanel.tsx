"use client";

import { CheckCircle2, Route, ShieldCheck, Target } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

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
  packet_field_key?: string | null;
  route_kind: string;
  route_label: string;
  route_summary: string;
  autonomy_tier: string;
  requires_review: boolean;
  work_product_targets: string[];
  recommended_capability_chain: string[];
  capability_route_card: {
    id: string;
    title: string;
    capability_count: number;
    steps: Array<{
      capability_id: string;
      label: string;
      capability_type: string;
      executor_kind: string;
      output_target: string;
      status: string;
    }>;
  };
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
  capability_progress: {
    percent_complete: number;
    steps: Array<{
      capability_id: string;
      label: string;
      status: string;
    }>;
  };
  output: {
    id: string;
    title: string;
    route_kind: string;
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

type PacketFieldAnswerView = {
  field_key: string;
  value: string | null;
  evidence_status: string;
  confidence: number | null;
  source_draft_id: string | null;
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
  packet_field_answer: PacketFieldAnswerView | null;
  activation_run: { run_id: string } | null;
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
  initialGoalId,
  initialPacketFieldKey,
  initialPacketFieldLabel,
  opportunityId,
}: {
  goals: AssistedCaptureGoal[];
  initialGoalId?: string;
  initialPacketFieldKey?: string;
  initialPacketFieldLabel?: string;
  opportunityId: string;
}) {
  const router = useRouter();
  const [selectedGoalId, setSelectedGoalId] = useState(
    initialGoalId ?? goals[0]?.id ?? "",
  );
  const [targetPacketFieldKey, setTargetPacketFieldKey] = useState<
    string | null
  >(initialPacketFieldKey ?? null);
  const [autoRequestKey, setAutoRequestKey] = useState<string | null>(null);
  const [routes, setRoutes] = useState<AssistedRouteRecommendation[]>([]);
  const [runsByRouteId, setRunsByRouteId] = useState<
    Record<string, AssistedRouteRun>
  >({});
  const [updatesByOutputId, setUpdatesByOutputId] = useState<
    Record<string, WorkProductUpdateProjection[]>
  >({});
  const [packetAnswersByOutputId, setPacketAnswersByOutputId] = useState<
    Record<string, PacketFieldAnswerView | null>
  >({});
  const [provenanceByRouteId, setProvenanceByRouteId] = useState<
    Record<string, ProvenanceView>
  >({});
  const [reviewNotesByOutputId, setReviewNotesByOutputId] = useState<
    Record<string, string>
  >({});
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const targetPacketFieldLabel =
    initialPacketFieldLabel ?? targetPacketFieldKey;

  useEffect(() => {
    if (initialGoalId === undefined && initialPacketFieldKey === undefined) {
      return;
    }
    const goalId = initialGoalId ?? selectedGoalId;
    if (!goalId) {
      return;
    }
    const requestKey = `${opportunityId}:${goalId}:${initialPacketFieldKey ?? ""}`;
    if (autoRequestKey === requestKey) {
      return;
    }
    setAutoRequestKey(requestKey);
    requestRoutes(goalId, initialPacketFieldKey ?? null);
  }, [
    autoRequestKey,
    initialGoalId,
    initialPacketFieldKey,
    opportunityId,
    selectedGoalId,
  ]);

  function requestRoutes(goalId: string, packetFieldKey: string | null = null) {
    setSelectedGoalId(goalId);
    setTargetPacketFieldKey(packetFieldKey);
    setError(null);
    startTransition(async () => {
      const response = await fetch(
        `/api/production-command-center/opportunities/${opportunityId}/route-recommendations`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            goal_id: goalId,
            packet_field_key: packetFieldKey ?? undefined,
          }),
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
      setPacketAnswersByOutputId({});
      setProvenanceByRouteId({});
      setReviewNotesByOutputId({});
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

  function reviewOutput(
    output: AssistedRouteRun["output"],
    decision: "accept" | "reject",
  ) {
    setError(null);
    startTransition(async () => {
      const reviewerRationale =
        reviewNotesByOutputId[output.id]?.trim() ||
        (decision === "accept"
          ? "Accepted from Command Center review gate."
          : "Rejected from Command Center review gate.");
      const response = await fetch(
        `/api/production-command-center/route-outputs/${output.id}/review-decisions`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            decision,
            accepted_destination:
              decision === "accept"
                ? output.recommended_destination
                : undefined,
            reviewer_rationale: reviewerRationale,
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
        [output.id]: body.accepted_updates,
      }));
      setPacketAnswersByOutputId((currentAnswers) => ({
        ...currentAnswers,
        [output.id]: body.packet_field_answer,
      }));
      if (body.activation_run !== null) {
        router.refresh();
      }
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
    <section
      className="action-route-surface"
      aria-labelledby="action-route-title"
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
            Opportunity Action Paths
          </p>
          <h3 id="action-route-title" className="text-xl font-semibold">
            What should Ariadne advance next?
          </h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
            Pick the capture need. Ariadne prepares the next useful work and
            returns reviewable updates for the packet, call plan, action plan,
            research, or artifact it can improve.
          </p>
          {targetPacketFieldLabel !== null ? (
            <p className="mt-2 text-sm text-ariadne-signal">
              Target packet field: {formatLabel(targetPacketFieldLabel)}
            </p>
          ) : null}
        </div>
        <Target className="text-ariadne-cyan" size={20} aria-hidden />
      </div>

      <div
        className="goal-grid mt-5"
        role="listbox"
        aria-label="Assisted capture goals"
      >
        {goals.map((goal) => (
          <button
            aria-selected={selectedGoalId === goal.id}
            className="goal-button"
            disabled={isPending}
            key={goal.id}
            onClick={() => requestRoutes(goal.id)}
            type="button"
          >
            <span className="goal-title">{goal.label}</span>
            <span className="goal-description">{goal.description}</span>
            <span className="goal-target">
              Improves {formatLabel(goal.primary_work_product)}
            </span>
          </button>
        ))}
      </div>

      {isPending ? (
        <p className="mt-4 text-sm text-ariadne-signal">Routing...</p>
      ) : null}
      {error !== null ? (
        <p className="mt-4 text-sm text-ariadne-rose">{error}</p>
      ) : null}

      <div className="mt-5 space-y-4">
        {routes.map((routeRecommendation) => (
          <article className="route-card" key={routeRecommendation.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-ariadne-cyan">
                  Recommended action path
                </p>
                <h4 className="mt-1 text-sm font-semibold text-slate-100">
                  {routeRecommendation.route_label}
                </h4>
                {routeRecommendation.packet_field_key !== undefined &&
                routeRecommendation.packet_field_key !== null ? (
                  <p className="mt-1 text-xs text-ariadne-signal">
                    {formatLabel(routeRecommendation.packet_field_key)} field
                  </p>
                ) : null}
                <span className="route-kind-chip">
                  {formatLabel(routeRecommendation.route_kind)}
                </span>
              </div>
              <Route size={18} className="text-ariadne-copper" aria-hidden />
            </div>
            <dl className="route-context-grid">
              <div>
                <dt>Need it advances</dt>
                <dd>{routeRecommendation.route_summary}</dd>
              </div>
              <div>
                <dt>Route kind</dt>
                <dd>
                  <span className="chip">
                    {formatLabel(routeRecommendation.route_kind)}
                  </span>
                </dd>
              </div>
              <div>
                <dt>Output lands in</dt>
                <dd className="chip-list">
                  {routeRecommendation.work_product_targets.map((target) => (
                    <span className="chip" key={target}>
                      {formatLabel(target)}
                    </span>
                  ))}
                </dd>
              </div>
              <div>
                <dt>Inputs Ariadne will use</dt>
                <dd className="chip-list">
                  {routeRecommendation.input_refs.map((inputRef) => (
                    <span className="source-chip" key={inputRef}>
                      {formatReferenceLabel(inputRef)}
                    </span>
                  ))}
                </dd>
              </div>
            </dl>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
              <ShieldCheck size={14} aria-hidden />
              <span>{formatLabel(routeRecommendation.autonomy_tier)}</span>
            </div>
            <div className="capability-chain">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                {routeRecommendation.capability_route_card.capability_count}{" "}
                steps
              </p>
              {routeRecommendation.capability_route_card.steps.map((step) => (
                <div className="capability-step" key={step.capability_id}>
                  <span>{step.label}</span>
                  <span>{formatLabel(step.status)}</span>
                </div>
              ))}
            </div>
            <div className="route-action-row">
              <button
                className="command-button route-run-button"
                disabled={isPending}
                onClick={() => runRoute(routeRecommendation.id)}
                type="button"
              >
                Let Ariadne prepare this
              </button>
              <button
                className="command-button route-run-button"
                disabled={isPending}
                onClick={() => inspectProvenance(routeRecommendation.id)}
                type="button"
              >
                Show reasoning and sources
              </button>
            </div>
            {runsByRouteId[routeRecommendation.id] !== undefined ? (
              <div className="run-output">
                <p className="text-xs uppercase tracking-[0.16em] text-ariadne-cyan">
                  {formatLabel(runsByRouteId[routeRecommendation.id].status)}
                </p>
                <h5 className="mt-1 text-sm font-semibold">
                  {runsByRouteId[routeRecommendation.id].output.title}
                </h5>
                <span className="route-kind-chip">
                  {formatLabel(
                    runsByRouteId[routeRecommendation.id].output.route_kind,
                  )}
                </span>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {runsByRouteId[routeRecommendation.id].output.summary}
                </p>
                <div className="progress-bar" aria-label="Capability progress">
                  <span
                    style={{
                      width: `${runsByRouteId[routeRecommendation.id].capability_progress.percent_complete}%`,
                    }}
                  />
                </div>
                <div className="review-gate">
                  <p className="text-xs uppercase tracking-[0.16em] text-ariadne-signal">
                    Human review required
                  </p>
                  <textarea
                    aria-label="Reviewer rationale"
                    className="review-textarea"
                    onChange={(event) =>
                      setReviewNotesByOutputId((currentNotes) => ({
                        ...currentNotes,
                        [runsByRouteId[routeRecommendation.id].output.id]:
                          event.target.value,
                      }))
                    }
                    placeholder="Reviewer rationale"
                    rows={3}
                    value={
                      reviewNotesByOutputId[
                        runsByRouteId[routeRecommendation.id].output.id
                      ] ?? ""
                    }
                  />
                  <div className="review-action-row">
                    <button
                      className="command-button"
                      disabled={isPending}
                      onClick={() =>
                        reviewOutput(
                          runsByRouteId[routeRecommendation.id].output,
                          "accept",
                        )
                      }
                      type="button"
                    >
                      Accept into work products
                    </button>
                    <button
                      className="command-button danger"
                      disabled={isPending}
                      onClick={() =>
                        reviewOutput(
                          runsByRouteId[routeRecommendation.id].output,
                          "reject",
                        )
                      }
                      type="button"
                    >
                      Reject output
                    </button>
                  </div>
                </div>
                {updatesByOutputId[
                  runsByRouteId[routeRecommendation.id].output.id
                ] !== undefined ? (
                  <div className="mt-3 space-y-2">
                    {updatesByOutputId[
                      runsByRouteId[routeRecommendation.id].output.id
                    ].map((update) => (
                      <div className="update-projection" key={update.id}>
                        <div>
                          <span>{formatLabel(update.destination)}</span>
                          <p>{update.before_summary}</p>
                          <p>{update.after_summary}</p>
                        </div>
                        <span>{formatLabel(update.state)}</span>
                      </div>
                    ))}
                  </div>
                ) : null}
                {packetAnswersByOutputId[
                  runsByRouteId[routeRecommendation.id].output.id
                ] !== undefined &&
                packetAnswersByOutputId[
                  runsByRouteId[routeRecommendation.id].output.id
                ] !== null ? (
                  <div className="mt-3 flex items-start gap-2 rounded-md border border-ariadne-cyan/30 bg-ariadne-cyan/10 p-3 text-sm text-slate-200">
                    <CheckCircle2
                      className="mt-0.5 text-ariadne-cyan"
                      size={15}
                      aria-hidden
                    />
                    <div>
                      <p className="font-semibold text-slate-100">
                        Packet answer created:{" "}
                        {formatLabel(
                          packetAnswersByOutputId[
                            runsByRouteId[routeRecommendation.id].output.id
                          ]?.field_key ?? "packet_field",
                        )}
                      </p>
                      <p className="mt-1 text-xs text-slate-300">
                        {formatLabel(
                          packetAnswersByOutputId[
                            runsByRouteId[routeRecommendation.id].output.id
                          ]?.evidence_status ?? "assumption",
                        )}{" "}
                        evidence / source{" "}
                        {formatReferenceLabel(
                          packetAnswersByOutputId[
                            runsByRouteId[routeRecommendation.id].output.id
                          ]?.source_draft_id ?? "route_output",
                        )}
                      </p>
                      <a
                        className="mt-2 inline-flex text-xs font-semibold text-ariadne-cyan hover:text-slate-100"
                        href={`/?opportunity_id=${encodeURIComponent(opportunityId)}&mode=packet`}
                      >
                        Open updated packet roadmap
                      </a>
                    </div>
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
                    <dd>
                      {provenanceByRouteId[
                        routeRecommendation.id
                      ].input_refs.join(", ")}
                    </dd>
                  </div>
                  <div>
                    <dt>Capability chain</dt>
                    <dd>
                      {provenanceByRouteId[
                        routeRecommendation.id
                      ].capability_chain.join(" -> ")}
                    </dd>
                  </div>
                  <div>
                    <dt>Reasoning</dt>
                    <dd>
                      {provenanceByRouteId[routeRecommendation.id].reasoning[0]}
                    </dd>
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
    .replace(/^ev_/, "")
    .replace(/\./g, "_")
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatReferenceLabel(value: string): string {
  const labels: Record<string, string> = {
    "packet.customer_context": "Customer context in the Living Packet",
    "packet.risks_and_gaps": "Open packet risks and gaps",
    "evidence.ev_customer_call": "Customer call evidence",
    "action_plan.customer_insight_backfill": "Customer insight backfill action",
    action_plan: "Current capture action plan",
    "packet.gaps": "Open packet gaps",
    capability_catalog: "Available Ariadne capabilities",
  };

  return labels[value] ?? formatLabel(value);
}
