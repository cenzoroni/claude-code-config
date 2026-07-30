#!/bin/sh
input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // "?"')
model=$(echo "$input" | jq -r '.model.display_name // "?"')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Shorten home directory
short_cwd=$(echo "$cwd" | sed "s|^$HOME|~|")

# Git branch (skip optional locks)
branch=""
if git_branch=$(GIT_OPTIONAL_LOCKS=0 git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null); then
  branch=" ($git_branch)"
fi

# Context usage
ctx=""
if [ -n "$used" ]; then
  ctx=" | ctx: ${used}%"
fi

printf "%s%s | %s%s" "$short_cwd" "$branch" "$model" "$ctx"
