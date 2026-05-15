from ariadne.config import RuntimeSettings
from ariadne.server import create_app


def test_runtime_settings_load_host_port_and_app_name_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "HOST=0.0.0.0\nPORT=9622\nPUBLIC_APP_NAME=Ariadne Local\n",
        encoding="utf-8",
    )

    settings = RuntimeSettings.from_env_file(env_file)

    assert settings.host == "0.0.0.0"
    assert settings.port == 9622
    assert settings.public_app_name == "Ariadne Local"
    assert settings.local_url == "http://127.0.0.1:9622"


def test_runtime_api_reports_configured_app_status() -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "HOST": "127.0.0.1",
            "PORT": "9622",
            "PUBLIC_APP_NAME": "Ariadne Local",
            "ARIADNE_WORKSPACE": "capture-dev",
        }
    )
    app = create_app(settings)

    from fastapi.testclient import TestClient

    response = TestClient(app).get("/api/runtime")

    assert response.status_code == 200
    assert response.json() == {
        "app_name": "Ariadne Local",
        "environment": "development",
        "workspace": "capture-dev",
        "host": "127.0.0.1",
        "port": 9622,
        "local_url": "http://127.0.0.1:9622",
        "status": "online",
    }


def test_root_serves_runtime_status_page() -> None:
    settings = RuntimeSettings.from_mapping(
        {
            "PORT": "9622",
            "PUBLIC_APP_NAME": "Ariadne Local",
        }
    )

    from fastapi.testclient import TestClient

    response = TestClient(create_app(settings)).get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Ariadne Local" in response.text
    assert "Runtime online" in response.text
    assert "http://127.0.0.1:9622" in response.text


def test_packet_review_page_serves_living_briefing_packet_skeleton() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/packets/review")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Living Briefing Packet" in response.text
    assert "AFLCMC recompete support" in response.text
    assert "Briefing View" in response.text
    assert "Coverage View" in response.text
    assert "Supported" in response.text
    assert "Partially Supported" in response.text


def test_packet_review_api_exposes_briefing_and_coverage_views() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app())

    briefing_response = client.get("/api/packets/review/briefing")
    coverage_response = client.get("/api/packets/review/coverage")

    assert briefing_response.status_code == 200
    assert briefing_response.json()["opportunity_name"] == "AFLCMC recompete support"
    assert briefing_response.json()["readiness"] == "draft_ready"
    assert len(briefing_response.json()["sections"]) == 8

    assert coverage_response.status_code == 200
    customer_context = next(
        section
        for section in coverage_response.json()["sections"]
        if section["section"] == "customer_context"
    )
    assert customer_context["evidence_status"] == "partial"
    assert customer_context["evidence_ids"] == ["ev_customer_call"]
    assert customer_context["gap_summary"] == (
        "Need validated customer pain and decision-maker map."
    )


def test_app_py_builds_runtime_app_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "HOST=127.0.0.1\nPORT=9622\nPUBLIC_APP_NAME=Ariadne App\n",
        encoding="utf-8",
    )

    import importlib.util
    from pathlib import Path

    from fastapi.testclient import TestClient

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    spec = importlib.util.spec_from_file_location("ariadne_app_entrypoint", app_path)
    assert spec is not None
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)

    response = TestClient(app_module.build_app(env_file)).get("/api/runtime")

    assert response.status_code == 200
    assert response.json()["app_name"] == "Ariadne App"
    assert response.json()["port"] == 9622