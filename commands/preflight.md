Run a quick quality check on the current changes. Does NOT commit or push — this is a read-only check.

Execute all steps, then present a summary.

## Step 1 — Build

Detect the project type and verify it builds:
- `pubspec.yaml` → `flutter analyze`
- `go.mod` → `go build ./...`
- `Pipfile` → `pipenv run python -m py_compile` on changed .py files
- `package.json` → `npm run build` (if build script exists)

## Step 2 — Test

Run the test suite:
- Flutter: `flutter test --concurrency=1`
- Go: `go test ./...`
- Python: `pipenv run pytest`
- Node: `npm test` (if test script exists)

## Step 3 — Quick Review

Review uncommitted changes (staged + unstaged) at medium effort:
- Correctness bugs and logic errors
- Obvious security issues
- Style consistency

## Step 4 — Report

Present results in a compact summary using tabulate with simple_grid format:

| Check    | Result | Details              |
|----------|--------|----------------------|
| Build    | PASS/FAIL | error summary if fail |
| Tests    | PASS/FAIL | N passed, N failed   |
| Review   | N findings | N critical, N warning |

If any critical issues found, list them with file:line references and suggested fixes.
