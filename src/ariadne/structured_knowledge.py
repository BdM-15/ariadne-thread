from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from ariadne.action_plans import CaptureActionPlan
from ariadne.capability_runs import (
    CapabilityRun,
    CapabilityRunOutputReviewState,
    CapabilityRunStatus,
    CapabilityRunStore,
)
from ariadne.document_intake import DocumentIntakeStore
from ariadne.evidence import EvidenceItem, LocalEvidenceStore
from ariadne.opportunities import Opportunity
from ariadne.packet_knowledge import PacketFieldAnswer, PacketFieldAnswerStatus
from ariadne.piid_profiles import PiidContractIntelligenceProfile, PiidProfileStore
from ariadne.sam_gov_profiles import SamGovEnrichmentProfile, SamGovProfileStore


class KnowledgeRecordKind(StrEnum):
    OPPORTUNITY = "opportunity"
    EVIDENCE_ITEM = "evidence_item"
    PACKET_FIELD_ANSWER = "packet_field_answer"
    ACTION_PLAN_ITEM = "action_plan_item"
    DOCUMENT_INTAKE_EVIDENCE_LINK = "document_intake_evidence_link"
    PIID_PROFILE = "piid_profile"
    SAM_GOV_PROFILE = "sam_gov_profile"
    CAPABILITY_RUN = "capability_run"
    CAPABILITY_RUN_OUTPUT = "capability_run_output"


class KnowledgeTrustState(StrEnum):
    TRUSTED = "trusted"
    REVIEWABLE = "reviewable"


class StructuredKnowledgeRecordRef(BaseModel):
    kind: KnowledgeRecordKind
    record_id: str
    trust_state: KnowledgeTrustState
    opportunity_id: str | None = None
    title: str
    summary: str | None = None


class StructuredKnowledgeConnection(BaseModel):
    source_kind: KnowledgeRecordKind
    source_id: str
    relationship: str
    target_kind: KnowledgeRecordKind
    target_id: str
    trust_state: KnowledgeTrustState
    provenance: str


class OpportunityKnowledgeProjection(BaseModel):
    opportunity_id: str
    trusted_records: tuple[StructuredKnowledgeRecordRef, ...] = ()
    reviewable_records: tuple[StructuredKnowledgeRecordRef, ...] = ()
    connections: tuple[StructuredKnowledgeConnection, ...] = ()


class KnowledgeContextItem(BaseModel):
    record_kind: KnowledgeRecordKind
    record_id: str
    title: str
    summary: str
    trust_state: KnowledgeTrustState
    status_label: str
    related_connection_count: int = 0


class KnowledgeContextSection(BaseModel):
    count: int
    items: tuple[KnowledgeContextItem, ...] = ()


class KnowledgeGapSummary(BaseModel):
    record_kind: KnowledgeRecordKind
    record_id: str
    summary: str
    command_id: str


class KnowledgeSourceLimitation(BaseModel):
    record_kind: KnowledgeRecordKind
    record_id: str
    summary: str


class KnowledgeCommandLink(BaseModel):
    command_id: str
    label: str
    target_kind: KnowledgeRecordKind
    target_id: str


class OpportunityKnowledgeContextView(BaseModel):
    opportunity_id: str
    trusted_context: KnowledgeContextSection
    reviewable_context: KnowledgeContextSection
    gaps: tuple[KnowledgeGapSummary, ...] = ()
    source_limitations: tuple[KnowledgeSourceLimitation, ...] = ()
    related_profile_ids: tuple[str, ...] = ()
    related_capability_run_ids: tuple[str, ...] = ()
    next_command_links: tuple[KnowledgeCommandLink, ...] = ()


class StructuredKnowledgeIndex(BaseModel):
    records: tuple[StructuredKnowledgeRecordRef, ...]
    connections: tuple[StructuredKnowledgeConnection, ...] = ()

    def for_opportunity(self, opportunity_id: str) -> OpportunityKnowledgeProjection:
        records_by_key = {
            (record.kind, record.record_id): record for record in self.records
        }
        selected_record_keys = {
            key
            for key, record in records_by_key.items()
            if record.opportunity_id == opportunity_id
        }
        changed = True
        while changed:
            changed = False
            for connection in self.connections:
                source_key = (connection.source_kind, connection.source_id)
                target_key = (connection.target_kind, connection.target_id)
                if source_key in selected_record_keys:
                    changed = _add_connected_record_key(
                        target_key,
                        records_by_key=records_by_key,
                        selected_record_keys=selected_record_keys,
                        opportunity_id=opportunity_id,
                    ) or changed
                if target_key in selected_record_keys:
                    changed = _add_connected_record_key(
                        source_key,
                        records_by_key=records_by_key,
                        selected_record_keys=selected_record_keys,
                        opportunity_id=opportunity_id,
                    ) or changed
        selected_records = tuple(
            records_by_key[key] for key in sorted(selected_record_keys, key=_record_key)
        )
        selected_connections = tuple(
            connection
            for connection in self.connections
            if (connection.source_kind, connection.source_id) in selected_record_keys
            and (connection.target_kind, connection.target_id) in selected_record_keys
        )
        return OpportunityKnowledgeProjection(
            opportunity_id=opportunity_id,
            trusted_records=tuple(
                record
                for record in selected_records
                if record.trust_state is KnowledgeTrustState.TRUSTED
            ),
            reviewable_records=tuple(
                record
                for record in selected_records
                if record.trust_state is KnowledgeTrustState.REVIEWABLE
            ),
            connections=selected_connections,
        )


def build_structured_knowledge_index(
    *,
    opportunities: tuple[Opportunity, ...] = (),
    evidence_store: LocalEvidenceStore | None = None,
    document_intake_store: DocumentIntakeStore | None = None,
    piid_profile_store: PiidProfileStore | None = None,
    sam_gov_profile_store: SamGovProfileStore | None = None,
    capability_run_store: CapabilityRunStore | None = None,
    packet_field_answers: tuple[PacketFieldAnswer, ...] = (),
    action_plans: tuple[CaptureActionPlan, ...] = (),
) -> StructuredKnowledgeIndex:
    records: list[StructuredKnowledgeRecordRef] = []
    connections: list[StructuredKnowledgeConnection] = []
    evidence_items = tuple(evidence_store.list()) if evidence_store is not None else ()
    evidence_opportunity_ids = {
        evidence.id: evidence.opportunity_id for evidence in evidence_items
    }

    records.extend(_opportunity_records(opportunities))
    records.extend(_evidence_records(evidence_items))
    connections.extend(_evidence_connections(evidence_items))
    if document_intake_store is not None:
        records.extend(
            _document_intake_link_records(
                document_intake_store,
                evidence_opportunity_ids=evidence_opportunity_ids,
            )
        )
        connections.extend(_document_intake_link_connections(document_intake_store))
    if piid_profile_store is not None:
        records.extend(_piid_profile_records(tuple(piid_profile_store.list())))
    if sam_gov_profile_store is not None:
        records.extend(_sam_gov_profile_records(tuple(sam_gov_profile_store.list())))
    records.extend(_packet_field_answer_records(packet_field_answers))
    records.extend(_action_plan_item_records(action_plans))
    capability_runs = (
        tuple(capability_run_store.list()) if capability_run_store is not None else ()
    )
    records.extend(_capability_run_records(capability_runs))
    records.extend(_capability_run_output_records(capability_runs))
    connections.extend(_packet_field_answer_connections(packet_field_answers))
    connections.extend(_action_plan_item_connections(action_plans))
    if capability_runs:
        connections.extend(
            _capability_run_connections(
                capability_runs,
                record_kinds_by_id={record.record_id: record.kind for record in records},
            )
        )

    return StructuredKnowledgeIndex(records=tuple(records), connections=tuple(connections))


def get_opportunity_knowledge_context(
    *,
    opportunity_id: str,
    opportunities: tuple[Opportunity, ...] = (),
    evidence_store: LocalEvidenceStore | None = None,
    document_intake_store: DocumentIntakeStore | None = None,
    piid_profile_store: PiidProfileStore | None = None,
    sam_gov_profile_store: SamGovProfileStore | None = None,
    capability_run_store: CapabilityRunStore | None = None,
    packet_field_answers: tuple[PacketFieldAnswer, ...] = (),
    action_plans: tuple[CaptureActionPlan, ...] = (),
) -> OpportunityKnowledgeContextView:
    index = build_structured_knowledge_index(
        opportunities=opportunities,
        evidence_store=evidence_store,
        document_intake_store=document_intake_store,
        piid_profile_store=piid_profile_store,
        sam_gov_profile_store=sam_gov_profile_store,
        capability_run_store=capability_run_store,
        packet_field_answers=packet_field_answers,
        action_plans=action_plans,
    )
    projection = index.for_opportunity(opportunity_id)
    related_profile_ids = _related_profile_ids(projection)
    related_capability_run_ids = _related_capability_run_ids(projection)
    capability_runs = (
        tuple(capability_run_store.list()) if capability_run_store is not None else ()
    )
    source_limitations = _source_limitations(
        related_profile_ids=related_profile_ids,
        piid_profile_store=piid_profile_store,
        sam_gov_profile_store=sam_gov_profile_store,
    )
    gaps = _gap_summaries(
        opportunity_id=opportunity_id,
        packet_field_answers=packet_field_answers,
        capability_runs=capability_runs,
        related_capability_run_ids=related_capability_run_ids,
    )
    return OpportunityKnowledgeContextView(
        opportunity_id=opportunity_id,
        trusted_context=_context_section(
            projection.trusted_records,
            connections=projection.connections,
        ),
        reviewable_context=_context_section(
            projection.reviewable_records,
            connections=projection.connections,
        ),
        gaps=gaps,
        source_limitations=source_limitations,
        related_profile_ids=related_profile_ids,
        related_capability_run_ids=related_capability_run_ids,
        next_command_links=_next_command_links(
            gaps=gaps,
            related_capability_run_ids=related_capability_run_ids,
            source_limitations=source_limitations,
        ),
    )


def _context_section(
    records: tuple[StructuredKnowledgeRecordRef, ...],
    *,
    connections: tuple[StructuredKnowledgeConnection, ...],
) -> KnowledgeContextSection:
    items = tuple(_context_item(record, connections=connections) for record in records)
    return KnowledgeContextSection(count=len(items), items=items)


def _context_item(
    record: StructuredKnowledgeRecordRef,
    *,
    connections: tuple[StructuredKnowledgeConnection, ...],
) -> KnowledgeContextItem:
    return KnowledgeContextItem(
        record_kind=record.kind,
        record_id=record.record_id,
        title=record.title,
        summary=_concise_summary(record.summary or record.title),
        trust_state=record.trust_state,
        status_label=record.trust_state.value,
        related_connection_count=sum(
            1
            for connection in connections
            if (connection.source_kind, connection.source_id)
            == (record.kind, record.record_id)
            or (connection.target_kind, connection.target_id)
            == (record.kind, record.record_id)
        ),
    )


def _related_profile_ids(
    projection: OpportunityKnowledgeProjection,
) -> tuple[str, ...]:
    return tuple(
        item.record_id
        for item in (*projection.trusted_records, *projection.reviewable_records)
        if item.kind
        in {KnowledgeRecordKind.PIID_PROFILE, KnowledgeRecordKind.SAM_GOV_PROFILE}
    )


def _related_capability_run_ids(
    projection: OpportunityKnowledgeProjection,
) -> tuple[str, ...]:
    return tuple(
        item.record_id
        for item in (*projection.trusted_records, *projection.reviewable_records)
        if item.kind is KnowledgeRecordKind.CAPABILITY_RUN
    )


def _gap_summaries(
    *,
    opportunity_id: str,
    packet_field_answers: tuple[PacketFieldAnswer, ...],
    capability_runs: tuple[CapabilityRun, ...],
    related_capability_run_ids: tuple[str, ...],
) -> tuple[KnowledgeGapSummary, ...]:
    gaps: list[KnowledgeGapSummary] = []
    gaps.extend(_packet_field_gap_summaries(opportunity_id, packet_field_answers))
    gaps.extend(_capability_run_gap_summaries(capability_runs, related_capability_run_ids))
    return tuple(gaps)


def _packet_field_gap_summaries(
    opportunity_id: str,
    answers: tuple[PacketFieldAnswer, ...],
) -> tuple[KnowledgeGapSummary, ...]:
    return tuple(
        KnowledgeGapSummary(
            record_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
            record_id=_packet_field_answer_id(answer),
            summary=_concise_summary(answer.gap_summary or "Packet field needs review."),
            command_id="review_packet_gap",
        )
        for answer in answers
        if answer.opportunity_id == opportunity_id and _packet_field_has_gap(answer)
    )


def _capability_run_gap_summaries(
    runs: tuple[CapabilityRun, ...],
    related_capability_run_ids: tuple[str, ...],
) -> tuple[KnowledgeGapSummary, ...]:
    related_run_ids = set(related_capability_run_ids)
    return tuple(
        KnowledgeGapSummary(
            record_kind=KnowledgeRecordKind.CAPABILITY_RUN_OUTPUT,
            record_id=_capability_run_output_id(run, output_id=output.output_id),
            summary=_concise_summary(gap),
            command_id="review_capability_run_output",
        )
        for run in runs
        if run.run_id in related_run_ids
        for output in run.outputs
        for gap in output.gaps
    )


def _source_limitations(
    *,
    related_profile_ids: tuple[str, ...],
    piid_profile_store: PiidProfileStore | None,
    sam_gov_profile_store: SamGovProfileStore | None,
) -> tuple[KnowledgeSourceLimitation, ...]:
    related_ids = set(related_profile_ids)
    limitations: list[KnowledgeSourceLimitation] = []
    if piid_profile_store is not None:
        limitations.extend(
            KnowledgeSourceLimitation(
                record_kind=KnowledgeRecordKind.PIID_PROFILE,
                record_id=profile.id,
                summary=_concise_summary(gap.source_limitation),
            )
            for profile in piid_profile_store.list()
            if profile.id in related_ids
            for gap in profile.gaps
        )
    if sam_gov_profile_store is not None:
        limitations.extend(_sam_gov_source_limitations(sam_gov_profile_store, related_ids))
    return tuple(limitations)


def _sam_gov_source_limitations(
    sam_gov_profile_store: SamGovProfileStore,
    related_ids: set[str],
) -> tuple[KnowledgeSourceLimitation, ...]:
    return tuple(
        KnowledgeSourceLimitation(
            record_kind=KnowledgeRecordKind.SAM_GOV_PROFILE,
            record_id=profile.id,
            summary=_concise_summary(limitation),
        )
        for profile in sam_gov_profile_store.list()
        if profile.id in related_ids
        for limitation in _sam_gov_profile_limitations(profile)
    )


def _sam_gov_profile_limitations(
    profile: SamGovEnrichmentProfile,
) -> tuple[str, ...]:
    limitations: list[str] = []
    for lane in (
        profile.entity_lane,
        profile.known_opportunity_lane,
        profile.opportunity_discovery_lane,
        profile.attachment_intake_lane,
    ):
        if lane is not None:
            limitations.extend(lane.source_limitations)
    return tuple(limitations)


def _next_command_links(
    *,
    gaps: tuple[KnowledgeGapSummary, ...],
    related_capability_run_ids: tuple[str, ...],
    source_limitations: tuple[KnowledgeSourceLimitation, ...],
) -> tuple[KnowledgeCommandLink, ...]:
    links: list[KnowledgeCommandLink] = []
    if any(gap.record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER for gap in gaps):
        packet_gap = next(
            gap for gap in gaps if gap.record_kind is KnowledgeRecordKind.PACKET_FIELD_ANSWER
        )
        links.append(
            KnowledgeCommandLink(
                command_id="review_packet_gap",
                label="Review packet gap",
                target_kind=packet_gap.record_kind,
                target_id=packet_gap.record_id,
            )
        )
    if related_capability_run_ids:
        links.append(
            KnowledgeCommandLink(
                command_id="review_capability_run_output",
                label="Review capability output",
                target_kind=KnowledgeRecordKind.CAPABILITY_RUN,
                target_id=related_capability_run_ids[0],
            )
        )
    if source_limitations:
        links.append(
            KnowledgeCommandLink(
                command_id="review_source_limitation",
                label="Review source limitation",
                target_kind=source_limitations[0].record_kind,
                target_id=source_limitations[0].record_id,
            )
        )
    return tuple(links)


def _packet_field_has_gap(answer: PacketFieldAnswer) -> bool:
    return answer.status is PacketFieldAnswerStatus.GAP or bool(answer.gap_summary)


def _concise_summary(summary: str, *, max_length: int = 160) -> str:
    normalized = " ".join(summary.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."


def _add_connected_record_key(
    record_key: tuple[KnowledgeRecordKind, str],
    *,
    records_by_key: dict[tuple[KnowledgeRecordKind, str], StructuredKnowledgeRecordRef],
    selected_record_keys: set[tuple[KnowledgeRecordKind, str]],
    opportunity_id: str,
) -> bool:
    record = records_by_key.get(record_key)
    if record is None:
        return False
    if record.opportunity_id not in {None, opportunity_id}:
        return False
    if record_key in selected_record_keys:
        return False
    selected_record_keys.add(record_key)
    return True


def _record_key(record_key: tuple[KnowledgeRecordKind, str]) -> tuple[str, str]:
    kind, record_id = record_key
    return kind.value, record_id


def _opportunity_records(
    opportunities: tuple[Opportunity, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.OPPORTUNITY,
            record_id=opportunity.name,
            opportunity_id=opportunity.name,
            trust_state=KnowledgeTrustState.TRUSTED,
            title=opportunity.name,
            summary=opportunity.lifecycle_state.value,
        )
        for opportunity in opportunities
    )


def _evidence_records(
    evidence_items: tuple[EvidenceItem, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.EVIDENCE_ITEM,
            record_id=evidence.id,
            opportunity_id=evidence.opportunity_id,
            trust_state=KnowledgeTrustState.TRUSTED,
            title=evidence.id,
            summary=evidence.content,
        )
        for evidence in evidence_items
    )


def _evidence_connections(
    evidence_items: tuple[EvidenceItem, ...],
) -> tuple[StructuredKnowledgeConnection, ...]:
    return tuple(
        StructuredKnowledgeConnection(
            source_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
            source_id=evidence.id,
            relationship="derived_from_evidence",
            target_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
            target_id=source_evidence_id,
            trust_state=KnowledgeTrustState.TRUSTED,
            provenance="EvidenceItem.derived_from_ids",
        )
        for evidence in evidence_items
        for source_evidence_id in evidence.derived_from_ids
    )


def _document_intake_link_records(
    document_intake_store: DocumentIntakeStore,
    *,
    evidence_opportunity_ids: dict[str, str | None],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.DOCUMENT_INTAKE_EVIDENCE_LINK,
            record_id=link.id,
            opportunity_id=evidence_opportunity_ids.get(link.evidence_id),
            trust_state=KnowledgeTrustState.TRUSTED,
            title=link.source_ref,
            summary=link.reviewer_rationale,
        )
        for link in document_intake_store.list_accepted_evidence_links()
    )


def _document_intake_link_connections(
    document_intake_store: DocumentIntakeStore,
) -> tuple[StructuredKnowledgeConnection, ...]:
    return tuple(
        StructuredKnowledgeConnection(
            source_kind=KnowledgeRecordKind.DOCUMENT_INTAKE_EVIDENCE_LINK,
            source_id=link.id,
            relationship="accepted_source_span_for_evidence",
            target_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
            target_id=link.evidence_id,
            trust_state=KnowledgeTrustState.TRUSTED,
            provenance="AcceptedDocumentEvidenceLink.evidence_id",
        )
        for link in document_intake_store.list_accepted_evidence_links()
    )


def _piid_profile_records(
    profiles: tuple[PiidContractIntelligenceProfile, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.PIID_PROFILE,
            record_id=profile.id,
            opportunity_id=None,
            trust_state=KnowledgeTrustState.REVIEWABLE,
            title=profile.normalized_piid,
            summary=profile.award_baseline.resolved_award_id,
        )
        for profile in profiles
    )


def _sam_gov_profile_records(
    profiles: tuple[SamGovEnrichmentProfile, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.SAM_GOV_PROFILE,
            record_id=profile.id,
            opportunity_id=None,
            trust_state=KnowledgeTrustState.REVIEWABLE,
            title=profile.normalized_pivot,
            summary=profile.input_pivot,
        )
        for profile in profiles
    )


def _capability_run_records(
    runs: tuple[CapabilityRun, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.CAPABILITY_RUN,
            record_id=run.run_id,
            opportunity_id=run.opportunity_id,
            trust_state=_capability_run_trust_state(run),
            title=run.capability_id,
            summary=run.inputs_summary,
        )
        for run in runs
    )


def _capability_run_output_records(
    runs: tuple[CapabilityRun, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.CAPABILITY_RUN_OUTPUT,
            record_id=_capability_run_output_id(run, output_id=output.output_id),
            opportunity_id=run.opportunity_id,
            trust_state=_capability_run_output_trust_state(output.review_state),
            title=output.title,
            summary=output.summary,
        )
        for run in runs
        for output in run.outputs
    )


def _capability_run_connections(
    runs: tuple[CapabilityRun, ...],
    *,
    record_kinds_by_id: dict[str, KnowledgeRecordKind],
) -> tuple[StructuredKnowledgeConnection, ...]:
    connections: list[StructuredKnowledgeConnection] = []
    for run in runs:
        run_trust_state = _capability_run_trust_state(run)
        connections.extend(
            StructuredKnowledgeConnection(
                source_kind=KnowledgeRecordKind.CAPABILITY_RUN,
                source_id=run.run_id,
                relationship="used_input_ref",
                target_kind=record_kinds_by_id[input_ref],
                target_id=input_ref,
                trust_state=run_trust_state,
                provenance="CapabilityRun.input_refs",
            )
            for input_ref in run.input_refs
            if input_ref in record_kinds_by_id
        )
        connections.extend(
            StructuredKnowledgeConnection(
                source_kind=KnowledgeRecordKind.CAPABILITY_RUN,
                source_id=run.run_id,
                relationship="produced_output",
                target_kind=KnowledgeRecordKind.CAPABILITY_RUN_OUTPUT,
                target_id=_capability_run_output_id(run, output_id=output.output_id),
                trust_state=_capability_run_output_trust_state(output.review_state),
                provenance="CapabilityRun.outputs",
            )
            for output in run.outputs
        )
    return tuple(connections)


def _packet_field_answer_records(
    answers: tuple[PacketFieldAnswer, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
            record_id=_packet_field_answer_id(answer),
            opportunity_id=answer.opportunity_id,
            trust_state=_packet_field_answer_trust_state(answer),
            title=answer.field_key,
            summary=answer.value or answer.gap_summary,
        )
        for answer in answers
    )


def _action_plan_item_records(
    action_plans: tuple[CaptureActionPlan, ...],
) -> tuple[StructuredKnowledgeRecordRef, ...]:
    return tuple(
        StructuredKnowledgeRecordRef(
            kind=KnowledgeRecordKind.ACTION_PLAN_ITEM,
            record_id=item.id,
            opportunity_id=plan.opportunity_name,
            trust_state=_action_plan_item_trust_state(item.review_status),
            title=item.action,
            summary=item.rationale,
        )
        for plan in action_plans
        for item in plan.items
    )


def _packet_field_answer_connections(
    answers: tuple[PacketFieldAnswer, ...],
) -> tuple[StructuredKnowledgeConnection, ...]:
    connections: list[StructuredKnowledgeConnection] = []
    for answer in answers:
        answer_id = _packet_field_answer_id(answer)
        answer_trust_state = _packet_field_answer_trust_state(answer)
        connections.extend(
            StructuredKnowledgeConnection(
                source_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                source_id=answer_id,
                relationship="supported_by_evidence",
                target_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                target_id=evidence_id,
                trust_state=answer_trust_state,
                provenance="PacketFieldAnswer.evidence_ids",
            )
            for evidence_id in answer.evidence_ids
        )
        connections.extend(
            StructuredKnowledgeConnection(
                source_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                source_id=answer_id,
                relationship="creates_action_need",
                target_kind=KnowledgeRecordKind.ACTION_PLAN_ITEM,
                target_id=action_item_id,
                trust_state=answer_trust_state,
                provenance="PacketFieldAnswer.action_item_ids",
            )
            for action_item_id in answer.action_item_ids
        )
    return tuple(connections)


def _action_plan_item_connections(
    action_plans: tuple[CaptureActionPlan, ...],
) -> tuple[StructuredKnowledgeConnection, ...]:
    connections: list[StructuredKnowledgeConnection] = []
    for plan in action_plans:
        for item in plan.items:
            item_trust_state = _action_plan_item_trust_state(item.review_status)
            connections.extend(
                StructuredKnowledgeConnection(
                    source_kind=KnowledgeRecordKind.ACTION_PLAN_ITEM,
                    source_id=item.id,
                    relationship="supported_by_evidence",
                    target_kind=KnowledgeRecordKind.EVIDENCE_ITEM,
                    target_id=evidence_id,
                    trust_state=item_trust_state,
                    provenance="ActionPlanItem.related_evidence_ids",
                )
                for evidence_id in item.related_evidence_ids
            )
            if item.related_packet_field_key:
                connections.append(
                    StructuredKnowledgeConnection(
                        source_kind=KnowledgeRecordKind.ACTION_PLAN_ITEM,
                        source_id=item.id,
                        relationship="addresses_packet_field",
                        target_kind=KnowledgeRecordKind.PACKET_FIELD_ANSWER,
                        target_id=(
                            f"packet_field_answer:{plan.opportunity_name}:"
                            f"{item.related_packet_field_key}"
                        ),
                        trust_state=item_trust_state,
                        provenance="ActionPlanItem.related_packet_field_key",
                    )
                )
    return tuple(connections)


def _packet_field_answer_id(answer: PacketFieldAnswer) -> str:
    return f"packet_field_answer:{answer.opportunity_id}:{answer.field_key}"


def _packet_field_answer_trust_state(
    answer: PacketFieldAnswer,
) -> KnowledgeTrustState:
    if answer.status in {
        PacketFieldAnswerStatus.ANSWERED,
        PacketFieldAnswerStatus.ASSUMPTION,
    }:
        return KnowledgeTrustState.TRUSTED
    return KnowledgeTrustState.REVIEWABLE


def _action_plan_item_trust_state(review_status: str | None) -> KnowledgeTrustState:
    if review_status is None or review_status == "accepted":
        return KnowledgeTrustState.TRUSTED
    return KnowledgeTrustState.REVIEWABLE


def _capability_run_trust_state(run: CapabilityRun) -> KnowledgeTrustState:
    if run.status is CapabilityRunStatus.NEEDS_REVIEW:
        return KnowledgeTrustState.REVIEWABLE
    if any(
        _capability_run_output_trust_state(output.review_state)
        is KnowledgeTrustState.REVIEWABLE
        for output in run.outputs
    ):
        return KnowledgeTrustState.REVIEWABLE
    return KnowledgeTrustState.TRUSTED


def _capability_run_output_trust_state(
    review_state: CapabilityRunOutputReviewState,
) -> KnowledgeTrustState:
    if review_state in {
        CapabilityRunOutputReviewState.ACCEPTED,
        CapabilityRunOutputReviewState.PROMOTED,
    }:
        return KnowledgeTrustState.TRUSTED
    return KnowledgeTrustState.REVIEWABLE


def _capability_run_output_id(run: CapabilityRun, *, output_id: str) -> str:
    return f"capability_run_output:{run.run_id}:{output_id}"