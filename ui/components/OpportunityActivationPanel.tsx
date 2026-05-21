"use client";

import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  LockKeyhole,
  RefreshCw,
  Route,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

type OpportunityActivationDigest = {
  coverage_gained: string[];
  review_ready_count: number;
  blocked_field_count: number;
  recommended_skill_chains: string[];
  approval_required_routes: string[];
  source_limitations: string[];
  next_best_actions: string[];
};

type PacketFieldActionItem = {
  field_key: string;
  label: string;
  question: string;
  section: string;
  value_kind: string;
  current_status: string;
  evidence_status: string;
  action_state: string;
  answer_paths: string[];
  required_milestone_gates?: string[];
  current_gate_required?: boolean;
  route_kind?: string;
  recommended_route: string;
  route_rationale: string;
  route_steps: string[];
  approval_gate: string | null;
  requires_review: boolean;
  approval_required: boolean;
  source_refs: string[];
  gap_summary: string | null;
  current_value: string | null;
};

type PacketFieldActionMatrix = {
  opportunity_id: string;
  current_milestone_gate?: string;
  fields: PacketFieldActionItem[];
  blocked_field_count: number;
  review_ready_count: number;
  answered_field_count: number;
  current_gate_field_count?: number;
  current_gate_blocked_count?: number;
  current_gate_review_ready_count?: number;
  current_gate_answered_count?: number;
  approval_required_count: number;
  source_ref_count: number;
};

type OpportunityActivationRunOutput = {
  output_id: string;
  field_key: string;
  title: string;
  summary: string;
  recommended_destination: string;
  recommended_route: string;
  review_state: string;
};

type FieldReviewDecision = "accept" | "edit" | "route" | "discard";

export type OpportunityActivationRun = {
  run_id: string;
  opportunity_id: string;
  trigger: string;
  status: string;
  review_state: string;
  packet_field_count: number;
  packet_field_gaps: number;
  activation_digest: OpportunityActivationDigest;
  packet_field_action_matrix: PacketFieldActionMatrix;
  outputs: OpportunityActivationRunOutput[];
  provenance: {
    trusted_downstream_writes?: boolean;
    network_required?: boolean;
    model_required?: boolean;
    executor?: string;
    [key: string]: unknown;
  };
  created_at: string;
  completed_at: string | null;
};

export function OpportunityActivationPanel({
  opportunityId,
  run,
  showDetail = false,
}: {
  opportunityId: string;
  run: OpportunityActivationRun | null;
  showDetail?: boolean;
}) {
  const router = useRouter();
  const [isRefreshing, startRefresh] = useTransition();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reviewingFieldKey, setReviewingFieldKey] = useState<string | null>(
    null,
  );
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [fieldNotes, setFieldNotes] = useState<Record<string, string>>({});
  const [fieldStatus, setFieldStatus] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const isBusy = isSubmitting || isRefreshing;
  const digest = run?.activation_digest;
  const matrix = run?.packet_field_action_matrix;
  const currentGateLabel = formatLabel(
    matrix?.current_milestone_gate ?? "milestone_1",
  );
  const activationFields = matrix?.fields ?? [];
  const currentGateFields = activationFields.filter(
    (field) => field.current_gate_required !== false,
  );
  const visibleGateFields =
    currentGateFields.length > 0 ? currentGateFields : activationFields;
  const supportedGateFields = visibleGateFields.filter(
    isActivationFieldAnswered,
  );
  const reviewReadyGateFields = visibleGateFields.filter(
    isActivationFieldReviewReady,
  );
  const outputByField = new Map(
    (run?.outputs ?? []).map((output) => [output.field_key, output]),
  );
  const trustedWrites = run?.provenance.trusted_downstream_writes === true;

  async function runActivation() {
    setError(null);
    setStatusMessage(null);
    setIsSubmitting(true);
    try {
      const response = await fetch(
        `/api/production-command-center/opportunities/${encodeURIComponent(opportunityId)}/activation-runs`,
        { method: "POST" },
      );
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Activation run failed.");
      }
      setStatusMessage("Activation run ready for review.");
      startRefresh(() => {
        router.refresh();
      });
    } catch (activationError) {
      setError(
        activationError instanceof Error
          ? activationError.message
          : "Activation run failed.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function reviewField(
    field: PacketFieldActionItem,
    decision: FieldReviewDecision,
  ) {
    if (run === null) {
      return;
    }
    const value = (
      fieldValues[field.field_key] ??
      field.current_value ??
      ""
    ).trim();
    const note = fieldNotes[field.field_key]?.trim();
    const reviewerRationale =
      note && note.length > 0
        ? note
        : `Reviewed ${field.label} from activation matrix.`;
    if ((decision === "accept" || decision === "edit") && !value) {
      setFieldStatus((current) => ({
        ...current,
        [field.field_key]: "Answer value required before accepting.",
      }));
      return;
    }

    setError(null);
    setStatusMessage(null);
    setReviewingFieldKey(field.field_key);
    setFieldStatus((current) => ({ ...current, [field.field_key]: "" }));
    try {
      const response = await fetch(
        `/api/production-command-center/activation-runs/${encodeURIComponent(run.run_id)}/fields/${encodeURIComponent(field.field_key)}/review-decisions`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            decision,
            value:
              decision === "accept" || decision === "edit" ? value : undefined,
            reviewer_rationale: reviewerRationale,
            routed_destination:
              decision === "route" ? "capture_research" : undefined,
          }),
        },
      );
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Field review failed.");
      }
      setFieldStatus((current) => ({
        ...current,
        [field.field_key]: `${field.label} review recorded.`,
      }));
      startRefresh(() => {
        router.refresh();
      });
    } catch (reviewError) {
      setFieldStatus((current) => ({
        ...current,
        [field.field_key]:
          reviewError instanceof Error
            ? reviewError.message
            : "Field review failed.",
      }));
    } finally {
      setReviewingFieldKey(null);
    }
  }

  return (
    <section
      className="workspace-section activation-panel"
      aria-labelledby="activation-title"
    >
      <div className="activation-panel-shell">
        <div className="activation-heading-row">
          <div className="section-heading activation-section-heading">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                Autonomy Digest
              </p>
              <h3 id="activation-title">Opportunity activation</h3>
            </div>
            <Activity className="text-ariadne-cyan" size={22} aria-hidden />
          </div>
          <button
            aria-label="Run Opportunity activation"
            className="command-button primary activation-run-button"
            disabled={isBusy}
            onClick={runActivation}
            type="button"
          >
            <RefreshCw
              className={isBusy ? "activation-spin" : undefined}
              size={17}
              aria-hidden
            />
            <span>{isBusy ? "Running" : "Run activation"}</span>
          </button>
        </div>

        <div className="activation-status-strip" aria-live="polite">
          <span className="activation-status-chip">
            <ShieldCheck size={15} aria-hidden />
            {run === null ? "No run yet" : formatLabel(run.status)}
          </span>
          <span className="activation-status-chip">
            <LockKeyhole size={15} aria-hidden />
            {trustedWrites ? "Trusted writes enabled" : "No trusted writes"}
          </span>
          {run !== null ? (
            <span className="activation-status-chip">
              <CheckCircle2 size={15} aria-hidden />
              {formatDateTime(run.completed_at ?? run.created_at)}
            </span>
          ) : null}
          {matrix !== undefined ? (
            <span className="activation-status-chip">
              <ShieldCheck size={15} aria-hidden />
              {currentGateLabel}
            </span>
          ) : null}
        </div>

        <ActivationGateCommandPanel
          currentGateLabel={currentGateLabel}
          fields={visibleGateFields}
          isBusy={isBusy}
          onRunActivation={runActivation}
          opportunityId={opportunityId}
          runExists={run !== null}
          showDetail={showDetail}
        />

        {error !== null ? <p className="activation-error">{error}</p> : null}
        {statusMessage !== null ? (
          <p className="activation-success">{statusMessage}</p>
        ) : null}

        {run === null || digest === undefined || matrix === undefined ? (
          <div className="activation-empty">
            <AlertTriangle size={19} aria-hidden />
            <p>No activation run stored for this Opportunity yet.</p>
          </div>
        ) : (
          <>
            <div className="activation-summary-grid">
              <ActivationMetric
                label="Current gate fields"
                value={visibleGateFields.length.toString()}
                description={`Living Packet fields required for ${currentGateLabel}.`}
              />
              <ActivationMetric
                label="Current gate gaps"
                value={(
                  visibleGateFields.length - supportedGateFields.length
                ).toString()}
                description="Fields still needing evidence, import, synthesis, or user input."
              />
              <ActivationMetric
                label="Review ready"
                value={reviewReadyGateFields.length.toString()}
                description="Field candidates waiting for human review."
              />
              <ActivationMetric
                label="Approvals"
                value={matrix.approval_required_count.toString()}
                description="Routes needing approval before live or capability-backed work."
              />
            </div>

            {showDetail ? (
              <details className="activation-detail-disclosure" open>
                <summary id="activation-detail-summary">
                  <span>Activation digest and full field matrix</span>
                  <strong>
                    {matrix.current_gate_blocked_count ??
                      matrix.blocked_field_count}{" "}
                    blockers /{" "}
                    {matrix.current_gate_review_ready_count ??
                      matrix.review_ready_count}{" "}
                    reviews
                  </strong>
                </summary>

                <div className="activation-detail-grid">
                  <ActivationListPanel
                    title="Coverage gained"
                    items={digest.coverage_gained}
                  />
                  <ActivationListPanel
                    title="Next best actions"
                    items={digest.next_best_actions}
                  />
                  <ActivationListPanel
                    title="Approvals needed"
                    items={digest.approval_required_routes}
                  />
                  <ActivationListPanel
                    title="Source limits"
                    items={digest.source_limitations}
                  />
                  <ActivationListPanel
                    title="Skill chains"
                    items={digest.recommended_skill_chains}
                  />
                </div>

                <div
                  className="activation-matrix"
                  aria-labelledby="activation-matrix-title"
                >
                  <div className="activation-matrix-heading">
                    <div>
                      <p>Packet Field Action Matrix</p>
                      <h4 id="activation-matrix-title">
                        {matrix.fields.length} packet fields mapped for{" "}
                        {currentGateLabel}
                      </h4>
                    </div>
                    <Route size={20} aria-hidden />
                  </div>
                  <div className="activation-field-grid">
                    {matrix.fields.map((field) => (
                      <ActivationFieldCard
                        field={field}
                        fieldNote={fieldNotes[field.field_key] ?? ""}
                        fieldStatus={fieldStatus[field.field_key] ?? ""}
                        fieldValue={
                          fieldValues[field.field_key] ??
                          field.current_value ??
                          ""
                        }
                        isBusy={reviewingFieldKey !== null || isRefreshing}
                        key={field.field_key}
                        onFieldNoteChange={(nextValue) =>
                          setFieldNotes((current) => ({
                            ...current,
                            [field.field_key]: nextValue,
                          }))
                        }
                        onFieldValueChange={(nextValue) =>
                          setFieldValues((current) => ({
                            ...current,
                            [field.field_key]: nextValue,
                          }))
                        }
                        onReview={(decision) => reviewField(field, decision)}
                        output={outputByField.get(field.field_key) ?? null}
                        routeHref={fieldRouteHref(
                          opportunityId,
                          field.field_key,
                        )}
                      />
                    ))}
                  </div>
                </div>
              </details>
            ) : (
              <section
                className="activation-detail-link"
                aria-labelledby="activation-detail-link-title"
              >
                <div>
                  <p>Activation detail</p>
                  <h4 id="activation-detail-link-title">
                    Digest and matrix are available on demand
                  </h4>
                  <span>
                    Load route detail for {matrix.fields.length} packet fields,
                    approval needs, source limits, and skill chains.
                  </span>
                </div>
                <a
                  className="command-button"
                  href={activationDetailHref(opportunityId)}
                >
                  <Route size={16} aria-hidden />
                  <span>Open activation detail</span>
                </a>
              </section>
            )}
          </>
        )}
      </div>
    </section>
  );
}

function ActivationGateCommandPanel({
  currentGateLabel,
  fields,
  isBusy,
  onRunActivation,
  opportunityId,
  runExists,
  showDetail,
}: {
  currentGateLabel: string;
  fields: PacketFieldActionItem[];
  isBusy: boolean;
  onRunActivation: () => void;
  opportunityId: string;
  runExists: boolean;
  showDetail: boolean;
}) {
  const supportedFields = fields.filter(isActivationFieldAnswered);
  const reviewReadyFields = fields.filter(isActivationFieldReviewReady);
  const blockedFields = fields.filter(
    (field) =>
      !isActivationFieldAnswered(field) && !isActivationFieldReviewReady(field),
  );
  const priorityField = reviewReadyFields[0] ?? blockedFields[0] ?? null;
  const commandSummary =
    priorityField === null
      ? runExists
        ? "No current-gate packet field is blocking the latest activation run."
        : "Activation has not built a current-gate route queue yet."
      : `${priorityField.label}: ${priorityField.gap_summary ?? priorityField.route_rationale}`;

  return (
    <section
      className="activation-gate-command"
      aria-labelledby="activation-gate-command-title"
    >
      <div className="activation-gate-command-main">
        <div>
          <p>Gate Packet Path</p>
          <h4 id="activation-gate-command-title">
            Next move for {currentGateLabel}
          </h4>
          <span>{commandSummary}</span>
        </div>
        <div className="activation-gate-command-actions">
          {priorityField === null ? (
            <button
              aria-label="Run Opportunity activation"
              className="command-button primary"
              disabled={isBusy}
              onClick={onRunActivation}
              type="button"
            >
              <RefreshCw size={16} aria-hidden />
              <span>{runExists ? "Refresh activation" : "Run activation"}</span>
            </button>
          ) : (
            <a
              className="command-button primary"
              href={fieldRouteHref(opportunityId, priorityField.field_key)}
            >
              <Route size={16} aria-hidden />
              <span>
                {isActivationFieldReviewReady(priorityField)
                  ? `Review ${priorityField.label}`
                  : `Start ${priorityField.label}`}
              </span>
            </a>
          )}
          <a
            className="command-button"
            href={
              showDetail
                ? "#activation-detail-summary"
                : activationDetailHref(opportunityId)
            }
          >
            <Activity size={16} aria-hidden />
            <span>Field matrix</span>
          </a>
        </div>
      </div>
      <div
        className="activation-gate-command-strip"
        aria-label="Current gate state"
      >
        <span>{fields.length} gate fields</span>
        <span>{supportedFields.length} supported</span>
        <span>{reviewReadyFields.length} review-ready</span>
        <span>{blockedFields.length} blockers</span>
      </div>
      {priorityField !== null ? (
        <div className="activation-gate-priority">
          <strong>{priorityField.recommended_route}</strong>
          <span>
            {formatLabel(
              priorityField.route_kind ?? priorityField.action_state,
            )}
          </span>
        </div>
      ) : null}
    </section>
  );
}

function ActivationFieldCard({
  field,
  fieldNote,
  fieldStatus,
  fieldValue,
  isBusy,
  onFieldNoteChange,
  onFieldValueChange,
  onReview,
  output,
  routeHref,
}: {
  field: PacketFieldActionItem;
  fieldNote: string;
  fieldStatus: string;
  fieldValue: string;
  isBusy: boolean;
  onFieldNoteChange: (value: string) => void;
  onFieldValueChange: (value: string) => void;
  onReview: (decision: FieldReviewDecision) => void;
  output: OpportunityActivationRunOutput | null;
  routeHref: string;
}) {
  const isReviewed =
    output !== null && output.review_state !== "pending_review";
  const canReview = output !== null && output.review_state === "pending_review";
  const canStartRoute = field.action_state !== "answered";

  return (
    <article
      className={`activation-field-card ${actionStateClass(field.action_state)}`}
    >
      <div className="activation-field-header">
        <div>
          <p>{formatLabel(field.section)}</p>
          <h5>{field.label}</h5>
        </div>
        <span className="activation-field-state">
          {isReviewed && output !== null
            ? formatLabel(output.review_state)
            : formatLabel(field.action_state)}
        </span>
      </div>
      <p className="activation-field-question">{field.question}</p>
      <p className="activation-field-route">{field.recommended_route}</p>
      <div className="activation-field-route-detail">
        <p>{field.route_rationale}</p>
        {field.route_steps.length > 0 ? (
          <ol aria-label={`${field.label} route steps`}>
            {field.route_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        ) : null}
      </div>
      {field.answer_paths.length > 0 ? (
        <div className="activation-field-answer-paths">
          <span>Answer paths</span>
          <div className="activation-field-answer-path-row">
            {field.answer_paths.map((path) => (
              <span key={path}>{path}</span>
            ))}
          </div>
        </div>
      ) : null}
      {field.approval_gate ? (
        <p className="activation-field-approval-gate">{field.approval_gate}</p>
      ) : null}
      <div className="activation-field-chip-row">
        <span>
          {field.current_gate_required === false
            ? "Future gate"
            : "Required this gate"}
        </span>
        {field.route_kind ? <span>{formatLabel(field.route_kind)}</span> : null}
        <span>{formatLabel(field.evidence_status)}</span>
        <span>{formatLabel(field.value_kind)}</span>
        {field.approval_required ? <span>Approval</span> : null}
      </div>

      {field.action_state === "answered" ? (
        <div className="activation-field-reviewed">
          <CheckCircle2 size={15} aria-hidden />
          <span>{field.current_value ?? "Answer accepted"}</span>
        </div>
      ) : null}

      {canStartRoute ? (
        <a className="activation-assisted-route-link" href={routeHref}>
          <Route size={15} aria-hidden />
          <span>Start assisted route</span>
        </a>
      ) : null}

      {canReview ? (
        <div className="activation-field-review-gate">
          <label>
            <span>Answer to trust</span>
            <textarea
              onChange={(event) => onFieldValueChange(event.target.value)}
              placeholder={field.gap_summary ?? field.label}
              value={fieldValue}
            />
          </label>
          <label>
            <span>Review note</span>
            <textarea
              onChange={(event) => onFieldNoteChange(event.target.value)}
              placeholder="Why this decision is safe"
              value={fieldNote}
            />
          </label>
          <div className="activation-field-actions">
            <button
              className="command-button primary"
              disabled={isBusy}
              onClick={() => onReview("accept")}
              type="button"
            >
              <CheckCircle2 size={15} aria-hidden />
              <span>Accept</span>
            </button>
            <button
              className="command-button"
              disabled={isBusy}
              onClick={() => onReview("edit")}
              type="button"
            >
              <CheckCircle2 size={15} aria-hidden />
              <span>Edit</span>
            </button>
            <button
              className="command-button"
              disabled={isBusy}
              onClick={() => onReview("route")}
              type="button"
            >
              <Route size={15} aria-hidden />
              <span>Route</span>
            </button>
            <button
              className="command-button danger"
              disabled={isBusy}
              onClick={() => onReview("discard")}
              type="button"
            >
              <XCircle size={15} aria-hidden />
              <span>Discard</span>
            </button>
          </div>
          {fieldStatus ? (
            <p className="activation-field-status" aria-live="polite">
              {fieldStatus}
            </p>
          ) : null}
        </div>
      ) : null}

      {isReviewed && output !== null ? (
        <div className="activation-field-reviewed">
          <CheckCircle2 size={15} aria-hidden />
          <span>Review state: {formatLabel(output.review_state)}</span>
        </div>
      ) : null}
    </article>
  );
}

function fieldRouteHref(opportunityId: string, fieldKey: string): string {
  const params = new URLSearchParams({
    opportunity_id: opportunityId,
    mode: "capture",
    packet_field_key: fieldKey,
    route_goal: "close_packet_gap",
  });
  return `/?${params.toString()}`;
}

function activationDetailHref(opportunityId: string): string {
  const params = new URLSearchParams({
    detail: "1",
    mode: "activation",
    opportunity_id: opportunityId,
  });

  return `/?${params.toString()}`;
}

function ActivationMetric({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <article className="activation-summary-card">
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
      <span>{description}</span>
    </article>
  );
}

function ActivationListPanel({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <article className="activation-list-panel">
      <h4>{title}</h4>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No items.</p>
      )}
    </article>
  );
}

function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function actionStateClass(value: string): string {
  return `activation-field-${value.split("_").join("-")}`;
}

function isActivationFieldReviewReady(field: PacketFieldActionItem): boolean {
  return field.requires_review || field.action_state === "review_ready";
}

function isActivationFieldAnswered(field: PacketFieldActionItem): boolean {
  return (
    field.action_state === "answered" || field.evidence_status === "answered"
  );
}

function formatDateTime(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) {
    return "Time unknown";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(timestamp);
}
