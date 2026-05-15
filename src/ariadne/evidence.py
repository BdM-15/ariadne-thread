from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class EvidenceKind(StrEnum):
    SOURCE = "source"
    DERIVED = "derived"


class EvidenceItem(BaseModel):
    id: str
    kind: EvidenceKind
    content: str
    source_ref: str | None = None
    opportunity_id: str | None = None
    derived_from_ids: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_traceability(self) -> EvidenceItem:
        if self.kind is EvidenceKind.SOURCE and not self.source_ref:
            raise ValueError("source evidence requires source_ref")
        if self.kind is EvidenceKind.DERIVED and not self.derived_from_ids:
            raise ValueError("derived evidence requires derived_from_ids")
        return self


class LocalEvidenceStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, evidence: EvidenceItem) -> EvidenceItem:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(evidence.id).write_text(
            evidence.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return evidence

    def read(self, evidence_id: str) -> EvidenceItem:
        return EvidenceItem.model_validate_json(
            self._path(evidence_id).read_text(encoding="utf-8")
        )

    def list(self) -> list[EvidenceItem]:
        if not self.root.exists():
            return []
        return [
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        ]

    def _path(self, evidence_id: str) -> Path:
        if not evidence_id or evidence_id != Path(evidence_id).name:
            raise ValueError("evidence_id must be a file-safe identifier")
        return self.root / f"{evidence_id}.json"


def create_source_evidence(
    *,
    content: str,
    source_ref: str,
    opportunity_id: str | None = None,
    evidence_id: str | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        id=evidence_id or f"ev_{uuid4().hex}",
        kind=EvidenceKind.SOURCE,
        content=content,
        source_ref=source_ref,
        opportunity_id=opportunity_id,
    )


def create_derived_evidence(
    *,
    content: str,
    derived_from_ids: list[str] | tuple[str, ...],
    opportunity_id: str | None = None,
    evidence_id: str | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        id=evidence_id or f"ev_{uuid4().hex}",
        kind=EvidenceKind.DERIVED,
        content=content,
        opportunity_id=opportunity_id,
        derived_from_ids=tuple(derived_from_ids),
    )
