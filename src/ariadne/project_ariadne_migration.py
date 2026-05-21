from pathlib import Path

from pydantic import BaseModel

from ariadne.knowledge_vault import ensure_knowledge_vault_scaffold


class ProjectAriadneMigrationCoverageItem(BaseModel):
    source_path: str
    status: str
    target_path: str | None = None
    native_target_paths: tuple[str, ...] = ()
    classification: str | None = None
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


def migrate_project_ariadne_corpus(
    corpus_root: Path | str,
    vault_root: Path | str,
) -> ProjectAriadneMigrationReport:
    source_root = Path(corpus_root)
    return migrate_project_ariadne_slice(
        source_root,
        vault_root,
        source_relative_paths=_discover_markdown_paths(source_root),
    )


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
        classification = _classify_source_path(source_path)
        target_path = _target_source_summary_path(source_path)
        target_file = target_root / target_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            _source_summary_page(
                source_path,
                source_text,
                frontmatter,
                classification=classification,
            ),
            encoding="utf-8",
        )
        native_target_paths = _write_native_pages_for_source(
            source_path=source_path,
            source_text=source_text,
            frontmatter=frontmatter,
            classification=classification,
            vault_root=target_root,
        )
        incorporated.append(
            ProjectAriadneMigrationCoverageItem(
                source_path=source_path,
                status="incorporated",
                target_path=target_path,
                native_target_paths=native_target_paths,
                classification=classification,
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
    _write_theseus_complementary_context(target_root)
    _write_native_relationship_map(target_root, report)
    coverage_file.write_text(_coverage_report_page(report), encoding="utf-8")
    return report


def _target_source_summary_path(source_path: str) -> str:
    return f"source-summaries/project-ariadne/{source_path}"


def _source_summary_page(
    source_path: str,
    source_text: str,
    frontmatter: dict[str, str],
    *,
    classification: str,
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
knowledge_role: {classification}
source_corpus: project-ariadne
source_path: {source_path}
source_updated: {frontmatter.get("updated", "unknown")}
---

# {title}

## Migration Status

- Status: incorporated
- Knowledge role: `{classification}`
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

This report tracks migration coverage only. The old corpus retained until maintainer retirement approval;
it should not remain an enduring second reference home after native vault coverage is accepted.
"""


def _coverage_lines(items: tuple[ProjectAriadneMigrationCoverageItem, ...]) -> str:
    if not items:
        return "- None"
    lines = []
    for item in items:
        suffix = f" -> `{item.target_path}`" if item.target_path else ""
        native = (
            f"; native: {', '.join(f'`{path}`' for path in item.native_target_paths)}"
            if item.native_target_paths
            else ""
        )
        classification = f" [{item.classification}]" if item.classification else ""
        reason = f" ({item.reason})" if item.reason else ""
        lines.append(
            f"- `{item.source_path}`: {item.status}{classification}{suffix}{native}{reason}"
        )
    return "\n".join(lines)


def _write_native_pages_for_source(
    *,
    source_path: str,
    source_text: str,
    frontmatter: dict[str, str],
    classification: str,
    vault_root: Path,
) -> tuple[str, ...]:
    if classification != "artifact_pattern":
        target_path = _native_context_path(source_path, classification)
        if target_path is None:
            return ()
        target_file = vault_root / target_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            _native_context_page(
                source_path,
                source_text,
                frontmatter,
                classification=classification,
            ),
            encoding="utf-8",
        )
        return (target_path,)

    target_path = _artifact_pattern_path(source_path)
    target_file = vault_root / target_path
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(
        _artifact_pattern_page(source_path, source_text, frontmatter),
        encoding="utf-8",
    )
    return (target_path,)


def _native_context_path(source_path: str, classification: str) -> str | None:
    if classification == "milestone_gate_reference":
        return f"milestones/project-ariadne/{source_path}"
    if classification == "seller_capability_or_entity":
        return f"entities/project-ariadne/{source_path}"
    if classification in _CAPTURE_CONCEPT_CLASSIFICATIONS:
        return f"capture-concepts/project-ariadne/{source_path}"
    return None


_CAPTURE_CONCEPT_CLASSIFICATIONS = frozenset(
    {
        "capture_methodology",
        "shipley_methodology",
        "evaluation_methodology",
        "regulatory_reference",
        "workload_pricing_reference",
        "lessons_learned_reference",
        "competitive_intelligence_reference",
    }
)


def _native_context_page(
    source_path: str,
    source_text: str,
    frontmatter: dict[str, str],
    *,
    classification: str,
) -> str:
    title = _title_for_source(source_path, frontmatter)
    summary = _body_without_frontmatter(source_text).strip()
    page_type = _native_page_type(classification)
    relationships = _native_relationships(
        source_path, frontmatter, summary, classification
    )
    relationship_lines = "\n".join(
        f"- `{relationship}`" for relationship in relationships
    )
    return f"""---
page_type: {page_type}
title: {title}
source_refs: [project-ariadne:{source_path}]
relationships: [{", ".join(relationships)}]
source_corpus: project-ariadne
source_path: {source_path}
knowledge_role: {classification}
---

# {title}

## Native Vault Role

This page is Ariadne-native connected knowledge derived from the Project Ariadne
source corpus. It exists so source summaries are not a dead archive: concepts,
milestone gates, and seller-capability context can route capture work.

## Working Summary

{summary or "No source body was available in the migrated note."}

## Relationship Links

{relationship_lines}

## Boundary

This page is global Capture Reference Context. It can inform route selection,
capture research, call planning, packet gaps, and artifact prep, but it is not
opportunity-specific Evidence or a trusted Packet Field Answer.
"""


def _title_for_source(source_path: str, frontmatter: dict[str, str]) -> str:
    return (
        frontmatter.get("title")
        or Path(source_path).stem.replace("_", " ").replace("-", " ").title()
    )


def _native_page_type(classification: str) -> str:
    if classification == "seller_capability_or_entity":
        return "entity"
    return "capture_concept"


def _native_relationships(
    source_path: str,
    frontmatter: dict[str, str],
    summary: str,
    classification: str,
) -> tuple[str, ...]:
    relationships = list(_relationship_hints(source_path, frontmatter, summary))
    relationships.append(f"uses_source:{_source_summary_ref(source_path)}")
    if classification == "milestone_gate_reference":
        relationships.extend(
            (
                f"applies_to_gate:{_milestone_gate_ref(source_path)}",
                "informs:data-elements/approval_criteria",
                "suggests_route:workflow/opportunity-activation",
                "suggests_route:workflow/packet-field-action-matrix",
            )
        )
    elif classification == "seller_capability_or_entity":
        relationships.extend(
            (
                "informs:data-elements/seller_capabilities",
                "suggests_route:workflow/seller-capability-baseline",
                "suggests_route:workflow/capture-research",
            )
        )
    elif classification in _CAPTURE_CONCEPT_CLASSIFICATIONS:
        relationships.extend(
            (
                "suggests_route:workflow/capture-research",
                "suggests_route:workflow/capture-mentoring",
            )
        )
    return tuple(dict.fromkeys(relationships))


def _source_summary_ref(source_path: str) -> str:
    return f"source-summaries/project-ariadne/{source_path.removesuffix('.md')}"


def _milestone_gate_ref(source_path: str) -> str:
    stem = Path(source_path).stem.lower()
    if stem.startswith("ms1"):
        return "milestone_1"
    if stem.startswith("ms2"):
        return "milestone_2"
    if stem.startswith("ms3"):
        return "milestone_3"
    if stem.startswith("ms4"):
        return "milestone_4"
    return "milestone_review"


def _artifact_pattern_path(source_path: str) -> str:
    return f"artifact-patterns/project-ariadne/{source_path}"


def _artifact_pattern_page(
    source_path: str,
    source_text: str,
    frontmatter: dict[str, str],
) -> str:
    title = (
        frontmatter.get("title")
        or Path(source_path).stem.replace("_", " ").replace("-", " ").title()
    )
    summary = _body_without_frontmatter(source_text).strip()
    data_elements = _artifact_data_elements(source_path, summary)
    relationships = tuple(
        dict.fromkeys(
            (
                f"derived_from:project-ariadne/{source_path}",
                *(
                    f"expects_data_element:data-elements/{data_element}"
                    for data_element in data_elements
                ),
                f"maps_to_artifact_block:artifact-block/{_artifact_block_slug(source_path)}",
                "suggests_route:workflow/artifact-assembly",
            )
        )
    )
    relationship_lines = "\n".join(
        f"- `{relationship}`" for relationship in relationships
    )
    data_element_lines = "\n".join(
        f"- `{data_element}`" for data_element in data_elements
    )
    return f"""---
page_type: artifact_pattern
title: {title}
source_refs: [project-ariadne:{source_path}]
relationships: [{", ".join(relationships)}]
source_corpus: project-ariadne
source_path: {source_path}
---

# {title}

## Artifact Expectation Role

This page captures reusable data expectations from a Project Ariadne template or
work-product pattern. Private source formats remain local or ignored; Ariadne
tracks public-like data elements, evidence expectations, and review routes.

## Expected Data Elements

{data_element_lines or "- `primary_scope`"}

## Source Pattern Summary

{summary or "No source body was available in the migrated artifact pattern."}

## Relationship Links

{relationship_lines}

## Boundary

This artifact pattern is not an opportunity-specific Packet Field Answer,
Evidence Item, Artifact Block Review, or renderer export profile. It can guide
Ariadne in finding and filling required data elements before a private format is
rendered through a future Artifact Export Profile.
"""


def _artifact_data_elements(source_path: str, summary: str) -> tuple[str, ...]:
    haystack = f"{source_path}\n{summary}".lower()
    elements: list[str] = []
    if "customer" in haystack:
        elements.extend(("customer", "customer_hot_buttons"))
    if "risk" in haystack:
        elements.append("risks")
    if "pwin" in haystack or "win probability" in haystack:
        elements.append("pwin")
    if "value" in haystack or "contract" in haystack:
        elements.append("total_contract_value")
    if "approval" in haystack or "milestone" in haystack or "decision" in haystack:
        elements.append("approval_criteria")
    if "scope" in haystack or "requirements" in haystack:
        elements.append("primary_scope")
    return tuple(dict.fromkeys(elements or ["primary_scope"]))


def _write_theseus_complementary_context(vault_root: Path) -> None:
    path = (
        vault_root / "skills-capabilities" / "capability-theseus-solicitation-parser.md"
    )
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_theseus_complementary_context_page(), encoding="utf-8")


def _write_native_relationship_map(
    vault_root: Path,
    report: ProjectAriadneMigrationReport,
) -> None:
    path = vault_root / "relationships" / "project-ariadne-native-relationship-map.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_native_relationship_map_page(report), encoding="utf-8")


def _native_relationship_map_page(report: ProjectAriadneMigrationReport) -> str:
    relationship_refs = _relationship_refs_from_report(report)
    relationship_lines = "\n".join(
        f"- `{relationship}`" for relationship in relationship_refs
    )
    native_count = sum(1 for item in report.incorporated if item.native_target_paths)
    return f"""---
page_type: relationship
title: Project Ariadne Native Relationship Map
source_refs: [project-ariadne:coverage]
relationships: [{", ".join(relationship_refs)}]
---

# Project Ariadne Native Relationship Map

## Map Role

This page summarizes first-pass connections between Project Ariadne source
summary pages and native concept/entity/artifact pages. It is an index for
relationship hygiene, not a replacement for individual page frontmatter.

## Counts

- source summary pages: {report.incorporated_count}
- native concept/entity/artifact pages: {native_count}
- pending source pages: {report.pending_count}

## Connection Families

{relationship_lines}

## Boundary

These links are deterministic first-pass routes from source text, path family,
and frontmatter. They need human review before becoming refined reusable insight
or trusted opportunity-specific knowledge.
"""


def _relationship_refs_from_report(
    report: ProjectAriadneMigrationReport,
) -> tuple[str, ...]:
    relationships: list[str] = [
        "derived_from:project-ariadne/knowledge",
        "uses_source:source-summaries/project-ariadne",
    ]
    for item in report.incorporated:
        if item.classification in _CAPTURE_CONCEPT_CLASSIFICATIONS:
            relationships.extend(
                (
                    "suggests_route:workflow/capture-research",
                    "informs:data-elements/evaluation_factors",
                )
            )
        if item.classification == "milestone_gate_reference":
            relationships.extend(
                (
                    "applies_to_gate:milestone_review",
                    "informs:data-elements/approval_criteria",
                )
            )
        if item.classification == "seller_capability_or_entity":
            relationships.extend(
                (
                    "informs:data-elements/seller_capabilities",
                    "suggests_route:workflow/seller-capability-baseline",
                )
            )
        if item.classification == "artifact_pattern":
            relationships.extend(
                (
                    "expects_data_element:data-elements/risks",
                    "suggests_route:workflow/artifact-assembly",
                )
            )
    return tuple(dict.fromkeys(relationships))


def _theseus_complementary_context_page() -> str:
    relationships = (
        "uses_capability:capability/theseus-solicitation-parser",
        "suggests_route:workflow/document-intake",
        "suggests_route:workflow/solicitation-analysis",
        "informs:data-elements/customer_hot_buttons",
        "informs:data-elements/evaluation_factors",
        "informs:data-elements/approval_criteria",
        "candidate_reusable_insight:reusable-insights/theseus-ontology-signal-mapping",
    )
    relationship_lines = "\n".join(
        f"- `{relationship}`" for relationship in relationships
    )
    return f"""---
page_type: workflow_capability
title: Project Theseus Solicitation Parser
source_refs: [project-theseus:solicitation-parser-candidate, ariadne-adr:0006]
relationships: [{", ".join(relationships)}]
category: capability_module
readiness: deferred_adapter
---

# Project Theseus Solicitation Parser

## Complementary Role

Project Theseus is complementary solicitation-parser and ontology context for
RFP-like documents. It can help identify requirements, evaluation factors,
customer hot buttons, risks, discriminators, dates, and relationship candidates.

## Ariadne Boundary

Theseus-style parsing should produce an Extraction Bundle with source spans,
entity candidates, relationship candidates, warnings, confidence, and parser
provenance. It does not write trusted Ariadne records, Packet Field Answers,
Evidence Items, review decisions, or artifact blocks directly.

## Relationship Links

{relationship_lines}
"""


def _classify_source_path(source_path: str) -> str:
    if source_path.startswith("pursuits/_template/"):
        return "artifact_pattern"
    if source_path.startswith("domain_intel/milestones/"):
        return "milestone_gate_reference"
    if source_path.startswith("domain_intel/capabilities/"):
        return "seller_capability_or_entity"
    if source_path.startswith("global_wiki/shipley/"):
        return "shipley_methodology"
    if source_path.startswith("global_wiki/evaluation/"):
        return "evaluation_methodology"
    if source_path.startswith("global_wiki/regulations/"):
        return "regulatory_reference"
    if source_path.startswith("global_wiki/workload/"):
        return "workload_pricing_reference"
    if source_path.startswith("global_wiki/lessons_learned/"):
        return "lessons_learned_reference"
    if source_path.startswith("global_wiki/capture/"):
        return "capture_methodology"
    if source_path.startswith("competitor_intel/"):
        return "competitive_intelligence_reference"
    return "source_summary"


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
    if "hot button" in haystack:
        relationships.append("informs:data-elements/customer_hot_buttons")
    if "evaluation" in haystack:
        relationships.append("informs:data-elements/evaluation_factors")
    if "decision" in haystack or "qualification" in haystack:
        relationships.append("applies_to_gate:milestone_1")
    if source_path.startswith("pursuits/_template/"):
        relationships.append(
            f"maps_to_artifact_block:artifact-block/{_artifact_block_slug(source_path)}"
        )
    relationships.append(f"candidate_reusable_insight:reusable-insights/{stem}")
    return tuple(dict.fromkeys(relationships))


def _artifact_block_slug(source_path: str) -> str:
    path = Path(source_path)
    parent_name = path.parent.name
    stem = path.stem
    if parent_name and parent_name != "_template":
        return _slug(f"{parent_name}-{stem}")
    return _slug(stem)


def _slug(value: str) -> str:
    return value.replace("_", "-").replace(" ", "-").lower()


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
