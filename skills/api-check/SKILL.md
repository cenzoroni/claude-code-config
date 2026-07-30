---
name: api-check
description: Use when hitting API errors like 403, 429, deprecated endpoints, or unexpected API responses. Validates endpoints against current docs and suggests fixes.
argument-hint: <paste the error or describe the API issue>
---

# API Check Skill

The user is hitting an API error. Diagnose and fix it:

1. **Identify the API and endpoint** from the error in `$ARGUMENTS` or from the codebase.
2. **Check the code** for the endpoint URL, parameters, and auth method being used.
3. **Common issues to check**:
   - Deprecated/legacy endpoints (e.g., `/api/v3/` → `/stable/` for FMP)
   - Rate limiting (429) — check if rate limiting or request spacing is needed
   - Auth errors (403) — verify API key handling and plan limits
   - Response format changes — compare expected vs actual response structure
4. **Fix the code**: Update endpoints, add rate limiting, or fix parsing as needed.
5. **Report**: Briefly explain what was wrong and what you changed.
