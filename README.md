# Claude Code Configuration

Personal Claude Code setup — agents, commands, skills, hooks, and configuration backup.

## What's Included

### Plugin (auto-installed via `/install-plugin`)

| Type     | Name              | Purpose                                     |
|----------|-------------------|---------------------------------------------|
| Agent    | architect         | Design architecture & make design decisions  |
| Agent    | developer         | Full-stack implementation with sub-agents    |
| Agent    | documenter        | Write docs & API documentation               |
| Agent    | implementer       | Implement features from a spec               |
| Agent    | reviewer          | Code review & bug auditing                   |
| Agent    | security-reviewer | Security review & OWASP compliance           |
| Agent    | spec-writer       | Write feature specifications                 |
| Agent    | tester            | Write tests & add coverage                   |
| Command  | /architect        | Design architecture for a feature            |
| Command  | /document         | Write documentation for code                 |
| Command  | /feature          | Full SDLC pipeline (spec → ship)             |
| Command  | /implement        | Implement a feature or change                |
| Command  | /preflight        | Quick quality check (no commit)              |
| Command  | /review           | Review code changes for issues               |
| Command  | /ship             | Full quality pipeline through to PR          |
| Command  | /spec             | Produce a structured feature spec            |
| Command  | /test             | Write tests for code or feature              |
| Skill    | api-check         | Diagnose API errors (403, 429, deprecated)   |
| Skill    | debug             | Diagnose root cause from error logs          |
| Skill    | modernize-ui      | Plan & execute Flutter UI modernization      |
| Skill    | run               | Auto-detect project type and run it          |
| Skill    | seed              | Run data seeding scripts with env setup      |

### Backup (restored via `./restore.sh`)

| File                       | Destination                    | Purpose                          |
|----------------------------|--------------------------------|----------------------------------|
| backup/CLAUDE.md           | ~/.claude/CLAUDE.md            | Global user preferences          |
| backup/settings.json       | ~/.claude/settings.json        | Permissions, hooks, status line  |
| backup/statusline-command.sh | ~/.claude/statusline-command.sh | Custom status bar script       |
| hooks/claude-precommit-gate.sh | ~/scripts/                 | Pre-commit build+test gate       |
| hooks/claude-autoformat.sh | ~/scripts/                     | Auto-format on file edit         |
| hooks/llm-cost-tracker.py  | ~/scripts/                     | Per-project cost tracking        |
| hooks/llm_cost_tracker_config.py | ~/scripts/               | Cost tracker pricing config      |
| backup/memory/             | ~/.claude/projects/.../memory/ | Cross-project memory files       |

## Setup on a New Machine

```bash
# 1. Clone the repo
git clone git@github.com:cenzoroni/claude-code-config.git
cd claude-code-config

# 2. Restore configs, hooks, and memory
./restore.sh

# 3. Install the plugin (run inside Claude Code)
/install-plugin from git@github.com:cenzoroni/claude-code-config.git
```

## Keeping It Updated

When you change agents, commands, skills, or configs locally in `~/.claude/`, update this repo:

```bash
cd ~/repos/claude-code-config
# Copy changed files back, commit, push
```
