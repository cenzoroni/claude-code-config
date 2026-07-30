Ship the current changes through a full quality pipeline.

Execute these steps in order. Stop and report if any step fails.

## Step 1 — Build

Detect the project type and run the build:
- `pubspec.yaml` → `flutter analyze`
- `go.mod` → `go build ./...`
- `Pipfile` → `pipenv run python -m py_compile` on changed .py files
- `package.json` → `npm run build` (if build script exists)

If no recognized project type, skip this step.

## Step 2 — Test

Run the test suite:
- Flutter: `flutter test --concurrency=1`
- Go: `go test ./...`
- Python: `pipenv run pytest`
- Node: `npm test` (if test script exists)

If no tests exist, note this and continue.

## Step 3 — Code Review

Review all uncommitted changes (staged + unstaged) at high effort:
- Correctness: logic errors, off-by-ones, nil dereferences, race conditions
- Performance: N+1 queries, hot loops, unnecessary allocations
- Style: naming, structure, consistency with the rest of the codebase
- Missing tests for new code paths

Report findings with severity (critical/warning/nit) and file:line locations.

## Step 4 — Security Review

Review all uncommitted changes for security issues:
- Injection (SQL, command, XSS, path traversal)
- Hardcoded secrets or credentials
- Auth/authz gaps
- Data exposure in logs or responses
- Insecure dependencies

Report findings with severity and remediation suggestions.

## Step 5 — Format

Run the appropriate formatter on all changed files:
- `.dart` files → `dart format`
- `.go` files → `gofmt -w`
- `.py` files → `black` (if available)

## Step 6 — Summary & Confirm

Present a summary table:
- Build: pass/fail
- Tests: pass/fail (with count)
- Code Review: finding counts by severity
- Security: finding counts by severity
- Files changed (list)

If there are critical findings from review or security, fix them before proceeding. Then ask the user to confirm before committing.

## Step 7 — Commit & PR

After user confirms:
1. Stage all relevant changed files (not .env or credentials)
2. Create a commit with a descriptive message summarizing the changes
3. Push to remote with `-u` flag
4. Create a PR using `gh pr create` with a summary title and body including:
   - What changed and why
   - Review findings that were addressed
   - Test coverage notes

If $ARGUMENTS contains "no-pr", skip PR creation and just commit + push.
If $ARGUMENTS contains "commit-only", just commit without push or PR.
