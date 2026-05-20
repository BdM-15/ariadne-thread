import {
  Archive,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileStack,
  FileSpreadsheet,
  FileText,
  Layers3,
  MessageSquareText,
  Presentation,
  SearchCheck,
  ShieldCheck,
} from "lucide-react";
import type { ComponentType } from "react";
import {
  AssistedCapturePanel,
  type AssistedCaptureGoal,
} from "../components/AssistedCapturePanel";
import { OpportunityIntakePanel } from "../components/OpportunityIntakePanel";

export const dynamic = "force-dynamic";

type Opportunity = {
  id: string;
  name: string;
  lifecycle_state: string;
  gate_status: string;
};

type Packet = {
  title: string;
  readiness_label: string;
  answered_section_count: number;
  gap_section_count: number;
  partial_section_count: number;
};

type ContextSummary = {
  trusted_count: number;
  reviewable_count: number;
  gap_count: number;
  source_limitation_count: number;
};

type LayoutRegion = {
  id: string;
  label: string;
  purpose: string;
};

type WorkMode = {
  id: string;
  label: string;
  pending_count: number;
};

type Workspace = {
  production_ui_contract: string;
  scaffold_role: string;
  opportunity: Opportunity;
  packet: Packet;
  context_summary: ContextSummary;
  layout_regions: LayoutRegion[];
  work_modes: WorkMode[];
  assisted_capture_goals: AssistedCaptureGoal[];
};

type WorkspaceResponse = {
  workspace: Workspace;
};

type PortfolioOpportunity = {
  id: string;
  name: string;
  lifecycle_state: string;
  gate_status: string;
  packet_readiness_label: string;
  review_ready_count: number;
  blocked_field_count: number;
  source_limitation_count: number;
  is_demo: boolean;
};

type PortfolioResponse = {
  opportunities: PortfolioOpportunity[];
};

type RendererCapability = {
  id: string;
  label: string;
  engine: string;
  output_formats: string[];
  readiness_state: string;
  mvp_required: boolean;
  role: string;
};

type RendererExportAction = {
  id: string;
  label: string;
  renderer_id: string;
  output_format: string;
  review_required: boolean;
  enabled: boolean;
  disabled_reason: string;
};

type RendererReadiness = {
  target_artifact: string;
  target_label: string;
  target_rationale: string;
  renderers: RendererCapability[];
  export_actions: RendererExportAction[];
  backend_blockers: string[];
};

type RendererReadinessResponse = {
  readiness: RendererReadiness;
};

type SignalTone = "cyan" | "copper" | "rose" | "signal";

type CommandCenterSearchParams = {
  opportunity_id?: string | string[];
  created?: string | string[];
};

type CommandCenterPageProps = {
  searchParams?: Promise<CommandCenterSearchParams>;
};

const modeIcons: Record<
  string,
  ComponentType<{ className?: string; size?: number }>
> = {
  packet: FileText,
  actions: ClipboardCheck,
  engagement: MessageSquareText,
  research: SearchCheck,
  documents: FileStack,
  artifacts: Archive,
  capability_studio: Bot,
};

const apiBaseUrl = process.env.ARIADNE_API_BASE_URL ?? "http://127.0.0.1:9622";

async function loadWorkspace(opportunityId?: string): Promise<Workspace | null> {
  try {
    const url = new URL(`${apiBaseUrl}/api/production-command-center/workspace`);
    if (opportunityId !== undefined) {
      url.searchParams.set("opportunity_id", opportunityId);
    }
    const response = await fetch(url, {
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    const body = (await response.json()) as WorkspaceResponse;
    return body.workspace;
  } catch {
    return null;
  }
}

async function loadPortfolio(): Promise<PortfolioOpportunity[]> {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/production-command-center/opportunities`,
      {
        cache: "no-store",
      },
    );
    if (!response.ok) {
      return [];
    }
    const body = (await response.json()) as PortfolioResponse;
    return body.opportunities;
  } catch {
    return [];
  }
}

async function loadRendererReadiness(): Promise<RendererReadiness | null> {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/production-command-center/renderer-readiness`,
      {
        cache: "no-store",
      },
    );
    if (!response.ok) {
      return null;
    }
    const body = (await response.json()) as RendererReadinessResponse;
    return body.readiness;
  } catch {
    return null;
  }
}

export default async function CommandCenterPage({
  searchParams,
}: CommandCenterPageProps) {
  const resolvedSearchParams = searchParams === undefined ? {} : await searchParams;
  const selectedOpportunityId = firstSearchParam(
    resolvedSearchParams.opportunity_id,
  );
  const createdWorkspace = firstSearchParam(resolvedSearchParams.created) === "1";
  const [workspace, rendererReadiness, portfolio] = await Promise.all([
    loadWorkspace(selectedOpportunityId),
    loadRendererReadiness(),
    loadPortfolio(),
  ]);

  if (workspace === null) {
    return <OfflineShell />;
  }

  const pulseSignals = [
    {
      label: "Trusted context",
      value: workspace.context_summary.trusted_count.toString(),
      tone: "cyan" as const,
      description:
        "Accepted evidence, packet answers, and source-backed records Ariadne can rely on when preparing recommendations.",
    },
    {
      label: "Needs review",
      value: workspace.context_summary.reviewable_count.toString(),
      tone: "copper" as const,
      description:
        "Drafts, route outputs, or candidate updates waiting for approval before they change capture work products.",
    },
    {
      label: "Open gaps",
      value: workspace.context_summary.gap_count.toString(),
      tone: "rose" as const,
      description:
        "Packet or workstream questions that still block confident briefing, action, research, or call-plan decisions.",
    },
    {
      label: "Source limits",
      value: workspace.context_summary.source_limitation_count.toString(),
      tone: "signal" as const,
      description:
        "Known data, document, crawl, provenance, or access limits Ariadne must work around before trusting an answer.",
    },
  ];

  const packetSignals = [
    {
      label: "Supported sections",
      value: workspace.packet.answered_section_count.toString(),
      tone: "cyan" as const,
      description:
        "Sections with enough accepted support to inform the Living Milestone Decision Briefing Packet.",
    },
    {
      label: "Partial sections",
      value: workspace.packet.partial_section_count.toString(),
      tone: "copper" as const,
      description:
        "Sections Ariadne can draft from current context, but where assumptions or review needs remain visible.",
    },
    {
      label: "Blocked sections",
      value: workspace.packet.gap_section_count.toString(),
      tone: "rose" as const,
      description:
        "Sections that need evidence, research, customer input, or a capability route before they can carry decisions.",
    },
  ];

  return (
    <main className="min-h-screen bg-ariadne-ink text-slate-100">
      <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-ariadne-line bg-black/30 p-5 xl:border-b-0 xl:border-r">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded border border-ariadne-cyan/50 bg-ariadne-cyan/10 text-ariadne-cyan">
              <BriefcaseBusiness size={21} aria-hidden />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
                Opportunity
              </p>
              <h1 className="text-lg font-semibold leading-tight">
                {workspace.opportunity.name}
              </h1>
            </div>
          </div>

          <dl className="mt-6 grid grid-cols-2 gap-3 text-sm xl:grid-cols-1">
            <Metric
              label="Lifecycle"
              value={formatLabel(workspace.opportunity.lifecycle_state)}
              tone="cyan"
            />
            <Metric
              label="Gate"
              value={formatLabel(workspace.opportunity.gate_status)}
              tone="copper"
            />
          </dl>

          <OpportunityPortfolioList
            opportunities={portfolio}
            selectedOpportunityId={workspace.opportunity.id}
          />

          <nav
            className="mt-7 space-y-2"
            aria-label="Command Center work modes"
          >
            {workspace.work_modes.map((mode) => {
              const ModeIcon = modeIcons[mode.id] ?? Layers3;
              return (
                <button className="mode-button" key={mode.id} type="button">
                  <span className="flex items-center gap-3">
                    <ModeIcon size={18} aria-hidden />
                    <span>{mode.label}</span>
                  </span>
                  {mode.pending_count > 0 ? (
                    <span className="mode-count">{mode.pending_count}</span>
                  ) : null}
                </button>
              );
            })}
          </nav>
        </aside>

        <section className="main-workspace p-5 sm:p-7">
          <div className="flex flex-col gap-4 border-b border-ariadne-line pb-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm text-ariadne-cyan">
                {workspace.opportunity.id}
              </p>
              <h2 className="mt-1 max-w-3xl text-2xl font-semibold leading-tight sm:text-3xl">
                {workspace.packet.title}
              </h2>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="inline-flex w-fit items-center gap-2 rounded border border-ariadne-signal/40 bg-ariadne-signal/10 px-3 py-2 text-sm text-ariadne-signal">
                <ShieldCheck size={17} aria-hidden />
                <span>{formatLabel(workspace.packet.readiness_label)}</span>
              </div>
              <OpportunityIntakePanel />
            </div>
          </div>

          {createdWorkspace ? (
            <section className="workspace-created-banner" aria-live="polite">
              <CheckCircle2 size={20} aria-hidden />
              <div>
                <p>Workspace created</p>
                <strong>{workspace.opportunity.name}</strong>
                <span>
                  Ariadne opened the new Opportunity and created the standard
                  workstreams, Living Packet structure, field slots, and first
                  activation digest.
                </span>
              </div>
              <a href={`/?opportunity_id=${encodeURIComponent(workspace.opportunity.id)}`}>
                Dismiss
              </a>
            </section>
          ) : null}

          <section
            className="workspace-section"
            aria-labelledby="pulse-check-title"
          >
            <div className="section-heading">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Pulse Check
                </p>
                <h3 id="pulse-check-title">Capture readiness signals</h3>
              </div>
              <Bot className="text-ariadne-cyan" size={22} aria-hidden />
            </div>
            <div className="signal-grid mt-4">
              {pulseSignals.map((signal) => (
                <PulseSignal key={signal.label} {...signal} />
              ))}
            </div>
          </section>

          <section
            className="workspace-section"
            aria-labelledby="packet-plan-title"
          >
            <div className="section-heading">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Living Packet
                </p>
                <h3 id="packet-plan-title">What the packet can support now</h3>
              </div>
              <FileText className="text-ariadne-copper" size={22} aria-hidden />
            </div>
            <div className="signal-grid mt-4 md:grid-cols-3">
              {packetSignals.map((signal) => (
                <PulseSignal key={signal.label} {...signal} />
              ))}
            </div>
          </section>

          <section
            className="workspace-section"
            aria-labelledby="work-map-title"
          >
            <div className="section-heading">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Work Map
                </p>
                <h3 id="work-map-title">Where Ariadne can act next</h3>
              </div>
              <Layers3 className="text-ariadne-cyan" size={22} aria-hidden />
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {workspace.layout_regions.map((region) => (
                <article className="region-panel" key={region.id}>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                    {formatLabel(region.id)}
                  </p>
                  <h3 className="mt-2 text-base font-semibold text-slate-100">
                    {region.label}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-slate-300">
                    {region.purpose}
                  </p>
                </article>
              ))}
            </div>
          </section>

          <AssistedCapturePanel
            goals={workspace.assisted_capture_goals}
            key={workspace.opportunity.id}
            opportunityId={workspace.opportunity.id}
          />

          {rendererReadiness !== null ? (
            <RendererReadinessPanel readiness={rendererReadiness} />
          ) : null}
        </section>
      </div>
    </main>
  );
}

function OpportunityPortfolioList({
  opportunities,
  selectedOpportunityId,
}: {
  opportunities: PortfolioOpportunity[];
  selectedOpportunityId: string;
}) {
  return (
    <section className="portfolio-panel" aria-labelledby="portfolio-title">
      <div className="portfolio-heading">
        <p>Portfolio</p>
        <span>{opportunities.length}</span>
      </div>
      <h2 id="portfolio-title">Managed Opportunities</h2>
      <div className="portfolio-list">
        {opportunities.map((opportunity) => {
          const isSelected = opportunity.id === selectedOpportunityId;
          const href = opportunity.is_demo
            ? "/"
            : `/?opportunity_id=${encodeURIComponent(opportunity.id)}`;
          return (
            <a
              aria-current={isSelected ? "page" : undefined}
              className={`portfolio-opportunity${isSelected ? " active" : ""}`}
              href={href}
              key={opportunity.id}
            >
              <span className="portfolio-opportunity-name">
                {opportunity.name}
              </span>
              <span className="portfolio-opportunity-meta">
                {formatLabel(opportunity.lifecycle_state)} / {formatLabel(opportunity.packet_readiness_label)}
              </span>
              <span className="portfolio-opportunity-status">
                {opportunity.is_demo ? <span>Demo</span> : null}
                {opportunity.blocked_field_count > 0 ? (
                  <span>{opportunity.blocked_field_count} fields</span>
                ) : null}
                {opportunity.review_ready_count > 0 ? (
                  <span>{opportunity.review_ready_count} reviews</span>
                ) : null}
              </span>
            </a>
          );
        })}
      </div>
    </section>
  );
}

function PulseSignal({
  label,
  value,
  description,
  tone,
}: {
  label: string;
  value: string;
  description: string;
  tone: SignalTone;
}) {
  return (
    <article className={`pulse-signal pulse-signal-${tone}`}>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
      <span>{description}</span>
    </article>
  );
}

function RendererReadinessPanel({
  readiness,
}: {
  readiness: RendererReadiness;
}) {
  const formatIcons: Record<string, typeof Presentation> = {
    pptx: Presentation,
    docx: FileText,
    xlsx: FileSpreadsheet,
  };

  return (
    <section className="renderer-readiness">
      <div className="flex flex-col gap-3 border-b border-ariadne-line pb-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-ariadne-cyan">
            Export readiness
          </p>
          <h3 className="mt-1 text-xl font-semibold">
            {readiness.target_label}
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
            {readiness.target_rationale}
          </p>
        </div>
        <Download className="text-ariadne-copper" size={24} aria-hidden />
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {readiness.export_actions.map((action) => {
          const FormatIcon = formatIcons[action.output_format] ?? FileText;
          return (
            <article className="export-action" key={action.id}>
              <div className="flex items-center justify-between gap-3">
                <FormatIcon
                  size={20}
                  className="text-ariadne-cyan"
                  aria-hidden
                />
                <span>{action.output_format.toUpperCase()}</span>
              </div>
              <h4 className="mt-3 text-sm font-semibold">{action.label}</h4>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                {action.disabled_reason}
              </p>
              <button
                className="command-button route-run-button"
                disabled
                type="button"
              >
                Export disabled
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: SignalTone;
}) {
  return (
    <div className={`metric metric-${tone}`}>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function OfflineShell() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-ariadne-ink p-6 text-slate-100">
      <section className="w-full max-w-xl border border-ariadne-line bg-ariadne-panel p-6">
        <p className="text-xs uppercase tracking-[0.18em] text-ariadne-cyan">
          Command Center
        </p>
        <h1 className="mt-3 text-2xl font-semibold">Backend offline</h1>
        <p className="mt-3 text-sm leading-6 text-slate-300">
          Start Ariadne on port 9622, then refresh this UI to load the
          Opportunity workspace.
        </p>
      </section>
    </main>
  );
}

function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function firstSearchParam(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
}
