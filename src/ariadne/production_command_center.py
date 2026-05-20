from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ariadne.config import RuntimeSettings
from ariadne.packets import EvidenceStatus
from ariadne.quick_capture_demo import build_quick_capture_demo_thread


class ProductionCommandCenterOpportunity(BaseModel):
    id: str
    name: str
    lifecycle_state: str
    gate_status: str


class ProductionCommandCenterPacket(BaseModel):
    title: str
    readiness_label: str
    answered_section_count: int
    gap_section_count: int
    partial_section_count: int


class ProductionCommandCenterContextSummary(BaseModel):
    trusted_count: int
    reviewable_count: int
    gap_count: int
    source_limitation_count: int


class ProductionCommandCenterRegion(BaseModel):
    id: str
    label: str
    purpose: str


class ProductionCommandCenterWorkMode(BaseModel):
    id: str
    label: str
    pending_count: int = 0


class ProductionCommandCenterWorkspace(BaseModel):
    production_ui_contract: str
    scaffold_role: str
    opportunity: ProductionCommandCenterOpportunity
    packet: ProductionCommandCenterPacket
    context_summary: ProductionCommandCenterContextSummary
    layout_regions: tuple[ProductionCommandCenterRegion, ...]
    work_modes: tuple[ProductionCommandCenterWorkMode, ...]


def build_production_command_center_workspace(
    settings: RuntimeSettings,
    *,
    workspace_root: Path | None = None,
) -> ProductionCommandCenterWorkspace:
    demo = build_quick_capture_demo_thread(
        settings,
        workspace_root=workspace_root or Path.cwd(),
    )
    packet_states = tuple(demo.packet.sections.values())
    gap_count = sum(1 for state in packet_states if state.evidence_status is EvidenceStatus.GAP)
    partial_count = sum(
        1 for state in packet_states if state.evidence_status is EvidenceStatus.PARTIAL
    )
    answered_count = sum(
        1 for state in packet_states if state.evidence_status is EvidenceStatus.ANSWERED
    )
    reviewable_count = (
        len(demo.capture_review.proposals)
        + len(demo.pasted_review.proposals)
        + len(demo.uploaded_review.proposals)
        + len(demo.document_intake.candidates)
    )

    return ProductionCommandCenterWorkspace(
        production_ui_contract="nextjs_command_center_shell",
        scaffold_role="fallback_debug_only",
        opportunity=ProductionCommandCenterOpportunity(
            id="opp-aflcmc-recompete",
            name=demo.opportunity.name,
            lifecycle_state=demo.opportunity.lifecycle_state.value,
            gate_status="capture_working_session",
        ),
        packet=ProductionCommandCenterPacket(
            title="Living Milestone Decision Briefing Packet",
            readiness_label=demo.packet.readiness.value,
            answered_section_count=answered_count,
            gap_section_count=gap_count,
            partial_section_count=partial_count,
        ),
        context_summary=ProductionCommandCenterContextSummary(
            trusted_count=3,
            reviewable_count=reviewable_count,
            gap_count=gap_count + partial_count,
            source_limitation_count=len(demo.unsupported_upload.warnings),
        ),
        layout_regions=(
            ProductionCommandCenterRegion(
                id="left_rail",
                label="Opportunity and work-mode navigation",
                purpose="Switch Opportunity, inspect gate state, and move between work modes.",
            ),
            ProductionCommandCenterRegion(
                id="packet_workspace",
                label="Living Milestone Decision Briefing Packet workspace",
                purpose="Show packet readiness, supported answers, gaps, assumptions, and source chips.",
            ),
            ProductionCommandCenterRegion(
                id="command_review_rail",
                label="Command and review rail",
                purpose="Start assisted capture, inspect route recommendations, and review output.",
            ),
            ProductionCommandCenterRegion(
                id="provenance_drawer",
                label="Provenance and output inspection",
                purpose="Inspect sources, route rationale, run details, and output trace.",
            ),
        ),
        work_modes=(
            ProductionCommandCenterWorkMode(id="packet", label="Packet", pending_count=gap_count + partial_count),
            ProductionCommandCenterWorkMode(id="actions", label="Actions", pending_count=len(demo.action_plan.items)),
            ProductionCommandCenterWorkMode(id="engagement", label="Engagement"),
            ProductionCommandCenterWorkMode(id="research", label="Research"),
            ProductionCommandCenterWorkMode(id="documents", label="Documents", pending_count=1),
            ProductionCommandCenterWorkMode(id="artifacts", label="Artifacts"),
            ProductionCommandCenterWorkMode(id="capability_studio", label="Capability Studio"),
        ),
    )