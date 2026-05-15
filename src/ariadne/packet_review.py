from __future__ import annotations

from html import escape

from ariadne.opportunities import EntryContext, EntryReason, LifecycleState, create_opportunity
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


def render_demo_packet_review_shell() -> str:
    return render_packet_review_shell(create_demo_packet())


def render_packet_review_shell(packet: LivingBriefingPacket) -> str:
    briefing_view = build_briefing_view(packet)
    coverage_view = build_coverage_view(packet)
    briefing_rows = "\n".join(
        f"""<li class=\"section-row\">
          <span>{_label(section.section.value)}</span>
          <strong>{_label(section.status.value)}</strong>
        </li>"""
        for section in briefing_view.sections
    )
    coverage_rows = "\n".join(
        f"""<tr>
          <th scope=\"row\">{_label(section.section.value)}</th>
          <td><span class=\"status {section.evidence_status.value}\">{_label(section.evidence_status.value)}</span></td>
          <td>{_format_evidence_ids(section.evidence_ids)}</td>
          <td>{escape(section.gap_summary or "No active gap noted.")}</td>
        </tr>"""
        for section in coverage_view.sections
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
      --bg: #08090d;
      --panel: #10131a;
      --panel-2: #151926;
      --edge: #273142;
      --text: #edf7ff;
      --muted: #9fb4c8;
      --cyan: #33e7ff;
      --magenta: #ff4fd8;
      --green: #7dffa7;
      --amber: #ffd166;
      --red: #ff6b7a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100dvh;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    main {{
      width: min(1280px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}
    a {{ color: var(--cyan); }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      border-bottom: 1px solid var(--edge);
      padding-bottom: 20px;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 4px 0 10px;
      font-size: clamp(2rem, 4vw, 4rem);
      line-height: 1;
      letter-spacing: 0;
    }}
    h2 {{ margin: 0 0 14px; font-size: 1.05rem; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.6; }}
    .eyebrow {{ color: var(--cyan); font-weight: 700; }}
    .readiness {{
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: var(--panel);
      padding: 14px 16px;
      min-width: 180px;
    }}
    .readiness span {{ display: block; color: var(--muted); font-size: 0.85rem; }}
    .readiness strong {{ display: block; margin-top: 8px; color: var(--green); }}
    .layout {{
      display: grid;
      gap: 16px;
      align-items: start;
    }}
    section {{
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: var(--panel);
      padding: 18px;
    }}
    .section-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px;
    }}
    .section-row {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      min-height: 48px;
      padding: 10px 12px;
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: var(--panel-2);
    }}
    .section-row span {{ color: var(--text); }}
    .section-row strong {{ color: var(--amber); font-size: 0.85rem; text-align: right; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th:nth-child(1), td:nth-child(1) {{ width: 24%; }}
    th:nth-child(2), td:nth-child(2) {{ width: 18%; }}
    th:nth-child(3), td:nth-child(3) {{ width: 24%; }}
    th:nth-child(4), td:nth-child(4) {{ width: 34%; }}
    th, td {{ border-bottom: 1px solid var(--edge); padding: 12px; text-align: left; vertical-align: top; }}
    th {{ color: var(--text); font-weight: 700; }}
    td {{ color: var(--muted); line-height: 1.5; overflow-wrap: anywhere; }}
    .status {{ font-weight: 700; }}
    .answered {{ color: var(--green); }}
    .partial {{ color: var(--amber); }}
    .gap {{ color: var(--red); }}
    .assumption {{ color: var(--magenta); }}
    @media (max-width: 860px) {{
      .topbar, .layout {{ display: block; }}
      .readiness {{ margin-top: 16px; }}
      section + section {{ margin-top: 16px; }}
      table {{ min-width: 720px; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class=\"topbar\">
      <div>
        <p class=\"eyebrow\">Living Briefing Packet</p>
        <h1>{escape(packet.opportunity_name)}</h1>
        <p>Review shape for canonical packet sections, decision briefing status, and evidence coverage.</p>
      </div>
      <aside class=\"readiness\" aria-label=\"Packet readiness\">
        <span>Packet readiness</span>
        <strong>{_label(packet.readiness.value)}</strong>
      </aside>
    </div>
    <div class=\"layout\">
      <section aria-labelledby=\"briefing-heading\">
        <h2 id=\"briefing-heading\">Briefing View</h2>
        <ul class=\"section-list\">{briefing_rows}</ul>
      </section>
      <section aria-labelledby=\"coverage-heading\">
        <h2 id=\"coverage-heading\">Coverage View</h2>
        <div class=\"table-wrap\">
          <table>
            <thead>
              <tr><th scope=\"col\">Section</th><th scope=\"col\">Evidence</th><th scope=\"col\">Sources</th><th scope=\"col\">Gap / Assumption</th></tr>
            </thead>
            <tbody>{coverage_rows}</tbody>
          </table>
        </div>
      </section>
    </div>
  </main>
</body>
</html>"""


def _label(value: str) -> str:
    return escape(value.replace("_", " ").title())


def _format_evidence_ids(evidence_ids: tuple[str, ...]) -> str:
    if not evidence_ids:
        return "None yet"
    return escape(", ".join(evidence_ids))