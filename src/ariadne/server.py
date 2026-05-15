from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ariadne.capabilities import CapabilityCatalog, discover_local_capability_catalog
from ariadne.command_center import render_command_center_shell
from ariadne.config import RuntimeSettings
from ariadne.packet_knowledge import PacketFieldReview, build_demo_packet_field_review
from ariadne.packet_review import (
    build_demo_packet_briefing_view,
    build_demo_packet_coverage_view,
    render_demo_packet_review_shell,
)
from ariadne.packets import (
    BriefingView,
    CoverageView,
)


def create_app(settings: RuntimeSettings | None = None) -> FastAPI:
    runtime_settings = settings or RuntimeSettings.from_env_file()
    app = FastAPI(title=runtime_settings.public_app_name)

    @app.get("/api/runtime")
    def runtime_status() -> dict[str, object]:
        return {
            "app_name": runtime_settings.public_app_name,
            "environment": runtime_settings.ariadne_env,
            "workspace": runtime_settings.ariadne_workspace,
            "host": runtime_settings.host,
            "port": runtime_settings.port,
            "local_url": runtime_settings.local_url,
            "status": "online",
        }

    @app.get("/", response_class=HTMLResponse)
    def command_center_status() -> str:
        return render_command_center_shell(runtime_settings)

    @app.get("/packets/review", response_class=HTMLResponse)
    def packet_review(stage: str = "MS2", slide: int = 4) -> str:
        return render_demo_packet_review_shell(stage=stage, slide=slide)

    @app.get("/api/packets/review/briefing")
    def packet_review_briefing() -> BriefingView:
        return build_demo_packet_briefing_view()

    @app.get("/api/packets/review/coverage")
    def packet_review_coverage() -> CoverageView:
        return build_demo_packet_coverage_view()

    @app.get("/api/packets/review/knowledge-slots")
    def packet_review_knowledge_slots() -> PacketFieldReview:
        return build_demo_packet_field_review()

    @app.get("/api/capabilities/catalog")
    def capability_catalog() -> CapabilityCatalog:
        return discover_local_capability_catalog(Path.cwd())

    return app
