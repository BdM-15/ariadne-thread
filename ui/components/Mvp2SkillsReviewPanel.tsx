"use client";

import {
  GitBranch,
  Loader2,
  PlayCircle,
  ShieldCheck,
} from "lucide-react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useState, useTransition } from "react";

export type Mvp2CapabilityReviewCard = {
  capability_id: string;
  name: string;
  capability_status: string;
  capability_type: string;
  validation_status: string;
  review_destination: string;
  quality_gate: string;
  source_path: string;
  next_enabling_action: string | null;
};

export type Mvp2RouteReviewCard = {
  route_id: string;
  field_key: string;
  capability_id: string;
  capability_type: string;
  status: string;
  approval_required: boolean;
  approval_gate: string | null;
  review_destination: string;
  invoked_run_id: string | null;
  invoked_output_ids: string[];
  source_limitations: string[];
  trusted_downstream_writes: boolean;
};

export type Mvp2ChainStageReviewCard = {
  run_id: string;
  stage_id: string;
  capability_id: string;
  status: string;
  quality_gate_result: string;
  review_destination: string;
  produced_handoff: string;
  input_refs: string[];
  gaps: string[];
};

export type Mvp2ModelRoleReviewCard = {
  model_role: string;
  allowed_uses: string[];
  approval_requirement: string;
  expected_output: string;
  review_destination: string;
  approval_required: boolean;
  fake_runner_supported: boolean;
  live_provider_allowed: boolean;
};

export type Mvp2ImprovementProposal = {
  proposal_id: string;
  kind: string;
  title: string;
  target_ref: string;
  proposed_change: string;
  rationale: string;
  guardrail_summary: string;
  review_state: string;
  mutates_skills: boolean;
  mutates_chain_maps: boolean;
  mutates_trusted_records: boolean;
  mutates_autonomy_settings: boolean;
  trusted_downstream_writes: boolean;
};

export type Mvp2CapabilityRunSummary = {
  run_id: string;
  capability_id: string;
  capability_type: string;
  executor_kind: string;
  status: string;
  inputs_summary: string;
  outputs: Array<{
    output_id: string;
    title: string;
    summary: string;
    review_state: string;
    recommended_destination: string | null;
  }>;
  provenance: Record<string, unknown>;
};

export type Mvp2SkillsReviewSummary = {
  review_status: string;
  focused_skills: Mvp2CapabilityReviewCard[];
  dependency_gated_capabilities: Mvp2CapabilityReviewCard[];
  route_cards: Mvp2RouteReviewCard[];
  chain_stages: Mvp2ChainStageReviewCard[];
  model_role_contracts: Mvp2ModelRoleReviewCard[];
  capability_runs: Mvp2CapabilityRunSummary[];
  improvement_proposals: Mvp2ImprovementProposal[];
  focused_skill_count: number;
  dependency_gated_count: number;
  pending_output_count: number;
  trusted_downstream_writes: boolean;
  guardrail_summary: string;
};

export function Mvp2SkillsReviewPanel({
  summary,
}: {
  summary: Mvp2SkillsReviewSummary | null;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [isSeeding, setIsSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function createReviewDemo() {
    setError(null);
    setIsSeeding(true);
    try {
      const response = await fetch(
        "/api/mvp-2/skills-review/actions/demo-run",
        { method: "POST" },
      );
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "MVP-2 review demo failed.");
      }
      startTransition(() => router.refresh());
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "MVP-2 review demo failed.",
      );
    } finally {
      setIsSeeding(false);
    }
  }

  if (summary === null) {
    return (
      <section className="focused-mode-placeholder">
        <p>MVP-2 Skills Review</p>
        <h3>Review summary unavailable.</h3>
        <span>
          Start the Ariadne backend on port 9622 so the Next.js Command Center
          can load the skill-chain review contract.
        </span>
      </section>
    );
  }

  const buttonBusy = isSeeding || isPending;

  return (
    <section className="action-plan-mode" aria-labelledby="mvp2-review-title">
      <div className="action-plan-hero">
        <div>
          <p>MVP-2 Skills Review</p>
          <h3 id="mvp2-review-title">Review skill chains in the real UI.</h3>
          <span>{summary.guardrail_summary}</span>
        </div>
        <button
          className="command-button primary"
          disabled={buttonBusy}
          onClick={createReviewDemo}
          type="button"
        >
          {buttonBusy ? (
            <Loader2 className="animate-spin" size={17} aria-hidden />
          ) : (
            <PlayCircle size={17} aria-hidden />
          )}
          <span>{buttonBusy ? "Creating demo" : "Create review demo"}</span>
        </button>
      </div>

      {error !== null ? <p className="intake-error">{error}</p> : null}

      <dl className="action-plan-metric-grid">
        <ReviewMetric label="Focused skills" value={summary.focused_skill_count} />
        <ReviewMetric label="Dependency-gated" value={summary.dependency_gated_count} />
        <ReviewMetric label="Pending outputs" value={summary.pending_output_count} />
        <ReviewMetric
          label="Trusted writes"
          value={summary.trusted_downstream_writes ? "Enabled" : "None"}
        />
      </dl>

      <div className="action-plan-lanes">
        <ReviewLane eyebrow="Runnable" title="Focused skills">
          {summary.focused_skills.map((skill) => (
            <CapabilityCard card={skill} key={skill.capability_id} />
          ))}
        </ReviewLane>

        <ReviewLane eyebrow="Blocked by design" title="Dependency gates">
          {summary.dependency_gated_capabilities.map((skill) => (
            <CapabilityCard card={skill} key={skill.capability_id} />
          ))}
        </ReviewLane>

        <ReviewLane eyebrow="Activation" title="Route cards">
          {summary.route_cards.map((routeCard) => (
            <article className="action-update-card" key={routeCard.route_id}>
              <div className="action-update-card-head">
                <span>{formatLabel(routeCard.status)}</span>
                <span>{routeCard.approval_required ? "Approval" : "Ready"}</span>
              </div>
              <p>{routeCard.route_id}</p>
              <span className="action-update-note">
                {routeCard.capability_id} routes {routeCard.field_key} to {routeCard.review_destination}.
              </span>
              <ReviewDefinitionList
                items={[
                  ["Gate", routeCard.approval_gate ?? "None"],
                  ["Invoked run", routeCard.invoked_run_id ?? "Not run"],
                  ["Outputs", joinOrNone(routeCard.invoked_output_ids)],
                  [
                    "Trusted writes",
                    routeCard.trusted_downstream_writes ? "Yes" : "No",
                  ],
                ]}
              />
            </article>
          ))}
        </ReviewLane>

        <ReviewLane eyebrow="Quality gates" title="Chain stages">
          {summary.chain_stages.map((stage) => (
            <article
              className="action-update-card"
              key={`${stage.run_id}:${stage.stage_id}`}
            >
              <div className="action-update-card-head">
                <span>{formatLabel(stage.status)}</span>
                <span>{formatLabel(stage.quality_gate_result)}</span>
              </div>
              <p>{stage.stage_id}</p>
              <span className="action-update-note">
                {stage.capability_id} produced {stage.produced_handoff} for {stage.review_destination}.
              </span>
              <ReviewDefinitionList
                items={[
                  ["Run", stage.run_id],
                  ["Input refs", joinOrNone(stage.input_refs)],
                  ["Gaps", joinOrNone(stage.gaps)],
                ]}
              />
            </article>
          ))}
        </ReviewLane>

        <ReviewLane eyebrow="Model discipline" title="Model role contracts">
          {summary.model_role_contracts.map((contract) => (
            <article className="action-update-card" key={contract.model_role}>
              <div className="action-update-card-head">
                <span>{formatLabel(contract.model_role)}</span>
                <span>{contract.fake_runner_supported ? "Fake runner" : "Live only"}</span>
              </div>
              <p>{contract.expected_output}</p>
              <ReviewDefinitionList
                items={[
                  ["Approval", formatLabel(contract.approval_requirement)],
                  ["Destination", formatLabel(contract.review_destination)],
                  ["Allowed uses", joinOrNone(contract.allowed_uses)],
                  [
                    "Live provider",
                    contract.live_provider_allowed ? "Allowed" : "Not allowed",
                  ],
                ]}
              />
            </article>
          ))}
        </ReviewLane>

        <ReviewLane eyebrow="Run proof" title="Run progress and provenance">
          {summary.capability_runs.slice(0, 5).map((run) => (
            <article className="action-update-card" key={run.run_id}>
              <div className="action-update-card-head">
                <span>{formatLabel(run.status)}</span>
                <span>{run.outputs.length} outputs</span>
              </div>
              <p>{run.capability_id}</p>
              <span className="action-update-note">{run.inputs_summary}</span>
              <ReviewDefinitionList
                items={[
                  ["Executor", formatLabel(run.executor_kind)],
                  ["Type", formatLabel(run.capability_type)],
                  ["Network", provenanceValue(run.provenance, "network_required")],
                  ["Model", provenanceValue(run.provenance, "model_required")],
                ]}
              />
            </article>
          ))}
        </ReviewLane>

        <ReviewLane eyebrow="Hermes" title="Improvement Proposals">
          {summary.improvement_proposals.map((proposal) => (
            <article className="action-update-card" key={proposal.proposal_id}>
              <div className="action-update-card-head">
                <span>{formatLabel(proposal.review_state)}</span>
                <span>{formatLabel(proposal.kind)}</span>
              </div>
              <p>{proposal.title}</p>
              <span className="action-update-note">
                {proposal.proposed_change}
              </span>
              <ReviewDefinitionList
                items={[
                  ["Target", proposal.target_ref],
                  ["Mutates skills", proposal.mutates_skills ? "Yes" : "No"],
                  ["Mutates chains", proposal.mutates_chain_maps ? "Yes" : "No"],
                  [
                    "Mutates autonomy",
                    proposal.mutates_autonomy_settings ? "Yes" : "No",
                  ],
                ]}
              />
            </article>
          ))}
        </ReviewLane>

        <section className="action-plan-lane" aria-labelledby="mvp2-boundary-title">
          <div className="action-plan-lane-heading">
            <p>Review boundary</p>
            <h4 id="mvp2-boundary-title">What this proves</h4>
          </div>
          <div className="action-plan-card-stack">
            <article className="action-gap-card">
              <ShieldCheck className="text-ariadne-cyan" size={20} aria-hidden />
              <div>
                <span>{formatLabel(summary.review_status)}</span>
                <h5>No trusted downstream writes</h5>
                <p>
                  The demo makes skill-chain shape visible without accepting packet answers,
                  creating evidence, changing chain maps, or expanding autonomy.
                </p>
              </div>
            </article>
          </div>
        </section>
      </div>
    </section>
  );
}

function CapabilityCard({ card }: { card: Mvp2CapabilityReviewCard }) {
  return (
    <article className="action-gap-card">
      <GitBranch className="text-ariadne-cyan" size={20} aria-hidden />
      <div>
        <span>{formatLabel(card.capability_status)}</span>
        <h5>{card.name}</h5>
        <p>{card.next_enabling_action ?? card.quality_gate}</p>
        <small>
          {card.capability_id} - {formatLabel(card.capability_type)} - {card.source_path}
        </small>
      </div>
    </article>
  );
}

function ReviewLane({
  children,
  eyebrow,
  title,
}: {
  children: ReactNode;
  eyebrow: string;
  title: string;
}) {
  return (
    <section className="action-plan-lane" aria-labelledby={`${slug(title)}-title`}>
      <div className="action-plan-lane-heading">
        <p>{eyebrow}</p>
        <h4 id={`${slug(title)}-title`}>{title}</h4>
      </div>
      <div className="action-plan-card-stack">
        {childrenCount(children) > 0 ? (
          children
        ) : (
          <div className="action-plan-empty">
            <p>Nothing queued.</p>
            <span>Create the review demo or run a workflow to populate this lane.</span>
          </div>
        )}
      </div>
    </section>
  );
}

function ReviewMetric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="metric metric-cyan">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function ReviewDefinitionList({ items }: { items: Array<[string, string]> }) {
  return (
    <dl>
      {items.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function provenanceValue(provenance: Record<string, unknown>, key: string): string {
  const value = provenance[key];
  if (Array.isArray(value)) {
    return joinOrNone(value.map(String));
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (value === null || value === undefined || value === "") {
    return "None";
  }
  return String(value);
}

function joinOrNone(values: string[]): string {
  return values.length > 0 ? values.map(formatLabel).join(", ") : "None";
}

function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function childrenCount(children: ReactNode): number {
  return Array.isArray(children) ? children.length : children === null ? 0 : 1;
}

function slug(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}