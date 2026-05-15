from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class LifecycleState(StrEnum):
    IDENTIFIED = "identified"
    QUALIFIED = "qualified"
    PURSUING = "pursuing"
    BID_DECIDED = "bid_decided"
    SUBMITTED = "submitted"
    AWARDED = "awarded"
    LOST = "lost"
    ARCHIVED = "archived"


class EntryReason(StrEnum):
    NEW_LEAD = "new_lead"
    RECOMPETE = "recompete"
    INCUMBENT_RECOMPETE = "incumbent_recompete"
    URGENT_SOLICITATION = "urgent_solicitation"
    LEGACY_PURSUIT = "legacy_pursuit"


class CoreCaptureWorkstream(StrEnum):
    CUSTOMER_INSIGHT = "customer_insight"
    OPPORTUNITY_REQUIREMENTS = "opportunity_requirements"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    PARTNER_STRATEGY = "partner_strategy"
    SOLUTION_STRATEGY = "solution_strategy"
    PRICE_TO_WIN = "price_to_win"
    WIN_THEMES = "win_themes"
    COMPLIANCE_READINESS = "compliance_readiness"
    RISKS_AND_ACTIONS = "risks_and_actions"
    ARTIFACTS = "artifacts"


class WorkstreamStatus(StrEnum):
    UNASSESSED = "unassessed"
    NEEDS_BACKFILL = "needs_backfill"


class EntryContext(BaseModel):
    reason: EntryReason
    starting_lifecycle_state: LifecycleState
    rationale: str
    missing_or_stale_workstreams: set[CoreCaptureWorkstream] = Field(default_factory=set)


class CaptureWorkstreamState(BaseModel):
    workstream: CoreCaptureWorkstream
    status: WorkstreamStatus = WorkstreamStatus.UNASSESSED


class BackfillNeed(BaseModel):
    workstream: CoreCaptureWorkstream
    rationale: str


class Opportunity(BaseModel):
    name: str
    lifecycle_state: LifecycleState
    entry_context: EntryContext
    workstreams: dict[CoreCaptureWorkstream, CaptureWorkstreamState]
    backfill_needs: list[BackfillNeed]


def create_opportunity(*, name: str, entry_context: EntryContext) -> Opportunity:
    workstreams = {
        workstream: CaptureWorkstreamState(
            workstream=workstream,
            status=(
                WorkstreamStatus.NEEDS_BACKFILL
                if workstream in entry_context.missing_or_stale_workstreams
                else WorkstreamStatus.UNASSESSED
            ),
        )
        for workstream in CoreCaptureWorkstream
    }
    backfill_needs = [
        BackfillNeed(
            workstream=workstream,
            rationale="Missing or stale workstream from opportunity entry context.",
        )
        for workstream in sorted(
            entry_context.missing_or_stale_workstreams,
            key=lambda workstream: workstream.value,
        )
    ]

    return Opportunity(
        name=name,
        lifecycle_state=entry_context.starting_lifecycle_state,
        entry_context=entry_context,
        workstreams=workstreams,
        backfill_needs=backfill_needs,
    )