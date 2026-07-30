---
name: run
description: Use when the user wants to run their project, app, or script. Detects the project type and runs the appropriate command.
argument-hint: <optional: specific file or target to run>
---

# Run Skill

Detect the project type from the current directory and run the appropriate command.

**Detection rules:**
- `pubspec.yaml` present → Flutter project → `flutter run`
- `go.mod` present → Go project → `go run .` (or `go build -o <name> && ./<name>` if binary preferred)
- `Pipfile` present → Python with pipenv → `pipenv run python3 $ARGUMENTS`
- `requirements.txt` present → Python → `python3 $ARGUMENTS`
- `*.py` file specified → `python3 $ARGUMENTS`
- `package.json` present → Node → `npm start` or `npx $ARGUMENTS`

If `$ARGUMENTS` specifies a file, run that file with the appropriate runtime.

If the environment isn't set up (missing dependencies, venv not created), set it up first silently, then run.
