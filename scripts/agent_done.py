"""Run by an agent when it finishes: reports its token use to Discord and wakes the orchestrator.

Usage: agent_done.py --role backend-builder --issue 12 --outcome needs-review [--dry-run]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

WEBHOOK_PREFIX = "https://discord.com/api/webhooks/"
KINDS = {
    "input_tokens": "input",
    "cache_creation_input_tokens": "cache write",
    "cache_read_input_tokens": "cache read",
    "output_tokens": "output",
}


def transcripts(session_id: str, projects: Path) -> list[Path]:
    """The session's transcript and those of its subagents."""
    return [
        *projects.glob(f"*/{session_id}.jsonl"),
        *projects.glob(f"*/{session_id}/subagents/*.jsonl"),
    ]


def count_tokens(files: list[Path]) -> dict[str, int]:
    """Sums usage, counting each message once."""
    usage_by_message: dict[str, dict[str, int]] = {}
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            try:
                message = json.loads(line).get("message")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(message, dict) and message.get("usage") and message.get("id"):
                usage_by_message[message["id"]] = message["usage"]
    return {kind: sum(u.get(kind) or 0 for u in usage_by_message.values()) for kind in KINDS}


def report(role: str, issue: int, outcome: str, tokens: dict[str, int]) -> str:
    parts = ", ".join(f"{label} {tokens[kind]:,}" for kind, label in KINDS.items())
    return (
        f"Issue #{issue} · {role} · {outcome}\n"
        f"Session tokens so far: {sum(tokens.values()):,} ({parts})"
    )


def git_dir() -> Path:
    """The .git directory shared by every worktree."""
    output = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(output)


def webhook_url(env_file: Path) -> str | None:
    """DISCORD_WEBHOOK_URL from the environment or the main checkout's .env."""
    url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not url and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("DISCORD_WEBHOOK_URL="):
                url = line.split("=", 1)[1].strip().strip("\"'")
    return url if url.startswith(WEBHOOK_PREFIX) else None


def post_to_discord(url: str, text: str) -> None:
    request = urllib.request.Request(  # noqa: S310
        url,
        data=json.dumps({"content": text, "allowed_mentions": {"parse": []}}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "agent-done"},
    )
    # nosemgrep
    with urllib.request.urlopen(request, timeout=15):  # noqa: S310
        pass


def wake_orchestrator(handle_file: Path) -> str:
    """Types /orchestrate into the orchestrator's Orca terminal."""
    orca = shutil.which("orca")
    if not handle_file.exists() or orca is None:
        return "orchestrator not registered: it will see this on its next run"
    handle = handle_file.read_text(encoding="utf-8").strip()
    result = subprocess.run(
        [orca, "terminal", "send", "--terminal", handle, "--text", "/orchestrate", "--enter"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return "orchestrator woken" if result.returncode == 0 else "could not reach the orchestrator"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    files = transcripts(session_id, Path.home() / ".claude" / "projects") if session_id else []
    text = report(args.role, args.issue, args.outcome, count_tokens(files))
    if not files:
        text += "\n(no transcript found: token counts are unavailable)"
    print(text)
    if args.dry_run:
        return 0

    try:
        common = git_dir()
        url = webhook_url(common.parent / ".env")
        if url:
            post_to_discord(url, text)
            print("sent to Discord")
        else:
            print("no DISCORD_WEBHOOK_URL: not sent to Discord")
    except Exception as error:
        print(f"Discord report failed: {type(error).__name__}")
    try:
        print(wake_orchestrator(git_dir() / "orchestrator-terminal"))
    except Exception as error:
        print(f"could not wake the orchestrator: {type(error).__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
