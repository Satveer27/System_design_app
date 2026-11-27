"""PreToolUse guard. Exit code 2 blocks the tool call and prints the reason."""

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

PROTECTED = {"main", "master"}
SHELLS = {"bash", "sh", "zsh", "powershell", "pwsh"}
OPERATORS = {";", "&", "&&", "|", "||", "(", ")"}
HARMLESS_PROGRAMS = {"git", "gh", "grep", "rg", "echo", "cat"}
GOLDEN_DIR = re.compile(r"tests[/\\]golden\b")
WRITES = re.compile(
    r">|\bsed\b[^|;&]*\s-i|\b(rm|mv|cp|tee|truncate|del|Set-Content|Out-File|Add-Content|"
    r"Remove-Item|Move-Item|Copy-Item)\b|\bgit\s+(rm|mv)\b|write_text"
)


class Blocked(Exception):
    pass


def current_branch(cwd: str) -> str:
    if branch := os.environ.get("GUARD_BRANCH"):  # Set by tests
        return branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, capture_output=True, text=True
    )
    return result.stdout.strip()


def segments(command: str) -> list[list[str]]:
    """Split into simple commands, keeping quoted text together."""
    text = command.replace("\\\n", " ").replace("\n", " ; ")
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    result: list[list[str]] = [[]]
    for token in lexer:
        if token in OPERATORS:
            result.append([])
        else:
            result[-1].append(token)
    return [s for s in result if s]


def check_git(args: list[str], cwd: str) -> None:
    index = 0
    while index < len(args) and args[index].startswith("-"):
        if args[index] in {"-c", "-C"}:
            if "core.hookspath" in " ".join(args[index : index + 2]).lower():
                raise Blocked("changing core.hooksPath skips the hooks")
            index += 2
        else:
            index += 1
    if index >= len(args):
        return
    sub, rest = args[index], args[index + 1 :]

    if sub == "config" and any("core.hookspath" in a.lower() for a in rest):
        raise Blocked("changing core.hooksPath skips the hooks")
    if sub in {"commit", "push", "merge", "rebase", "am"} and "--no-verify" in rest:
        raise Blocked("--no-verify skips the hooks")
    if sub == "commit" and any(re.fullmatch(r"-[a-zA-Z]*n[a-zA-Z]*", a) for a in rest):
        raise Blocked("git commit -n skips the hooks")
    if sub != "push":
        return

    flags = [a for a in rest if a.startswith("-")]
    positional = [a for a in rest if not a.startswith("-")]
    for flag in flags:
        if flag.startswith("--force") or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", flag):
            raise Blocked("force-pushing is not allowed")
        if flag in {"--all", "--mirror"}:
            raise Blocked(f"git push {flag} would push main")
    refspecs = positional[1:]  # First is the remote
    for refspec in refspecs:
        if refspec.startswith("+"):
            raise Blocked("force-pushing is not allowed")
        target = refspec.split(":")[-1].removeprefix("refs/heads/")
        if target == "HEAD":
            target = current_branch(cwd)
        if target in PROTECTED:
            raise Blocked("pushing to main is not allowed: open a pull request")
    if not refspecs and current_branch(cwd) in PROTECTED:
        raise Blocked("you are on main: pushing to main is not allowed")


def check_command(command: str, cwd: str) -> None:
    if GOLDEN_DIR.search(command):
        quiet = re.sub(r"\d?>&\d|\d?>\s*(/dev/null|\$null)", "", command)
        if WRITES.search(quiet):
            raise Blocked(
                "golden scenarios must not be changed from the shell. If an expected value looks "
                "wrong, comment on the issue and stop"
            )

    for words in segments(command):
        assignments = []
        while words and re.match(r"[A-Za-z_]\w*=", words[0]):
            assignments.append(words.pop(0))
        if not words:
            continue
        program = Path(words[0]).name.removesuffix(".exe").lower()
        args = words[1:]
        joined = " ".join(words)

        if program == "git":
            if any(a.startswith("SKIP=") for a in assignments):
                raise Blocked("SKIP= skips the hooks")
            check_git(args, cwd)
        if program in SHELLS:
            for flag, script in zip(args, args[1:], strict=False):
                if flag.lower() in {"-c", "-command"}:
                    check_command(script, cwd)
        if "pre-commit" in joined and "uninstall" in words:
            raise Blocked("uninstalling the hooks is not allowed")
        if program == "gh":
            if args[:2] == ["pr", "merge"]:
                raise Blocked("agents never merge pull requests")
            if args[:1] == ["api"] and re.search(r"/merges?\b|mergePullRequest", joined):
                raise Blocked("agents never merge pull requests")
        if program == "dropdb" or "dropdb" in args:
            raise Blocked("dropping databases is not allowed")
        if program not in HARMLESS_PROGRAMS and re.search(
            r"\bdrop\s+(database|schema)\b", joined, re.IGNORECASE
        ):
            raise Blocked("dropping databases is not allowed")
        if program in {"docker", "docker-compose"}:
            if "down" in args and {"-v", "--volumes"} & set(args):
                raise Blocked("this would delete the database volume")
            if "volume" in args and {"rm", "prune"} & set(args):
                raise Blocked("this would delete database volumes")
            if "prune" in args and "--volumes" in args:
                raise Blocked("this would delete database volumes")
        if "alembic" in joined and "downgrade" in words and "base" in words:
            raise Blocked("downgrading to base drops every table")


def check_file(path: str) -> None:
    file = Path(path)
    if GOLDEN_DIR.search(path) and file.suffix in {".yaml", ".yml"} and file.exists():
        raise Blocked(
            "existing golden scenarios must not be edited. If an expected value looks wrong, "
            "comment on the issue and stop"
        )


def main() -> int:
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        if data.get("tool_name") in {"Bash", "PowerShell"}:
            command = tool_input.get("command", "")
            try:
                check_command(command, data.get("cwd") or ".")
            except ValueError:  # Unbalanced quotes
                if re.search(r"--no-verify|git\s+push|gh\s+pr\s+merge|drop\s+database", command):
                    raise Blocked("could not parse a command that may be dangerous") from None
        else:
            check_file(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    except Blocked as reason:
        print(f"Blocked by the project guard: {reason}.", file=sys.stderr)
        return 2
    except Exception as error:  # Blocks on any error
        print(f"Project guard failed, so the action is blocked: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
