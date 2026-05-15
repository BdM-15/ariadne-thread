# Ariadne Thread

Ariadne Thread is a capture command center for managing the full pursuit lifecycle from opportunity identification through award. The project is guided by Shipley capture discipline, deep modular architecture, local-first knowledge workflows, and an immersive dark cyberpunk user experience.

The product source of truth is [PRD.md](PRD.md). Phase 0 and the first domain/storage epic are complete; the next iteration should start with a `grill-with-docs` planning session before new product work begins.

## Current State

- Local FastAPI runtime starts from [app.py](app.py).
- First Command Center shell ties together Opportunity, Quick Capture, Living Briefing Packet, Capture Action Plan, and read-only Capability Catalog surfaces.
- First-slice domain modules cover opportunities, evidence, quick capture, packets, packet knowledge slots, action plans, runtime config, and local capability discovery.
- Packet data elements are modeled as reusable strategic Packet Field Definitions with opportunity-specific Packet Field Answers and cross-opportunity context through Shared Knowledge Entities.
- Capability Studio remains advanced/read-only in this slice; capability management is not the default capture workflow.

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

## Validate

```powershell
uv run ruff check src tests
uv run pytest -q
```
