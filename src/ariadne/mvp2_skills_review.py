from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ariadne.capabilities import (
    CapabilityCatalogEntry,
    CapabilityStatus,
    discover_local_capability_catalog,
)
from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunOutputReviewState,
    CapabilityRunReviewDecisionType,
    CapabilityRunStore,
    record_capability_run_output_review,
)
from ariadne.config import RuntimeSettings
from ariadne.data_table_profiler import DataTableProfileRequest
from ariadne.improvement_proposals import (
    HermesImprovementProposal,
    ImprovementProposalKind,
    ImprovementProposalStore,
    propose_skill_improvement_from_capability_run,
)
from ariadne.opportunities import MilestoneGate
from ariadne.opportunity_activation import (
    OpportunityActivationCapabilityRoute,
    OpportunityActivationRun,
    OpportunityActivationRunStore,
    run_opportunity_activation,
)
from ariadne.packet_knowledge import build_default_packet_field_definitions
from ariadne.production_command_center import (
    AssistedRouteModelRoleContract,
    MVP2_MODEL_ROLE_CONTRACTS,
)


MVP2_REVIEW_OPPORTUNITY_ID = "opp-mvp2-skills-review"
MVP2_REVIEW_ROUTE_ID = "actroute_competition_data_table_profile_next_route_chain"
MVP2_REVIEW_ACTIVATION_RUN_ID = "actrun_mvp2_skills_review_demo"
MVP2_FOCUSED_SKILL_IDS = frozenset(
    {
        "data-table-profiler",
        "anomaly-route-recommender",
        "incumbent-award-history-brief",
        "compliance-spine-planner",
        "win-theme-synthesizer",
        "competitive-gap-route-hint",
        "subcontractor-assumption-list",
    }
)


class Mvp2CapabilityReviewCard(BaseModel):
    capability_id: str
    name: str
    capability_status: str
    capability_type: str
    validation_status: str
    review_destination: str
    quality_gate: str
    source_path: str
    next_enabling_action: str | None = None


class Mvp2RouteReviewCard(BaseModel):
    route_id: str
    field_key: str
    capability_id: str
    capability_type: str
    status: str
    approval_required: bool
    approval_gate: str | None
    review_destination: str
    invoked_run_id: str | None
    invoked_output_ids: tuple[str, ...]
    source_limitations: tuple[str, ...]
    trusted_downstream_writes: bool


class Mvp2ChainStageReviewCard(BaseModel):
    run_id: str
    stage_id: str
    capability_id: str
    status: str
    quality_gate_result: str
    review_destination: str
    produced_handoff: str
    input_refs: tuple[str, ...]
    gaps: tuple[str, ...]


class Mvp2ModelRoleReviewCard(BaseModel):
    model_role: str
    allowed_uses: tuple[str, ...]
    approval_requirement: str
    expected_output: str
    review_destination: str
    approval_required: bool
    fake_runner_supported: bool
    live_provider_allowed: bool


class Mvp2SkillsReviewSummary(BaseModel):
    review_status: str = "ready_for_human_review"
    focused_skills: tuple[Mvp2CapabilityReviewCard, ...]
    dependency_gated_capabilities: tuple[Mvp2CapabilityReviewCard, ...]
    route_cards: tuple[Mvp2RouteReviewCard, ...]
    chain_stages: tuple[Mvp2ChainStageReviewCard, ...]
    model_role_contracts: tuple[Mvp2ModelRoleReviewCard, ...]
    capability_runs: tuple[CapabilityRun, ...]
    improvement_proposals: tuple[HermesImprovementProposal, ...]
    focused_skill_count: int
    dependency_gated_count: int
    pending_output_count: int
    trusted_downstream_writes: bool = False
    guardrail_summary: str = (
        "No trusted downstream writes. Skill, chain, model, and autonomy outputs require review."
    )


def build_mvp2_skills_review_summary(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> Mvp2SkillsReviewSummary:
    root = workspace_root or Path.cwd()
    catalog = discover_local_capability_catalog(root)
    capability_runs = tuple(_capability_run_store(settings, root).list())
    activation_runs = _activation_run_store(settings, root).list()
    proposals = _improvement_proposal_store(settings, root).list()
    focused = tuple(
        _capability_card(entry)
        for entry in catalog.entries
        if entry.id in MVP2_FOCUSED_SKILL_IDS
    )
    dependency_gated = tuple(
        _capability_card(entry)
        for entry in catalog.entries
        if entry.capability_status is CapabilityStatus.DEPENDENCY_GATED
    )
    return Mvp2SkillsReviewSummary(
        focused_skills=focused,
        dependency_gated_capabilities=dependency_gated,
        route_cards=_route_cards(activation_runs),
        chain_stages=_chain_stage_cards(capability_runs),
        model_role_contracts=_model_role_cards(),
        capability_runs=capability_runs,
        improvement_proposals=proposals,
        focused_skill_count=len(focused),
        dependency_gated_count=len(dependency_gated),
        pending_output_count=_pending_output_count(capability_runs),
    )


def seed_mvp2_skills_review_demo(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> Mvp2SkillsReviewSummary:
    root = workspace_root or Path.cwd()
    capability_store = _capability_run_store(settings, root)
    activation_store = _activation_run_store(settings, root)
    run_opportunity_activation(
        opportunity_id=MVP2_REVIEW_OPPORTUNITY_ID,
        definitions=build_default_packet_field_definitions(),
        current_milestone_gate=MilestoneGate.MILESTONE_2,
        store=activation_store,
        capability_run_store=capability_store,
        approved_capability_route_ids=(MVP2_REVIEW_ROUTE_ID,),
        capability_route_inputs={MVP2_REVIEW_ROUTE_ID: _demo_table_request()},
        run_id=MVP2_REVIEW_ACTIVATION_RUN_ID,
    )
    chain_run = _latest_chain_run(capability_store.list())
    reviewed_run = chain_run
    if chain_run.outputs and chain_run.outputs[0].review_state is CapabilityRunOutputReviewState.PENDING:
        reviewed_run = record_capability_run_output_review(
            store=capability_store,
            run_id=chain_run.run_id,
            output_id=chain_run.outputs[0].output_id,
            decision=CapabilityRunReviewDecisionType.DISCARD,
            reviewer_rationale="Route summary missed workload assumptions.",
        )
    proposal = propose_skill_improvement_from_capability_run(
        run=reviewed_run,
        kind=ImprovementProposalKind.CHAIN_ORDER_CHANGE,
        target_ref="skill-chain:data-table-profile-next-route",
        title="Add workload-assumption review after data profiling",
        proposed_change=(
            "Insert a workload-assumption review stage before the next-route summary."
        ),
    )
    _improvement_proposal_store(settings, root).write(proposal)
    return build_mvp2_skills_review_summary(settings, workspace_root=root)


def render_mvp2_skills_review_shell(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> str:
    summary = build_mvp2_skills_review_summary(
        settings,
        workspace_root=workspace_root,
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(settings.public_app_name)} MVP-2 Skills Review</title>
  <style>
    :root {{ color-scheme: dark; --bg: #020617; --surface: #0f172a; --surface-strong: #111c31; --edge: #334155; --edge-soft: #243244; --text: #f8fafc; --muted: #b6c4d6; --quiet: #8292a8; --cyan: #22d3ee; --green: #22c55e; --amber: #fbbf24; --red: #fb7185; --focus: #fbbf24; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100dvh; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--text); }}
    a {{ color: inherit; }}
    a:focus-visible, button:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
    .shell {{ width: min(100% - 32px, 1420px); margin: 0 auto; padding: 24px 0 48px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 18px; }}
    .back-link, .link-row, .action-button {{ display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 10px 14px; border: 1px solid var(--cyan); border-radius: 8px; color: var(--cyan); background: rgba(34, 211, 238, 0.1); text-decoration: none; font: inherit; font-weight: 900; cursor: pointer; }}
    .eyebrow {{ margin: 0 0 8px; color: var(--cyan); font-size: 0.78rem; font-weight: 800; letter-spacing: 0; text-transform: uppercase; }}
    h1 {{ margin: 0; font-size: 1.75rem; line-height: 1.15; letter-spacing: 0; }}
    h2 {{ margin: 0; font-size: 1.05rem; line-height: 1.25; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 16px 0; }}
    .metric, .panel, .row {{ border: 1px solid var(--edge); border-radius: 8px; background: rgba(15, 23, 42, 0.94); }}
    .metric {{ min-height: 92px; padding: 14px; }}
    .metric span {{ display: block; color: var(--quiet); font-size: 0.78rem; font-weight: 800; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 8px; font-size: 1.15rem; }}
    .review-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .panel {{ padding: 16px; }}
    .panel-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }}
    .row-list {{ display: grid; gap: 8px; }}
    .row {{ display: grid; gap: 6px; padding: 12px; background: var(--surface-strong); }}
    .row strong {{ color: var(--text); }}
    .row span {{ color: var(--muted); line-height: 1.45; overflow-wrap: anywhere; }}
    .status-chip {{ display: inline-flex; align-items: center; min-height: 30px; padding: 5px 8px; border: 1px solid var(--edge); border-radius: 8px; color: var(--muted); background: #0b1220; font-size: 0.78rem; font-weight: 800; white-space: nowrap; }}
    .status-chip.green {{ border-color: rgba(34, 197, 94, 0.55); color: var(--green); background: rgba(34, 197, 94, 0.1); }}
    .status-chip.cyan {{ border-color: rgba(34, 211, 238, 0.55); color: var(--cyan); background: rgba(34, 211, 238, 0.1); }}
    .status-chip.amber {{ border-color: rgba(251, 191, 36, 0.55); color: var(--amber); background: rgba(251, 191, 36, 0.1); }}
    .mono {{ font-family: Consolas, "Courier New", monospace; }}
    @media (max-width: 980px) {{ .review-grid, .metric-grid {{ grid-template-columns: 1fr; }} .topbar {{ display: block; }} .back-link {{ margin-top: 12px; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <div><p class="eyebrow">Human review gate</p><h1>MVP-2 Skills Review</h1></div>
      <a class="back-link" href="/">Back to Command Center</a>
    </div>
    <form action="/mvp-2/skills-review/actions/demo-run" method="post"><button class="action-button" type="submit">Create MVP-2 review demo</button></form>
    <div class="metric-grid">
      <div class="metric"><span>Focused skills</span><strong>{summary.focused_skill_count}</strong></div>
      <div class="metric"><span>Dependency-gated</span><strong>{summary.dependency_gated_count}</strong></div>
      <div class="metric"><span>Pending outputs</span><strong>{summary.pending_output_count}</strong></div>
      <div class="metric"><span>Guardrail</span><strong>No trusted downstream writes</strong></div>
    </div>
    <div class="review-grid">
      {_render_focused_skills(summary.focused_skills)}
      {_render_dependency_gated(summary.dependency_gated_capabilities)}
      {_render_route_cards(summary.route_cards)}
      {_render_chain_stages(summary.chain_stages)}
      {_render_model_roles(summary.model_role_contracts)}
      {_render_capability_runs(summary.capability_runs)}
      {_render_improvement_proposals(summary.improvement_proposals)}
      <section class="panel" aria-labelledby="review-api-heading"><div class="panel-heading"><h2 id="review-api-heading">Review API</h2><span class="status-chip cyan">JSON</span></div><a class="link-row" href="/api/mvp-2/skills-review">Open API summary</a></section>
    </div>
  </main>
</body>
</html>"""


def _capability_card(entry: CapabilityCatalogEntry) -> Mvp2CapabilityReviewCard:
    return Mvp2CapabilityReviewCard(
        capability_id=entry.id,
        name=entry.name,
        capability_status=entry.capability_status.value,
        capability_type=entry.capability_type.value,
        validation_status=entry.validation_status.value,
        review_destination=entry.contract.review_destination,
        quality_gate=entry.contract.quality_gate,
        source_path=entry.source_path,
        next_enabling_action=entry.contract.next_enabling_action,
    )


def _route_cards(
    runs: tuple[OpportunityActivationRun, ...],
) -> tuple[Mvp2RouteReviewCard, ...]:
    return tuple(
        _route_card(route)
        for run in runs
        for field in run.packet_field_action_matrix.fields
        for route in field.capability_routes
    )


def _route_card(route: OpportunityActivationCapabilityRoute) -> Mvp2RouteReviewCard:
    return Mvp2RouteReviewCard(
        route_id=route.route_id,
        field_key=route.field_key,
        capability_id=route.capability_id,
        capability_type=route.capability_type,
        status=route.status.value,
        approval_required=route.approval_required,
        approval_gate=route.approval_gate,
        review_destination=route.review_destination,
        invoked_run_id=route.invoked_run_id,
        invoked_output_ids=route.invoked_output_ids,
        source_limitations=route.source_limitations,
        trusted_downstream_writes=route.trusted_downstream_writes,
    )


def _chain_stage_cards(
    runs: tuple[CapabilityRun, ...],
) -> tuple[Mvp2ChainStageReviewCard, ...]:
    cards: list[Mvp2ChainStageReviewCard] = []
    for run in runs:
        for output in run.outputs:
            chain = output.provenance.get("thin_orchestration_chain")
            if not isinstance(chain, dict):
                continue
            stages = chain.get("stage_records", ())
            if not isinstance(stages, list | tuple):
                continue
            cards.extend(_stage_card(run.run_id, stage) for stage in stages if isinstance(stage, dict))
    return tuple(cards)


def _stage_card(run_id: str, stage: dict[str, Any]) -> Mvp2ChainStageReviewCard:
    return Mvp2ChainStageReviewCard(
        run_id=run_id,
        stage_id=str(stage.get("stage_id", "")),
        capability_id=str(stage.get("capability_id", "")),
        status=str(stage.get("status", "")),
        quality_gate_result=str(stage.get("quality_gate_result", "")),
        review_destination=str(stage.get("review_destination", "")),
        produced_handoff=str(stage.get("produced_handoff", "")),
        input_refs=_string_tuple(stage.get("input_refs", ())),
        gaps=_string_tuple(stage.get("gaps", ())),
    )


def _model_role_cards() -> tuple[Mvp2ModelRoleReviewCard, ...]:
    return tuple(
        _model_role_card(contract)
        for contract in MVP2_MODEL_ROLE_CONTRACTS
    )


def _model_role_card(
    contract: AssistedRouteModelRoleContract,
) -> Mvp2ModelRoleReviewCard:
    return Mvp2ModelRoleReviewCard(
        model_role=contract.model_role.value,
        allowed_uses=contract.allowed_uses,
        approval_requirement=contract.approval_requirement.value,
        expected_output=contract.expected_output,
        review_destination=contract.review_destination,
        approval_required=contract.approval_required,
        fake_runner_supported=contract.fake_runner_supported,
        live_provider_allowed=contract.live_provider_allowed,
    )


def _pending_output_count(runs: tuple[CapabilityRun, ...]) -> int:
    return sum(
        output.review_state is CapabilityRunOutputReviewState.PENDING
        for run in runs
        for output in run.outputs
    )


def _latest_chain_run(runs: list[CapabilityRun]) -> CapabilityRun:
    for run in reversed(runs):
        if run.capability_id == "data-table-profile-next-route-chain":
            return run
    raise ValueError("MVP-2 demo chain run was not created")


def _capability_run_store(settings: RuntimeSettings, root: Path) -> CapabilityRunStore:
    return CapabilityRunStore(_runtime_path(root, settings.ariadne_capability_runs_dir))


def _activation_run_store(
    settings: RuntimeSettings,
    root: Path,
) -> OpportunityActivationRunStore:
    return OpportunityActivationRunStore(
        _runtime_path(root, settings.ariadne_opportunity_activation_dir)
    )


def _improvement_proposal_store(
    settings: RuntimeSettings,
    root: Path,
) -> ImprovementProposalStore:
    capability_dir = _runtime_path(root, settings.ariadne_capability_runs_dir)
    return ImprovementProposalStore(capability_dir.parent / "improvement-proposals")


def _runtime_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _demo_table_request() -> DataTableProfileRequest:
    return DataTableProfileRequest(
        table_label="MVP-2 review workload table",
        source_ref="fixture://mvp2-skills-review-workload-table",
        source_refs=("fixture://mvp2-skills-review-workload-table",),
        rows=(
            {"Workload ID": "WL-1", "Labor Category": "Analyst", "Hours": 120},
            {"Workload ID": "WL-1", "Labor Category": "", "Hours": None},
            {"Workload ID": "WL-2", "Labor Category": "Engineer", "Hours": 240},
        ),
    )


def _render_focused_skills(cards: tuple[Mvp2CapabilityReviewCard, ...]) -> str:
    return _render_card_section("Focused skills", "runnable", tuple(_capability_row(card) for card in cards))


def _render_dependency_gated(cards: tuple[Mvp2CapabilityReviewCard, ...]) -> str:
    return _render_card_section(
        "Dependency-gated capabilities",
        "blocked",
        tuple(_capability_row(card) for card in cards),
    )


def _capability_row(card: Mvp2CapabilityReviewCard) -> str:
    enabling = card.next_enabling_action or "Review output before trusted use."
    return f"""<div class="row"><strong>{escape(card.name)}</strong><span>{escape(card.capability_id)} - {escape(card.capability_status)} - {escape(card.validation_status)}</span><span>Destination: {escape(card.review_destination)} - Gate: {escape(card.quality_gate)}</span><span>{escape(enabling)}</span></div>"""


def _render_route_cards(cards: tuple[Mvp2RouteReviewCard, ...]) -> str:
    rows = tuple(
        f"""<div class="row"><strong>{escape(card.route_id)}</strong><span>{escape(card.capability_id)} - {escape(card.status)} - field {escape(card.field_key)}</span><span>Approval: {escape(str(card.approval_required))} - {escape(card.approval_gate or 'none')}</span><span>Destination: {escape(card.review_destination)} - Invoked: {escape(card.invoked_run_id or 'not run')}</span><span>Limits: {escape(_join_or_none(card.source_limitations))}</span></div>"""
        for card in cards
    )
    return _render_card_section("Route cards", "activation", rows)


def _render_chain_stages(cards: tuple[Mvp2ChainStageReviewCard, ...]) -> str:
    rows = tuple(
        f"""<div class="row"><strong>{escape(card.stage_id)}</strong><span>{escape(card.capability_id)} - {escape(card.status)} - run {escape(card.run_id)}</span><span>Quality gate: {escape(card.quality_gate_result)} - Destination: {escape(card.review_destination)}</span><span>Handoff: {escape(card.produced_handoff)}</span><span>Gaps: {escape(_join_or_none(card.gaps))}</span></div>"""
        for card in cards
    )
    return _render_card_section("Chain stages", "quality gates", rows)


def _render_model_roles(cards: tuple[Mvp2ModelRoleReviewCard, ...]) -> str:
    rows = tuple(
        f"""<div class="row"><strong>{escape(card.model_role)}</strong><span>{escape(card.expected_output)}</span><span>Approval: {escape(card.approval_requirement)} - Destination: {escape(card.review_destination)}</span><span>Uses: {escape(_join_or_none(card.allowed_uses))}</span><span>Fake runner: {escape(str(card.fake_runner_supported))} - Live provider: {escape(str(card.live_provider_allowed))}</span></div>"""
        for card in cards
    )
    return _render_card_section("Model role contracts", "approval", rows)


def _render_capability_runs(runs: tuple[CapabilityRun, ...]) -> str:
    rows = tuple(
        f"""<div class="row"><strong>{escape(run.capability_id)}</strong><span>{escape(run.run_id)} - {escape(run.status.value)} - {escape(run.executor_kind.value)}</span><span>Outputs: {len(run.outputs)} - Trusted writes: {escape(str(run.provenance.get('trusted_downstream_writes', False)))}</span><a class="link-row" href="/capability-studio/runs/{escape(run.run_id)}">Open run detail</a></div>"""
        for run in runs
    )
    return _render_card_section("Run progress and provenance", "runs", rows)


def _render_improvement_proposals(
    proposals: tuple[HermesImprovementProposal, ...],
) -> str:
    rows = tuple(
        f"""<div class="row"><strong>{escape(proposal.title)}</strong><span>{escape(proposal.kind.value)} - {escape(proposal.review_state.value)} - {escape(proposal.target_ref)}</span><span>{escape(proposal.proposed_change)}</span><span>{escape(proposal.guardrail_summary)}</span><span>Mutates skills: {escape(str(proposal.mutates_skills))} - Mutates chains: {escape(str(proposal.mutates_chain_maps))} - Mutates autonomy: {escape(str(proposal.mutates_autonomy_settings))}</span></div>"""
        for proposal in proposals
    )
    return _render_card_section("Hermes Improvement Proposals", "suggestions", rows)


def _render_card_section(title: str, label: str, rows: tuple[str, ...]) -> str:
    body = "".join(rows) if rows else """<div class="row"><strong>None yet</strong><span>Create demo or run workflow to populate this review area.</span></div>"""
    return f"""<section class="panel" aria-labelledby="{escape(_slug(title))}-heading"><div class="panel-heading"><h2 id="{escape(_slug(title))}-heading">{escape(title)}</h2><span class="status-chip cyan">{escape(label)}</span></div><div class="row-list">{body}</div></section>"""


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple | list):
        return tuple(str(item) for item in value)
    if value is None:
        return ()
    return (str(value),)


def _join_or_none(values: tuple[str, ...]) -> str:
    return " | ".join(values) if values else "none"


def _slug(value: str) -> str:
    return "-".join(value.lower().split())