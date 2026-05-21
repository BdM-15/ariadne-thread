from pathlib import Path


MAP_PATH = Path("docs/architecture/mvp-2-skill-decomposition-map.md")


THESEUS_SKILL_FAMILIES = (
    "proposal-generator",
    "competitive-intel",
    "compliance-auditor",
    "rfp-reverse-engineer",
    "workload-analyzer",
    "data-analyzer",
    "subcontractor-sow-builder",
    "govcon-ontology",
)


REVIEW_DESTINATIONS = (
    "Packet Field Answer candidate",
    "Call Plan signal",
    "Action Plan recommendation",
    "Capture Research candidate",
    "Artifact Content Block",
    "Capability Run Output",
)


def test_mvp2_decomposition_map_covers_required_theseus_skill_families() -> None:
    text = MAP_PATH.read_text(encoding="utf-8")

    for skill_family in THESEUS_SKILL_FAMILIES:
        assert f"`{skill_family}`" in text

    assert "Theseus inspiration only" in text
    assert "not copied wholesale" in text


def test_mvp2_decomposition_map_names_statuses_and_destinations() -> None:
    text = MAP_PATH.read_text(encoding="utf-8")

    for status in (
        "runnable-now",
        "dependency-gated",
        "deferred",
        "utility/reference",
        "inspiration-only",
    ):
        assert status in text

    for destination in REVIEW_DESTINATIONS:
        assert destination in text

    assert "no parser/RAG/graph/rendering runtime expansion" in text
    assert "one repeatable outcome" in text