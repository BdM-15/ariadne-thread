from pathlib import Path

from ariadne.capabilities import (
    CapabilityStatus,
    dependency_gate_for_catalog_entry,
    discover_local_capability_catalog,
)


EXPECTED_GOVCON_CANDIDATES = {
    "rfp-reverse-engineer": {
        "missing_dependency": "solicitation_extraction",
        "decomposition": "evaluation-criteria-extractor",
        "destination": "Document Intake Queue",
    },
    "compliance-auditor": {
        "missing_dependency": "clause_ecfr_readiness",
        "decomposition": "clause-obligation-checker",
        "destination": "Artifact Content Block",
    },
    "workload-analyzer": {
        "missing_dependency": "workload_attachment_intake",
        "decomposition": "staffing-table-profiler",
        "destination": "Capture Research candidate",
    },
    "subcontractor-sow-builder": {
        "missing_dependency": "reviewed_scope_package",
        "decomposition": "subcontractor-assumption-list",
        "destination": "Artifact Content Block",
    },
    "govcon-ontology": {
        "missing_dependency": "ontology_alignment",
        "decomposition": "govcon-term-alignment-checker",
        "destination": "Ariadne Knowledge Vault",
    },
}


def test_govcon_candidates_are_visible_but_dependency_gated() -> None:
    catalog = discover_local_capability_catalog(Path(__file__).resolve().parents[1])
    entries_by_id = {entry.id: entry for entry in catalog.entries}

    for candidate_id, expectation in EXPECTED_GOVCON_CANDIDATES.items():
        entry = entries_by_id[candidate_id]
        assert entry.capability_status is CapabilityStatus.DEPENDENCY_GATED
        assert entry.contract.fake_runner_supported is False
        assert expectation["missing_dependency"] in entry.contract.missing_dependencies
        assert expectation["decomposition"] in entry.contract.decomposition_options
        assert entry.contract.product_workflow_destination == expectation["destination"]
        assert entry.contract.next_enabling_action


def test_dependency_gated_candidates_do_not_plan_execution_or_trusted_writes() -> None:
    catalog = discover_local_capability_catalog(Path(__file__).resolve().parents[1])
    entries_by_id = {entry.id: entry for entry in catalog.entries}

    for candidate_id in EXPECTED_GOVCON_CANDIDATES:
        readiness = dependency_gate_for_catalog_entry(entries_by_id[candidate_id])
        assert readiness.capability_id == candidate_id
        assert readiness.executable is False
        assert readiness.capability_status == "dependency_gated"
        assert readiness.blocked_reason.startswith("Dependency-gated")
        assert readiness.missing_dependencies
        assert readiness.next_enabling_action
        assert readiness.trusted_downstream_writes is False
        assert readiness.review_destination == (
            entries_by_id[candidate_id].contract.review_destination
        )