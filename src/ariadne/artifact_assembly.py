from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel

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

    @property
    def _source_package_root(self) -> Path:
        return self.root / "source-packages"

    def _source_package_path(self, package_id: str) -> Path:
        if not package_id or package_id != Path(package_id).name:
            raise ValueError("package_id must be a file-safe identifier")
        return self._source_package_root / f"{package_id}.json"


def create_artifact_source_package_from_context(
    *,
    context: OpportunityKnowledgeContextView,
    store: ArtifactAssemblyStore,
    created_at: str,
) -> ArtifactSourcePackage:
    package = build_artifact_source_package_from_context(
        context=context,
        created_at=created_at,
    )
    return store.write_source_package(package)


def build_artifact_source_package_from_context(
    *,
    context: OpportunityKnowledgeContextView,
    created_at: str,
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
