# Upstream Vendor Notes

| Field | Value |
|-------|-------|
| Upstream repo | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| Upstream commit | b7e3af80f6e331f6fb456667b82b12cade7c9d35 |
| Source skill | `.claude/skills/ui-ux-pro-max/` |
| Vendored path | `.github/skills/ui-ux-pro-max/` |
| License | MIT |

## Local Adaptation

- Upstream stores `data` and `scripts` as symlinks to `src/ui-ux-pro-max/`; Ariadne vendors those targets as real directories so the skill works standalone on Windows.
- Upstream command examples reference `skills/ui-ux-pro-max/scripts/search.py`; Ariadne patches them to `.github/skills/ui-ux-pro-max/scripts/search.py` for VS Code workspace layout.

Re-vendor by cloning upstream, copying `.claude/skills/ui-ux-pro-max/SKILL.md`, copying `src/ui-ux-pro-max/data` and `src/ui-ux-pro-max/scripts`, then reapplying the command-path patch above.