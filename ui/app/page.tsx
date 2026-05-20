import {
  Archive,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronDown,
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
import {
  OpportunityActivationPanel,
  type OpportunityActivationRun,
} from "../components/OpportunityActivationPanel";
import { OpportunityIntakePanel } from "../components/OpportunityIntakePanel";

export const dynamic = "force-dynamic";

type Opportunity = {
  id: string;
  name: string;
  lifecycle_state: string;
  gate_status: string;
  portfolio_status: string;
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

type CommandMode = WorkMode & {
  description: string;
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
  portfolio_status: string;
  packet_readiness_label: string;
  review_ready_count: number;
  blocked_field_count: number;
  source_limitation_count: number;
  attention_reason?: string;
  attention_route_label?: string;
  attention_route_mode?: string;
  attention_field_key?: string | null;
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

type OpportunityActivationRunListResponse = {
  runs: OpportunityActivationRun[];
};

type PacketRoadmapField =
  OpportunityActivationRun["packet_field_action_matrix"]["fields"][number];

type PacketRoadmapSection = {
  id: string;
  label: string;
  total: number;
  answered: number;
  reviewReady: number;
  blocked: number;
};

type GlobalOpportunityPulseUrgency = "critical" | "review" | "watch" | "steady";

type GlobalOpportunityPulseItem = PortfolioOpportunity & {
  reason: string;
  score: number;
  urgency: GlobalOpportunityPulseUrgency;
  urgencyLabel: string;
};

type SignalTone = "cyan" | "copper" | "rose" | "signal";

type PulseSignalModel = {
  label: string;
  value: string;
  description: string;
  tone: SignalTone;
};

type CommandCenterSearchParams = {
  opportunity_id?: string | string[];
  created?: string | string[];
  mode?: string | string[];
  packet_field_key?: string | string[];
  route_goal?: string | string[];
};

type CommandCenterPageProps = {
  searchParams?: Promise<CommandCenterSearchParams>;
};

const modeIcons: Record<
  string,
  ComponentType<{ className?: string; size?: number }>
> = {
  pulse: ShieldCheck,
  packet: FileText,
  activation: SearchCheck,
  capture: Bot,
  actions: ClipboardCheck,
  engagement: MessageSquareText,
  research: SearchCheck,
  documents: FileStack,
  artifacts: Archive,
  capability_studio: Bot,
};

const workModeDescriptions: Record<string, string> = {
  pulse: "Readiness, blockers, review needs, and next best routes.",
  packet: "Living Packet coverage, support, gaps, and field-level routes.",
  activation: "Autonomy Digest, Packet Field Action Matrix, and review gate.",
  capture: "Goal-led assisted capture route recommendation and review loop.",
  actions: "Outcome tasks, urgency, owners, and action-plan AI support.",
  engagement: "Call plans, customer prep, meetings, and follow-up commitments.",
  research: "Capture research briefs, findings, lenses, and review candidates.",
  documents:
    "Document intake, extraction bundles, source spans, and parser gaps.",
  artifacts: "Draft readiness, renderer status, and future export paths.",
  capability_studio:
    "Advanced capability inventory, validation, runs, and provenance.",
};

const apiBaseUrl = process.env.ARIADNE_API_BASE_URL ?? "http://127.0.0.1:9622";

async function loadWorkspace(
  opportunityId?: string,
): Promise<Workspace | null> {
  try {
    const url = new URL(
      `${apiBaseUrl}/api/production-command-center/workspace`,
    );
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

async function loadLatestActivationRun(
  opportunityId: string,
): Promise<OpportunityActivationRun | null> {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/production-command-center/opportunities/${encodeURIComponent(opportunityId)}/activation-runs`,
      {
        cache: "no-store",
      },
    );
    if (!response.ok) {
      return null;
    }
    const body =
      (await response.json()) as OpportunityActivationRunListResponse;
    return (
      [...body.runs].sort(
        (firstRun, secondRun) =>
          activationTimestamp(secondRun) - activationTimestamp(firstRun),
      )[0] ?? null
    );
  } catch {
    return null;
  }
}

export default async function CommandCenterPage({
  searchParams,
}: CommandCenterPageProps) {
  const resolvedSearchParams =
    searchParams === undefined ? {} : await searchParams;
  const selectedOpportunityId = firstSearchParam(
    resolvedSearchParams.opportunity_id,
  );
  const requestedMode = firstSearchParam(resolvedSearchParams.mode);
  const requestedPacketFieldKey = firstSearchParam(
    resolvedSearchParams.packet_field_key,
  );
  const requestedRouteGoal = firstSearchParam(resolvedSearchParams.route_goal);
  const createdWorkspace =
    firstSearchParam(resolvedSearchParams.created) === "1";
  const [workspace, rendererReadiness, portfolio] = await Promise.all([
    loadWorkspace(selectedOpportunityId),
    loadRendererReadiness(),
    loadPortfolio(),
  ]);

  if (workspace === null) {
    return <OfflineShell />;
  }

  const latestActivationRun = await loadLatestActivationRun(
    workspace.opportunity.id,
  );
  const targetedPacketField =
    latestActivationRun?.packet_field_action_matrix.fields.find(
      (field) => field.field_key === requestedPacketFieldKey,
    );
  const initialRouteGoal =
    requestedRouteGoal ??
    (requestedPacketFieldKey !== undefined ? "close_packet_gap" : undefined);
  const commandModes = buildCommandModes(workspace.work_modes);
  const selectedModeId = normalizeCommandMode(requestedMode, commandModes);
  const selectedMode =
    commandModes.find((mode) => mode.id === selectedModeId) ?? commandModes[0];

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
                Command Center
              </p>
              <h1 className="text-lg font-semibold leading-tight">
                Capture workspace
              </h1>
            </div>
          </div>

          <OpportunityPortfolioSwitcher
            currentOpportunity={workspace.opportunity}
            opportunities={portfolio}
            selectedOpportunityId={workspace.opportunity.id}
          />

          <dl className="mt-6 grid grid-cols-2 gap-3 text-sm xl:grid-cols-1">
            <Metric
              label="Lifecycle"
              value={formatLabel(workspace.opportunity.lifecycle_state)}
              tone="cyan"
            />
            <Metric
              label="Milestone Gate"
              value={formatLabel(workspace.opportunity.gate_status)}
              tone="copper"
            />
            <Metric
              label="Portfolio"
              value={formatLabel(workspace.opportunity.portfolio_status)}
              tone="signal"
            />
          </dl>

          <nav
            className="mt-7 space-y-2"
            aria-label="Command Center work modes"
          >
            {commandModes.map((mode) => {
              const ModeIcon = modeIcons[mode.id] ?? Layers3;
              return (
                <a
                  aria-current={mode.id === selectedModeId ? "page" : undefined}
                  className={`mode-button${mode.id === selectedModeId ? " active" : ""}`}
                  href={modeHref(mode.id, workspace.opportunity.id)}
                  key={mode.id}
                >
                  <span className="flex items-center gap-3">
                    <ModeIcon size={18} aria-hidden />
                    <span>{mode.label}</span>
                  </span>
                  {mode.pending_count > 0 ? (
                    <span className="mode-count">{mode.pending_count}</span>
                  ) : null}
                </a>
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
              <a
                href={`/?opportunity_id=${encodeURIComponent(workspace.opportunity.id)}`}
              >
                Dismiss
              </a>
            </section>
          ) : null}

          <section className="mode-surface-heading" aria-live="polite">
            <div>
              <p>Work Mode</p>
              <h3>{selectedMode.label}</h3>
            </div>
            <span>{selectedMode.description}</span>
          </section>

          {selectedModeId === "pulse" ? (
            <CommandCenterHome
              latestActivationRun={latestActivationRun}
              packetSignals={packetSignals}
              portfolio={portfolio}
              pulseSignals={pulseSignals}
              regions={workspace.layout_regions}
              selectedOpportunityId={workspace.opportunity.id}
            />
          ) : null}

          {selectedModeId === "packet" ? (
            <PacketMode
              latestActivationRun={latestActivationRun}
              packetSignals={packetSignals}
              selectedOpportunityId={workspace.opportunity.id}
            />
          ) : null}

          {selectedModeId === "activation" ? (
            <OpportunityActivationPanel
              opportunityId={workspace.opportunity.id}
              run={latestActivationRun}
            />
          ) : null}

          {selectedModeId === "capture" ? (
            <AssistedCapturePanel
              goals={workspace.assisted_capture_goals}
              initialGoalId={initialRouteGoal}
              initialPacketFieldKey={requestedPacketFieldKey}
              initialPacketFieldLabel={targetedPacketField?.label}
              key={workspace.opportunity.id}
              opportunityId={workspace.opportunity.id}
            />
          ) : null}

          {selectedModeId === "artifacts" && rendererReadiness !== null ? (
            <RendererReadinessPanel readiness={rendererReadiness} />
          ) : null}

          {isPlaceholderMode(selectedModeId) ? (
            <FocusedModePlaceholder mode={selectedMode} />
          ) : null}
        </section>
      </div>
    </main>
  );
}

function OpportunityPortfolioSwitcher({
  currentOpportunity,
  opportunities,
  selectedOpportunityId,
}: {
  currentOpportunity: Opportunity;
  opportunities: PortfolioOpportunity[];
  selectedOpportunityId: string;
}) {
  const selectedOpportunity = opportunities.find(
    (opportunity) => opportunity.id === selectedOpportunityId,
  );
  const selectedName = selectedOpportunity?.name ?? currentOpportunity.name;
  const selectedLifecycle =
    selectedOpportunity?.lifecycle_state ?? currentOpportunity.lifecycle_state;
  const selectedPortfolioStatus =
    selectedOpportunity?.portfolio_status ?? currentOpportunity.portfolio_status;
  const selectedReadiness = selectedOpportunity?.packet_readiness_label;
  const groupedOpportunities = groupPortfolioOpportunities(opportunities);
  const activeCount = opportunities.filter(
    (opportunity) => opportunity.portfolio_status === "active",
  ).length;

  return (
    <section className="portfolio-switcher" aria-labelledby="portfolio-title">
      <div className="portfolio-switcher-heading">
        <p id="portfolio-title">Opportunity</p>
        <span>
          {opportunities.length} managed / {activeCount} active
        </span>
      </div>
      <details className="portfolio-dropdown">
        <summary
          aria-label={`Switch Opportunity workspace, current ${selectedName}`}
          className="portfolio-current"
        >
          <span>
            <span className="portfolio-current-name">{selectedName}</span>
            <span className="portfolio-current-meta">
              {formatLabel(selectedPortfolioStatus)} /{" "}
              {formatLabel(selectedLifecycle)}
              {selectedReadiness !== undefined
                ? ` / ${formatLabel(selectedReadiness)}`
                : null}
            </span>
          </span>
          <ChevronDown className="portfolio-chevron" size={18} aria-hidden />
        </summary>
        <nav className="portfolio-menu" aria-label="Managed Opportunities">
          {opportunities.length > 0 ? (
            groupedOpportunities.map((group) => (
              <div className="portfolio-menu-group" key={group.id}>
                <p className="portfolio-menu-group-heading">
                  {group.label} / {group.opportunities.length}
                </p>
                {group.opportunities.length > 0 ? (
                  group.opportunities.map((opportunity) => {
                    const isSelected = opportunity.id === selectedOpportunityId;
                    const href = opportunityAttentionHref(opportunity);
                    return (
                      <a
                        aria-current={isSelected ? "page" : undefined}
                        className={`portfolio-menu-link${isSelected ? " active" : ""}`}
                        href={href}
                        key={opportunity.id}
                      >
                        <span className="portfolio-opportunity-name">
                          {opportunity.name}
                        </span>
                        <span className="portfolio-opportunity-meta">
                          {formatLabel(opportunity.lifecycle_state)} /{" "}
                          {formatLabel(opportunity.packet_readiness_label)}
                        </span>
                        <span className="portfolio-opportunity-status">
                          <span className="portfolio-status-chip">
                            {formatLabel(opportunity.portfolio_status)}
                          </span>
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
                  })
                ) : (
                  <p className="portfolio-menu-group-empty">
                    No Opportunities
                  </p>
                )}
              </div>
            ))
          ) : (
            <p className="portfolio-empty">No saved Opportunities found.</p>
          )}
        </nav>
      </details>
    </section>
  );
}

function CommandCenterHome({
  latestActivationRun,
  packetSignals,
  portfolio,
  pulseSignals,
  regions,
  selectedOpportunityId,
}: {
  latestActivationRun: OpportunityActivationRun | null;
  packetSignals: PulseSignalModel[];
  portfolio: PortfolioOpportunity[];
  pulseSignals: PulseSignalModel[];
  regions: LayoutRegion[];
  selectedOpportunityId: string;
}) {
  const globalPulse = buildGlobalOpportunityPulse(
    portfolio,
    selectedOpportunityId,
  );
  const entryPoints = [
    {
      id: "activation",
      label: "Review activation matrix",
      description:
        "Inspect Autonomy Digest, field routes, and review-ready answers.",
    },
    {
      id: "capture",
      label: "Start assisted capture",
      description: "Pick a goal, inspect routes, run a bounded capture loop.",
    },
    {
      id: "artifacts",
      label: "Check artifact readiness",
      description: "See renderer readiness and blocked export paths.",
    },
  ];

  return (
    <>
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
        aria-labelledby="global-pulse-title"
      >
        <div className="section-heading">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
              Global Opportunity Pulse
            </p>
            <h3 id="global-pulse-title">Which roadmaps need attention</h3>
          </div>
          <BriefcaseBusiness
            className="text-ariadne-cyan"
            size={22}
            aria-hidden
          />
        </div>
        <div className="global-pulse-grid">
          {globalPulse.length > 0 ? (
            globalPulse.map((opportunity) => {
              const attentionHref = opportunityAttentionHref(opportunity);
              const routeLabel = opportunity.attention_field_key
                ? "Assisted capture"
                : formatLabel(opportunityAttentionMode(opportunity));
              return (
                <a
                  className={`global-pulse-card ${opportunityPulseToneClass(opportunity.urgency)}`}
                  href={attentionHref}
                  key={opportunity.id}
                  aria-current={
                    opportunity.id === selectedOpportunityId
                      ? "page"
                      : undefined
                  }
                >
                  <div className="global-pulse-card-heading">
                    <div>
                      <p>
                        {formatLabel(opportunity.portfolio_status)} /{" "}
                        {formatLabel(opportunity.lifecycle_state)}
                      </p>
                      <h4>{opportunity.name}</h4>
                    </div>
                    <span>{opportunity.urgencyLabel}</span>
                  </div>
                  <span className="global-pulse-reason">
                    {opportunity.reason}
                  </span>
                  <div className="global-pulse-chip-row">
                    <span>{formatLabel(opportunity.portfolio_status)}</span>
                    <span>
                      {formatLabel(opportunity.packet_readiness_label)}
                    </span>
                    <span>{routeLabel} route</span>
                    {opportunity.blocked_field_count > 0 ? (
                      <span>{opportunity.blocked_field_count} gaps</span>
                    ) : null}
                    {opportunity.review_ready_count > 0 ? (
                      <span>{opportunity.review_ready_count} reviews</span>
                    ) : null}
                    {opportunity.source_limitation_count > 0 ? (
                      <span>
                        {opportunity.source_limitation_count} source limits
                      </span>
                    ) : null}
                  </div>
                  <strong className="global-pulse-card-action">
                    {opportunity.attention_route_label ?? "Open roadmap"}
                  </strong>
                </a>
              );
            })
          ) : (
            <article className="global-pulse-empty">
              No managed Opportunities yet. Create one to begin activation.
            </article>
          )}
        </div>
      </section>

      <section className="workspace-section" aria-labelledby="home-route-title">
        <div className="section-heading">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
              Next Routes
            </p>
            <h3 id="home-route-title">Focused places to act</h3>
          </div>
          <Layers3 className="text-ariadne-cyan" size={22} aria-hidden />
        </div>
        <div className="mode-entry-grid">
          {entryPoints.map((entry) => (
            <a
              className="mode-entry-card"
              href={modeHref(entry.id, selectedOpportunityId)}
              key={entry.id}
            >
              <strong>{entry.label}</strong>
              <span>{entry.description}</span>
            </a>
          ))}
        </div>
      </section>

      <PacketMode
        latestActivationRun={latestActivationRun}
        packetSignals={packetSignals}
        selectedOpportunityId={selectedOpportunityId}
        compact
      />

      <section className="workspace-section" aria-labelledby="work-map-title">
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
          {regions.map((region) => (
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
    </>
  );
}

function PacketMode({
  compact = false,
  latestActivationRun,
  packetSignals,
  selectedOpportunityId,
}: {
  compact?: boolean;
  latestActivationRun: OpportunityActivationRun | null;
  packetSignals: PulseSignalModel[];
  selectedOpportunityId: string;
}) {
  const matrix = latestActivationRun?.packet_field_action_matrix;
  const currentGateLabel = formatLabel(
    matrix?.current_milestone_gate ?? "milestone_1",
  );
  const currentGateFields = (matrix?.fields ?? []).filter(
    (field) => field.current_gate_required !== false,
  );
  const roadmapFields = [
    ...(currentGateFields.length > 0
      ? currentGateFields
      : (matrix?.fields ?? [])),
  ].sort(compareRoadmapFields);
  const roadmapSections = buildRoadmapSections(roadmapFields);
  const supportedFields = roadmapFields.filter(isRoadmapFieldAnswered);
  const needsActionFields = roadmapFields.filter((field) =>
    isRoadmapFieldActionable(field),
  );

  return (
    <>
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

      {!compact && matrix !== undefined ? (
        <>
          <section
            className="workspace-section"
            aria-labelledby="packet-roadmap-title"
          >
            <div className="section-heading">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Milestone Roadmap
                </p>
                <h3 id="packet-roadmap-title">
                  Data elements for {currentGateLabel}
                </h3>
              </div>
              <ClipboardCheck
                className="text-ariadne-cyan"
                size={22}
                aria-hidden
              />
            </div>
            <div className="packet-roadmap-grid">
              {roadmapSections.map((section) => (
                <article className="packet-section-card" key={section.id}>
                  <div>
                    <p>{section.label}</p>
                    <strong>{section.total} fields</strong>
                  </div>
                  <span>
                    {section.answered} supported / {section.reviewReady} review
                    / {section.blocked} gaps
                  </span>
                </article>
              ))}
            </div>
          </section>

          <section
            className="workspace-section"
            aria-labelledby="packet-field-roadmap-title"
          >
            <div className="section-heading">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Packet Field Routes
                </p>
                <h3 id="packet-field-roadmap-title">
                  How to populate missing answers
                </h3>
              </div>
              <SearchCheck
                className="text-ariadne-copper"
                size={22}
                aria-hidden
              />
            </div>
            <div className="packet-field-grid">
              {needsActionFields.length > 0 ? (
                needsActionFields.map((field) => (
                  <PacketRoadmapFieldCard
                    field={field}
                    key={field.field_key}
                    selectedOpportunityId={selectedOpportunityId}
                  />
                ))
              ) : (
                <article className="packet-field-empty">
                  <CheckCircle2 size={20} aria-hidden />
                  <div>
                    <p>No open packet field gaps in latest activation run.</p>
                    <span>
                      Review accepted answers, source support, and assumptions
                      before treating packet as gate-ready.
                    </span>
                  </div>
                </article>
              )}
            </div>
          </section>

          {supportedFields.length > 0 ? (
            <section
              className="workspace-section"
              aria-labelledby="packet-supported-answer-title"
            >
              <div className="section-heading">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    Supported Answers
                  </p>
                  <h3 id="packet-supported-answer-title">
                    Packet fields already carrying trusted values
                  </h3>
                </div>
                <CheckCircle2
                  className="text-ariadne-cyan"
                  size={22}
                  aria-hidden
                />
              </div>
              <div className="packet-field-grid">
                {supportedFields.map((field) => (
                  <SupportedPacketFieldCard
                    field={field}
                    key={field.field_key}
                  />
                ))}
              </div>
            </section>
          ) : null}

          <section
            className="workspace-section packet-content-lane"
            aria-labelledby="packet-content-title"
          >
            <div>
              <p>Packet Content Opportunities</p>
              <h3 id="packet-content-title">
                Visual or add-on content can be staged, not rendered yet.
              </h3>
            </div>
            <span>
              Ariadne can route ideas like synopsis visuals, timelines,
              capability maps, customer-org views, or partner ecosystem blocks
              into Artifact mode. huashu-design/PPTX rendering stays disabled
              until renderer adapters exist.
            </span>
            <a
              className="packet-action-link"
              href={modeHref("artifacts", selectedOpportunityId)}
            >
              Check renderer readiness
            </a>
          </section>
        </>
      ) : null}

      {!compact && matrix === undefined ? (
        <section className="focused-mode-placeholder">
          <p>Packet roadmap unavailable</p>
          <h3>Run activation to build field routes.</h3>
          <span>
            Packet Mode needs an Opportunity Activation Run before it can show
            field-level gaps, route recommendations, and source limitations.
          </span>
          <a
            className="packet-action-link mt-4"
            href={modeHref("activation", selectedOpportunityId)}
          >
            Open Activation mode
          </a>
        </section>
      ) : null}
    </>
  );
}

function PacketRoadmapFieldCard({
  field,
  selectedOpportunityId,
}: {
  field: PacketRoadmapField;
  selectedOpportunityId: string;
}) {
  const routeHref = modeHref("capture", selectedOpportunityId, {
    packet_field_key: field.field_key,
    route_goal: "close_packet_gap",
  });
  return (
    <article className={`packet-field-card ${packetFieldToneClass(field)}`}>
      <div className="packet-field-card-heading">
        <div>
          <p>{formatLabel(field.section)}</p>
          <h4>{field.label}</h4>
        </div>
        <span>{formatLabel(field.current_status)}</span>
      </div>
      <p className="packet-field-question">{field.question}</p>
      {field.current_value !== null && field.current_value.length > 0 ? (
        <p className="packet-field-value">{field.current_value}</p>
      ) : null}
      <div className="packet-field-status-row">
        <span>{formatLabel(field.evidence_status)}</span>
        {field.requires_review ? <span>Needs review</span> : null}
        {field.current_gate_required !== false ? (
          <span>Required this gate</span>
        ) : null}
        {field.approval_required ? <span>Approval</span> : null}
        {field.source_refs.length > 0 ? (
          <span>{field.source_refs.length} sources</span>
        ) : null}
      </div>
      <p className="packet-field-gap">
        {field.gap_summary ?? field.route_rationale}
      </p>
      <div className="packet-field-route-row">
        <span>{field.recommended_route}</span>
        <a className="packet-action-link" href={routeHref}>
          Start route
        </a>
      </div>
    </article>
  );
}

function SupportedPacketFieldCard({ field }: { field: PacketRoadmapField }) {
  return (
    <article className="packet-field-card packet-field-card-supported">
      <div className="packet-field-card-heading">
        <div>
          <p>{formatLabel(field.section)}</p>
          <h4>{field.label}</h4>
        </div>
        <span>{formatLabel(field.evidence_status)}</span>
      </div>
      <p className="packet-field-value">
        {field.current_value ?? "Accepted packet answer"}
      </p>
      <div className="packet-field-status-row">
        <span>{formatLabel(field.current_status)}</span>
        {field.current_gate_required !== false ? (
          <span>Required this gate</span>
        ) : null}
        {field.source_refs.length > 0 ? (
          <span>{field.source_refs.length} sources</span>
        ) : null}
      </div>
      <p className="packet-field-gap">Review source support before gate use.</p>
    </article>
  );
}

function FocusedModePlaceholder({ mode }: { mode: CommandMode }) {
  return (
    <section className="focused-mode-placeholder">
      <p>{mode.label}</p>
      <h3>Focused surface not built yet.</h3>
      <span>
        {mode.description} This mode is now routed separately so future work can
        land here without expanding Command Center Home into one huge page.
      </span>
    </section>
  );
}

function PulseSignal({ label, value, description, tone }: PulseSignalModel) {
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

function firstSearchParam(
  value: string | string[] | undefined,
): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
}

function buildCommandModes(workModes: WorkMode[]): CommandMode[] {
  const backendModes = new Map(workModes.map((mode) => [mode.id, mode]));
  const orderedIds = [
    "pulse",
    "packet",
    "activation",
    "capture",
    "actions",
    "engagement",
    "research",
    "documents",
    "artifacts",
  ];
  const orderedModes = orderedIds.map((id) => {
    const backendMode = backendModes.get(id);
    return {
      id,
      label: backendMode?.label ?? formatLabel(id),
      pending_count: backendMode?.pending_count ?? 0,
      description:
        workModeDescriptions[id] ?? "Focused Command Center work mode.",
    };
  });
  const extraModes = workModes
    .filter((mode) => !orderedIds.includes(mode.id))
    .map((mode) => ({
      ...mode,
      description:
        workModeDescriptions[mode.id] ?? "Focused Command Center work mode.",
    }));
  return [...orderedModes, ...extraModes];
}

function normalizeCommandMode(
  requestedMode: string | undefined,
  commandModes: CommandMode[],
): string {
  if (
    requestedMode !== undefined &&
    commandModes.some((mode) => mode.id === requestedMode)
  ) {
    return requestedMode;
  }
  return "pulse";
}

function modeHref(
  modeId: string,
  opportunityId: string,
  extraParams: Record<string, string | undefined> = {},
): string {
  const params = new URLSearchParams({
    opportunity_id: opportunityId,
    mode: modeId,
  });
  Object.entries(extraParams).forEach(([key, value]) => {
    if (value !== undefined) {
      params.set(key, value);
    }
  });
  return `/?${params.toString()}`;
}

function opportunityAttentionHref(opportunity: PortfolioOpportunity): string {
  if (opportunity.attention_field_key) {
    return modeHref("capture", opportunity.id, {
      packet_field_key: opportunity.attention_field_key,
      route_goal: "close_packet_gap",
    });
  }
  return modeHref(opportunityAttentionMode(opportunity), opportunity.id);
}

function opportunityAttentionMode(opportunity: PortfolioOpportunity): string {
  return (
    opportunity.attention_route_mode ??
    modeForPacketRoute(opportunity.attention_reason ?? "")
  );
}

function isPlaceholderMode(modeId: string): boolean {
  return [
    "actions",
    "engagement",
    "research",
    "documents",
    "capability_studio",
  ].includes(modeId);
}

function buildGlobalOpportunityPulse(
  opportunities: PortfolioOpportunity[],
  selectedOpportunityId: string,
): GlobalOpportunityPulseItem[] {
  const managedOpportunities = opportunities.filter(
    (opportunity) => !opportunity.is_demo,
  );
  const pulseCandidates =
    managedOpportunities.length > 0 ? managedOpportunities : opportunities;

  return pulseCandidates
    .map((opportunity) => {
      const score = opportunityPulseScore(opportunity);
      return {
        ...opportunity,
        reason: opportunityPulseReason(opportunity),
        score,
        urgency: opportunityPulseUrgency(opportunity, score),
        urgencyLabel: opportunityPulseUrgencyLabel(opportunity, score),
      };
    })
    .sort((firstOpportunity, secondOpportunity) => {
      const scoreDifference = secondOpportunity.score - firstOpportunity.score;
      if (scoreDifference !== 0) {
        return scoreDifference;
      }
      if (firstOpportunity.id === selectedOpportunityId) {
        return -1;
      }
      if (secondOpportunity.id === selectedOpportunityId) {
        return 1;
      }
      return firstOpportunity.name.localeCompare(secondOpportunity.name);
    })
    .slice(0, 6);
}

function groupPortfolioOpportunities(
  opportunities: PortfolioOpportunity[],
): Array<{
  id: string;
  label: string;
  opportunities: PortfolioOpportunity[];
}> {
  const groups = [
    { id: "active", label: "Active" },
    { id: "future", label: "Future / Watchlist" },
    { id: "held", label: "Held" },
    { id: "past", label: "Past / Archive" },
  ];
  return groups.map((group) => ({
    ...group,
    opportunities: opportunities
      .filter((opportunity) => portfolioGroupId(opportunity) === group.id)
      .sort((firstOpportunity, secondOpportunity) =>
        firstOpportunity.name.localeCompare(secondOpportunity.name),
      ),
  }));
}

function portfolioGroupId(opportunity: PortfolioOpportunity): string {
  if (opportunity.is_demo || opportunity.portfolio_status === "active") {
    return "active";
  }
  if (
    opportunity.portfolio_status === "future" ||
    opportunity.portfolio_status === "watchlist"
  ) {
    return "future";
  }
  if (opportunity.portfolio_status === "held") {
    return "held";
  }
  return "past";
}

function opportunityPulseScore(opportunity: PortfolioOpportunity): number {
  const readinessScore =
    opportunity.packet_readiness_label === "not_ready"
      ? 4
      : opportunity.packet_readiness_label === "draft_ready"
        ? 2
        : 0;
  const statusScore =
    opportunity.portfolio_status === "active"
      ? 4
      : opportunity.portfolio_status === "future" ||
          opportunity.portfolio_status === "watchlist"
        ? 2
        : opportunity.portfolio_status === "held"
          ? 1
          : 0;
  return (
    opportunity.blocked_field_count * 5 +
    opportunity.review_ready_count * 3 +
    opportunity.source_limitation_count * 2 +
    readinessScore +
    statusScore
  );
}

function opportunityPulseReason(opportunity: PortfolioOpportunity): string {
  if (opportunity.attention_reason) {
    return opportunity.attention_reason;
  }
  if (
    ["archived", "won", "lost"].includes(opportunity.portfolio_status)
  ) {
    return `${formatLabel(opportunity.portfolio_status)} Opportunity. Open roadmap for trace and lessons.`;
  }
  if (opportunity.blocked_field_count > 0) {
    return `${opportunity.blocked_field_count} packet fields still block this roadmap.`;
  }
  if (opportunity.review_ready_count > 0) {
    return `${opportunity.review_ready_count} review items can improve packet readiness.`;
  }
  if (opportunity.source_limitation_count > 0) {
    return `${opportunity.source_limitation_count} source limits need review before trusting answers.`;
  }
  if (opportunity.packet_readiness_label !== "decision_ready") {
    return `${formatLabel(opportunity.packet_readiness_label)} packet. Open roadmap for next gaps.`;
  }
  return "Roadmap has no urgent gaps in current pulse data.";
}

function opportunityPulseUrgency(
  opportunity: PortfolioOpportunity,
  score: number,
): GlobalOpportunityPulseUrgency {
  if (opportunity.blocked_field_count > 0 || score >= 8) {
    return "critical";
  }
  if (opportunity.review_ready_count > 0) {
    return "review";
  }
  if (
    opportunity.source_limitation_count > 0 ||
    opportunity.packet_readiness_label !== "decision_ready"
  ) {
    return "watch";
  }
  return "steady";
}

function opportunityPulseUrgencyLabel(
  opportunity: PortfolioOpportunity,
  score: number,
): string {
  const urgency = opportunityPulseUrgency(opportunity, score);
  if (urgency === "critical") {
    return "Needs action";
  }
  if (urgency === "review") {
    return "Review ready";
  }
  if (urgency === "watch") {
    return "Watch";
  }
  return "Steady";
}

function opportunityPulseToneClass(
  urgency: GlobalOpportunityPulseUrgency,
): string {
  return `global-pulse-card-${urgency}`;
}

function buildRoadmapSections(
  fields: PacketRoadmapField[],
): PacketRoadmapSection[] {
  const sections = new Map<string, PacketRoadmapSection>();
  fields.forEach((field) => {
    const section = sections.get(field.section) ?? {
      id: field.section,
      label: formatLabel(field.section),
      total: 0,
      answered: 0,
      reviewReady: 0,
      blocked: 0,
    };
    section.total += 1;
    if (isRoadmapFieldAnswered(field)) {
      section.answered += 1;
    } else if (field.action_state === "review_ready") {
      section.reviewReady += 1;
    } else {
      section.blocked += 1;
    }
    sections.set(field.section, section);
  });
  return [...sections.values()];
}

function compareRoadmapFields(
  firstField: PacketRoadmapField,
  secondField: PacketRoadmapField,
): number {
  const currentGateDelta =
    Number(secondField.current_gate_required !== false) -
    Number(firstField.current_gate_required !== false);
  if (currentGateDelta !== 0) {
    return currentGateDelta;
  }
  const priorityDelta =
    roadmapFieldPriority(firstField) - roadmapFieldPriority(secondField);
  if (priorityDelta !== 0) {
    return priorityDelta;
  }
  return firstField.label.localeCompare(secondField.label);
}

function roadmapFieldPriority(field: PacketRoadmapField): number {
  if (field.approval_required) {
    return 0;
  }
  if (field.requires_review) {
    return 1;
  }
  if (!isRoadmapFieldAnswered(field)) {
    return 2;
  }
  return 3;
}

function isRoadmapFieldActionable(field: PacketRoadmapField): boolean {
  return (
    !isRoadmapFieldAnswered(field) ||
    field.requires_review ||
    field.approval_required ||
    field.gap_summary !== null
  );
}

function isRoadmapFieldAnswered(field: PacketRoadmapField): boolean {
  return (
    field.current_status === "answered" || field.evidence_status === "answered"
  );
}

function packetFieldToneClass(field: PacketRoadmapField): string {
  if (field.approval_required || !isRoadmapFieldAnswered(field)) {
    return "packet-field-card-gap";
  }
  if (field.requires_review) {
    return "packet-field-card-review";
  }
  return "packet-field-card-supported";
}

function modeForPacketRoute(route: string): string {
  const normalizedRoute = route.toLowerCase();
  if (
    normalizedRoute.includes("document") ||
    normalizedRoute.includes("source") ||
    normalizedRoute.includes("parser")
  ) {
    return "documents";
  }
  if (
    normalizedRoute.includes("research") ||
    normalizedRoute.includes("competitor") ||
    normalizedRoute.includes("teaming") ||
    normalizedRoute.includes("partner")
  ) {
    return "research";
  }
  if (
    normalizedRoute.includes("call") ||
    normalizedRoute.includes("customer") ||
    normalizedRoute.includes("engagement")
  ) {
    return "engagement";
  }
  if (
    normalizedRoute.includes("artifact") ||
    normalizedRoute.includes("visual") ||
    normalizedRoute.includes("renderer") ||
    normalizedRoute.includes("export")
  ) {
    return "artifacts";
  }
  return "activation";
}

function activationTimestamp(run: OpportunityActivationRun): number {
  const timestamp = Date.parse(run.completed_at ?? run.created_at);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}
