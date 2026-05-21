from pathlib import Path

from ariadne.config import RuntimeSettings


def test_artifact_assembly_dir_uses_configured_local_store_path() -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_ARTIFACT_ASSEMBLY_DIR": ".ariadne/artifact-assembly-test"}
    )

    assert settings.ariadne_artifact_assembly_dir == Path(
        ".ariadne/artifact-assembly-test"
    )


def test_obsidian_vault_dir_defaults_to_canonical_llm_wiki_path() -> None:
    default_settings = RuntimeSettings.from_mapping({})
    configured_settings = RuntimeSettings.from_mapping(
        {"ARIADNE_OBSIDIAN_VAULT_DIR": "private/ariadne-vault"}
    )

    assert default_settings.ariadne_obsidian_vault_dir == Path(
        "knowledge/ariadnes-thread"
    )
    assert configured_settings.ariadne_obsidian_vault_dir == Path(
        "private/ariadne-vault"
    )


def test_opportunities_dir_uses_configured_local_store_path() -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_OPPORTUNITIES_DIR": ".ariadne/opportunities-test"}
    )

    assert settings.ariadne_opportunities_dir == Path(".ariadne/opportunities-test")


def test_packet_field_answers_dir_uses_configured_local_store_path() -> None:
    settings = RuntimeSettings.from_mapping(
        {"ARIADNE_PACKET_FIELD_ANSWERS_DIR": ".ariadne/packet-answers-test"}
    )

    assert settings.ariadne_packet_field_answers_dir == Path(
        ".ariadne/packet-answers-test"
    )


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