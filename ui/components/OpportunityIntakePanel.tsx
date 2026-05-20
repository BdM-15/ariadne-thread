"use client";

import { CheckCircle2, Loader2, PlusCircle, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

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
  packet_sections: { id: string; label: string; evidence_status: string }[];
  packet_fields: {
    key: string;
    label: string;
    status: string;
    recommended_route: string;
  }[];
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

export function OpportunityIntakePanel() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isOpeningWorkspace, setIsOpeningWorkspace] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scaffold, setScaffold] = useState<OpportunityScaffold | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isOpen]);

  async function createOpportunity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await fetch(
        "/api/production-command-center/opportunities",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name }),
        },
      );
      if (!response.ok) {
        const body = (await response.json()) as { detail?: string };
        throw new Error(body.detail ?? "Opportunity creation failed.");
      }
      const body = (await response.json()) as OpportunityCreateResponse;
      setScaffold(body.scaffold);
      setName("");
      setIsOpeningWorkspace(true);
      setIsOpen(false);
      router.push(
        `/?opportunity_id=${encodeURIComponent(body.scaffold.opportunity.id)}&created=1`,
      );
      router.refresh();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Opportunity creation failed.",
      );
    } finally {
      setIsSubmitting(false);
      setIsOpeningWorkspace(false);
    }
  }

  return (
    <>
      <button
        className="new-opportunity-button"
        onClick={() => {
          setError(null);
          setScaffold(null);
          setIsOpen(true);
        }}
        type="button"
      >
        <PlusCircle size={18} aria-hidden />
        <span>New Opportunity</span>
      </button>

      {isOpen ? (
        <div
          className="modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setIsOpen(false);
            }
          }}
        >
          <section
            aria-labelledby="opportunity-intake-title"
            aria-modal="true"
            className="opportunity-modal"
            role="dialog"
          >
            <div className="modal-heading">
              <div>
                <p>Opportunity Intake</p>
                <h2 id="opportunity-intake-title">Create workspace</h2>
              </div>
              <button
                aria-label="Close opportunity intake"
                className="modal-close-button"
                onClick={() => setIsOpen(false)}
                type="button"
              >
                <X size={18} aria-hidden />
              </button>
            </div>

            <form className="mt-5 space-y-4" onSubmit={createOpportunity}>
              <label className="intake-field" htmlFor="opportunity-name">
                <span>Opportunity name</span>
                <input
                  autoFocus
                  id="opportunity-name"
                  minLength={2}
                  onChange={(event) => setName(event.target.value)}
                  required
                  type="text"
                  value={name}
                />
              </label>

              <p className="modal-helper-text">
                Ariadne will build the standard capture workspace, packet
                sections, workstreams, field slots, and first activation digest.
              </p>

              <button
                className="command-button primary flex items-center justify-center gap-2"
                disabled={isSubmitting || isOpeningWorkspace}
                type="submit"
              >
                {isSubmitting || isOpeningWorkspace ? (
                  <Loader2 className="animate-spin" size={17} aria-hidden />
                ) : (
                  <PlusCircle size={17} aria-hidden />
                )}
                <span>
                  {isOpeningWorkspace
                    ? "Opening workspace"
                    : "Create workspace"}
                </span>
              </button>
            </form>

            <div aria-live="polite">
              {error !== null ? <p className="intake-error">{error}</p> : null}

              {scaffold !== null ? (
                <article className="intake-result">
                  <div className="flex items-start gap-3">
                    <CheckCircle2
                      className="mt-1 text-ariadne-cyan"
                      size={19}
                      aria-hidden
                    />
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
                      <dd>{scaffold.packet_sections.length}</dd>
                    </div>
                    <div>
                      <dt>Fields</dt>
                      <dd>{scaffold.packet_fields.length}</dd>
                    </div>
                  </dl>

                  <div className="mt-3 border-t border-ariadne-line pt-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      Activation Digest
                    </p>
                    <ul className="mt-2 space-y-2 text-sm leading-5 text-slate-300">
                      {scaffold.activation_digest.coverage_gained.map(
                        (item) => (
                          <li key={item}>{item}</li>
                        ),
                      )}
                    </ul>
                    <p className="mt-3 text-sm text-ariadne-signal">
                      {scaffold.activation_digest.next_best_actions[0]}
                    </p>
                  </div>
                </article>
              ) : null}
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}
