#!/bin/bash
# Auto-format hook for Claude Code
# Called as a PostToolUse hook on Edit|Write
# Reads JSON from stdin, formats the edited file based on extension

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    exit 0
fi

case "$FILE" in
    *.dart)  dart format "$FILE" >/dev/null 2>&1 ;;
    *.go)    gofmt -w "$FILE" 2>/dev/null ;;
    *.py)    command -v black &>/dev/null && black -q "$FILE" 2>/dev/null ;;
esac

exit 0
