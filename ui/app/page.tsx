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
  next_action_urgency: string;
  source_freshness_label: string;
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

type WorkProductUpdateProjection = {
  id: string;
  source_output_id: string;
  review_decision_id: string;
  destination: string;
  state: string;
  before_summary: string;
  after_summary: string;
  source_refs: string[];
};

type WorkProductUpdateListResponse = {
  updates: WorkProductUpdateProjection[];
  summary: Record<string, number>;
};

type CaptureResearchProvider = {
  provider_id: string;
  provider_name: string;
  role: string;
  source_mode: string;
  status: string;
  diagnostic_summary: string;
  source_limitations: string[];
};

type CaptureResearchSourceRegistry = {
  providers: CaptureResearchProvider[];
  quality_status: string;
  quality_summary: string;
  recommended_provider_ids: string[];
};

type CaptureResearchSourceProviderResponse = {
  registry: CaptureResearchSourceRegistry;
};

type CaptureResearchSignal = {
  id: string;
  summary: string;
  confidence?: number;
  review_state?: string;
  target_workflow?: string;
  source_limitations?: string[];
  follow_up_needs?: string[];
};

type CaptureResearchLensAnalysis = {
  id: string;
  lens: string;
  summary: string;
  signals: CaptureResearchSignal[];
  review_state: string;
};

type CaptureResearchCandidate = {
  id: string;
  title?: string;
  summary?: string;
  candidate_group?: string;
  candidate_group_label?: string;
  candidate_type?: string;
  review_state?: string;
  selected_lens?: string | null;
  trusted_output_written?: boolean;
  supporting_source_finding_ids?: string[];
};

type CaptureResearchRun = {
  research_run_id: string;
  opportunity_id: string | null;
  status: string;
  research_brief: {
    research_question: string;
    known_pivots: string[];
    source_targets: string[];
    selected_lenses: string[];
    evidence_goals: string[];
    source_limits: string[];
    approval_basis: string;
  };
  research_trigger_context: {
    trigger_type: string;
    summary: string;
    captured_at: string;
  };
  user_prompt: { prompt: string } | null;
  selected_lenses: string[];
  source_collection_records: unknown[];
  source_findings: {
    id: string;
    source_target: string;
    title: string;
    url: string;
    excerpt: string;
    confidence: number;
    source_limitations: string[];
    source_mode: string;
  }[];
  capture_lens_analyses: CaptureResearchLensAnalysis[];
  downstream_candidates: CaptureResearchCandidate[];
  research_summary_view: string | null;
  review_decisions: unknown[];
  created_at: string;
  updated_at: string;
};

type CaptureResearchRunListResponse = {
  runs: CaptureResearchRun[];
};

type DocumentIntakeRecord = {
  id: string;
  source_ref: string;
  filename: string | null;
  mime_type: string | null;
  byte_size: number;
  material_type: string | null;
  content_type: string;
  status: string;
  queue_state: string | null;
  opportunity_id: string | null;
  warnings: string[];
  capability_hint: string;
  extraction_bundle_id: string | null;
  extraction_status: string | null;
  extraction_review_status: string | null;
  extraction_warning_count: number;
  created_at: string;
  updated_at: string;
};

type DocumentIntakeDraftPart = {
  id: string;
  part_type: string;
  content: string;
  recommended_route: string;
  suggested_skill_chain: string[];
  source_intake_record_id: string | null;
  source_extraction_bundle_id: string | null;
  source_span_ids: string[];
  recommendation: string | null;
  assumptions: string[];
  confidence_notes: string[];
};

type DocumentIntakeDraft = {
  id: string;
  raw_item_id: string;
  opportunity_id: string | null;
  status: string;
  polished_capture: string;
  clarity_status: string;
  assumptions: string[];
  confidence_notes: string[];
  gaps: string[];
  intelligence_pieces: DocumentIntakeDraftPart[];
  extraction_bundle_id: string | null;
  extraction_document_id: string | null;
  extracted_source_span_ids: string[];
  extraction_warnings_summarized: string | null;
};

type DocumentIntakeCaptureCandidate = {
  id: string;
  candidate_type: string;
  title: string;
  content: string;
  target_workflow: string;
  recommendation: string;
  rationale: string;
  confidence: number | null;
  review_state: string;
  trusted_output_written: boolean;
  source_intake_record_id: string;
  source_extraction_bundle_id: string;
  source_draft_id: string;
  source_draft_part_id: string;
  source_span_ids: string[];
  suggested_skill_chain: string[];
};

type DocumentIntakeCapability = {
  id: string;
  name: string;
  adapter_kind: string;
  status: string;
  supported_material_types: string[];
  expected_output_contract: string;
  capability_hint: string;
  deferred_reason: string | null;
  external_tool_invocation_allowed: boolean;
};

type DocumentIntakeQueueResponse = {
  records: DocumentIntakeRecord[];
};

type DocumentIntakeExtractionDraftsResponse = {
  drafts: DocumentIntakeDraft[];
};

type DocumentIntakeCaptureCandidatesResponse = {
  candidates: DocumentIntakeCaptureCandidate[];
};

type DocumentIntakeCapabilitiesResponse = {
  capabilities: DocumentIntakeCapability[];
  available_count: number;
  deferred_count: number;
  extraction_bundle_boundary: string;
};

type CapabilityCatalogEntry = {
  id: string;
  name: string;
  description: string;
  capability_type: string;
  source_path: string;
  maturity: string;
  validation_status: string;
  lifecycle_fit: string[];
  workstream_fit: string[];
  product_workflow_fit: string[];
  provenance_note: string;
};

type CapabilityCatalog = {
  entries: CapabilityCatalogEntry[];
  indexed_at: string;
  read_only: boolean;
  canonical_locations: string[];
};

type CapabilityRunReviewDecision = {
  decision_id: string;
  output_id: string;
  decision: string;
  reviewer_rationale: string;
  routed_destination: string | null;
  decided_at: string;
};

type CapabilityRunOutput = {
  output_id: string;
  output_type: string;
  title: string;
  summary: string;
  gaps: string[];
  review_state: string;
  autonomy_recommendation: string;
  recommended_destination: string | null;
  review_decisions: CapabilityRunReviewDecision[];
  provenance: Record<string, unknown>;
};

type CapabilityRun = {
  run_id: string;
  capability_id: string;
  capability_type: string;
  executor_kind: string;
  session_context: string;
  opportunity_id: string | null;
  product_workflow: string;
  status: string;
  inputs_summary: string;
  input_refs: string[];
  outputs: CapabilityRunOutput[];
  provenance: Record<string, unknown>;
  created_at: string;
  completed_at: string | null;
};

type CapabilityRunListResponse = {
  runs: CapabilityRun[];
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

type LivePacketSection = PacketRoadmapSection & {
  fields: PacketRoadmapField[];
  routeKinds: string[];
  sourceCount: number;
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

async function loadWorkProductUpdates(
  opportunityId: string,
  destination: string,
): Promise<WorkProductUpdateProjection[]> {
  try {
    const url = new URL(
      `${apiBaseUrl}/api/production-command-center/work-product-updates`,
    );
    url.searchParams.set("opportunity_id", opportunityId);
    url.searchParams.set("destination", destination);
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    const body = (await response.json()) as WorkProductUpdateListResponse;
    return body.updates;
  } catch {
    return [];
  }
}

async function loadCaptureResearchRuns(
  opportunityId: string,
): Promise<CaptureResearchRun[]> {
  try {
    const url = new URL(`${apiBaseUrl}/api/capture-research/runs`);
    url.searchParams.set("opportunity_id", opportunityId);
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    const body = (await response.json()) as CaptureResearchRunListResponse;
    return [...body.runs].sort(
      (firstRun, secondRun) =>
        Date.parse(secondRun.updated_at) - Date.parse(firstRun.updated_at),
    );
  } catch {
    return [];
  }
}

async function loadCaptureResearchSourceRegistry(): Promise<CaptureResearchSourceRegistry | null> {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/capture-research/source-providers`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return null;
    }
    const body =
      (await response.json()) as CaptureResearchSourceProviderResponse;
    return body.registry;
  } catch {
    return null;
  }
}

async function loadDocumentIntakeRecords(): Promise<DocumentIntakeRecord[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/document-intake/queue`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return [];
    }
    const body = (await response.json()) as DocumentIntakeQueueResponse;
    return [...body.records].sort(
      (firstRecord, secondRecord) =>
        Date.parse(secondRecord.updated_at) - Date.parse(firstRecord.updated_at),
    );
  } catch {
    return [];
  }
}

async function loadDocumentIntakeDrafts(): Promise<DocumentIntakeDraft[]> {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/document-intake/extraction-drafts`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return [];
    }
    const body =
      (await response.json()) as DocumentIntakeExtractionDraftsResponse;
    return body.drafts;
  } catch {
    return [];
  }
}

async function loadDocumentIntakeCandidates(): Promise<
  DocumentIntakeCaptureCandidate[]
> {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/document-intake/capture-candidates`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return [];
    }
    const body =
      (await response.json()) as DocumentIntakeCaptureCandidatesResponse;
    return body.candidates;
  } catch {
    return [];
  }
}

async function loadDocumentIntakeCapabilities(): Promise<DocumentIntakeCapabilitiesResponse | null> {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/document-intake/capabilities`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as DocumentIntakeCapabilitiesResponse;
  } catch {
    return null;
  }
}

async function loadCapabilityRuns(): Promise<CapabilityRun[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/capability-runs`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return [];
    }
    const body = (await response.json()) as CapabilityRunListResponse;
    return [...body.runs].sort(
      (firstRun, secondRun) =>
        Date.parse(secondRun.completed_at ?? secondRun.created_at) -
        Date.parse(firstRun.completed_at ?? firstRun.created_at),
    );
  } catch {
    return [];
  }
}

async function loadCapabilityCatalog(): Promise<CapabilityCatalog | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/capabilities/catalog`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as CapabilityCatalog;
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

  const [
    latestActivationRun,
    actionPlanUpdates,
    callPlanUpdates,
    researchRuns,
    researchSourceRegistry,
    documentRecords,
    documentDrafts,
    documentCandidates,
    documentCapabilities,
    capabilityRuns,
    capabilityCatalog,
  ] = await Promise.all([
      loadLatestActivationRun(workspace.opportunity.id),
      loadWorkProductUpdates(workspace.opportunity.id, "action_plan"),
      loadWorkProductUpdates(workspace.opportunity.id, "call_plan"),
      loadCaptureResearchRuns(workspace.opportunity.id),
      loadCaptureResearchSourceRegistry(),
      loadDocumentIntakeRecords(),
      loadDocumentIntakeDrafts(),
      loadDocumentIntakeCandidates(),
      loadDocumentIntakeCapabilities(),
      loadCapabilityRuns(),
      loadCapabilityCatalog(),
    ]);
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

          {selectedModeId === "actions" ? (
            <ActionPlanMode
              latestActivationRun={latestActivationRun}
              selectedOpportunityId={workspace.opportunity.id}
              updates={actionPlanUpdates}
            />
          ) : null}

          {selectedModeId === "engagement" ? (
            <EngagementMode
              latestActivationRun={latestActivationRun}
              selectedOpportunityId={workspace.opportunity.id}
              updates={callPlanUpdates}
            />
          ) : null}

          {selectedModeId === "research" ? (
            <ResearchMode
              latestActivationRun={latestActivationRun}
              runs={researchRuns}
              selectedOpportunityId={workspace.opportunity.id}
              sourceRegistry={researchSourceRegistry}
            />
          ) : null}

          {selectedModeId === "documents" ? (
            <DocumentsMode
              capabilities={documentCapabilities}
              candidates={documentCandidates}
              drafts={documentDrafts}
              latestActivationRun={latestActivationRun}
              records={documentRecords}
              selectedOpportunityId={workspace.opportunity.id}
            />
          ) : null}

          {selectedModeId === "artifacts" && rendererReadiness !== null ? (
            <RendererReadinessPanel readiness={rendererReadiness} />
          ) : null}

          {selectedModeId === "capability_studio" ? (
            <CapabilityStudioMode
              catalog={capabilityCatalog}
              runs={capabilityRuns}
              selectedOpportunityId={workspace.opportunity.id}
            />
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
    selectedOpportunity?.portfolio_status ??
    currentOpportunity.portfolio_status;
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
                          <span className="portfolio-urgency-chip">
                            {formatLabel(opportunity.next_action_urgency)}
                          </span>
                          <span className="portfolio-source-chip">
                            {formatLabel(opportunity.source_freshness_label)}
                          </span>
                          {opportunity.is_demo ? <span>Demo</span> : null}
                          {opportunity.blocked_field_count > 0 ? (
                            <span>
                              {opportunity.blocked_field_count} fields
                            </span>
                          ) : null}
                          {opportunity.review_ready_count > 0 ? (
                            <span>
                              {opportunity.review_ready_count} reviews
                            </span>
                          ) : null}
                        </span>
                      </a>
                    );
                  })
                ) : (
                  <p className="portfolio-menu-group-empty">No Opportunities</p>
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
                    <span>{formatLabel(opportunity.next_action_urgency)}</span>
                    <span>{formatLabel(opportunity.source_freshness_label)}</span>
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
  const livePacketSections = buildLivePacketSections(roadmapFields);
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
            aria-labelledby="live-packet-title"
          >
            <div className="section-heading">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Living Packet Live View
                </p>
                <h3 id="live-packet-title">
                  Sections, data elements, support, routes
                </h3>
              </div>
              <FileText className="text-ariadne-cyan" size={22} aria-hidden />
            </div>
            <LivingPacketLiveView
              currentGateLabel={currentGateLabel}
              sections={livePacketSections}
              selectedOpportunityId={selectedOpportunityId}
            />
          </section>

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
  const routeHref = packetFieldRouteHref(field, selectedOpportunityId);
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

function LivingPacketLiveView({
  currentGateLabel,
  sections,
  selectedOpportunityId,
}: {
  currentGateLabel: string;
  sections: LivePacketSection[];
  selectedOpportunityId: string;
}) {
  const totalFields = sections.reduce(
    (count, section) => count + section.total,
    0,
  );
  const supportedFields = sections.reduce(
    (count, section) => count + section.answered,
    0,
  );
  const reviewFields = sections.reduce(
    (count, section) => count + section.reviewReady,
    0,
  );
  const blockedFields = sections.reduce(
    (count, section) => count + section.blocked,
    0,
  );

  return (
    <div className="live-packet-view">
      <div className="live-packet-summary-strip" aria-label="Packet coverage">
        <span>{currentGateLabel}</span>
        <span>{totalFields} fields</span>
        <span>{supportedFields} supported</span>
        <span>{reviewFields} review</span>
        <span>{blockedFields} gaps</span>
      </div>
      <div className="live-packet-section-flow">
        {sections.map((section) => (
          <article className="live-packet-section" key={section.id}>
            <div className="live-packet-section-head">
              <div>
                <p>{section.label}</p>
                <strong>
                  {section.answered}/{section.total} supported
                </strong>
              </div>
              <span>{section.sourceCount} sources</span>
            </div>
            <div className="live-packet-route-kind-row">
              {section.routeKinds.map((routeKind) => (
                <span key={routeKind}>{formatLabel(routeKind)}</span>
              ))}
            </div>
            <div className="live-packet-field-stack">
              {section.fields.map((field) => (
                <div
                  className={`live-packet-field ${livePacketFieldToneClass(field)}`}
                  key={field.field_key}
                >
                  <div className="live-packet-field-main">
                    <span className="live-packet-state-dot" aria-hidden />
                    <div>
                      <strong>{field.label}</strong>
                      <span>
                        {formatLabel(field.current_status)} /{" "}
                        {formatLabel(field.evidence_status)}
                      </span>
                    </div>
                  </div>
                  <div className="live-packet-field-trace">
                    <span>
                      {field.source_refs.length > 0
                        ? `${field.source_refs.length} sources`
                        : "No sources"}
                    </span>
                    <span>{formatLabel(field.route_kind ?? "route")}</span>
                    <a
                      className="live-packet-route-link"
                      href={packetFieldRouteHref(field, selectedOpportunityId)}
                    >
                      {isRoadmapFieldAnswered(field) ? "Review" : "Start route"}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
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

function ActionPlanMode({
  latestActivationRun,
  selectedOpportunityId,
  updates,
}: {
  latestActivationRun: OpportunityActivationRun | null;
  selectedOpportunityId: string;
  updates: WorkProductUpdateProjection[];
}) {
  const matrix = latestActivationRun?.packet_field_action_matrix;
  const actionFields = matrix?.fields.filter(
    (field) =>
      field.action_state === "blocked" || field.action_state === "review_ready",
  );
  const currentGateActionFields =
    actionFields?.filter((field) => field.current_gate_required) ?? [];
  const visibleActionFields =
    currentGateActionFields.length > 0
      ? currentGateActionFields.slice(0, 4)
      : (actionFields ?? []).slice(0, 4);
  const sourceCount = new Set(updates.flatMap((update) => update.source_refs))
    .size;

  return (
    <section className="action-plan-mode" aria-labelledby="action-plan-title">
      <div className="action-plan-hero">
        <div>
          <p>Capture Action Plan</p>
          <h3 id="action-plan-title">Review route-born follow-up work.</h3>
          <span>
            Accepted route outputs land here as review-ready Action Plan
            updates. Packet gaps stay linked to the route that can produce the
            next action.
          </span>
        </div>
        <a
          className="packet-action-link"
          href={modeHref("capture", selectedOpportunityId, {
            route_goal: "build_capture_action_plan",
          })}
        >
          Sequence next actions
        </a>
      </div>

      <dl className="action-plan-metric-grid">
        <Metric
          label="Ready updates"
          value={updates.length.toString()}
          tone="cyan"
        />
        <Metric
          label="Open action fields"
          value={(actionFields?.length ?? 0).toString()}
          tone="rose"
        />
        <Metric
          label="Source refs"
          value={sourceCount.toString()}
          tone="copper"
        />
      </dl>

      <div className="action-plan-lanes">
        <section
          className="action-plan-lane"
          aria-labelledby="route-updates-title"
        >
          <div className="action-plan-lane-heading">
            <p>Review-ready updates</p>
            <h4 id="route-updates-title">Accepted route outputs</h4>
          </div>
          {updates.length > 0 ? (
            <div className="action-plan-card-stack">
              {updates.map((update) => (
                <article className="action-update-card" key={update.id}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(update.destination)}</span>
                    <span>{formatLabel(update.state)}</span>
                  </div>
                  <p>{update.after_summary}</p>
                  <dl>
                    <div>
                      <dt>Before</dt>
                      <dd>{update.before_summary}</dd>
                    </div>
                    <div>
                      <dt>Sources</dt>
                      <dd>
                        {update.source_refs.length > 0
                          ? update.source_refs
                              .map((sourceRef) =>
                                formatReferenceLabel(sourceRef),
                              )
                              .join(", ")
                          : "No source refs"}
                      </dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No Action Plan updates ready.</p>
              <span>
                Run and accept an action route to stage follow-up work.
              </span>
            </div>
          )}
        </section>

        <section
          className="action-plan-lane"
          aria-labelledby="action-gaps-title"
        >
          <div className="action-plan-lane-heading">
            <p>Next action inputs</p>
            <h4 id="action-gaps-title">Packet gaps that can become tasks</h4>
          </div>
          {visibleActionFields.length > 0 ? (
            <div className="action-plan-card-stack">
              {visibleActionFields.map((field) => (
                <article className="action-gap-card" key={field.field_key}>
                  <div>
                    <span>{formatLabel(field.section)}</span>
                    <h5>{field.label}</h5>
                    <p>{field.gap_summary ?? field.route_rationale}</p>
                  </div>
                  <a
                    className="packet-action-link"
                    href={packetFieldRouteHref(field, selectedOpportunityId)}
                  >
                    Start route
                  </a>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No blocking packet fields.</p>
              <span>Current packet state has no action-producing gaps.</span>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

function EngagementMode({
  latestActivationRun,
  selectedOpportunityId,
  updates,
}: {
  latestActivationRun: OpportunityActivationRun | null;
  selectedOpportunityId: string;
  updates: WorkProductUpdateProjection[];
}) {
  const matrix = latestActivationRun?.packet_field_action_matrix;
  const engagementFields = matrix?.fields.filter((field) => {
    const routeText = [
      field.field_key,
      field.label,
      field.question,
      field.section,
      field.route_kind,
      field.recommended_route,
      field.route_rationale,
      ...field.answer_paths,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return (
      isRoadmapFieldActionable(field) &&
      (routeText.includes("customer_call_plan") ||
        routeText.includes("call") ||
        routeText.includes("customer") ||
        routeText.includes("engagement") ||
        routeText.includes("capture lead"))
    );
  });
  const currentGateEngagementFields =
    engagementFields?.filter((field) => field.current_gate_required) ?? [];
  const visibleEngagementFields =
    currentGateEngagementFields.length > 0
      ? currentGateEngagementFields.slice(0, 4)
      : (engagementFields ?? []).slice(0, 4);
  const sourceCount = new Set(updates.flatMap((update) => update.source_refs))
    .size;

  return (
    <section className="action-plan-mode" aria-labelledby="engagement-title">
      <div className="action-plan-hero">
        <div>
          <p>Engagement Prep</p>
          <h3 id="engagement-title">Use call-plan route outputs.</h3>
          <span>
            Customer-call routes stay reviewable here until the operator turns
            them into meeting prep, follow-up work, or packet support.
          </span>
        </div>
        <a
          className="packet-action-link"
          href={modeHref("capture", selectedOpportunityId, {
            route_goal: "prepare_customer_call",
          })}
        >
          Prepare customer call
        </a>
      </div>

      <dl className="action-plan-metric-grid">
        <Metric
          label="Call-plan outputs"
          value={updates.length.toString()}
          tone="cyan"
        />
        <Metric
          label="Engagement fields"
          value={(engagementFields?.length ?? 0).toString()}
          tone="copper"
        />
        <Metric
          label="Source refs"
          value={sourceCount.toString()}
          tone="signal"
        />
      </dl>

      <div className="action-plan-lanes">
        <section className="action-plan-lane" aria-labelledby="call-plan-title">
          <div className="action-plan-lane-heading">
            <p>Review-ready prep</p>
            <h4 id="call-plan-title">Accepted call-plan outputs</h4>
          </div>
          {updates.length > 0 ? (
            <div className="action-plan-card-stack">
              {updates.map((update) => (
                <article className="action-update-card" key={update.id}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(update.destination)}</span>
                    <span>{formatLabel(update.state)}</span>
                  </div>
                  <p>{update.after_summary}</p>
                  <dl>
                    <div>
                      <dt>Before</dt>
                      <dd>{update.before_summary}</dd>
                    </div>
                    <div>
                      <dt>Sources</dt>
                      <dd>
                        {update.source_refs.length > 0
                          ? update.source_refs
                              .map((sourceRef) =>
                                formatReferenceLabel(sourceRef),
                              )
                              .join(", ")
                          : "No source refs"}
                      </dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No call-plan output ready.</p>
              <span>Run and accept a customer-call route to stage prep.</span>
            </div>
          )}
        </section>

        <section
          className="action-plan-lane"
          aria-labelledby="engagement-gaps-title"
        >
          <div className="action-plan-lane-heading">
            <p>Call inputs</p>
            <h4 id="engagement-gaps-title">
              Packet gaps needing customer input
            </h4>
          </div>
          {visibleEngagementFields.length > 0 ? (
            <div className="action-plan-card-stack">
              {visibleEngagementFields.map((field) => (
                <article className="action-gap-card" key={field.field_key}>
                  <div>
                    <span>{formatLabel(field.section)}</span>
                    <h5>{field.label}</h5>
                    <p>{field.gap_summary ?? field.route_rationale}</p>
                  </div>
                  <a
                    className="packet-action-link"
                    href={packetFieldRouteHref(field, selectedOpportunityId)}
                  >
                    Start route
                  </a>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No engagement-specific gaps.</p>
              <span>
                Current packet routes do not require customer follow-up.
              </span>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

function ResearchMode({
  latestActivationRun,
  runs,
  selectedOpportunityId,
  sourceRegistry,
}: {
  latestActivationRun: OpportunityActivationRun | null;
  runs: CaptureResearchRun[];
  selectedOpportunityId: string;
  sourceRegistry: CaptureResearchSourceRegistry | null;
}) {
  const matrix = latestActivationRun?.packet_field_action_matrix;
  const researchFields = matrix?.fields.filter((field) => {
    const routeText = [
      field.field_key,
      field.label,
      field.question,
      field.section,
      field.route_kind,
      field.recommended_route,
      field.route_rationale,
      ...field.answer_paths,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return (
      isRoadmapFieldActionable(field) &&
      (routeText.includes("research_or_mcp") ||
        routeText.includes("research") ||
        routeText.includes("mcp") ||
        routeText.includes("capability") ||
        routeText.includes("skill"))
    );
  });
  const visibleResearchFields = [...(researchFields ?? [])]
    .sort(compareRoadmapFields)
    .slice(0, 4);
  const findingCount = runs.reduce(
    (total, run) => total + run.source_findings.length,
    0,
  );
  const candidateCount = runs.reduce(
    (total, run) => total + run.downstream_candidates.length,
    0,
  );
  const recommendedProviderIds = sourceRegistry?.recommended_provider_ids ?? [];
  const recommendedProviders =
    recommendedProviderIds.length > 0
      ? recommendedProviderIds.map((providerId) => formatLabel(providerId)).join(", ")
      : "None ready";

  return (
    <section
      className="action-plan-mode research-mode"
      aria-labelledby="research-title"
    >
      <div className="action-plan-hero">
        <div>
          <p>Research Desk</p>
          <h3 id="research-title">Trace source collection into review work.</h3>
          <span>
            Research stays scoped to this Opportunity, keeps source limits
            visible, and routes candidates through review before trusted writes.
          </span>
        </div>
        <a
          className="packet-action-link"
          href={modeHref("capture", selectedOpportunityId, {
            route_goal: "close_packet_gap",
          })}
        >
          Start research route
        </a>
      </div>

      <dl className="action-plan-metric-grid">
        <Metric
          label="Research runs"
          value={runs.length.toString()}
          tone="cyan"
        />
        <Metric
          label="Source findings"
          value={findingCount.toString()}
          tone="signal"
        />
        <Metric
          label="Review candidates"
          value={candidateCount.toString()}
          tone="copper"
        />
      </dl>

      <div className="action-plan-lanes">
        <section className="action-plan-lane" aria-labelledby="research-runs-title">
          <div className="action-plan-lane-heading">
            <p>Opportunity research</p>
            <h4 id="research-runs-title">Capture research runs</h4>
          </div>
          {runs.length > 0 ? (
            <div className="action-plan-card-stack">
              {runs.slice(0, 4).map((run) => (
                <article className="action-update-card" key={run.research_run_id}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(run.status)}</span>
                    <span>{run.source_findings.length} findings</span>
                  </div>
                  <p>
                    {run.user_prompt?.prompt ??
                      run.research_brief.research_question}
                  </p>
                  <dl>
                    <div>
                      <dt>Lenses</dt>
                      <dd>
                        {run.research_brief.selected_lenses
                          .map(formatLabel)
                          .join(", ")}
                      </dd>
                    </div>
                    <div>
                      <dt>Targets</dt>
                      <dd>{joinOrNone(run.research_brief.source_targets)}</dd>
                    </div>
                    <div>
                      <dt>Candidates</dt>
                      <dd>{run.downstream_candidates.length.toString()}</dd>
                    </div>
                    <div>
                      <dt>Source limits</dt>
                      <dd>{joinOrNone(run.research_brief.source_limits)}</dd>
                    </div>
                  </dl>
                  {run.research_summary_view ? (
                    <span className="action-update-note">
                      {run.research_summary_view}
                    </span>
                  ) : null}
                  {run.downstream_candidates.length > 0 ? (
                    <div className="research-candidate-list">
                      {run.downstream_candidates.slice(0, 3).map((candidate) => (
                        <span key={candidate.id}>
                          {candidate.title ?? candidate.id} -{" "}
                          {formatLabel(
                            candidate.review_state ?? "pending_review",
                          )}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No research runs for this Opportunity.</p>
              <span>
                Research-backed packet gaps can start from Assisted Capture.
              </span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="source-readiness-title">
          <div className="action-plan-lane-heading">
            <p>Source readiness</p>
            <h4 id="source-readiness-title">Collection providers</h4>
          </div>
          {sourceRegistry ? (
            <div className="action-plan-card-stack">
              <article className="action-update-card">
                <div className="action-update-card-head">
                  <span>{formatLabel(sourceRegistry.quality_status)}</span>
                  <span>{recommendedProviders}</span>
                </div>
                <p>{sourceRegistry.quality_summary}</p>
              </article>
              {sourceRegistry.providers.slice(0, 5).map((provider) => (
                <article className="action-gap-card" key={provider.provider_id}>
                  <div>
                    <span>{formatLabel(provider.status)}</span>
                    <h5>{provider.provider_name}</h5>
                    <p>{provider.diagnostic_summary}</p>
                    <small>
                      {formatLabel(provider.role)} -{" "}
                      {formatLabel(provider.source_mode)}
                    </small>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>Source readiness unavailable.</p>
              <span>Research provider registry did not respond.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="research-gaps-title">
          <div className="action-plan-lane-heading">
            <p>Research inputs</p>
            <h4 id="research-gaps-title">Packet gaps needing research</h4>
          </div>
          {visibleResearchFields.length > 0 ? (
            <div className="action-plan-card-stack">
              {visibleResearchFields.map((field) => (
                <article className="action-gap-card" key={field.field_key}>
                  <div>
                    <span>{formatLabel(field.route_kind ?? field.section)}</span>
                    <h5>{field.label}</h5>
                    <p>{field.gap_summary ?? field.route_rationale}</p>
                  </div>
                  <a
                    className="packet-action-link"
                    href={packetFieldRouteHref(field, selectedOpportunityId)}
                  >
                    Start route
                  </a>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No research-routed packet gaps.</p>
              <span>Current packet routes do not require research support.</span>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

function DocumentsMode({
  capabilities,
  candidates,
  drafts,
  latestActivationRun,
  records,
  selectedOpportunityId,
}: {
  capabilities: DocumentIntakeCapabilitiesResponse | null;
  candidates: DocumentIntakeCaptureCandidate[];
  drafts: DocumentIntakeDraft[];
  latestActivationRun: OpportunityActivationRun | null;
  records: DocumentIntakeRecord[];
  selectedOpportunityId: string;
}) {
  const draftParts = drafts.flatMap((draft) =>
    draft.intelligence_pieces.map((piece) => ({ draft, piece })),
  );
  const parserRequiredCount = records.filter(
    (record) => record.status === "parser_required",
  ).length;
  const pendingReviewCount = records.filter((record) =>
    ["pending_review", "in_review"].includes(
      record.extraction_review_status ?? "",
    ),
  ).length;
  const matrix = latestActivationRun?.packet_field_action_matrix;
  const sourceBackedFields = matrix?.fields.filter((field) => {
    const routeText = [
      field.field_key,
      field.label,
      field.question,
      field.section,
      field.route_kind,
      field.recommended_route,
      field.route_rationale,
      ...field.answer_paths,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return (
      isRoadmapFieldActionable(field) &&
      (routeText.includes("source_backed_answer") ||
        routeText.includes("source material") ||
        routeText.includes("extract") ||
        routeText.includes("document"))
    );
  });
  const visibleSourceBackedFields = [...(sourceBackedFields ?? [])]
    .sort(compareRoadmapFields)
    .slice(0, 4);

  return (
    <section className="action-plan-mode" aria-labelledby="documents-title">
      <div className="action-plan-hero">
        <div>
          <p>Document Intake</p>
          <h3 id="documents-title">Turn source material into review work.</h3>
          <span>
            Intake records, extraction drafts, parser gaps, and document-derived
            candidates stay visible before any source span becomes trusted evidence.
          </span>
        </div>
        <a
          className="packet-action-link"
          href={modeHref("capture", selectedOpportunityId, {
            route_goal: "close_packet_gap",
          })}
        >
          Route document gap
        </a>
      </div>

      <dl className="action-plan-metric-grid">
        <Metric
          label="Intake records"
          value={records.length.toString()}
          tone="cyan"
        />
        <Metric
          label="Review queue"
          value={`${pendingReviewCount}/${draftParts.length}`}
          tone="copper"
        />
        <Metric
          label="Parser gaps"
          value={parserRequiredCount.toString()}
          tone="rose"
        />
        <Metric
          label="Deferred adapters"
          value={(capabilities?.deferred_count ?? 0).toString()}
          tone="signal"
        />
      </dl>

      <div className="action-plan-lanes">
        <section className="action-plan-lane" aria-labelledby="document-queue-title">
          <div className="action-plan-lane-heading">
            <p>Source queue</p>
            <h4 id="document-queue-title">Intake records</h4>
          </div>
          {records.length > 0 ? (
            <div className="action-plan-card-stack">
              {records.slice(0, 5).map((record) => (
                <article className="action-update-card" key={record.id}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(record.queue_state ?? record.status)}</span>
                    <span>{formatLabel(record.material_type ?? "source")}</span>
                  </div>
                  <p>{record.filename ?? record.source_ref}</p>
                  <dl>
                    <div>
                      <dt>Extraction</dt>
                      <dd>
                        {formatLabel(record.extraction_status ?? "not_started")} / {formatLabel(record.extraction_review_status ?? "not_ready")}
                      </dd>
                    </div>
                    <div>
                      <dt>Opportunity</dt>
                      <dd>{record.opportunity_id ?? "Unassigned"}</dd>
                    </div>
                    <div>
                      <dt>Warnings</dt>
                      <dd>{record.extraction_warning_count.toString()}</dd>
                    </div>
                    <div>
                      <dt>Source</dt>
                      <dd>{record.source_ref}</dd>
                    </div>
                  </dl>
                  <span className="action-update-note">
                    {record.capability_hint}
                  </span>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No intake records.</p>
              <span>Upload or register source material to start Document Intake.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="document-drafts-title">
          <div className="action-plan-lane-heading">
            <p>Extraction review</p>
            <h4 id="document-drafts-title">Document-derived draft parts</h4>
          </div>
          {draftParts.length > 0 ? (
            <div className="action-plan-card-stack">
              {draftParts.slice(0, 5).map(({ draft, piece }) => (
                <article className="action-update-card" key={piece.id}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(piece.part_type)}</span>
                    <span>{formatLabel(draft.status)}</span>
                  </div>
                  <p>{piece.content}</p>
                  <dl>
                    <div>
                      <dt>Route</dt>
                      <dd>{formatLabel(piece.recommended_route)}</dd>
                    </div>
                    <div>
                      <dt>Skill chain</dt>
                      <dd>{joinOrNone(piece.suggested_skill_chain)}</dd>
                    </div>
                    <div>
                      <dt>Source spans</dt>
                      <dd>{joinOrNone(piece.source_span_ids)}</dd>
                    </div>
                    <div>
                      <dt>Bundle</dt>
                      <dd>{piece.source_extraction_bundle_id ?? draft.extraction_bundle_id ?? "None"}</dd>
                    </div>
                  </dl>
                  {piece.recommendation ? (
                    <span className="action-update-note">
                      {piece.recommendation}
                    </span>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No extraction drafts.</p>
              <span>Readable text or Markdown intake creates reviewable draft parts.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="document-candidates-title">
          <div className="action-plan-lane-heading">
            <p>Review-gated outputs</p>
            <h4 id="document-candidates-title">Capture candidates</h4>
          </div>
          {candidates.length > 0 ? (
            <div className="action-plan-card-stack">
              {candidates.slice(0, 5).map((candidate) => (
                <article className="action-update-card" key={candidate.id}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(candidate.target_workflow)}</span>
                    <span>{formatLabel(candidate.review_state)}</span>
                  </div>
                  <p>{candidate.title}</p>
                  <span className="action-update-note">{candidate.content}</span>
                  <dl>
                    <div>
                      <dt>Skill chain</dt>
                      <dd>{joinOrNone(candidate.suggested_skill_chain)}</dd>
                    </div>
                    <div>
                      <dt>Trace</dt>
                      <dd>{candidate.source_extraction_bundle_id}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No capture candidates.</p>
              <span>Draft parts can queue Action Plan, Packet, Risk, or Call Plan candidates after review prep.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="document-capabilities-title">
          <div className="action-plan-lane-heading">
            <p>Parser boundary</p>
            <h4 id="document-capabilities-title">Intake capabilities</h4>
          </div>
          {capabilities ? (
            <div className="action-plan-card-stack">
              <article className="action-update-card">
                <div className="action-update-card-head">
                  <span>{capabilities.available_count} available</span>
                  <span>{capabilities.deferred_count} deferred</span>
                </div>
                <p>{capabilities.extraction_bundle_boundary}</p>
              </article>
              {capabilities.capabilities.slice(0, 5).map((capability) => (
                <article className="action-gap-card" key={capability.id}>
                  <div>
                    <span>{formatLabel(capability.status)}</span>
                    <h5>{capability.name}</h5>
                    <p>{capability.capability_hint}</p>
                    <small>
                      {formatLabel(capability.adapter_kind)} - {joinOrNone(capability.supported_material_types)}
                    </small>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>Capability report unavailable.</p>
              <span>Document Intake capability endpoint did not respond.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="document-gaps-title">
          <div className="action-plan-lane-heading">
            <p>Packet inputs</p>
            <h4 id="document-gaps-title">Source-backed packet gaps</h4>
          </div>
          {visibleSourceBackedFields.length > 0 ? (
            <div className="action-plan-card-stack">
              {visibleSourceBackedFields.map((field) => (
                <article className="action-gap-card" key={field.field_key}>
                  <div>
                    <span>{formatLabel(field.route_kind ?? field.section)}</span>
                    <h5>{field.label}</h5>
                    <p>{field.gap_summary ?? field.route_rationale}</p>
                  </div>
                  <a
                    className="packet-action-link"
                    href={packetFieldRouteHref(field, selectedOpportunityId)}
                  >
                    Start route
                  </a>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No source-backed packet gaps.</p>
              <span>Current packet routes do not require document/source extraction.</span>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

function CapabilityStudioMode({
  catalog,
  runs,
  selectedOpportunityId,
}: {
  catalog: CapabilityCatalog | null;
  runs: CapabilityRun[];
  selectedOpportunityId: string;
}) {
  const outputs = runs.flatMap((run) =>
    run.outputs.map((output) => ({ output, run })),
  );
  const pendingOutputs = outputs.filter(
    ({ output }) => output.review_state === "pending",
  );
  const validationGapOutputs = outputs.filter(
    ({ output }) => output.gaps.length > 0,
  );
  const unvalidatedCatalogEntries = catalog?.entries.filter(
    (entry) => entry.validation_status === "unvalidated",
  );
  const latestRun = runs[0];

  return (
    <section className="action-plan-mode" aria-labelledby="capability-studio-title">
      <div className="action-plan-hero">
        <div>
          <p>Capability Studio</p>
          <h3 id="capability-studio-title">Inspect runs before automation grows.</h3>
          <span>
            Capability runs stay behind product workflows: outputs, gaps,
            provenance, and autonomy recommendations remain review-gated.
          </span>
        </div>
        <a
          className="packet-action-link"
          href={modeHref("capture", selectedOpportunityId, {
            route_goal: "close_packet_gap",
          })}
        >
          Route capability need
        </a>
      </div>

      <dl className="action-plan-metric-grid">
        <Metric label="Runs" value={runs.length.toString()} tone="cyan" />
        <Metric
          label="Pending outputs"
          value={pendingOutputs.length.toString()}
          tone="copper"
        />
        <Metric
          label="Catalog entries"
          value={(catalog?.entries.length ?? 0).toString()}
          tone="signal"
        />
        <Metric
          label="Validation gaps"
          value={validationGapOutputs.length.toString()}
          tone="rose"
        />
      </dl>

      <div className="action-plan-lanes">
        <section className="action-plan-lane" aria-labelledby="capability-runs-title">
          <div className="action-plan-lane-heading">
            <p>Run history</p>
            <h4 id="capability-runs-title">Capability runs</h4>
          </div>
          {runs.length > 0 ? (
            <div className="action-plan-card-stack">
              {runs.slice(0, 5).map((run) => (
                <article className="action-update-card" key={run.run_id}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(run.status)}</span>
                    <span>{run.outputs.length} outputs</span>
                  </div>
                  <p>{run.capability_id}</p>
                  <dl>
                    <div>
                      <dt>Executor</dt>
                      <dd>{formatLabel(run.executor_kind)}</dd>
                    </div>
                    <div>
                      <dt>Context</dt>
                      <dd>{formatLabel(run.session_context)}</dd>
                    </div>
                    <div>
                      <dt>Workflow</dt>
                      <dd>{formatLabel(run.product_workflow)}</dd>
                    </div>
                    <div>
                      <dt>Input refs</dt>
                      <dd>{joinOrNone(run.input_refs)}</dd>
                    </div>
                  </dl>
                  <span className="action-update-note">
                    {run.inputs_summary}
                  </span>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No capability runs.</p>
              <span>Run history appears after a capability validation or workflow execution.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="capability-output-title">
          <div className="action-plan-lane-heading">
            <p>Review queue</p>
            <h4 id="capability-output-title">Run outputs</h4>
          </div>
          {pendingOutputs.length > 0 ? (
            <div className="action-plan-card-stack">
              {pendingOutputs.slice(0, 6).map(({ output, run }) => (
                <article className="action-update-card" key={`${run.run_id}:${output.output_id}`}>
                  <div className="action-update-card-head">
                    <span>{formatLabel(output.review_state)}</span>
                    <span>{formatLabel(output.autonomy_recommendation)}</span>
                  </div>
                  <p>{output.title}</p>
                  <span className="action-update-note">{output.summary}</span>
                  <dl>
                    <div>
                      <dt>Destination</dt>
                      <dd>{output.recommended_destination ?? "Review queue"}</dd>
                    </div>
                    <div>
                      <dt>Capability</dt>
                      <dd>{run.capability_id}</dd>
                    </div>
                    <div>
                      <dt>Gaps</dt>
                      <dd>{joinOrNone(output.gaps)}</dd>
                    </div>
                    <div>
                      <dt>Source</dt>
                      <dd>{capabilityProvenanceValue(output.provenance, "source_path")}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No pending outputs.</p>
              <span>Capability outputs are clear or already reviewed.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="capability-catalog-title">
          <div className="action-plan-lane-heading">
            <p>Local inventory</p>
            <h4 id="capability-catalog-title">Capability catalog</h4>
          </div>
          {catalog ? (
            <div className="action-plan-card-stack">
              <article className="action-update-card">
                <div className="action-update-card-head">
                  <span>{catalog.entries.length} entries</span>
                  <span>{catalog.read_only ? "Read only" : "Writable"}</span>
                </div>
                <p>{joinOrNone(catalog.canonical_locations)}</p>
                <span className="action-update-note">
                  Indexed from canonical workspace skill locations.
                </span>
              </article>
              {(unvalidatedCatalogEntries ?? catalog.entries).slice(0, 5).map((entry) => (
                <article className="action-gap-card" key={entry.id}>
                  <div>
                    <span>{formatLabel(entry.validation_status)}</span>
                    <h5>{entry.name}</h5>
                    <p>{entry.description || entry.provenance_note}</p>
                    <small>
                      {formatLabel(entry.capability_type)} - {formatLabel(entry.maturity)} - {entry.source_path}
                    </small>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>Capability catalog unavailable.</p>
              <span>Local capability inventory endpoint did not respond.</span>
            </div>
          )}
        </section>

        <section className="action-plan-lane" aria-labelledby="capability-provenance-title">
          <div className="action-plan-lane-heading">
            <p>Reasoning view</p>
            <h4 id="capability-provenance-title">Latest provenance</h4>
          </div>
          {latestRun ? (
            <div className="action-plan-card-stack">
              <article className="action-update-card">
                <div className="action-update-card-head">
                  <span>{formatLabel(latestRun.executor_kind)}</span>
                  <span>{formatLabel(latestRun.capability_type)}</span>
                </div>
                <p>{latestRun.inputs_summary}</p>
                <dl>
                  <div>
                    <dt>Sources</dt>
                    <dd>{capabilityProvenanceValue(latestRun.provenance, "sources")}</dd>
                  </div>
                  <div>
                    <dt>Tools</dt>
                    <dd>{capabilityProvenanceValue(latestRun.provenance, "tool_names")}</dd>
                  </div>
                  <div>
                    <dt>Network</dt>
                    <dd>{capabilityProvenanceValue(latestRun.provenance, "network_required")}</dd>
                  </div>
                  <div>
                    <dt>Model</dt>
                    <dd>{capabilityProvenanceValue(latestRun.provenance, "model_required")}</dd>
                  </div>
                </dl>
                <span className="action-update-note">
                  Capability outputs still require review before trusted use.
                </span>
              </article>
            </div>
          ) : (
            <div className="action-plan-empty">
              <p>No provenance yet.</p>
              <span>Capability Reasoning View appears after a run exists.</span>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

function capabilityProvenanceValue(
  provenance: Record<string, unknown>,
  key: string,
): string {
  const value = provenance[key];
  if (Array.isArray(value)) {
    return joinOrNone(value.map(String));
  }
  if (value === undefined || value === null || value === "") {
    return "None";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
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

  return (
    labels[value] ?? formatLabel(value.replace(/^ev_/, "").replace(/\./g, "_"))
  );
}

function joinOrNone(values: string[]): string {
  return values.length > 0 ? values.map(formatLabel).join(", ") : "None";
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
    "capability_studio",
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
  return modeId === "__placeholder__";
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
  const urgencyScore: Record<string, number> = {
    needs_action: 8,
    review_ready: 6,
    source_limited: 4,
    watch: 2,
    steady: 0,
  };
  if (opportunity.next_action_urgency === "steady") {
    return opportunity.portfolio_status === "active" ? 1 : 0;
  }
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
    (urgencyScore[opportunity.next_action_urgency] ?? 0) +
    opportunity.blocked_field_count * 5 +
    opportunity.review_ready_count * 3 +
    opportunity.source_limitation_count * 2 +
    readinessScore +
    statusScore
  );
}

function opportunityPulseReason(opportunity: PortfolioOpportunity): string {
  if (["archived", "won", "lost"].includes(opportunity.portfolio_status)) {
    return `${formatLabel(opportunity.portfolio_status)} Opportunity. Open roadmap for trace and lessons.`;
  }
  if (opportunity.attention_reason) {
    return opportunity.attention_reason;
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
  if (opportunity.next_action_urgency === "needs_action") {
    return "critical";
  }
  if (opportunity.next_action_urgency === "review_ready") {
    return "review";
  }
  if (
    opportunity.next_action_urgency === "source_limited" ||
    opportunity.next_action_urgency === "watch"
  ) {
    return "watch";
  }
  if (opportunity.next_action_urgency === "steady") {
    return "steady";
  }
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
  if (opportunity.next_action_urgency) {
    return formatLabel(opportunity.next_action_urgency);
  }
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

function buildLivePacketSections(
  fields: PacketRoadmapField[],
): LivePacketSection[] {
  const sections = new Map<string, LivePacketSection>();
  fields.forEach((field) => {
    const section = sections.get(field.section) ?? {
      id: field.section,
      label: formatLabel(field.section),
      total: 0,
      answered: 0,
      reviewReady: 0,
      blocked: 0,
      fields: [],
      routeKinds: [],
      sourceCount: 0,
    };
    section.total += 1;
    section.sourceCount += field.source_refs.length;
    section.fields.push(field);
    const routeKind = field.route_kind ?? "route";
    if (!section.routeKinds.includes(routeKind)) {
      section.routeKinds.push(routeKind);
    }
    if (isRoadmapFieldAnswered(field)) {
      section.answered += 1;
    } else if (field.action_state === "review_ready") {
      section.reviewReady += 1;
    } else {
      section.blocked += 1;
    }
    sections.set(field.section, section);
  });
  return [...sections.values()].map((section) => ({
    ...section,
    fields: [...section.fields].sort(compareRoadmapFields),
    routeKinds: [...section.routeKinds].sort(),
  }));
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

function livePacketFieldToneClass(field: PacketRoadmapField): string {
  if (isRoadmapFieldAnswered(field)) {
    return "live-packet-field-supported";
  }
  if (field.requires_review) {
    return "live-packet-field-review";
  }
  return "live-packet-field-gap";
}

function packetFieldRouteHref(
  field: PacketRoadmapField,
  selectedOpportunityId: string,
): string {
  return modeHref("capture", selectedOpportunityId, {
    packet_field_key: field.field_key,
    route_goal: "close_packet_gap",
  });
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
