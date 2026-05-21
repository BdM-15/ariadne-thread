from ariadne.knowledge_vault import (
    ensure_knowledge_vault_scaffold,
    validate_knowledge_vault_pages,
)
from ariadne.mirror_update_proposals import (
    list_pending_mirror_update_proposals,
    scan_vault_for_mirror_update_proposals,
)
from ariadne.packet_knowledge import (
    PacketFieldAnswerStatus,
    PacketFieldAnswerStore,
    create_packet_field_answer,
)
from ariadne.packets import EvidenceStatus


def test_vault_edit_targeting_packet_answer_creates_proposal_without_store_write(
    tmp_path,
) -> None:
    vault_root = tmp_path / "vault"
    answer_store = PacketFieldAnswerStore(tmp_path / "packet-field-answers")
    answer_store.write(
        create_packet_field_answer(
            field_key="customer",
            opportunity_id="opp-disa-cloud",
            value="DISA",
            status=PacketFieldAnswerStatus.ANSWERED,
            evidence_status=EvidenceStatus.ANSWERED,
            evidence_ids=("ev_customer",),
        )
    )
    ensure_knowledge_vault_scaffold(vault_root)
    (vault_root / "inbox" / "customer-answer-edit.md").write_text(
        """---
page_type: capture_concept
title: Customer Answer Edit Attempt
source_refs: [vault-edit:customer-answer-edit]
relationships: [informs:data-elements/briefing-packet/customer]
target_record_kind: packet_field_answer
target_record_ref: opp-disa-cloud/customer
requested_change_summary: Change customer answer from DISA to DISA J9.
confidence: medium
risk_notes: User edited wiki text; needs normal packet answer review.
---

# Customer Answer Edit Attempt

Suggested answer: DISA J9.
""",
        encoding="utf-8",
    )

    report = scan_vault_for_mirror_update_proposals(vault_root)
    trusted_answer = answer_store.read(
        opportunity_id="opp-disa-cloud",
        field_key="customer",
    )

    assert report.created_count == 1
    assert report.pending_count == 1
    proposal = report.proposals[0]
    assert proposal.source_page == "inbox/customer-answer-edit.md"
    assert proposal.target_record_kind == "packet_field_answer"
    assert proposal.target_record_ref == "opp-disa-cloud/customer"
    assert proposal.requested_change_summary == (
        "Change customer answer from DISA to DISA J9."
    )
    assert proposal.review_status == "pending_review"
    assert proposal.provenance == "vault-edit:customer-answer-edit"
    assert proposal.confidence == "medium"
    assert "normal packet answer review" in proposal.risk_notes
    assert (vault_root / proposal.proposal_path).exists()
    assert trusted_answer.value == "DISA"

    proposal_text = (vault_root / proposal.proposal_path).read_text(encoding="utf-8")
    assert "page_type: mirror_update_proposal" in proposal_text
    assert "source_page: inbox/customer-answer-edit.md" in proposal_text
    assert "target_record_kind: packet_field_answer" in proposal_text
    assert "review_status: pending_review" in proposal_text

    validation_report = validate_knowledge_vault_pages(vault_root)
    assert validation_report.valid is True


def test_pending_mirror_update_proposals_api_lists_review_queue(tmp_path) -> None:
    from fastapi.testclient import TestClient

    from ariadne.config import RuntimeSettings
    from ariadne.server import create_app

    vault_root = tmp_path / "vault"
    ensure_knowledge_vault_scaffold(vault_root)
    (vault_root / "inbox" / "evidence-edit.md").write_text(
        """---
page_type: capture_concept
title: Evidence Edit Attempt
source_refs: [vault-edit:evidence-edit]
relationships: [supports:data-elements/briefing-packet/customer]
target_record_kind: evidence_item
target_record_ref: ev_customer
requested_change_summary: Replace accepted evidence summary.
risk_notes: Evidence edits need normal evidence review.
---

# Evidence Edit Attempt
""",
        encoding="utf-8",
    )
    client = TestClient(
        create_app(
            RuntimeSettings.from_mapping(
                {"ARIADNE_OBSIDIAN_VAULT_DIR": str(vault_root)}
            )
        )
    )

    scan_response = client.post("/api/knowledge-vault/mirror-update-proposals/scan")
    list_response = client.get("/api/knowledge-vault/mirror-update-proposals")

    assert scan_response.status_code == 200
    assert scan_response.json()["created_count"] == 1
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["pending_count"] == 1
    assert body["proposals"][0]["target_record_kind"] == "evidence_item"
    assert body["proposals"][0]["review_status"] == "pending_review"


def test_existing_proposal_page_is_listed_without_duplicate_creation(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    ensure_knowledge_vault_scaffold(vault_root)
    (vault_root / "proposals" / "existing.md").write_text(
        """---
page_type: mirror_update_proposal
title: Existing Mirror Update Proposal
source_refs: [vault-edit:existing]
relationships: [derived_from:inbox/existing-edit]
proposal_id: mirror_update_existing
source_page: inbox/existing-edit.md
target_record_kind: action_plan_state
target_record_ref: opp-disa-cloud/action-1
requested_change_summary: Mark action complete from vault edit.
provenance: vault-edit:existing
review_status: pending_review
risk_notes: Action state changes require normal action review.
---

# Existing Mirror Update Proposal
""",
        encoding="utf-8",
    )

    report = scan_vault_for_mirror_update_proposals(vault_root)
    pending = list_pending_mirror_update_proposals(vault_root)

    assert report.created_count == 0
    assert report.pending_count == 1
    assert pending.pending_count == 1
    assert pending.proposals[0].proposal_id == "mirror_update_existing"
