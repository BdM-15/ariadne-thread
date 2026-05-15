---
name: cli-anything
description: Use when building, refining, testing, or validating a CLI-Anything harness for an Ariadne internal capability, GUI application, external tool, or source repository. Use when a repeatable workflow should become an agent-native Python CLI with JSON output instead of a complicated UI or bespoke tool integration.
---

# CLI-Anything Harness Builder

Use this skill when the user wants an agent to act like the `CLI-Anything` builder.

Before building, refining, testing, or validating a harness, read `resources/cli-anything-plugin/HARNESS.md`. That file is the full methodology source of truth. If it is not available, follow the condensed rules below.

## Ariadne Use

Use CLI-first harnesses for Ariadne capabilities that are repeatable, batchable, tool-facing, or agent-facing:

- research/data pulls such as SAM.gov, USAspending, BLS, and api.data.gov workflows
- document conversion, artifact export, and renderer pipelines
- Shipley reference extraction, refresh, validation, and future indexing jobs
- knowledge ingestion and reindexing commands once architecture chooses a knowledge engine
- developer/admin validation commands
- wrappers around real external software, MCP tools, or APIs that benefit from deterministic JSON output

Do not turn strategy review, decision-making, visual sensemaking, or high-context human workflows into CLI-only surfaces. Those belong in the Command Center UI, with CLI harnesses behind them where useful.

## Inputs

Accept either:

- A local source path such as `./gimp` or `/path/to/software`
- A GitHub repository URL

Derive the software name from the local directory name after cloning if needed.

## Modes

### Build

Use when the user wants a new harness.

Produce this structure:

```text
<software>/
`-- agent-harness/
    |-- <SOFTWARE>.md
    |-- setup.py
    `-- cli_anything/
        `-- <software>/
            |-- README.md
            |-- __init__.py
            |-- __main__.py
            |-- <software>_cli.py
            |-- core/
            |-- utils/
            `-- tests/
```

Implement a stateful Click CLI with:

- one-shot subcommands
- REPL mode as the default when no subcommand is given
- `--json` machine-readable output
- session state with undo/redo where the target software supports it

### Refine

Use when the harness already exists.

First inventory current commands and tests, then do gap analysis against the target software. Prefer:

- high-impact missing features
- easy wrappers around existing backend APIs or CLIs
- additions that compose well with existing commands

Do not remove existing commands unless the user explicitly asks for a breaking change.

### Test

Plan tests before writing them. Keep both:

- `test_core.py` for unit coverage
- `test_full_e2e.py` for workflow and backend validation

When possible, test the installed command via subprocess using `cli-anything-<software>` rather than only module imports.

### Validate

Check that the harness:

- uses the `cli_anything.<software>` namespace package layout
- has an installable `setup.py` entry point
- supports JSON output
- has a REPL default path
- documents usage and tests

## Backend Rules

Prefer the real software backend over reimplementation. Wrap the actual executable or scripting interface in `utils/<software>_backend.py` when possible. Use synthetic reimplementation only when the project explicitly requires it or no viable native backend exists.

## Packaging Rules

- Use `find_namespace_packages(include=["cli_anything.*"])`
- Keep `cli_anything/` as a namespace package without a top-level `__init__.py`
- Expose `cli-anything-<software>` through `console_scripts`

## Workflow

1. Acquire the source tree locally.
2. Analyze architecture, data model, existing CLIs, and GUI-to-API mappings.
3. Design command groups and state model.
4. Implement the harness.
5. Write `TEST.md`, then tests, then run them.
6. Update README usage docs.
7. Verify local installation with `uv pip install -e .`

## Output Expectations

When reporting progress or final results, include:

- target software and source path
- files added or changed
- validation commands run
- open risks or backend limitations
