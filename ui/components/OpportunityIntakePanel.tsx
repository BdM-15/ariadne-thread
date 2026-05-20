"use client";

import { CheckCircle2, Loader2, PlusCircle } from "lucide-react";
import { FormEvent, useState } from "react";

type OpportunityScaffold = {
  opportunity: {
    id: string;
    name: string;
    lifecycle_state: string;
    gate_status: string;
  };
  workstreams: { id: string; label: string; status: string }[];
  backfill_needs: { workstream_id: string; label: string; rationale: string }[];
  packet: {
    readiness_label: string;
    gap_section_count: number;
  };
  packet_fields: { key: string; label: string; status: string; recommended_route: string }[];
  activation_digest: {
    coverage_gained: string[];
    review_ready_count: number;
    blocked_field_count: number;
    recommended_skill_chains: string[];
    approval_required_routes: string[];
    source_limitations: string[];
    next_best_actions: string[];
  };
};

type OpportunityCreateResponse = {
  scaffold: OpportunityScaffold;
};

const entryReasons = [
  { value: "new_lead", label: "New lead" },
  { value: "recompete", label: "Recompete" },
  { value: "incumbent_recompete", label: "Incumbent recompete" },
  { value: "urgent_solicitation", label: "Urgent solicitation" },
  { value: "legacy_pursuit", label: "Legacy pursuit" },
] as const;

const lifecycleStates = [
  { value: "identified", label: "Identified" },
  { value: "qualified", label: "Qualified" },
  { value: "pursuing", label: "Pursuing" },
] as const;

const backfillOptions = [
  { value: "customer_insight", label: "Customer" },
  { value: "competitive_intelligence", label: "Competition" },
  { value: "partner_strategy", label: "Partners" },
  { value: "price_to_win", label: "Price" },
] as const;

export function OpportunityIntakePanel() {
  const [name, setName] = useState("");
  const [entryReason, setEntryReason] = useState("new_lead");
  const [lifecycleState, setLifecycleState] = useState("identified");
  const [rationale, setRationale] = useState("");
  const [selectedBackfills, setSelectedBackfills] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scaffold, setScaffold] = useState<OpportunityScaffold | null>(null);

  async function createOpportunity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await fetch("/api/production-command-center/opportunities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          entry_reason: entryReason,
          starting_lifecycle_state: lifecycleState,
          rationale: rationale || null,
          missing_or_stale_workstreams: selectedBackfills,
        }),
      });
      if (!response.ok) {
        const body = (await response.json()) as { detail?: string };
        throw new Error(body.detail ?? "Opportunity creation failed.");
      }
      const body = (await response.json()) as OpportunityCreateResponse;
      setScaffold(body.scaffold);
      setName("");
      setRationale("");
      setSelectedBackfills([]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Opportunity creation failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function toggleBackfill(workstreamId: string) {
    setSelectedBackfills((current) =>
      current.includes(workstreamId)
        ? current.filter((id) => id !== workstreamId)
        : [...current, workstreamId],
    );
  }

  return (
    <section className="intake-panel" aria-labelledby="opportunity-intake-title">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Intake</p>
          <h2 id="opportunity-intake-title" className="text-lg font-semibold">
            Add Opportunity
          </h2>
        </div>
        <PlusCircle className="text-ariadne-cyan" size={21} aria-hidden />
      </div>

      <form className="mt-4 space-y-3" onSubmit={createOpportunity}>
        <label className="intake-field" htmlFor="opportunity-name">
          <span>Name</span>
          <input
            id="opportunity-name"
            minLength={2}
            onChange={(event) => setName(event.target.value)}
            required
            type="text"
            value={name}
          />
        </label>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <label className="intake-field" htmlFor="entry-reason">
            <span>Entry</span>
            <select
              id="entry-reason"
              onChange={(event) => setEntryReason(event.target.value)}
              value={entryReason}
            >
              {entryReasons.map((reason) => (
                <option key={reason.value} value={reason.value}>
                  {reason.label}
                </option>
              ))}
            </select>
          </label>

          <label className="intake-field" htmlFor="lifecycle-state">
            <span>State</span>
            <select
              id="lifecycle-state"
              onChange={(event) => setLifecycleState(event.target.value)}
              value={lifecycleState}
            >
              {lifecycleStates.map((state) => (
                <option key={state.value} value={state.value}>
                  {state.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="intake-field" htmlFor="entry-rationale">
          <span>Rationale</span>
          <textarea
            id="entry-rationale"
            onChange={(event) => setRationale(event.target.value)}
            rows={3}
            value={rationale}
          />
        </label>

        <fieldset className="intake-backfill">
          <legend>Backfill</legend>
          <div className="grid grid-cols-2 gap-2">
            {backfillOptions.map((option) => (
              <label key={option.value}>
                <input
                  checked={selectedBackfills.includes(option.value)}
                  onChange={() => toggleBackfill(option.value)}
                  type="checkbox"
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <button className="command-button primary flex items-center justify-center gap-2" disabled={isSubmitting} type="submit">
          {isSubmitting ? <Loader2 className="animate-spin" size={17} aria-hidden /> : <PlusCircle size={17} aria-hidden />}
          <span>Create scaffold</span>
        </button>
      </form>

      <div aria-live="polite">
        {error !== null ? <p className="intake-error">{error}</p> : null}

        {scaffold !== null ? (
          <article className="intake-result">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-1 text-ariadne-cyan" size={19} aria-hidden />
              <div>
                <h3>{scaffold.opportunity.name}</h3>
                <p>{scaffold.opportunity.id}</p>
              </div>
            </div>

            <dl className="mt-3 grid grid-cols-3 gap-2">
              <div>
                <dt>Workstreams</dt>
                <dd>{scaffold.workstreams.length}</dd>
              </div>
              <div>
                <dt>Sections</dt>
                <dd>{scaffold.packet.gap_section_count}</dd>
              </div>
              <div>
                <dt>Fields</dt>
                <dd>{scaffold.packet_fields.length}</dd>
              </div>
            </dl>

            <div className="mt-3 border-t border-ariadne-line pt-3">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Activation Digest</p>
              <ul className="mt-2 space-y-2 text-sm leading-5 text-slate-300">
                {scaffold.activation_digest.coverage_gained.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p className="mt-3 text-sm text-ariadne-signal">
                {scaffold.activation_digest.next_best_actions[0]}
              </p>
            </div>
          </article>
        ) : null}
      </div>
    </section>
  );
}