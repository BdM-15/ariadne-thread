from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class CaptureResearchRunStatus(StrEnum):
    PLANNED = "planned"
    AWAITING_APPROVAL = "awaiting_approval"
    COLLECTING = "collecting"
    INTERPRETING = "interpreting"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class CaptureResearchLens(StrEnum):
    CUSTOMER_RESEARCH = "customer_research"
    COMPETITIVE_POSITIONING = "competitive_positioning"
    PRODUCT_POSITIONING = "product_positioning"
    SALES_ENABLEMENT = "sales_enablement"
    PRICE_TO_WIN = "price_to_win"
    WORKLOAD_ANALYSIS = "workload_analysis"
    CALL_PLAN_CRO = "call_plan_cro"


class SourceProfileType(StrEnum):
    PIID_CONTRACT_INTELLIGENCE_PROFILE = "piid_contract_intelligence_profile"
    SAM_GOV_ENRICHMENT_PROFILE = "sam_gov_enrichment_profile"
    OPPORTUNITY = "opportunity"
    OPPORTUNITY_KNOWLEDGE_CONTEXT = "opportunity_knowledge_context"


class SourceProfileRef(BaseModel):
    source_profile_type: SourceProfileType
    source_profile_id: str
    source_element_key: str
    source_element_summary: str

    @model_validator(mode="after")
    def validate_stable_ref(self) -> SourceProfileRef:
        if not self.source_profile_id.strip():
            raise ValueError("source_profile_id is required")
        if not self.source_element_key.strip():
            raise ValueError("source_element_key is required")
        if not self.source_element_summary.strip():
            raise ValueError("source_element_summary is required")
        return self


class UserPromptedResearchRequest(BaseModel):
    id: str
    prompt: str
    opportunity_id: str | None = None
    source_targets: tuple[str, ...]
    source_limits: tuple[str, ...]
    created_at: str

    @model_validator(mode="after")
    def validate_bounded_prompt(self) -> UserPromptedResearchRequest:
        if not self.prompt.strip():
            raise ValueError("prompt is required")
        if not self.source_targets:
            raise ValueError("source_targets are required")
        if not self.source_limits:
            raise ValueError("source_limits are required")
        return self


class ResearchTriggerContext(BaseModel):
    trigger_type: str
    summary: str
    captured_at: str


class CaptureResearchBrief(BaseModel):
    research_question: str
    known_pivots: tuple[str, ...] = ()
    source_targets: tuple[str, ...]
    selected_lenses: tuple[CaptureResearchLens, ...]
    evidence_goals: tuple[str, ...] = ()
    source_limits: tuple[str, ...]
    approval_basis: str = "user_triggered"

    @model_validator(mode="after")
    def validate_bounded_brief(self) -> CaptureResearchBrief:
        if not self.research_question.strip():
            raise ValueError("research_question is required")
        if not self.source_targets:
            raise ValueError("source_targets are required")
        if not self.selected_lenses:
            raise ValueError("selected_lenses are required")
        if not self.source_limits:
            raise ValueError("source_limits are required")
        return self


class CaptureResearchRun(BaseModel):
    research_run_id: str
    opportunity_id: str | None = None
    status: CaptureResearchRunStatus = CaptureResearchRunStatus.PLANNED
    research_brief: CaptureResearchBrief
    research_trigger_context: ResearchTriggerContext
    user_prompt: UserPromptedResearchRequest | None = None
    selected_lenses: tuple[CaptureResearchLens, ...]
    source_profile_refs: tuple[SourceProfileRef, ...] = ()
    seller_baseline_refs: tuple[str, ...] = ()
    source_collection_records: tuple[dict[str, object], ...] = ()
    source_findings: tuple[dict[str, object], ...] = ()
    insight_candidates: tuple[dict[str, object], ...] = ()
    downstream_candidates: tuple[dict[str, object], ...] = ()
    research_summary_view: str | None = None
    capability_run_refs: tuple[str, ...] = ()
    review_decisions: tuple[dict[str, object], ...] = ()
    created_at: str
    updated_at: str
    version: int = Field(default=1, ge=1)


class CaptureResearchStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def write(self, run: CaptureResearchRun) -> CaptureResearchRun:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(run.research_run_id).write_text(
            run.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return run

    def read(self, research_run_id: str) -> CaptureResearchRun:
        return CaptureResearchRun.model_validate_json(
            self._path(research_run_id).read_text(encoding="utf-8")
        )

    def list(
        self,
        *,
        opportunity_id: str | None = None,
        status: CaptureResearchRunStatus | None = None,
    ) -> list[CaptureResearchRun]:
        if not self.root.exists():
            return []
        runs = [
            self.read(path.name.removesuffix(".json"))
            for path in sorted(self.root.glob("*.json"))
        ]
        if opportunity_id is not None:
            runs = [run for run in runs if run.opportunity_id == opportunity_id]
        if status is not None:
            runs = [run for run in runs if run.status is status]
        return runs

    def _path(self, research_run_id: str) -> Path:
        if not research_run_id or research_run_id != Path(research_run_id).name:
            raise ValueError("research_run_id must be a file-safe identifier")
        return self.root / f"{research_run_id}.json"


def create_user_prompted_research_run(
    prompt: str,
    *,
    opportunity_id: str | None = None,
    selected_lenses: tuple[CaptureResearchLens, ...],
    source_targets: tuple[str, ...],
    source_limits: tuple[str, ...],
    evidence_goals: tuple[str, ...] = (),
    known_pivots: tuple[str, ...] = (),
    created_at: str | None = None,
) -> CaptureResearchRun:
    timestamp = created_at or datetime.now(UTC).isoformat()
    prompt_request = UserPromptedResearchRequest(
        id=f"user_prompt_{uuid4().hex}",
        prompt=prompt.strip(),
        opportunity_id=opportunity_id,
        source_targets=tuple(source_targets),
        source_limits=tuple(source_limits),
        created_at=timestamp,
    )
    brief = CaptureResearchBrief(
        research_question=prompt_request.prompt,
        known_pivots=tuple(known_pivots),
        source_targets=prompt_request.source_targets,
        selected_lenses=tuple(selected_lenses),
        evidence_goals=tuple(evidence_goals),
        source_limits=prompt_request.source_limits,
    )
    return CaptureResearchRun(
        research_run_id=f"capture_research_run_{uuid4().hex}",
        opportunity_id=opportunity_id,
        research_brief=brief,
        research_trigger_context=ResearchTriggerContext(
            trigger_type="user_prompted_research_request",
            summary=prompt_request.prompt,
            captured_at=timestamp,
        ),
        user_prompt=prompt_request,
        selected_lenses=brief.selected_lenses,
        created_at=timestamp,
        updated_at=timestamp,
    )


def create_source_context_research_run(
    trigger_summary: str,
    *,
    opportunity_id: str | None = None,
    source_profile_refs: tuple[SourceProfileRef, ...],
    selected_lenses: tuple[CaptureResearchLens, ...],
    source_targets: tuple[str, ...],
    source_limits: tuple[str, ...],
    prompt: str | None = None,
    evidence_goals: tuple[str, ...] = (),
    known_pivots: tuple[str, ...] = (),
    created_at: str | None = None,
) -> CaptureResearchRun:
    if not trigger_summary.strip():
        raise ValueError("trigger_summary is required")
    if not source_profile_refs:
        raise ValueError("source_profile_refs are required")
    timestamp = created_at or datetime.now(UTC).isoformat()
    prompt_request = None
    if prompt is not None:
        prompt_request = UserPromptedResearchRequest(
            id=f"user_prompt_{uuid4().hex}",
            prompt=prompt.strip(),
            opportunity_id=opportunity_id,
            source_targets=tuple(source_targets),
            source_limits=tuple(source_limits),
            created_at=timestamp,
        )
    research_question = prompt_request.prompt if prompt_request else trigger_summary.strip()
    brief = CaptureResearchBrief(
        research_question=research_question,
        known_pivots=tuple(known_pivots),
        source_targets=tuple(source_targets),
        selected_lenses=tuple(selected_lenses),
        evidence_goals=tuple(evidence_goals),
        source_limits=tuple(source_limits),
        approval_basis="source_profile_context",
    )
    return CaptureResearchRun(
        research_run_id=f"capture_research_run_{uuid4().hex}",
        opportunity_id=opportunity_id,
        research_brief=brief,
        research_trigger_context=ResearchTriggerContext(
            trigger_type="source_profile_context",
            summary=trigger_summary.strip(),
            captured_at=timestamp,
        ),
        user_prompt=prompt_request,
        selected_lenses=brief.selected_lenses,
        source_profile_refs=tuple(source_profile_refs),
        created_at=timestamp,
        updated_at=timestamp,
    )