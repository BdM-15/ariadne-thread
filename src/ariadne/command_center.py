from __future__ import annotations

from html import escape
from pathlib import Path

from ariadne.action_plans import (
    add_packet_gap_actions,
    build_action_plan_view,
    create_capture_action_plan,
)
from ariadne.capabilities import CapabilityCatalog, discover_local_capability_catalog
from ariadne.config import RuntimeSettings
from ariadne.draft_promotion import (
    promote_action_candidate_to_plan_item,
    promote_packet_implication_to_field_answer,
)
from ariadne.document_intake import classify_uploaded_source_material
from ariadne.opportunities import (
    CoreCaptureWorkstream,
    EntryContext,
    EntryReason,
    LifecycleState,
    create_opportunity,
)
from ariadne.packets import (
    build_coverage_view,
    create_living_briefing_packet,
    update_packet_readiness,
    update_packet_section_coverage,
    CanonicalPacketSection,
    EvidenceStatus,
    PacketReadiness,
)
from ariadne.quick_capture import (
    CaptureIntelligenceDraftPartType,
    capture_pasted_text,
    capture_raw_item,
    capture_raw_item_from_upload,
    process_raw_capture_item,
)
from ariadne.reference_wiki import ReferenceWikiInfluence, load_reference_wiki


def render_command_center_shell(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> str:
    root = workspace_root or Path.cwd()
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
            missing_or_stale_workstreams={
                CoreCaptureWorkstream.CUSTOMER_INSIGHT,
                CoreCaptureWorkstream.COMPETITIVE_INTELLIGENCE,
            },
        ),
    )
    packet = create_living_briefing_packet(opportunity)
    update_packet_readiness(packet, PacketReadiness.DRAFT_READY)
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.OPPORTUNITY_OVERVIEW,
        evidence_status=EvidenceStatus.ANSWERED,
        evidence_ids=["ev_notice", "ev_contract_history"],
    )
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.CUSTOMER_CONTEXT,
        evidence_status=EvidenceStatus.PARTIAL,
        evidence_ids=["ev_customer_call"],
        gap_summary="Need validated customer pain and decision-maker map.",
    )
    quick_capture = capture_raw_item(
        "Customer said incumbent transition plan is weak. Need follow up with PM next week.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_customer_transition_note",
    )
    reference_wiki = load_reference_wiki(
        _reference_wiki_root(settings.ariadne_reference_wiki_dir, root)
    )
    capture_review = process_raw_capture_item(
        quick_capture,
        reference_wiki=reference_wiki,
    )
    pasted_capture = capture_pasted_text(
        "Customer pasted note says transition proof needs PM follow up.",
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_pasted_transition_note",
    )
    pasted_review = process_raw_capture_item(
        pasted_capture,
        reference_wiki=reference_wiki,
    )
    uploaded_source = classify_uploaded_source_material(
        filename="customer-call.md",
        mime_type="text/markdown",
        content=b"# Call note\n\nCustomer says transition risk needs packet gap.",
    )
    if uploaded_source.text is None:
        raise ValueError("demo uploaded source material was not readable")
    uploaded_capture = capture_raw_item_from_upload(
        uploaded_source.text,
        filename=uploaded_source.filename,
        mime_type=uploaded_source.mime_type,
        content_type=uploaded_source.content_type.value,
        byte_size=uploaded_source.byte_size,
        source_ref=uploaded_source.source_ref,
        warnings=uploaded_source.warnings,
        opportunity_id="opp-aflcmc-recompete",
        raw_item_id="raw_uploaded_customer_call",
    )
    uploaded_review = process_raw_capture_item(
        uploaded_capture,
        reference_wiki=reference_wiki,
    )
    unsupported_upload = classify_uploaded_source_material(
        filename="draft-rfp.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4\n...",
    )
    accepted_action = promote_action_candidate_to_plan_item(
        capture_review,
        draft_part_id=_draft_part_id_for_type(
            capture_review,
            CaptureIntelligenceDraftPartType.ACTION_CANDIDATE,
        ),
        reviewer_rationale="Reviewer accepted PM follow-up as next capture action.",
        evidence_ids=("ev_customer_call",),
    )
    accepted_packet_answer = promote_packet_implication_to_field_answer(
        capture_review,
        draft_part_id=_draft_part_id_for_type(
            capture_review,
            CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
        ),
        field_key="risks",
        reviewer_rationale="Reviewer accepted transition risk as packet update.",
        edited_value="Transition risk needs mitigation evidence before gate review.",
        evidence_ids=("ev_customer_call",),
        confidence=0.64,
    )
    action_plan = add_packet_gap_actions(
        create_capture_action_plan(opportunity),
        packet,
    )
    action_plan = action_plan.model_copy(
        update={"items": action_plan.items + (accepted_action,)}
    )
    action_view = build_action_plan_view(action_plan)
    reference_influences = capture_review.reference_influences
    coverage_view = build_coverage_view(packet)
    catalog = discover_local_capability_catalog(root)

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
        {_render_capture_intelligence_draft_panel(capture_review.intelligence_draft)}
        {_render_accepted_promotions_panel(accepted_action, accepted_packet_answer)}
        {_render_packet_panel(packet, coverage_view)}
        {_render_action_plan_panel(action_view)}
        {_render_capability_panel(catalog)}
      </div>
    </main>
  </div>
</body>
</html>"""


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
        for influence in reference_influences[:3]
    )
    pasted_metadata = pasted_raw_item.source_metadata
    uploaded_metadata = uploaded_raw_item.source_metadata
    candidate_status = (
        intake_candidate.status.value.replace("_", " ").title()
        if intake_candidate is not None
        else "Parser Required"
    )
    return f"""<section class="panel" id="quick-capture" aria-labelledby="quick-capture-heading">
      <div class="panel-heading"><h2 id="quick-capture-heading">Quick Capture</h2><span class="status-chip amber">Needs Review</span></div>
      <div class="row-list">
        <div class="row"><strong>{escape(raw_item.id)}</strong><span>{escape(raw_item.content)}</span></div>
        <div class="row"><strong>Pasted Text Intake</strong><span>{escape(pasted_metadata.source_type.value if pasted_metadata else "pasted_text")} - {len(pasted_review.proposals)} review proposals queued.</span></div>
        <div class="row"><strong>Text / Markdown Upload</strong><span>{escape(uploaded_metadata.filename if uploaded_metadata and uploaded_metadata.filename else "uploaded material")} - {escape(uploaded_metadata.content_type if uploaded_metadata and uploaded_metadata.content_type else "text")} - {len(uploaded_review.proposals)} review proposals queued.</span></div>
        <div class="row"><strong>Document Intake Candidate</strong><span>{escape(intake_candidate.filename if intake_candidate and intake_candidate.filename else "unsupported file")} - {escape(candidate_status)}</span></div>
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


def _render_capture_intelligence_draft_panel(draft) -> str:
    if draft is None:
        return ""

    return f"""<section class="panel" id="capture-intelligence-draft" aria-labelledby="capture-intelligence-draft-heading">
      <div class="panel-heading"><h2 id="capture-intelligence-draft-heading">Capture Intelligence Draft</h2><span class="status-chip amber">{escape(draft.status.value.replace("_", " ").title())}</span></div>
      <div class="row-list">
        <div class="row"><strong>Raw Source</strong><span>{escape(draft.raw_source_content)}</span></div>
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
    return "".join(_render_intelligence_piece_row(piece) for piece in draft.intelligence_pieces)


def _render_intelligence_piece_row(piece) -> str:
    skill_chain = " -> ".join(piece.suggested_skill_chain) or "needs capability match"
    label = piece.part_type.value.replace("_", " ").title()
    return f"""<div class="row"><strong>{escape(label)}</strong><span>{escape(piece.content)}</span><span>Recommended Route: {escape(piece.recommended_route.replace("_", " "))}</span><span>Suggested Skill Chain: {escape(skill_chain)}</span><div class="action-strip" aria-label="{escape(label)} actions"><button class="action-button" type="button">Accept as Evidence</button><button class="action-button secondary" type="button">Recommend Route</button><button class="action-button secondary" type="button">Plan Skill Chain</button><button class="action-button danger" type="button">Discard Piece</button></div></div>"""


def _render_inline_items(items: tuple[str, ...]) -> str:
    return "<br>".join(escape(item) for item in items)


def _render_accepted_promotions_panel(action_item, packet_answer) -> str:
    return f"""<section class="panel" id="accepted-promotions" aria-labelledby="accepted-promotions-heading">
    <div class="panel-heading"><h2 id="accepted-promotions-heading">Accepted Draft Promotions</h2><span class="status-chip green">Review Status: accepted</span></div>
    <div class="row-list">
    <div class="row"><strong>Accepted Action</strong><span>{escape(action_item.action)}</span><span>Evidence: {escape(", ".join(action_item.related_evidence_ids))}</span></div>
    <div class="row"><strong>Accepted Packet Update</strong><span>{escape(packet_answer.value or "")}</span><span>Field: {escape(packet_answer.field_key)} - Confidence: {packet_answer.confidence}</span></div>
    </div>
  </section>"""


def _draft_part_id_for_type(review, part_type: CaptureIntelligenceDraftPartType) -> str:
    if review.intelligence_draft is None:
        raise ValueError("capture review has no intelligence draft")
    for part in review.intelligence_draft.intelligence_pieces:
        if part.part_type is part_type:
            return part.id
    raise ValueError(f"capture review has no draft part for {part_type.value}")


def _reference_wiki_root(path: Path, workspace_root: Path) -> Path:
    if path.is_absolute():
        return path
    return workspace_root / path


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
