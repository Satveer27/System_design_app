#!/usr/bin/env bash
# PostToolUse hook: formats the edited file.
root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
python_bin="$(command -v python || command -v python3)" || exit 0

# Prints the edited file path with forward slashes.
file="$("$python_bin" -I -c '
import json, sys
path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
sys.stdout.write(path.replace(chr(92), "/"))
' 2>/dev/null)"
[ -f "$file" ] || exit 0

case "$file" in
  */node_modules/* | */.venv/*) ;;
  */backend/*.py)
    # Fixes lint issues except unused imports (F401), then formats.
    (
      cd "$root/backend" &&
        uv run ruff check --fix --unfixable F401 "$file"
      uv run ruff format "$file"
    ) >/dev/null 2>&1
    ;;
  */frontend/*.ts | */frontend/*.tsx | */frontend/*.css)
    (cd "$root/frontend" && pnpm exec prettier --write "$file") >/dev/null 2>&1
    ;;
esac
exit 0
