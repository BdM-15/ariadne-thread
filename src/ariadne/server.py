from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ariadne.config import RuntimeSettings
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
        return _render_status_shell(runtime_settings)

    @app.get("/packets/review", response_class=HTMLResponse)
    def packet_review(stage: str = "MS2", slide: int = 4) -> str:
        return render_demo_packet_review_shell(stage=stage, slide=slide)

    @app.get("/api/packets/review/briefing")
    def packet_review_briefing() -> BriefingView:
        return build_demo_packet_briefing_view()

    @app.get("/api/packets/review/coverage")
    def packet_review_coverage() -> CoverageView:
        return build_demo_packet_coverage_view()

    return app


def _render_status_shell(settings: RuntimeSettings) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{settings.public_app_name}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #08090d;
      --panel: #10131a;
      --edge: #273142;
      --text: #edf7ff;
      --muted: #9fb4c8;
      --cyan: #33e7ff;
      --magenta: #ff4fd8;
      --green: #7dffa7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100dvh;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 48px 0;
    }}
    header {{
      border-bottom: 1px solid var(--edge);
      padding-bottom: 24px;
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: clamp(2rem, 5vw, 4.5rem);
      line-height: 1;
      letter-spacing: 0;
    }}
    p {{ margin: 0; color: var(--muted); line-height: 1.6; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .tile {{
      border: 1px solid var(--edge);
      border-radius: 8px;
      background: var(--panel);
      padding: 16px;
      min-height: 112px;
    }}
    .label {{ color: var(--muted); font-size: 0.85rem; }}
    .value {{ margin-top: 10px; font-size: 1.1rem; font-weight: 700; }}
    .online {{ color: var(--green); }}
    .cyan {{ color: var(--cyan); }}
    .magenta {{ color: var(--magenta); }}
  </style>
</head>
<body>
  <main>
    <header>
      <p class=\"cyan\">Runtime online</p>
      <h1>{settings.public_app_name}</h1>
      <p>Command Center shell not built yet. Runtime entrypoint, env loading, and API surface are active.</p>
    </header>
    <section class=\"grid\" aria-label=\"Runtime status\">
      <div class=\"tile\"><div class=\"label\">Status</div><div class=\"value online\">online</div></div>
      <div class=\"tile\"><div class=\"label\">Workspace</div><div class=\"value\">{settings.ariadne_workspace}</div></div>
      <div class=\"tile\"><div class=\"label\">Environment</div><div class=\"value\">{settings.ariadne_env}</div></div>
      <div class=\"tile\"><div class=\"label\">Local URL</div><div class=\"value magenta\">{settings.local_url}</div></div>
    </section>
    <p class=\"review-link\"><a href=\"/packets/review\">Open Living Briefing Packet review</a></p>
  </main>
</body>
</html>"""
