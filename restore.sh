#!/bin/bash
# Restore Claude Code configuration from this repo backup.
# Run from the repo root: ./restore.sh
#
# What it does:
#   - Copies CLAUDE.md to ~/.claude/CLAUDE.md
#   - Merges settings.json into ~/.claude/settings.json (hooks, permissions, statusLine)
#   - Copies statusline-command.sh to ~/.claude/
#   - Copies hook scripts to ~/scripts/
#   - Copies memory files to the repos-level project memory
#
# The plugin parts (agents, commands, skills) are installed separately via:
#   /install-plugin from <repo-url>

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SCRIPTS_DIR="$HOME/scripts"
MEMORY_DIR="$CLAUDE_DIR/projects/-Users-vince-repos/memory"

echo "Restoring Claude Code config from: $REPO_DIR"
echo ""

# CLAUDE.md
if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
    echo "[skip] ~/.claude/CLAUDE.md already exists (diff below if different)"
    diff "$CLAUDE_DIR/CLAUDE.md" "$REPO_DIR/backup/CLAUDE.md" || true
else
    cp "$REPO_DIR/backup/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
    echo "[done] Copied CLAUDE.md to ~/.claude/"
fi

# settings.json — don't overwrite, just show diff
if [ -f "$CLAUDE_DIR/settings.json" ]; then
    echo ""
    echo "[info] ~/.claude/settings.json already exists."
    echo "       Compare with backup and merge manually if needed:"
    diff "$CLAUDE_DIR/settings.json" "$REPO_DIR/backup/settings.json" || true
else
    cp "$REPO_DIR/backup/settings.json" "$CLAUDE_DIR/settings.json"
    echo "[done] Copied settings.json to ~/.claude/"
fi

# Statusline
cp "$REPO_DIR/backup/statusline-command.sh" "$CLAUDE_DIR/statusline-command.sh"
chmod +x "$CLAUDE_DIR/statusline-command.sh"
echo "[done] Copied statusline-command.sh to ~/.claude/"

# Hook scripts
mkdir -p "$SCRIPTS_DIR"
for script in claude-precommit-gate.sh claude-autoformat.sh; do
    cp "$REPO_DIR/hooks/$script" "$SCRIPTS_DIR/$script"
    chmod +x "$SCRIPTS_DIR/$script"
    echo "[done] Copied $script to ~/scripts/"
done

cp "$REPO_DIR/hooks/llm-cost-tracker.py" "$SCRIPTS_DIR/llm-cost-tracker.py"
cp "$REPO_DIR/hooks/llm_cost_tracker_config.py" "$SCRIPTS_DIR/llm_cost_tracker_config.py"
echo "[done] Copied cost tracker scripts to ~/scripts/"

# Memory
mkdir -p "$MEMORY_DIR"
for memfile in "$REPO_DIR/backup/memory/"*.md; do
    fname=$(basename "$memfile")
    if [ -f "$MEMORY_DIR/$fname" ]; then
        echo "[skip] Memory file $fname already exists"
    else
        cp "$memfile" "$MEMORY_DIR/$fname"
        echo "[done] Copied memory/$fname"
    fi
done

echo ""
echo "Restore complete."
echo ""
echo "To install the plugin (agents, commands, skills), run in Claude Code:"
echo "  /install-plugin from <this-repo-url>"
