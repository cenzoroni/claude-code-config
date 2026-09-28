# /play-ready — Play Store Preparation Skill

## Status: Core complete, ready for use

## Repo
- Templates and scripts: `~/templates/play-store/` (a separate private repo)
- Skill: `~/.claude/commands/play-ready.md`

## What's built

### Shared templates (`~/templates/play-store/templates/`)
- [x] `privacy-policy.html.j2` — consolidated from two existing apps
- [x] `data-deletion.html.j2` — consolidated from an existing app
- [x] `data-safety-answers.md.j2` — Google Data Safety form mapping
- [x] `content-rating-answers.md.j2` — IARC questionnaire mapping
- [x] `store-listing-guide.md.j2` — description, screenshots, assets
- [x] `play-console-walkthrough.md.j2` — step-by-step Play Console guide

### App configs (`~/templates/play-store/config/`)
- [x] One YAML per app, fully populated for two apps

### Tooling (`~/templates/play-store/scripts/`)
- [x] `render.py` — Jinja2 renderer (`--config`, `--template`/`--all`, `--output`)
- [x] `analyze.py` — Flutter project analyzer + readiness checklist
- [x] `Pipfile` — deps: pyyaml, jinja2, tabulate

### Other
- [x] `proguard/flutter.pro` — shared ProGuard base rules
- [x] Claude Code skill at `~/.claude/commands/play-ready.md`

### Rendered output (already generated)
- [x] Generated for two apps, into each app repo's `docs/plans/play-store/`

## App readiness
Tracked in each app's own repo (`docs/plans/play-store/`), not here.

## Original plan
See `completed/plan.md` for the full design document.
