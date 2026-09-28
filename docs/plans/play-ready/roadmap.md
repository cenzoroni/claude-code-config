# /play-ready — Play Store Preparation Skill

## Status: Core complete, ready for use

## Where things live
- **Command:** `commands/play-ready.md`
- **Templates, scripts, ProGuard base:** `play-ready/` in this repo
- **Each app's config:** `play-store.yaml` at the root of that app's own repo
- **Personal details:** `~/.claude/play-ready.yaml` (developer profiles, policy
  hosting, keystore identity). A dummy sample is in
  `config/play-ready.sample.yaml`.
- The old private `play-store-templates` repo is archived.

## What's built

### Templates (`play-ready/templates/`)
- [x] `privacy-policy.html.j2`, `data-deletion.html.j2`
- [x] `data-safety-answers.md.j2` — Google Data Safety form mapping
- [x] `content-rating-answers.md.j2` — IARC questionnaire mapping
- [x] `store-listing-guide.md.j2` — description, screenshots, assets, policy URLs
- [x] `play-console-walkthrough.md.j2` — step-by-step Play Console guide

### Scripts (`play-ready/scripts/`)
- [x] `analyze.py` — Flutter project analyzer; drafts `play-store.yaml` and a readiness checklist
- [x] `render.py` — renders templates (`--template`, `--all`, `--hosted`)
- [x] `generate_assets.py` — icon, feature graphic, screenshots
- [x] `user_config.py` — loads the personal config: developer profiles, policy hosting
- [x] `Pipfile` — deps: pyyaml, jinja2, tabulate, pillow

### Other
- [x] `play-ready/proguard/flutter.pro` — shared ProGuard base rules
- [x] Personal details kept out of app configs; an app picks a `developer_profile`
- [x] Policy hosting: `render.py --hosted` publishes privacy and data-deletion
      pages into a site repo under `<base_url>/<app>/privacy` and `/delete-data`
- [x] Apps without Firebase render (previously crashed)

## Known issues
- [ ] `Pipfile` pins only `python_version = "3"`, so pipenv warns on 3.14.

## App readiness
Tracked in each app's own repo (`docs/plans/play-store/`), not here.

## Original plan
See `completed/plan.md` for the full design document.
