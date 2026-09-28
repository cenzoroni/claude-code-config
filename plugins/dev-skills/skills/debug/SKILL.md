---
name: debug
description: Use when the user pastes error logs, stack traces, or crash output. Diagnose the root cause and apply a targeted fix.
argument-hint: <paste error output or describe the issue>
---

# Debug Skill

The user has provided error output or described a bug. Follow these steps:

1. **Parse the error**: Identify the file, line number, error type, and root cause from the pasted output in `$ARGUMENTS`.
2. **Read the relevant source files**: Don't guess — read the actual code at the referenced locations.
3. **Diagnose**: Identify the root cause. Consider recent changes that may have introduced the issue.
4. **Fix**: Apply a minimal, targeted fix. Do NOT refactor surrounding code or add unrelated improvements.
5. **Verify**: If there are tests, run the relevant ones. If it's a runtime error, explain what changed and why the fix works.

Keep explanations brief — focus on what was wrong and what you changed.
