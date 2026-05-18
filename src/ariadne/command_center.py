from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html import escape
from pathlib import Path

from ariadne.action_plans import CaptureActionPlan
from ariadne.capabilities import CapabilityCatalog
from ariadne.capability_runs import (
    CapabilityReasoningView,
    CapabilityRun,
    CapabilityRunOutputReviewState,
    CapabilityRunStore,
    build_capability_reasoning_view,
)
from ariadne.capture_research import CaptureResearchRun, CaptureResearchStore
from ariadne.config import RuntimeSettings
from ariadne.document_intake import (
    AcceptedDocumentEvidenceLink,
    DocumentIntakeAdapterDeclaration,
    DocumentIntakeCaptureCandidate,
    DocumentIntakeRecord,
    DocumentIntakeStore,
    ExtractionBundleReviewStatus,
    KnowledgeNoteProjection,
    create_capture_intelligence_draft_from_extraction_bundle,
    list_document_intake_adapter_declarations,
)
from ariadne.evidence import EvidenceItem
from ariadne.federal_data import (
    FederalDataCapabilityManifest,
    list_federal_data_capability_manifests,
)
from ariadne.next_action_recommendations import (
    NextActionRecommendation,
    NextActionRecommendationReviewState,
    NextActionRecommendationStore,
)
from ariadne.packet_knowledge import (
    PacketFieldAnswerStatus,
    create_packet_field_answer,
)
from ariadne.packets import (
    CanonicalPacketSection,
    EvidenceStatus,
)
from ariadne.piid_profiles import (
    PiidContractIntelligenceProfile,
    PiidEnrichmentRoute,
    PiidProfileStore,
    PiidReviewCandidate,
)
from ariadne.quick_capture import CaptureIntelligenceDraft
from ariadne.quick_capture_demo import (
    DocumentIntakeDemoThread,
    InMemoryDemoEvidenceStore,
    QuickCaptureDemoThread,
    build_quick_capture_demo_thread,
)
from ariadne.reference_wiki import ReferenceWikiInfluence
from ariadne.sam_gov_profiles import (
    SamGovEnrichmentProfile,
    SamGovProfileStore,
    SamGovReviewCandidate,
    build_sam_gov_command_surface_summary,
)
from ariadne.structured_knowledge import (
    KnowledgeContextItem,
    KnowledgeContextSection,
    KnowledgeGapSummary,
    KnowledgeSourceLimitation,
    OpportunityKnowledgeContextView,
    get_opportunity_knowledge_context,
)


@dataclass(frozen=True)
class CommandCenterKnowledgeContext:
    opportunity_id: str
    context: OpportunityKnowledgeContextView
    recommendations: tuple[NextActionRecommendation, ...]
    action_plan: CaptureActionPlan


def render_command_center_shell(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> str:
    root = workspace_root or Path.cwd()
    demo = build_quick_capture_demo_thread(settings, workspace_root=root)
    opportunity = demo.opportunity
    packet = demo.packet
    quick_capture = demo.quick_capture
    capture_review = demo.capture_review
    pasted_capture = demo.pasted_capture
    pasted_review = demo.pasted_review
    uploaded_capture = demo.uploaded_capture
    uploaded_review = demo.uploaded_review
    unsupported_upload = demo.unsupported_upload
    document_intake_demo = demo.document_intake
    document_intake_store = DocumentIntakeStore(
        _resolve_runtime_path(root, settings.ariadne_document_intake_dir)
    )
    document_intake_records = [
        document_intake_demo.record
    ] + document_intake_store.list()
    accepted_document_evidence_links = [
        document_intake_demo.accepted_evidence.accepted_link
    ] + document_intake_store.list_accepted_evidence_links()
    document_intake_drafts = [document_intake_demo.draft] + [
        create_capture_intelligence_draft_from_extraction_bundle(bundle)
        for bundle in document_intake_store.list_extraction_bundles()
    ]
    document_intake_capture_candidates = list(document_intake_demo.candidates) + (
        document_intake_store.list_capture_candidates()
    )
    document_intake_knowledge_note_projections = [
        document_intake_demo.projection
    ] + document_intake_store.list_knowledge_note_projections()
    document_intake_adapter_declarations = list_document_intake_adapter_declarations()
    federal_data_registry = list_federal_data_capability_manifests()
    piid_profile_store = PiidProfileStore(
        _resolve_runtime_path(root, settings.ariadne_piid_profiles_dir)
    )
    piid_profiles = piid_profile_store.list()
    sam_gov_profile_store = SamGovProfileStore(
        _resolve_runtime_path(root, settings.ariadne_sam_gov_profiles_dir)
    )
    sam_gov_profiles = sam_gov_profile_store.list()
    capability_run_store = CapabilityRunStore(
        _resolve_runtime_path(root, settings.ariadne_capability_runs_dir)
    )
    capability_runs = tuple(capability_run_store.list())
    capture_research_store = CaptureResearchStore(
        _resolve_runtime_path(root, settings.ariadne_capture_research_dir)
    )
    capture_research_runs = tuple(capture_research_store.list())
    sam_gov_live_ready = "SAM_GOV_API_KEY" in settings.federal_data_env
    accepted_evidence = demo.accepted_evidence
    accepted_action = demo.accepted_action
    accepted_packet_answer = demo.accepted_packet_answer
    discarded_output = demo.discarded_output
    action_view = demo.action_view
    reference_influences = demo.reference_influences
    coverage_view = demo.coverage_view
    catalog = demo.catalog
    knowledge_context = build_command_center_knowledge_context(
        settings,
        workspace_root=root,
        demo=demo,
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(settings.public_app_name)} Command Center</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #020617;
      --surface: #0f172a;
      --surface-strong: #111c31;
      --surface-soft: #16243a;
      --edge: #334155;
      --edge-soft: #243244;
      --text: #f8fafc;
      --muted: #b6c4d6;
      --quiet: #8292a8;
      --cyan: #22d3ee;
      --green: #22c55e;
      --magenta: #e879f9;
      --amber: #fbbf24;
      --red: #fb7185;
      --focus: #fbbf24;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      min-height: 100dvh;
      overflow-x: hidden;
      font-family: Arial, Helvetica, sans-serif;
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.06) 1px, transparent 1px) 0 0 / 48px 48px,
        linear-gradient(0deg, rgba(34, 211, 238, 0.035) 1px, transparent 1px) 0 0 / 48px 48px,
        var(--bg);
      color: var(--text);
    }}
    a {{ color: inherit; }}
    a:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
    .skip-link {{
      position: absolute;
      top: -80px;
      left: 16px;
      z-index: 20;
      min-height: 44px;
      padding: 12px 16px;
      border-radius: 8px;
      background: var(--focus);
      color: #071018;
      font-weight: 800;
    }}
    .skip-link:focus {{ top: 16px; }}
    .shell {{
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: 100dvh;
    }}
    .sidebar {{
      position: sticky;
      top: 0;
      height: 100dvh;
      padding: 20px;
      border-right: 1px solid var(--edge);
      background: rgba(15, 23, 42, 0.94);
    }}
    .brand {{ padding-bottom: 18px; border-bottom: 1px solid var(--edge-soft); }}
    .eyebrow {{
      margin: 0 0 8px;
      color: var(--cyan);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{ margin: 0; font-size: 1.55rem; line-height: 1.12; letter-spacing: 0; }}
    h2 {{ margin: 0; font-size: 1.05rem; line-height: 1.25; letter-spacing: 0; }}
    h3 {{ margin: 0; font-size: 0.95rem; line-height: 1.3; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
    .nav {{ display: grid; gap: 8px; margin-top: 18px; }}
    .nav a {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 44px;
      padding: 10px 12px;
      border: 1px solid var(--edge-soft);
      border-radius: 8px;
      background: var(--surface);
      color: var(--text);
      text-decoration: none;
      font-weight: 800;
      transition: border-color 180ms ease, background-color 180ms ease, color 180ms ease;
    }}
    .nav a:hover {{ border-color: var(--cyan); color: var(--cyan); }}
    .nav small {{ color: var(--quiet); font-weight: 700; }}
    .advanced {{ margin-top: 18px; padding-top: 18px; border-top: 1px solid var(--edge-soft); }}
    .advanced-label {{ color: var(--quiet); font-size: 0.8rem; font-weight: 800; text-transform: uppercase; }}
    .main {{ width: min(100% - 32px, 1480px); margin: 0 auto; padding: 24px 0 48px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    .runtime-pill {{
      display: inline-flex;
      align-items: center;
      min-height: 44px;
      padding: 10px 14px;
      border: 1px solid rgba(34, 197, 94, 0.55);
      border-radius: 8px;
      background: rgba(34, 197, 94, 0.1);
      color: var(--green);
      font-weight: 900;
      white-space: nowrap;
    }}
    .hero {{
      margin-top: 18px;
      padding: 18px;
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.9);
    }}
    .hero h2 {{ font-size: 2.1rem; line-height: 1.08; }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }}
    .metric {{
      min-height: 94px;
      padding: 14px;
      border: 1px solid var(--edge-soft);
      border-radius: 8px;
      background: var(--surface-strong);
    }}
    .metric span {{ display: block; color: var(--quiet); font-size: 0.78rem; font-weight: 800; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 8px; font-size: 1.15rem; color: var(--text); }}
    .metric .green {{ color: var(--green); }}
    .metric .cyan {{ color: var(--cyan); }}
    .metric .amber {{ color: var(--amber); }}
    .surface-grid {{ display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 14px; margin-top: 14px; }}
    .panel {{
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.9);
      padding: 16px;
    }}
    .panel-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }}
    .status-chip {{
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 5px 8px;
      border: 1px solid var(--edge);
      border-radius: 8px;
      color: var(--muted);
      background: #0b1220;
      font-size: 0.78rem;
      font-weight: 800;
      white-space: nowrap;
    }}
    .status-chip.green {{ border-color: rgba(34, 197, 94, 0.55); color: var(--green); background: rgba(34, 197, 94, 0.1); }}
    .status-chip.cyan {{ border-color: rgba(34, 211, 238, 0.55); color: var(--cyan); background: rgba(34, 211, 238, 0.1); }}
    .status-chip.amber {{ border-color: rgba(251, 191, 36, 0.55); color: var(--amber); background: rgba(251, 191, 36, 0.1); }}
    .row-list {{ display: grid; gap: 8px; }}
    .compact-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }}
    .row {{
      display: grid;
      gap: 6px;
      padding: 12px;
      border: 1px solid var(--edge-soft);
      border-radius: 8px;
      background: var(--surface-strong);
    }}
    .row strong {{ color: var(--text); }}
    .row span {{ color: var(--muted); line-height: 1.45; overflow-wrap: anywhere; }}
    .row .meta-line {{ display: block; margin-top: 2px; color: var(--quiet); font-family: Consolas, "Courier New", monospace; overflow-wrap: anywhere; word-break: break-word; }}
    .link-row {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      margin-top: 12px;
      padding: 10px 14px;
      border: 1px solid var(--cyan);
      border-radius: 8px;
      color: var(--cyan);
      text-decoration: none;
      font-weight: 900;
    }}
    .action-strip {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }}
    .action-button {{
      min-height: 44px;
      padding: 10px 12px;
      border: 1px solid rgba(34, 211, 238, 0.7);
      border-radius: 8px;
      background: rgba(34, 211, 238, 0.12);
      color: var(--cyan);
      font: inherit;
      font-weight: 900;
      cursor: pointer;
    }}
    .action-button.secondary {{ border-color: rgba(251, 191, 36, 0.7); background: rgba(251, 191, 36, 0.12); color: var(--amber); }}
    .action-button.danger {{ border-color: rgba(251, 113, 133, 0.7); background: rgba(251, 113, 133, 0.12); color: var(--red); }}
    .action-button:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
    .action-button[disabled] {{ cursor: not-allowed; opacity: 0.72; }}
    details.detail-block {{ margin-top: 10px; border: 1px solid var(--edge-soft); border-radius: 8px; background: var(--surface-strong); }}
    details.detail-block > summary {{ min-height: 44px; padding: 12px; cursor: pointer; color: var(--cyan); font-weight: 900; }}
    .detail-body {{ display: grid; gap: 8px; padding: 0 12px 12px; }}
    .inline-form {{ margin: 0; }}
    .upload-form {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(180px, 0.7fr) auto;
      gap: 8px;
      align-items: center;
      padding: 12px;
      border: 1px solid var(--edge-soft);
      border-radius: 8px;
      background: var(--surface-strong);
    }}
    .upload-form label {{ color: var(--text); font-weight: 900; }}
    .upload-form input {{
      min-height: 44px;
      width: 100%;
      color: var(--muted);
    }}
    @media (max-width: 1100px) {{
      .shell {{ grid-template-columns: 1fr; }}
      .sidebar {{ position: static; height: auto; }}
      .nav {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .compact-grid {{ grid-template-columns: 1fr; }}
      .surface-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 680px) {{
      .main {{ width: min(100% - 24px, 760px); }}
      .topbar {{ display: block; }}
      .runtime-pill {{ margin-top: 12px; }}
      .nav,
      .metric-grid {{ grid-template-columns: 1fr; }}
      .action-strip {{ grid-template-columns: 1fr; }}
      .upload-form {{ grid-template-columns: 1fr; }}
      .hero h2 {{ font-size: 1.55rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      .nav a {{ transition: none; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#workspace">Skip to workspace</a>
  <div class="shell">
    <aside class="sidebar" aria-label="Command Center navigation">
      <div class="brand">
        <p class="eyebrow">Ariadne Thread</p>
        <h1>Capture Command Center</h1>
      </div>
      <nav class="nav" aria-label="First-slice surfaces">
        <a href="#opportunity">Opportunity <small>active</small></a>
        <a href="#knowledge-context">Knowledge Context <small>{_pending_recommendation_count(knowledge_context.recommendations)}</small></a>
        <a href="#quick-capture">Quick Capture <small>review</small></a>
        <a href="#document-intake">Document Intake <small>{len(document_intake_records)}</small></a>
        <a href="/packets/review">Living Briefing Packet <small>deck</small></a>
        <a href="#action-plan">Capture Action Plan <small>{len(action_view.items)}</small></a>
      </nav>
      <div class="advanced">
        <p class="advanced-label">Advanced / read-only</p>
        <nav class="nav" aria-label="Advanced surfaces">
          <a href="#capability-studio">Capability Studio <small>{_capability_outputs_needing_review_count(capability_runs)}</small></a>
          <a href="#federal-data-capabilities">Federal Data <small>{len(federal_data_registry.capabilities)}</small></a>
                    <a href="#capture-research-enrichment">Capture Research <small>{len(capture_research_runs)}</small></a>
          <a href="#sam-gov-enrichment-profiles">SAM.gov Profiles <small>{len(sam_gov_profiles)}</small></a>
          <a href="#piid-profile-command-surface">PIID Profiles <small>{len(piid_profiles)}</small></a>
        </nav>
      </div>
    </aside>
    <main class="main" id="workspace">
      <div class="topbar">
        <div>
          <p class="eyebrow">{escape(settings.public_app_name)}</p>
          <h2>Today's capture thread.</h2>
        </div>
        <div class="runtime-pill">Runtime online - {escape(settings.local_url)}</div>
      </div>
      <section class="hero" aria-labelledby="mission-heading">
        <h2 id="mission-heading">AFLCMC recompete support</h2>
        <p>Lifecycle: {escape(opportunity.lifecycle_state.value.replace("_", " "))}. Entry: incumbent recompete. Packet: {escape(packet.readiness.value.replace("_", " "))}.</p>
        {_render_metrics(action_view, coverage_view, capture_review, catalog, reference_influences)}
      </section>
      <div class="surface-grid">
        {_render_opportunity_panel(opportunity)}
        {_render_knowledge_context_panel(knowledge_context)}
        {_render_quick_capture_panel(quick_capture, capture_review, reference_influences, pasted_capture, pasted_review, uploaded_capture, uploaded_review, unsupported_upload.intake_candidate)}
        {_render_document_intake_demo_thread_panel(document_intake_demo)}
        {_render_document_intake_queue_panel(document_intake_records, accepted_document_evidence_links)}
        {_render_document_intake_capabilities_panel(document_intake_adapter_declarations)}
        {_render_federal_data_capabilities_panel(federal_data_registry.capabilities)}
        {_render_capture_research_enrichment_panel(capture_research_runs)}
        {_render_sam_gov_enrichment_profiles_panel(sam_gov_profiles, sam_gov_live_ready)}
        {_render_piid_profile_command_surface_panel(piid_profiles)}
        {_render_document_intake_draft_parts_panel(document_intake_drafts, accepted_document_evidence_links)}
        {_render_document_intake_capture_candidates_panel(document_intake_capture_candidates)}
        {_render_knowledge_note_projections_panel(document_intake_knowledge_note_projections)}
        {_render_capture_intelligence_draft_panel(capture_review.intelligence_draft)}
        {_render_accepted_promotions_panel(accepted_evidence, accepted_action, accepted_packet_answer, discarded_output)}
        {_render_packet_panel(packet, coverage_view)}
        {_render_action_plan_panel(action_view)}
        {_render_capability_panel(catalog, capability_runs)}
      </div>
    </main>
  </div>
</body>
</html>"""


def build_command_center_knowledge_context(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
    demo: QuickCaptureDemoThread | None = None,
) -> CommandCenterKnowledgeContext:
    root = workspace_root or Path.cwd()
    thread = demo or build_quick_capture_demo_thread(settings, workspace_root=root)
    opportunity_id = _knowledge_context_opportunity_id(thread)
    evidence_items = _stable_demo_knowledge_evidence_items(thread)
    evidence_id_map = _knowledge_evidence_id_map(thread)
    evidence_store = _demo_knowledge_evidence_store(evidence_items)
    action_plan = _stable_knowledge_action_plan(
        thread,
        opportunity_id=opportunity_id,
        evidence_id_map=evidence_id_map,
    )
    context = get_opportunity_knowledge_context(
        opportunity_id=opportunity_id,
        opportunities=(thread.opportunity.model_copy(update={"name": opportunity_id}),),
        evidence_store=evidence_store,
        document_intake_store=DocumentIntakeStore(
            _resolve_runtime_path(root, settings.ariadne_document_intake_dir)
        ),
        piid_profile_store=PiidProfileStore(
            _resolve_runtime_path(root, settings.ariadne_piid_profiles_dir)
        ),
        sam_gov_profile_store=SamGovProfileStore(
            _resolve_runtime_path(root, settings.ariadne_sam_gov_profiles_dir)
        ),
        capability_run_store=CapabilityRunStore(
            _resolve_runtime_path(root, settings.ariadne_capability_runs_dir)
        ),
        packet_field_answers=_knowledge_packet_field_answers(
            thread,
            opportunity_id,
            evidence_items=evidence_items,
            evidence_id_map=evidence_id_map,
        ),
        action_plans=(action_plan,),
    )
    recommendation_store = NextActionRecommendationStore(
        _resolve_runtime_path(root, settings.ariadne_next_action_recommendations_dir)
    )
    return CommandCenterKnowledgeContext(
        opportunity_id=opportunity_id,
        context=context,
        recommendations=tuple(
            recommendation_store.list(opportunity_id=opportunity_id)
        ),
        action_plan=action_plan,
    )


def _knowledge_context_opportunity_id(thread: QuickCaptureDemoThread) -> str:
    return thread.accepted_packet_answer.opportunity_id or thread.opportunity.name


def _demo_knowledge_evidence_store(
    evidence_items: tuple[EvidenceItem, ...],
) -> InMemoryDemoEvidenceStore:
    evidence_store = InMemoryDemoEvidenceStore()
    for evidence in evidence_items:
        evidence_store.write(evidence)
    return evidence_store


def _stable_demo_knowledge_evidence_items(
    thread: QuickCaptureDemoThread,
) -> tuple[EvidenceItem, ...]:
    evidence_items: list[EvidenceItem] = []
    if thread.accepted_evidence.evidence is not None:
        evidence_items.append(
            thread.accepted_evidence.evidence.model_copy(
                update={"id": "ev_demo_quick_capture_customer_signal"}
            )
        )
    if thread.document_intake.accepted_evidence.evidence is not None:
        evidence_items.append(thread.document_intake.accepted_evidence.evidence)
    return tuple(evidence_items)


def _knowledge_evidence_id_map(thread: QuickCaptureDemoThread) -> dict[str, str]:
    evidence_id_map: dict[str, str] = {}
    if thread.accepted_evidence.evidence is not None:
        evidence_id_map[thread.accepted_evidence.evidence.id] = (
            "ev_demo_quick_capture_customer_signal"
        )
    if thread.document_intake.accepted_evidence.evidence is not None:
        evidence = thread.document_intake.accepted_evidence.evidence
        evidence_id_map[evidence.id] = evidence.id
    return evidence_id_map


def _stable_knowledge_action_plan(
    thread: QuickCaptureDemoThread,
    *,
    opportunity_id: str,
    evidence_id_map: dict[str, str],
) -> CaptureActionPlan:
    return thread.action_plan.model_copy(
        update={
            "opportunity_name": opportunity_id,
            "items": tuple(
                item.model_copy(
                    update={
                        "id": _stable_action_item_id(opportunity_id, index, item.action),
                        "related_evidence_ids": _map_evidence_ids(
                            item.related_evidence_ids,
                            evidence_id_map,
                        ),
                    }
                )
                for index, item in enumerate(thread.action_plan.items, start=1)
            ),
        }
    )


def _knowledge_packet_field_answers(
    thread: QuickCaptureDemoThread,
    opportunity_id: str,
    *,
    evidence_items: tuple[EvidenceItem, ...],
    evidence_id_map: dict[str, str],
):
    trusted_evidence_ids = tuple(evidence.id for evidence in evidence_items)
    return (
        thread.accepted_packet_answer.model_copy(
            update={
                "opportunity_id": opportunity_id,
                "evidence_ids": _map_evidence_ids(
                    thread.accepted_packet_answer.evidence_ids,
                    evidence_id_map,
                ),
            }
        ),
        create_packet_field_answer(
            field_key="primary_scope",
            opportunity_id=opportunity_id,
            status=PacketFieldAnswerStatus.GAP,
            evidence_status=EvidenceStatus.GAP,
            evidence_ids=trusted_evidence_ids[:1],
            gap_summary="Need validated transition scope before gate review.",
        ),
    )


def _map_evidence_ids(
    evidence_ids: tuple[str, ...],
    evidence_id_map: dict[str, str],
) -> tuple[str, ...]:
    return tuple(evidence_id_map.get(evidence_id, evidence_id) for evidence_id in evidence_ids)


def _stable_action_item_id(opportunity_id: str, index: int, action: str) -> str:
    digest = sha256(f"{opportunity_id}|{index}|{action}".encode("utf-8")).hexdigest()
    return f"ap_demo_{digest[:12]}"


def render_capability_studio_shell(
        settings: RuntimeSettings,
        *,
        run_id: str | None = None,
        workspace_root: Path | None = None,
) -> str:
        root = workspace_root or Path.cwd()
        store = CapabilityRunStore(
                _resolve_runtime_path(root, settings.ariadne_capability_runs_dir)
        )
        runs = tuple(store.list())
        selected_run = store.read(run_id) if run_id is not None else (runs[0] if runs else None)
        detail = _render_capability_studio_empty_state()
        if selected_run is not None:
                detail = _render_capability_run_detail(selected_run)

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(settings.public_app_name)} Capability Studio</title>
    <style>
        :root {{ color-scheme: dark; --bg: #020617; --surface: #0f172a; --surface-strong: #111c31; --edge: #334155; --edge-soft: #243244; --text: #f8fafc; --muted: #b6c4d6; --quiet: #8292a8; --cyan: #22d3ee; --green: #22c55e; --amber: #fbbf24; --red: #fb7185; --focus: #fbbf24; }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; min-height: 100dvh; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--text); }}
        a {{ color: inherit; }}
        a:focus-visible, button:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
        .shell {{ width: min(100% - 32px, 1360px); margin: 0 auto; padding: 24px 0 48px; }}
        .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 18px; }}
        .back-link, .link-row {{ display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 10px 14px; border: 1px solid var(--cyan); border-radius: 8px; color: var(--cyan); text-decoration: none; font-weight: 900; }}
        .eyebrow {{ margin: 0 0 8px; color: var(--cyan); font-size: 0.78rem; font-weight: 800; letter-spacing: 0; text-transform: uppercase; }}
        h1 {{ margin: 0; font-size: 1.7rem; line-height: 1.15; letter-spacing: 0; }}
        h2 {{ margin: 0; font-size: 1.05rem; line-height: 1.25; letter-spacing: 0; }}
        h3 {{ margin: 0; font-size: 0.95rem; line-height: 1.3; letter-spacing: 0; }}
        p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
        .studio-grid {{ display: grid; grid-template-columns: 0.8fr 1.2fr; gap: 14px; }}
        .panel {{ border: 1px solid var(--edge); border-radius: 8px; background: rgba(15, 23, 42, 0.94); padding: 16px; }}
        .panel-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }}
        .row-list {{ display: grid; gap: 8px; }}
        .row {{ display: grid; gap: 6px; padding: 12px; border: 1px solid var(--edge-soft); border-radius: 8px; background: var(--surface-strong); }}
        .row strong {{ color: var(--text); }}
        .row span {{ color: var(--muted); line-height: 1.45; overflow-wrap: anywhere; }}
        .status-chip {{ display: inline-flex; align-items: center; min-height: 30px; padding: 5px 8px; border: 1px solid var(--edge); border-radius: 8px; color: var(--muted); background: #0b1220; font-size: 0.78rem; font-weight: 800; white-space: nowrap; }}
        .status-chip.green {{ border-color: rgba(34, 197, 94, 0.55); color: var(--green); background: rgba(34, 197, 94, 0.1); }}
        .status-chip.cyan {{ border-color: rgba(34, 211, 238, 0.55); color: var(--cyan); background: rgba(34, 211, 238, 0.1); }}
        .status-chip.amber {{ border-color: rgba(251, 191, 36, 0.55); color: var(--amber); background: rgba(251, 191, 36, 0.1); }}
        .status-chip.red {{ border-color: rgba(251, 113, 133, 0.55); color: var(--red); background: rgba(251, 113, 133, 0.1); }}
        .mono {{ font-family: Consolas, "Courier New", monospace; }}
        @media (max-width: 920px) {{ .studio-grid {{ grid-template-columns: 1fr; }} .topbar {{ display: block; }} .back-link {{ margin-top: 12px; }} }}
    </style>
</head>
<body>
    <main class="shell">
        <div class="topbar">
            <div><p class="eyebrow">Advanced workspace</p><h1>Capability Studio</h1></div>
            <a class="back-link" href="/#capability-studio">Back to Command Center</a>
        </div>
        <div class="studio-grid">
            {_render_capability_run_history(runs)}
            {detail}
        </div>
    </main>
</body>
</html>"""


def _resolve_runtime_path(workspace_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return workspace_root / path


def _render_capability_run_history(runs: tuple[CapabilityRun, ...]) -> str:
    if not runs:
        rows = """<div class="row"><strong>No Capability Runs yet</strong><span>Run local Capability Catalog validation to create the first reviewable run record.</span></div>"""
    else:
        rows = "".join(_render_capability_run_history_row(run) for run in runs)
    return f"""<section class="panel" aria-labelledby="capability-run-history-heading">
      <div class="panel-heading"><h2 id="capability-run-history-heading">Run History</h2><span class="status-chip cyan">{len(runs)} runs</span></div>
      <div class="row-list">{rows}</div>
    </section>"""


def _render_capability_run_history_row(run: CapabilityRun) -> str:
    return f"""<div class="row"><strong class="mono">{escape(run.run_id)}</strong><span>{escape(run.capability_id)} - {escape(run.executor_kind.value)} - {escape(run.status.value)}</span><span>{len(run.outputs)} outputs - {escape(run.product_workflow)}</span><a class="link-row" href="/capability-studio/runs/{escape(run.run_id)}">Open run detail</a></div>"""


def _render_capability_studio_empty_state() -> str:
    return """<section class="panel" aria-labelledby="capability-run-detail-heading"><div class="panel-heading"><h2 id="capability-run-detail-heading">Run Detail</h2><span class="status-chip amber">empty</span></div><div class="row-list"><div class="row"><strong>No run selected</strong><span>Capability Reasoning View appears after a run exists.</span></div></div></section>"""


def _render_capability_run_detail(run: CapabilityRun) -> str:
    outputs = "".join(_render_capability_run_output_row(output) for output in run.outputs)
    reasoning = build_capability_reasoning_view(run)
    return f"""<section class="panel" aria-labelledby="capability-run-detail-heading">
      <div class="panel-heading"><h2 id="capability-run-detail-heading">Run Detail</h2><span class="status-chip {_status_chip_class(run.status.value)}">{escape(run.status.value)}</span></div>
      <div class="row-list">
        <div class="row"><strong>{escape(run.capability_id)}</strong><span>Executor: {escape(run.executor_kind.value)} - Capability type: {escape(run.capability_type.value)} - Workflow: {escape(run.product_workflow)}</span><span>{escape(run.inputs_summary)}</span><span>Created: {escape(run.created_at.isoformat())}</span></div>
        <div class="row"><strong>Capability Provenance</strong>{_render_inline_spans(_provenance_items(run))}</div>
        <div class="row"><strong>Validation Findings</strong>{outputs}</div>
        {_render_capability_reasoning_view(reasoning)}
      </div>
    </section>"""


def _render_capability_run_output_row(output) -> str:
    gaps = " | ".join(output.gaps) if output.gaps else "No gaps recorded."
    decisions = (
        " | ".join(_review_decision_label(decision) for decision in output.review_decisions)
        if output.review_decisions
        else "No review decisions recorded."
    )
    return f"""<span><strong>{escape(output.title)}</strong></span><span>{escape(output.summary)}</span><span>Review: {escape(output.review_state.value)} - Autonomy: {escape(output.autonomy_recommendation.value)} - Destination: {escape(output.recommended_destination or "review queue")}</span><span>Gaps: {escape(gaps)}</span><span>Review decisions: {escape(decisions)}</span>"""


def _render_capability_reasoning_view(reasoning: CapabilityReasoningView) -> str:
    model_status = (
        f"Model: {reasoning.model_name} - {reasoning.model_status}"
        if reasoning.model_name or reasoning.model_status
        else "Model: none"
    )
    return f"""<div class="row"><strong>Capability Reasoning View</strong><span>{escape(reasoning.title)}</span><span>Capability: {escape(reasoning.capability_id)} - Executor: {escape(reasoning.executor_kind.value)} - Output: {escape(reasoning.output_id)}</span><span>{escape(model_status)}</span><span>Input summary: {escape(reasoning.input_summary)}</span><span>Source refs: {escape(_join_or_none(reasoning.source_refs))}</span><span>Tools: {escape(_join_or_none(reasoning.tool_names))}</span><span>Validation logic: {escape(_join_or_none(reasoning.validation_logic))}</span><span>Gaps: {escape(_join_or_none(reasoning.gaps))}</span><span>Limitations: {escape(_join_or_none(reasoning.limitations))}</span><span>Recommended destination: {escape(reasoning.recommended_destination or "review queue")} - Autonomy: {escape(reasoning.autonomy_recommendation.value)}</span><span>Review history: {escape(_join_or_none(reasoning.review_decision_history))}</span></div>"""


def _provenance_items(run: CapabilityRun) -> tuple[str, ...]:
    items: list[str] = []
    for key in (
        "sources",
        "tool_names",
        "executor",
        "source_mode",
        "model_name",
        "model_status",
        "ollama_base_url",
        "timeout_seconds",
        "entry_count",
        "model_required",
        "network_required",
    ):
        if key in run.provenance:
            items.append(f"{key}: {run.provenance[key]}")
    return tuple(items)


def _render_inline_spans(values: tuple[str, ...]) -> str:
    if not values:
        return "<span>No provenance recorded.</span>"
    return "".join(f"<span>{escape(value)}</span>" for value in values)


def _review_decision_label(decision) -> str:
    destination = f" -> {decision.routed_destination}" if decision.routed_destination else ""
    rationale = f": {decision.reviewer_rationale}" if decision.reviewer_rationale else ""
    return f"{decision.decision.value}{destination}{rationale}"


def _join_or_none(values: tuple[str, ...]) -> str:
    return " | ".join(values) if values else "none"


def _status_chip_class(status: str) -> str:
    if status == "needs_review":
        return "amber"
    if status == "succeeded":
        return "green"
    if status in {"failed", "unavailable"}:
        return "red"
    return "cyan"


def _render_metrics(
    action_view,
    coverage_view,
    capture_review,
    catalog: CapabilityCatalog,
    reference_influences: tuple[ReferenceWikiInfluence, ...],
) -> str:
    open_coverage = sum(
        section.evidence_status is not EvidenceStatus.ANSWERED
        for section in coverage_view.sections
    )
    return f"""<section class="metric-grid" aria-label="Command Center metrics">
      <div class="metric"><span>Opportunity</span><strong class="cyan">Pursuing</strong></div>
      <div class="metric"><span>Packet gaps</span><strong class="amber">{open_coverage}</strong></div>
      <div class="metric"><span>Action items</span><strong>{len(action_view.items)}</strong></div>
      <div class="metric"><span>Local capabilities</span><strong class="green">{len(catalog.entries)}</strong></div>
      <div class="metric"><span>Quick Capture</span><strong>{len(capture_review.proposals)} proposals</strong></div>
      <div class="metric"><span>Reference influences</span><strong class="cyan">{len(reference_influences)}</strong></div>
      <div class="metric"><span>Knowledge flow</span><strong>review first</strong></div>
      <div class="metric"><span>Autonomy</span><strong>human gated</strong></div>
    </section>"""


def _render_opportunity_panel(opportunity) -> str:
    workstreams = "".join(
        f"""<div class="row"><strong>{escape(need.workstream.value.replace("_", " ").title())}</strong><span>{escape(need.rationale)}</span></div>"""
        for need in opportunity.backfill_needs
    )
    return f"""<section class="panel" id="opportunity" aria-labelledby="opportunity-heading">
      <div class="panel-heading"><h2 id="opportunity-heading">Opportunity</h2><span class="status-chip cyan">{escape(opportunity.lifecycle_state.value.replace("_", " ").title())}</span></div>
      <div class="row-list">
        <div class="row"><strong>{escape(opportunity.name)}</strong><span>{escape(opportunity.entry_context.rationale)}</span></div>
        {workstreams}
      </div>
    </section>"""


def _render_knowledge_context_panel(
    knowledge_context: CommandCenterKnowledgeContext,
) -> str:
    context = knowledge_context.context
    recommendations = knowledge_context.recommendations
    pending_recommendations = tuple(
        recommendation
        for recommendation in recommendations
        if recommendation.review_state is NextActionRecommendationReviewState.PENDING
    )
    history_recommendations = tuple(
        recommendation
        for recommendation in recommendations
        if recommendation.review_state is not NextActionRecommendationReviewState.PENDING
    )
    health_label = _knowledge_context_health_label(context, pending_recommendations)
    gap_rows = _render_knowledge_gap_rows(context.gaps, context.source_limitations)
    pending_rows = _render_pending_recommendation_rows(pending_recommendations)
    command_rows = _render_knowledge_command_rows(context)
    detail_rows = _render_knowledge_context_detail_rows(
        context,
        recommendations=recommendations,
        history_recommendations=history_recommendations,
    )
    return f"""<section class="panel" id="knowledge-context" aria-labelledby="knowledge-context-heading">
      <div class="panel-heading"><h2 id="knowledge-context-heading">Knowledge Context</h2><span class="status-chip amber">{escape(health_label)}</span></div>
      <div class="row-list">
        <div class="compact-grid" aria-label="Knowledge Context compact summary">
          <div class="row"><strong>Context health</strong><span>{escape(health_label)} for {escape(knowledge_context.opportunity_id)}.</span></div>
          <div class="row"><strong>Trusted Context</strong><span>{context.trusted_context.count} records ready for capture decisions.</span></div>
          <div class="row"><strong>Reviewable Context</strong><span>{context.reviewable_context.count} records need human review before trusted use.</span></div>
        </div>
        <div class="row"><strong>Recommend Next Capture Actions</strong><span>Generate reviewable recommendations from current gaps, source limitations, and deterministic capability routes.</span><form class="inline-form" action="/knowledge-context/opportunities/{escape(knowledge_context.opportunity_id)}/recommend-next-capture-actions" method="post"><button class="action-button" type="submit">Recommend Next Capture Actions</button></form></div>
        <div class="row"><strong>Top gaps and limitations</strong>{gap_rows}</div>
        <div class="row"><strong>Pending recommendations</strong>{pending_rows}</div>
        <div class="row"><strong>Next command links</strong>{command_rows}</div>
      </div>
      <details class="detail-block">
        <summary>Supporting refs and provenance</summary>
        <div class="detail-body">{detail_rows}</div>
      </details>
    </section>"""


def _knowledge_context_health_label(
    context: OpportunityKnowledgeContextView,
    pending_recommendations: tuple[NextActionRecommendation, ...],
) -> str:
    if context.gaps or context.source_limitations or pending_recommendations:
        return "Review needed"
    if context.reviewable_context.count:
        return "Context review"
    return "Steady"


def _render_knowledge_gap_rows(
    gaps: tuple[KnowledgeGapSummary, ...],
    source_limitations: tuple[KnowledgeSourceLimitation, ...],
) -> str:
    rows = []
    rows.extend(
        f"""<span>{escape(gap.summary)} <span class="meta-line">{escape(gap.record_id)}</span></span>"""
        for gap in gaps[:2]
    )
    rows.extend(
        f"""<span>{escape(limitation.summary)} <span class="meta-line">{escape(limitation.record_id)}</span></span>"""
        for limitation in source_limitations[:2]
    )
    if not rows:
        return "<span>No active gaps or source limitations for this Opportunity.</span>"
    return "".join(rows)


def _render_pending_recommendation_rows(
    recommendations: tuple[NextActionRecommendation, ...],
) -> str:
    if not recommendations:
        return "<span>No pending recommendations yet.</span>"
    return "".join(
        _render_pending_recommendation_row(recommendation)
        for recommendation in recommendations[:3]
    )


def _render_pending_recommendation_row(
    recommendation: NextActionRecommendation,
) -> str:
    summary = f"""<span>{escape(recommendation.title)} - {escape(recommendation.capability_route.support.value.replace("_", " "))}</span>"""
    if recommendation.is_stale:
        return (
            summary
            + """<span>Refresh needed before this recommendation can create Action Plan work.</span><button class="action-button secondary" type="button" disabled>Refresh needed</button>"""
        )
    return (
        summary
        + f"""<form class="inline-form" action="/knowledge-context/recommendations/{escape(recommendation.id)}/accept" method="post"><button class="action-button secondary" type="submit">Accept to Action Plan</button></form>"""
    )


def _render_knowledge_command_rows(context: OpportunityKnowledgeContextView) -> str:
    if not context.next_command_links:
        return "<span>No context command links yet.</span>"
    return "".join(
        f"""<span>{escape(link.label)} <span class="meta-line">{escape(link.command_id)} - {escape(link.target_id)}</span></span>"""
        for link in context.next_command_links[:4]
    )


def _render_knowledge_context_detail_rows(
    context: OpportunityKnowledgeContextView,
    *,
    recommendations: tuple[NextActionRecommendation, ...],
    history_recommendations: tuple[NextActionRecommendation, ...],
) -> str:
    trusted = _render_knowledge_context_items(context.trusted_context, "Trusted Context")
    reviewable = _render_knowledge_context_items(
        context.reviewable_context,
        "Reviewable Context",
    )
    recommendation_rows = _render_recommendation_detail_rows(recommendations)
    history_rows = _render_recommendation_history_rows(history_recommendations)
    return trusted + reviewable + recommendation_rows + history_rows


def _render_knowledge_context_items(
    section: KnowledgeContextSection,
    label: str,
) -> str:
    if not section.items:
        return f"""<div class="row"><strong>{escape(label)}</strong><span>No records in this section.</span></div>"""
    rows = "".join(_render_knowledge_context_item(item) for item in section.items[:5])
    return f"""<div class="row"><strong>{escape(label)}</strong><div class="row-list">{rows}</div></div>"""


def _render_knowledge_context_item(item: KnowledgeContextItem) -> str:
    return f"""<div class="row"><strong>{escape(item.title)}</strong><span>{escape(item.summary)}</span><span class="meta-line">{escape(item.record_kind.value)} - {escape(item.record_id)} - {item.related_connection_count} refs</span></div>"""


def _render_recommendation_detail_rows(
    recommendations: tuple[NextActionRecommendation, ...],
) -> str:
    if not recommendations:
        return """<div class="row"><strong>Recommendation detail</strong><span>No recommendation snapshots have been generated.</span></div>"""
    rows = "".join(_render_recommendation_detail_row(item) for item in recommendations[:5])
    return f"""<div class="row"><strong>Recommendation detail</strong><div class="row-list">{rows}</div></div>"""


def _render_recommendation_detail_row(recommendation: NextActionRecommendation) -> str:
    snapshot = recommendation.context_snapshot
    stale = (
        f"Stale snapshot: {escape(recommendation.stale_reason or 'refresh needed')}"
        if recommendation.is_stale
        else "Snapshot current"
    )
    route = recommendation.capability_route
    return f"""<div class="row"><strong>{escape(recommendation.title)}</strong><span>{escape(recommendation.description)}</span><span>Capability route: {escape(route.support.value.replace("_", " "))} - {escape(route.capability_id or route.next_command_id)} - {escape(route.rationale)}</span><span>{stale}</span><span class="meta-line">trusted refs: {escape(", ".join(snapshot.trusted_refs) or "none")} | reviewable refs: {escape(", ".join(snapshot.reviewable_refs) or "none")}</span></div>"""


def _render_recommendation_history_rows(
    recommendations: tuple[NextActionRecommendation, ...],
) -> str:
    if not recommendations:
        return """<div class="row"><strong>Rejected/discarded recommendation history</strong><span>No routed, accepted, or discarded recommendation decisions yet.</span></div>"""
    rows = "".join(
        _render_recommendation_history_row(recommendation)
        for recommendation in recommendations[:5]
    )
    return f"""<div class="row"><strong>Rejected/discarded recommendation history</strong><div class="row-list">{rows}</div></div>"""


def _render_recommendation_history_row(
    recommendation: NextActionRecommendation,
) -> str:
    decisions = " | ".join(
        f"{decision.decision}: {decision.reviewer_rationale}"
        for decision in recommendation.review_decisions
    ) or "No review decision recorded."
    return f"""<div class="row"><strong>{escape(recommendation.title)}</strong><span>State: {escape(recommendation.review_state.value)} - Version: {recommendation.version}</span><span>{escape(decisions)}</span></div>"""


def _pending_recommendation_count(
    recommendations: tuple[NextActionRecommendation, ...],
) -> int:
    return sum(
        recommendation.review_state is NextActionRecommendationReviewState.PENDING
        for recommendation in recommendations
    )


def _render_quick_capture_panel(
    raw_item,
    capture_review,
    reference_influences: tuple[ReferenceWikiInfluence, ...],
    pasted_raw_item,
    pasted_review,
    uploaded_raw_item,
    uploaded_review,
    intake_candidate,
) -> str:
    influence_rows = "".join(
        f"""<div class="row"><strong>{escape(influence.title)}</strong><span>{escape(influence.influence_type.value.replace("_", " ").title())} - {escape(influence.why_it_matters)}</span></div>"""
        for influence in reference_influences[:4]
    )
    pasted_metadata = pasted_raw_item.source_metadata
    uploaded_metadata = uploaded_raw_item.source_metadata
    candidate_status = (
        intake_candidate.status.value.replace("_", " ").title()
        if intake_candidate is not None
        else "Parser Required"
    )
    candidate_reason = (
        intake_candidate.reason
        if intake_candidate is not None
        else "Unsupported file requires future Document Intake."
    )
    candidate_hint = (
        intake_candidate.parser_hint
        if intake_candidate is not None
        else "Parser required before Quick Capture can trust this source."
    )
    return f"""<section class="panel" id="quick-capture" aria-labelledby="quick-capture-heading">
      <div class="panel-heading"><h2 id="quick-capture-heading">Quick Capture</h2><span class="status-chip amber">Needs Review</span></div>
      <div class="row-list">
        <div class="row"><strong>{escape(raw_item.id)}</strong><span>{escape(raw_item.content)}</span></div>
        <div class="row"><strong>Pasted Text Intake</strong><span>{escape(pasted_metadata.source_type.value if pasted_metadata else "pasted_text")} - {len(pasted_review.proposals)} review proposals queued.</span></div>
        <div class="row"><strong>Text / Markdown Upload</strong><span>{escape(uploaded_metadata.filename if uploaded_metadata and uploaded_metadata.filename else "uploaded material")} - {escape(uploaded_metadata.content_type if uploaded_metadata and uploaded_metadata.content_type else "text")} - {len(uploaded_review.proposals)} review proposals queued.</span></div>
      <div class="row"><strong>Document Intake Candidate</strong><span>{escape(intake_candidate.filename if intake_candidate and intake_candidate.filename else "unsupported file")} - {escape(candidate_status)}</span><span>{escape(candidate_reason)}</span><span>{escape(candidate_hint)}</span></div>
        <form class="upload-form" action="/api/quick-capture/uploads" method="post" enctype="multipart/form-data">
          <label for="quick-capture-upload">Text / Markdown Upload</label>
          <input id="quick-capture-upload" name="file" type="file" accept=".txt,.text,.md,.markdown,text/plain,text/markdown">
          <button class="action-button" type="submit">Upload</button>
        </form>
        <div class="row"><strong>{len(capture_review.proposals)} review proposals</strong><span>Evidence Item Review plus Action Plan Item Review queued.</span></div>
        <div class="row"><strong>{len(reference_influences)} Reference Wiki influences</strong><span>Background context surfaced for review; no opportunity evidence is written automatically.</span></div>
        {influence_rows}
      </div>
    </section>"""


def _render_document_intake_queue_panel(
    records: list[DocumentIntakeRecord],
    accepted_links: list[AcceptedDocumentEvidenceLink],
) -> str:
    if records:
        rows = "".join(
            _render_document_intake_record_row(record, accepted_links)
            for record in records
        )
    else:
        rows = """<div class="row"><strong>No persisted intake records</strong><span>Upload or register source material to start Document Intake.</span></div>"""

    return f"""<section class="panel" id="document-intake" aria-labelledby="document-intake-heading">
      <div class="panel-heading"><h2 id="document-intake-heading">Document Intake Queue</h2><span class="status-chip cyan">{len(records)} persisted</span></div>
      <div class="row-list">
        <div class="row"><strong>Backed by persisted intake records</strong><span>Queue state survives runtime restarts and stays separate from trusted evidence.</span></div>
        {rows}
      </div>
    </section>"""


def _render_document_intake_record_row(
    record: DocumentIntakeRecord,
    accepted_links: list[AcceptedDocumentEvidenceLink],
) -> str:
    filename = record.filename or record.source_ref
    status = record.status.value.replace("_", " ").title()
    queue_state = record.queue_state.value.title() if record.queue_state else "Ready"
    material_type = (
        record.material_type.value.replace("_", " ").title()
        if record.material_type
        else "Generic Source Material"
    )
    content_type = record.content_type.value.replace("_", " ").title()
    extraction_status = (
        record.extraction_status.value.replace("_", " ").title()
        if record.extraction_status
        else "Not Started"
    )
    review_status = (
        record.extraction_review_status.value.replace("_", " ").title()
        if record.extraction_review_status
        else "Not Ready"
    )
    review_need = (
        "Review needed"
        if record.extraction_review_status
        in {
            ExtractionBundleReviewStatus.PENDING_REVIEW,
            ExtractionBundleReviewStatus.IN_REVIEW,
        }
        else "No extraction review queued"
    )
    opportunity = record.opportunity_id or "unassigned"
    warnings = " | ".join(record.warnings) if record.warnings else "no warnings"
    accepted_count = sum(link.intake_record_id == record.id for link in accepted_links)
    return f"""<div class="row"><strong>{escape(filename)}</strong><span>Queue: {escape(queue_state)} - {escape(status)} - {escape(material_type)} - {escape(content_type)} - {escape(opportunity)}</span><span>Extraction: {escape(extraction_status)} - Review: {escape(review_status)} - {escape(review_need)} - Extraction warnings: {record.extraction_warning_count} - Accepted Evidence: {accepted_count}</span><span>{escape(record.capability_hint)}</span><span>Source: {escape(record.source_ref)} - {record.byte_size} bytes</span><span>{escape(warnings)}</span></div>"""


def _render_document_intake_demo_thread_panel(
    document_thread: DocumentIntakeDemoThread,
) -> str:
    source_material = document_thread.source_material
    record = document_thread.record
    bundle = document_thread.bundle
    draft = document_thread.draft
    accepted_result = document_thread.accepted_evidence
    projection = document_thread.projection
    first_piece = draft.intelligence_pieces[0]
    skill_chain = " -> ".join(first_piece.suggested_skill_chain)
    workflow_labels = _demo_capture_candidate_workflow_labels(
        document_thread.candidates
    )
    classification = (
        f"Classification: {source_material.status.value.replace('_', ' ').title()} - "
        f"{record.material_type.value.replace('_', ' ').title()}"
    )
    extraction_state = (
        f"Extraction Bundle: {bundle.extraction_status.value.replace('_', ' ').title()} - "
        f"{bundle.review_status.value.replace('_', ' ').title()}"
    )
    projection_href = (
        "/api/document-intake/knowledge-note-projections?bundle_id="
        f"{projection.source_extraction_bundle_id}"
    )
    return f"""<section class="panel" id="document-intake-demo-thread" aria-labelledby="document-intake-demo-thread-heading">
      <div class="panel-heading"><h2 id="document-intake-demo-thread-heading">Document Intake Demo Thread</h2><span class="status-chip green">Real behavior path</span></div>
      <div class="row-list">
      <div class="row"><strong>{escape(source_material.filename or record.source_ref)}</strong><span>{escape(classification)}</span><span>{escape(source_material.capability_hint or record.capability_hint)}</span><span>Source: {escape(record.source_ref)} - {record.byte_size} bytes</span></div>
      <div class="row"><strong>{escape(extraction_state)}</strong><span>Source spans: {len(bundle.source_spans)} - Entity candidates: {len(bundle.entity_candidates)} - Relationship candidates: {len(bundle.relationship_candidates)}</span><span>Extraction warnings: {len(bundle.warnings)}</span><span>Parser provenance: {escape(bundle.parser_provenance.adapter_name)} {escape(bundle.parser_provenance.adapter_version)}</span></div>
      <div class="row"><strong>Recommended document-derived action</strong><span>{escape(first_piece.content)}</span><span>Recommended Route: {escape(first_piece.recommended_route.replace("_", " "))}</span><span>Skill-chain options: {escape(skill_chain or "needs capability match")}</span><span>{escape(first_piece.recommendation or "Review before promotion.")}</span></div>
      <div class="row"><strong>Accepted source-span evidence</strong><span>{escape(accepted_result.evidence.content)}</span><span>Evidence: {escape(accepted_result.evidence.id)} - Accepted link: {escape(accepted_result.accepted_link.id)}</span><span>Reviewer rationale: {escape(accepted_result.accepted_link.reviewer_rationale)}</span></div>
      <div class="row"><strong>Review-gated next actions</strong><span>{escape(workflow_labels)}</span><span>Document-derived candidates stay review-gated until the user accepts, routes, or discards them.</span><div class="action-strip" aria-label="Document Intake demo actions"><button class="action-button" type="button">Review Candidate</button><button class="action-button secondary" type="button">Plan Skill Chain</button><button class="action-button secondary" type="button">Route Candidate</button><button class="action-button danger" type="button">Discard Candidate</button></div></div>
      <div class="row"><strong>{escape(projection.title)}</strong><span>{escape(projection.summary)}</span><span>Structured Ariadne records remain source of truth.</span><div class="action-strip" aria-label="Document Intake demo projection actions"><a class="action-button" href="{escape(projection_href)}">Open Markdown Projection</a><button class="action-button secondary" type="button" disabled>Cannot overwrite structured knowledge</button></div></div>
      </div>
    </section>"""


def _demo_capture_candidate_workflow_labels(
    candidates: tuple[DocumentIntakeCaptureCandidate, ...],
) -> str:
    labels: list[str] = []
    for candidate in candidates:
        label = _capture_candidate_workflow_label(candidate.target_workflow)
        if label not in labels:
            labels.append(label)
    return ", ".join(labels)


def _render_document_intake_capabilities_panel(
    declarations: tuple[DocumentIntakeAdapterDeclaration, ...],
) -> str:
    deferred_count = sum(
        declaration.status.value == "deferred" for declaration in declarations
    )
    rows = "".join(
        _render_document_intake_capability_row(declaration)
        for declaration in declarations
    )
    return f"""<section class="panel" id="document-intake-capabilities" aria-labelledby="document-intake-capabilities-heading">
      <div class="panel-heading"><h2 id="document-intake-capabilities-heading">Document Intake Capabilities</h2><span class="status-chip amber">{deferred_count} deferred</span></div>
      <div class="row-list">
        <div class="row"><strong>ExtractionBundle boundary</strong><span>Future parser and retrieval hooks must produce reviewable Extraction Bundles before anything becomes trusted knowledge.</span><span>Deferred hooks do not invoke external tools.</span><a class="action-button secondary" href="/api/document-intake/capabilities">Open capability report</a></div>
        {rows}
      </div>
    </section>"""


def _render_document_intake_capability_row(
    declaration: DocumentIntakeAdapterDeclaration,
) -> str:
    material_types = ", ".join(
        material_type.value.replace("_", " ").title()
        for material_type in declaration.supported_material_types
    )
    status = declaration.status.value.replace("_", " ").title()
    adapter_kind = declaration.adapter_kind.value.replace("_", " ").title()
    deferred_reason = declaration.deferred_reason or "available for current intake"
    return f"""<div class="row"><strong>{escape(declaration.name)}</strong><span>{escape(status)} - {escape(adapter_kind)} - {escape(material_types)}</span><span>Output contract: {escape(declaration.expected_output_contract)} with parser provenance fields.</span><span>{escape(declaration.capability_hint)}</span><span>{escape(deferred_reason)}</span></div>"""


def _render_federal_data_capabilities_panel(
    manifests: tuple[FederalDataCapabilityManifest, ...],
) -> str:
    product_integrated_count = sum(
        manifest.product_status.value == "product_integrated" for manifest in manifests
    )
    rows = "".join(
        _render_federal_data_capability_row(manifest) for manifest in manifests
    )
    return f"""<section class="panel" id="federal-data-capabilities" aria-labelledby="federal-data-capabilities-heading">
      <div class="panel-heading"><h2 id="federal-data-capabilities-heading">Federal Data Capabilities</h2><span class="status-chip cyan">{product_integrated_count} product integrated</span></div>
      <div class="row-list">
        <div class="row"><strong>1102tools MCP registry</strong><span>No upstream MCP source is vendored into Ariadne.</span><span>Manifests record pinned packages, command shapes, provenance, and env-var names only.</span><a class="action-button secondary" href="/api/federal-data/capabilities">Open federal data report</a></div>
        <div class="row"><strong>Initialize smoke checks</strong><span>Initialize smoke checks use JSON-RPC initialize only.</span><span>POST /api/federal-data/capabilities/{{capability_id}}/smoke-check</span><span>Page render never starts upstream MCP processes.</span></div>
        {rows}
      </div>
    </section>"""


def _render_federal_data_capability_row(
    manifest: FederalDataCapabilityManifest,
) -> str:
    status = manifest.product_status.value.replace("_", " ")
    env_vars = (
        ", ".join(
            manifest.required_env_vars
            + manifest.optional_env_vars
            + manifest.upstream_env_vars
        )
        or "no env vars"
    )
    return f"""<div class="row"><strong>{escape(manifest.name)}</strong><span>{escape(status)} - {escape(manifest.package)} {escape(manifest.version)}</span><span>{escape(manifest.description)}</span><span>Env names: {escape(env_vars)}</span></div>"""


def _render_piid_profile_command_surface_panel(
    profiles: list[PiidContractIntelligenceProfile],
) -> str:
    if not profiles:
        rows = """<div class="row"><strong>No PIID profiles yet</strong><span>Create one through POST /api/federal-data/usaspending/piid-profiles with a contract_number.</span><span>Page render reads persisted profiles only and does not start upstream MCP processes.</span></div>"""
    else:
        rows = "".join(_render_piid_profile_row(profile) for profile in profiles[-3:])
    return f"""<section class="panel" id="piid-profile-command-surface" aria-labelledby="piid-profile-command-surface-heading">
      <div class="panel-heading"><h2 id="piid-profile-command-surface-heading">PIID Profile Command Surface</h2><span class="status-chip cyan">{len(profiles)} persisted</span></div>
      <div class="row-list">
      <div class="row"><strong>USAspending-backed profile workflow</strong><span>Enter one contract number through POST /api/federal-data/usaspending/piid-profiles, then review persisted profile output here.</span><span>Review decisions use POST /api/federal-data/usaspending/piid-profiles/{{profile_id}}/review-decisions and do not bypass Evidence Store discipline.</span></div>
      {rows}
      </div>
    </section>"""


def _render_capture_research_enrichment_panel(
    runs: tuple[CaptureResearchRun, ...],
) -> str:
    if not runs:
        rows = """<div class="row"><strong>No Capture Research runs yet</strong><span>Create one through POST /api/capture-research/runs with a bounded prompt, selected lenses, source targets, and source limits.</span><span>Page render reads persisted research runs only and does not start Firecrawl or other source collection.</span></div>"""
    else:
        rows = "".join(_render_capture_research_run_row(run) for run in runs[-3:])
    return f"""<section class="panel" id="capture-research-enrichment" aria-labelledby="capture-research-enrichment-heading">
      <div class="panel-heading"><h2 id="capture-research-enrichment-heading">Capture Research Enrichment</h2><span class="status-chip cyan">{len(runs)} persisted</span></div>
      <div class="row-list">
        <div class="row"><strong>Bounded research brief workflow</strong><span>Prompted runs start as Capture Research Briefs with selected lenses, source targets, and source limits before any source collection can occur.</span><span>Trusted downstream writes remain unavailable in this first slice.</span></div>
        {rows}
      </div>
    </section>"""


def _render_capture_research_run_row(run: CaptureResearchRun) -> str:
    prompt = run.user_prompt.prompt if run.user_prompt else run.research_brief.research_question
    lenses = ", ".join(
        lens.value.replace("_", " ") for lens in run.research_brief.selected_lenses
    )
    source_targets = ", ".join(run.research_brief.source_targets) or "none"
    source_limits = ", ".join(run.research_brief.source_limits) or "none"
    collection_state = (
        f"Source collection records: {len(run.source_collection_records)}"
        if run.source_collection_records
        else "No source collection has run for this brief."
    )
    source_refs = _render_capture_research_source_refs(run)
    return f"""<div class="row"><strong>{escape(prompt)}</strong><span>Status: {escape(run.status.value.replace("_", " ").title())}</span><span>Lenses: {escape(lenses)}</span><span>Source targets: {escape(source_targets)}</span><span>Source limits: {escape(source_limits)}</span>{source_refs}<span>{escape(collection_state)}</span><span class="meta-line">Run: {escape(run.research_run_id)} | Trigger: {escape(run.research_trigger_context.trigger_type)}</span></div>"""


def _render_capture_research_source_refs(run: CaptureResearchRun) -> str:
    if not run.source_profile_refs:
        return ""
    refs = "".join(
        f"<span>{escape(_capture_research_source_profile_label(ref.source_profile_type.value))}: {escape(ref.source_profile_id)} - {escape(ref.source_element_key)} - {escape(ref.source_element_summary)}</span>"
        for ref in run.source_profile_refs
    )
    return f"""<div class="row-list"><div class="row"><strong>Source Profile refs</strong>{refs}</div></div>"""


def _capture_research_source_profile_label(source_profile_type: str) -> str:
    labels = {
        "piid_contract_intelligence_profile": "PIID Contract Intelligence Profile",
        "sam_gov_enrichment_profile": "SAM.gov Enrichment Profile",
        "opportunity": "Opportunity",
        "opportunity_knowledge_context": "Opportunity Knowledge Context",
    }
    return labels.get(source_profile_type, source_profile_type.replace("_", " ").title())


def _render_piid_profile_row(profile: PiidContractIntelligenceProfile) -> str:
    baseline = profile.award_baseline
    burn = profile.burn_posture
    vehicle = profile.vehicle_context
    routes = "".join(
        _render_piid_enrichment_route(route)
        for route in profile.recommended_enrichment_routes[:5]
    )
    candidates = "".join(
        _render_piid_review_candidate(candidate)
        for candidate in profile.review_candidates
    )
    pivots = (
        ", ".join(
            f"{pivot.pivot_type.value}: {pivot.value}"
            for pivot in profile.deterministic_pivots[:8]
        )
        or "none"
    )
    gaps = ", ".join(gap.field_key for gap in profile.gaps[:8]) or "none"
    return f"""<div class="row"><strong>{escape(profile.normalized_piid)}</strong><span>Scenario: {escape(profile.scenario.value.replace("_", " ").title())} - Profile: {escape(profile.id)}</span><span>Award baseline: {escape(baseline.recipient_name or "recipient unknown")} - {escape(baseline.awarding_agency_name or "agency unknown")} - {escape(_money_label(baseline.award_amount))}</span><span>Burn posture: net obligations {escape(_money_label(burn.net_obligations))} - transactions {burn.transaction_count} - completeness {escape(burn.completeness)}</span><span>Vehicle context: {escape(vehicle.linkage_confidence)} - parent {escape(vehicle.parent_idv or vehicle.parent_generated_internal_id or "none")}</span><span>Deterministic pivots: {escape(pivots)}</span><span>Gaps: {escape(gaps)}</span><span>Provenance: {escape(profile.provenance.source_capability_id)} - {escape(profile.provenance.source_tool_name)} - {escape(profile.provenance.source_package)} {escape(profile.provenance.source_package_version)}</span><div class="row-list"><div class="row"><strong>Recommended enrichments</strong>{routes}</div><div class="row"><strong>PIID review candidates</strong>{candidates}</div><div class="row"><strong>Deferred artifact actions</strong><span>Draft report - Deferred until Artifact Renderer work exists.</span><span>Export XLSX - Deferred until Artifact Renderer work exists.</span><span>Export DOCX - Deferred until Artifact Renderer work exists.</span><span>Prepare visual briefing - Deferred until Artifact Renderer work exists.</span><div class="action-strip" aria-label="Deferred PIID artifact actions"><button class="action-button secondary" type="button" disabled>Draft report</button><button class="action-button secondary" type="button" disabled>Export XLSX</button><button class="action-button secondary" type="button" disabled>Export DOCX</button><button class="action-button secondary" type="button" disabled>Prepare visual briefing</button></div></div></div></div>"""


def _render_piid_enrichment_route(route: PiidEnrichmentRoute) -> str:
    fields = ", ".join(route.source_fields)
    return f"""<span>{escape(route.title)} - {escape(route.target_capability)} - {escape(fields)} - downstream review required</span>"""


def _render_piid_review_candidate(candidate: PiidReviewCandidate) -> str:
    state = candidate.review_state.value.replace("_", " ").title()
    trusted_state = (
        "trusted output written"
        if candidate.trusted_output_written
        else "trusted output not written"
    )
    workflow = candidate.target_workflow.replace("_", " ").title()
    return f"""<span>{escape(candidate.title)} - {escape(workflow)} - Review State: {escape(state)} - {escape(trusted_state)}</span>"""


def _render_sam_gov_enrichment_profiles_panel(
    profiles: list[SamGovEnrichmentProfile],
    live_ready: bool,
) -> str:
    readiness = (
        "Live readiness: SAM.gov API key configured"
        if live_ready
        else "Live readiness: missing SAM.gov API key"
    )
    readiness_class = "green" if live_ready else "amber"
    if not profiles:
        rows = """<div class="row"><strong>No SAM.gov profiles yet</strong><span>Create one through POST /api/federal-data/sam-gov/enrichment-profiles with an input_pivot.</span><span>Page render reads persisted profiles only and does not start upstream MCP processes.</span></div>"""
    else:
        rows = "".join(
            _render_sam_gov_enrichment_profile_row(profile) for profile in profiles[-3:]
        )
    return f"""<section class="panel" id="sam-gov-enrichment-profiles" aria-labelledby="sam-gov-enrichment-profiles-heading">
      <div class="panel-heading"><h2 id="sam-gov-enrichment-profiles-heading">SAM.gov Enrichment Profiles</h2><span class="status-chip {readiness_class}">{len(profiles)} persisted</span></div>
    <div class="row-list">
        <div class="row"><strong>Entity Record, Known Opportunity, Opportunity Discovery, and Attachment Intake lanes</strong><span>{escape(readiness)}</span><span>User-triggered POST actions use live SAM.gov when configured; this panel reads saved profiles only.</span></div>
      {rows}
      </div>
    </section>"""


def render_sam_gov_enrichment_profile_shell(
    settings: RuntimeSettings,
    profile_id: str,
    *,
    workspace_root: Path | None = None,
) -> str:
    root = workspace_root or Path.cwd()
    store = SamGovProfileStore(
        _resolve_runtime_path(root, settings.ariadne_sam_gov_profiles_dir)
    )
    profile = store.read(profile_id)
    live_ready = "SAM_GOV_API_KEY" in settings.federal_data_env
    summary = build_sam_gov_command_surface_summary(profile, live_ready=live_ready)
    readiness = (
        "Live readiness: SAM.gov API key configured"
        if live_ready
        else "Live readiness: missing SAM.gov API key"
    )
    fake_note = (
        "Fake adapter test data is not live SAM.gov source success."
        if "fake adapter test" in summary.source_mode_labels
        else "Live SAM.gov data still requires reviewer acceptance before trusted writes."
    )
    lane_rows = "".join(
        _render_sam_gov_command_lane_state(lane) for lane in summary.lane_states
    )
    review_rows = "".join(
        _render_sam_gov_review_candidate(candidate)
        for candidate in profile.review_candidates
    )
    attachment_rows = _render_sam_gov_attachment_command_rows(profile)
    deferral_rows = "".join(
        f"""<div class="row"><strong>{escape(_sam_gov_deferral_label(deferral))}</strong><span>Visible deferral; no implementation is invoked from this command surface.</span></div>"""
        for deferral in summary.explicit_deferrals
    )
    source_modes = ", ".join(summary.source_mode_labels) or "not started"
    workflows = (
        ", ".join(
            _sam_gov_workflow_label(workflow)
            for workflow in summary.review_summary.target_workflows
        )
        or "none"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SAM.gov Enrichment Profile Command Surface</title>
    <style>
        :root {{ color-scheme: dark; --bg: #071018; --surface: #0f172a; --surface-strong: #111c31; --edge: #334155; --edge-soft: #243244; --text: #f8fafc; --muted: #b6c4d6; --quiet: #8292a8; --cyan: #22d3ee; --green: #22c55e; --amber: #fbbf24; --focus: #fbbf24; }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; min-height: 100dvh; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--text); }}
        a {{ color: inherit; }}
        a:focus-visible, button:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
        .main {{ width: min(100% - 32px, 1320px); margin: 0 auto; padding: 24px 0 48px; }}
        .topbar {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 14px; }}
        .back-link, .action-button {{ display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 10px 14px; border: 1px solid var(--cyan); border-radius: 8px; color: var(--cyan); background: rgba(34, 211, 238, 0.1); text-decoration: none; font: inherit; font-weight: 900; }}
        .action-button {{ cursor: not-allowed; opacity: 0.74; }}
        h1 {{ margin: 0; font-size: 1.8rem; line-height: 1.12; letter-spacing: 0; }}
        h2 {{ margin: 0; font-size: 1.05rem; line-height: 1.25; letter-spacing: 0; }}
        p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
        .eyebrow {{ margin: 0 0 8px; color: var(--cyan); font-size: 0.78rem; font-weight: 800; letter-spacing: 0; text-transform: uppercase; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 14px 0; }}
        .metric, .panel, .row {{ border: 1px solid var(--edge); border-radius: 8px; background: var(--surface); }}
        .metric {{ min-height: 94px; padding: 14px; }}
        .metric span {{ display: block; color: var(--quiet); font-size: 0.78rem; font-weight: 800; text-transform: uppercase; }}
        .metric strong {{ display: block; margin-top: 8px; color: var(--text); }}
        .grid {{ display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr); gap: 14px; }}
        .panel {{ padding: 16px; }}
        .panel-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }}
        .row-list {{ display: grid; gap: 8px; }}
        .row {{ display: grid; gap: 6px; padding: 12px; background: var(--surface-strong); }}
        .row span {{ color: var(--muted); line-height: 1.45; }}
        .status-chip {{ display: inline-flex; align-items: center; min-height: 30px; padding: 5px 8px; border: 1px solid var(--edge); border-radius: 8px; color: var(--muted); background: #0b1220; font-size: 0.78rem; font-weight: 800; white-space: nowrap; }}
        .status-chip.green {{ border-color: rgba(34, 197, 94, 0.55); color: var(--green); background: rgba(34, 197, 94, 0.1); }}
        .status-chip.amber {{ border-color: rgba(251, 191, 36, 0.55); color: var(--amber); background: rgba(251, 191, 36, 0.1); }}
        .actions {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }}
        @media (max-width: 980px) {{ .summary, .grid {{ grid-template-columns: 1fr; }} .actions {{ grid-template-columns: 1fr; }} .topbar {{ align-items: flex-start; flex-direction: column; }} }}
    </style>
</head>
<body>
    <main class="main">
        <div class="topbar"><a class="back-link" href="/#sam-gov-enrichment-profiles">Back to Command Center</a><span class="status-chip {"green" if live_ready else "amber"}">{escape(readiness)}</span></div>
        <header>
            <p class="eyebrow">Saved SAM.gov profile</p>
            <h1>SAM.gov Enrichment Profile Command Surface</h1>
            <p>Profile {escape(profile.id)} keeps Entity Record, Known Opportunity, Opportunity Discovery, and Attachment Intake lanes together for review. Page render reads saved state only.</p>
        </header>
        <section class="summary" aria-label="SAM.gov command surface summary">
            <div class="metric"><span>Source modes</span><strong>{escape(source_modes)}</strong></div>
            <div class="metric"><span>Review candidates</span><strong>{summary.review_summary.candidate_count}</strong></div>
            <div class="metric"><span>Document Intake links</span><strong>{len(summary.linked_document_intake_record_ids)}</strong></div>
            <div class="metric"><span>Trusted writes</span><strong>Trusted writes: none</strong></div>
        </section>
        <div class="grid">
            <section class="panel" aria-labelledby="profile-source-heading">
                <div class="panel-heading"><h2 id="profile-source-heading">Source And Readiness</h2><span class="status-chip {"green" if live_ready else "amber"}">{escape(readiness)}</span></div>
                <div class="row-list">
                    <div class="row"><strong>{escape(fake_note)}</strong><span>{escape(summary.no_auto_trusted_writes_message)}</span></div>
                    <div class="row"><strong>Review target workflows</strong><span>{escape(workflows)}</span></div>
                </div>
            </section>
            <section class="panel" aria-labelledby="lane-heading">
                <div class="panel-heading"><h2 id="lane-heading">Four-Lane Workflow</h2><span class="status-chip amber">review gated</span></div>
                <div class="row-list">{lane_rows}</div>
            </section>
            <section class="panel" aria-labelledby="attachment-heading">
                <div class="panel-heading"><h2 id="attachment-heading">Attachment And Document Intake State</h2><span class="status-chip amber">explicit approval only</span></div>
                <div class="row-list">{attachment_rows}</div>
            </section>
            <section class="panel" aria-labelledby="candidate-heading">
                <div class="panel-heading"><h2 id="candidate-heading">Review Candidates</h2><span class="status-chip amber">no trusted writes</span></div>
                <div class="row-list"><div class="row"><strong>Trusted writes: none</strong><span>{escape(summary.review_summary.review_gate_message)}</span><div class="actions"><button class="action-button" type="button" disabled>Accept Evidence Store</button><button class="action-button" type="button" disabled>Promote Briefing Packet</button><button class="action-button" type="button" disabled>Route Follow-up</button></div></div><div class="row"><strong>Candidate destinations</strong>{review_rows}</div></div>
            </section>
            <section class="panel" aria-labelledby="deferral-heading">
                <div class="panel-heading"><h2 id="deferral-heading">Explicit Deferrals</h2><span class="status-chip amber">visible</span></div>
                <div class="row-list">{deferral_rows}</div>
            </section>
            <section class="panel" aria-labelledby="json-heading">
                <div class="panel-heading"><h2 id="json-heading">API Surface</h2><span class="status-chip green">saved</span></div>
                <div class="row-list"><div class="row"><strong>Profile JSON</strong><span>/api/federal-data/sam-gov/enrichment-profiles/{escape(profile.id)}</span></div><div class="row"><strong>Command summary JSON</strong><span>/api/federal-data/sam-gov/enrichment-profiles/{escape(profile.id)}/command-surface</span></div></div>
            </section>
        </div>
    </main>
</body>
</html>"""


def _render_sam_gov_command_lane_state(lane) -> str:
    source_mode = lane.source_mode.replace("_", " ") if lane.source_mode else "none"
    limitations = "; ".join(lane.source_limitations) or "none"
    return f"""<div class="row"><strong>{escape(lane.lane_name)}</strong><span>Status: {escape(lane.status.replace("_", " "))}</span><span>Primary: {escape(lane.primary_label)}</span><span>Source mode: {escape(source_mode)} - Source limitations: {escape(limitations)}</span></div>"""


def _render_sam_gov_attachment_command_rows(profile: SamGovEnrichmentProfile) -> str:
    if (
        profile.attachment_intake_lane is None
        or not profile.attachment_intake_lane.attachments
    ):
        return """<div class="row"><strong>No official attachments</strong><span>Attachment Intake waits for official SAM.gov resource links.</span></div>"""
    rows = []
    for attachment in profile.attachment_intake_lane.attachments:
        status = attachment.download_status.value.replace("_", " ")
        intake = attachment.intake_record_id or "not routed to Document Intake"
        source = (
            attachment.source_title
            or attachment.source_solicitation_number
            or "unknown source notice"
        )
        rows.append(
            f"""<div class="row"><strong>{escape(attachment.title)}</strong><span>{escape(source)} - {escape(status)}</span><span>Document Intake record: {escape(intake)}</span><span>{escape(attachment.filename or attachment.url)}</span></div>"""
        )
    return "".join(rows)


def _sam_gov_workflow_label(workflow: str) -> str:
    return {
        "evidence_store": "Evidence Store",
        "living_briefing_packet": "Living Briefing Packet",
        "capture_action_plan": "Capture Action Plan",
        "risk_register": "Risk Register",
        "call_plan": "Call Plan",
        "document_intake": "Document Intake",
        "web_enrichment_support": "Web Enrichment Support",
    }.get(workflow, workflow.replace("_", " ").title())


def _sam_gov_deferral_label(deferral: str) -> str:
    return deferral.removesuffix(".").replace(
        "Firecrawl/Web Enrichment Support implementation deferred",
        "Firecrawl/Web Enrichment Support deferred",
    )


def _render_sam_gov_enrichment_profile_row(
    profile: SamGovEnrichmentProfile,
) -> str:
    lane_rows = []
    if profile.entity_lane is not None:
        lane = profile.entity_lane
        match = lane.matches[0] if lane.matches else None
        match_label = (
            match.legal_business_name or match.uei or "no official entity match"
            if match is not None
            else "no official entity match"
        )
        source_mode = lane.provenance.source_mode.value.replace("_", " ")
        limitations = "; ".join(lane.source_limitations) or "none"
        lane_rows.append(
            f"""<div class="row"><strong>Entity Record lane</strong><span>Entity status: {escape(lane.lookup_status.value.replace("_", " "))}</span><span>Entity match: {escape(match_label)}</span><span>Source mode: {escape(source_mode)} - Tool: {escape(lane.provenance.source_tool_name)}</span><span>Source limitations: {escape(limitations)}</span></div>"""
        )
    if profile.known_opportunity_lane is not None:
        lane = profile.known_opportunity_lane
        record = lane.records[0] if lane.records else None
        record_label = (
            record.title
            or record.solicitation_number
            or record.notice_id
            or "no official opportunity match"
            if record is not None
            else "no official opportunity match"
        )
        notice_label = (
            record.notice_type if record is not None and record.notice_type else "none"
        )
        source_mode = lane.provenance.source_mode.value.replace("_", " ")
        limitations = "; ".join(lane.source_limitations) or "none"
        lane_rows.append(
            f"""<div class="row"><strong>Known Opportunity lane</strong><span>Lookup status: {escape(lane.lookup_status.value.replace("_", " "))} - Pivot: {escape(lane.normalized_pivot)}</span><span>Top notice: {escape(record_label)} - {escape(notice_label)}</span><span>Source mode: {escape(source_mode)} - Tool: {escape(lane.provenance.source_tool_name)}</span><span>Source limitations: {escape(limitations)}</span></div>"""
        )
    if profile.opportunity_discovery_lane is not None:
        lane = profile.opportunity_discovery_lane
        record = lane.records[0] if lane.records else None
        record_label = (
            record.title
            or record.solicitation_number
            or record.notice_id
            or "no official opportunity match"
            if record is not None
            else "no official opportunity match"
        )
        notice_label = (
            record.notice_type if record is not None and record.notice_type else "none"
        )
        confidence = (
            f"{record.match_confidence:.2f}" if record is not None else "unknown"
        )
        source_mode = lane.provenance.source_mode.value.replace("_", " ")
        limitations = "; ".join(lane.source_limitations) or "none"
        lane_rows.append(
            f"""<div class="row"><strong>Opportunity Discovery lane</strong><span>Discovery status: {escape(lane.discovery_status.value.replace("_", " "))} - Records: {len(lane.records)}</span><span>Top notice: {escape(record_label)} - {escape(notice_label)} - confidence {escape(confidence)}</span><span>Source mode: {escape(source_mode)} - Tool: {escape(lane.provenance.source_tool_name)}</span><span>Source limitations: {escape(limitations)}</span></div>"""
        )
    if profile.attachment_intake_lane is not None:
        lane = profile.attachment_intake_lane
        attachment = lane.attachments[0] if lane.attachments else None
        attachment_label = (
            attachment.title if attachment is not None else "no official attachments"
        )
        attachment_status = (
            attachment.download_status.value.replace("_", " ")
            if attachment is not None
            else "none"
        )
        intake_label = (
            attachment.intake_record_id
            if attachment is not None and attachment.intake_record_id
            else "not routed to Document Intake"
        )
        source_mode = lane.provenance.source_mode.value.replace("_", " ")
        limitations = "; ".join(lane.source_limitations) or "none"
        lane_rows.append(
            f"""<div class="row"><strong>Attachment Intake lane</strong><span>Attachments: {len(lane.attachments)} - First: {escape(attachment_label)}</span><span>Download state: {escape(attachment_status)} - Document Intake: {escape(intake_label)}</span><span>Source mode: {escape(source_mode)} - Tool: {escape(lane.provenance.source_tool_name)}</span><span>Source limitations: {escape(limitations)}</span></div>"""
        )
    if not lane_rows:
        lane_rows.append(
            """<div class="row"><strong>No SAM.gov lane started</strong><span>Create an entity or opportunity discovery profile through the API.</span></div>"""
        )
    candidates = "".join(
        _render_sam_gov_review_candidate(candidate)
        for candidate in profile.review_candidates[:8]
    )
    return f"""<div class="row"><strong>{escape(profile.normalized_pivot)}</strong><span>Profile: {escape(profile.id)}</span><a class="link-row" href="/federal-data/sam-gov/enrichment-profiles/{escape(profile.id)}">Open profile command surface</a><div class="row-list">{"".join(lane_rows)}<div class="row"><strong>SAM.gov review candidates</strong>{candidates}</div></div></div>"""


def _render_sam_gov_review_candidate(candidate: SamGovReviewCandidate) -> str:
    state = candidate.review_state.value.replace("_", " ").title()
    trusted_state = (
        "trusted output written"
        if candidate.trusted_output_written
        else "trusted output not written"
    )
    workflow = candidate.target_workflow.replace("_", " ").title()
    return f"""<span>{escape(candidate.title)} - {escape(workflow)} - Review State: {escape(state)} - {escape(trusted_state)}</span>"""


def _money_label(amount: float | None) -> str:
    if amount is None:
        return "amount unavailable"
    return f"${amount:,.2f}"


def _render_document_intake_draft_parts_panel(
    drafts: list[CaptureIntelligenceDraft],
    accepted_links: list[AcceptedDocumentEvidenceLink],
) -> str:
    if drafts:
        rows = "".join(
            _render_document_intake_draft_part_row(draft, piece, accepted_links)
            for draft in drafts
            for piece in draft.intelligence_pieces[:6]
        )
    else:
        rows = """<div class="row"><strong>No document-derived draft parts</strong><span>Create an Extraction Bundle from generic source material to queue document-derived review parts.</span></div>"""

    piece_count = sum(len(draft.intelligence_pieces) for draft in drafts)
    return f"""<section class="panel" id="document-draft-parts" aria-labelledby="document-draft-parts-heading">
      <div class="panel-heading"><h2 id="document-draft-parts-heading">Document-Derived Draft Parts</h2><span class="status-chip amber">{piece_count} review parts</span></div>
      <div class="row-list">
        <div class="row"><strong>Extraction review surface</strong><span>Document-derived parts stay separate from manual Quick Capture input. Trusted writes still require reviewer action.</span></div>
        {rows}
      </div>
    </section>"""


def _render_document_intake_draft_part_row(
    draft,
    piece,
    accepted_links: list[AcceptedDocumentEvidenceLink],
) -> str:
    label = piece.part_type.value.replace("_", " ").title()
    skill_chain = " -> ".join(piece.suggested_skill_chain) or "needs capability match"
    source_spans = ", ".join(piece.source_span_ids) or "none"
    recommendation = piece.recommendation or "Review before promotion."
    accepted_link = _accepted_document_evidence_link_for_piece(
        piece,
        accepted_links,
    )
    accepted_status = _render_document_intake_evidence_status(accepted_link)
    accept_button = (
        '<button class="action-button green" type="button" disabled>'
        "Accepted as Evidence</button>"
        if accepted_link is not None
        else '<button class="action-button" type="button">Accept as Evidence</button>'
    )
    return f"""<div class="row"><strong>{escape(label)}</strong><span>{escape(piece.content)}</span><span>Recommended Route: {escape(piece.recommended_route.replace("_", " "))}</span><span>Suggested Skill Chain: {escape(skill_chain)}</span><span>Recommendation: {escape(recommendation)}</span><span>Document Bundle: {escape(draft.extraction_bundle_id or "none")} - Intake Record: {escape(piece.source_intake_record_id or draft.extraction_document_id or "none")}</span><span>Source spans: {escape(source_spans)}</span>{accepted_status}<div class="action-strip" aria-label="{escape(label)} document actions">{accept_button}<button class="action-button secondary" type="button">Recommend Route</button><button class="action-button secondary" type="button">Plan Skill Chain</button><button class="action-button danger" type="button">Discard Piece</button></div></div>"""


def _accepted_document_evidence_link_for_piece(
    piece,
    accepted_links: list[AcceptedDocumentEvidenceLink],
) -> AcceptedDocumentEvidenceLink | None:
    piece_span_ids = set(piece.source_span_ids)
    for link in accepted_links:
        if link.draft_part_id == piece.id:
            return link
        if (
            link.extraction_bundle_id == piece.source_extraction_bundle_id
            and piece_span_ids.intersection(link.source_span_ids)
        ):
            return link
    return None


def _render_document_intake_evidence_status(
    accepted_link: AcceptedDocumentEvidenceLink | None,
) -> str:
    if accepted_link is None:
        return "<span>Evidence status: pending reviewer acceptance</span>"
    return f"""<span>Evidence accepted - {escape(accepted_link.evidence_id)}</span><span>Reviewer rationale: {escape(accepted_link.reviewer_rationale)}</span>"""


def _render_document_intake_capture_candidates_panel(
    candidates: list[DocumentIntakeCaptureCandidate],
) -> str:
    pending_candidates = [
        candidate for candidate in candidates if not candidate.trusted_output_written
    ]
    if pending_candidates:
        rows = "".join(
            _render_document_intake_capture_candidate_row(candidate)
            for candidate in pending_candidates[:8]
        )
    else:
        rows = """<div class="row"><strong>No suggested next actions</strong><span>Create document-derived draft parts to queue review-gated downstream candidates.</span></div>"""
    return f"""<section class="panel" id="document-capture-candidates" aria-labelledby="document-capture-candidates-heading">
      <div class="panel-heading"><h2 id="document-capture-candidates-heading">Review-Gated Capture Candidates</h2><span class="status-chip amber">{len(pending_candidates)} pending</span></div>
      <div class="row-list">
        <div class="row"><strong>Suggested next actions</strong><span>Trusted outputs still require acceptance; these candidates are prepared for review, routing, or dismissal.</span></div>
        {rows}
      </div>
    </section>"""


def _render_document_intake_capture_candidate_row(
    candidate: DocumentIntakeCaptureCandidate,
) -> str:
    workflow_label = _capture_candidate_workflow_label(candidate.target_workflow)
    confidence = (
        f"{candidate.confidence:.2f}" if candidate.confidence is not None else "unknown"
    )
    skill_chain = (
        " -> ".join(candidate.suggested_skill_chain) or "needs capability match"
    )
    source_spans = ", ".join(candidate.source_span_ids)
    return f"""<div class="row"><strong>{escape(workflow_label)}</strong><span>{escape(candidate.title)}</span><span>{escape(candidate.content)}</span><span>Review State: {escape(candidate.review_state.value.replace("_", " ").title())} - Confidence: {escape(confidence)}</span><span>Target workflow: {escape(workflow_label)} - Suggested Skill Chain: {escape(skill_chain)}</span><span>Trace: draft {escape(candidate.source_draft_id)} - part {escape(candidate.source_draft_part_id)} - bundle {escape(candidate.source_extraction_bundle_id)}</span><span>Source spans: {escape(source_spans)}</span><span>{escape(candidate.recommendation)}</span><div class="action-strip" aria-label="{escape(workflow_label)} candidate actions"><button class="action-button" type="button">Review Candidate</button><button class="action-button secondary" type="button">Route Candidate</button><button class="action-button secondary" type="button">Plan Skill Chain</button><button class="action-button danger" type="button">Ignore Candidate</button></div></div>"""


def _capture_candidate_workflow_label(target_workflow: str) -> str:
    labels = {
        "capture_action_plan": "Capture Action Plan",
        "living_briefing_packet": "Living Briefing Packet",
        "risk_register": "Risk Register",
        "call_plan": "Call Plan",
    }
    return labels.get(target_workflow, target_workflow.replace("_", " ").title())


def _render_knowledge_note_projections_panel(
    projections: list[KnowledgeNoteProjection],
) -> str:
    if projections:
        rows = "".join(
            _render_knowledge_note_projection_row(projection)
            for projection in projections[:8]
        )
    else:
        rows = """<div class="row"><strong>No note projections generated</strong><span>Accept document-derived evidence, then generate a one-way note projection for lightweight browsing.</span></div>"""
    return f"""<section class="panel" id="knowledge-note-projections" aria-labelledby="knowledge-note-projections-heading">
    <div class="panel-heading"><h2 id="knowledge-note-projections-heading">Knowledge Note Projections</h2><span class="status-chip cyan">{len(projections)} notes</span></div>
    <div class="row-list">
    <div class="row"><strong>Human-readable one-way notes</strong><span>Structured Ariadne records remain source of truth. Cannot overwrite structured knowledge.</span></div>
    {rows}
    </div>
  </section>"""


def _render_knowledge_note_projection_row(
    projection: KnowledgeNoteProjection,
) -> str:
    evidence_ids = ", ".join(projection.evidence_ids)
    source_spans = ", ".join(projection.source_span_ids)
    projection_href = (
        "/api/document-intake/knowledge-note-projections?bundle_id="
        f"{projection.source_extraction_bundle_id}"
    )
    return f"""<div class="row"><strong>{escape(projection.title)}</strong><span>{escape(projection.summary)}</span><span>Evidence: {escape(evidence_ids)}</span><span>Trace: intake {escape(projection.source_intake_record_id)} - bundle {escape(projection.source_extraction_bundle_id)} - source spans {escape(source_spans)}</span><span>Structured Ariadne records remain source of truth; projection markdown is a readable mirror only.</span><div class="action-strip" aria-label="{escape(projection.title)} projection actions"><a class="action-button" href="{escape(projection_href)}">Open Markdown Projection</a><button class="action-button secondary" type="button" disabled>Cannot overwrite structured knowledge</button></div></div>"""


def _render_capture_intelligence_draft_panel(draft) -> str:
    if draft is None:
        return ""

    return f"""<section class="panel" id="capture-intelligence-draft" aria-labelledby="capture-intelligence-draft-heading">
      <div class="panel-heading"><h2 id="capture-intelligence-draft-heading">Capture Intelligence Draft</h2><span class="status-chip amber">{escape(draft.status.value.replace("_", " ").title())}</span></div>
      <div class="row-list">
        <div class="row"><strong>Polished Capture</strong><span>{escape(draft.polished_capture)}</span></div>
        <div class="row"><strong>Trace/Admin Raw Note</strong><span>{escape(draft.raw_source_content)}</span></div>
        <div class="row"><strong>Local Admin Model Assist</strong><span>{escape(draft.local_admin_model_assist_status.replace("_", " ").title())} - {escape(draft.inference_source.value.replace("_", " ").title())}</span></div>
        <div class="row"><strong>Per-Piece Intelligence Review</strong><span>Each draft part gets its own review, route, skill-chain, and discard controls. Trusted writes require reviewer action.</span></div>
        {_render_intelligence_piece_rows(draft)}
        <div class="row"><strong>Assumptions</strong><span>{_render_inline_items(draft.assumptions)}</span></div>
        <div class="row"><strong>Confidence Notes</strong><span>{_render_inline_items(draft.confidence_notes)}</span></div>
        <div class="row"><strong>Gaps</strong><span>{_render_inline_items(draft.gaps)}</span></div>
        <div class="row"><strong>{len(draft.reference_influences)} reference influences</strong><span>No trusted opportunity knowledge updated.</span></div>
      </div>
    </section>"""


def _render_intelligence_piece_rows(draft) -> str:
    return "".join(
        _render_intelligence_piece_row(piece) for piece in draft.intelligence_pieces
    )


def _render_intelligence_piece_row(piece) -> str:
    skill_chain = " -> ".join(piece.suggested_skill_chain) or "needs capability match"
    label = piece.part_type.value.replace("_", " ").title()
    return f"""<div class="row"><strong>{escape(label)}</strong><span>{escape(piece.content)}</span><span>Recommended Route: {escape(piece.recommended_route.replace("_", " "))}</span><span>Suggested Skill Chain: {escape(skill_chain)}</span><div class="action-strip" aria-label="{escape(label)} actions"><button class="action-button" type="button">Accept as Evidence</button><button class="action-button secondary" type="button">Recommend Route</button><button class="action-button secondary" type="button">Plan Skill Chain</button><button class="action-button danger" type="button">Discard Piece</button></div></div>"""


def _render_inline_items(items: tuple[str, ...]) -> str:
    return "<br>".join(escape(item) for item in items)


def _render_accepted_promotions_panel(
    accepted_evidence,
    action_item,
    packet_answer,
    discarded_output,
) -> str:
    evidence = accepted_evidence.evidence
    evidence_id = evidence.id if evidence is not None else "unwritten"
    evidence_rationale = " | ".join(evidence.rationale if evidence is not None else ())
    return f"""<section class="panel" id="accepted-promotions" aria-labelledby="accepted-promotions-heading">
    <div class="panel-heading"><h2 id="accepted-promotions-heading">Accepted Draft Promotions</h2><span class="status-chip green">Review Status: accepted</span></div>
    <div class="row-list">
    <div class="row"><strong>Accepted Evidence</strong><span>{escape(evidence.content if evidence is not None else "No evidence created")}</span><span>Saved content: polished capture, not raw note.</span><span>Trace: raw {escape(accepted_evidence.raw_item_id)} - draft {escape(accepted_evidence.draft_id or "none")} - evidence {escape(evidence_id)}</span><span>Draft Rationale: {escape(evidence_rationale)}</span></div>
    <div class="row"><strong>Accepted Action</strong><span>{escape(action_item.action)}</span><span>Trace: raw {escape(action_item.source_raw_item_id or "none")} - draft {escape(action_item.source_draft_id or "none")} - part {escape(action_item.promoted_from_draft_part_id or "none")}</span><span>Evidence: {escape(", ".join(action_item.related_evidence_ids))}</span><span>Reviewer Rationale: {escape(action_item.rationale)}</span></div>
    <div class="row"><strong>Accepted Packet Update</strong><span>{escape(packet_answer.value or "")}</span><span>Trace: raw {escape(packet_answer.source_raw_item_id or "none")} - draft {escape(packet_answer.source_draft_id or "none")} - part {escape(packet_answer.promoted_from_draft_part_id or "none")}</span><span>Field: {escape(packet_answer.field_key)} - Confidence: {packet_answer.confidence}</span><span>Reviewer Rationale: {escape(packet_answer.provenance_note or "none")}</span></div>
    <div class="row"><strong>Discarded Output</strong><span>Trace: raw {escape(discarded_output.source_raw_item_id)} - draft {escape(discarded_output.source_draft_id or "none")} - part {escape(discarded_output.draft_part_id)}</span><span>{escape(discarded_output.discard_reason or "No discard reason")}</span></div>
    </div>
  </section>"""


def _render_packet_panel(packet, coverage_view) -> str:
    customer_context = next(
        section
        for section in coverage_view.sections
        if section.section is CanonicalPacketSection.CUSTOMER_CONTEXT
    )
    return f"""<section class="panel" id="packet" aria-labelledby="packet-heading">
      <div class="panel-heading"><h2 id="packet-heading">Living Briefing Packet</h2><span class="status-chip green">{escape(packet.readiness.value.replace("_", " ").title())}</span></div>
      <div class="row-list">
        <div class="row"><strong>Coverage View</strong><span>{len(coverage_view.sections)} canonical sections tracked.</span></div>
        <div class="row"><strong>Customer Context</strong><span>{escape(customer_context.gap_summary or "No active gap noted.")}</span></div>
      </div>
      <a class="link-row" href="/packets/review">Open packet review</a>
    </section>"""


def _render_action_plan_panel(action_view) -> str:
    rows = "".join(
        f"""<div class="row"><strong>{escape(item.action)}</strong><span>{escape(item.rationale)}</span></div>"""
        for item in action_view.items[:4]
    )
    return f"""<section class="panel" id="action-plan" aria-labelledby="action-plan-heading">
      <div class="panel-heading"><h2 id="action-plan-heading">Capture Action Plan</h2><span class="status-chip amber">{len(action_view.items)} open</span></div>
      <div class="row-list">{rows}</div>
    </section>"""


def _render_capability_panel(
    catalog: CapabilityCatalog,
    capability_runs: tuple[CapabilityRun, ...],
) -> str:
    entries = "".join(
        f"""<div class="row"><strong>{escape(entry.name)}</strong><span>{escape(entry.capability_type.value)} - {escape(entry.validation_status.value)} - {escape(entry.source_path)}</span></div>"""
        for entry in catalog.entries[:4]
    )
    review_rows = _render_capability_outputs_needing_review(capability_runs)
    return f"""<section class="panel" id="capability-studio" aria-labelledby="capability-heading">
      <div class="panel-heading"><h2 id="capability-heading">Capability Studio</h2><span class="status-chip cyan">{len(capability_runs)} runs</span></div>
      <div class="row-list">
        <div class="row"><strong>Run Capability Catalog Validation</strong><span>Create a deterministic Capability Run and open the Studio detail without model, network, or external API dependency.</span><form action="/capability-studio/actions/catalog-validation" method="post"><button class="action-button" type="submit">Run Capability Catalog Validation</button></form></div>
        <div class="row"><strong>Capability Run Outputs Needing Review</strong><span>{_capability_outputs_needing_review_count(capability_runs)} outputs need review before trusted downstream use.</span></div>
        {review_rows}
        {entries}
      </div>
            <a class="link-row" href="/capability-studio">Open Capability Studio</a>
            <a class="link-row" href="/api/capabilities/catalog">Open catalog API</a>
    </section>"""


def _capability_outputs_needing_review_count(
    capability_runs: tuple[CapabilityRun, ...],
) -> int:
    return sum(
        output.review_state is CapabilityRunOutputReviewState.PENDING
        for run in capability_runs
        for output in run.outputs
    )


def _render_capability_outputs_needing_review(
    capability_runs: tuple[CapabilityRun, ...],
) -> str:
    rows: list[str] = []
    for run in capability_runs:
        for output in run.outputs:
            if output.review_state is not CapabilityRunOutputReviewState.PENDING:
                continue
            rows.append(
                f"""<div class="row"><strong>{escape(output.title)}</strong><span>Run: {escape(run.run_id)} - Status: {escape(run.status.value)} - Review: {escape(output.review_state.value)}</span><span>{escape(output.summary)}</span><span>Autonomy: {escape(output.autonomy_recommendation.value)} - Destination: {escape(output.recommended_destination or "review queue")}</span><a class="link-row" href="/capability-studio/runs/{escape(run.run_id)}">Open in Capability Studio</a></div>"""
            )
    if not rows:
        return """<div class="row"><strong>No Capability Run Outputs needing review</strong><span>Run validation from this panel to create the first reviewable output.</span></div>"""
    return "".join(rows[:4])
