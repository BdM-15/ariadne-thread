from __future__ import annotations

from dataclasses import dataclass
from html import escape

from ariadne.opportunities import (
    EntryContext,
    EntryReason,
    LifecycleState,
    create_opportunity,
)
from ariadne.packets import (
    BriefingView,
    CanonicalPacketSection,
    CoverageView,
    EvidenceStatus,
    LivingBriefingPacket,
    PacketReadiness,
    build_briefing_view,
    build_coverage_view,
    create_living_briefing_packet,
    update_packet_readiness,
    update_packet_section_coverage,
)


@dataclass(frozen=True)
class PacketReviewSlide:
    number: int
    title: str
    role: str
    timing: str
    required_for: tuple[str, ...]
    optional_for: tuple[str, ...]
    section: CanonicalPacketSection | None
    data_slots: tuple[str, ...]
    prose_slots: tuple[str, ...]


MILESTONE_STAGES = ("MS1", "MS2", "MS3", "MS4")

PACKET_REVIEW_SLIDES = (
    PacketReviewSlide(
        1,
        "Review Instructions",
        "Milestone rules and expectations",
        "Reference",
        MILESTONE_STAGES,
        (),
        None,
        (
            "Milestone purpose",
            "Required-slide markers",
            "Approval authority",
            "Presentation time",
        ),
        ("Decision-gate expectations", "Stage timing and briefer pattern"),
    ),
    PacketReviewSlide(
        2,
        "Milestone Cover",
        "Packet identity",
        "1 min",
        MILESTONE_STAGES,
        (),
        CanonicalPacketSection.OPPORTUNITY_OVERVIEW,
        (
            "Business unit",
            "Operating unit",
            "Opportunity name",
            "Milestone",
            "Date",
            "Prepared by",
            "Role",
        ),
        ("Review framing",),
    ),
    PacketReviewSlide(
        3,
        "Safety Moment",
        "Opening ritual",
        "2 min",
        MILESTONE_STAGES,
        (),
        None,
        ("Safety title", "Media/visual", "Readiness flag"),
        ("Safety message",),
    ),
    PacketReviewSlide(
        4,
        "Opportunity Synopsis",
        "Structured opportunity facts",
        "4 min",
        MILESTONE_STAGES,
        (),
        CanonicalPacketSection.OPPORTUNITY_OVERVIEW,
        (
            "CRM / Salesforce ID",
            "Prime name",
            "RFP release date",
            "Proposal due date",
            "Total contract value",
            "pWin",
            "Primary scope",
            "Competition",
        ),
        ("Special considerations", "Scope summary"),
    ),
    PacketReviewSlide(
        5,
        "Opportunity BLUF",
        "Leadership decision summary",
        "4 min",
        MILESTONE_STAGES,
        (),
        CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
        ("Strategic fit", "Capture progress", "Funding status", "Recommendation"),
        (
            "What you need to know",
            "What it takes to win",
            "Proceed / hold / no-bid rationale",
        ),
    ),
    PacketReviewSlide(
        6,
        "Pursuit Team",
        "Resourcing and ownership",
        "3 min",
        ("MS1", "MS2", "MS3"),
        ("MS4",),
        CanonicalPacketSection.SOLUTION_STRATEGY,
        (
            "Capture manager",
            "Operations lead",
            "Pricing lead",
            "Contracts lead",
            "Proposal manager",
            "B&P request",
        ),
        ("Resource gaps", "Non-US person participation notes"),
    ),
    PacketReviewSlide(
        7,
        "Evaluation Methodology",
        "How the customer will score",
        "4 min",
        ("MS2", "MS3", "MS4"),
        ("MS1",),
        CanonicalPacketSection.REQUIREMENTS_AND_SCOPE,
        (
            "Document date",
            "Evaluation factors",
            "Ratings",
            "Basis of evaluated price",
            "Relative importance",
        ),
        ("Customer award trends", "Evaluation implications"),
    ),
    PacketReviewSlide(
        8,
        "Opportunity SWOT",
        "Position and risk synthesis",
        "3 min",
        ("MS1", "MS2", "MS3"),
        ("MS4",),
        CanonicalPacketSection.COMPETITIVE_POSITION,
        ("Strengths", "Weaknesses", "Opportunities", "Threats"),
        ("Evidence-backed capture interpretation",),
    ),
    PacketReviewSlide(
        9,
        "Path to Blue",
        "Pursuit maturity tracker",
        "4 min",
        ("MS1", "MS2", "MS3"),
        ("MS4",),
        CanonicalPacketSection.SOLUTION_STRATEGY,
        (
            "Strategic fit",
            "Leadership highlights",
            "Win strategy",
            "Previous status",
            "Current status",
        ),
        ("Status updates", "Next steps and actions"),
    ),
    PacketReviewSlide(
        10,
        "Pricing Strategy",
        "Price-to-win posture",
        "4 min",
        ("MS2", "MS3", "MS4"),
        ("MS1",),
        CanonicalPacketSection.PRICE_TO_WIN,
        (
            "Pricing variables",
            "Customer pricing guidance",
            "Competitive position",
            "Price-to-win view",
        ),
        ("Pricing strategy summary", "Pricing risks and opportunities"),
    ),
    PacketReviewSlide(
        11,
        "Proposed Pricing Summary",
        "Price output by stage",
        "4 min",
        ("MS3", "MS4"),
        ("MS1", "MS2"),
        CanonicalPacketSection.PRICE_TO_WIN,
        (
            "Evaluated price",
            "Major cost elements",
            "Contract periods",
            "Price-to-win comparison",
        ),
        ("Pricing maturity explanation",),
    ),
    PacketReviewSlide(
        12,
        "Execution Business Case",
        "Financial outcome model",
        "4 min",
        ("MS2", "MS3", "MS4"),
        ("MS1",),
        CanonicalPacketSection.PRICE_TO_WIN,
        (
            "Revenue",
            "Estimated cost",
            "Profit/fee",
            "Price",
            "Operating margin",
            "Cashflow",
        ),
        ("Conservative and optimistic case notes",),
    ),
    PacketReviewSlide(
        13,
        "High Risk Elements",
        "Proposal and execution risk",
        "4 min",
        ("MS3", "MS4"),
        ("MS1", "MS2"),
        CanonicalPacketSection.RISKS_AND_GAPS,
        ("Proposal risks", "Execution risks", "Risk response", "Owner", "Severity"),
        ("Accepted risk rationale", "Mitigation narrative"),
    ),
    PacketReviewSlide(
        14,
        "Action Plan",
        "Dated work to close gaps",
        "3 min",
        MILESTONE_STAGES,
        (),
        CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
        ("Action", "Responsible party", "Due date", "Status", "Related gap"),
        ("Why this action matters",),
    ),
    PacketReviewSlide(
        15,
        "Questions",
        "Meeting close",
        "1 min",
        MILESTONE_STAGES,
        (),
        None,
        ("Questions enabled", "Legal notice"),
        ("Closing prompt",),
    ),
    PacketReviewSlide(
        16,
        "Promotion Criteria",
        "Gate readiness overview",
        "3 min",
        MILESTONE_STAGES,
        (),
        CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
        ("Criteria by milestone", "Completion status", "Briefer pattern"),
        ("Promotion rationale",),
    ),
    PacketReviewSlide(
        17,
        "MS1 / MS2 Approval Decision",
        "Early-stage approval answers",
        "4 min",
        ("MS1", "MS2"),
        (),
        CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
        (
            "Qualification answers",
            "Pursuit/no-pursuit answers",
            "OCI status",
            "B&P estimate",
        ),
        ("Concise approval-answer prose",),
    ),
    PacketReviewSlide(
        18,
        "MS3 / MS4 Approval Decision",
        "Bid and pricing approval answers",
        "4 min",
        ("MS3", "MS4"),
        (),
        CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
        ("Bid/no-bid answers", "Pricing approval answers", "Execution-risk acceptance"),
        ("Concise approval-answer prose",),
    ),
)


def create_demo_packet() -> LivingBriefingPacket:
    opportunity = create_opportunity(
        name="AFLCMC recompete support",
        entry_context=EntryContext(
            reason=EntryReason.INCUMBENT_RECOMPETE,
            starting_lifecycle_state=LifecycleState.PURSUING,
            rationale="Existing contract is approaching its recompete window.",
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
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.COMPETITIVE_POSITION,
        evidence_status=EvidenceStatus.GAP,
        gap_summary="Need competitor field and incumbent performance evidence.",
    )
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.SOLUTION_STRATEGY,
        evidence_status=EvidenceStatus.ASSUMPTION,
        evidence_ids=["ev_solution_note"],
        gap_summary="Solution themes are inferred and need technical validation.",
    )
    update_packet_section_coverage(
        packet,
        section=CanonicalPacketSection.RECOMMENDATION_AND_NEXT_ACTIONS,
        evidence_status=EvidenceStatus.PARTIAL,
        evidence_ids=["ev_capture_notes"],
        gap_summary="Need dated next actions and gate recommendation confidence.",
    )
    return packet


def build_demo_packet_briefing_view() -> BriefingView:
    return build_briefing_view(create_demo_packet())


def build_demo_packet_coverage_view() -> CoverageView:
    return build_coverage_view(create_demo_packet())


def render_demo_packet_review_shell(stage: str = "MS2", slide: int = 4) -> str:
    return render_packet_review_shell(
        create_demo_packet(), stage=stage, selected_slide_number=slide
    )


def render_packet_review_shell(
    packet: LivingBriefingPacket,
    *,
    stage: str = "MS2",
    selected_slide_number: int = 4,
) -> str:
    active_stage = _normalize_stage(stage)
    selected_slide = _find_slide(selected_slide_number, active_stage)
    briefing_view = build_briefing_view(packet)
    coverage_view = build_coverage_view(packet)
    stage_tabs = _render_stage_tabs(active_stage, selected_slide.number)
    slide_nav = _render_slide_nav(active_stage, selected_slide.number)
    deck_canvas = _render_slide_canvas(packet, selected_slide, active_stage)
    evidence_inspector = _render_evidence_inspector(
        packet, selected_slide, active_stage
    )
    coverage_matrix = _render_coverage_matrix(coverage_view)
    readiness_summary = _render_readiness_summary(
        packet, briefing_view, coverage_view, active_stage
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Living Briefing Packet</title>
  <style>
    :root {{
      color-scheme: dark;
      --app-bg: #080b12;
      --surface: #101722;
      --surface-strong: #162131;
      --surface-soft: #1c2a3b;
      --edge: #314156;
      --edge-soft: #223044;
      --text: #f4f8fb;
      --muted: #aab9c8;
      --quiet: #7f91a3;
      --navy: #0b2545;
      --blue: #116aa6;
      --cyan: #2bd4e8;
      --teal: #1f9f8b;
      --magenta: #d95bd8;
      --green: #47d18c;
      --amber: #f5c451;
      --red: #ff6b76;
      --paper: #f7fbff;
      --paper-ink: #0a1b2d;
      --paper-muted: #51657a;
      --paper-rule: #bfd6e8;
      --focus: #f5c451;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      min-height: 100dvh;
      font-family: Arial, Helvetica, sans-serif;
      background:
        linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px) 0 0 / 48px 48px,
        linear-gradient(0deg, rgba(255,255,255,0.03) 1px, transparent 1px) 0 0 / 48px 48px,
        var(--app-bg);
      color: var(--text);
      overflow-x: hidden;
    }}
    a {{ color: inherit; }}
    a:focus-visible,
    button:focus-visible {{
      outline: 3px solid var(--focus);
      outline-offset: 3px;
    }}
    .skip-link {{
      position: absolute;
      left: 16px;
      top: -80px;
      z-index: 10;
      min-height: 44px;
      padding: 12px 16px;
      border-radius: 8px;
      background: var(--focus);
      color: #081018;
      font-weight: 700;
    }}
    .skip-link:focus {{ top: 16px; }}
    main {{
      width: min(1480px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 24px 0 56px;
    }}
    .app-header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 16px;
    }}
    h1 {{
      margin: 6px 0 10px;
      font-size: 2.25rem;
      line-height: 1.08;
      letter-spacing: 0;
    }}
    h2 {{ margin: 0; font-size: 1.05rem; line-height: 1.25; letter-spacing: 0; }}
    h3 {{ margin: 0; font-size: 0.95rem; line-height: 1.3; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.6; }}
    .eyebrow {{ color: var(--cyan); font-size: 0.82rem; font-weight: 700; text-transform: uppercase; }}
    .header-copy {{ max-width: 760px; }}
    .header-actions {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
    .action-link,
    .stage-tab,
    .slide-link {{
      touch-action: manipulation;
      transition: background-color 180ms ease, border-color 180ms ease, color 180ms ease;
    }}
    .action-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 10px 14px;
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: var(--surface);
      color: var(--text);
      text-decoration: none;
      font-weight: 700;
    }}
    .action-link:hover {{ border-color: var(--cyan); color: var(--cyan); }}
    .stage-bar,
    .summary-grid,
    .workspace,
    .coverage-panel {{ margin-top: 16px; }}
    .stage-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      padding: 10px;
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: rgba(16, 23, 34, 0.92);
    }}
    .stage-label {{ color: var(--muted); font-size: 0.9rem; font-weight: 700; margin-right: 4px; }}
    .stage-tab {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      min-width: 64px;
      padding: 10px 14px;
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: var(--surface-strong);
      color: var(--muted);
      text-decoration: none;
      font-weight: 800;
    }}
    .stage-tab.active {{
      border-color: var(--cyan);
      background: #102d3a;
      color: var(--text);
    }}
    .stage-tab:hover {{ border-color: var(--cyan); color: var(--text); }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .metric,
    .rail,
    .deck-panel,
    .inspector,
    .coverage-panel {{
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: rgba(16, 23, 34, 0.94);
    }}
    .metric {{ min-height: 96px; padding: 14px; }}
    .metric span {{ display: block; color: var(--quiet); font-size: 0.82rem; }}
    .metric strong {{ display: block; margin-top: 8px; color: var(--text); font-size: 1.15rem; }}
    .metric .green {{ color: var(--green); }}
    .metric .amber {{ color: var(--amber); }}
    .metric .cyan {{ color: var(--cyan); }}
    .workspace {{
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr) 340px;
      gap: 14px;
      align-items: start;
    }}
    .rail,
    .deck-panel,
    .inspector {{ padding: 14px; }}
    .panel-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }}
    .count-pill,
    .status-chip,
    .marker {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      border-radius: 8px;
      border: 1px solid var(--edge);
      padding: 5px 8px;
      font-size: 0.78rem;
      font-weight: 800;
      white-space: nowrap;
    }}
    .count-pill {{ color: var(--muted); background: var(--surface-strong); }}
    .slide-list {{
      display: grid;
      gap: 8px;
      max-height: 760px;
      overflow: auto;
      padding-right: 2px;
    }}
    .slide-link {{
      display: grid;
      grid-template-columns: 42px minmax(0, 1fr);
      gap: 10px;
      min-height: 64px;
      padding: 10px;
      border: 1px solid var(--edge-soft);
      border-radius: 8px;
      background: var(--surface-strong);
      color: var(--text);
      text-decoration: none;
    }}
    .slide-link:hover,
    .slide-link.active {{ border-color: var(--cyan); background: #102a39; }}
    .slide-link.optional {{ color: var(--muted); }}
    .slide-number {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 38px;
      height: 38px;
      border-radius: 8px;
      background: var(--navy);
      color: var(--cyan);
      font-weight: 900;
      font-variant-numeric: tabular-nums;
    }}
    .slide-title {{ display: block; font-weight: 800; line-height: 1.25; }}
    .slide-meta {{ display: block; margin-top: 4px; color: var(--quiet); font-size: 0.82rem; line-height: 1.35; }}
    .deck-toolbar {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 12px;
    }}
    .deck-caption {{ color: var(--muted); font-size: 0.9rem; }}
    .slide-stage-status {{ display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }}
    .slide-frame {{
      aspect-ratio: 16 / 9;
      min-height: 420px;
      border-radius: 8px;
      border: 1px solid #9ebbd4;
      background: var(--paper);
      color: var(--paper-ink);
      padding: 22px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      box-shadow: 0 18px 44px rgba(0, 0, 0, 0.35);
    }}
    .slide-header {{ border-bottom: 3px solid var(--blue); padding-bottom: 10px; }}
    .slide-kicker {{ color: var(--paper-muted); font-size: 0.78rem; font-weight: 800; text-transform: uppercase; }}
    .slide-header h2 {{ margin-top: 4px; color: var(--navy); font-size: 1.65rem; line-height: 1.1; }}
    .slide-body {{
      display: grid;
      grid-template-columns: minmax(0, 1.12fr) minmax(0, 0.88fr);
      gap: 14px;
      padding: 18px 0;
      min-height: 0;
    }}
    .slide-band {{
      min-height: 30px;
      padding: 7px 10px;
      border-radius: 6px 6px 0 0;
      background: var(--navy);
      color: #fff;
      font-size: 0.82rem;
      font-weight: 900;
    }}
    .slide-band.teal {{ background: var(--teal); }}
    .slot-grid,
    .prose-list {{
      border: 1px solid var(--paper-rule);
      border-top: 0;
      border-radius: 0 0 6px 6px;
      background: #eaf4fb;
    }}
    .slot-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .slot {{ min-height: 46px; padding: 8px 10px; border-top: 1px solid #d3e4ef; color: var(--paper-ink); }}
    .slot:nth-child(odd) {{ border-right: 1px solid #d3e4ef; }}
    .slot-label {{ display: block; color: #446175; font-size: 0.72rem; font-weight: 800; }}
    .slot-value {{ display: block; margin-top: 4px; color: #0c2438; font-size: 0.88rem; font-weight: 800; }}
    .prose-list {{ list-style: none; padding: 0; margin: 0; }}
    .prose-list li {{ min-height: 46px; padding: 10px; border-top: 1px solid #d3e4ef; color: #19334a; line-height: 1.35; }}
    .slide-footer {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto auto;
      gap: 12px;
      align-items: center;
      min-height: 38px;
      padding: 7px 10px;
      border-radius: 6px;
      background: var(--navy);
      color: #fff;
      font-size: 0.78rem;
      font-weight: 800;
    }}
    .footer-markers {{ display: inline-flex; gap: 5px; align-items: center; }}
    .marker {{ min-width: 30px; min-height: 28px; padding: 4px 7px; }}
    .marker.required {{ border-color: var(--cyan); color: var(--cyan); background: rgba(43, 212, 232, 0.12); }}
    .marker.optional {{ border-color: var(--edge); color: var(--quiet); background: rgba(255,255,255,0.04); }}
    .status-chip.supported,
    .status-chip.answered {{ border-color: rgba(71, 209, 140, 0.62); color: var(--green); background: rgba(71, 209, 140, 0.12); }}
    .status-chip.partially_supported,
    .status-chip.partial {{ border-color: rgba(245, 196, 81, 0.62); color: var(--amber); background: rgba(245, 196, 81, 0.12); }}
    .status-chip.needs_evidence,
    .status-chip.gap {{ border-color: rgba(255, 107, 118, 0.62); color: var(--red); background: rgba(255, 107, 118, 0.12); }}
    .status-chip.assumption {{ border-color: rgba(217, 91, 216, 0.62); color: var(--magenta); background: rgba(217, 91, 216, 0.12); }}
    .inspector-grid {{ display: grid; gap: 10px; }}
    .inspector-row {{
      border: 1px solid var(--edge-soft);
      border-radius: 8px;
      background: var(--surface-strong);
      padding: 12px;
    }}
    .inspector-row span {{ display: block; color: var(--quiet); font-size: 0.78rem; font-weight: 800; text-transform: uppercase; }}
    .inspector-row strong,
    .inspector-row p {{ margin-top: 6px; display: block; color: var(--text); }}
    .tag-list {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
    .tag {{
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 5px 8px;
      border: 1px solid var(--edge);
      border-radius: 8px;
      color: var(--muted);
      background: #0d1420;
      font-size: 0.78rem;
      font-weight: 700;
    }}
    .coverage-panel {{ padding: 16px; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th:nth-child(1), td:nth-child(1) {{ width: 24%; }}
    th:nth-child(2), td:nth-child(2) {{ width: 18%; }}
    th:nth-child(3), td:nth-child(3) {{ width: 22%; }}
    th:nth-child(4), td:nth-child(4) {{ width: 36%; }}
    th, td {{ border-bottom: 1px solid var(--edge); padding: 12px; text-align: left; vertical-align: top; }}
    th {{ color: var(--text); font-weight: 800; }}
    td {{ color: var(--muted); line-height: 1.5; overflow-wrap: anywhere; }}
    @media (max-width: 1180px) {{
      .summary-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .workspace {{ grid-template-columns: 260px minmax(0, 1fr); }}
      .inspector {{ grid-column: 1 / -1; }}
      .inspector-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 820px) {{
      main {{ width: min(100% - 24px, 760px); padding-top: 18px; }}
      .app-header {{ display: block; }}
      .header-actions {{ justify-content: flex-start; margin-top: 12px; }}
      h1 {{ font-size: 1.8rem; }}
      .summary-grid,
      .workspace,
      .slide-body,
      .inspector-grid {{ grid-template-columns: 1fr; }}
      .slide-list {{ max-height: none; }}
      .slide-frame {{ min-height: auto; padding: 14px; }}
      .slide-header h2 {{ font-size: 1.25rem; }}
      .slot-grid {{ grid-template-columns: 1fr; }}
      .slot:nth-child(odd) {{ border-right: 0; }}
      .slide-footer {{ grid-template-columns: 1fr; }}
      table {{ min-width: 760px; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      .action-link,
      .stage-tab,
      .slide-link {{ transition: none; }}
    }}
  </style>
</head>
<body>
  <a class=\"skip-link\" href=\"#packet-workspace\">Skip to packet workspace</a>
  <main id=\"main\">
    <header class=\"app-header\">
      <div class=\"header-copy\">
        <p class=\"eyebrow\">Living Briefing Packet</p>
        <h1>{escape(packet.opportunity_name)}</h1>
        <p>Briefing View for the milestone packet, shaped like a deck while keeping evidence coverage available beside the slide.</p>
      </div>
      <nav class=\"header-actions\" aria-label=\"Packet review links\">
        <a class=\"action-link\" href=\"/\">Runtime</a>
        <a class=\"action-link\" href=\"/api/packets/review/coverage\">Coverage JSON</a>
      </nav>
    </header>
    <nav class=\"stage-bar\" aria-label=\"Milestone stage\">
      <span class=\"stage-label\">Milestone</span>
      {stage_tabs}
    </nav>
    {readiness_summary}
    <div class=\"workspace\" id=\"packet-workspace\">
      <aside class=\"rail\" aria-labelledby=\"slide-nav-heading\">
        <div class=\"panel-heading\">
          <h2 id=\"slide-nav-heading\">Slide Navigator</h2>
          <span class=\"count-pill\">18 slides</span>
        </div>
        <div class=\"slide-list\">{slide_nav}</div>
      </aside>
      {deck_canvas}
      {evidence_inspector}
    </div>
    {coverage_matrix}
  </main>
</body>
</html>"""


def _normalize_stage(stage: str) -> str:
    normalized_stage = stage.upper()
    if normalized_stage in MILESTONE_STAGES:
        return normalized_stage
    return "MS2"


def _find_slide(selected_slide_number: int, active_stage: str) -> PacketReviewSlide:
    for slide in PACKET_REVIEW_SLIDES:
        if slide.number == selected_slide_number:
            return slide
    for slide in PACKET_REVIEW_SLIDES:
        if active_stage in slide.required_for:
            return slide
    return PACKET_REVIEW_SLIDES[0]


def _render_stage_tabs(active_stage: str, selected_slide_number: int) -> str:
    links = []
    for milestone_stage in MILESTONE_STAGES:
        active_class = " active" if milestone_stage == active_stage else ""
        current_attr = ' aria-current="page"' if milestone_stage == active_stage else ""
        links.append(
            f"""<a class="stage-tab{active_class}" href="/packets/review?stage={milestone_stage}&amp;slide={selected_slide_number}"{current_attr}>{milestone_stage}</a>"""
        )
    return "\n".join(links)


def _render_slide_nav(active_stage: str, selected_slide_number: int) -> str:
    links = []
    for slide in PACKET_REVIEW_SLIDES:
        active_class = " active" if slide.number == selected_slide_number else ""
        optional_class = " optional" if active_stage not in slide.required_for else ""
        current_attr = (
            ' aria-current="page"' if slide.number == selected_slide_number else ""
        )
        requirement = _slide_requirement_label(slide, active_stage)
        links.append(
            f"""<a class="slide-link{active_class}{optional_class}" href="/packets/review?stage={active_stage}&amp;slide={slide.number}"{current_attr}>
              <span class="slide-number">{slide.number:02d}</span>
              <span>
                <span class="slide-title">{escape(slide.title)}</span>
                <span class="slide-meta">{escape(requirement)} - {escape(slide.timing)}</span>
              </span>
            </a>"""
        )
    return "\n".join(links)


def _render_readiness_summary(
    packet: LivingBriefingPacket,
    briefing_view: BriefingView,
    coverage_view: CoverageView,
    active_stage: str,
) -> str:
    supported_sections = sum(
        section.status.value == "supported" for section in briefing_view.sections
    )
    open_coverage_items = sum(
        section.evidence_status is not EvidenceStatus.ANSWERED
        for section in coverage_view.sections
    )
    required_slide_count = sum(
        active_stage in slide.required_for for slide in PACKET_REVIEW_SLIDES
    )
    return f"""<section class="summary-grid" aria-label="Packet readiness summary">
      <div class="metric"><span>Packet readiness</span><strong class="green">{_label(packet.readiness.value)}</strong></div>
      <div class="metric"><span>Active milestone</span><strong class="cyan">{active_stage}</strong></div>
      <div class="metric"><span>Required slides</span><strong>{required_slide_count}</strong></div>
      <div class="metric"><span>Open evidence items</span><strong class="amber">{open_coverage_items} of {len(coverage_view.sections)}</strong></div>
      <div class="metric"><span>Supported sections</span><strong>{supported_sections} of {len(briefing_view.sections)}</strong></div>
      <div class="metric"><span>Review surface</span><strong>Deck workspace</strong></div>
      <div class="metric"><span>Slide skin</span><strong>16:9 preview</strong></div>
      <div class="metric"><span>Evidence model</span><strong>Traceable fields</strong></div>
    </section>"""


def _render_slide_canvas(
    packet: LivingBriefingPacket,
    slide: PacketReviewSlide,
    active_stage: str,
) -> str:
    status_label, status_class = _slide_evidence_status(packet, slide)
    requirement_label = _slide_requirement_label(slide, active_stage)
    data_slots = "\n".join(
        f"""<div class="slot"><span class="slot-label">Data</span><span class="slot-value">{escape(slot)}</span></div>"""
        for slot in slide.data_slots
    )
    prose_slots = "\n".join(f"<li>{escape(slot)}</li>" for slot in slide.prose_slots)
    markers = _render_stage_markers(slide)
    return f"""<section class="deck-panel" aria-labelledby="deck-preview-heading">
      <div class="deck-toolbar">
        <div>
          <h2 id="deck-preview-heading">Briefing View</h2>
          <p class="deck-caption">Slide {slide.number:02d} - {escape(slide.role)}</p>
        </div>
        <div class="slide-stage-status" aria-label="Selected slide status">
          <span class="status-chip {status_class}">{escape(status_label)}</span>
          <span class="status-chip partial">{escape(requirement_label)}</span>
        </div>
      </div>
      <article class="slide-frame" aria-label="Selected slide deck preview">
        <header class="slide-header">
          <p class="slide-kicker">Milestone Decision Briefing - {active_stage}</p>
          <h2>{slide.number}. {escape(slide.title)}</h2>
        </header>
        <div class="slide-body">
          <section aria-label="Visible data fields">
            <div class="slide-band">Visible Data Elements</div>
            <div class="slot-grid">{data_slots}</div>
          </section>
          <section aria-label="Prose and decision outputs">
            <div class="slide-band teal">Prose / Decision Outputs</div>
            <ul class="prose-list">{prose_slots}</ul>
          </section>
        </div>
        <footer class="slide-footer">
          <span>Living packet preview - Evidence stays under the hood</span>
          <span class="footer-markers" aria-label="Milestone markers">{markers}</span>
          <span>{slide.number:02d}</span>
        </footer>
      </article>
    </section>"""


def _render_evidence_inspector(
    packet: LivingBriefingPacket,
    slide: PacketReviewSlide,
    active_stage: str,
) -> str:
    status_label, status_class = _slide_evidence_status(packet, slide)
    state = packet.sections.get(slide.section) if slide.section else None
    section_label = (
        _label(slide.section.value) if slide.section else "Template / Manual Slide"
    )
    evidence_ids = state.evidence_ids if state else ()
    gap_summary = state.gap_summary if state else "Tracked outside the evidence matrix."
    return f"""<aside class="inspector" aria-labelledby="inspector-heading">
      <div class="panel-heading">
        <h2 id="inspector-heading">Evidence Inspector</h2>
        <span class="status-chip {status_class}">{escape(status_label)}</span>
      </div>
      <div class="inspector-grid">
        <div class="inspector-row">
          <span>Selected slide</span>
          <strong>{slide.number:02d}. {escape(slide.title)}</strong>
        </div>
        <div class="inspector-row">
          <span>Canonical section</span>
          <strong>{section_label}</strong>
        </div>
        <div class="inspector-row">
          <span>Applicability</span>
          <strong>{escape(_slide_requirement_label(slide, active_stage))}</strong>
          <div class="tag-list">{_render_stage_tags(slide)}</div>
        </div>
        <div class="inspector-row">
          <span>Evidence sources</span>
          <strong>{_format_evidence_ids(evidence_ids)}</strong>
        </div>
        <div class="inspector-row">
          <span>Gap / assumption</span>
          <p>{escape(gap_summary or "No active gap noted.")}</p>
        </div>
        <div class="inspector-row">
          <span>Tracked data slots</span>
          <div class="tag-list">{_render_tags(slide.data_slots)}</div>
        </div>
        <div class="inspector-row">
          <span>Tracked prose slots</span>
          <div class="tag-list">{_render_tags(slide.prose_slots)}</div>
        </div>
      </div>
    </aside>"""


def _render_coverage_matrix(coverage_view: CoverageView) -> str:
    coverage_rows = "\n".join(
        f"""<tr>
          <th scope="row">{_label(section.section.value)}</th>
          <td><span class="status-chip {section.evidence_status.value}">{_label(section.evidence_status.value)}</span></td>
          <td>{_format_evidence_ids(section.evidence_ids)}</td>
          <td>{escape(section.gap_summary or "No active gap noted.")}</td>
        </tr>"""
        for section in coverage_view.sections
    )
    return f"""<section class="coverage-panel" aria-labelledby="coverage-heading">
      <div class="panel-heading">
        <h2 id="coverage-heading">Coverage View</h2>
        <span class="count-pill">{len(coverage_view.sections)} canonical sections</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th scope="col">Section</th><th scope="col">Evidence</th><th scope="col">Sources</th><th scope="col">Gap / Assumption</th></tr>
          </thead>
          <tbody>{coverage_rows}</tbody>
        </table>
      </div>
    </section>"""


def _slide_evidence_status(
    packet: LivingBriefingPacket,
    slide: PacketReviewSlide,
) -> tuple[str, str]:
    if slide.section is None:
        return "Manual / static", "partial"
    state = packet.sections[slide.section]
    return _label(state.evidence_status.value), state.evidence_status.value


def _slide_requirement_label(slide: PacketReviewSlide, active_stage: str) -> str:
    if active_stage in slide.required_for:
        return f"Required for {active_stage}"
    if active_stage in slide.optional_for:
        return f"Optional for {active_stage}"
    return f"Not marked for {active_stage}"


def _render_stage_markers(slide: PacketReviewSlide) -> str:
    return "\n".join(
        f'<span class="marker {"required" if milestone_stage in slide.required_for else "optional"}">{milestone_stage}</span>'
        for milestone_stage in MILESTONE_STAGES
    )


def _render_stage_tags(slide: PacketReviewSlide) -> str:
    labels = [f"Required: {', '.join(slide.required_for)}"]
    if slide.optional_for:
        labels.append(f"Optional: {', '.join(slide.optional_for)}")
    return _render_tags(tuple(labels))


def _render_tags(values: tuple[str, ...]) -> str:
    if not values:
        return '<span class="tag">None yet</span>'
    return "\n".join(f'<span class="tag">{escape(value)}</span>' for value in values)


def _label(value: str) -> str:
    return escape(value.replace("_", " ").title())


def _format_evidence_ids(evidence_ids: tuple[str, ...]) -> str:
    if not evidence_ids:
        return "None yet"
    return escape(", ".join(evidence_ids))
