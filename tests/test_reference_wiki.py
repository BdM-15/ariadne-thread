from pathlib import Path

from ariadne.reference_wiki import load_reference_wiki


def test_reference_wiki_returns_structured_influences_for_raw_capture_note(
    tmp_path: Path,
) -> None:
    _write_note(
        tmp_path / "global_wiki" / "capture" / "incumbent-analysis-strategy.md",
        """---
title: Incumbent Analysis Strategy
entity_type: concept
---

# Incumbent Analysis Strategy

Incumbent contractors have advantages in customer relationships, performance history,
and transition risk. Counter with proof points, transition plans, and ghosting weak
response times.
""",
    )
    _write_note(
        tmp_path / "global_wiki" / "capture" / "customer-hot-buttons.md",
        """---
title: Customer Hot Button Identification
entity_type: concept
---

# Customer Hot Buttons

Customer complaints, response times, decision-maker priorities, and mission risk
signals should shape capture strategy.
""",
    )
    _write_note(
        tmp_path / "global_wiki" / "shipley" / "proposal-schedule.md",
        """---
title: Proposal Schedule
entity_type: concept
---

# Proposal Schedule

Follow-up actions and review dates keep capture work moving after customer calls.
See [[capture-planning-phase]].
""",
    )

    wiki = load_reference_wiki(tmp_path)
    influences = wiki.find_influences(
        "Customer says the incumbent transition plan is weak and response times "
        "need follow up.",
        limit=7,
    )

    assert len(influences) == 3
    assert influences[0].title == "Incumbent Analysis Strategy"
    assert influences[0].reference_id == "global_wiki/capture/incumbent-analysis-strategy"
    assert influences[0].source_path == "global_wiki/capture/incumbent-analysis-strategy.md"
    assert influences[0].influence_type == "capture_methodology"
    assert "transition risk" in influences[0].excerpt
    assert "customer" in influences[0].why_it_matters.lower()


def test_reference_wiki_considers_note_structure_and_orders_deterministically(
    tmp_path: Path,
) -> None:
    _write_note(
        tmp_path / "foldertoken" / "neutral.md",
        """---
title: Neutral Folder Note
---

No matching body terms.
""",
    )
    _write_note(
        tmp_path / "neutral" / "filenametoken.md",
        """---
title: Neutral Filename Note
---

No matching body terms.
""",
    )
    _write_note(
        tmp_path / "neutral" / "frontmatter.md",
        """---
title: Neutral Frontmatter Note
keywords: frontmattertoken
---

No matching body terms.
""",
    )
    _write_note(
        tmp_path / "neutral" / "heading.md",
        """---
title: Neutral Heading Note
---

# Headingtoken

No matching body terms.
""",
    )
    _write_note(
        tmp_path / "neutral" / "wikilink.md",
        """---
title: Neutral Wikilink Note
---

See [[linkedtopic]].
""",
    )
    _write_note(
        tmp_path / "neutral" / "body.md",
        """---
title: Neutral Body Note
---

Bodytoken appears only in body text.
""",
    )

    wiki = load_reference_wiki(tmp_path)
    influences = wiki.find_influences(
        "foldertoken filenametoken frontmattertoken headingtoken "
        "linkedtopic bodytoken",
        limit=7,
    )
    repeated_influences = wiki.find_influences(
        "foldertoken filenametoken frontmattertoken headingtoken "
        "linkedtopic bodytoken",
        limit=7,
    )

    assert {influence.source_path for influence in influences} == {
        "foldertoken/neutral.md",
        "neutral/body.md",
        "neutral/filenametoken.md",
        "neutral/frontmatter.md",
        "neutral/heading.md",
        "neutral/wikilink.md",
    }
    assert [influence.source_path for influence in influences] == [
        influence.source_path for influence in repeated_influences
    ]


def _write_note(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")