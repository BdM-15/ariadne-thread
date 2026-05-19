from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, Field

from ariadne.packets import CanonicalPacketSection
from ariadne.structured_knowledge import (
    KnowledgeContextItem,
    KnowledgeGapSummary,
    KnowledgeRecordKind,
    KnowledgeSourceLimitation,
    KnowledgeTrustState,
    OpportunityKnowledgeContextView,
)


class ArtifactSourceUse(StrEnum):
    DIRECT_SUPPORT = "direct_support"
    NEEDS_REVIEW = "needs_review"
    GAP = "gap"
    ASSUMPTION = "assumption"
    LIMITATION = "limitation"


class ArtifactDraftType(StrEnum):
    MILESTONE_DECISION_BRIEFING_PACKET = "milestone_decision_briefing_packet"


class ArtifactDraftReadiness(StrEnum):
    ASSEMBLING = "assembling"
    NEEDS_REVIEW = "needs_review"
    PARTIALLY_REVIEWED = "partially_reviewed"
    PREVIEW_READY = "preview_ready"
    EXPORT_READY = "export_ready"
    SUPERSEDED = "superseded"
    CANCELED = "canceled"


class ArtifactContentBlockKind(StrEnum):
    NARRATIVE = "narrative"
    DECISION_SUMMARY = "decision_summary"
    EVIDENCE_TABLE = "evidence_table"
    ACTION_LIST = "action_list"
    RISK_LIST = "risk_list"
    ASSUMPTION_LIST = "assumption_list"
    GAP_LIST = "gap_list"
    SOURCE_APPENDIX = "source_appendix"


class ArtifactBlockSupportClassification(StrEnum):
    TRUSTED_SUPPORT = "trusted_support"
    NEEDS_REVIEW = "needs_review"
    MIXED_SUPPORT = "mixed_support"
    ASSUMPTION = "assumption"


class ArtifactBlockReviewAction(StrEnum):
    ACCEPT = "accept"
    EDIT = "edit"
    DISCARD = "discard"
    ROUTE = "route"
    EXCLUDE_FROM_EXPORT = "exclude_from_export"
    MARK_NEEDS_EVIDENCE = "mark_needs_evidence"


class ArtifactBlockReviewState(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EDITED = "edited"
    DISCARDED = "discarded"
    ROUTED = "routed"
    EXCLUDED_FROM_EXPORT = "excluded_from_export"
    NEEDS_EVIDENCE = "needs_evidence"


class ArtifactSourceRef(BaseModel):
    record_kind: KnowledgeRecordKind
    record_id: str
    title: str
    summary: str
    trust_state: KnowledgeTrustState
    allowed_use: ArtifactSourceUse


class ArtifactGapRef(BaseModel):
    record_kind: KnowledgeRecordKind
    record_id: str
    summary: str
    command_id: str
    allowed_use: ArtifactSourceUse = ArtifactSourceUse.GAP


class ArtifactSourceLimitationRef(BaseModel):
    record_kind: KnowledgeRecordKind
    record_id: str
    summary: str
    allowed_use: ArtifactSourceUse = ArtifactSourceUse.LIMITATION


class ArtifactSourcePackage(BaseModel):
    package_id: str
    opportunity_id: str
    source_context: str = "opportunity_knowledge_context"
    trusted_refs: tuple[ArtifactSourceRef, ...] = ()
    reviewable_refs: tuple[ArtifactSourceRef, ...] = ()
    gap_refs: tuple[ArtifactGapRef, ...] = ()
    assumptions: tuple[str, ...] = ()
    source_limitations: tuple[ArtifactSourceLimitationRef, ...] = ()
    pending_review_refs: tuple[str, ...] = ()
    created_at: str


class ArtifactSourcePackageSummary(BaseModel):
    package_id: str
    opportunity_id: str
    trusted_count: int
    reviewable_count: int
    gap_count: int
    assumption_count: int
    source_limitation_count: int
    pending_review_count: int


class ArtifactRendererReadiness(BaseModel):
    preview_ready: bool = False
    export_ready: bool = False
    renderer_invoked: bool = False
    preview_blocking_refs: tuple[str, ...] = ()
    export_blocking_refs: tuple[str, ...] = ()
    deferred_renderer_note: str = "Renderer execution is deferred."


class ArtifactDraftProvenance(BaseModel):
    source_package_id: str
    source_package_created_at: str
    capability_id: str
    capability_contract_id: str
    assembly_mode: str = "deterministic_non_llm"
    model_assist_used: bool = False


class ArtifactBlockReviewDecision(BaseModel):
    decision_id: str
    block_id: str
    action: ArtifactBlockReviewAction
    decided_at: str
    reviewer_notes: str = ""
    routed_destination: str | None = None
    original_body: str
    revised_body: str | None = None
    source_ref_ids: tuple[str, ...] = ()
    reviewable_ref_ids: tuple[str, ...] = ()
    gap_ref_ids: tuple[str, ...] = ()
    source_limitation_ref_ids: tuple[str, ...] = ()
    autonomy_hint: str = "review_required"


class ArtifactContentBlock(BaseModel):
    block_id: str
    block_kind: ArtifactContentBlockKind
    title: str
    body: str
    source_ref_ids: tuple[str, ...] = ()
    reviewable_ref_ids: tuple[str, ...] = ()
    gap_ref_ids: tuple[str, ...] = ()
    source_limitation_ref_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    support_classification: ArtifactBlockSupportClassification = (
        ArtifactBlockSupportClassification.NEEDS_REVIEW
    )
    content_data: dict[str, object] = Field(default_factory=dict)
    review_state: ArtifactBlockReviewState = ArtifactBlockReviewState.PENDING
    review_decisions: tuple[ArtifactBlockReviewDecision, ...] = ()
    autonomy_hint: str = "review_required"
    export_required: bool = True


class ArtifactSection(BaseModel):
    section_id: str
    title: str
    purpose: str
    source_ref_ids: tuple[str, ...] = ()
    blocks: tuple[ArtifactContentBlock, ...]


class ArtifactAssemblyCapabilityContract(BaseModel):
    capability_id: str
    capability_contract_id: str
    product_workflow: str
    contribution_boundary: str
    third_party_installation_required: bool = False
    skill_chain_execution_required: bool = False
    renderer_execution_allowed: bool = False


class ArtifactDraft(BaseModel):
    draft_id: str
    artifact_type: ArtifactDraftType
    opportunity_id: str
    source_package_id: str
    readiness_state: ArtifactDraftReadiness
    sections: tuple[ArtifactSection, ...]
    renderer_readiness: ArtifactRendererReadiness
    provenance: ArtifactDraftProvenance
    created_at: str
    refreshed_at: str | None = None


class ArtifactAssemblyStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write_source_package(
        self,
        package: ArtifactSourcePackage,
    ) -> ArtifactSourcePackage:
        self._source_package_root.mkdir(parents=True, exist_ok=True)
        self._source_package_path(package.package_id).write_text(
            package.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return package

    def read_source_package(self, package_id: str) -> ArtifactSourcePackage:
        return ArtifactSourcePackage.model_validate_json(
            self._source_package_path(package_id).read_text(encoding="utf-8")
        )

    def list_source_packages(
        self,
        *,
        opportunity_id: str | None = None,
    ) -> list[ArtifactSourcePackage]:
        if not self._source_package_root.exists():
            return []
        packages = [
            self.read_source_package(path.name.removesuffix(".json"))
            for path in sorted(self._source_package_root.glob("*.json"))
        ]
        if opportunity_id is not None:
            packages = [
                package
                for package in packages
                if package.opportunity_id == opportunity_id
            ]
        return packages

    def write_artifact_draft(self, draft: ArtifactDraft) -> ArtifactDraft:
        self._artifact_draft_root.mkdir(parents=True, exist_ok=True)
        self._artifact_draft_path(draft.draft_id).write_text(
            draft.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return draft

    def read_artifact_draft(self, draft_id: str) -> ArtifactDraft:
        return ArtifactDraft.model_validate_json(
            self._artifact_draft_path(draft_id).read_text(encoding="utf-8")
        )

    def list_artifact_drafts(
        self,
        *,
        opportunity_id: str | None = None,
    ) -> list[ArtifactDraft]:
        if not self._artifact_draft_root.exists():
            return []
        drafts = [
            self.read_artifact_draft(path.name.removesuffix(".json"))
            for path in sorted(self._artifact_draft_root.glob("*.json"))
        ]
        if opportunity_id is not None:
            drafts = [draft for draft in drafts if draft.opportunity_id == opportunity_id]
        return drafts

    @property
    def _source_package_root(self) -> Path:
        return self.root / "source-packages"

    @property
    def _artifact_draft_root(self) -> Path:
        return self.root / "artifact-drafts"

    def _source_package_path(self, package_id: str) -> Path:
        if not package_id or package_id != Path(package_id).name:
            raise ValueError("package_id must be a file-safe identifier")
        return self._source_package_root / f"{package_id}.json"

    def _artifact_draft_path(self, draft_id: str) -> Path:
        if not draft_id or draft_id != Path(draft_id).name:
            raise ValueError("draft_id must be a file-safe identifier")
        return self._artifact_draft_root / f"{draft_id}.json"


def create_artifact_source_package_from_context(
    *,
    context: OpportunityKnowledgeContextView,
    store: ArtifactAssemblyStore,
    created_at: str,
    assumptions: tuple[str, ...] = (),
) -> ArtifactSourcePackage:
    package = build_artifact_source_package_from_context(
        context=context,
        created_at=created_at,
        assumptions=assumptions,
    )
    return store.write_source_package(package)


def build_artifact_source_package_from_context(
    *,
    context: OpportunityKnowledgeContextView,
    created_at: str,
    assumptions: tuple[str, ...] = (),
) -> ArtifactSourcePackage:
    trusted_refs = tuple(
        _source_ref(item, allowed_use=ArtifactSourceUse.DIRECT_SUPPORT)
        for item in context.trusted_context.items
    )
    reviewable_refs = tuple(
        _source_ref(item, allowed_use=ArtifactSourceUse.NEEDS_REVIEW)
        for item in context.reviewable_context.items
    )
    gap_refs = tuple(_gap_ref(gap) for gap in context.gaps)
    source_limitations = tuple(
        _source_limitation_ref(limitation)
        for limitation in context.source_limitations
    )
    return ArtifactSourcePackage(
        package_id=_source_package_id(context.opportunity_id),
        opportunity_id=context.opportunity_id,
        trusted_refs=trusted_refs,
        reviewable_refs=reviewable_refs,
        gap_refs=gap_refs,
        assumptions=assumptions,
        source_limitations=source_limitations,
        pending_review_refs=_pending_review_refs(
            reviewable_refs=reviewable_refs,
            gap_refs=gap_refs,
            source_limitations=source_limitations,
        ),
        created_at=created_at,
    )


def summarize_artifact_source_package(
    package: ArtifactSourcePackage,
) -> ArtifactSourcePackageSummary:
    return ArtifactSourcePackageSummary(
        package_id=package.package_id,
        opportunity_id=package.opportunity_id,
        trusted_count=len(package.trusted_refs),
        reviewable_count=len(package.reviewable_refs),
        gap_count=len(package.gap_refs),
        assumption_count=len(package.assumptions),
        source_limitation_count=len(package.source_limitations),
        pending_review_count=len(package.pending_review_refs),
    )


def milestone_packet_draft_capability_contract() -> ArtifactAssemblyCapabilityContract:
    return ArtifactAssemblyCapabilityContract(
        capability_id="artifact_assembly.milestone_packet_draft_shell",
        capability_contract_id="artifact_assembly.milestone_packet_draft_shell.v1",
        product_workflow="milestone_decision_briefing_packet",
        contribution_boundary=(
            "Create renderer-neutral draft sections and source-backed block shells "
            "from an explicit Artifact Source Package."
        ),
    )


def assemble_milestone_packet_draft(
    *,
    source_package_id: str,
    store: ArtifactAssemblyStore,
    assembled_at: str,
) -> ArtifactDraft:
    source_package = store.read_source_package(source_package_id)
    contract = milestone_packet_draft_capability_contract()
    draft_id = _artifact_draft_id(
        source_package.opportunity_id,
        source_package.package_id,
    )
    try:
        existing_draft = store.read_artifact_draft(draft_id)
    except FileNotFoundError:
        existing_draft = None
    draft = ArtifactDraft(
        draft_id=draft_id,
        artifact_type=ArtifactDraftType.MILESTONE_DECISION_BRIEFING_PACKET,
        opportunity_id=source_package.opportunity_id,
        source_package_id=source_package.package_id,
        readiness_state=ArtifactDraftReadiness.NEEDS_REVIEW,
        sections=_milestone_packet_sections(source_package),
        renderer_readiness=ArtifactRendererReadiness(
            preview_blocking_refs=source_package.pending_review_refs,
            export_blocking_refs=source_package.pending_review_refs,
        ),
        provenance=ArtifactDraftProvenance(
            source_package_id=source_package.package_id,
            source_package_created_at=source_package.created_at,
            capability_id=contract.capability_id,
            capability_contract_id=contract.capability_contract_id,
        ),
        created_at=existing_draft.created_at if existing_draft else assembled_at,
        refreshed_at=assembled_at if existing_draft else None,
    )
    return store.write_artifact_draft(draft)


def review_artifact_block(
    *,
    draft_id: str,
    block_id: str,
    action: ArtifactBlockReviewAction,
    store: ArtifactAssemblyStore,
    reviewed_at: str,
    reviewer_notes: str = "",
    edited_body: str | None = None,
    routed_destination: str | None = None,
) -> ArtifactDraft:
    draft = store.read_artifact_draft(draft_id)
    updated_sections: list[ArtifactSection] = []
    block_found = False
    for section in draft.sections:
        updated_blocks: list[ArtifactContentBlock] = []
        for block in section.blocks:
            if block.block_id == block_id:
                updated_blocks.append(
                    _reviewed_block(
                        block,
                        action=action,
                        reviewed_at=reviewed_at,
                        reviewer_notes=reviewer_notes,
                        edited_body=edited_body,
                        routed_destination=routed_destination,
                    )
                )
                block_found = True
            else:
                updated_blocks.append(block)
        updated_sections.append(
            section.model_copy(update={"blocks": tuple(updated_blocks)})
        )
    if not block_found:
        raise ValueError(f"Artifact block not found: {block_id}")
    reviewed_draft = draft.model_copy(update={"sections": tuple(updated_sections)})
    reviewed_draft = _refresh_draft_readiness(reviewed_draft)
    return store.write_artifact_draft(reviewed_draft)


def _source_ref(
    item: KnowledgeContextItem,
    *,
    allowed_use: ArtifactSourceUse,
) -> ArtifactSourceRef:
    return ArtifactSourceRef(
        record_kind=item.record_kind,
        record_id=item.record_id,
        title=item.title,
        summary=item.summary,
        trust_state=item.trust_state,
        allowed_use=allowed_use,
    )


def _reviewed_block(
    block: ArtifactContentBlock,
    *,
    action: ArtifactBlockReviewAction,
    reviewed_at: str,
    reviewer_notes: str,
    edited_body: str | None,
    routed_destination: str | None,
) -> ArtifactContentBlock:
    if action is ArtifactBlockReviewAction.EDIT and edited_body is None:
        raise ValueError("edited_body is required for edit review action")
    if action is ArtifactBlockReviewAction.ROUTE and not routed_destination:
        raise ValueError("routed_destination is required for route review action")
    revised_body = edited_body if action is ArtifactBlockReviewAction.EDIT else None
    review_state = _review_state_for_action(action)
    export_required = False if action is ArtifactBlockReviewAction.EXCLUDE_FROM_EXPORT else block.export_required
    decision = ArtifactBlockReviewDecision(
        decision_id=_review_decision_id(block.block_id, action, reviewed_at),
        block_id=block.block_id,
        action=action,
        decided_at=reviewed_at,
        reviewer_notes=reviewer_notes,
        routed_destination=routed_destination,
        original_body=block.body,
        revised_body=revised_body,
        source_ref_ids=block.source_ref_ids,
        reviewable_ref_ids=block.reviewable_ref_ids,
        gap_ref_ids=block.gap_ref_ids,
        source_limitation_ref_ids=block.source_limitation_ref_ids,
        autonomy_hint=block.autonomy_hint,
    )
    return block.model_copy(
        update={
            "body": revised_body if revised_body is not None else block.body,
            "review_state": review_state,
            "review_decisions": (*block.review_decisions, decision),
            "export_required": export_required,
        }
    )


def _review_state_for_action(
    action: ArtifactBlockReviewAction,
) -> ArtifactBlockReviewState:
    return {
        ArtifactBlockReviewAction.ACCEPT: ArtifactBlockReviewState.ACCEPTED,
        ArtifactBlockReviewAction.EDIT: ArtifactBlockReviewState.EDITED,
        ArtifactBlockReviewAction.DISCARD: ArtifactBlockReviewState.DISCARDED,
        ArtifactBlockReviewAction.ROUTE: ArtifactBlockReviewState.ROUTED,
        ArtifactBlockReviewAction.EXCLUDE_FROM_EXPORT: ArtifactBlockReviewState.EXCLUDED_FROM_EXPORT,
        ArtifactBlockReviewAction.MARK_NEEDS_EVIDENCE: ArtifactBlockReviewState.NEEDS_EVIDENCE,
    }[action]


def _refresh_draft_readiness(draft: ArtifactDraft) -> ArtifactDraft:
    blocks = tuple(block for section in draft.sections for block in section.blocks)
    reviewed_blocks = tuple(
        block
        for block in blocks
        if block.review_state is not ArtifactBlockReviewState.PENDING
    )
    export_blockers = _export_blocking_refs(blocks)
    preview_ready = len(reviewed_blocks) == len(blocks)
    export_ready = preview_ready and not export_blockers
    if not reviewed_blocks:
        readiness = ArtifactDraftReadiness.NEEDS_REVIEW
    elif export_ready:
        readiness = ArtifactDraftReadiness.EXPORT_READY
    elif preview_ready:
        readiness = ArtifactDraftReadiness.PREVIEW_READY
    else:
        readiness = ArtifactDraftReadiness.PARTIALLY_REVIEWED
    return draft.model_copy(
        update={
            "readiness_state": readiness,
            "renderer_readiness": draft.renderer_readiness.model_copy(
                update={
                    "preview_ready": preview_ready,
                    "export_ready": export_ready,
                    "renderer_invoked": False,
                    "preview_blocking_refs": _pending_block_refs(blocks),
                    "export_blocking_refs": export_blockers,
                }
            ),
        }
    )


def _pending_block_refs(blocks: tuple[ArtifactContentBlock, ...]) -> tuple[str, ...]:
    return tuple(
        block.block_id
        for block in blocks
        if block.review_state is ArtifactBlockReviewState.PENDING
    )


def _export_blocking_refs(blocks: tuple[ArtifactContentBlock, ...]) -> tuple[str, ...]:
    blockers: list[str] = []
    for block in blocks:
        if block.review_state in {
            ArtifactBlockReviewState.PENDING,
            ArtifactBlockReviewState.ROUTED,
            ArtifactBlockReviewState.NEEDS_EVIDENCE,
        }:
            blockers.append(block.block_id)
        blockers.extend(block.gap_ref_ids)
        blockers.extend(block.source_limitation_ref_ids)
    return tuple(dict.fromkeys(blockers))


def _review_decision_id(
    block_id: str,
    action: ArtifactBlockReviewAction,
    reviewed_at: str,
) -> str:
    digest = sha256(f"{block_id}:{action.value}:{reviewed_at}".encode("utf-8")).hexdigest()[
        :16
    ]
    return f"artifact_block_review_{digest}"


def _gap_ref(gap: KnowledgeGapSummary) -> ArtifactGapRef:
    return ArtifactGapRef(
        record_kind=gap.record_kind,
        record_id=gap.record_id,
        summary=gap.summary,
        command_id=gap.command_id,
    )


def _source_limitation_ref(
    limitation: KnowledgeSourceLimitation,
) -> ArtifactSourceLimitationRef:
    return ArtifactSourceLimitationRef(
        record_kind=limitation.record_kind,
        record_id=limitation.record_id,
        summary=limitation.summary,
    )


def _pending_review_refs(
    *,
    reviewable_refs: tuple[ArtifactSourceRef, ...],
    gap_refs: tuple[ArtifactGapRef, ...],
    source_limitations: tuple[ArtifactSourceLimitationRef, ...],
) -> tuple[str, ...]:
    refs = [
        *(ref.record_id for ref in reviewable_refs),
        *(ref.record_id for ref in gap_refs),
        *(ref.record_id for ref in source_limitations),
    ]
    return tuple(dict.fromkeys(refs))


def _source_package_id(opportunity_id: str) -> str:
    digest = sha256(opportunity_id.encode("utf-8")).hexdigest()[:16]
    return f"artifact_source_package_{digest}"


def _artifact_draft_id(opportunity_id: str, source_package_id: str) -> str:
    digest = sha256(f"{opportunity_id}:{source_package_id}".encode("utf-8")).hexdigest()[
        :16
    ]
    return f"milestone_packet_draft_{digest}"


def _milestone_packet_sections(
    source_package: ArtifactSourcePackage,
) -> tuple[ArtifactSection, ...]:
    source_ref_ids = tuple(ref.record_id for ref in source_package.trusted_refs)
    reviewable_ref_ids = tuple(ref.record_id for ref in source_package.reviewable_refs)
    gap_ref_ids = tuple(ref.record_id for ref in source_package.gap_refs)
    source_limitation_ref_ids = tuple(
        ref.record_id for ref in source_package.source_limitations
    )
    return tuple(
        ArtifactSection(
            section_id=section.value,
            title=section.value.replace("_", " ").title(),
            purpose=f"Reviewable shell for {section.value.replace('_', ' ')}.",
            source_ref_ids=source_ref_ids,
            blocks=_section_blocks(
                section=section,
                source_package=source_package,
                source_ref_ids=source_ref_ids,
                reviewable_ref_ids=reviewable_ref_ids,
                gap_ref_ids=gap_ref_ids,
                source_limitation_ref_ids=source_limitation_ref_ids,
            ),
        )
        for section in CanonicalPacketSection
    )


def _section_blocks(
    *,
    section: CanonicalPacketSection,
    source_package: ArtifactSourcePackage,
    source_ref_ids: tuple[str, ...],
    reviewable_ref_ids: tuple[str, ...],
    gap_ref_ids: tuple[str, ...],
    source_limitation_ref_ids: tuple[str, ...],
) -> tuple[ArtifactContentBlock, ...]:
    section_title = section.value.replace("_", " ").title()
    return (
        ArtifactContentBlock(
            block_id=f"{section.value}_narrative",
            block_kind=ArtifactContentBlockKind.NARRATIVE,
            title=f"{section_title} narrative",
            body=_joined_summaries(source_package.trusted_refs),
            source_ref_ids=source_ref_ids,
            support_classification=ArtifactBlockSupportClassification.TRUSTED_SUPPORT,
            content_data={"format": "narrative", "section": section.value},
        ),
        ArtifactContentBlock(
            block_id=f"{section.value}_decision_summary",
            block_kind=ArtifactContentBlockKind.DECISION_SUMMARY,
            title=f"{section_title} decision summary",
            body="Review trusted support and reviewable signals before gate decision.",
            source_ref_ids=source_ref_ids,
            reviewable_ref_ids=reviewable_ref_ids,
            support_classification=ArtifactBlockSupportClassification.MIXED_SUPPORT,
            content_data={"format": "summary", "section": section.value},
        ),
        ArtifactContentBlock(
            block_id=f"{section.value}_evidence_table",
            block_kind=ArtifactContentBlockKind.EVIDENCE_TABLE,
            title=f"{section_title} trusted support",
            body=f"{len(source_package.trusted_refs)} trusted refs available.",
            source_ref_ids=source_ref_ids,
            support_classification=ArtifactBlockSupportClassification.TRUSTED_SUPPORT,
            content_data={"rows": _source_rows(source_package.trusted_refs)},
        ),
        ArtifactContentBlock(
            block_id=f"{section.value}_action_list",
            block_kind=ArtifactContentBlockKind.ACTION_LIST,
            title=f"{section_title} action refs",
            body="Action refs remain source-backed draft inputs.",
            source_ref_ids=_source_ref_ids_by_kind(
                source_package.trusted_refs,
                KnowledgeRecordKind.ACTION_PLAN_ITEM,
            ),
            support_classification=ArtifactBlockSupportClassification.TRUSTED_SUPPORT,
            content_data={
                "items": _source_rows_by_kind(
                    source_package.trusted_refs,
                    KnowledgeRecordKind.ACTION_PLAN_ITEM,
                )
            },
        ),
        ArtifactContentBlock(
            block_id=f"{section.value}_assumption_list",
            block_kind=ArtifactContentBlockKind.ASSUMPTION_LIST,
            title=f"{section_title} assumptions",
            body="Assumptions need explicit review before export readiness.",
            assumptions=source_package.assumptions,
            support_classification=ArtifactBlockSupportClassification.ASSUMPTION,
            content_data={"items": list(source_package.assumptions)},
        ),
        ArtifactContentBlock(
            block_id=f"{section.value}_gap_list",
            block_kind=ArtifactContentBlockKind.GAP_LIST,
            title=f"{section_title} gaps and limitations",
            body="Open gaps and limitations block export readiness.",
            gap_ref_ids=gap_ref_ids,
            source_limitation_ref_ids=source_limitation_ref_ids,
            support_classification=ArtifactBlockSupportClassification.NEEDS_REVIEW,
            content_data={
                "gaps": _gap_rows(source_package.gap_refs),
                "source_limitations": _limitation_rows(source_package.source_limitations),
            },
        ),
        ArtifactContentBlock(
            block_id=f"{section.value}_source_appendix",
            block_kind=ArtifactContentBlockKind.SOURCE_APPENDIX,
            title=f"{section_title} source appendix",
            body="Trusted and reviewable refs are separated for artifact review.",
            source_ref_ids=source_ref_ids,
            reviewable_ref_ids=reviewable_ref_ids,
            gap_ref_ids=gap_ref_ids,
            source_limitation_ref_ids=source_limitation_ref_ids,
            support_classification=ArtifactBlockSupportClassification.MIXED_SUPPORT,
            content_data={
                "trusted_refs": _source_rows(source_package.trusted_refs),
                "reviewable_refs": _source_rows(source_package.reviewable_refs),
            },
        ),
    )


def _joined_summaries(refs: tuple[ArtifactSourceRef, ...]) -> str:
    if not refs:
        return "No trusted source refs available."
    return " ".join(ref.summary for ref in refs)


def _source_rows(refs: tuple[ArtifactSourceRef, ...]) -> list[dict[str, str]]:
    return [
        {
            "record_kind": ref.record_kind.value,
            "record_id": ref.record_id,
            "title": ref.title,
            "summary": ref.summary,
            "trust_state": ref.trust_state.value,
            "allowed_use": ref.allowed_use.value,
        }
        for ref in refs
    ]


def _source_ref_ids_by_kind(
    refs: tuple[ArtifactSourceRef, ...],
    record_kind: KnowledgeRecordKind,
) -> tuple[str, ...]:
    return tuple(ref.record_id for ref in refs if ref.record_kind is record_kind)


def _source_rows_by_kind(
    refs: tuple[ArtifactSourceRef, ...],
    record_kind: KnowledgeRecordKind,
) -> list[dict[str, str]]:
    return _source_rows(tuple(ref for ref in refs if ref.record_kind is record_kind))


def _gap_rows(refs: tuple[ArtifactGapRef, ...]) -> list[dict[str, str]]:
    return [
        {
            "record_kind": ref.record_kind.value,
            "record_id": ref.record_id,
            "summary": ref.summary,
            "command_id": ref.command_id,
            "allowed_use": ref.allowed_use.value,
        }
        for ref in refs
    ]


def _limitation_rows(
    refs: tuple[ArtifactSourceLimitationRef, ...],
) -> list[dict[str, str]]:
    return [
        {
            "record_kind": ref.record_kind.value,
            "record_id": ref.record_id,
            "summary": ref.summary,
            "allowed_use": ref.allowed_use.value,
        }
        for ref in refs
    ]
