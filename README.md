# Ariadne Thread

Ariadne Thread is a capture command center for managing the full pursuit lifecycle from opportunity identification through award. The project is guided by Shipley capture discipline, deep modular architecture, local-first knowledge workflows, and an immersive dark cyberpunk user experience.

The product source of truth is [PRD.md](PRD.md). Phase 0, the first domain/storage epic, Quick Capture Knowledge Processing, Document Intake Command Surface, Federal Data MCP Foundation, SAM.gov Enrichment Profile, Capability Run Foundation, Knowledge Layer Foundation, Capture Research Enrichment, and the local-dev provider stack follow-on are complete; the next iteration should start with a `grill-with-docs` planning session before new product work begins.

## Current State

- Local FastAPI runtime starts from [app.py](app.py).
- The current Command Center shell ties together Opportunity, Quick Capture, Document Intake, Living Briefing Packet, Capture Action Plan, Capability Studio, Federal Data, Knowledge Context, Capture Research Enrichment, and review-gated demo threads.
- Current domain modules cover opportunities, evidence, quick capture knowledge processing, Document Intake, uploaded source material classification, packets, packet knowledge slots, action plans, runtime config, local model assist, capability discovery/runs, federal-data profiles, structured knowledge, next-action recommendations, and Capture Research Enrichment.
- Quick Capture turns rough notes, pasted text, and text/Markdown uploads into reviewable Capture Intelligence Drafts with Reference Wiki influences, polished trusted evidence candidates, per-piece review routes, promotions, traceability, and parser-required unsupported upload candidates.
- Document Intake persists source material records, creates generic Extraction Bundles, turns extracted signals into reviewable draft parts, promotes accepted source spans into Evidence Items, surfaces review-gated Action Plan/Packet/Risk Register/Call Plan candidates, generates one-way Knowledge Note Projections, and declares inert future parser/retrieval adapter hooks.
- Packet data elements are modeled as reusable strategic Packet Field Definitions with opportunity-specific Packet Field Answers and cross-opportunity context through Shared Knowledge Entities.
- Capability Studio remains advanced; capability management is not the default capture workflow.
- The next planning step is documented in [docs/architecture/next-grill-with-docs-session.md](docs/architecture/next-grill-with-docs-session.md).

## Run Locally

```powershell
uv sync
Copy-Item .env.example .env
uv run python app.py
```

The app reads `HOST`, `PORT`, `PUBLIC_APP_NAME`, `ARIADNE_ENV`, `ARIADNE_WORKSPACE`, `ARIADNE_EVIDENCE_DIR`, `ARIADNE_DOCUMENT_INTAKE_DIR`, and `ARIADNE_REFERENCE_WIKI_DIR` from `.env`, then starts the local FastAPI runtime. Open the URL printed at startup, usually `http://127.0.0.1:9622`. Port `9621` is reserved for Project Theseus.

With the virtual environment activated, `python app.py` also works.

## Local Dev Provider Stack

The selected local Capture Research providers can be started with Docker Compose, while the Ariadne app still runs through `uv` on the host:

```powershell
.\scripts\start-local-dev.ps1
```

That one command starts SearXNG on `http://localhost:8080`, Crawl4AI on `http://localhost:11235`, exports those base URLs for the app process, and starts Ariadne on `http://127.0.0.1:9622`. Use `-ProvidersOnly` when you only want the containers.

Validate the running stack with:

```powershell
.\scripts\smoke-local-dev.ps1
```

The smoke script checks Crawl4AI directly, verifies SearXNG JSON search results are enabled, and runs Ariadne's `crawl4ai_local` and `searxng_local` approved smoke-check endpoints. Stop the provider containers with `docker compose -f docker-compose.local.yml down`. Ollama remains optional/external through `OLLAMA_HOST` and is not required by this stack.

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
