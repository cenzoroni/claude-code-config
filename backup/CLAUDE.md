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
- Store all project plans in `~/plans/<unique-project-name>/plan.md`
- Supporting artifacts (diagrams, samples) go in the same subfolder
- Plans should be detailed enough to execute without this conversation as context

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
