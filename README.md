# Ariadne Thread

Ariadne Thread is a capture command center for managing the full pursuit lifecycle from opportunity identification through award. The project is guided by Shipley capture discipline, deep modular architecture, local-first knowledge workflows, and an immersive dark cyberpunk user experience.

The product source of truth is [PRD.md](PRD.md). Phase 0 focuses on developer skills, architecture foundations, and the first local runtime slice of the command center.

## Phase 0 Priorities

- Bring in architecture, first-principles, skill-creation, and UI/UX developer skills.
- Vendor `ui-ux-pro-max` from `nextlevelbuilder/ui-ux-pro-max-skill`.
- Use Python 3.14+ as the main application language, managed with `uv` and `uvx`.
- Capture architecture recommendations before writing application code.
- Keep secrets out of the repository; use `.env.example` for the public configuration shape only.

## Run Locally

```powershell
uv sync
Copy-Item .env.example .env
uv run python app.py
```

The app reads `HOST`, `PORT`, `PUBLIC_APP_NAME`, `ARIADNE_ENV`, `ARIADNE_WORKSPACE`, and `ARIADNE_EVIDENCE_DIR` from `.env`, then starts the local FastAPI runtime. Open the URL printed at startup, usually `http://127.0.0.1:9621` unless your private `.env` sets another port.

With the virtual environment activated, `python app.py` also works.

## Development Defaults

- Python is the default language for backend, agents, orchestration, document processing, knowledge workflows, and platform tooling.
- TypeScript is reserved for the Next.js Command Center UI and frontend-adjacent tooling.
- Use `uv sync` to create/update the local `.venv/`, `uv add` for Python dependencies, and `uvx` for one-off Python CLIs.
- Keep live values in `.env`; commit only secret-free placeholders in `.env.example`.
