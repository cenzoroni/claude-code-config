# User Preferences

## Agent Usage
- Always parallelize work by sending independent tasks to multiple agents simultaneously.
- Use the lowest cost model/agent appropriate for the task (prefer haiku for quick, straightforward tasks; use sonnet for moderate complexity; reserve opus for tasks requiring deep reasoning).

## Communication
- Be concise. Don't explain unless asked.

## Environment
- Primary languages: Flutter/Dart, Go, Python
- macOS development
- Flutter apps tested with `--concurrency=1` to avoid segfaults
- Python: use pipenv for dependency management (avoid raw venv setup)
- Go: build with `go build` before running

## Debugging
- When I paste logs/errors, diagnose and fix immediately — don't ask clarifying questions unless truly ambiguous.
- Prefer minimal, targeted fixes over broad refactors when debugging.

## Secrets
- Never hardcode API keys. Use .env files or environment variables.

## Plans
- **Plans live in the project's own repo** at `docs/plans/`, so a plan and the
  code it describes change in the same commit (a roadmap saying "M5 next" moves
  in the commit that finishes M5).
- Master plan is `roadmap.md` (or `plan.md` for single-plan projects)
- Sub-plans and supporting artifacts live alongside the master plan
- Completed sub-plans go in `docs/plans/completed/`
- Canceled sub-plans go in `docs/plans/canceled/`
- Plans should be detailed enough to execute without this conversation as context
- **No repo yet? Create one first** (`git init`, then a private GitHub repo)
  before writing the plan. Every project gets a repo from day one.
- **Decisions go in ADRs** at `docs/adr/NNNN-short-title.md` (Context →
  Decision → Consequences), indexed in `docs/adr/README.md`. Plans link to ADRs
  instead of repeating the reasoning. Never rewrite an accepted ADR; supersede
  it with a new one.
- **Tasks and known problems go in `docs/plans/issues.md`** (Open / Closed
  checklists), not GitHub Issues for now. Tick items off in the commit that
  fixes them.
- Search plans across projects: `rg <pattern> -g 'docs/plans/**' ~/repos`
- The old `~/plans` repo is retired; don't add to it.

### Naming
- Flutter repos (`groovy_baby`, `top_runner`, `gofish_kotlin`) keep
  underscores: the directory matches `name:` in `pubspec.yaml`, and a Dart
  package name must be a valid identifier. New non-Flutter projects use
  hyphens; don't rename existing repos just to match.
- **Before renaming any repo, check what pins its name.** Deploy auth commonly
  does: `trailplan` had its name in a Workload Identity condition *and* a service
  account binding, and renaming without widening both first breaks deploys.
  Widen to accept old and new, rename, verify a deploy, then narrow.

## Scripts
- Store standalone utility scripts in `~/scripts/` with unique descriptive names
- Use a prefix to group related scripts (e.g. `finetune-`, `stock-`, `gofish-`)
- Reference script names in the relevant plan so they're discoverable

## Data
- Store datasets in `~/data/<unique-dataset-name>/`
- Subfolder names should describe the dataset contents, not the project
- Current datasets: `finance-stock-screener/`, `fishing-synthetic/`, `fishing-regulations/`, `training-final/`

## Tables
- Always render CLI tables using `tabulate` with `tablefmt="simple_grid"` and right-aligned numeric columns
- For multi-group tables (e.g. per-project breakdowns), print each group as a separate labeled table with a header row, followed by a grand total line
- Never use rich, markdown tables, or raw unicode box-drawing for CLI table output

## SDLC Workflow
- `/feature <desc>` — Full pipeline: spec → architect → plan → implement → test → review → ship
- `/ship` — Quality pipeline: build → test → review → security → format → commit → PR
- `/preflight` — Quick check: build → test → review summary (no commit)
- `/code-review <effort>` — Review at effort level: low / medium / high / max / ultra
- `/security-review` — Security-focused review (OWASP, secrets, auth)
- `/verify` — Run the app and verify changes work in practice
- `/simplify` — Review changed code for reuse/efficiency, apply fixes

## Git
- Never auto-commit. Only commit when explicitly asked.
- When asked to "commit and push", do both in sequence without extra confirmation on the push.
