from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from ariadne.evidence import EvidenceItem, LocalEvidenceStore, create_source_evidence
from ariadne.quick_capture import (
    CaptureDraftInferenceSource,
    CaptureIntelligenceDraft,
    CaptureIntelligenceDraftPart,
    CaptureIntelligenceDraftPartType,
    suggest_capture_intelligence_piece_route,
)


class DocumentIntakeStatus(StrEnum):
    READY_FOR_QUICK_CAPTURE = "ready_for_quick_capture"
    PARSER_REQUIRED = "parser_required"


class DocumentIntakeQueueState(StrEnum):
    ACTIVE = "active"
    READY = "ready"
    WAITING = "waiting"


class DocumentIntakeMaterialType(StrEnum):
    GENERIC_SOURCE_MATERIAL = "generic_source_material"
    VISUAL_SOURCE_MATERIAL = "visual_source_material"
    SOLICITATION_DOCUMENT = "solicitation_document"
    UNSUPPORTED_DOCUMENT = "unsupported_document"


class DocumentIntakeContentType(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"
    UNSUPPORTED = "unsupported"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"


class ExtractionBundleReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"


class ExtractionWarningSeverity(StrEnum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class DocumentIntakeAdapterStatus(StrEnum):
    AVAILABLE = "available"
    DEFERRED = "deferred"


class DocumentIntakeAdapterKind(StrEnum):
    PARSER = "parser"
    OCR = "ocr"
    MULTIMODAL = "multimodal"
    RETRIEVAL = "retrieval"


class DocumentIntakeCaptureCandidateType(StrEnum):
    ACTION_PLAN_ITEM = "action_plan_item"
    PACKET_FIELD_ANSWER = "packet_field_answer"
    RISK_REGISTER_ITEM = "risk_register_item"
    CALL_PLAN_SIGNAL = "call_plan_signal"


class DocumentIntakeCandidateReviewState(StrEnum):
    PENDING_REVIEW = "pending_review"
    ROUTED = "routed"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"


class DocumentIntakeCandidate(BaseModel):
    id: str
    filename: str | None = None
    mime_type: str | None = None
    byte_size: int
    material_type: DocumentIntakeMaterialType = (
        DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT
    )
    content_type: DocumentIntakeContentType = DocumentIntakeContentType.UNSUPPORTED
    status: DocumentIntakeStatus = DocumentIntakeStatus.PARSER_REQUIRED
    reason: str
    parser_hint: str
    capability_hint: str
    source_ref: str


class DocumentIntakeAdapterDeclaration(BaseModel):
    id: str
    name: str
    adapter_kind: DocumentIntakeAdapterKind
    status: DocumentIntakeAdapterStatus
    supported_material_types: tuple[DocumentIntakeMaterialType, ...]
    expected_output_contract: str = "ExtractionBundle"
    provenance_fields: tuple[str, ...] = (
        "adapter_name",
        "adapter_version",
        "extraction_method",
        "generated_at",
    )
    capability_hint: str
    deferred_reason: str | None = None
    external_tool_invocation_allowed: bool = False

    @model_validator(mode="after")
    def validate_adapter_declaration(self) -> DocumentIntakeAdapterDeclaration:
        if not self.supported_material_types:
            raise ValueError("adapter declaration requires supported_material_types")
        required_provenance_fields = {
            "adapter_name",
            "adapter_version",
            "extraction_method",
            "generated_at",
        }
        if not required_provenance_fields.issubset(self.provenance_fields):
            raise ValueError("adapter declaration missing provenance fields")
        if self.status is DocumentIntakeAdapterStatus.DEFERRED:
            if not self.deferred_reason:
                raise ValueError("deferred adapter declaration requires reason")
            if self.external_tool_invocation_allowed:
                raise ValueError("deferred adapter cannot invoke external tools")
        return self


class UploadedSourceMaterial(BaseModel):
    status: DocumentIntakeStatus
    content_type: DocumentIntakeContentType
    filename: str | None = None
    mime_type: str | None = None
    byte_size: int
    source_ref: str
    material_type: DocumentIntakeMaterialType | None = None
    text: str | None = None
    warnings: tuple[str, ...] = ()
    intake_candidate: DocumentIntakeCandidate | None = None
    capability_hint: str | None = None


class DocumentIntakeRecord(BaseModel):
    id: str
    source_ref: str
    filename: str | None = None
    mime_type: str | None = None
    byte_size: int
    material_type: DocumentIntakeMaterialType | None = None
    content_type: DocumentIntakeContentType
    status: DocumentIntakeStatus
    queue_state: DocumentIntakeQueueState | None = None
    opportunity_id: str | None = None
    source_provenance: dict[str, str] = Field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    capability_hint: str = "Document is recorded for intake."
    extraction_bundle_id: str | None = None
    extraction_status: ExtractionStatus | None = None
    extraction_review_status: ExtractionBundleReviewStatus | None = None
    extraction_warning_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def derive_queue_state(self) -> DocumentIntakeRecord:
        if self.material_type is None:
            self.material_type = (
                DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT
                if self.status is DocumentIntakeStatus.PARSER_REQUIRED
                else DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL
            )
        if self.queue_state is None:
            self.queue_state = (
                DocumentIntakeQueueState.WAITING
                if self.status is DocumentIntakeStatus.PARSER_REQUIRED
                else DocumentIntakeQueueState.READY
            )
        return self

    def with_extraction_bundle(
        self,
        bundle: ExtractionBundle,
    ) -> DocumentIntakeRecord:
        if bundle.document_id != self.id:
            raise ValueError("extraction bundle must belong to intake record")
        return self.model_copy(
            update={
                "extraction_bundle_id": bundle.id,
                "extraction_status": bundle.extraction_status,
                "extraction_review_status": bundle.review_status,
                "extraction_warning_count": len(bundle.warnings),
                "updated_at": datetime.now(UTC),
            }
        )


class ParserProvenance(BaseModel):
    adapter_name: str
    adapter_version: str
    extraction_method: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SourceSpan(BaseModel):
    id: str
    document_id: str
    span_type: str = "text"
    text: str
    start_offset: int
    end_offset: int
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_offsets(self) -> SourceSpan:
        if self.end_offset < self.start_offset:
            raise ValueError("source span end_offset must be after start_offset")
        return self


class EntityCandidate(BaseModel):
    id: str
    entity_type: str
    text: str
    source_span_ids: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_source_trace(self) -> EntityCandidate:
        if not self.source_span_ids:
            raise ValueError("entity candidate requires source_span_ids")
        return self


class RelationshipCandidate(BaseModel):
    id: str
    relationship_type: str
    source_entity_id: str
    target_entity_id: str
    source_span_ids: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_relationship_trace(self) -> RelationshipCandidate:
        if self.source_entity_id == self.target_entity_id:
            raise ValueError("relationship candidate must connect two entities")
        if not self.source_span_ids:
            raise ValueError("relationship candidate requires source_span_ids")
        return self


class ExtractionWarning(BaseModel):
    id: str
    warning_type: str
    message: str
    affected_span_ids: tuple[str, ...] = ()
    severity: ExtractionWarningSeverity = ExtractionWarningSeverity.INFO


class ExtractionBundle(BaseModel):
    id: str
    document_id: str
    source_ref: str
    filename: str | None = None
    mime_type: str | None = None
    byte_size: int
    material_type: DocumentIntakeMaterialType
    content_type: DocumentIntakeContentType
    opportunity_id: str | None = None
    parser_provenance: ParserProvenance
    extraction_status: ExtractionStatus = ExtractionStatus.COMPLETE
    review_status: ExtractionBundleReviewStatus = (
        ExtractionBundleReviewStatus.PENDING_REVIEW
    )
    confidence: float = Field(ge=0, le=1)
    source_spans: tuple[SourceSpan, ...] = ()
    entity_candidates: tuple[EntityCandidate, ...] = ()
    relationship_candidates: tuple[RelationshipCandidate, ...] = ()
    warnings: tuple[ExtractionWarning, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_candidate_trace(self) -> ExtractionBundle:
        span_ids = {span.id for span in self.source_spans}
        entity_ids = {candidate.id for candidate in self.entity_candidates}
        for candidate in self.entity_candidates:
            missing_span_ids = set(candidate.source_span_ids) - span_ids
            if missing_span_ids:
                raise ValueError("entity candidate references unknown source span")
        for relationship in self.relationship_candidates:
            if relationship.source_entity_id not in entity_ids:
                raise ValueError(
                    "relationship candidate references unknown source entity"
                )
            if relationship.target_entity_id not in entity_ids:
                raise ValueError(
                    "relationship candidate references unknown target entity"
                )
            missing_span_ids = set(relationship.source_span_ids) - span_ids
            if missing_span_ids:
                raise ValueError(
                    "relationship candidate references unknown source span"
                )
        for warning in self.warnings:
            missing_span_ids = set(warning.affected_span_ids) - span_ids
            if missing_span_ids:
                raise ValueError("extraction warning references unknown source span")
        return self


class AcceptedDocumentEvidenceLink(BaseModel):
    id: str
    intake_record_id: str
    extraction_bundle_id: str
    source_span_ids: tuple[str, ...]
    evidence_id: str
    source_ref: str
    parser_adapter: str
    parser_version: str
    parser_method: str
    confidence: float = Field(ge=0, le=1)
    warnings: tuple[str, ...] = ()
    reviewer_rationale: str
    draft_part_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_review_trace(self) -> AcceptedDocumentEvidenceLink:
        if not self.source_span_ids:
            raise ValueError("accepted evidence link requires source_span_ids")
        if not self.reviewer_rationale.strip():
            raise ValueError("accepted evidence link requires reviewer_rationale")
        return self


class AcceptedSourceSpanEvidenceResult(BaseModel):
    evidence: EvidenceItem
    accepted_link: AcceptedDocumentEvidenceLink
    duplicate: bool = False


class DocumentIntakeCaptureCandidate(BaseModel):
    id: str
    candidate_type: DocumentIntakeCaptureCandidateType
    title: str
    content: str
    target_workflow: str
    recommendation: str
    rationale: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    review_state: DocumentIntakeCandidateReviewState = (
        DocumentIntakeCandidateReviewState.PENDING_REVIEW
    )
    trusted_output_written: bool = False
    source_ref: str
    source_intake_record_id: str
    source_extraction_bundle_id: str
    source_draft_id: str
    source_draft_part_id: str
    source_span_ids: tuple[str, ...]
    suggested_skill_chain: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_candidate_trace(self) -> DocumentIntakeCaptureCandidate:
        if not self.source_span_ids:
            raise ValueError("capture candidate requires source_span_ids")
        if self.trusted_output_written and self.review_state is not (
            DocumentIntakeCandidateReviewState.ACCEPTED
        ):
            raise ValueError("trusted output requires accepted review state")
        return self


class KnowledgeNoteProjection(BaseModel):
    id: str
    title: str
    summary: str
    markdown_content: str
    source_intake_record_id: str
    source_extraction_bundle_id: str
    source_ref: str
    evidence_ids: tuple[str, ...]
    accepted_evidence_link_ids: tuple[str, ...]
    source_span_ids: tuple[str, ...]
    parser_adapter: str
    parser_version: str
    parser_method: str
    opportunity_id: str | None = None
    is_source_of_truth: bool = False
    can_overwrite_structured_knowledge: bool = False
    generated_from_accepted_evidence_count: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_projection_guardrails(self) -> KnowledgeNoteProjection:
        if not self.evidence_ids:
            raise ValueError("knowledge note projection requires evidence_ids")
        if not self.accepted_evidence_link_ids:
            raise ValueError(
                "knowledge note projection requires accepted_evidence_link_ids"
            )
        if not self.source_span_ids:
            raise ValueError("knowledge note projection requires source_span_ids")
        if self.is_source_of_truth:
            raise ValueError("knowledge note projection cannot be source of truth")
        if self.can_overwrite_structured_knowledge:
            raise ValueError(
                "knowledge note projection cannot overwrite structured knowledge"
            )
        return self


class DocumentIntakeStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, record: DocumentIntakeRecord) -> DocumentIntakeRecord:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(record.id).write_text(
            record.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return record

    def read(self, record_id: str) -> DocumentIntakeRecord:
        return DocumentIntakeRecord.model_validate_json(
            self._path(record_id).read_text(encoding="utf-8")
        )

    def list(
        self,
        *,
        opportunity_id: str | None = None,
        status: DocumentIntakeStatus | None = None,
    ) -> list[DocumentIntakeRecord]:
        if not self.root.exists():
            return []
        records = [
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        ]
        if opportunity_id is not None:
            records = [
                record for record in records if record.opportunity_id == opportunity_id
            ]
        if status is not None:
            records = [record for record in records if record.status is status]
        return records

    def write_extraction_bundle(self, bundle: ExtractionBundle) -> ExtractionBundle:
        self._bundle_root.mkdir(parents=True, exist_ok=True)
        self._bundle_path(bundle.id).write_text(
            bundle.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return bundle

    def read_extraction_bundle(self, bundle_id: str) -> ExtractionBundle:
        return ExtractionBundle.model_validate_json(
            self._bundle_path(bundle_id).read_text(encoding="utf-8")
        )

    def list_extraction_bundles(
        self,
        *,
        document_id: str | None = None,
    ) -> list[ExtractionBundle]:
        if not self._bundle_root.exists():
            return []
        bundles = [
            self.read_extraction_bundle(path.name.removesuffix(".json"))
            for path in sorted(self._bundle_root.glob("*.json"))
        ]
        if document_id is not None:
            bundles = [
                bundle for bundle in bundles if bundle.document_id == document_id
            ]
        return bundles

    def write_accepted_evidence_link(
        self,
        link: AcceptedDocumentEvidenceLink,
    ) -> AcceptedDocumentEvidenceLink:
        self._accepted_evidence_root.mkdir(parents=True, exist_ok=True)
        self._accepted_evidence_path(link.id).write_text(
            link.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return link

    def read_accepted_evidence_link(
        self,
        link_id: str,
    ) -> AcceptedDocumentEvidenceLink:
        return AcceptedDocumentEvidenceLink.model_validate_json(
            self._accepted_evidence_path(link_id).read_text(encoding="utf-8")
        )

    def list_accepted_evidence_links(
        self,
        *,
        bundle_id: str | None = None,
        intake_record_id: str | None = None,
        evidence_id: str | None = None,
    ) -> list[AcceptedDocumentEvidenceLink]:
        if not self._accepted_evidence_root.exists():
            return []
        links = [
            self.read_accepted_evidence_link(path.name.removesuffix(".json"))
            for path in sorted(self._accepted_evidence_root.glob("*.json"))
        ]
        if bundle_id is not None:
            links = [link for link in links if link.extraction_bundle_id == bundle_id]
        if intake_record_id is not None:
            links = [
                link for link in links if link.intake_record_id == intake_record_id
            ]
        if evidence_id is not None:
            links = [link for link in links if link.evidence_id == evidence_id]
        return links

    def write_capture_candidate(
        self,
        candidate: DocumentIntakeCaptureCandidate,
    ) -> DocumentIntakeCaptureCandidate:
        self._capture_candidate_root.mkdir(parents=True, exist_ok=True)
        self._capture_candidate_path(candidate.id).write_text(
            candidate.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return candidate

    def read_capture_candidate(
        self,
        candidate_id: str,
    ) -> DocumentIntakeCaptureCandidate:
        return DocumentIntakeCaptureCandidate.model_validate_json(
            self._capture_candidate_path(candidate_id).read_text(encoding="utf-8")
        )

    def list_capture_candidates(
        self,
        *,
        bundle_id: str | None = None,
        intake_record_id: str | None = None,
        candidate_type: DocumentIntakeCaptureCandidateType | None = None,
        review_state: DocumentIntakeCandidateReviewState | None = None,
    ) -> list[DocumentIntakeCaptureCandidate]:
        if not self._capture_candidate_root.exists():
            return []
        candidates = [
            self.read_capture_candidate(path.name.removesuffix(".json"))
            for path in sorted(self._capture_candidate_root.glob("*.json"))
        ]
        if bundle_id is not None:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.source_extraction_bundle_id == bundle_id
            ]
        if intake_record_id is not None:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.source_intake_record_id == intake_record_id
            ]
        if candidate_type is not None:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.candidate_type is candidate_type
            ]
        if review_state is not None:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.review_state is review_state
            ]
        return candidates

    def write_knowledge_note_projection(
        self,
        projection: KnowledgeNoteProjection,
    ) -> KnowledgeNoteProjection:
        self._knowledge_note_projection_root.mkdir(parents=True, exist_ok=True)
        self._knowledge_note_projection_path(projection.id).write_text(
            projection.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return projection

    def read_knowledge_note_projection(
        self,
        projection_id: str,
    ) -> KnowledgeNoteProjection:
        return KnowledgeNoteProjection.model_validate_json(
            self._knowledge_note_projection_path(projection_id).read_text(
                encoding="utf-8"
            )
        )

    def list_knowledge_note_projections(
        self,
        *,
        bundle_id: str | None = None,
        intake_record_id: str | None = None,
        evidence_id: str | None = None,
    ) -> list[KnowledgeNoteProjection]:
        if not self._knowledge_note_projection_root.exists():
            return []
        projections = [
            self.read_knowledge_note_projection(path.name.removesuffix(".json"))
            for path in sorted(self._knowledge_note_projection_root.glob("*.json"))
        ]
        if bundle_id is not None:
            projections = [
                projection
                for projection in projections
                if projection.source_extraction_bundle_id == bundle_id
            ]
        if intake_record_id is not None:
            projections = [
                projection
                for projection in projections
                if projection.source_intake_record_id == intake_record_id
            ]
        if evidence_id is not None:
            projections = [
                projection
                for projection in projections
                if evidence_id in projection.evidence_ids
            ]
        return projections

    def _path(self, record_id: str) -> Path:
        if not record_id or record_id != Path(record_id).name:
            raise ValueError("record_id must be a file-safe identifier")
        return self.root / f"{record_id}.json"

    @property
    def _bundle_root(self) -> Path:
        return self.root / "extraction-bundles"

    def _bundle_path(self, bundle_id: str) -> Path:
        if not bundle_id or bundle_id != Path(bundle_id).name:
            raise ValueError("bundle_id must be a file-safe identifier")
        return self._bundle_root / f"{bundle_id}.json"

    @property
    def _accepted_evidence_root(self) -> Path:
        return self.root / "accepted-evidence-links"

    def _accepted_evidence_path(self, link_id: str) -> Path:
        if not link_id or link_id != Path(link_id).name:
            raise ValueError("link_id must be a file-safe identifier")
        return self._accepted_evidence_root / f"{link_id}.json"

    @property
    def _capture_candidate_root(self) -> Path:
        return self.root / "capture-candidates"

    def _capture_candidate_path(self, candidate_id: str) -> Path:
        if not candidate_id or candidate_id != Path(candidate_id).name:
            raise ValueError("candidate_id must be a file-safe identifier")
        return self._capture_candidate_root / f"{candidate_id}.json"

    @property
    def _knowledge_note_projection_root(self) -> Path:
        return self.root / "knowledge-note-projections"

    def _knowledge_note_projection_path(self, projection_id: str) -> Path:
        if not projection_id or projection_id != Path(projection_id).name:
            raise ValueError("projection_id must be a file-safe identifier")
        return self._knowledge_note_projection_root / f"{projection_id}.json"


def create_document_intake_record(
    source_material: UploadedSourceMaterial,
    *,
    opportunity_id: str | None = None,
    record_id: str | None = None,
    source_provenance: dict[str, str] | None = None,
) -> DocumentIntakeRecord:
    return DocumentIntakeRecord(
        id=record_id or source_material.source_ref.replace(":", "_"),
        source_ref=source_material.source_ref,
        filename=source_material.filename,
        mime_type=source_material.mime_type,
        byte_size=source_material.byte_size,
        material_type=source_material.material_type,
        content_type=source_material.content_type,
        status=source_material.status,
        opportunity_id=opportunity_id,
        source_provenance=source_provenance or {},
        warnings=source_material.warnings,
        capability_hint=source_material.capability_hint
        or "Document is recorded for intake.",
    )


def list_document_intake_adapter_declarations(
    *,
    material_type: DocumentIntakeMaterialType | None = None,
    status: DocumentIntakeAdapterStatus | None = None,
) -> tuple[DocumentIntakeAdapterDeclaration, ...]:
    declarations = _DOCUMENT_INTAKE_ADAPTER_DECLARATIONS
    if material_type is not None:
        declarations = tuple(
            declaration
            for declaration in declarations
            if material_type in declaration.supported_material_types
        )
    if status is not None:
        declarations = tuple(
            declaration for declaration in declarations if declaration.status is status
        )
    return declarations


def create_generic_extraction_bundle(
    record: DocumentIntakeRecord,
    source_material: UploadedSourceMaterial,
    *,
    bundle_id: str | None = None,
) -> ExtractionBundle:
    if record.material_type is not DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL:
        raise ValueError("generic extraction requires generic source material")
    if source_material.text is None:
        raise ValueError("generic extraction requires readable source text")

    resolved_bundle_id = bundle_id or f"bundle_{record.id}"
    source_spans = _extract_text_source_spans(
        source_material.text,
        document_id=record.id,
        bundle_id=resolved_bundle_id,
    )
    entity_candidates = _extract_entity_candidates(
        source_spans,
        bundle_id=resolved_bundle_id,
    )
    relationship_candidates = _extract_relationship_candidates(
        source_spans,
        entity_candidates,
        bundle_id=resolved_bundle_id,
    )
    warnings = _extraction_warnings_for_generic_material(
        source_material,
        source_spans,
        entity_candidates,
        bundle_id=resolved_bundle_id,
    )
    return ExtractionBundle(
        id=resolved_bundle_id,
        document_id=record.id,
        source_ref=record.source_ref,
        filename=record.filename,
        mime_type=record.mime_type,
        byte_size=record.byte_size,
        material_type=DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL,
        content_type=record.content_type,
        opportunity_id=record.opportunity_id,
        parser_provenance=ParserProvenance(
            adapter_name="ariadne.generic_text_extractor",
            adapter_version="0.1",
            extraction_method="deterministic_text_span_heuristics",
        ),
        confidence=_bundle_confidence(source_spans, entity_candidates),
        source_spans=source_spans,
        entity_candidates=entity_candidates,
        relationship_candidates=relationship_candidates,
        warnings=warnings,
    )


def create_capture_intelligence_draft_from_extraction_bundle(
    bundle: ExtractionBundle,
) -> CaptureIntelligenceDraft:
    intelligence_pieces = _build_extraction_intelligence_pieces(bundle)
    inferred_claims = tuple(
        piece.content
        for piece in intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.INFERRED_CLAIM
    )

    likely_risks = tuple(
        piece.content
        for piece in intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.LIKELY_RISK
    )
    discriminator_candidates = tuple(
        piece.content
        for piece in intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE
    )
    packet_implications = tuple(
        piece.content
        for piece in intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.PACKET_IMPLICATION
    )
    action_candidates = tuple(
        piece.content
        for piece in intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.ACTION_CANDIDATE
    )
    follow_up_questions = tuple(
        piece.content
        for piece in intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION
    )
    assumptions = _extraction_draft_assumptions(bundle)
    confidence_notes = _extraction_draft_confidence_notes(bundle)
    return CaptureIntelligenceDraft(
        id=f"draft_{bundle.id}",
        raw_item_id=bundle.document_id,
        opportunity_id=bundle.opportunity_id,
        raw_source_content=_bundle_raw_source_preview(bundle),
        polished_capture=_extraction_polished_capture(
            inferred_claims=inferred_claims,
            likely_risks=likely_risks,
            packet_implications=packet_implications,
            action_candidates=action_candidates,
            follow_up_questions=follow_up_questions,
        ),
        inferred_claims=inferred_claims
        or ("Document extraction needs reviewer classification.",),
        assumptions=assumptions,
        confidence_notes=confidence_notes,
        likely_risks=likely_risks,
        discriminator_candidates=discriminator_candidates,
        packet_implications=packet_implications,
        action_candidates=action_candidates,
        gaps=_extraction_draft_gaps(bundle),
        follow_up_questions=follow_up_questions,
        intelligence_pieces=intelligence_pieces,
        inference_source=CaptureDraftInferenceSource.HEURISTIC,
        extraction_bundle_id=bundle.id,
        extraction_document_id=bundle.document_id,
        extracted_source_span_ids=tuple(span.id for span in bundle.source_spans),
        extraction_entity_type_refs=tuple(
            sorted({candidate.entity_type for candidate in bundle.entity_candidates})
        ),
        extraction_warnings_summarized=_summarize_extraction_warnings(bundle),
    )


def accept_source_spans_to_evidence(
    bundle: ExtractionBundle,
    *,
    source_span_ids: tuple[str, ...] | list[str],
    reviewer_rationale: str,
    intake_store: DocumentIntakeStore,
    evidence_store: LocalEvidenceStore,
    draft_part_id: str | None = None,
    evidence_content: str | None = None,
    opportunity_id: str | None = None,
    evidence_id: str | None = None,
) -> AcceptedSourceSpanEvidenceResult:
    if not reviewer_rationale.strip():
        raise ValueError("reviewer_rationale is required to accept source spans")
    accepted_span_ids = _unique_source_span_ids(source_span_ids)
    selected_spans = _selected_source_spans(bundle, accepted_span_ids)
    exact_existing_link = _find_exact_accepted_evidence_link(
        intake_store,
        bundle=bundle,
        source_span_ids=accepted_span_ids,
    )
    if exact_existing_link is not None:
        return AcceptedSourceSpanEvidenceResult(
            evidence=evidence_store.read(exact_existing_link.evidence_id),
            accepted_link=exact_existing_link,
            duplicate=True,
        )
    overlapping_link = _find_overlapping_accepted_evidence_link(
        intake_store,
        bundle=bundle,
        source_span_ids=accepted_span_ids,
    )
    if overlapping_link is not None:
        raise ValueError(
            "source span already accepted as evidence: "
            f"{', '.join(overlapping_link.source_span_ids)}"
        )

    warnings = _source_span_warning_messages(bundle, accepted_span_ids)
    confidence = _accepted_source_span_confidence(selected_spans)
    evidence = create_source_evidence(
        content=evidence_content or "\n".join(span.text for span in selected_spans),
        source_ref=bundle.source_ref,
        opportunity_id=opportunity_id or bundle.opportunity_id,
        evidence_id=evidence_id,
        raw_item_id=bundle.document_id,
        draft_id=f"draft_{bundle.id}",
        source_intake_record_id=bundle.document_id,
        source_extraction_bundle_id=bundle.id,
        source_span_ids=accepted_span_ids,
        parser_adapter=bundle.parser_provenance.adapter_name,
        parser_version=bundle.parser_provenance.adapter_version,
        parser_method=bundle.parser_provenance.extraction_method,
        source_confidence=confidence,
        source_warnings=warnings,
        rationale=(reviewer_rationale,),
    )
    evidence_store.write(evidence)
    accepted_link = AcceptedDocumentEvidenceLink(
        id=_accepted_evidence_link_id(bundle.id, accepted_span_ids),
        intake_record_id=bundle.document_id,
        extraction_bundle_id=bundle.id,
        source_span_ids=accepted_span_ids,
        evidence_id=evidence.id,
        source_ref=bundle.source_ref,
        parser_adapter=bundle.parser_provenance.adapter_name,
        parser_version=bundle.parser_provenance.adapter_version,
        parser_method=bundle.parser_provenance.extraction_method,
        confidence=confidence,
        warnings=warnings,
        reviewer_rationale=reviewer_rationale,
        draft_part_id=draft_part_id,
    )
    intake_store.write_accepted_evidence_link(accepted_link)
    return AcceptedSourceSpanEvidenceResult(
        evidence=evidence,
        accepted_link=accepted_link,
    )


def _unique_source_span_ids(
    source_span_ids: tuple[str, ...] | list[str],
) -> tuple[str, ...]:
    unique_ids: list[str] = []
    for span_id in source_span_ids:
        if span_id and span_id not in unique_ids:
            unique_ids.append(span_id)
    if not unique_ids:
        raise ValueError("source_span_ids are required to accept source spans")
    return tuple(unique_ids)


def _selected_source_spans(
    bundle: ExtractionBundle,
    source_span_ids: tuple[str, ...],
) -> tuple[SourceSpan, ...]:
    selected_spans = tuple(
        span for span in bundle.source_spans if span.id in source_span_ids
    )
    missing_span_ids = set(source_span_ids) - {span.id for span in selected_spans}
    if missing_span_ids:
        raise ValueError(
            "unknown source span id(s): " + ", ".join(sorted(missing_span_ids))
        )
    return selected_spans


def _find_exact_accepted_evidence_link(
    intake_store: DocumentIntakeStore,
    *,
    bundle: ExtractionBundle,
    source_span_ids: tuple[str, ...],
) -> AcceptedDocumentEvidenceLink | None:
    for link in intake_store.list_accepted_evidence_links(bundle_id=bundle.id):
        if link.source_span_ids == source_span_ids:
            return link
    return None


def _find_overlapping_accepted_evidence_link(
    intake_store: DocumentIntakeStore,
    *,
    bundle: ExtractionBundle,
    source_span_ids: tuple[str, ...],
) -> AcceptedDocumentEvidenceLink | None:
    candidate_span_ids = set(source_span_ids)
    for link in intake_store.list_accepted_evidence_links(bundle_id=bundle.id):
        if candidate_span_ids.intersection(link.source_span_ids):
            return link
    return None


def _source_span_warning_messages(
    bundle: ExtractionBundle,
    source_span_ids: tuple[str, ...],
) -> tuple[str, ...]:
    accepted_span_ids = set(source_span_ids)
    return tuple(
        warning.message
        for warning in bundle.warnings
        if not warning.affected_span_ids
        or accepted_span_ids.intersection(warning.affected_span_ids)
    )


def _accepted_source_span_confidence(spans: tuple[SourceSpan, ...]) -> float:
    return round(sum(span.confidence for span in spans) / len(spans), 2)


def _accepted_evidence_link_id(
    bundle_id: str,
    source_span_ids: tuple[str, ...],
) -> str:
    digest = sha256((bundle_id + "\0" + "\0".join(source_span_ids)).encode())
    return f"accepted_{digest.hexdigest()[:16]}"


def create_knowledge_note_projection_from_accepted_evidence(
    bundle: ExtractionBundle,
    *,
    intake_store: DocumentIntakeStore,
    evidence_store: LocalEvidenceStore,
    projection_id: str | None = None,
) -> KnowledgeNoteProjection | None:
    accepted_links = intake_store.list_accepted_evidence_links(bundle_id=bundle.id)
    if not accepted_links:
        return None
    evidence_items = tuple(
        evidence_store.read(link.evidence_id) for link in accepted_links
    )
    source_span_ids = _unique_projection_source_span_ids(accepted_links)
    evidence_ids = tuple(link.evidence_id for link in accepted_links)
    markdown_content = _render_knowledge_note_projection_markdown(
        bundle,
        accepted_links=tuple(accepted_links),
        evidence_items=evidence_items,
    )
    return KnowledgeNoteProjection(
        id=projection_id
        or _knowledge_note_projection_id(
            bundle.id, tuple(link.id for link in accepted_links)
        ),
        title=_knowledge_note_projection_title(bundle),
        summary=_knowledge_note_projection_summary(evidence_items),
        markdown_content=markdown_content,
        source_intake_record_id=bundle.document_id,
        source_extraction_bundle_id=bundle.id,
        source_ref=bundle.source_ref,
        evidence_ids=evidence_ids,
        accepted_evidence_link_ids=tuple(link.id for link in accepted_links),
        source_span_ids=source_span_ids,
        parser_adapter=bundle.parser_provenance.adapter_name,
        parser_version=bundle.parser_provenance.adapter_version,
        parser_method=bundle.parser_provenance.extraction_method,
        opportunity_id=bundle.opportunity_id,
        generated_from_accepted_evidence_count=len(accepted_links),
    )


def _render_knowledge_note_projection_markdown(
    bundle: ExtractionBundle,
    *,
    accepted_links: tuple[AcceptedDocumentEvidenceLink, ...],
    evidence_items: tuple[EvidenceItem, ...],
) -> str:
    title = _knowledge_note_projection_title(bundle)
    lines = [
        f"# {title}",
        "",
        "> Structured Ariadne records remain the source of truth. This one-way note cannot overwrite evidence, intake records, or extraction bundles.",
        "",
        "## Provenance",
        f"- Intake record: {bundle.document_id}",
        f"- Extraction bundle: {bundle.id}",
        f"- Source: {bundle.source_ref}",
        f"- Parser: {bundle.parser_provenance.adapter_name} {bundle.parser_provenance.adapter_version} ({bundle.parser_provenance.extraction_method})",
        "",
        "## Accepted Evidence",
    ]
    for index, (link, evidence) in enumerate(zip(accepted_links, evidence_items), 1):
        warnings = "; ".join(link.warnings) if link.warnings else "none"
        source_spans = ", ".join(link.source_span_ids)
        lines.extend(
            [
                "",
                f"### {index}. Evidence {evidence.id}",
                "",
                evidence.content,
                "",
                f"- Accepted evidence link: {link.id}",
                f"- Source spans: {source_spans}",
                f"- Confidence: {link.confidence:.2f}",
                f"- Reviewer rationale: {link.reviewer_rationale}",
                f"- Warnings: {warnings}",
            ]
        )
    return "\n".join(lines)


def _knowledge_note_projection_title(bundle: ExtractionBundle) -> str:
    source_label = bundle.filename or bundle.source_ref
    return f"Knowledge Note Projection: {source_label}"


def _knowledge_note_projection_summary(
    evidence_items: tuple[EvidenceItem, ...],
) -> str:
    summary_source = " ".join(evidence.content.strip() for evidence in evidence_items)
    if len(summary_source) <= 220:
        return summary_source
    return summary_source[:217].rstrip() + "..."


def _unique_projection_source_span_ids(
    accepted_links: list[AcceptedDocumentEvidenceLink],
) -> tuple[str, ...]:
    source_span_ids: list[str] = []
    for link in accepted_links:
        for source_span_id in link.source_span_ids:
            if source_span_id not in source_span_ids:
                source_span_ids.append(source_span_id)
    return tuple(source_span_ids)


def _knowledge_note_projection_id(
    bundle_id: str,
    accepted_link_ids: tuple[str, ...],
) -> str:
    digest = sha256((bundle_id + "\0" + "\0".join(accepted_link_ids)).encode())
    return f"note_{digest.hexdigest()[:16]}"


def create_review_gated_capture_candidates_from_extraction_bundle(
    bundle: ExtractionBundle,
) -> tuple[DocumentIntakeCaptureCandidate, ...]:
    draft = create_capture_intelligence_draft_from_extraction_bundle(bundle)
    candidates: list[DocumentIntakeCaptureCandidate] = []
    seen_keys: set[tuple[DocumentIntakeCaptureCandidateType, str]] = set()
    for piece in draft.intelligence_pieces:
        for candidate_type in _candidate_types_for_draft_part(piece):
            key = (candidate_type, piece.id)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            candidates.append(
                _create_review_gated_capture_candidate(
                    bundle,
                    draft_id=draft.id,
                    piece=piece,
                    candidate_type=candidate_type,
                    sequence=len(candidates) + 1,
                )
            )
    return tuple(candidates)


def _create_review_gated_capture_candidate(
    bundle: ExtractionBundle,
    *,
    draft_id: str,
    piece: CaptureIntelligenceDraftPart,
    candidate_type: DocumentIntakeCaptureCandidateType,
    sequence: int,
) -> DocumentIntakeCaptureCandidate:
    target_workflow, recommendation = _candidate_workflow_and_recommendation(
        candidate_type,
        piece,
    )
    return DocumentIntakeCaptureCandidate(
        id=_capture_candidate_id(bundle.id, candidate_type, piece.id, sequence),
        candidate_type=candidate_type,
        title=_capture_candidate_title(candidate_type, piece),
        content=piece.content,
        target_workflow=target_workflow,
        recommendation=recommendation,
        rationale=_capture_candidate_rationale(bundle, piece),
        confidence=_confidence_from_draft_part(piece),
        source_ref=bundle.source_ref,
        source_intake_record_id=bundle.document_id,
        source_extraction_bundle_id=bundle.id,
        source_draft_id=draft_id,
        source_draft_part_id=piece.id,
        source_span_ids=piece.source_span_ids,
        suggested_skill_chain=piece.suggested_skill_chain,
    )


def _candidate_types_for_draft_part(
    piece: CaptureIntelligenceDraftPart,
) -> tuple[DocumentIntakeCaptureCandidateType, ...]:
    candidate_types: list[DocumentIntakeCaptureCandidateType] = []
    if piece.part_type is CaptureIntelligenceDraftPartType.ACTION_CANDIDATE:
        candidate_types.append(DocumentIntakeCaptureCandidateType.ACTION_PLAN_ITEM)
    if piece.part_type is CaptureIntelligenceDraftPartType.PACKET_IMPLICATION:
        candidate_types.append(DocumentIntakeCaptureCandidateType.PACKET_FIELD_ANSWER)
    if piece.part_type is CaptureIntelligenceDraftPartType.LIKELY_RISK:
        candidate_types.append(DocumentIntakeCaptureCandidateType.RISK_REGISTER_ITEM)
    if piece.part_type is CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION:
        candidate_types.append(DocumentIntakeCaptureCandidateType.CALL_PLAN_SIGNAL)
    if piece.part_type in {
        CaptureIntelligenceDraftPartType.ACTION_CANDIDATE,
        CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
    } and _looks_like_customer_engagement_signal(piece.content):
        candidate_types.append(DocumentIntakeCaptureCandidateType.CALL_PLAN_SIGNAL)
    return tuple(candidate_types)


def _candidate_workflow_and_recommendation(
    candidate_type: DocumentIntakeCaptureCandidateType,
    piece: CaptureIntelligenceDraftPart,
) -> tuple[str, str]:
    if candidate_type is DocumentIntakeCaptureCandidateType.ACTION_PLAN_ITEM:
        return (
            "capture_action_plan",
            "Review as a candidate Capture Action Plan item before assigning work.",
        )
    if candidate_type is DocumentIntakeCaptureCandidateType.PACKET_FIELD_ANSWER:
        return (
            "living_briefing_packet",
            "Review as a candidate packet field answer or evidence-backed packet gap update.",
        )
    if candidate_type is DocumentIntakeCaptureCandidateType.RISK_REGISTER_ITEM:
        return (
            "risk_register",
            "Review as a candidate Risk Register item before treating it as pursuit risk.",
        )
    return (
        "call_plan",
        "Review as a candidate Call Plan signal before preparing customer engagement.",
    )


def _capture_candidate_title(
    candidate_type: DocumentIntakeCaptureCandidateType,
    piece: CaptureIntelligenceDraftPart,
) -> str:
    label = candidate_type.value.replace("_", " ").title()
    return f"{label}: {_candidate_text(piece.content)}"


def _capture_candidate_rationale(
    bundle: ExtractionBundle,
    piece: CaptureIntelligenceDraftPart,
) -> str:
    return (
        f"Generated from document-derived draft part {piece.id}; "
        f"bundle confidence {bundle.confidence:.2f}; trusted output still requires review."
    )


def _confidence_from_draft_part(piece: CaptureIntelligenceDraftPart) -> float | None:
    for note in piece.confidence_notes:
        if "Extraction candidate confidence" not in note:
            continue
        confidence_text = note.split("Extraction candidate confidence", 1)[1]
        confidence_value = confidence_text.split(";", 1)[0].strip()
        try:
            return float(confidence_value)
        except ValueError:
            return None
    return None


def _looks_like_customer_engagement_signal(content: str) -> bool:
    lowered_content = content.lower()
    return any(
        term in lowered_content
        for term in (
            "customer",
            "decision maker",
            "follow up",
            "meeting",
            "pm",
            "stakeholder",
        )
    )


def _capture_candidate_id(
    bundle_id: str,
    candidate_type: DocumentIntakeCaptureCandidateType,
    draft_part_id: str,
    sequence: int,
) -> str:
    digest = sha256(
        f"{bundle_id}\0{candidate_type.value}\0{draft_part_id}\0{sequence}".encode()
    )
    return f"candidate_{digest.hexdigest()[:16]}"


_TEXT_EXTENSIONS = {".txt", ".text"}
_MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown"}
_VISUAL_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
_SOLICITATION_TERMS = (
    "amendment",
    "draft-rfp",
    "draft_rfp",
    "final-rfp",
    "final_rfp",
    "requirements-attachment",
    "requirements_attachment",
    "rfi",
    "rfp",
    "sources-sought",
    "sources_sought",
)
_TEXT_MIME_TYPES = {"text/plain"}
_MARKDOWN_MIME_TYPES = {"text/markdown", "text/x-markdown"}
_GENERIC_ENTITY_KEYWORDS = {
    "customer": ("customer", "buyer", "agency", "aflcmc"),
    "organization": ("incumbent", "partner", "prime", "team"),
    "stakeholder": ("decision maker", "pm", "program manager", "stakeholder"),
    "opportunity": ("opportunity", "pursuit", "recompete"),
    "need": ("need", "needs", "requirement", "requires"),
    "milestone": ("date", "deadline", "due", "milestone"),
    "risk": ("concern", "risk", "weak", "weakness"),
    "commitment": ("action", "commitment", "follow up", "follow-up"),
    "document": ("brief", "document", "note", "source"),
    "capability": ("capability", "proof", "solution", "transition"),
    "discriminator": ("advantage", "discriminator", "proof point", "strength"),
}
_EXTRACTION_DRAFT_CONFIDENCE_THRESHOLD = 0.6
_EXTRACTION_ENTITY_PART_TYPES = {
    "capability": CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE,
    "commitment": CaptureIntelligenceDraftPartType.ACTION_CANDIDATE,
    "customer": CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
    "discriminator": CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE,
    "milestone": CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
    "need": CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
    "opportunity": CaptureIntelligenceDraftPartType.INFERRED_CLAIM,
    "organization": CaptureIntelligenceDraftPartType.INFERRED_CLAIM,
    "risk": CaptureIntelligenceDraftPartType.LIKELY_RISK,
    "stakeholder": CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
}
_EXTRACTION_RELATIONSHIP_PART_TYPES = {
    "addresses_need": CaptureIntelligenceDraftPartType.PACKET_IMPLICATION,
    "creates_risk": CaptureIntelligenceDraftPartType.LIKELY_RISK,
    "evidence_for": CaptureIntelligenceDraftPartType.INFERRED_CLAIM,
    "mentions": CaptureIntelligenceDraftPartType.INFERRED_CLAIM,
}


def _build_extraction_intelligence_pieces(
    bundle: ExtractionBundle,
) -> tuple[CaptureIntelligenceDraftPart, ...]:
    pieces: list[CaptureIntelligenceDraftPart] = []
    seen_content: set[tuple[CaptureIntelligenceDraftPartType, str]] = set()
    for candidate in bundle.entity_candidates:
        if candidate.confidence < _EXTRACTION_DRAFT_CONFIDENCE_THRESHOLD:
            continue
        part_type = _EXTRACTION_ENTITY_PART_TYPES.get(
            candidate.entity_type,
            CaptureIntelligenceDraftPartType.INFERRED_CLAIM,
        )
        content = _entity_candidate_draft_content(candidate, part_type)
        _append_extraction_piece(
            pieces,
            seen_content,
            bundle=bundle,
            part_type=part_type,
            content=content,
            source_span_ids=candidate.source_span_ids,
            confidence=candidate.confidence,
            sequence_ref=candidate.id,
        )
    for relationship in bundle.relationship_candidates:
        if relationship.confidence < _EXTRACTION_DRAFT_CONFIDENCE_THRESHOLD:
            continue
        part_type = _EXTRACTION_RELATIONSHIP_PART_TYPES.get(
            relationship.relationship_type,
            CaptureIntelligenceDraftPartType.INFERRED_CLAIM,
        )
        content = _relationship_candidate_draft_content(bundle, relationship)
        _append_extraction_piece(
            pieces,
            seen_content,
            bundle=bundle,
            part_type=part_type,
            content=content,
            source_span_ids=relationship.source_span_ids,
            confidence=relationship.confidence,
            sequence_ref=relationship.id,
        )
    if bundle.warnings:
        warning_span_ids = tuple(
            span_id
            for warning in bundle.warnings
            for span_id in warning.affected_span_ids
        )
        _append_extraction_piece(
            pieces,
            seen_content,
            bundle=bundle,
            part_type=CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION,
            content=f"Review extraction warning before promotion: {_summarize_extraction_warnings(bundle)}",
            source_span_ids=warning_span_ids,
            confidence=max(bundle.confidence, 0.1),
            sequence_ref="warnings",
        )
    if not pieces:
        _append_extraction_piece(
            pieces,
            seen_content,
            bundle=bundle,
            part_type=CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION,
            content="Which extracted source span is useful enough to review for capture intelligence?",
            source_span_ids=tuple(span.id for span in bundle.source_spans),
            confidence=bundle.confidence,
            sequence_ref="fallback",
        )
    return tuple(pieces)


def _append_extraction_piece(
    pieces: list[CaptureIntelligenceDraftPart],
    seen_content: set[tuple[CaptureIntelligenceDraftPartType, str]],
    *,
    bundle: ExtractionBundle,
    part_type: CaptureIntelligenceDraftPartType,
    content: str,
    source_span_ids: tuple[str, ...],
    confidence: float,
    sequence_ref: str,
) -> None:
    key = (part_type, content)
    if key in seen_content:
        return
    seen_content.add(key)
    route, skill_chain = suggest_capture_intelligence_piece_route(part_type, content)
    pieces.append(
        CaptureIntelligenceDraftPart(
            id=f"draft_{bundle.id}_{part_type.value}_{len(pieces) + 1}_{sequence_ref}",
            part_type=part_type,
            content=content,
            recommended_route=route,
            suggested_skill_chain=skill_chain,
            source_intake_record_id=bundle.document_id,
            source_extraction_bundle_id=bundle.id,
            source_span_ids=source_span_ids,
            recommendation=_recommendation_for_extraction_piece(part_type),
            assumptions=_extraction_draft_assumptions(bundle),
            confidence_notes=(
                f"Extraction candidate confidence {confidence:.2f}; bundle confidence {bundle.confidence:.2f}.",
                f"Parser provenance: {bundle.parser_provenance.adapter_name} {bundle.parser_provenance.adapter_version}.",
            ),
        )
    )


def _entity_candidate_draft_content(
    candidate: EntityCandidate,
    part_type: CaptureIntelligenceDraftPartType,
) -> str:
    if part_type is CaptureIntelligenceDraftPartType.LIKELY_RISK:
        return f"Document extraction flags risk candidate: {candidate.text}"
    if part_type is CaptureIntelligenceDraftPartType.ACTION_CANDIDATE:
        return f"Document extraction suggests action candidate: {candidate.text}"
    if part_type is CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE:
        return f"Document extraction suggests discriminator candidate: {candidate.text}"
    if part_type is CaptureIntelligenceDraftPartType.PACKET_IMPLICATION:
        return f"Document extraction may update packet context: {candidate.text}"
    return f"Document extraction found capture-relevant source signal: {candidate.text}"


def _relationship_candidate_draft_content(
    bundle: ExtractionBundle,
    relationship: RelationshipCandidate,
) -> str:
    source = _entity_text_for_relationship(bundle, relationship.source_entity_id)
    target = _entity_text_for_relationship(bundle, relationship.target_entity_id)
    relationship_label = relationship.relationship_type.replace("_", " ")
    return f"Document extraction links {source} to {target} as {relationship_label}."


def _entity_text_for_relationship(bundle: ExtractionBundle, entity_id: str) -> str:
    for candidate in bundle.entity_candidates:
        if candidate.id == entity_id:
            return candidate.text
    return entity_id


def _recommendation_for_extraction_piece(
    part_type: CaptureIntelligenceDraftPartType,
) -> str:
    if part_type is CaptureIntelligenceDraftPartType.LIKELY_RISK:
        return "Review as a risk signal before routing to Risk Register or packet gaps."
    if part_type is CaptureIntelligenceDraftPartType.ACTION_CANDIDATE:
        return "Review as a possible Capture Action Plan item before assigning work."
    if part_type is CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE:
        return "Review evidence strength before treating this as a discriminator."
    if part_type is CaptureIntelligenceDraftPartType.PACKET_IMPLICATION:
        return "Review against packet fields before updating opportunity knowledge."
    if part_type is CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION:
        return "Resolve extraction uncertainty before promotion."
    return "Review source-span provenance before accepting as evidence."


def _extraction_draft_assumptions(bundle: ExtractionBundle) -> tuple[str, ...]:
    return (
        "Draft treats Extraction Bundle findings as untrusted parser output.",
        "Reviewer must accept, route, or discard each document-derived part before promotion.",
        f"Source material remains traceable through intake record {bundle.document_id}.",
    )


def _extraction_draft_confidence_notes(bundle: ExtractionBundle) -> tuple[str, ...]:
    warning_note = (
        f"{len(bundle.warnings)} extraction warning(s) require review."
        if bundle.warnings
        else "No extraction warnings were recorded for this bundle."
    )
    return (
        f"Bundle confidence is {bundle.confidence:.2f}; parser output is review-gated.",
        warning_note,
        f"Parser provenance: {bundle.parser_provenance.adapter_name} via {bundle.parser_provenance.extraction_method}.",
    )


def _extraction_draft_gaps(bundle: ExtractionBundle) -> tuple[str, ...]:
    gaps = ["Need reviewer validation before promotion into trusted knowledge."]
    if bundle.warnings:
        gaps.append("Need reviewer attention to extraction warnings before promotion.")
    return tuple(gaps)


def _bundle_raw_source_preview(bundle: ExtractionBundle) -> str:
    return "\n".join(span.text for span in bundle.source_spans[:8])


def _extraction_polished_capture(
    *,
    inferred_claims: tuple[str, ...],
    likely_risks: tuple[str, ...],
    packet_implications: tuple[str, ...],
    action_candidates: tuple[str, ...],
    follow_up_questions: tuple[str, ...],
) -> str:
    sections = (
        ("Document signal", inferred_claims[:2]),
        ("Document-derived risk", likely_risks[:2]),
        ("Packet implication", packet_implications[:1]),
        ("Recommended action", action_candidates[:1]),
        ("Review question", follow_up_questions[:1]),
    )
    return " ".join(
        f"{label}: {'; '.join(items)}" for label, items in sections if items
    )


def _summarize_extraction_warnings(bundle: ExtractionBundle) -> str | None:
    if not bundle.warnings:
        return None
    return " | ".join(warning.message for warning in bundle.warnings)


def _extract_text_source_spans(
    text: str,
    *,
    document_id: str,
    bundle_id: str,
) -> tuple[SourceSpan, ...]:
    spans: list[SourceSpan] = []
    current_offset = 0
    for line in text.splitlines(keepends=True):
        stripped_line = line.strip()
        if stripped_line:
            start_offset = current_offset + line.index(stripped_line)
            end_offset = start_offset + len(stripped_line)
            spans.append(
                SourceSpan(
                    id=f"span_{bundle_id}_{len(spans) + 1}",
                    document_id=document_id,
                    text=stripped_line,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    confidence=0.82,
                )
            )
        current_offset += len(line)
    return tuple(spans)


def _extract_entity_candidates(
    source_spans: tuple[SourceSpan, ...],
    *,
    bundle_id: str,
) -> tuple[EntityCandidate, ...]:
    candidates: list[EntityCandidate] = []
    for span in source_spans:
        lowered_text = span.text.lower()
        for entity_type, keywords in _GENERIC_ENTITY_KEYWORDS.items():
            if any(keyword in lowered_text for keyword in keywords):
                candidates.append(
                    EntityCandidate(
                        id=f"entity_{bundle_id}_{len(candidates) + 1}",
                        entity_type=entity_type,
                        text=_candidate_text(span.text),
                        source_span_ids=(span.id,),
                        confidence=0.64,
                    )
                )
    return tuple(candidates)


def _extract_relationship_candidates(
    source_spans: tuple[SourceSpan, ...],
    entity_candidates: tuple[EntityCandidate, ...],
    *,
    bundle_id: str,
) -> tuple[RelationshipCandidate, ...]:
    relationships: list[RelationshipCandidate] = []
    for span in source_spans:
        span_candidates = [
            candidate
            for candidate in entity_candidates
            if span.id in candidate.source_span_ids
        ]
        if len(span_candidates) < 2:
            continue
        anchor = span_candidates[0]
        for target in span_candidates[1:]:
            relationships.append(
                RelationshipCandidate(
                    id=f"relationship_{bundle_id}_{len(relationships) + 1}",
                    relationship_type=_relationship_type(anchor, target),
                    source_entity_id=anchor.id,
                    target_entity_id=target.id,
                    source_span_ids=(span.id,),
                    confidence=0.56,
                )
            )
    return tuple(relationships)


def _relationship_type(
    source: EntityCandidate,
    target: EntityCandidate,
) -> str:
    if source.entity_type == "risk" or target.entity_type == "risk":
        return "creates_risk"
    if source.entity_type == "need" or target.entity_type == "need":
        return "addresses_need"
    return "mentions"


def _extraction_warnings_for_generic_material(
    source_material: UploadedSourceMaterial,
    source_spans: tuple[SourceSpan, ...],
    entity_candidates: tuple[EntityCandidate, ...],
    *,
    bundle_id: str,
) -> tuple[ExtractionWarning, ...]:
    warnings = [
        ExtractionWarning(
            id=f"warning_{bundle_id}_{index}",
            warning_type="source_material_warning",
            message=message,
            severity=ExtractionWarningSeverity.WARN,
        )
        for index, message in enumerate(source_material.warnings, start=1)
    ]
    if not source_spans:
        warnings.append(
            ExtractionWarning(
                id=f"warning_{bundle_id}_{len(warnings) + 1}",
                warning_type="missing_source_spans",
                message="No usable source spans were extracted from generic source material.",
                severity=ExtractionWarningSeverity.ERROR,
            )
        )
    elif not entity_candidates:
        warnings.append(
            ExtractionWarning(
                id=f"warning_{bundle_id}_{len(warnings) + 1}",
                warning_type="missing_context",
                message="No initial capture knowledge entity candidates were detected.",
                affected_span_ids=tuple(span.id for span in source_spans),
                severity=ExtractionWarningSeverity.WARN,
            )
        )
    return tuple(warnings)


def _candidate_text(text: str) -> str:
    return text if len(text) <= 160 else f"{text[:157]}..."


def _bundle_confidence(
    source_spans: tuple[SourceSpan, ...],
    entity_candidates: tuple[EntityCandidate, ...],
) -> float:
    if entity_candidates:
        return round(
            sum(candidate.confidence for candidate in entity_candidates)
            / len(entity_candidates),
            2,
        )
    if source_spans:
        return 0.42
    return 0.0


def classify_uploaded_source_material(
    *,
    filename: str | None,
    mime_type: str | None,
    content: bytes,
) -> UploadedSourceMaterial:
    display_filename = _display_filename(filename)
    normalized_mime_type = _normalize_mime_type(mime_type)
    byte_size = len(content)
    source_ref = _source_ref(display_filename, content)
    content_type = _detect_content_type(display_filename, normalized_mime_type)
    material_type = _detect_material_type(
        display_filename,
        normalized_mime_type,
        content_type,
    )

    if (
        material_type is DocumentIntakeMaterialType.SOLICITATION_DOCUMENT
        or content_type is DocumentIntakeContentType.UNSUPPORTED
    ):
        reason, capability_hint = _parser_required_reason_and_hint(material_type)
        return _parser_required_result(
            filename=display_filename,
            mime_type=normalized_mime_type,
            byte_size=byte_size,
            source_ref=source_ref,
            material_type=material_type,
            content_type=content_type,
            reason=reason,
            capability_hint=capability_hint,
        )

    text = _decode_text(content)
    if text is None:
        return _parser_required_result(
            filename=display_filename,
            mime_type=normalized_mime_type,
            byte_size=byte_size,
            source_ref=source_ref,
            material_type=DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT,
            reason="Binary or non-UTF-8 content requires a document parser.",
            capability_hint=(
                "Readable text is unavailable; keep this source in Document Intake "
                "until an adapter can extract usable source spans."
            ),
        )

    return UploadedSourceMaterial(
        status=DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE,
        content_type=content_type,
        filename=display_filename,
        mime_type=normalized_mime_type,
        byte_size=byte_size,
        source_ref=source_ref,
        material_type=DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL,
        text=text,
        warnings=_classification_warnings(display_filename, normalized_mime_type),
        capability_hint="Ready for Quick Capture; no parser capability required.",
    )


def _display_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    return Path(filename).name


def _normalize_mime_type(mime_type: str | None) -> str | None:
    if not mime_type:
        return None
    return mime_type.split(";", 1)[0].strip().lower() or None


def _detect_content_type(
    filename: str | None,
    mime_type: str | None,
) -> DocumentIntakeContentType:
    suffix = Path(filename or "").suffix.lower()
    if suffix in _MARKDOWN_EXTENSIONS or mime_type in _MARKDOWN_MIME_TYPES:
        return DocumentIntakeContentType.MARKDOWN
    if suffix in _TEXT_EXTENSIONS or mime_type in _TEXT_MIME_TYPES:
        return DocumentIntakeContentType.TEXT
    if mime_type and mime_type.startswith("text/"):
        return DocumentIntakeContentType.TEXT
    return DocumentIntakeContentType.UNSUPPORTED


def _detect_material_type(
    filename: str | None,
    mime_type: str | None,
    content_type: DocumentIntakeContentType,
) -> DocumentIntakeMaterialType:
    if _looks_like_solicitation(filename):
        return DocumentIntakeMaterialType.SOLICITATION_DOCUMENT
    if content_type is not DocumentIntakeContentType.UNSUPPORTED:
        return DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL
    suffix = Path(filename or "").suffix.lower()
    if suffix in _VISUAL_EXTENSIONS or (mime_type and mime_type.startswith("image/")):
        return DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL
    return DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT


def _looks_like_solicitation(filename: str | None) -> bool:
    if not filename:
        return False
    normalized = Path(filename).name.lower().replace(" ", "-")
    return any(term in normalized for term in _SOLICITATION_TERMS)


def _parser_required_reason_and_hint(
    material_type: DocumentIntakeMaterialType,
) -> tuple[str, str]:
    if material_type is DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL:
        return (
            "Visual Source Material requires OCR or multimodal extraction before Quick Capture.",
            "Record and preserve provenance now; OCR and multimodal extraction remain deferred capabilities.",
        )
    if material_type is DocumentIntakeMaterialType.SOLICITATION_DOCUMENT:
        return (
            "Solicitation Document requires a future solicitation parser before Quick Capture.",
            "Queue for Solicitation Parser Capability for RFIs, Sources Soughts, RFPs, amendments, and requirements attachments.",
        )
    return (
        "Unsupported Document recorded as a capability gap; current adapters cannot extract usable source spans.",
        "Parser or readability adapter required before this source can create source spans.",
    )


def _decode_text(content: bytes) -> str | None:
    if b"\x00" in content:
        return None
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def _classification_warnings(
    filename: str | None,
    mime_type: str | None,
) -> tuple[str, ...]:
    if not filename or not mime_type:
        return ()
    suffix = Path(filename).suffix.lower()
    if suffix in _MARKDOWN_EXTENSIONS and mime_type not in _MARKDOWN_MIME_TYPES:
        return ("Filename looks like Markdown, but MIME type was not Markdown.",)
    if suffix in _TEXT_EXTENSIONS and not mime_type.startswith("text/"):
        return ("Filename looks like text, but MIME type was not text.",)
    return ()


def _parser_required_result(
    *,
    filename: str | None,
    mime_type: str | None,
    byte_size: int,
    source_ref: str,
    material_type: DocumentIntakeMaterialType,
    content_type: DocumentIntakeContentType = DocumentIntakeContentType.UNSUPPORTED,
    reason: str,
    capability_hint: str,
) -> UploadedSourceMaterial:
    candidate = DocumentIntakeCandidate(
        id=source_ref.replace(":", "_"),
        filename=filename,
        mime_type=mime_type,
        byte_size=byte_size,
        material_type=material_type,
        reason=reason,
        parser_hint=(
            "Parser required before this source can enter Quick Capture; full "
            "document parsing remains a later Document Intake capability."
        ),
        capability_hint=capability_hint,
        source_ref=source_ref,
    )
    return UploadedSourceMaterial(
        status=DocumentIntakeStatus.PARSER_REQUIRED,
        content_type=content_type,
        filename=filename,
        mime_type=mime_type,
        byte_size=byte_size,
        source_ref=source_ref,
        material_type=material_type,
        intake_candidate=candidate,
        capability_hint=capability_hint,
    )


def _source_ref(filename: str | None, content: bytes) -> str:
    digest = sha256((filename or "uploaded-material").encode() + b"\0" + content)
    return f"upload:{digest.hexdigest()[:16]}"


_DOCUMENT_INTAKE_ADAPTER_DECLARATIONS = (
    DocumentIntakeAdapterDeclaration(
        id="ariadne.generic_text_extractor",
        name="Ariadne Generic Text Extractor",
        adapter_kind=DocumentIntakeAdapterKind.PARSER,
        status=DocumentIntakeAdapterStatus.AVAILABLE,
        supported_material_types=(DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL,),
        capability_hint=(
            "Current deterministic adapter for readable text and Markdown source "
            "material; output is a reviewable Extraction Bundle."
        ),
    ),
    DocumentIntakeAdapterDeclaration(
        id="ariadne.ocr_extractor",
        name="Ariadne OCR Extractor Hook",
        adapter_kind=DocumentIntakeAdapterKind.OCR,
        status=DocumentIntakeAdapterStatus.DEFERRED,
        supported_material_types=(
            DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL,
            DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT,
        ),
        capability_hint=(
            "Future OCR adapter for scans, screenshots, and image-like source "
            "material; must produce reviewable source spans."
        ),
        deferred_reason="OCR integration is not implemented in this slice.",
    ),
    DocumentIntakeAdapterDeclaration(
        id="ariadne.multimodal_extractor",
        name="Ariadne Multimodal Extractor Hook",
        adapter_kind=DocumentIntakeAdapterKind.MULTIMODAL,
        status=DocumentIntakeAdapterStatus.DEFERRED,
        supported_material_types=(DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL,),
        capability_hint=(
            "Future multimodal extraction hook for image, layout, and visual "
            "meaning; output remains an Extraction Bundle."
        ),
        deferred_reason="Multimodal extraction remains deferred capability work.",
    ),
    DocumentIntakeAdapterDeclaration(
        id="project_theseus.solicitation_parser",
        name="Project Theseus Solicitation Parser Hook",
        adapter_kind=DocumentIntakeAdapterKind.PARSER,
        status=DocumentIntakeAdapterStatus.DEFERRED,
        supported_material_types=(DocumentIntakeMaterialType.SOLICITATION_DOCUMENT,),
        capability_hint=(
            "Future solicitation parser adapter for RFIs, Sources Soughts, RFPs, "
            "amendments, and attachments."
        ),
        deferred_reason="Theseus integration will arrive through the Extraction Bundle boundary later.",
    ),
    DocumentIntakeAdapterDeclaration(
        id="opendatalab.mineru",
        name="MinerU Layout Extraction Hook",
        adapter_kind=DocumentIntakeAdapterKind.PARSER,
        status=DocumentIntakeAdapterStatus.DEFERRED,
        supported_material_types=(
            DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL,
            DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL,
            DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT,
        ),
        capability_hint=(
            "Future MinerU adapter candidate for document layout and multimodal "
            "source span extraction."
        ),
        deferred_reason="MinerU is only declared as a future adapter candidate.",
    ),
    DocumentIntakeAdapterDeclaration(
        id="hkuds.raganything",
        name="RAGAnything Retrieval Hook",
        adapter_kind=DocumentIntakeAdapterKind.RETRIEVAL,
        status=DocumentIntakeAdapterStatus.DEFERRED,
        supported_material_types=(
            DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL,
            DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL,
            DocumentIntakeMaterialType.SOLICITATION_DOCUMENT,
        ),
        capability_hint=(
            "Future RAGAnything retrieval candidate after source spans and "
            "reviewed Extraction Bundles exist."
        ),
        deferred_reason="RAGAnything retrieval integration is not implemented yet.",
    ),
    DocumentIntakeAdapterDeclaration(
        id="hkuds.lightrag",
        name="LightRAG Knowledge Layer Hook",
        adapter_kind=DocumentIntakeAdapterKind.RETRIEVAL,
        status=DocumentIntakeAdapterStatus.DEFERRED,
        supported_material_types=(
            DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL,
            DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL,
            DocumentIntakeMaterialType.SOLICITATION_DOCUMENT,
        ),
        capability_hint=(
            "Future LightRAG knowledge-layer candidate for retrieval over accepted "
            "Ariadne knowledge and projections."
        ),
        deferred_reason="LightRAG remains a future Knowledge Layer adapter decision.",
    ),
)
