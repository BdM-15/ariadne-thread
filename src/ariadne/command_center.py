from __future__ import annotations

from html import escape
from pathlib import Path

from ariadne.capabilities import CapabilityCatalog
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
from ariadne.packets import (
    CanonicalPacketSection,
    EvidenceStatus,
)
from ariadne.quick_capture import CaptureIntelligenceDraft
from ariadne.quick_capture_demo import build_quick_capture_demo_thread
from ariadne.reference_wiki import ReferenceWikiInfluence


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
    document_intake_store = DocumentIntakeStore(
        _resolve_runtime_path(root, settings.ariadne_document_intake_dir)
    )
    document_intake_records = document_intake_store.list()
    accepted_document_evidence_links = (
        document_intake_store.list_accepted_evidence_links()
    )
    document_intake_drafts = [
        create_capture_intelligence_draft_from_extraction_bundle(bundle)
        for bundle in document_intake_store.list_extraction_bundles()
    ]
    document_intake_capture_candidates = document_intake_store.list_capture_candidates()
    document_intake_knowledge_note_projections = (
        document_intake_store.list_knowledge_note_projections()
    )
    document_intake_adapter_declarations = list_document_intake_adapter_declarations()
    accepted_evidence = demo.accepted_evidence
    accepted_action = demo.accepted_action
    accepted_packet_answer = demo.accepted_packet_answer
    discarded_output = demo.discarded_output
    action_view = demo.action_view
    reference_influences = demo.reference_influences
    coverage_view = demo.coverage_view
    catalog = demo.catalog

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
    .row {{
      display: grid;
      gap: 6px;
      padding: 12px;
      border: 1px solid var(--edge-soft);
      border-radius: 8px;
      background: var(--surface-strong);
    }}
    .row strong {{ color: var(--text); }}
    .row span {{ color: var(--muted); line-height: 1.45; }}
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
        <a href="#quick-capture">Quick Capture <small>review</small></a>
        <a href="#document-intake">Document Intake <small>{len(document_intake_records)}</small></a>
        <a href="/packets/review">Living Briefing Packet <small>deck</small></a>
        <a href="#action-plan">Capture Action Plan <small>{len(action_view.items)}</small></a>
      </nav>
      <div class="advanced">
        <p class="advanced-label">Advanced / read-only</p>
        <nav class="nav" aria-label="Advanced surfaces">
          <a href="#capability-studio">Capability Studio <small>{len(catalog.entries)}</small></a>
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
        {_render_quick_capture_panel(quick_capture, capture_review, reference_influences, pasted_capture, pasted_review, uploaded_capture, uploaded_review, unsupported_upload.intake_candidate)}
        {_render_document_intake_queue_panel(document_intake_records, accepted_document_evidence_links)}
        {_render_document_intake_capabilities_panel(document_intake_adapter_declarations)}
        {_render_document_intake_draft_parts_panel(document_intake_drafts, accepted_document_evidence_links)}
        {_render_document_intake_capture_candidates_panel(document_intake_capture_candidates)}
        {_render_knowledge_note_projections_panel(document_intake_knowledge_note_projections)}
        {_render_capture_intelligence_draft_panel(capture_review.intelligence_draft)}
        {_render_accepted_promotions_panel(accepted_evidence, accepted_action, accepted_packet_answer, discarded_output)}
        {_render_packet_panel(packet, coverage_view)}
        {_render_action_plan_panel(action_view)}
        {_render_capability_panel(catalog)}
      </div>
    </main>
  </div>
</body>
</html>"""


def _resolve_runtime_path(workspace_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return workspace_root / path


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


def _render_capability_panel(catalog: CapabilityCatalog) -> str:
    entries = "".join(
        f"""<div class="row"><strong>{escape(entry.name)}</strong><span>{escape(entry.capability_type.value)} - {escape(entry.validation_status.value)} - {escape(entry.source_path)}</span></div>"""
        for entry in catalog.entries[:4]
    )
    return f"""<section class="panel" id="capability-studio" aria-labelledby="capability-heading">
      <div class="panel-heading"><h2 id="capability-heading">Capability Studio</h2><span class="status-chip cyan">Advanced / read-only</span></div>
      <div class="row-list">{entries}</div>
      <a class="link-row" href="/api/capabilities/catalog">Open catalog API</a>
    </section>"""
