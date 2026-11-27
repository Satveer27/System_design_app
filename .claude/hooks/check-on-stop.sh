#!/usr/bin/env bash
# Stop hook: checks the side that changed.
# Exit code 2 returns the failures to the agent.
root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
input="$(cat)"

# Allows the stop on the second attempt.
if printf '%s' "$input" | grep -qE '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

cd "$root" || exit 0

# Changed: committed on this branch, uncommitted or new.
base="$(git merge-base HEAD origin/main 2>/dev/null || git rev-parse HEAD 2>/dev/null)"
changed="$(
  {
    git diff --name-only "$base"
    git ls-files --others --exclude-standard
  } 2>/dev/null | grep -v '\.md$' | sort -u
)"

failures=""
check() { # check <folder> <command...>
  local folder="$1" output
  shift
  if ! output="$(cd "$root/$folder" && "$@" 2>&1)"; then
    failures+=$'\n'"--- FAILED in $folder: $*"$'\n'"$(printf '%s\n' "$output" | tail -n 30)"$'\n'
  fi
}

if [ -f "$root/backend/pyproject.toml" ] && printf '%s\n' "$changed" | grep -qE '^(backend/|\.claude/hooks/)'; then
  check backend uv run ruff check .
  check backend uv run ruff format --check .
  check backend uv run mypy .
  check backend uv run pytest -q
fi

if [ -f "$root/frontend/package.json" ] && printf '%s\n' "$changed" | grep -q '^frontend/'; then
  check frontend pnpm lint
  check frontend pnpm tsc --noEmit
  check frontend pnpm test
fi

if [ -n "$failures" ]; then
  {
    echo "Checks failed, so you are not done."
    echo "$failures"
    echo "Fix the code. Do not weaken tests or change golden values. If you cannot fix it, or you are"
    echo "a reviewer, report the failure instead. Database tests need: docker compose up -d db redis"
  } >&2
  exit 2
fi
exit 0
