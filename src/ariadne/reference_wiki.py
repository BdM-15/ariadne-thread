from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class ReferenceInfluenceType(StrEnum):
    CAPTURE_METHODOLOGY = "capture_methodology"
    DOMAIN_INTEL = "domain_intel"
    REGULATION = "regulation"
    EVALUATION = "evaluation"
    LESSON_LEARNED = "lesson_learned"
    PURSUIT_TEMPLATE = "pursuit_template"
    WORKLOAD = "workload"
    REFERENCE_NOTE = "reference_note"


class ReferenceWikiInfluence(BaseModel):
    title: str
    reference_id: str
    source_path: str
    excerpt: str
    why_it_matters: str
    influence_type: ReferenceInfluenceType
    score: float = Field(ge=0)
    matched_terms: tuple[str, ...] = ()


class ReferenceWiki(BaseModel):
    root: Path
    notes: tuple[ReferenceWikiNote, ...]

    def find_influences(
        self,
        content: str,
        *,
        limit: int = 7,
    ) -> tuple[ReferenceWikiInfluence, ...]:
        query_tokens = _normalized_tokens(content)
        if not query_tokens or limit <= 0:
            return ()

        scored_notes = tuple(
            scored_note
            for note in self.notes
            if (scored_note := _score_note(note, query_tokens)).score > 0
        )
        ordered_notes = sorted(
            scored_notes,
            key=lambda scored_note: (-scored_note.score, scored_note.note.source_path),
        )
        return tuple(
            _to_influence(scored_note)
            for scored_note in ordered_notes[: min(limit, 7)]
        )


class ReferenceWikiNote(BaseModel):
    title: str
    reference_id: str
    source_path: str
    excerpt: str
    influence_type: ReferenceInfluenceType
    fields: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class _ScoredReferenceNote:
    note: ReferenceWikiNote
    score: float
    matched_terms: tuple[str, ...]
    matched_fields: tuple[str, ...]


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
_STOP_WORDS = frozenset(
    {
        "about",
        "after",
        "also",
        "and",
        "are",
        "but",
        "for",
        "from",
        "has",
        "have",
        "into",
        "its",
        "need",
        "said",
        "says",
        "that",
        "the",
        "this",
        "with",
    }
)
_FIELD_WEIGHTS = {
    "path": 2.0,
    "filename": 2.5,
    "frontmatter": 2.0,
    "title": 4.0,
    "headings": 3.0,
    "wikilinks": 1.5,
    "body": 1.0,
}


def load_reference_wiki(root: Path | str) -> ReferenceWiki:
    wiki_root = Path(root)
    notes = tuple(
        _load_note(path, wiki_root)
        for path in sorted(wiki_root.rglob("*.md"))
        if path.is_file()
    )
    return ReferenceWiki(root=wiki_root, notes=notes)


def _load_note(path: Path, root: Path) -> ReferenceWikiNote:
    relative_path = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    title = frontmatter.get("title") or _first_heading(body) or _title_from_path(path)
    headings = tuple(_heading_text(line) for line in body.splitlines() if _heading_text(line))
    wikilinks = tuple(match.group(1) for match in _WIKILINK_PATTERN.finditer(body))
    excerpt = _excerpt(frontmatter, body)
    fields = {
        "path": tuple(_normalized_tokens(" ".join(path.relative_to(root).parts[:-1]))),
        "filename": tuple(_normalized_tokens(path.stem.replace("-", " "))),
        "frontmatter": tuple(_normalized_tokens(" ".join(frontmatter.values()))),
        "title": tuple(_normalized_tokens(title)),
        "headings": tuple(_normalized_tokens(" ".join(headings))),
        "wikilinks": tuple(_normalized_tokens(" ".join(wikilinks).replace("-", " "))),
        "body": tuple(_normalized_tokens(body)),
    }
    return ReferenceWikiNote(
        title=title,
        reference_id=relative_path.removesuffix(".md"),
        source_path=relative_path,
        excerpt=excerpt,
        influence_type=_influence_type_for(relative_path),
        fields=fields,
    )


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    frontmatter_lines: list[str] = []
    for line_index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return _parse_frontmatter(frontmatter_lines), "\n".join(lines[line_index + 1 :])
        frontmatter_lines.append(line)
    return {}, text


def _parse_frontmatter(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    current_key: str | None = None
    for line in lines:
        if not line.strip():
            continue
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            key, value = line.split(":", 1)
            current_key = key.strip()
            values[current_key] = value.strip().strip('"').strip("'")
        elif current_key:
            values[current_key] = f"{values[current_key]} {line.strip().lstrip('-').strip()}".strip()
    return values


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        heading = _heading_text(line)
        if heading:
            return heading
    return None


def _heading_text(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return None
    return stripped.lstrip("#").strip() or None


def _title_from_path(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def _excerpt(frontmatter: dict[str, str], body: str) -> str:
    summary = frontmatter.get("summary")
    if summary:
        return _truncate(summary)

    body_lines = tuple(
        line.strip()
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith(">")
    )
    return _truncate(" ".join(body_lines))


def _score_note(
    note: ReferenceWikiNote,
    query_tokens: frozenset[str],
) -> _ScoredReferenceNote:
    score = 0.0
    matched_terms: set[str] = set()
    matched_fields: set[str] = set()
    for field_name, field_terms in note.fields.items():
        matches = query_tokens.intersection(field_terms)
        if not matches:
            continue
        score += len(matches) * _FIELD_WEIGHTS[field_name]
        matched_terms.update(matches)
        matched_fields.add(field_name)

    return _ScoredReferenceNote(
        note=note,
        score=score,
        matched_terms=tuple(sorted(matched_terms)),
        matched_fields=tuple(sorted(matched_fields)),
    )


def _to_influence(scored_note: _ScoredReferenceNote) -> ReferenceWikiInfluence:
    matched_terms = ", ".join(scored_note.matched_terms[:5])
    matched_fields = ", ".join(scored_note.matched_fields)
    why_it_matters = (
        f"Matches raw capture terms ({matched_terms}) in {matched_fields}; "
        "use as background context, not opportunity evidence by itself."
    )
    return ReferenceWikiInfluence(
        title=scored_note.note.title,
        reference_id=scored_note.note.reference_id,
        source_path=scored_note.note.source_path,
        excerpt=scored_note.note.excerpt,
        why_it_matters=why_it_matters,
        influence_type=scored_note.note.influence_type,
        score=scored_note.score,
        matched_terms=scored_note.matched_terms,
    )


def _influence_type_for(relative_path: str) -> ReferenceInfluenceType:
    parts = relative_path.split("/")
    if "domain_intel" in parts:
        return ReferenceInfluenceType.DOMAIN_INTEL
    if "pursuits" in parts:
        return ReferenceInfluenceType.PURSUIT_TEMPLATE
    if "regulations" in parts:
        return ReferenceInfluenceType.REGULATION
    if "evaluation" in parts:
        return ReferenceInfluenceType.EVALUATION
    if "lessons_learned" in parts:
        return ReferenceInfluenceType.LESSON_LEARNED
    if "workload" in parts:
        return ReferenceInfluenceType.WORKLOAD
    if "capture" in parts or "shipley" in parts:
        return ReferenceInfluenceType.CAPTURE_METHODOLOGY
    return ReferenceInfluenceType.REFERENCE_NOTE


def _normalized_tokens(text: str) -> frozenset[str]:
    return frozenset(
        normalized
        for token in _TOKEN_PATTERN.findall(text.lower())
        if (normalized := _normalize_token(token))
    )


def _normalize_token(token: str) -> str | None:
    if len(token) <= 2 or token in _STOP_WORDS:
        return None
    if len(token) > 4 and token.endswith("ies"):
        token = f"{token[:-3]}y"
    elif len(token) > 4 and token.endswith("es"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("s"):
        token = token[:-1]
    if token in _STOP_WORDS:
        return None
    return token


def _truncate(text: str, *, max_length: int = 260) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3].rstrip()}..."