# Upstream

- Repository: https://github.com/HKUDS/CLI-Anything
- Commit: `2bb59aa4479eb50f3a115f4b5dd29827b60bfe03`
- Primary skill source path: `codex-skill/`
- Methodology resource source path: `cli-anything-plugin/`
- Vendored path: `.github/skills/cli-anything/`
- License: Apache-2.0, copied from upstream `LICENSE`

## Adaptations

- Vendored the upstream `codex-skill` as the VS Code workspace skill `cli-anything`.
- Bundled selected `cli-anything-plugin` methodology resources under `resources/cli-anything-plugin/` so the full HARNESS playbook is available without vendoring the full CLI-Anything monorepo.
- Updated skill language for Ariadne internal CLI-first architecture decisions, not only GUI app harness generation.
- Replaced Python installation examples with `uv`/`uv pip`/`uv tool` forms to match Ariadne's tooling rules.