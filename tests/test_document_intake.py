import pytest

from ariadne.document_intake import (
    DocumentIntakeContentType,
    DocumentIntakeMaterialType,
    DocumentIntakeQueueState,
    DocumentIntakeRecord,
    DocumentIntakeStatus,
    DocumentIntakeStore,
    DocumentIntakeCaptureCandidateType,
    DocumentIntakeCandidateReviewState,
    EntityCandidate,
    ExtractionBundleReviewStatus,
    ExtractionStatus,
    ExtractionWarningSeverity,
    KnowledgeNoteProjection,
    accept_source_spans_to_evidence,
    classify_uploaded_source_material,
    create_capture_intelligence_draft_from_extraction_bundle,
    create_document_intake_record,
    create_generic_extraction_bundle,
    create_knowledge_note_projection_from_accepted_evidence,
    create_review_gated_capture_candidates_from_extraction_bundle,
)
from ariadne.evidence import LocalEvidenceStore
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


def test_accept_source_span_to_evidence_preserves_lineage_and_link(tmp_path) -> None:
    intake_store = DocumentIntakeStore(tmp_path / "document-intake")
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/plain",
        content=b"Customer needs transition proof. Risk needs PM follow up.",
    )
    record = intake_store.write(
        create_document_intake_record(
            source_material,
            opportunity_id="opp-aflcmc-recompete",
            record_id="intake_customer_brief",
        )
    )
    bundle = intake_store.write_extraction_bundle(
        create_generic_extraction_bundle(
            record,
            source_material,
            bundle_id="bundle_customer_brief",
        )
    )
    span = bundle.source_spans[0]

    assert evidence_store.list() == []

    result = accept_source_spans_to_evidence(
        bundle,
        source_span_ids=(span.id,),
        reviewer_rationale="Reviewer accepted source span as trusted customer signal.",
        intake_store=intake_store,
        evidence_store=evidence_store,
        draft_part_id="draft_part_customer_need",
        evidence_id="ev_document_customer_need",
    )

    evidence = result.evidence
    assert evidence.id == "ev_document_customer_need"
    assert evidence.content == span.text
    assert evidence.source_ref == bundle.source_ref
    assert evidence.opportunity_id == "opp-aflcmc-recompete"
    assert evidence.source_intake_record_id == record.id
    assert evidence.source_extraction_bundle_id == bundle.id
    assert evidence.source_span_ids == (span.id,)
    assert evidence.parser_adapter == "ariadne.generic_text_extractor"
    assert evidence.parser_version == "0.1"
    assert evidence.parser_method == "deterministic_text_span_heuristics"
    assert evidence.source_confidence == span.confidence
    assert evidence.source_warnings == (
        "Filename looks like Markdown, but MIME type was not Markdown.",
    )
    assert "Reviewer accepted source span" in evidence.rationale[0]

    loaded_evidence = evidence_store.read("ev_document_customer_need")
    assert loaded_evidence == evidence
    links = intake_store.list_accepted_evidence_links(bundle_id=bundle.id)
    assert links == [result.accepted_link]
    assert links[0].evidence_id == evidence.id
    assert links[0].draft_part_id == "draft_part_customer_need"
    assert links[0].source_span_ids == (span.id,)
    assert links[0].warnings == evidence.source_warnings
    assert result.duplicate is False

    duplicate_result = accept_source_spans_to_evidence(
        bundle,
        source_span_ids=(span.id,),
        reviewer_rationale="Reviewer clicked accept again.",
        intake_store=intake_store,
        evidence_store=evidence_store,
    )

    assert duplicate_result.duplicate is True
    assert duplicate_result.evidence.id == "ev_document_customer_need"
    assert len(evidence_store.list()) == 1
    assert intake_store.list_accepted_evidence_links(bundle_id=bundle.id) == links


def test_accepted_document_evidence_generates_knowledge_note_projection(
    tmp_path,
) -> None:
    intake_store = DocumentIntakeStore(tmp_path / "document-intake")
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=b"Customer needs transition proof. Risk needs PM follow up.",
    )
    record = intake_store.write(
        create_document_intake_record(
            source_material,
            opportunity_id="opp-aflcmc-recompete",
            record_id="intake_customer_brief",
        )
    )
    bundle = intake_store.write_extraction_bundle(
        create_generic_extraction_bundle(
            record,
            source_material,
            bundle_id="bundle_customer_brief",
        )
    )
    span = bundle.source_spans[0]
    accepted = accept_source_spans_to_evidence(
        bundle,
        source_span_ids=(span.id,),
        reviewer_rationale="Accepted for human-readable sensemaking note.",
        intake_store=intake_store,
        evidence_store=evidence_store,
        evidence_id="ev_document_customer_signal",
    )

    projection = create_knowledge_note_projection_from_accepted_evidence(
        bundle,
        intake_store=intake_store,
        evidence_store=evidence_store,
        projection_id="note_customer_brief",
    )

    assert projection is not None
    assert projection.id == "note_customer_brief"
    assert projection.title == "Knowledge Note Projection: customer-brief.md"
    assert projection.source_intake_record_id == record.id
    assert projection.source_extraction_bundle_id == bundle.id
    assert projection.source_ref == bundle.source_ref
    assert projection.evidence_ids == (accepted.evidence.id,)
    assert projection.accepted_evidence_link_ids == (accepted.accepted_link.id,)
    assert projection.source_span_ids == (span.id,)
    assert projection.parser_adapter == "ariadne.generic_text_extractor"
    assert projection.parser_version == "0.1"
    assert projection.parser_method == "deterministic_text_span_heuristics"
    assert projection.is_source_of_truth is False
    assert projection.can_overwrite_structured_knowledge is False
    assert projection.generated_from_accepted_evidence_count == 1
    assert projection.markdown_content.startswith(
        "# Knowledge Note Projection: customer-brief.md"
    )
    assert "Structured Ariadne records remain the source of truth." in (
        projection.markdown_content
    )
    assert accepted.evidence.content in projection.markdown_content
    assert accepted.evidence.id in projection.markdown_content
    assert accepted.accepted_link.reviewer_rationale in projection.markdown_content


def test_knowledge_note_projection_requires_accepted_document_evidence(
    tmp_path,
) -> None:
    intake_store = DocumentIntakeStore(tmp_path / "document-intake")
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=b"Customer needs transition proof. Risk needs PM follow up.",
    )
    record = intake_store.write(
        create_document_intake_record(
            source_material,
            record_id="intake_customer_brief",
        )
    )
    bundle = intake_store.write_extraction_bundle(
        create_generic_extraction_bundle(
            record,
            source_material,
            bundle_id="bundle_customer_brief",
        )
    )

    projection = create_knowledge_note_projection_from_accepted_evidence(
        bundle,
        intake_store=intake_store,
        evidence_store=evidence_store,
    )

    assert projection is None
    assert intake_store.list_knowledge_note_projections(bundle_id=bundle.id) == []


def test_document_intake_store_persists_knowledge_note_projections(
    tmp_path,
) -> None:
    intake_store = DocumentIntakeStore(tmp_path / "document-intake")
    evidence_store = LocalEvidenceStore(tmp_path / "evidence")
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=b"Customer needs transition proof. Risk needs PM follow up.",
    )
    record = intake_store.write(
        create_document_intake_record(
            source_material,
            opportunity_id="opp-aflcmc-recompete",
            record_id="intake_customer_brief",
        )
    )
    bundle = intake_store.write_extraction_bundle(
        create_generic_extraction_bundle(
            record,
            source_material,
            bundle_id="bundle_customer_brief",
        )
    )
    span = bundle.source_spans[0]
    accepted = accept_source_spans_to_evidence(
        bundle,
        source_span_ids=(span.id,),
        reviewer_rationale="Accepted for human-readable sensemaking note.",
        intake_store=intake_store,
        evidence_store=evidence_store,
        evidence_id="ev_document_customer_signal",
    )
    projection = create_knowledge_note_projection_from_accepted_evidence(
        bundle,
        intake_store=intake_store,
        evidence_store=evidence_store,
        projection_id="note_customer_brief",
    )
    assert projection is not None

    intake_store.write_knowledge_note_projection(projection)

    reloaded_store = DocumentIntakeStore(tmp_path / "document-intake")
    assert reloaded_store.read_knowledge_note_projection(projection.id).model_dump(
        mode="json"
    ) == projection.model_dump(mode="json")
    assert reloaded_store.list_knowledge_note_projections(bundle_id=bundle.id) == [
        projection
    ]
    assert reloaded_store.list_knowledge_note_projections(
        intake_record_id=record.id
    ) == [projection]
    assert reloaded_store.list_knowledge_note_projections(
        evidence_id=accepted.evidence.id
    ) == [projection]


def test_knowledge_note_projection_cannot_be_source_of_truth() -> None:
    projection_data = {
        "id": "note_customer_brief",
        "title": "Knowledge Note Projection: customer-brief.md",
        "summary": "Customer needs transition proof.",
        "markdown_content": "# Knowledge Note Projection: customer-brief.md",
        "source_intake_record_id": "intake_customer_brief",
        "source_extraction_bundle_id": "bundle_customer_brief",
        "source_ref": "upload:customer-brief.md",
        "evidence_ids": ("ev_document_customer_signal",),
        "accepted_evidence_link_ids": ("accepted_customer_signal",),
        "source_span_ids": ("span_customer_signal",),
        "parser_adapter": "ariadne.generic_text_extractor",
        "parser_version": "0.1",
        "parser_method": "deterministic_text_span_heuristics",
        "generated_from_accepted_evidence_count": 1,
    }

    with pytest.raises(ValueError, match="cannot be source of truth"):
        KnowledgeNoteProjection(**projection_data, is_source_of_truth=True)

    with pytest.raises(ValueError, match="cannot overwrite structured knowledge"):
        KnowledgeNoteProjection(
            **projection_data,
            can_overwrite_structured_knowledge=True,
        )


def test_extraction_bundle_creates_review_gated_capture_candidates() -> None:
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=(
            b"Customer needs transition proof and PM follow up.\n"
            b"Response-time risk could affect the recompete.\n"
            b"Decision maker expects a customer meeting before the next milestone."
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

    candidates = create_review_gated_capture_candidates_from_extraction_bundle(bundle)

    assert {candidate.candidate_type for candidate in candidates} >= {
        DocumentIntakeCaptureCandidateType.ACTION_PLAN_ITEM,
        DocumentIntakeCaptureCandidateType.PACKET_FIELD_ANSWER,
        DocumentIntakeCaptureCandidateType.RISK_REGISTER_ITEM,
        DocumentIntakeCaptureCandidateType.CALL_PLAN_SIGNAL,
    }
    assert all(
        candidate.review_state is DocumentIntakeCandidateReviewState.PENDING_REVIEW
        for candidate in candidates
    )
    assert all(candidate.trusted_output_written is False for candidate in candidates)

    risk_candidate = next(
        candidate
        for candidate in candidates
        if candidate.candidate_type
        is DocumentIntakeCaptureCandidateType.RISK_REGISTER_ITEM
    )
    assert risk_candidate.target_workflow == "risk_register"
    assert risk_candidate.source_intake_record_id == record.id
    assert risk_candidate.source_extraction_bundle_id == bundle.id
    assert risk_candidate.source_draft_id == f"draft_{bundle.id}"
    assert risk_candidate.source_draft_part_id.startswith(f"draft_{bundle.id}_")
    assert risk_candidate.source_span_ids
    assert risk_candidate.recommendation
    assert risk_candidate.rationale
    assert risk_candidate.confidence is not None


def test_document_intake_store_persists_review_gated_capture_candidates(
    tmp_path,
) -> None:
    store = DocumentIntakeStore(tmp_path / "document-intake")
    source_material = classify_uploaded_source_material(
        filename="customer-brief.md",
        mime_type="text/markdown",
        content=(
            b"Customer needs transition proof and PM follow up.\n"
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
    bundle = store.write_extraction_bundle(
        create_generic_extraction_bundle(
            record,
            source_material,
            bundle_id="bundle_customer_brief",
        )
    )
    candidates = create_review_gated_capture_candidates_from_extraction_bundle(bundle)

    for candidate in candidates:
        store.write_capture_candidate(candidate)

    reloaded_store = DocumentIntakeStore(tmp_path / "document-intake")
    loaded_candidates = reloaded_store.list_capture_candidates(bundle_id=bundle.id)

    assert sorted(candidate.id for candidate in loaded_candidates) == sorted(
        candidate.id for candidate in candidates
    )
    assert reloaded_store.read_capture_candidate(candidates[0].id).model_dump(
        mode="json"
    ) == candidates[0].model_dump(mode="json")
    loaded_risk_candidate_ids = sorted(
        candidate.id
        for candidate in reloaded_store.list_capture_candidates(
            candidate_type=DocumentIntakeCaptureCandidateType.RISK_REGISTER_ITEM
        )
    )
    expected_risk_candidate_ids = sorted(
        candidate.id
        for candidate in candidates
        if candidate.candidate_type
        is DocumentIntakeCaptureCandidateType.RISK_REGISTER_ITEM
    )
    assert loaded_risk_candidate_ids == expected_risk_candidate_ids
    assert (
        reloaded_store.list_capture_candidates(
            review_state=DocumentIntakeCandidateReviewState.PENDING_REVIEW
        )
        == loaded_candidates
    )


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
