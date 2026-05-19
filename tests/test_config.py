from ariadne.config import RuntimeSettings


def test_capture_research_source_provider_env_exposes_configured_connectors() -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "CRAWL4AI_BASE_URL": "http://localhost:11235",
            "SEARXNG_BASE_URL": "http://localhost:8080",
            "SERPAPI_API_KEY": "serpapi-secret",
            "OLOSTEP_API_KEY": "olostep-secret",
            "FIRECRAWL_API_KEY": "firecrawl-secret",
        }
    )

    assert settings.capture_research_source_env == {
        "CRAWL4AI_BASE_URL": "http://localhost:11235",
        "SEARXNG_BASE_URL": "http://localhost:8080",
        "SERPAPI_API_KEY": "serpapi-secret",
        "OLOSTEP_API_KEY": "olostep-secret",
        "FIRECRAWL_API_KEY": "firecrawl-secret",
    }
    dumped = settings.model_dump_json()
    assert "serpapi-secret" not in dumped
    assert "olostep-secret" not in dumped
    assert "firecrawl-secret" not in dumped