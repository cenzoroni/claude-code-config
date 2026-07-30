---
name: seed
description: Run data seeding scripts with proper environment setup. Handles dependency installation automatically.
disable-model-invocation: true
argument-hint: <path to seed script>
---

# Seed Skill

Run a data seeding script with automatic environment setup:

1. **Identify the script** from `$ARGUMENTS`.
2. **Set up environment** if needed:
   - If `Pipfile` exists in the project root: `pipenv install` then `pipenv run python3 <script>`
   - If `requirements.txt` exists: create venv if missing, install deps, then run
   - If Go project: `go run <script>`
3. **Run the script** and stream output.
4. **Report results**: Show counts (uploaded, skipped, failed) if available.

Handle errors gracefully — if a dependency is missing, install it and retry.
