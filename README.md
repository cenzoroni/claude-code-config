# Claude Code Configuration

Personal Claude Code setup — agents, commands, skills, hooks, and configuration backup.

## What's Included

### Plugins (installed from this repo's marketplace)

This repo is a **plugin marketplace** (`.claude-plugin/marketplace.json`) that
ships three plugins under `plugins/`:

| Plugin          | Contents                                                        |
|-----------------|-----------------------------------------------------------------|
| `sdlc-pipeline` | 8 agents + 9 workflow commands (spec → architect → ship)        |
| `play-ready`    | `/play-ready` command + `play-ready/` templates/scripts/proguard |
| `dev-skills`    | 5 skills: api-check, debug, modernize-ui, run, seed             |


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
| Command  | /play-ready       | Prepare a Flutter app for Google Play        |
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

# 2. Restore configs, hooks, and memory (the dotfile half)
./restore.sh

# 3. Install the plugins (run inside Claude Code)
/plugin marketplace add cenzoroni/claude-code-config
/plugin install sdlc-pipeline play-ready dev-skills
```

## Keeping It Updated

Two tracks, because they sync differently:

**Plugins (agents, commands, skills)** — edit the files under `plugins/`,
commit, and push. Each machine that has the marketplace added pulls the changes:

```bash
# on the authoring machine
cd ~/repos/claude-code-config
$EDITOR plugins/sdlc-pipeline/commands/ship.md   # etc.
git commit -am "…" && git push

# on any other machine (or leave auto-update on to skip this)
/plugin marketplace update vince-claude-config
```

Auto-update is enabled by default in this setup, so a `git push` here reaches
every machine on its next session. There is no more hand-copying into
`~/.claude/skills/` — the installed plugin (pulled from git) is the single
source of truth.

**Dotfiles (CLAUDE.md, settings.json, hooks, memory)** — plugins can't deliver
these, so they stay on the `restore.sh` track. Copy changed files back into
`backup/` / `hooks/`, commit, push, and run `./restore.sh` on the other machine.

## /play-ready

Prepares a Flutter app for Google Play: readiness checklist, signing and
build setup, privacy and data-deletion pages, and filled-in answers for the
Play Console forms.

- `play-ready/` holds the templates, scripts and ProGuard base rules. Install
  the script dependencies once: `cd plugins/play-ready/play-ready/scripts && pipenv install`.
- Everything for one app lives in `play-store/` in that app's repo:
  `config.yaml` (drafted by `analyze.py`), `guides/`, `pages/` and `assets/`.
  `/play-ready` first runs `migrate.py`, which moves files from older layouts
  into that folder, so re-running on an older app brings it up to date.
- Personal details (developer names and emails, where policy pages are
  hosted, keystore identity) live in `~/.claude/play-ready.yaml`, which
  `restore.sh` creates from
  [`config/play-ready.sample.yaml`](config/play-ready.sample.yaml). Fill it in
  locally. `play-ready.yaml` is gitignored so a real copy can't be committed.
