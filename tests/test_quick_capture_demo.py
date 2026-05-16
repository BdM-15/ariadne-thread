from ariadne.config import RuntimeSettings
from ariadne.quick_capture_demo import build_quick_capture_demo_thread


def test_quick_capture_demo_thread_shows_end_to_end_review_flow(tmp_path) -> None:
    wiki_root = tmp_path / "knowledge"
    _write_reference_note(
        wiki_root / "global_wiki" / "capture" / "incumbent-analysis-strategy.md",
        """---
title: Incumbent Analysis Strategy
entity_type: concept
---

Incumbent transition risk, weak response times, customer complaints, proof points,
and ghost strategy should shape capture follow-up.
""",
    )
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_REFERENCE_WIKI_DIR": str(wiki_root)}
    )

    demo = build_quick_capture_demo_thread(settings, workspace_root=tmp_path)

    assert demo.quick_capture.id == "raw_demo_rushed_capture_note"
    assert "call blur" in demo.quick_capture.content
    assert demo.reference_influences[0].title == "Incumbent Analysis Strategy"
    assert demo.capture_review.intelligence_draft is not None
    assert demo.capture_review.intelligence_draft.intelligence_pieces

    assert demo.accepted_evidence.status == "accepted"
    assert demo.accepted_evidence.trusted_evidence_written is True
    assert demo.accepted_evidence.evidence is not None
    assert demo.accepted_evidence.evidence.content == (
        demo.capture_review.intelligence_draft.polished_capture
    )
    assert "call blur" not in demo.accepted_evidence.evidence.content
    assert demo.accepted_evidence.evidence.raw_item_id == demo.quick_capture.id
    assert demo.accepted_evidence.evidence.draft_id == (
        demo.capture_review.intelligence_draft.id
    )
    assert demo.accepted_evidence.evidence.rationale[0] == (
        "Reviewer accepted rushed customer note as source evidence."
    )

    accepted_evidence_id = demo.accepted_evidence.evidence.id
    assert demo.accepted_action.review_status == "accepted"
    assert demo.accepted_action.source_raw_item_id == demo.quick_capture.id
    assert (
        demo.accepted_action.source_draft_id
        == demo.capture_review.intelligence_draft.id
    )
    assert demo.accepted_action.related_evidence_ids == (accepted_evidence_id,)

    assert demo.accepted_packet_answer.review_status == "accepted"
    assert demo.accepted_packet_answer.source_raw_item_id == demo.quick_capture.id
    assert demo.accepted_packet_answer.source_draft_id == (
        demo.capture_review.intelligence_draft.id
    )
    assert demo.accepted_packet_answer.evidence_ids == (accepted_evidence_id,)

    assert demo.discarded_output.status == "discarded"
    assert demo.discarded_output.source_raw_item_id == demo.quick_capture.id
    assert (
        demo.discarded_output.source_draft_id
        == demo.capture_review.intelligence_draft.id
    )
    assert "proof points" in (demo.discarded_output.discard_reason or "")

    candidate = demo.unsupported_upload.intake_candidate
    assert candidate is not None
    assert candidate.status == "parser_required"
    assert candidate.material_type == "solicitation_document"
    assert candidate.reason == (
        "Solicitation Document requires a future solicitation parser before Quick Capture."
    )
    assert "Solicitation Parser Capability" in candidate.capability_hint
    assert "Document Intake capability" in candidate.parser_hint


def test_quick_capture_demo_thread_includes_document_intake_command_surface(
    tmp_path,
) -> None:
    settings = RuntimeSettings.from_mapping({})

    demo = build_quick_capture_demo_thread(settings, workspace_root=tmp_path)
    document_thread = demo.document_intake

    assert document_thread.source_material.filename == "customer-capture-brief.md"
    assert document_thread.source_material.status == "ready_for_quick_capture"
    assert document_thread.record.material_type == "generic_source_material"
    assert document_thread.record.extraction_bundle_id == document_thread.bundle.id
    assert document_thread.bundle.source_spans
    assert document_thread.bundle.extraction_status == "complete"
    assert document_thread.bundle.review_status == "pending_review"
    assert document_thread.draft.intelligence_pieces
    assert any(
        piece.suggested_skill_chain
        for piece in document_thread.draft.intelligence_pieces
    )
    assert document_thread.accepted_evidence.evidence.id == (
        "ev_demo_document_transition_risk"
    )
    assert document_thread.accepted_evidence.accepted_link.draft_part_id
    assert {candidate.target_workflow for candidate in document_thread.candidates} >= {
        "capture_action_plan",
        "living_briefing_packet",
        "risk_register",
        "call_plan",
    }
    assert document_thread.projection.title == (
        "Knowledge Note Projection: customer-capture-brief.md"
    )
    assert document_thread.projection.evidence_ids == (
        "ev_demo_document_transition_risk",
    )


def _write_reference_note(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
