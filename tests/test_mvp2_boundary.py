from pathlib import Path


def _mvp2_section() -> str:
    prd_text = Path("PRD.md").read_text(encoding="utf-8")
    start = prd_text.index("**MVP-2: AI Usage Layer + Skills Integration**")
    end = prd_text.index("**MVP-3: Capture Work Product Loop**")
    return prd_text[start:end]


def test_mvp2_scope_confirms_theseus_decomposition_boundary() -> None:
    section = _mvp2_section()

    assert "MVP-2 boundary" in section
    assert (
        "Theseus skills are inspiration-only unless decomposed into "
        "Ariadne-native focused skills with explicit contracts"
    ) in section
    assert "runnable-now" in section
    assert "dependency-gated" in section
    assert "deferred" in section


def test_mvp2_boundary_keeps_review_gates_and_deferred_runtime_scope() -> None:
    section = _mvp2_section()

    assert "Hermes may propose skill and chain improvements" in section
    assert "must not silently mutate skills, chains, or trusted workflow records" in section
    assert "no LangGraph runtime adoption" in section
    assert "no parser/RAG/graph/rendering expansion" in section
    assert "no automatic trusted downstream writes" in section
    assert "fake-runner tests" in section