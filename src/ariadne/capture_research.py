from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
import json
from pathlib import Path
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from urllib.parse import urlparse
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
    source_collection_records: tuple[WebSourceCollectionRecord, ...] = ()
    source_findings: tuple[SourceFinding, ...] = ()
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


def _read_json_response(request: Request) -> dict[str, object]:
    try:
        with urlopen(request, timeout=60) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ValueError(f"source provider request failed: {error.code} {detail}") from error
    except URLError as error:
        raise ValueError(f"source provider request failed: {error.reason}") from error
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