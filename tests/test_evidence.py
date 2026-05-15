import pytest
from pydantic import ValidationError

from ariadne.evidence import (
    EvidenceKind,
    LocalEvidenceStore,
    create_derived_evidence,
    create_source_evidence,
)


def test_local_evidence_store_persists_source_evidence(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    evidence = create_source_evidence(
        content="Customer said incumbent performance is slipping on response times.",
        source_ref="meeting-notes:2026-05-15",
        opportunity_id="opp-aflcmc-recompete",
    )

    written = store.write(evidence)

    assert written.kind is EvidenceKind.SOURCE
    assert written.id
    assert written.source_ref == "meeting-notes:2026-05-15"
    assert written.opportunity_id == "opp-aflcmc-recompete"
    assert written.derived_from_ids == ()
    assert store.read(written.id) == written
    assert store.list() == [written]


def test_derived_evidence_preserves_lineage_to_source_evidence(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    source = store.write(
        create_source_evidence(
            content="Program office wants stronger transition planning.",
            source_ref="customer-call:2026-05-15",
            opportunity_id="opp-aflcmc-recompete",
        )
    )

    derived = store.write(
        create_derived_evidence(
            content="Transition risk should be tracked in the milestone packet.",
            derived_from_ids=[source.id],
            opportunity_id="opp-aflcmc-recompete",
        )
    )

    assert derived.kind is EvidenceKind.DERIVED
    assert derived.derived_from_ids == (source.id,)
    assert store.read(derived.id) == derived
    assert {item.id for item in store.list()} == {source.id, derived.id}


def test_derived_evidence_requires_lineage() -> None:
    with pytest.raises(ValidationError, match="derived evidence requires derived_from_ids"):
        create_derived_evidence(
            content="Unsupported synthesis should not become evidence.",
            derived_from_ids=[],
        )
