#!/usr/bin/env bash
# PreToolUse hook: blocks dangerous commands and golden scenario edits.
dir="$(cd "$(dirname "$0")" && pwd)"
python_bin="$(command -v python || command -v python3)"
if [ -z "$python_bin" ]; then
  echo "Project guard: Python not found, so the action is blocked." >&2
  exit 2
fi
"$python_bin" -I "$dir/guard.py" || exit 2
