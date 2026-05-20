from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel

from ariadne.knowledge_vault import ensure_knowledge_vault_scaffold


PROTECTED_TARGET_RECORD_KINDS = frozenset(
    {
        "packet_field_answer",
        "evidence_item",
        "action_plan_state",
        "review_decision",
        "source_span",
        "capability_run_output",
        "artifact_block_review",
    }
)


class MirrorUpdateProposal(BaseModel):
    proposal_id: str
    proposal_path: str
    source_page: str
    target_record_kind: str
    target_record_ref: str | None
    requested_change_summary: str
    provenance: str
    confidence: str | None = None
    risk_notes: str
    review_status: str = "pending_review"


class MirrorUpdateProposalReport(BaseModel):
    vault_root: str
    proposals: tuple[MirrorUpdateProposal, ...]
    pending_count: int
    created_count: int = 0


def scan_vault_for_mirror_update_proposals(
    vault_root: Path | str,
) -> MirrorUpdateProposalReport:
    root = Path(vault_root)
    ensure_knowledge_vault_scaffold(root)
    existing = list_pending_mirror_update_proposals(root).proposals
    existing_keys = {
        _proposal_key(
            proposal.source_page,
            proposal.target_record_kind,
            proposal.target_record_ref,
        )
        for proposal in existing
    }
    created_count = 0

    for page_path in sorted(root.rglob("*.md")):
        relative_path = page_path.relative_to(root).as_posix()
        if relative_path.startswith("proposals/"):
            continue
        frontmatter = _read_frontmatter(page_path)
        if not frontmatter:
            continue
        proposal = _proposal_from_candidate_page(root, relative_path, frontmatter)
        if proposal is None:
            continue
        key = _proposal_key(
            proposal.source_page,
            proposal.target_record_kind,
            proposal.target_record_ref,
        )
        if key in existing_keys:
            continue
        _write_proposal_page(root, proposal)
        existing_keys.add(key)
        created_count += 1

    return list_pending_mirror_update_proposals(root).model_copy(
        update={"created_count": created_count}
    )


def list_pending_mirror_update_proposals(
    vault_root: Path | str,
) -> MirrorUpdateProposalReport:
    root = Path(vault_root)
    proposals: list[MirrorUpdateProposal] = []
    proposal_root = root / "proposals"
    if proposal_root.exists():
        for page_path in sorted(proposal_root.glob("*.md")):
            frontmatter = _read_frontmatter(page_path)
            if not frontmatter:
                continue
            if frontmatter.get("page_type") != "mirror_update_proposal":
                continue
            if str(frontmatter.get("review_status", "pending_review")) != "pending_review":
                continue
            proposal = _proposal_from_proposal_page(root, page_path, frontmatter)
            if proposal is not None:
                proposals.append(proposal)
    return MirrorUpdateProposalReport(
        vault_root=str(root),
        proposals=tuple(proposals),
        pending_count=len(proposals),
    )


def _proposal_from_candidate_page(
    root: Path,
    relative_path: str,
    frontmatter: dict[str, object],
) -> MirrorUpdateProposal | None:
    target_record_kind = str(frontmatter.get("target_record_kind", "")).strip()
    if target_record_kind not in PROTECTED_TARGET_RECORD_KINDS:
        return None
    requested_change_summary = str(
        frontmatter.get("requested_change_summary", "")
    ).strip()
    if not requested_change_summary:
        return None
    target_record_ref = _optional_str(frontmatter.get("target_record_ref"))
    proposal_id = _proposal_id(relative_path, target_record_kind, target_record_ref)
    provenance = _first_source_ref(frontmatter) or f"vault-page:{relative_path}"
    return MirrorUpdateProposal(
        proposal_id=proposal_id,
        proposal_path=f"proposals/{proposal_id}.md",
        source_page=relative_path,
        target_record_kind=target_record_kind,
        target_record_ref=target_record_ref,
        requested_change_summary=requested_change_summary,
        provenance=str(frontmatter.get("provenance", provenance)).strip(),
        confidence=_optional_str(frontmatter.get("confidence")),
        risk_notes=str(
            frontmatter.get(
                "risk_notes",
                "Vault edits cannot directly update trusted Ariadne records.",
            )
        ).strip(),
        review_status=str(frontmatter.get("review_status", "pending_review")).strip(),
    )


def _proposal_from_proposal_page(
    root: Path,
    page_path: Path,
    frontmatter: dict[str, object],
) -> MirrorUpdateProposal | None:
    source_page = str(frontmatter.get("source_page", "")).strip()
    target_record_kind = str(frontmatter.get("target_record_kind", "")).strip()
    requested_change_summary = str(
        frontmatter.get("requested_change_summary", "")
    ).strip()
    if not source_page or target_record_kind not in PROTECTED_TARGET_RECORD_KINDS:
        return None
    if not requested_change_summary:
        return None
    target_record_ref = _optional_str(frontmatter.get("target_record_ref"))
    proposal_id = str(frontmatter.get("proposal_id", "")).strip() or _proposal_id(
        source_page,
        target_record_kind,
        target_record_ref,
    )
    provenance = str(
        frontmatter.get("provenance", _first_source_ref(frontmatter) or "vault-edit")
    ).strip()
    return MirrorUpdateProposal(
        proposal_id=proposal_id,
        proposal_path=page_path.relative_to(root).as_posix(),
        source_page=source_page,
        target_record_kind=target_record_kind,
        target_record_ref=target_record_ref,
        requested_change_summary=requested_change_summary,
        provenance=provenance,
        confidence=_optional_str(frontmatter.get("confidence")),
        risk_notes=str(
            frontmatter.get(
                "risk_notes",
                "Vault edits cannot directly update trusted Ariadne records.",
            )
        ).strip(),
        review_status=str(frontmatter.get("review_status", "pending_review")).strip(),
    )


def _write_proposal_page(root: Path, proposal: MirrorUpdateProposal) -> None:
    path = root / proposal.proposal_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_proposal_page_template(proposal), encoding="utf-8")


def _proposal_page_template(proposal: MirrorUpdateProposal) -> str:
    target_record_ref = proposal.target_record_ref or "unknown"
    confidence = proposal.confidence or "unknown"
    return f"""---
page_type: mirror_update_proposal
title: Mirror Update Proposal - {proposal.target_record_kind}
source_refs: [{proposal.provenance}]
relationships: [derived_from:{proposal.source_page}]
proposal_id: {proposal.proposal_id}
source_page: {proposal.source_page}
target_record_kind: {proposal.target_record_kind}
target_record_ref: {target_record_ref}
requested_change_summary: {proposal.requested_change_summary}
provenance: {proposal.provenance}
confidence: {confidence}
risk_notes: {proposal.risk_notes}
review_status: {proposal.review_status}
---

# Mirror Update Proposal - {proposal.target_record_kind}

## Requested Change

{proposal.requested_change_summary}

## Target

- Target record kind: `{proposal.target_record_kind}`
- Target record ref: `{target_record_ref}`
- Source page: `[[{proposal.source_page.removesuffix(".md")}]]`

## Guardrail

This proposal is pending review. Vault edits do not directly write trusted
Ariadne workflow records; normal review-gated workflows must accept or reject
the change.

## Risk Notes

{proposal.risk_notes}
"""


def _proposal_key(
    source_page: str,
    target_record_kind: str,
    target_record_ref: str | None,
) -> tuple[str, str, str | None]:
    return (source_page, target_record_kind, target_record_ref)


def _proposal_id(
    source_page: str,
    target_record_kind: str,
    target_record_ref: str | None,
) -> str:
    raw_key = "|".join((source_page, target_record_kind, target_record_ref or ""))
    return f"mirror_update_{sha256(raw_key.encode()).hexdigest()[:12]}"


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text == "unknown":
        return None
    return text


def _first_source_ref(frontmatter: dict[str, object]) -> str | None:
    source_refs = _frontmatter_list(frontmatter.get("source_refs"))
    if not source_refs:
        return None
    return source_refs[0]


def _read_frontmatter(path: Path) -> dict[str, object] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    frontmatter: dict[str, object] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return frontmatter
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        frontmatter[key.strip()] = _parse_frontmatter_value(raw_value.strip())
    return None


def _parse_frontmatter_value(raw_value: str) -> object:
    if raw_value.startswith("[") and raw_value.endswith("]"):
        inner = raw_value[1:-1].strip()
        if not inner:
            return ()
        return tuple(item.strip() for item in inner.split(",") if item.strip())
    return raw_value.strip('"').strip("'")


def _frontmatter_list(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    return ()