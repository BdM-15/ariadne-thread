import pytest

from ariadne.document_intake import (
    DocumentIntakeContentType,
    DocumentIntakeMaterialType,
    DocumentIntakeQueueState,
    DocumentIntakeRecord,
    DocumentIntakeStatus,
    DocumentIntakeStore,
    EntityCandidate,
    ExtractionBundleReviewStatus,
    ExtractionStatus,
    ExtractionWarningSeverity,
    classify_uploaded_source_material,
    create_capture_intelligence_draft_from_extraction_bundle,
    create_document_intake_record,
    create_generic_extraction_bundle,
)
from ariadne.quick_capture import CaptureIntelligenceDraftPartType


def test_document_intake_store_writes_and_reads_generic_source_material(
    tmp_path,
) -> None:
    store = DocumentIntakeStore(tmp_path / "document-intake")
    record = DocumentIntakeRecord(
        id="intake_customer_note",
        source_ref="upload:customer-note",
        filename="customer-note.md",
        mime_type="text/markdown",
        byte_size=72,
        content_type=DocumentIntakeContentType.MARKDOWN,
        status=DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE,
        opportunity_id="opp-aflcmc-recompete",
    )

    store.write(record)

    loaded = store.read("intake_customer_note")
    assert loaded == record
    assert loaded.filename == "customer-note.md"
    assert loaded.status is DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE


def test_document_intake_store_lists_persisted_records_with_filters(tmp_path) -> None:
    root = tmp_path / "document-intake"
    store = DocumentIntakeStore(root)
    ready_record = DocumentIntakeRecord(
        id="intake_ready_note",
        source_ref="upload:ready-note",
        filename="ready-note.txt",
        mime_type="text/plain",
        byte_size=42,
        content_type=DocumentIntakeContentType.TEXT,
        status=DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE,
        opportunity_id="opp-ready",
    )
    waiting_record = DocumentIntakeRecord(
        id="intake_waiting_pdf",
        source_ref="upload:waiting-pdf",
        filename="waiting.pdf",
        mime_type="application/pdf",
        byte_size=18,
        content_type=DocumentIntakeContentType.UNSUPPORTED,
        status=DocumentIntakeStatus.PARSER_REQUIRED,
        opportunity_id="opp-waiting",
    )

    store.write(waiting_record)
    store.write(ready_record)
    reloaded_store = DocumentIntakeStore(root)

    assert [record.id for record in reloaded_store.list()] == [
        "intake_ready_note",
        "intake_waiting_pdf",
    ]
    assert reloaded_store.list(opportunity_id="opp-ready") == [ready_record]
    assert reloaded_store.list(status=DocumentIntakeStatus.PARSER_REQUIRED) == [
        waiting_record
    ]


def test_document_intake_store_rejects_non_file_safe_ids(tmp_path) -> None:
    store = DocumentIntakeStore(tmp_path / "document-intake")

    with pytest.raises(ValueError, match="record_id must be a file-safe identifier"):
        store.read("../escape")


def test_generic_source_material_creates_persisted_extraction_bundle(tmp_path) -> None:
    store = DocumentIntakeStore(tmp_path / "document-intake")
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=(
            b"# Customer brief\n\n"
            b"Customer needs transition proof and PM follow up.\n\n"
            b"Response-time risk could affect the recompete."
        ),
    )
    record = store.write(
        create_document_intake_record(
            source_material,
            opportunity_id="opp-aflcmc-recompete",
            record_id="intake_customer_brief",
        )
    )

    bundle = create_generic_extraction_bundle(
        record,
        source_material,
        bundle_id="bundle_customer_brief",
    )
    store.write_extraction_bundle(bundle)

    loaded = store.read_extraction_bundle("bundle_customer_brief")
    assert loaded == bundle
    assert loaded.document_id == record.id
    assert loaded.source_ref == record.source_ref
    assert loaded.material_type is DocumentIntakeMaterialType.GENERIC_SOURCE_MATERIAL
    assert loaded.extraction_status is ExtractionStatus.COMPLETE
    assert loaded.review_status is ExtractionBundleReviewStatus.PENDING_REVIEW
    assert loaded.parser_provenance.adapter_name == "ariadne.generic_text_extractor"
    assert loaded.source_spans[0].text == "# Customer brief"
    assert {candidate.entity_type for candidate in loaded.entity_candidates} >= {
        "customer",
        "need",
        "risk",
    }
    assert loaded.relationship_candidates
    assert loaded.confidence > 0


def test_extraction_bundle_preserves_warnings_and_lists_by_document_id(
    tmp_path,
) -> None:
    store = DocumentIntakeStore(tmp_path / "document-intake")
    warned_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/plain",
        content=b"Customer says transition risk needs follow up.",
    )
    other_material = classify_uploaded_source_material(
        filename="customer-note.txt",
        mime_type="text/plain",
        content=b"Customer needs proof points.",
    )
    warned_record = store.write(
        create_document_intake_record(warned_material, record_id="intake_warned")
    )
    other_record = store.write(
        create_document_intake_record(other_material, record_id="intake_other")
    )
    warned_bundle = store.write_extraction_bundle(
        create_generic_extraction_bundle(
            warned_record,
            warned_material,
            bundle_id="bundle_warned",
        )
    )
    store.write_extraction_bundle(
        create_generic_extraction_bundle(
            other_record,
            other_material,
            bundle_id="bundle_other",
        )
    )

    loaded = store.read_extraction_bundle("bundle_warned")
    assert loaded.warnings[0].warning_type == "source_material_warning"
    assert loaded.warnings[0].severity is ExtractionWarningSeverity.WARN
    assert "MIME type" in loaded.warnings[0].message
    assert store.list_extraction_bundles(document_id=warned_record.id) == [
        warned_bundle
    ]


def test_entity_candidate_requires_source_span_trace() -> None:
    with pytest.raises(ValueError, match="entity candidate requires source_span_ids"):
        EntityCandidate(
            id="entity_untraced_customer",
            entity_type="customer",
            text="Customer",
            source_span_ids=(),
            confidence=0.7,
        )


def test_extraction_bundle_creates_review_ready_draft_parts_with_provenance() -> None:
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=(
            b"Customer needs transition proof and PM follow up.\n"
            b"Response-time risk could affect the recompete."
        ),
    )
    record = create_document_intake_record(
        source_material,
        opportunity_id="opp-aflcmc-recompete",
        record_id="intake_customer_brief",
    )
    bundle = create_generic_extraction_bundle(
        record,
        source_material,
        bundle_id="bundle_customer_brief",
    )

    draft = create_capture_intelligence_draft_from_extraction_bundle(bundle)

    assert draft.id == "draft_bundle_customer_brief"
    assert draft.raw_item_id == "intake_customer_brief"
    assert draft.opportunity_id == "opp-aflcmc-recompete"
    assert draft.extraction_bundle_id == "bundle_customer_brief"
    assert draft.extraction_document_id == "intake_customer_brief"
    assert draft.trusted_opportunity_knowledge_updated is False
    assert draft.intelligence_pieces

    by_type = {piece.part_type for piece in draft.intelligence_pieces}
    assert CaptureIntelligenceDraftPartType.LIKELY_RISK in by_type
    assert CaptureIntelligenceDraftPartType.ACTION_CANDIDATE in by_type
    assert CaptureIntelligenceDraftPartType.DISCRIMINATOR_CANDIDATE in by_type

    risk_piece = next(
        piece
        for piece in draft.intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.LIKELY_RISK
    )
    assert risk_piece.recommended_route == "risk_and_gap_review"
    assert risk_piece.suggested_skill_chain == ("capture_strategy_review",)

    first_piece = draft.intelligence_pieces[0]
    assert first_piece.source_intake_record_id == record.id
    assert first_piece.source_extraction_bundle_id == bundle.id
    assert first_piece.source_span_ids
    assert first_piece.recommendation
    assert first_piece.assumptions
    assert first_piece.confidence_notes
    assert first_piece.review_required is True


def test_extraction_warning_becomes_follow_up_question_draft_part() -> None:
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/plain",
        content=b"Customer says transition risk needs follow up.",
    )
    record = create_document_intake_record(
        source_material,
        record_id="intake_warned_brief",
    )
    bundle = create_generic_extraction_bundle(
        record,
        source_material,
        bundle_id="bundle_warned_brief",
    )

    draft = create_capture_intelligence_draft_from_extraction_bundle(bundle)

    warning_piece = next(
        piece
        for piece in draft.intelligence_pieces
        if piece.part_type is CaptureIntelligenceDraftPartType.FOLLOW_UP_QUESTION
    )
    assert "Review extraction warning" in warning_piece.content
    assert "MIME type" in warning_piece.content
    assert warning_piece.recommended_route == "evidence_or_knowledge_review"
    assert draft.extraction_warnings_summarized is not None
    assert "MIME type" in draft.extraction_warnings_summarized


def test_create_document_intake_record_from_generic_upload() -> None:
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=b"# Brief\n\nCustomer says transition proof needs follow up.",
    )

    record = create_document_intake_record(
        source_material,
        opportunity_id="opp-aflcmc-recompete",
        record_id="intake_customer_brief",
    )

    assert record.id == "intake_customer_brief"
    assert record.source_ref == source_material.source_ref
    assert record.filename == "customer-brief.md"
    assert record.content_type is DocumentIntakeContentType.MARKDOWN
    assert record.status is DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE
    assert record.queue_state is DocumentIntakeQueueState.READY
    assert record.opportunity_id == "opp-aflcmc-recompete"
    assert record.warnings == source_material.warnings


def test_document_intake_record_derives_waiting_queue_state() -> None:
    source_material = classify_uploaded_source_material(
        filename="draft-rfp.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4\n...",
    )

    record = create_document_intake_record(source_material)

    assert record.status is DocumentIntakeStatus.PARSER_REQUIRED
    assert record.queue_state is DocumentIntakeQueueState.WAITING


def test_visual_source_material_is_classified_and_preserved_with_capability_hint() -> (
    None
):
    source_material = classify_uploaded_source_material(
        filename="whiteboard-photo.png",
        mime_type="image/png",
        content=b"\x89PNG\r\n\x1a\n",
    )

    record = create_document_intake_record(source_material)

    assert (
        source_material.material_type
        is DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL
    )
    assert source_material.status is DocumentIntakeStatus.PARSER_REQUIRED
    assert source_material.text is None
    assert source_material.intake_candidate is not None
    assert source_material.intake_candidate.material_type is (
        DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL
    )
    assert "multimodal" in source_material.intake_candidate.capability_hint.lower()
    assert record.material_type is DocumentIntakeMaterialType.VISUAL_SOURCE_MATERIAL
    assert record.queue_state is DocumentIntakeQueueState.WAITING
    assert "ocr" in record.capability_hint.lower()


def test_solicitation_document_is_queued_for_future_parser_capability() -> None:
    source_material = classify_uploaded_source_material(
        filename="draft-rfp-amendment-001.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4\n...",
    )

    record = create_document_intake_record(source_material)

    assert (
        source_material.material_type
        is DocumentIntakeMaterialType.SOLICITATION_DOCUMENT
    )
    assert source_material.status is DocumentIntakeStatus.PARSER_REQUIRED
    assert source_material.intake_candidate is not None
    assert source_material.intake_candidate.material_type is (
        DocumentIntakeMaterialType.SOLICITATION_DOCUMENT
    )
    assert (
        "solicitation parser"
        in source_material.intake_candidate.capability_hint.lower()
    )
    assert record.material_type is DocumentIntakeMaterialType.SOLICITATION_DOCUMENT
    assert record.queue_state is DocumentIntakeQueueState.WAITING
    assert "rfp" in record.capability_hint.lower()


def test_readable_solicitation_filename_still_queues_for_solicitation_parser() -> None:
    source_material = classify_uploaded_source_material(
        filename="sources-sought-notice.txt",
        mime_type="text/plain",
        content=b"Sources sought notice with readable text.",
    )

    assert (
        source_material.material_type
        is DocumentIntakeMaterialType.SOLICITATION_DOCUMENT
    )
    assert source_material.status is DocumentIntakeStatus.PARSER_REQUIRED
    assert source_material.text is None
    assert source_material.intake_candidate is not None
    assert (
        "solicitation parser"
        in source_material.intake_candidate.capability_hint.lower()
    )


def test_unknown_binary_file_is_unsupported_document_with_capability_gap_reason() -> (
    None
):
    source_material = classify_uploaded_source_material(
        filename="mystery.bundle",
        mime_type="application/octet-stream",
        content=b"\x00\x01\x02",
    )

    record = create_document_intake_record(source_material)

    assert (
        source_material.material_type is DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT
    )
    assert source_material.intake_candidate is not None
    assert "capability gap" in source_material.intake_candidate.reason.lower()
    assert record.material_type is DocumentIntakeMaterialType.UNSUPPORTED_DOCUMENT
    assert "readability adapter" in record.capability_hint.lower()


def test_text_upload_is_ready_for_quick_capture() -> None:
    result = classify_uploaded_source_material(
        filename="customer-note.txt",
        mime_type="text/plain",
        content=b"Customer says transition proof needs PM follow up.",
    )

    assert result.status is DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE
    assert result.content_type is DocumentIntakeContentType.TEXT
    assert result.text == "Customer says transition proof needs PM follow up."
    assert result.intake_candidate is None


def test_markdown_upload_is_ready_for_quick_capture() -> None:
    result = classify_uploaded_source_material(
        filename="customer-call.md",
        mime_type="text/markdown",
        content=b"# Call note\n\nCustomer says transition risk needs packet gap.",
    )

    assert result.status is DocumentIntakeStatus.READY_FOR_QUICK_CAPTURE
    assert result.content_type is DocumentIntakeContentType.MARKDOWN
    assert "transition risk" in result.text


def test_unsupported_upload_becomes_document_intake_candidate() -> None:
    result = classify_uploaded_source_material(
        filename="draft-rfp.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4\n...",
    )

    assert result.status is DocumentIntakeStatus.PARSER_REQUIRED
    assert result.content_type is DocumentIntakeContentType.UNSUPPORTED
    assert result.text is None
    assert result.intake_candidate is not None
    assert result.intake_candidate.filename == "draft-rfp.pdf"
    assert result.intake_candidate.status is DocumentIntakeStatus.PARSER_REQUIRED
    assert "parser" in result.intake_candidate.parser_hint.lower()


def test_binary_text_extension_still_requires_parser() -> None:
    result = classify_uploaded_source_material(
        filename="customer-note.txt",
        mime_type="text/plain",
        content=b"\x00\x01\x02",
    )

    assert result.status is DocumentIntakeStatus.PARSER_REQUIRED
    assert result.intake_candidate is not None
    assert "binary" in result.intake_candidate.reason.lower()
