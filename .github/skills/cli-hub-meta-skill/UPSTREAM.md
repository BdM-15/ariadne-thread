# Upstream

- Repository: https://github.com/HKUDS/CLI-Anything
- Commit: `2bb59aa4479eb50f3a115f4b5dd29827b60bfe03`
- Source path: `skills/cli-hub-meta-skill/`
- Vendored path: `.github/skills/cli-hub-meta-skill/`
- License: Apache-2.0, copied from upstream `LICENSE`

## Adaptations

- Vendored only the CLI-Hub meta-skill, not the full CLI-Anything monorepo.
- Replaced `pip install cli-anything-hub` examples with `uv tool install cli-anything-hub` to match Ariadne's Python tooling rules.
- Demoted this skill to optional live-catalog discovery; Ariadne internal harness building uses `.github/skills/cli-anything/`.
