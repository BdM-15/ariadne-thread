from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class DocumentIntakeStatus(StrEnum):
    READY_FOR_QUICK_CAPTURE = "ready_for_quick_capture"
    PARSER_REQUIRED = "parser_required"


class DocumentIntakeQueueState(StrEnum):
    ACTIVE = "active"
    READY = "ready"
    WAITING = "waiting"


class DocumentIntakeContentType(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"
    UNSUPPORTED = "unsupported"


class DocumentIntakeCandidate(BaseModel):
    id: str
    filename: str | None = None
    mime_type: str | None = None
    byte_size: int
    content_type: DocumentIntakeContentType = DocumentIntakeContentType.UNSUPPORTED
    status: DocumentIntakeStatus = DocumentIntakeStatus.PARSER_REQUIRED
    reason: str
    parser_hint: str
    source_ref: str


class UploadedSourceMaterial(BaseModel):
    status: DocumentIntakeStatus
    content_type: DocumentIntakeContentType
    filename: str | None = None
    mime_type: str | None = None
    byte_size: int
    source_ref: str
    text: str | None = None
    warnings: tuple[str, ...] = ()
    intake_candidate: DocumentIntakeCandidate | None = None


class DocumentIntakeRecord(BaseModel):
    id: str
    source_ref: str
    filename: str | None = None
    mime_type: str | None = None
    byte_size: int
    content_type: DocumentIntakeContentType
    status: DocumentIntakeStatus
    queue_state: DocumentIntakeQueueState | None = None
    opportunity_id: str | None = None
    warnings: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def derive_queue_state(self) -> DocumentIntakeRecord:
        if self.queue_state is None:
            self.queue_state = (
                DocumentIntakeQueueState.WAITING
                if self.status is DocumentIntakeStatus.PARSER_REQUIRED
                else DocumentIntakeQueueState.READY
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

    def _path(self, record_id: str) -> Path:
        if not record_id or record_id != Path(record_id).name:
            raise ValueError("record_id must be a file-safe identifier")
        return self.root / f"{record_id}.json"


def create_document_intake_record(
    source_material: UploadedSourceMaterial,
    *,
    opportunity_id: str | None = None,
    record_id: str | None = None,
) -> DocumentIntakeRecord:
    return DocumentIntakeRecord(
        id=record_id or source_material.source_ref.replace(":", "_"),
        source_ref=source_material.source_ref,
        filename=source_material.filename,
        mime_type=source_material.mime_type,
        byte_size=source_material.byte_size,
        content_type=source_material.content_type,
        status=source_material.status,
        opportunity_id=opportunity_id,
        warnings=source_material.warnings,
    )


_TEXT_EXTENSIONS = {".txt", ".text"}
_MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown"}
_TEXT_MIME_TYPES = {"text/plain"}
_MARKDOWN_MIME_TYPES = {"text/markdown", "text/x-markdown"}


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

    if content_type is DocumentIntakeContentType.UNSUPPORTED:
        return _parser_required_result(
            filename=display_filename,
            mime_type=normalized_mime_type,
            byte_size=byte_size,
            source_ref=source_ref,
            reason="Unsupported file type requires a document parser before Quick Capture.",
        )

    text = _decode_text(content)
    if text is None:
        return _parser_required_result(
            filename=display_filename,
            mime_type=normalized_mime_type,
            byte_size=byte_size,
            source_ref=source_ref,
            reason="Binary or non-UTF-8 content requires a document parser.",
        )

    return UploadedSourceMaterial(
        status=DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE,
        content_type=content_type,
        filename=display_filename,
        mime_type=normalized_mime_type,
        byte_size=byte_size,
        source_ref=source_ref,
        text=text,
        warnings=_classification_warnings(display_filename, normalized_mime_type),
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
    reason: str,
) -> UploadedSourceMaterial:
    candidate = DocumentIntakeCandidate(
        id=source_ref.replace(":", "_"),
        filename=filename,
        mime_type=mime_type,
        byte_size=byte_size,
        reason=reason,
        parser_hint=(
            "Parser required before this source can enter Quick Capture; full "
            "document parsing remains a later Document Intake capability."
        ),
        source_ref=source_ref,
    )
    return UploadedSourceMaterial(
        status=DocumentIntakeStatus.PARSER_REQUIRED,
        content_type=DocumentIntakeContentType.UNSUPPORTED,
        filename=filename,
        mime_type=mime_type,
        byte_size=byte_size,
        source_ref=source_ref,
        intake_candidate=candidate,
    )


def _source_ref(filename: str | None, content: bytes) -> str:
    digest = sha256((filename or "uploaded-material").encode() + b"\0" + content)
    return f"upload:{digest.hexdigest()[:16]}"
