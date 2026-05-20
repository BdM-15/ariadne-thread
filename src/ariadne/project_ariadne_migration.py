from pathlib import Path

from pydantic import BaseModel

from ariadne.knowledge_vault import ensure_knowledge_vault_scaffold


class ProjectAriadneMigrationCoverageItem(BaseModel):
    source_path: str
    status: str
    target_path: str | None = None
    reason: str | None = None


class ProjectAriadneMigrationReport(BaseModel):
    corpus_root: str
    vault_root: str
    coverage_report_path: str
    incorporated_count: int
    skipped_count: int
    pending_count: int
    incorporated: tuple[ProjectAriadneMigrationCoverageItem, ...]
    skipped: tuple[ProjectAriadneMigrationCoverageItem, ...]
    pending: tuple[ProjectAriadneMigrationCoverageItem, ...]


def migrate_project_ariadne_slice(
    corpus_root: Path | str,
    vault_root: Path | str,
    *,
    source_relative_paths: tuple[str, ...],
) -> ProjectAriadneMigrationReport:
    source_root = Path(corpus_root)
    target_root = Path(vault_root)
    ensure_knowledge_vault_scaffold(target_root)

    requested_paths = tuple(_normalize_path(path) for path in source_relative_paths)
    incorporated: list[ProjectAriadneMigrationCoverageItem] = []
    skipped: list[ProjectAriadneMigrationCoverageItem] = []

    for source_path in requested_paths:
        source_file = source_root / Path(source_path)
        if not source_file.exists():
            skipped.append(
                ProjectAriadneMigrationCoverageItem(
                    source_path=source_path,
                    status="skipped",
                    reason="source file missing",
                )
            )
            continue
        if source_file.suffix.lower() != ".md":
            skipped.append(
                ProjectAriadneMigrationCoverageItem(
                    source_path=source_path,
                    status="skipped",
                    reason="only Markdown source files are migrated by this tracer",
                )
            )
            continue

        source_text = source_file.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(source_text)
        target_path = _target_source_summary_path(source_path)
        target_file = target_root / target_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            _source_summary_page(source_path, source_text, frontmatter),
            encoding="utf-8",
        )
        incorporated.append(
            ProjectAriadneMigrationCoverageItem(
                source_path=source_path,
                status="incorporated",
                target_path=target_path,
            )
        )

    pending = tuple(
        ProjectAriadneMigrationCoverageItem(source_path=path, status="pending")
        for path in _discover_markdown_paths(source_root)
        if path not in requested_paths
    )
    coverage_report_path = "migration/project-ariadne-coverage.md"
    coverage_file = target_root / coverage_report_path
    coverage_file.parent.mkdir(parents=True, exist_ok=True)
    report = ProjectAriadneMigrationReport(
        corpus_root=str(source_root),
        vault_root=str(target_root),
        coverage_report_path=coverage_report_path,
        incorporated_count=len(incorporated),
        skipped_count=len(skipped),
        pending_count=len(pending),
        incorporated=tuple(incorporated),
        skipped=tuple(skipped),
        pending=pending,
    )
    coverage_file.write_text(_coverage_report_page(report), encoding="utf-8")
    return report


def _target_source_summary_path(source_path: str) -> str:
    return f"source-summaries/project-ariadne/{Path(source_path).stem}.md"


def _source_summary_page(
    source_path: str,
    source_text: str,
    frontmatter: dict[str, str],
) -> str:
    title = frontmatter.get("title") or Path(source_path).stem.replace("-", " ").title()
    summary = _body_without_frontmatter(source_text).strip()
    relationships = _relationship_hints(source_path, frontmatter, summary)
    relationship_lines = "\n".join(
        f"- `{relationship}`" for relationship in relationships
    )
    return f"""---
page_type: source_summary
title: {title}
source_refs: [project-ariadne:{source_path}]
relationships: [{", ".join(relationships)}]
migration_status: incorporated
source_corpus: project-ariadne
source_path: {source_path}
source_updated: {frontmatter.get("updated", "unknown")}
---

# {title}

## Migration Status

- Status: incorporated
- Source corpus: Project Ariadne temporary corpus
- Source path: `{source_path}`
- Target role: Ariadne-native source summary in the canonical LLM-wiki vault

## Source Summary

{summary or "No source body was available in the migrated note."}

## Relationship Links

{relationship_lines}

## Reusable Insight Candidate Status

- Candidate status: needs review before becoming a durable reusable insight.
- Candidate target: `reusable-insights/{Path(source_path).stem}`

## Structured Store Boundary

This migrated page is global reference context, not opportunity-specific Evidence.
Opportunity answers, Evidence Items, actions, review decisions, and trusted
workflow records remain in Ariadne structured stores.
"""


def _coverage_report_page(report: ProjectAriadneMigrationReport) -> str:
    incorporated_lines = _coverage_lines(report.incorporated)
    skipped_lines = _coverage_lines(report.skipped)
    pending_lines = _coverage_lines(report.pending)
    return f"""---
page_type: source_summary
title: Project Ariadne Migration Coverage
source_refs: [project-ariadne:coverage]
relationships: [derived_from:project-ariadne/knowledge]
migration_status: coverage
---

# Project Ariadne Migration Coverage

## Counts

- incorporated: {report.incorporated_count}
- skipped: {report.skipped_count}
- pending: {report.pending_count}

## Incorporated

{incorporated_lines}

## Skipped

{skipped_lines}

## Pending

{pending_lines}

## Boundary

This report tracks migration coverage only. It does not preserve Project Ariadne
as an enduring second reference home.
"""


def _coverage_lines(items: tuple[ProjectAriadneMigrationCoverageItem, ...]) -> str:
    if not items:
        return "- None"
    lines = []
    for item in items:
        suffix = f" -> `{item.target_path}`" if item.target_path else ""
        reason = f" ({item.reason})" if item.reason else ""
        lines.append(f"- `{item.source_path}`: {item.status}{suffix}{reason}")
    return "\n".join(lines)


def _relationship_hints(
    source_path: str,
    frontmatter: dict[str, str],
    summary: str,
) -> tuple[str, ...]:
    stem = Path(source_path).stem
    relationships = [f"derived_from:project-ariadne/{source_path}"]
    entity_type = frontmatter.get("entity_type", "")
    haystack = f"{entity_type}\n{summary}".lower()
    if "customer" in haystack:
        relationships.append("informs:data-elements/customer")
        relationships.append("suggests_route:workflow/customer-engagement")
    if "decision" in haystack or "qualification" in haystack:
        relationships.append("applies_to_gate:milestone_1")
    relationships.append(f"candidate_reusable_insight:reusable-insights/{stem}")
    return tuple(dict.fromkeys(relationships))


def _discover_markdown_paths(corpus_root: Path) -> tuple[str, ...]:
    if not corpus_root.exists():
        return ()
    return tuple(
        _normalize_path(path.relative_to(corpus_root).as_posix())
        for path in sorted(corpus_root.rglob("*.md"))
    )


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _parse_frontmatter(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    frontmatter: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator:
            frontmatter[key.strip()] = value.strip().strip("'").strip('"')
    return frontmatter


def _body_without_frontmatter(markdown: str) -> str:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return markdown
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :]).strip()
    return markdown