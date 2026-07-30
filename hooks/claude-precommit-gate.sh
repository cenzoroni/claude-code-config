#!/bin/bash
# Pre-commit quality gate for Claude Code
# Called as a PreToolUse hook on Bash. Reads JSON from stdin, runs build + tests,
# blocks commit on failure (exit 2).
#
# NOTE: The settings.json `if: "Bash(git commit *)"` filter fails OPEN on complex
# compound commands (multiline loops, ${param} expansions), so this script must
# re-verify the command is actually a git commit before doing any work.

set -uo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Source-of-truth gate: only act on real `git commit` invocations.
if ! echo "$COMMAND" | grep -Eq '(^|[;&|]|[[:space:]])git[[:space:]]+commit([[:space:]]|$)'; then
    exit 0
fi

[ -n "$CWD" ] && cd "$CWD"

ERRORS=""

if [ -f "pubspec.yaml" ]; then
    # Flutter — analyze only (full test suite too slow for a commit gate).
    # Block on errors only; warnings/infos are lint debt, not a commit blocker.
    OUTPUT=$(flutter analyze --no-pub --no-fatal-infos --no-fatal-warnings 2>&1) || {
        ERRORS+="flutter analyze found errors:\n${OUTPUT}\n\n"
    }
elif [ -f "go.mod" ]; then
    OUTPUT=$(go build ./... 2>&1) || {
        ERRORS+="go build failed:\n${OUTPUT}\n\n"
    }
    OUTPUT=$(go test ./... 2>&1) || {
        ERRORS+="go test failed:\n${OUTPUT}\n\n"
    }
elif [ -f "Pipfile" ]; then
    CHANGED_PY=$(git diff --cached --name-only --diff-filter=ACM -- '*.py' 2>/dev/null || true)
    if [ -n "$CHANGED_PY" ]; then
        for f in $CHANGED_PY; do
            OUTPUT=$(pipenv run python -m py_compile "$f" 2>&1) || {
                ERRORS+="Syntax error in $f:\n${OUTPUT}\n\n"
            }
        done
    fi
    if [ -d "tests" ] || [ -f "pytest.ini" ] || [ -f "setup.cfg" ] || [ -f "pyproject.toml" ]; then
        OUTPUT=$(pipenv run pytest --tb=short -q 2>&1) || {
            ERRORS+="pytest failed:\n${OUTPUT}\n\n"
        }
    fi
elif [ -f "package.json" ]; then
    if [ -f "tsconfig.json" ] && command -v npx &>/dev/null; then
        OUTPUT=$(npx tsc --noEmit 2>&1) || {
            ERRORS+="TypeScript build failed:\n${OUTPUT}\n\n"
        }
    fi
    if jq -e '.scripts.test' package.json &>/dev/null 2>&1; then
        OUTPUT=$(npm test 2>&1) || {
            ERRORS+="npm test failed:\n${OUTPUT}\n\n"
        }
    fi
fi

if [ -n "$ERRORS" ]; then
    echo -e "PRE-COMMIT GATE BLOCKED\n\n${ERRORS}Fix the issues above before committing." >&2
    exit 2
fi

exit 0
