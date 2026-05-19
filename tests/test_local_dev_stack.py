from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_local_dev_compose_exposes_selected_provider_stack_only() -> None:
    compose = (ROOT / "docker-compose.local.yml").read_text(encoding="utf-8")

    assert "searxng:" in compose
    assert "searxng/searxng:latest" in compose
    assert "127.0.0.1:8080:8080" in compose
    assert "container_name" not in compose
    assert "crawl4ai:" in compose
    assert "unclecode/crawl4ai:basic-amd64" in compose
    assert "127.0.0.1:11235:11235" in compose
    assert "neo4j" not in compose.lower()
    assert "postgres" not in compose.lower()
    assert "9621" not in compose


def test_local_dev_searxng_config_enables_json_results() -> None:
    settings = (ROOT / "docker" / "searxng" / "settings.yml").read_text(
        encoding="utf-8"
    )

    assert "formats:" in settings
    assert "json" in settings
    assert "port: 8080" in settings


def test_local_dev_scripts_preserve_ariadne_runtime_contract() -> None:
    start_script = (ROOT / "scripts" / "start-local-dev.ps1").read_text(
        encoding="utf-8"
    )
    smoke_script = (ROOT / "scripts" / "smoke-local-dev.ps1").read_text(
        encoding="utf-8"
    )

    assert "docker compose -f docker-compose.local.yml up -d" in start_script
    assert "Invoke-CheckedCommand" in start_script
    assert "CRAWL4AI_BASE_URL = \"http://localhost:11235\"" in start_script
    assert "SEARXNG_BASE_URL = \"http://localhost:8080\"" in start_script
    assert "PORT = \"9622\"" in start_script
    assert "PORT=9621 is reserved" in start_script
    assert "uv run python app.py" in start_script
    assert "/api/capture-research/source-providers" in smoke_script
    assert "crawl4ai_local" in smoke_script
    assert "searxng_local" in smoke_script
    assert "approved = $true" in smoke_script