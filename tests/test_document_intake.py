from ariadne.document_intake import (
    DocumentIntakeContentType,
    DocumentIntakeStatus,
    classify_uploaded_source_material,
)


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