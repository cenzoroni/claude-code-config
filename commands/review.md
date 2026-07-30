Review the following code changes for issues.

Target: $ARGUMENTS

If no specific files are mentioned, review the current uncommitted changes (use git diff and git diff --staged).

Check for:
1. **Correctness**: Logic errors, off-by-ones, nil dereferences, race conditions
2. **Security**: Injection, XSS, auth bypass, secrets exposure, OWASP top 10
3. **Performance**: N+1 queries, unnecessary allocations, missing indexes, hot loops
4. **Error handling**: Swallowed errors, poor error messages, missing cleanup
5. **Style**: Naming, structure, consistency with the rest of the codebase
6. **Missing tests**: What should be tested but isn't

For each issue found, report:
- **Severity**: critical / warning / nit
- **Location**: file:line
- **Issue**: What's wrong
- **Fix**: Suggested fix (code snippet if helpful)

Be direct. Don't pad with praise. If the code is clean, say so briefly and move on.
