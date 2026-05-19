from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
import json
from pathlib import Path
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from ariadne.evidence import EvidenceItem
from ariadne.reference_wiki import ReferenceWikiInfluence


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


class CaptureResearchSourceMode(StrEnum):
    FAKE_ADAPTER_TEST = "fake_adapter_test"
    LOCAL_CRAWL4AI = "local_crawl4ai"
    LOCAL_SEARXNG = "local_searxng"
    LIVE_SERPAPI = "live_serpapi"
    LIVE_OLOSTEP = "live_olostep"
    LIVE_FIRECRAWL = "live_firecrawl"


class SourceCollectionProviderRole(StrEnum):
    SEARCH_DISCOVERY = "search_discovery"
    PAGE_CRAWL_EXTRACTION = "page_crawl_extraction"
    SEARCH_AND_CRAWL = "search_and_crawl"


class SourceCollectionProviderStatus(StrEnum):
    AVAILABLE = "available"
    MISSING_CONFIG = "missing_config"


class SourceCollectionQualityStatus(StrEnum):
    FULL_READY = "full_ready"
    DISCOVERY_ONLY = "discovery_only"
    EXTRACTION_ONLY = "extraction_only"
    NOT_READY = "not_ready"


class SourceProviderSmokeCheckStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    MISSING_ENV = "missing_env"
    REQUIRES_APPROVAL = "requires_approval"


class SourceCollectionProviderManifest(BaseModel):
    id: str
    name: str
    role: SourceCollectionProviderRole
    source_mode: CaptureResearchSourceMode
    required_env_vars: tuple[str, ...]
    priority: int
    source_limitations: tuple[str, ...]

    @model_validator(mode="after")
    def validate_env_var_names_only(self) -> SourceCollectionProviderManifest:
        for env_var_name in self.required_env_vars:
            if not _ENV_VAR_NAME_PATTERN.fullmatch(env_var_name):
                raise ValueError("provider env var metadata must contain names only")
        return self


class SourceCollectionProviderReadiness(BaseModel):
    provider_id: str
    provider_name: str
    role: SourceCollectionProviderRole
    source_mode: CaptureResearchSourceMode
    status: SourceCollectionProviderStatus
    priority: int
    configured_env_vars: tuple[str, ...] = ()
    missing_env_vars: tuple[str, ...] = ()
    diagnostic_summary: str
    source_limitations: tuple[str, ...]


class SourceProviderRegistry(BaseModel):
    providers: tuple[SourceCollectionProviderReadiness, ...]
    quality_status: SourceCollectionQualityStatus
    quality_summary: str
    recommended_provider_ids: tuple[str, ...] = ()

    def available_provider_ids(self) -> tuple[str, ...]:
        return tuple(
            provider.provider_id
            for provider in self.providers
            if provider.status is SourceCollectionProviderStatus.AVAILABLE
        )

    def require_available_provider_ids(
        self, requested_provider_ids: tuple[str, ...]
    ) -> tuple[str, ...]:
        provider_ids = requested_provider_ids or self.recommended_provider_ids
        if not provider_ids:
            raise ValueError("no eligible source collection provider is configured")
        available = set(self.available_provider_ids())
        unavailable = tuple(
            provider_id for provider_id in provider_ids if provider_id not in available
        )
        if unavailable:
            raise ValueError(
                "source collection providers are not available: "
                + ", ".join(unavailable)
            )
        return provider_ids


class SourceProviderSmokeRunnerResult(BaseModel):
    ok: bool = False
    timed_out: bool = False
    diagnostic_summary: str
    endpoint_label: str = ""
    observed_result_count: int = 0


class SourceProviderSmokeCheckResult(BaseModel):
    provider_id: str
    provider_name: str
    source_mode: CaptureResearchSourceMode
    status: SourceProviderSmokeCheckStatus
    checked_at: str
    diagnostic_summary: str
    missing_env_vars: tuple[str, ...] = ()
    configured_env_vars: tuple[str, ...] = ()
    endpoint_label: str = ""
    observed_result_count: int = 0
    source_limitations: tuple[str, ...]


class SourceProviderSmokeRunner(Protocol):
    def __call__(
        self,
        manifest: SourceCollectionProviderManifest,
        *,
        env: dict[str, str],
        smoke_target: str,
        timeout_seconds: int,
    ) -> SourceProviderSmokeRunnerResult: ...


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


class CapabilityProvenance(BaseModel):
    source_capability_id: str
    source_tool_name: str
    source_package: str
    source_package_version: str


class WebSourceCollectionRecord(BaseModel):
    id: str
    source_target: str
    source_mode: CaptureResearchSourceMode
    collected_at: str
    capability_provenance: CapabilityProvenance
    source_limitations: tuple[str, ...]
    finding_ids: tuple[str, ...]
    provider_ids: tuple[str, ...] = ()
    approval_basis: str | None = None


class SourceFinding(BaseModel):
    id: str
    source_target: str
    url: str
    title: str
    source_type: str
    collected_at: str
    excerpt: str
    confidence: float = Field(ge=0, le=1)
    source_limitations: tuple[str, ...]
    source_mode: CaptureResearchSourceMode
    capability_provenance: CapabilityProvenance
    provider_ids: tuple[str, ...] = ()
    approval_basis: str | None = None


class SellerBaselineRefType(StrEnum):
    ACCEPTED_EVIDENCE = "accepted_evidence"
    REFERENCE_WIKI_NOTE = "reference_wiki_note"
    BASELINE_GAP = "baseline_gap"


class SellerBaselineRef(BaseModel):
    id: str
    ref_type: SellerBaselineRefType
    source_label: str
    source_ref: str
    summarized_support: str
    assumptions: tuple[str, ...] = ()
    baseline_gaps: tuple[str, ...] = ()
    matched_terms: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_reviewable_ref(self) -> SellerBaselineRef:
        if not self.id.strip():
            raise ValueError("seller baseline ref id is required")
        if not self.source_label.strip():
            raise ValueError("seller baseline source label is required")
        if not self.source_ref.strip():
            raise ValueError("seller baseline source ref is required")
        if not self.summarized_support.strip():
            raise ValueError("seller baseline summarized support is required")
        return self


class RequirementsFitSignal(BaseModel):
    id: str
    summary: str
    supporting_seller_baseline_ref_ids: tuple[str, ...] = ()
    supporting_source_finding_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)


class RequirementsFitAnalysis(BaseModel):
    id: str
    analyzed_at: str
    summary: str
    seller_baseline_ref_ids: tuple[str, ...]
    source_finding_ids: tuple[str, ...] = ()
    selected_lenses: tuple[CaptureResearchLens, ...]
    strengths: tuple[RequirementsFitSignal, ...] = ()
    weaknesses: tuple[RequirementsFitSignal, ...] = ()
    qualification_risks: tuple[RequirementsFitSignal, ...] = ()
    proof_needs: tuple[RequirementsFitSignal, ...] = ()
    follow_up_recommendations: tuple[RequirementsFitSignal, ...] = ()


class CompetitiveGapSignal(BaseModel):
    id: str
    summary: str
    supporting_seller_baseline_ref_ids: tuple[str, ...] = ()
    supporting_source_finding_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)
    review_state: str = "pending_review"
    bcc_ready_input: bool = False


class CompetitiveGapAnalysis(BaseModel):
    id: str
    analyzed_at: str
    summary: str
    seller_baseline_ref_ids: tuple[str, ...]
    source_finding_ids: tuple[str, ...] = ()
    selected_lenses: tuple[CaptureResearchLens, ...]
    discriminator_candidates: tuple[CompetitiveGapSignal, ...] = ()
    vulnerabilities: tuple[CompetitiveGapSignal, ...] = ()
    proof_gaps: tuple[CompetitiveGapSignal, ...] = ()
    competitor_incumbent_notes: tuple[CompetitiveGapSignal, ...] = ()
    teaming_partner_needs: tuple[CompetitiveGapSignal, ...] = ()
    bcc_ready_notes: tuple[CompetitiveGapSignal, ...] = ()
    follow_up_recommendations: tuple[CompetitiveGapSignal, ...] = ()
    bcc_artifact_generated: bool = False


class CaptureResearchRun(BaseModel):
    research_run_id: str
    opportunity_id: str | None = None
    status: CaptureResearchRunStatus = CaptureResearchRunStatus.PLANNED
    research_brief: CaptureResearchBrief
    research_trigger_context: ResearchTriggerContext
    user_prompt: UserPromptedResearchRequest | None = None
    selected_lenses: tuple[CaptureResearchLens, ...]
    source_profile_refs: tuple[SourceProfileRef, ...] = ()
    seller_baseline_refs: tuple[SellerBaselineRef, ...] = ()
    source_collection_records: tuple[WebSourceCollectionRecord, ...] = ()
    source_findings: tuple[SourceFinding, ...] = ()
    requirements_fit_analysis: RequirementsFitAnalysis | None = None
    competitive_gap_analysis: CompetitiveGapAnalysis | None = None
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


class WebSourceCollectionAdapter(Protocol):
    def collect(
        self,
        run: CaptureResearchRun,
        *,
        collected_at: str,
    ) -> tuple[tuple[WebSourceCollectionRecord, ...], tuple[SourceFinding, ...]]: ...


class ApprovedWebSourceCollectionAdapter(WebSourceCollectionAdapter, Protocol):
    provider_ids: tuple[str, ...]


class SourceProviderHttpClient(Protocol):
    def get_json(self, url: str, *, headers: dict[str, str]) -> dict[str, object]: ...

    def post_json(
        self, url: str, *, headers: dict[str, str], payload: dict[str, object]
    ) -> dict[str, object]: ...


class UrlLibSourceProviderHttpClient:
    def get_json(self, url: str, *, headers: dict[str, str]) -> dict[str, object]:
        request = Request(url, headers=headers, method="GET")
        return _read_json_response(request)

    def post_json(
        self, url: str, *, headers: dict[str, str], payload: dict[str, object]
    ) -> dict[str, object]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        return _read_json_response(request)


class ProviderBackedWebSourceCollectionAdapter:
    source_mode = CaptureResearchSourceMode.LIVE_OLOSTEP

    def __init__(
        self,
        *,
        env: dict[str, str],
        provider_ids: tuple[str, ...],
        http_client: SourceProviderHttpClient | None = None,
        result_limit: int = 3,
    ) -> None:
        self.env = env
        self.provider_ids = provider_ids
        self.http_client = http_client or UrlLibSourceProviderHttpClient()
        self.result_limit = result_limit
        if provider_ids == ("serpapi_live",):
            self.source_mode = CaptureResearchSourceMode.LIVE_SERPAPI

    def collect(
        self,
        run: CaptureResearchRun,
        *,
        collected_at: str,
    ) -> tuple[tuple[WebSourceCollectionRecord, ...], tuple[SourceFinding, ...]]:
        records: list[WebSourceCollectionRecord] = []
        findings: list[SourceFinding] = []
        for source_target in run.research_brief.source_targets:
            target_findings = self._collect_target(
                run,
                source_target=source_target,
                collected_at=collected_at,
            )
            findings.extend(target_findings)
            records.append(
                WebSourceCollectionRecord(
                    id=f"web_collection_{_source_target_slug(source_target)}_{uuid4().hex[:8]}",
                    source_target=source_target,
                    source_mode=self.source_mode,
                    collected_at=collected_at,
                    capability_provenance=self._provenance(),
                    source_limitations=self._source_limitations(),
                    finding_ids=tuple(finding.id for finding in target_findings),
                    provider_ids=self.provider_ids,
                    approval_basis=run.research_brief.approval_basis,
                )
            )
        return tuple(records), tuple(findings)

    def _collect_target(
        self,
        run: CaptureResearchRun,
        *,
        source_target: str,
        collected_at: str,
    ) -> tuple[SourceFinding, ...]:
        serpapi_results = self._serpapi_search(source_target)
        if "olostep_live" in self.provider_ids:
            if serpapi_results:
                return self._olostep_scrape_results(
                    run,
                    source_target=source_target,
                    search_results=serpapi_results,
                    collected_at=collected_at,
                )
            return self._olostep_search_results(
                run,
                source_target=source_target,
                collected_at=collected_at,
            )
        return self._serpapi_findings(
            run,
            source_target=source_target,
            search_results=serpapi_results,
            collected_at=collected_at,
        )

    def _serpapi_search(self, source_target: str) -> tuple[dict[str, str], ...]:
        api_key = self.env.get("SERPAPI_API_KEY")
        if not api_key or "serpapi_live" not in self.provider_ids:
            return ()
        url = (
            "https://serpapi.com/search.json?engine=google&q="
            + quote_plus(source_target)
            + "&api_key="
            + quote_plus(api_key)
        )
        response = self.http_client.get_json(url, headers={})
        organic_results = response.get("organic_results", [])
        if not isinstance(organic_results, list):
            return ()
        results: list[dict[str, str]] = []
        for result in organic_results[: self.result_limit]:
            if not isinstance(result, dict):
                continue
            link = _as_string(result.get("link"))
            if not link:
                continue
            results.append(
                {
                    "url": link,
                    "title": _as_string(result.get("title")) or link,
                    "excerpt": _as_string(result.get("snippet")),
                }
            )
        return tuple(results)

    def _olostep_scrape_results(
        self,
        run: CaptureResearchRun,
        *,
        source_target: str,
        search_results: tuple[dict[str, str], ...],
        collected_at: str,
    ) -> tuple[SourceFinding, ...]:
        findings: list[SourceFinding] = []
        for result in search_results:
            scrape = self._olostep_scrape(result["url"])
            scrape_result = scrape.get("result", {})
            if not isinstance(scrape_result, dict):
                scrape_result = {}
            content = _as_string(scrape_result.get("markdown_content"))
            title = _as_string(
                scrape_result.get("page_metadata", {}).get("title")
                if isinstance(scrape_result.get("page_metadata"), dict)
                else None
            )
            findings.append(
                self._finding(
                    run,
                    source_target=source_target,
                    url=result["url"],
                    title=title or result["title"],
                    excerpt=_compact_excerpt(content or result["excerpt"]),
                    collected_at=collected_at,
                    source_type="serpapi_discovered_olostep_scraped_public_web",
                    confidence=0.78 if content else 0.64,
                )
            )
        return tuple(findings)

    def _olostep_search_results(
        self,
        run: CaptureResearchRun,
        *,
        source_target: str,
        collected_at: str,
    ) -> tuple[SourceFinding, ...]:
        response = self._olostep_search(source_target)
        result = response.get("result", {})
        links = result.get("links", []) if isinstance(result, dict) else []
        if not isinstance(links, list):
            return ()
        findings: list[SourceFinding] = []
        for link in links[: self.result_limit]:
            if not isinstance(link, dict):
                continue
            url = _as_string(link.get("url"))
            if not url:
                continue
            content = _as_string(link.get("markdown_content"))
            findings.append(
                self._finding(
                    run,
                    source_target=source_target,
                    url=url,
                    title=_as_string(link.get("title")) or url,
                    excerpt=_compact_excerpt(
                        content or _as_string(link.get("description"))
                    ),
                    collected_at=collected_at,
                    source_type="olostep_search_scraped_public_web",
                    confidence=0.76 if content else 0.62,
                )
            )
        return tuple(findings)

    def _serpapi_findings(
        self,
        run: CaptureResearchRun,
        *,
        source_target: str,
        search_results: tuple[dict[str, str], ...],
        collected_at: str,
    ) -> tuple[SourceFinding, ...]:
        return tuple(
            self._finding(
                run,
                source_target=source_target,
                url=result["url"],
                title=result["title"],
                excerpt=result["excerpt"],
                collected_at=collected_at,
                source_type="serpapi_search_public_web",
                confidence=0.58,
            )
            for result in search_results
        )

    def _olostep_search(self, source_target: str) -> dict[str, object]:
        api_key = self.env.get("OLOSTEP_API_KEY")
        if not api_key:
            raise ValueError("OLOSTEP_API_KEY is required for Olostep collection")
        return self.http_client.post_json(
            "https://api.olostep.com/v1/searches",
            headers=_olostep_headers(api_key),
            payload={
                "query": source_target,
                "limit": self.result_limit,
                "scrape_options": {
                    "formats": ["markdown"],
                    "remove_css_selectors": "default",
                    "timeout": 25,
                },
            },
        )

    def _olostep_scrape(self, url: str) -> dict[str, object]:
        api_key = self.env.get("OLOSTEP_API_KEY")
        if not api_key:
            raise ValueError("OLOSTEP_API_KEY is required for Olostep collection")
        return self.http_client.post_json(
            "https://api.olostep.com/v1/scrapes",
            headers=_olostep_headers(api_key),
            payload={
                "url_to_scrape": url,
                "formats": ["markdown"],
                "remove_css_selectors": "default",
            },
        )

    def _finding(
        self,
        run: CaptureResearchRun,
        *,
        source_target: str,
        url: str,
        title: str,
        excerpt: str,
        collected_at: str,
        source_type: str,
        confidence: float,
    ) -> SourceFinding:
        return SourceFinding(
            id=f"source_finding_{_source_target_slug(source_target)}_{uuid4().hex[:8]}",
            source_target=source_target,
            url=url,
            title=title,
            source_type=source_type,
            collected_at=collected_at,
            excerpt=excerpt or "Provider returned no text excerpt for this source.",
            confidence=confidence,
            source_limitations=self._source_limitations(),
            source_mode=self.source_mode,
            capability_provenance=self._provenance(),
            provider_ids=self.provider_ids,
            approval_basis=run.research_brief.approval_basis,
        )

    def _provenance(self) -> CapabilityProvenance:
        return CapabilityProvenance(
            source_capability_id="+".join(self.provider_ids),
            source_tool_name="collect_provider_backed_public_sources",
            source_package="ariadne.capture_research",
            source_package_version="local",
        )

    def _source_limitations(self) -> tuple[str, ...]:
        limitations = [
            "Live provider-backed collection uses bounded public source targets only.",
        ]
        if "serpapi_live" in self.provider_ids and "olostep_live" in self.provider_ids:
            limitations.append(
                "SerpApi supplies search discovery; Olostep supplies crawl/extraction."
            )
        elif "olostep_live" in self.provider_ids:
            limitations.append("Olostep supplies search and crawl/extraction.")
        elif "serpapi_live" in self.provider_ids:
            limitations.append("SerpApi supplies search snippets without page extraction.")
        return tuple(limitations)


_ENV_VAR_NAME_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*")

_RESTRICTED_SOURCE_HOSTS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
}

_RESTRICTED_SOURCE_MARKERS = (
    "login required",
    "logged-in",
    "private group",
    "paywall bypass",
)

_SELLER_BASELINE_KEYWORDS = frozenset(
    {
        "baseline",
        "capability",
        "capabilities",
        "certification",
        "certifications",
        "constraint",
        "constraints",
        "differentiator",
        "differentiators",
        "experience",
        "incumbent",
        "past",
        "performance",
        "proof",
        "relationship",
        "relationships",
        "seller",
        "staffing",
        "transition",
        "vehicle",
        "vehicles",
        "workload",
    }
)

_LOW_SIGNAL_REQUIREMENT_TERMS = frozenset(
    {
        "agency",
        "and",
        "context",
        "customer",
        "evidence",
        "find",
        "for",
        "public",
        "research",
        "source",
        "sources",
        "the",
        "this",
        "with",
    }
)

_COMPETITIVE_SIGNAL_TERMS = frozenset(
    {
        "awardee",
        "competitor",
        "contractor",
        "incumbent",
        "prime",
        "subcontractor",
        "teaming",
        "vendor",
    }
)

_GAP_SIGNAL_TERMS = frozenset(
    {
        "certification",
        "clearance",
        "constraint",
        "coverage",
        "gap",
        "gaps",
        "partner",
        "staffing",
        "subcontractor",
        "teaming",
        "vehicle",
    }
)

_SOURCE_PROVIDER_MANIFESTS = (
    SourceCollectionProviderManifest(
        id="crawl4ai_local",
        name="Crawl4AI local crawler",
        role=SourceCollectionProviderRole.PAGE_CRAWL_EXTRACTION,
        source_mode=CaptureResearchSourceMode.LOCAL_CRAWL4AI,
        required_env_vars=("CRAWL4AI_BASE_URL",),
        priority=10,
        source_limitations=(
            "Local Crawl4AI handles page crawl and LLM-ready extraction after discovery.",
        ),
    ),
    SourceCollectionProviderManifest(
        id="searxng_local",
        name="SearXNG local search",
        role=SourceCollectionProviderRole.SEARCH_DISCOVERY,
        source_mode=CaptureResearchSourceMode.LOCAL_SEARXNG,
        required_env_vars=("SEARXNG_BASE_URL",),
        priority=10,
        source_limitations=(
            "Local SearXNG handles search discovery; extracted page quality depends on a crawl provider.",
        ),
    ),
    SourceCollectionProviderManifest(
        id="serpapi_live",
        name="SerpApi search",
        role=SourceCollectionProviderRole.SEARCH_DISCOVERY,
        source_mode=CaptureResearchSourceMode.LIVE_SERPAPI,
        required_env_vars=("SERPAPI_API_KEY",),
        priority=20,
        source_limitations=(
            "SerpApi handles SERP discovery; extracted page quality depends on a crawl provider.",
        ),
    ),
    SourceCollectionProviderManifest(
        id="olostep_live",
        name="Olostep search and crawl",
        role=SourceCollectionProviderRole.SEARCH_AND_CRAWL,
        source_mode=CaptureResearchSourceMode.LIVE_OLOSTEP,
        required_env_vars=("OLOSTEP_API_KEY",),
        priority=30,
        source_limitations=(
            "Olostep can backfill search, scraping, and crawling when local providers are insufficient.",
        ),
    ),
    SourceCollectionProviderManifest(
        id="firecrawl_live",
        name="Firecrawl optional crawler",
        role=SourceCollectionProviderRole.SEARCH_AND_CRAWL,
        source_mode=CaptureResearchSourceMode.LIVE_FIRECRAWL,
        required_env_vars=("FIRECRAWL_API_KEY",),
        priority=40,
        source_limitations=(
            "Firecrawl is optional paid/later fallback and should be used only when credits are approved.",
        ),
    ),
)


def build_source_provider_registry(env: dict[str, str]) -> SourceProviderRegistry:
    providers = tuple(_source_provider_readiness(manifest, env) for manifest in _SOURCE_PROVIDER_MANIFESTS)
    quality_status, quality_summary, recommended_provider_ids = _source_collection_quality(
        providers
    )
    return SourceProviderRegistry(
        providers=providers,
        quality_status=quality_status,
        quality_summary=quality_summary,
        recommended_provider_ids=recommended_provider_ids,
    )


def run_source_provider_smoke_check(
    *,
    provider_id: str,
    env: dict[str, str],
    approved: bool,
    smoke_target: str,
    runner: SourceProviderSmokeRunner | None = None,
    timeout_seconds: int = 60,
    checked_at: str | None = None,
) -> SourceProviderSmokeCheckResult:
    manifest = _source_provider_manifest_by_id(provider_id)
    readiness = _source_provider_readiness(manifest, env)
    resolved_checked_at = checked_at or datetime.now(UTC).isoformat()
    if readiness.missing_env_vars:
        return SourceProviderSmokeCheckResult(
            provider_id=manifest.id,
            provider_name=manifest.name,
            source_mode=manifest.source_mode,
            status=SourceProviderSmokeCheckStatus.MISSING_ENV,
            checked_at=resolved_checked_at,
            diagnostic_summary=(
                "Missing required env vars: " + ", ".join(readiness.missing_env_vars)
            ),
            missing_env_vars=readiness.missing_env_vars,
            configured_env_vars=readiness.configured_env_vars,
            source_limitations=manifest.source_limitations,
        )
    if not approved:
        return SourceProviderSmokeCheckResult(
            provider_id=manifest.id,
            provider_name=manifest.name,
            source_mode=manifest.source_mode,
            status=SourceProviderSmokeCheckStatus.REQUIRES_APPROVAL,
            checked_at=resolved_checked_at,
            diagnostic_summary="Live source-provider smoke check requires explicit approval.",
            configured_env_vars=readiness.configured_env_vars,
            source_limitations=manifest.source_limitations,
        )
    runner_result = (runner or run_source_provider_live_smoke)(
        manifest,
        env=env,
        smoke_target=smoke_target,
        timeout_seconds=timeout_seconds,
    )
    if runner_result.timed_out:
        status = SourceProviderSmokeCheckStatus.TIMEOUT
    elif runner_result.ok:
        status = SourceProviderSmokeCheckStatus.SUCCESS
    else:
        status = SourceProviderSmokeCheckStatus.FAILURE
    return SourceProviderSmokeCheckResult(
        provider_id=manifest.id,
        provider_name=manifest.name,
        source_mode=manifest.source_mode,
        status=status,
        checked_at=resolved_checked_at,
        diagnostic_summary=_redact_env_values(runner_result.diagnostic_summary, env),
        configured_env_vars=readiness.configured_env_vars,
        endpoint_label=runner_result.endpoint_label,
        observed_result_count=runner_result.observed_result_count,
        source_limitations=manifest.source_limitations,
    )


def run_source_provider_live_smoke(
    manifest: SourceCollectionProviderManifest,
    *,
    env: dict[str, str],
    smoke_target: str,
    timeout_seconds: int,
) -> SourceProviderSmokeRunnerResult:
    try:
        if manifest.id == "crawl4ai_local":
            return _smoke_crawl4ai(env, timeout_seconds=timeout_seconds)
        if manifest.id == "searxng_local":
            return _smoke_searxng(
                env,
                smoke_target=smoke_target,
                timeout_seconds=timeout_seconds,
            )
        if manifest.id == "serpapi_live":
            return _smoke_serpapi(
                env,
                smoke_target=smoke_target,
                timeout_seconds=timeout_seconds,
            )
        if manifest.id == "olostep_live":
            return _smoke_olostep(
                env,
                smoke_target=smoke_target,
                timeout_seconds=timeout_seconds,
            )
        if manifest.id == "firecrawl_live":
            return _smoke_firecrawl(
                env,
                smoke_target=smoke_target,
                timeout_seconds=timeout_seconds,
            )
    except TimeoutError as error:
        return SourceProviderSmokeRunnerResult(
            timed_out=True,
            diagnostic_summary=f"source provider smoke timed out: {error}",
        )
    except ValueError as error:
        return SourceProviderSmokeRunnerResult(diagnostic_summary=str(error))
    return SourceProviderSmokeRunnerResult(
        diagnostic_summary=f"unknown source provider smoke target: {manifest.id}"
    )


def create_source_provider_adapter(
    *,
    env: dict[str, str],
    registry: SourceProviderRegistry,
    provider_ids: tuple[str, ...] = (),
    http_client: SourceProviderHttpClient | None = None,
) -> ProviderBackedWebSourceCollectionAdapter:
    selected_provider_ids = registry.require_available_provider_ids(provider_ids)
    if not any(
        provider_id in selected_provider_ids
        for provider_id in ("serpapi_live", "olostep_live")
    ):
        raise ValueError(
            "live source provider collection currently requires SerpApi or Olostep"
        )
    return ProviderBackedWebSourceCollectionAdapter(
        env=env,
        provider_ids=selected_provider_ids,
        http_client=http_client,
    )


def list_source_provider_manifests() -> tuple[SourceCollectionProviderManifest, ...]:
    return _SOURCE_PROVIDER_MANIFESTS


def _source_provider_manifest_by_id(provider_id: str) -> SourceCollectionProviderManifest:
    for manifest in _SOURCE_PROVIDER_MANIFESTS:
        if manifest.id == provider_id:
            return manifest
    raise ValueError(f"unknown source provider: {provider_id}")


def _source_provider_readiness(
    manifest: SourceCollectionProviderManifest, env: dict[str, str]
) -> SourceCollectionProviderReadiness:
    configured_env_vars = tuple(
        env_var_name for env_var_name in manifest.required_env_vars if env.get(env_var_name)
    )
    missing_env_vars = tuple(
        env_var_name
        for env_var_name in manifest.required_env_vars
        if not env.get(env_var_name)
    )
    status = (
        SourceCollectionProviderStatus.MISSING_CONFIG
        if missing_env_vars
        else SourceCollectionProviderStatus.AVAILABLE
    )
    diagnostic_summary = (
        "configured via env var names: " + ", ".join(configured_env_vars)
        if status is SourceCollectionProviderStatus.AVAILABLE
        else "missing required env vars: " + ", ".join(missing_env_vars)
    )
    return SourceCollectionProviderReadiness(
        provider_id=manifest.id,
        provider_name=manifest.name,
        role=manifest.role,
        source_mode=manifest.source_mode,
        status=status,
        priority=manifest.priority,
        configured_env_vars=configured_env_vars,
        missing_env_vars=missing_env_vars,
        diagnostic_summary=diagnostic_summary,
        source_limitations=manifest.source_limitations,
    )


def _source_collection_quality(
    providers: tuple[SourceCollectionProviderReadiness, ...]
) -> tuple[SourceCollectionQualityStatus, str, tuple[str, ...]]:
    available = tuple(
        provider
        for provider in sorted(providers, key=lambda candidate: candidate.priority)
        if provider.status is SourceCollectionProviderStatus.AVAILABLE
    )
    search_provider = _first_provider_for_roles(
        available,
        (
            SourceCollectionProviderRole.SEARCH_DISCOVERY,
            SourceCollectionProviderRole.SEARCH_AND_CRAWL,
        ),
    )
    crawl_provider = _first_provider_for_roles(
        available,
        (
            SourceCollectionProviderRole.PAGE_CRAWL_EXTRACTION,
            SourceCollectionProviderRole.SEARCH_AND_CRAWL,
        ),
    )
    if search_provider and crawl_provider:
        recommended_provider_ids = tuple(
            dict.fromkeys((search_provider.provider_id, crawl_provider.provider_id))
        )
        return (
            SourceCollectionQualityStatus.FULL_READY,
            "Search discovery and page crawl/extraction coverage are configured.",
            recommended_provider_ids,
        )
    if search_provider:
        return (
            SourceCollectionQualityStatus.DISCOVERY_ONLY,
            "Search discovery is configured, but page crawl/extraction coverage is missing.",
            (search_provider.provider_id,),
        )
    if crawl_provider:
        return (
            SourceCollectionQualityStatus.EXTRACTION_ONLY,
            "Page crawl/extraction is configured, but search discovery coverage is missing.",
            (crawl_provider.provider_id,),
        )
    return (
        SourceCollectionQualityStatus.NOT_READY,
        "No source collection provider is configured.",
        (),
    )


def _first_provider_for_roles(
    providers: tuple[SourceCollectionProviderReadiness, ...],
    roles: tuple[SourceCollectionProviderRole, ...],
) -> SourceCollectionProviderReadiness | None:
    for provider in providers:
        if provider.role in roles:
            return provider
    return None


def _smoke_crawl4ai(
    env: dict[str, str], *, timeout_seconds: int
) -> SourceProviderSmokeRunnerResult:
    base_url = _normalized_base_url(env["CRAWL4AI_BASE_URL"])
    try:
        _request_json("GET", f"{base_url}/health", timeout_seconds=timeout_seconds)
        return SourceProviderSmokeRunnerResult(
            ok=True,
            diagnostic_summary="Crawl4AI health endpoint responded.",
            endpoint_label="crawl4ai_health",
            observed_result_count=1,
        )
    except ValueError:
        openapi = _request_json(
            "GET", f"{base_url}/openapi.json", timeout_seconds=timeout_seconds
        )
        return SourceProviderSmokeRunnerResult(
            ok=bool(openapi),
            diagnostic_summary="Crawl4AI OpenAPI endpoint responded.",
            endpoint_label="crawl4ai_openapi",
            observed_result_count=1 if openapi else 0,
        )


def _smoke_searxng(
    env: dict[str, str], *, smoke_target: str, timeout_seconds: int
) -> SourceProviderSmokeRunnerResult:
    base_url = _normalized_base_url(env["SEARXNG_BASE_URL"])
    response = _request_json(
        "GET",
        f"{base_url}/search?{urlencode({'q': smoke_target, 'format': 'json'})}",
        timeout_seconds=timeout_seconds,
    )
    results = response.get("results", [])
    result_count = len(results) if isinstance(results, list) else 0
    return SourceProviderSmokeRunnerResult(
        ok=result_count > 0,
        diagnostic_summary=f"SearXNG returned {result_count} search result(s).",
        endpoint_label="searxng_search_json",
        observed_result_count=result_count,
    )


def _smoke_serpapi(
    env: dict[str, str], *, smoke_target: str, timeout_seconds: int
) -> SourceProviderSmokeRunnerResult:
    url = (
        "https://serpapi.com/search.json?"
        + urlencode(
            {
                "engine": "google",
                "q": smoke_target,
                "api_key": env["SERPAPI_API_KEY"],
            }
        )
    )
    response = _request_json("GET", url, timeout_seconds=timeout_seconds)
    results = response.get("organic_results", [])
    result_count = len(results) if isinstance(results, list) else 0
    return SourceProviderSmokeRunnerResult(
        ok=result_count > 0,
        diagnostic_summary=f"SerpApi returned {result_count} organic result(s).",
        endpoint_label="serpapi_google_search_json",
        observed_result_count=result_count,
    )


def _smoke_olostep(
    env: dict[str, str], *, smoke_target: str, timeout_seconds: int
) -> SourceProviderSmokeRunnerResult:
    response = _request_json(
        "POST",
        "https://api.olostep.com/v1/scrapes",
        headers=_olostep_headers(env["OLOSTEP_API_KEY"]),
        payload={
            "url_to_scrape": smoke_target,
            "formats": ["markdown"],
            "remove_css_selectors": "default",
        },
        timeout_seconds=timeout_seconds,
    )
    result = response.get("result", {})
    result_count = 1 if isinstance(result, dict) and result else 0
    return SourceProviderSmokeRunnerResult(
        ok=result_count > 0,
        diagnostic_summary="Olostep scrape endpoint returned content metadata.",
        endpoint_label="olostep_scrapes_markdown",
        observed_result_count=result_count,
    )


def _smoke_firecrawl(
    env: dict[str, str], *, smoke_target: str, timeout_seconds: int
) -> SourceProviderSmokeRunnerResult:
    response = _request_json(
        "POST",
        "https://api.firecrawl.dev/v1/scrape",
        headers={
            "Authorization": f"Bearer {env['FIRECRAWL_API_KEY']}",
            "Content-Type": "application/json",
        },
        payload={"url": smoke_target, "formats": ["markdown"]},
        timeout_seconds=timeout_seconds,
    )
    success = response.get("success") is True or isinstance(response.get("data"), dict)
    return SourceProviderSmokeRunnerResult(
        ok=success,
        diagnostic_summary="Firecrawl scrape endpoint responded."
        if success
        else "Firecrawl scrape endpoint returned no success marker.",
        endpoint_label="firecrawl_scrape_markdown",
        observed_result_count=1 if success else 0,
    )


def _normalized_base_url(value: str) -> str:
    return value.rstrip("/")


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    payload: dict[str, object] | None = None,
    timeout_seconds: int = 60,
) -> dict[str, object]:
    request_headers = headers or {}
    data = None
    if payload is not None:
        request_headers = {"Content-Type": "application/json", **request_headers}
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=request_headers, method=method)
    return _read_json_response(request, timeout_seconds=timeout_seconds)


def _read_json_response(
    request: Request, *, timeout_seconds: int = 60
) -> dict[str, object]:
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ValueError(f"source provider request failed: {error.code} {detail}") from error
    except URLError as error:
        raise ValueError(f"source provider request failed: {error.reason}") from error
    except TimeoutError as error:
        raise TimeoutError("source provider request timed out") from error
    if not isinstance(payload, dict):
        raise ValueError("source provider returned a non-object JSON response")
    return payload


def _olostep_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _as_string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _compact_excerpt(value: str, *, limit: int = 420) -> str:
    compacted = " ".join(value.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."


def _redact_env_values(text: str, env: dict[str, str]) -> str:
    redacted = text
    for value in sorted(env.values(), key=len, reverse=True):
        if value:
            redacted = redacted.replace(value, "<redacted>")
    return redacted


class FakeWebSourceCollectionAdapter:
    source_mode = CaptureResearchSourceMode.FAKE_ADAPTER_TEST

    def collect(
        self,
        run: CaptureResearchRun,
        *,
        collected_at: str,
    ) -> tuple[tuple[WebSourceCollectionRecord, ...], tuple[SourceFinding, ...]]:
        provenance = CapabilityProvenance(
            source_capability_id="fake_web_source_collection",
            source_tool_name="collect_fake_public_sources",
            source_package="ariadne.capture_research",
            source_package_version="local",
        )
        limitations = (
            "Fake adapter test data is not live source-provider success.",
            "No live network request was made.",
        )
        findings = tuple(
            _fake_source_finding(
                source_target,
                collected_at=collected_at,
                provenance=provenance,
                limitations=limitations,
            )
            for source_target in run.research_brief.source_targets
        )
        records = tuple(
            WebSourceCollectionRecord(
                id=f"web_collection_{uuid4().hex}",
                source_target=finding.source_target,
                source_mode=self.source_mode,
                collected_at=collected_at,
                capability_provenance=provenance,
                source_limitations=limitations,
                finding_ids=(finding.id,),
                provider_ids=("fake_adapter_test",),
                approval_basis=run.research_brief.approval_basis,
            )
            for finding in findings
        )
        return records, findings


def run_web_source_collection(
    *,
    store: CaptureResearchStore,
    research_run_id: str,
    adapter: WebSourceCollectionAdapter,
    collected_at: str | None = None,
) -> CaptureResearchRun:
    timestamp = collected_at or datetime.now(UTC).isoformat()
    run = store.read(research_run_id)
    records, findings = adapter.collect(run, collected_at=timestamp)
    updated = run.model_copy(
        update={
            "status": CaptureResearchRunStatus.NEEDS_REVIEW,
            "source_collection_records": run.source_collection_records + records,
            "source_findings": run.source_findings + findings,
            "updated_at": timestamp,
        }
    )
    return store.write(updated)


def run_approved_source_provider_collection(
    *,
    store: CaptureResearchStore,
    research_run_id: str,
    registry: SourceProviderRegistry,
    adapter: ApprovedWebSourceCollectionAdapter,
    approved: bool,
    provider_ids: tuple[str, ...] = (),
    collected_at: str | None = None,
) -> CaptureResearchRun:
    timestamp = collected_at or datetime.now(UTC).isoformat()
    run = store.read(research_run_id)
    _validate_source_provider_run_request(
        run,
        registry=registry,
        adapter=adapter,
        approved=approved,
        provider_ids=provider_ids,
    )
    records, findings = adapter.collect(run, collected_at=timestamp)
    updated = run.model_copy(
        update={
            "status": CaptureResearchRunStatus.NEEDS_REVIEW,
            "source_collection_records": run.source_collection_records + records,
            "source_findings": run.source_findings + findings,
            "updated_at": timestamp,
        }
    )
    return store.write(updated)


def build_seller_baseline_query(run: CaptureResearchRun) -> str:
    parts = [
        run.research_brief.research_question,
        run.research_trigger_context.summary,
        " ".join(run.research_brief.known_pivots),
        " ".join(run.research_brief.evidence_goals),
        " ".join(run.research_brief.source_targets),
        " ".join(ref.source_element_summary for ref in run.source_profile_refs),
        " ".join(finding.title for finding in run.source_findings),
        " ".join(finding.excerpt for finding in run.source_findings),
        "seller capability baseline past performance proof vehicle transition",
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def run_requirements_fit_analysis(
    *,
    store: CaptureResearchStore,
    research_run_id: str,
    evidence_items: tuple[EvidenceItem, ...] = (),
    reference_influences: tuple[ReferenceWikiInfluence, ...] = (),
    analyzed_at: str | None = None,
) -> CaptureResearchRun:
    timestamp = analyzed_at or datetime.now(UTC).isoformat()
    run = store.read(research_run_id)
    baseline_refs = select_seller_baseline_refs(
        run,
        evidence_items=evidence_items,
        reference_influences=reference_influences,
    )
    analysis = build_requirements_fit_analysis(
        run,
        seller_baseline_refs=baseline_refs,
        analyzed_at=timestamp,
    )
    insight_candidates = _requirements_fit_insight_candidates(analysis)
    updated = run.model_copy(
        update={
            "status": CaptureResearchRunStatus.NEEDS_REVIEW,
            "seller_baseline_refs": baseline_refs,
            "requirements_fit_analysis": analysis,
            "insight_candidates": run.insight_candidates + insight_candidates,
            "research_summary_view": _requirements_fit_summary_view(analysis),
            "updated_at": timestamp,
        }
    )
    return store.write(updated)


def run_competitive_gap_analysis(
    *,
    store: CaptureResearchStore,
    research_run_id: str,
    analyzed_at: str | None = None,
) -> CaptureResearchRun:
    timestamp = analyzed_at or datetime.now(UTC).isoformat()
    run = store.read(research_run_id)
    baseline_refs = run.seller_baseline_refs or (_missing_seller_baseline_ref(run),)
    analysis = build_competitive_gap_analysis(
        run,
        seller_baseline_refs=baseline_refs,
        analyzed_at=timestamp,
    )
    insight_candidates = _competitive_gap_insight_candidates(analysis)
    updated = run.model_copy(
        update={
            "status": CaptureResearchRunStatus.NEEDS_REVIEW,
            "seller_baseline_refs": baseline_refs,
            "competitive_gap_analysis": analysis,
            "insight_candidates": run.insight_candidates + insight_candidates,
            "research_summary_view": _competitive_gap_summary_view(analysis),
            "updated_at": timestamp,
        }
    )
    return store.write(updated)


def select_seller_baseline_refs(
    run: CaptureResearchRun,
    *,
    evidence_items: tuple[EvidenceItem, ...] = (),
    reference_influences: tuple[ReferenceWikiInfluence, ...] = (),
    evidence_limit: int = 4,
    reference_limit: int = 4,
) -> tuple[SellerBaselineRef, ...]:
    query_tokens = _normalized_signal_tokens(build_seller_baseline_query(run))
    evidence_refs = tuple(
        _seller_baseline_ref_from_evidence(evidence, matched_terms=matched_terms)
        for evidence, matched_terms in _rank_seller_baseline_evidence(
            run,
            evidence_items=evidence_items,
            query_tokens=query_tokens,
        )[:evidence_limit]
    )
    reference_refs = tuple(
        _seller_baseline_ref_from_reference(influence)
        for influence in reference_influences[:reference_limit]
    )
    refs = evidence_refs + reference_refs
    if refs:
        return refs
    return (_missing_seller_baseline_ref(run),)


def build_requirements_fit_analysis(
    run: CaptureResearchRun,
    *,
    seller_baseline_refs: tuple[SellerBaselineRef, ...],
    analyzed_at: str,
) -> RequirementsFitAnalysis:
    ref_ids = tuple(ref.id for ref in seller_baseline_refs)
    finding_ids = tuple(finding.id for finding in run.source_findings)
    non_gap_ref_ids = tuple(
        ref.id
        for ref in seller_baseline_refs
        if ref.ref_type is not SellerBaselineRefType.BASELINE_GAP
    )
    gap_refs = tuple(
        ref for ref in seller_baseline_refs if ref.ref_type is SellerBaselineRefType.BASELINE_GAP
    )
    shared_terms = _shared_requirement_terms(run, seller_baseline_refs)
    strengths = _requirements_fit_strengths(
        ref_ids=non_gap_ref_ids,
        finding_ids=finding_ids,
        shared_terms=shared_terms,
    )
    weaknesses = _requirements_fit_weaknesses(
        ref_ids=ref_ids,
        finding_ids=finding_ids,
        gap_refs=gap_refs,
        shared_terms=shared_terms,
    )
    qualification_risks = _requirements_fit_qualification_risks(
        ref_ids=ref_ids,
        finding_ids=finding_ids,
        gap_refs=gap_refs,
        has_findings=bool(run.source_findings),
    )
    proof_needs = _requirements_fit_proof_needs(
        ref_ids=ref_ids,
        finding_ids=finding_ids,
        gap_refs=gap_refs,
        shared_terms=shared_terms,
    )
    follow_ups = _requirements_fit_follow_ups(
        ref_ids=ref_ids,
        finding_ids=finding_ids,
        gap_refs=gap_refs,
    )
    summary = (
        f"Requirements fit analysis found {len(strengths)} strength(s), "
        f"{len(weaknesses)} weakness(es), {len(qualification_risks)} "
        "qualification risk(s), and "
        f"{len(proof_needs)} proof need(s)."
    )
    return RequirementsFitAnalysis(
        id=f"requirements_fit_{uuid4().hex}",
        analyzed_at=analyzed_at,
        summary=summary,
        seller_baseline_ref_ids=ref_ids,
        source_finding_ids=finding_ids,
        selected_lenses=run.selected_lenses,
        strengths=strengths,
        weaknesses=weaknesses,
        qualification_risks=qualification_risks,
        proof_needs=proof_needs,
        follow_up_recommendations=follow_ups,
    )


def build_competitive_gap_analysis(
    run: CaptureResearchRun,
    *,
    seller_baseline_refs: tuple[SellerBaselineRef, ...],
    analyzed_at: str,
) -> CompetitiveGapAnalysis:
    ref_ids = tuple(ref.id for ref in seller_baseline_refs)
    finding_ids = tuple(finding.id for finding in run.source_findings)
    competitor_notes = _competitive_incumbent_notes(run.source_findings)
    discriminators = _competitive_discriminator_candidates(
        seller_baseline_refs=seller_baseline_refs,
        source_finding_ids=finding_ids,
    )
    vulnerabilities = _competitive_vulnerabilities(
        seller_baseline_refs=seller_baseline_refs,
        source_findings=run.source_findings,
    )
    proof_gaps = _competitive_proof_gaps(
        seller_baseline_refs=seller_baseline_refs,
        source_finding_ids=finding_ids,
    )
    teaming_needs = _competitive_teaming_partner_needs(
        seller_baseline_refs=seller_baseline_refs,
        source_findings=run.source_findings,
    )
    bcc_notes = _competitive_bcc_ready_notes(
        ref_ids=ref_ids,
        finding_ids=finding_ids,
        discriminators=discriminators,
        vulnerabilities=vulnerabilities,
        competitor_notes=competitor_notes,
    )
    follow_ups = _competitive_follow_ups(
        ref_ids=ref_ids,
        finding_ids=finding_ids,
        proof_gaps=proof_gaps,
        teaming_needs=teaming_needs,
    )
    summary = (
        f"Competitive gap analysis found {len(discriminators)} discriminator candidate(s), "
        f"{len(vulnerabilities)} vulnerabilit(y/ies), {len(competitor_notes)} "
        f"competitor/incumbent note(s), and {len(teaming_needs)} teaming need(s)."
    )
    return CompetitiveGapAnalysis(
        id=f"competitive_gap_{uuid4().hex}",
        analyzed_at=analyzed_at,
        summary=summary,
        seller_baseline_ref_ids=ref_ids,
        source_finding_ids=finding_ids,
        selected_lenses=run.selected_lenses,
        discriminator_candidates=discriminators,
        vulnerabilities=vulnerabilities,
        proof_gaps=proof_gaps,
        competitor_incumbent_notes=competitor_notes,
        teaming_partner_needs=teaming_needs,
        bcc_ready_notes=bcc_notes,
        follow_up_recommendations=follow_ups,
    )


def _rank_seller_baseline_evidence(
    run: CaptureResearchRun,
    *,
    evidence_items: tuple[EvidenceItem, ...],
    query_tokens: set[str],
) -> list[tuple[EvidenceItem, tuple[str, ...]]]:
    ranked: list[tuple[int, str, EvidenceItem, tuple[str, ...]]] = []
    for evidence in evidence_items:
        if (
            run.opportunity_id
            and evidence.opportunity_id
            and evidence.opportunity_id != run.opportunity_id
        ):
            continue
        evidence_tokens = _normalized_signal_tokens(evidence.content)
        baseline_matches = evidence_tokens & _SELLER_BASELINE_KEYWORDS
        query_matches = evidence_tokens & query_tokens
        if not baseline_matches and len(query_matches) < 2:
            continue
        matched_terms = tuple(sorted((baseline_matches | query_matches))[:8])
        score = (len(baseline_matches) * 3) + len(query_matches)
        if evidence.opportunity_id == run.opportunity_id:
            score += 2
        ranked.append((score, evidence.id, evidence, matched_terms))
    return [
        (evidence, matched_terms)
        for _, _, evidence, matched_terms in sorted(
            ranked,
            key=lambda candidate: (-candidate[0], candidate[1]),
        )
    ]


def _competitive_discriminator_candidates(
    *,
    seller_baseline_refs: tuple[SellerBaselineRef, ...],
    source_finding_ids: tuple[str, ...],
) -> tuple[CompetitiveGapSignal, ...]:
    refs = tuple(
        ref
        for ref in seller_baseline_refs
        if ref.ref_type is not SellerBaselineRefType.BASELINE_GAP
    )
    if not refs:
        return ()
    terms = tuple(
        sorted(
            {
                term
                for ref in refs
                for term in ref.matched_terms
                if term in _SELLER_BASELINE_KEYWORDS or term in _GAP_SIGNAL_TERMS
            }
        )
    )[:6]
    summary = "Seller baseline may support discriminator claims"
    if terms:
        summary += " around " + ", ".join(terms) + "."
    else:
        summary += ", but reviewer must connect proof to customer hot buttons."
    return (
        _competitive_gap_signal(
            "discriminator",
            summary,
            ref_ids=tuple(ref.id for ref in refs),
            finding_ids=source_finding_ids,
            assumptions=(
                "Discriminators remain candidates until reviewer confirms relevance, uniqueness, and proof strength.",
            ),
            confidence=0.68 if terms else 0.55,
        ),
    )


def _competitive_vulnerabilities(
    *,
    seller_baseline_refs: tuple[SellerBaselineRef, ...],
    source_findings: tuple[SourceFinding, ...],
) -> tuple[CompetitiveGapSignal, ...]:
    vulnerabilities: list[CompetitiveGapSignal] = []
    finding_ids = tuple(finding.id for finding in source_findings)
    for ref in seller_baseline_refs:
        for gap in ref.baseline_gaps:
            vulnerabilities.append(
                _competitive_gap_signal(
                    "vulnerability",
                    "Competitive vulnerability: " + gap,
                    ref_ids=(ref.id,),
                    finding_ids=finding_ids,
                    assumptions=ref.assumptions,
                    confidence=0.78,
                )
            )
    if _source_findings_have_terms(source_findings, _COMPETITIVE_SIGNAL_TERMS):
        vulnerabilities.append(
            _competitive_gap_signal(
                "vulnerability",
                "Competitor or incumbent signals require proof-backed positioning before using seller fit claims.",
                ref_ids=tuple(ref.id for ref in seller_baseline_refs),
                finding_ids=finding_ids,
                assumptions=(
                    "Public-source competitor signals are directional until reviewed against customer evidence.",
                ),
                confidence=0.7,
            )
        )
    return tuple(vulnerabilities)


def _competitive_proof_gaps(
    *,
    seller_baseline_refs: tuple[SellerBaselineRef, ...],
    source_finding_ids: tuple[str, ...],
) -> tuple[CompetitiveGapSignal, ...]:
    proof_gaps: list[CompetitiveGapSignal] = []
    if any(ref.ref_type is SellerBaselineRefType.BASELINE_GAP for ref in seller_baseline_refs):
        proof_gaps.append(
            _competitive_gap_signal(
                "proof_gap",
                "Seller proof gap blocks confident competitive positioning against incumbent or competitor alternatives.",
                ref_ids=tuple(ref.id for ref in seller_baseline_refs),
                finding_ids=source_finding_ids,
                assumptions=("Proof gap should route to Evidence or Action Plan review before BCC use.",),
                confidence=0.82,
            )
        )
    elif seller_baseline_refs:
        proof_gaps.append(
            _competitive_gap_signal(
                "proof_gap",
                "Attach sharper proof artifacts before promoting discriminator or vulnerability claims.",
                ref_ids=tuple(ref.id for ref in seller_baseline_refs),
                finding_ids=source_finding_ids,
                assumptions=("Baseline refs support analysis but may not yet be evaluator-ready proof.",),
                confidence=0.62,
            )
        )
    return tuple(proof_gaps)


def _competitive_incumbent_notes(
    source_findings: tuple[SourceFinding, ...]
) -> tuple[CompetitiveGapSignal, ...]:
    notes: list[CompetitiveGapSignal] = []
    for finding in source_findings:
        tokens = _normalized_signal_tokens(f"{finding.title} {finding.excerpt}")
        matched_terms = tuple(sorted(tokens & _COMPETITIVE_SIGNAL_TERMS))
        if not matched_terms:
            continue
        notes.append(
            _competitive_gap_signal(
                "competitor_note",
                "Public source suggests competitor/incumbent signal around "
                + ", ".join(matched_terms)
                + f": {finding.title}.",
                finding_ids=(finding.id,),
                assumptions=(
                    "Competitor/incumbent note is a reviewable signal, not confirmed competitive intelligence.",
                ),
                confidence=min(0.85, max(0.55, finding.confidence)),
            )
        )
    if notes:
        return tuple(notes)
    if source_findings:
        return (
            _competitive_gap_signal(
                "competitor_note",
                "No explicit competitor or incumbent signal found in current Source Findings.",
                finding_ids=tuple(finding.id for finding in source_findings),
                assumptions=("Run targeted competitor/incumbent research before BCC preparation.",),
                confidence=0.5,
            ),
        )
    return ()


def _competitive_teaming_partner_needs(
    *,
    seller_baseline_refs: tuple[SellerBaselineRef, ...],
    source_findings: tuple[SourceFinding, ...],
) -> tuple[CompetitiveGapSignal, ...]:
    finding_ids = tuple(finding.id for finding in source_findings)
    source_has_gap = _source_findings_have_terms(source_findings, _GAP_SIGNAL_TERMS)
    baseline_has_gap = any(ref.baseline_gaps for ref in seller_baseline_refs)
    if not source_has_gap and not baseline_has_gap:
        return ()
    return (
        _competitive_gap_signal(
            "teaming_need",
            "Teaming Partner Need: investigate partner coverage for capability, vehicle, staffing, certification, or customer-access gaps before competitive positioning hardens.",
            ref_ids=tuple(ref.id for ref in seller_baseline_refs),
            finding_ids=finding_ids,
            assumptions=(
                "Teaming need is a candidate route; reviewer must confirm gap size and partner strategy.",
            ),
            confidence=0.72,
        ),
    )


def _competitive_bcc_ready_notes(
    *,
    ref_ids: tuple[str, ...],
    finding_ids: tuple[str, ...],
    discriminators: tuple[CompetitiveGapSignal, ...],
    vulnerabilities: tuple[CompetitiveGapSignal, ...],
    competitor_notes: tuple[CompetitiveGapSignal, ...],
) -> tuple[CompetitiveGapSignal, ...]:
    if not (discriminators or vulnerabilities or competitor_notes):
        return ()
    return (
        _competitive_gap_signal(
            "bcc_ready_note",
            "BCC-ready input only: use these discriminator, vulnerability, and competitor/incumbent signals as evidence candidates for later Bidder Comparison Chart work; no BCC row, slide, or artifact is generated.",
            ref_ids=ref_ids,
            finding_ids=finding_ids,
            assumptions=(
                "Later BCC artifact work must re-check evidence, scoring criteria, and reviewer decisions.",
            ),
            confidence=0.76,
            bcc_ready_input=True,
        ),
    )


def _competitive_follow_ups(
    *,
    ref_ids: tuple[str, ...],
    finding_ids: tuple[str, ...],
    proof_gaps: tuple[CompetitiveGapSignal, ...],
    teaming_needs: tuple[CompetitiveGapSignal, ...],
) -> tuple[CompetitiveGapSignal, ...]:
    recommendations = [
        "Review competitive signals, confirm proof strength, then route accepted needs to Evidence, Action Plan, Risk Register, or Call Plan workflows."
    ]
    if proof_gaps:
        recommendations.append("Collect evaluator-ready proof for discriminator and vulnerability claims.")
    if teaming_needs:
        recommendations.append("Open teaming research for unresolved capability, vehicle, staffing, certification, or access gaps.")
    return tuple(
        _competitive_gap_signal(
            "follow_up",
            recommendation,
            ref_ids=ref_ids,
            finding_ids=finding_ids,
            assumptions=("Follow-up remains review-gated and does not create downstream records automatically.",),
            confidence=0.74,
        )
        for recommendation in recommendations
    )


def _competitive_gap_signal(
    kind: str,
    summary: str,
    *,
    ref_ids: tuple[str, ...] = (),
    finding_ids: tuple[str, ...] = (),
    assumptions: tuple[str, ...] = (),
    confidence: float,
    bcc_ready_input: bool = False,
) -> CompetitiveGapSignal:
    return CompetitiveGapSignal(
        id=f"competitive_gap_{kind}_{uuid4().hex[:8]}",
        summary=summary,
        supporting_seller_baseline_ref_ids=ref_ids,
        supporting_source_finding_ids=finding_ids,
        assumptions=assumptions,
        confidence=confidence,
        bcc_ready_input=bcc_ready_input,
    )


def _source_findings_have_terms(
    source_findings: tuple[SourceFinding, ...], terms: frozenset[str]
) -> bool:
    return any(
        _normalized_signal_tokens(f"{finding.title} {finding.excerpt}") & terms
        for finding in source_findings
    )


def _seller_baseline_ref_from_evidence(
    evidence: EvidenceItem, *, matched_terms: tuple[str, ...]
) -> SellerBaselineRef:
    assumptions = (
        "Accepted evidence can support seller baseline only within its stated source and review context.",
    )
    return SellerBaselineRef(
        id=f"seller_baseline_evidence_{evidence.id}",
        ref_type=SellerBaselineRefType.ACCEPTED_EVIDENCE,
        source_label=f"Accepted Evidence {evidence.id}",
        source_ref=evidence.id,
        summarized_support=_compact_excerpt(evidence.content, limit=260),
        assumptions=assumptions,
        matched_terms=matched_terms,
    )


def _seller_baseline_ref_from_reference(
    influence: ReferenceWikiInfluence,
) -> SellerBaselineRef:
    return SellerBaselineRef(
        id=f"seller_baseline_reference_{_source_target_slug(influence.reference_id)}",
        ref_type=SellerBaselineRefType.REFERENCE_WIKI_NOTE,
        source_label=influence.title,
        source_ref=influence.source_path,
        summarized_support=_compact_excerpt(
            influence.why_it_matters or influence.excerpt,
            limit=260,
        ),
        assumptions=(
            "Reference Wiki notes can guide seller baseline fit but do not replace opportunity-specific accepted evidence.",
        ),
        baseline_gaps=(
            "Confirm the reference note is current and applicable to this opportunity before using it as proof.",
        ),
        matched_terms=influence.matched_terms,
    )


def _missing_seller_baseline_ref(run: CaptureResearchRun) -> SellerBaselineRef:
    return SellerBaselineRef(
        id=f"seller_baseline_gap_{_source_target_slug(run.research_run_id)}",
        ref_type=SellerBaselineRefType.BASELINE_GAP,
        source_label="Seller Capability Baseline gap",
        source_ref=run.research_run_id,
        summarized_support=(
            "No accepted seller capability evidence or Reference Wiki note matched this research run."
        ),
        assumptions=(
            "Ariadne should not infer seller capabilities without accepted proof or reference context.",
        ),
        baseline_gaps=(
            "Add accepted evidence for relevant seller capabilities, vehicles, past performance, relationships, certifications, differentiators, constraints, or transition proof.",
        ),
    )


def _shared_requirement_terms(
    run: CaptureResearchRun,
    refs: tuple[SellerBaselineRef, ...],
) -> tuple[str, ...]:
    requirement_tokens = _normalized_signal_tokens(
        " ".join(
            (
                run.research_brief.research_question,
                " ".join(run.research_brief.evidence_goals),
                " ".join(finding.excerpt for finding in run.source_findings),
            )
        )
    )
    baseline_tokens = _normalized_signal_tokens(
        " ".join(ref.summarized_support for ref in refs)
    )
    shared = (requirement_tokens & baseline_tokens) - _LOW_SIGNAL_REQUIREMENT_TERMS
    return tuple(sorted(shared))[:8]


def _requirements_fit_strengths(
    *,
    ref_ids: tuple[str, ...],
    finding_ids: tuple[str, ...],
    shared_terms: tuple[str, ...],
) -> tuple[RequirementsFitSignal, ...]:
    if not ref_ids:
        return ()
    if shared_terms:
        summary = (
            "Seller baseline refs overlap with customer/source signals around "
            + ", ".join(shared_terms[:5])
            + "."
        )
        confidence = 0.72
    else:
        summary = (
            "Seller baseline refs are available for comparison, but exact requirement overlap still needs reviewer confirmation."
        )
        confidence = 0.56
    return (
        _requirements_fit_signal(
            "strength",
            summary,
            ref_ids=ref_ids,
            finding_ids=finding_ids,
            assumptions=(
                "Deterministic term overlap is a fit signal, not a final qualification decision.",
            ),
            confidence=confidence,
        ),
    )


def _requirements_fit_weaknesses(
    *,
    ref_ids: tuple[str, ...],
    finding_ids: tuple[str, ...],
    gap_refs: tuple[SellerBaselineRef, ...],
    shared_terms: tuple[str, ...],
) -> tuple[RequirementsFitSignal, ...]:
    if gap_refs:
        return tuple(
            _requirements_fit_signal(
                "weakness",
                gap,
                ref_ids=(gap_ref.id,),
                finding_ids=finding_ids,
                assumptions=gap_ref.assumptions,
                confidence=0.82,
            )
            for gap_ref in gap_refs
            for gap in gap_ref.baseline_gaps
        )
    if not shared_terms:
        return (
            _requirements_fit_signal(
                "weakness",
                "Available seller baseline refs do not yet show direct proof against the collected customer/source signals.",
                ref_ids=ref_ids,
                finding_ids=finding_ids,
                assumptions=(
                    "The baseline may still fit, but Ariadne has not found explicit linked proof yet.",
                ),
                confidence=0.64,
            ),
        )
    return ()


def _requirements_fit_qualification_risks(
    *,
    ref_ids: tuple[str, ...],
    finding_ids: tuple[str, ...],
    gap_refs: tuple[SellerBaselineRef, ...],
    has_findings: bool,
) -> tuple[RequirementsFitSignal, ...]:
    risks: list[RequirementsFitSignal] = []
    if gap_refs:
        risks.append(
            _requirements_fit_signal(
                "risk",
                "Qualification risk: the run lacks enough accepted seller proof to support a confident fit position.",
                ref_ids=ref_ids,
                finding_ids=finding_ids,
                assumptions=(
                    "Capture decisions should stay tentative until seller proof is accepted or attached.",
                ),
                confidence=0.78,
            )
        )
    if not has_findings:
        risks.append(
            _requirements_fit_signal(
                "risk",
                "Qualification risk: requirements fit is based on the brief and baseline refs before source findings are collected.",
                ref_ids=ref_ids,
                assumptions=(
                    "Run Web Source Collection or attach source-profile evidence before relying on this analysis.",
                ),
                confidence=0.68,
            )
        )
    return tuple(risks)


def _requirements_fit_proof_needs(
    *,
    ref_ids: tuple[str, ...],
    finding_ids: tuple[str, ...],
    gap_refs: tuple[SellerBaselineRef, ...],
    shared_terms: tuple[str, ...],
) -> tuple[RequirementsFitSignal, ...]:
    if gap_refs:
        return (
            _requirements_fit_signal(
                "proof_need",
                "Collect or accept seller proof for the baseline gaps before promoting fit claims.",
                ref_ids=ref_ids,
                finding_ids=finding_ids,
                assumptions=("Proof needs should route to Evidence, Packet, or Action Plan review.",),
                confidence=0.84,
            ),
        )
    if shared_terms:
        return (
            _requirements_fit_signal(
                "proof_need",
                "Attach stronger proof artifacts that connect seller baseline refs to the identified customer/source terms.",
                ref_ids=ref_ids,
                finding_ids=finding_ids,
                assumptions=("Current fit support is directional until proof is linked to exact requirements.",),
                confidence=0.66,
            ),
        )
    return ()


def _requirements_fit_follow_ups(
    *,
    ref_ids: tuple[str, ...],
    finding_ids: tuple[str, ...],
    gap_refs: tuple[SellerBaselineRef, ...],
) -> tuple[RequirementsFitSignal, ...]:
    if gap_refs:
        summary = (
            "Ask the user for seller capability, vehicle, past-performance, relationship, certification, differentiator, or constraint evidence."
        )
    else:
        summary = (
            "Review the fit analysis and route strongest proof needs into Evidence, Packet, Action Plan, or Risk Register candidates."
        )
    return (
        _requirements_fit_signal(
            "follow_up",
            summary,
            ref_ids=ref_ids,
            finding_ids=finding_ids,
            assumptions=("Follow-up recommendations remain reviewable and do not write trusted downstream records.",),
            confidence=0.74,
        ),
    )


def _requirements_fit_signal(
    kind: str,
    summary: str,
    *,
    ref_ids: tuple[str, ...] = (),
    finding_ids: tuple[str, ...] = (),
    assumptions: tuple[str, ...] = (),
    confidence: float,
) -> RequirementsFitSignal:
    return RequirementsFitSignal(
        id=f"requirements_fit_{kind}_{uuid4().hex[:8]}",
        summary=summary,
        supporting_seller_baseline_ref_ids=ref_ids,
        supporting_source_finding_ids=finding_ids,
        assumptions=assumptions,
        confidence=confidence,
    )


def _requirements_fit_insight_candidates(
    analysis: RequirementsFitAnalysis,
) -> tuple[dict[str, object], ...]:
    candidates: list[dict[str, object]] = []
    for candidate_type, target_workflow, signals in (
        ("requirements_fit_strength", "evidence", analysis.strengths),
        ("requirements_fit_weakness", "packet", analysis.weaknesses),
        ("requirements_fit_qualification_risk", "risk_register", analysis.qualification_risks),
        ("requirements_fit_proof_need", "action_plan", analysis.proof_needs),
        ("requirements_fit_follow_up", "action_plan", analysis.follow_up_recommendations),
    ):
        for signal in signals:
            candidates.append(
                {
                    "id": f"insight_candidate_{signal.id}",
                    "candidate_type": candidate_type,
                    "target_workflow": target_workflow,
                    "title": signal.summary,
                    "summary": signal.summary,
                    "review_state": "pending_review",
                    "supporting_seller_baseline_ref_ids": signal.supporting_seller_baseline_ref_ids,
                    "supporting_source_finding_ids": signal.supporting_source_finding_ids,
                    "autonomy_tier": "review_required",
                    "requirements_fit_analysis_id": analysis.id,
                }
            )
    return tuple(candidates)


def _competitive_gap_insight_candidates(
    analysis: CompetitiveGapAnalysis,
) -> tuple[dict[str, object], ...]:
    candidates: list[dict[str, object]] = []
    for candidate_type, target_workflow, signals in (
        ("competitive_gap_discriminator", "evidence", analysis.discriminator_candidates),
        ("competitive_gap_vulnerability", "risk_register", analysis.vulnerabilities),
        ("competitive_gap_proof_gap", "action_plan", analysis.proof_gaps),
        ("competitive_gap_competitor_note", "packet", analysis.competitor_incumbent_notes),
        ("competitive_gap_teaming_need", "action_plan", analysis.teaming_partner_needs),
        ("competitive_gap_bcc_ready_note", "bcc_ready_input", analysis.bcc_ready_notes),
        ("competitive_gap_follow_up", "action_plan", analysis.follow_up_recommendations),
    ):
        for signal in signals:
            candidates.append(
                {
                    "id": f"insight_candidate_{signal.id}",
                    "candidate_type": candidate_type,
                    "target_workflow": target_workflow,
                    "title": signal.summary,
                    "summary": signal.summary,
                    "review_state": signal.review_state,
                    "supporting_seller_baseline_ref_ids": signal.supporting_seller_baseline_ref_ids,
                    "supporting_source_finding_ids": signal.supporting_source_finding_ids,
                    "autonomy_tier": "review_required",
                    "competitive_gap_analysis_id": analysis.id,
                    "bcc_ready_input": signal.bcc_ready_input,
                    "bcc_artifact_generated": False,
                }
            )
    return tuple(candidates)


def _requirements_fit_summary_view(analysis: RequirementsFitAnalysis) -> str:
    return (
        f"{analysis.summary} Trusted downstream writes remain review-gated; "
        "seller-baseline refs and source findings must be reviewed before promotion."
    )


def _competitive_gap_summary_view(analysis: CompetitiveGapAnalysis) -> str:
    return (
        f"{analysis.summary} BCC-ready notes are inputs for later Bidder Comparison Chart work only; "
        "no BCC artifact, row, or slide is generated. Trusted downstream writes remain review-gated."
    )


def _normalized_signal_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in _LOW_SIGNAL_REQUIREMENT_TERMS
    }


def _validate_source_provider_run_request(
    run: CaptureResearchRun,
    *,
    registry: SourceProviderRegistry,
    adapter: ApprovedWebSourceCollectionAdapter,
    approved: bool,
    provider_ids: tuple[str, ...],
) -> None:
    if not approved:
        raise ValueError("source provider collection requires explicit approval")
    if not run.research_brief.approval_basis.strip():
        raise ValueError("source provider collection requires an approval basis")
    if not run.research_brief.source_targets:
        raise ValueError("source provider collection requires bounded source targets")
    _validate_bounded_public_source_targets(run.research_brief.source_targets)
    selected_provider_ids = registry.require_available_provider_ids(provider_ids)
    if tuple(adapter.provider_ids) != selected_provider_ids:
        raise ValueError(
            "source provider adapter does not match selected provider ids: "
            + ", ".join(selected_provider_ids)
        )


def _validate_bounded_public_source_targets(source_targets: tuple[str, ...]) -> None:
    for source_target in source_targets:
        normalized_target = source_target.strip().lower()
        if not normalized_target:
            raise ValueError("source target is required")
        parsed = urlparse(normalized_target)
        host = parsed.netloc or parsed.path.split("/", 1)[0]
        if host.startswith("www."):
            host = host.removeprefix("www.")
        if host in _RESTRICTED_SOURCE_HOSTS:
            raise ValueError(
                "restricted or logged-in source targets are out of scope: "
                + source_target
            )
        if any(marker in normalized_target for marker in _RESTRICTED_SOURCE_MARKERS):
            raise ValueError(
                "restricted or logged-in source targets are out of scope: "
                + source_target
            )


def _fake_source_finding(
    source_target: str,
    *,
    collected_at: str,
    provenance: CapabilityProvenance,
    limitations: tuple[str, ...],
) -> SourceFinding:
    source_slug = _source_target_slug(source_target)
    return SourceFinding(
        id=f"source_finding_{uuid4().hex}",
        source_target=source_target,
        url=f"fake://capture-research/{source_slug}",
        title=f"Fake source finding for {source_target}",
        source_type="fake_public_web",
        collected_at=collected_at,
        excerpt=f"Fake public-source excerpt for {source_target}.",
        confidence=0.42,
        source_limitations=limitations,
        source_mode=CaptureResearchSourceMode.FAKE_ADAPTER_TEST,
        capability_provenance=provenance,
        provider_ids=("fake_adapter_test",),
        approval_basis=None,
    )


def _source_target_slug(source_target: str) -> str:
    slug = "-".join(source_target.strip().lower().split())
    return slug or "unknown-target"


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