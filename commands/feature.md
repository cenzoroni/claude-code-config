Execute a full SDLC pipeline for the following feature. This is a guided, phased pipeline — present results at each gate and wait for user confirmation before proceeding.

Feature: $ARGUMENTS

---

## Phase 1 — Specification

Generate a structured spec:
1. Read CLAUDE.md and relevant source files for project context
2. Produce:
   - **Summary**: One-paragraph description
   - **Requirements**: Numbered, specific, implementable
   - **Acceptance Criteria**: Testable criteria per requirement
   - **Edge Cases**: Potential edge cases and handling
   - **Out of Scope**: What this does NOT include
   - **Dependencies**: External services, libraries, or existing code needed

Present the spec. Ask the user: approve, request changes, or skip to next phase.

## Phase 2 — Architecture

Design the technical approach based on the approved spec:
1. Analyze the spec against the existing codebase architecture
2. Produce:
   - **Overview**: High-level approach (2-3 sentences)
   - **Files to Modify**: Each file with summary of changes needed
   - **New Files**: Files to create with purpose and interfaces
   - **Data Flow**: How data moves through the system
   - **API Changes**: New or modified endpoints/interfaces
   - **Risks & Tradeoffs**: Technical risks and alternatives considered

Present the architecture. Ask the user: approve, request changes, or skip.

## Phase 3 — Plan

Save the approved spec and architecture as a persistent plan:
1. Determine project name from the current directory name or git remote
2. Create `~/plans/<project-name>/plan.md` with both spec and architecture sections
3. Confirm the plan is saved and report the path

## Phase 4 — Implementation

Execute the plan:
1. Read the saved plan for reference
2. Implement changes following the architecture design
3. Delegate to sub-agents for parallel work on independent files/modules when beneficial
4. Follow all project conventions from CLAUDE.md
5. Build to verify compilation after implementation

Report what was implemented, files changed, and files created.

## Phase 5 — Testing

Write and run tests:
1. Read existing tests to understand the framework and patterns
2. Write tests covering: happy path, edge cases, error cases
3. Follow existing test naming and file conventions
4. Run the full test suite (Flutter: `--concurrency=1`)
5. Report results: passed, failed, coverage if available

If tests fail, fix the issues before proceeding.

## Phase 6 — Review

Run code review and security review in parallel:

**Code Review** (high effort):
- Correctness, performance, style, missing tests

**Security Review**:
- OWASP top 10, secrets, auth issues, data exposure

Present combined findings with severity and file:line locations. If critical issues exist, fix them and re-run the review.

## Phase 7 — Ship

Execute the ship pipeline:
1. Format all changed code (dart format / gofmt / black)
2. Present final summary of all changes, findings, and test results
3. Ask user to confirm
4. Create commit with descriptive message
5. Create PR with summary
6. Push to remote
