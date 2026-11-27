---
name: orchestrate
description: Assigns ready GitHub issues to free builder slots, prepares a git worktree and .env for each, and starts each agent in its own Orca terminal. Also starts the next review and sends fix requests. Use when the user runs /orchestrate.
---

# Orchestrate

You coordinate work. You never write feature code, review code or merge PRs. Label names and states
come from `docs/agents/triage-labels.md`; use those exactly. State is read from **issue labels**:
reviews are posted as comments, so a PR's `reviewDecision` is always empty.

Run from the main checkout, in an Orca **terminal** tab (a chat tab cannot be woken), started with
`claude --model sonnet --effort low --permission-mode auto`. Builders run on Sonnet and reviewers on
Opus, both at medium effort, as set in their agent files.

You are run by Sat, by `/loop` and by agents finishing (their `scripts/agent_done.py` types
`/orchestrate` into your terminal). Every run must be safe to repeat. If nothing needs doing, say
so in one line and stop.

## 0. Register

`echo "$ORCA_TERMINAL_HANDLE" > "$(git rev-parse --git-common-dir)/orchestrator-terminal"`. If the
variable is empty, tell Sat that agents cannot wake you from this tab.

## Slots

| Slot | Worktree | `API_PORT` | `WEB_PORT` | `DB_NAME` | `REDIS_DB` |
|---|---|---|---|---|---|
| 1 | `../fpl-slot1` | 8001 | 3001 | fpl_slot1 | 1 |
| 2 | `../fpl-slot2` | 8002 | 3002 | fpl_slot2 | 2 |
| review | `../fpl-review` | 8009 | 3009 | fpl_review | 9 |

A slot's `.env` is a single file at the **root** of its worktree, made from `.env.slot.example` by
replacing `{{API_PORT}}`, `{{WEB_PORT}}`, `{{DB_NAME}}` and `{{REDIS_DB}}`. Don't write
`backend/.env` or `frontend/.env`: nothing reads them.

## 1. Check state

1. Confirm you are on `main` with a clean tree. If not, stop and tell Sat. Then `git fetch origin`
   and `git pull --ff-only`.
2. `git worktree list`. For each builder slot, the issue number is in its branch name
   (`issue-<N>-<slug>`).
3. A slot is **free** only if it has no worktree, or its branch's PR is merged and
   `git status --porcelain` there is empty. Check with
   `gh pr list --state all --head <branch> --json number,state`.
   Anything else is **busy**, including a freshly assigned slot with no commits yet.
4. Clean up merged slots only: `orca terminal close --worktree path:<absolute path> --all`, then
   `git worktree remove <path>` and `git branch -D <branch>`. Never remove a worktree with
   uncommitted work; report it. If a PR was closed without merging, ask Sat.
5. `orca terminal list --json` shows which slots already have an agent terminal.

## 2. Pick issues

1. `gh issue list --state open --label ready-for-agent --json number,title,labels,body`
2. Skip any issue with an open blocker. Check GitHub's blocked-by dependencies and every
   `Blocked by #X` in the body: #X must be closed.
3. Order: foundation work first, then lowest issue number.
4. Rules:
   - Each issue needs exactly one of `backend` or `frontend`. Otherwise report it and skip it.
   - Never run two issues that edit the same area at once (for example both touch
     `pipeline/dags/`, or the same frontend feature folder). Compare against busy slots too.
     If an issue doesn't say enough to tell, report that instead of guessing.
   - At most one `migrate` issue is unmerged at any time. An open `migrate` issue labelled
     `in-progress`, `needs-review`, `review-fix1`, `review-fix2` or `ready-for-human` holds the lock.
   - Frontend issues only when their backend blocker is merged.
5. Fill free slots, at most 2 builders in total.

## 3. Prepare each assignment

1. `git worktree add ../fpl-slot<S> -b issue-<N>-<short-slug> origin/main`
2. Write `../fpl-slot<S>/.env` from `.env.slot.example` with the slot's values.
3. `gh issue edit <N> --remove-label ready-for-agent --add-label in-progress`, then comment
   `Assigned to slot <S>`.

## 4. Start the agents

Each agent runs as a full Claude session in a visible Orca terminal, so Sat can watch it and type to
it. Use the worktree's absolute path:

```
orca terminal create --worktree path:<absolute path to fpl-slot<S>> --title "Slot <S> · #<N>" \
  --command 'claude --permission-mode auto --agent <backend|frontend>-builder "Implement issue #<N>."' --json
```

Always pass `--permission-mode auto`: without it Orca may start the session with permissions
bypassed. Leave a builder's terminal open when it finishes: it keeps its context until the PR is
merged. If the command fails, print it for Sat to run by hand.

## 5. Review queue

One review runs at a time. If `../fpl-review` does not exist, create it with
`git worktree add --detach ../fpl-review origin/main` and write its `.env`.

A review's round `<R>` is 1 plus the number of `Review round` comments already on the issue when it
starts, and it is part of the terminal title. An open review terminal is **finished** once the issue
has at least `<R>` such comments; until then it is **running**.

- Running: start nothing.
- Finished: close it (`orca terminal close --worktree path:<absolute path to fpl-review> --all`), even
  if no other review is waiting. Each review, including a re-review, is a new session.

`gh issue list --state open --label needs-review --json number,title,labels,updatedAt`, oldest first.
Find the issue's PR (`gh pr list --head <branch>`), start the first, and list the rest as waiting:

```
orca terminal create --worktree path:<absolute path to fpl-review> --title "Review · #<N> · round <R>" \
  --command 'claude --permission-mode auto --agent <backend|frontend>-reviewer "Review PR #<P>."' --json
```

For issues labelled `review-fix1` or `review-fix2`, send the fix once per round. Skip it if the issue
already has a comment `Fix sent for round <R>`, where `<R>` counts its `Review round` comments.

- Builder terminal open: check it is idle
  (`orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 5000`), then
  `MSYS_NO_PATHCONV=1 orca terminal send --terminal <handle> --text "Address the review on issue #<N>." --enter --wait-submit 20`.
  If it is not idle, leave it for the next run. Never type into a terminal showing a question or
  permission prompt.
- No builder terminal: start one in that slot as in step 4, with that sentence as the prompt.

Then comment `Fix sent for round <R>` on the issue.

List issues labelled `ready-for-human` or `needs-info` as waiting for Sat.

## 6. Report

End with a short table (slot, issue, status), then the waiting issues and why: blocked by #X, area
conflict, migration lock, no free slot, or needs Sat.

Agents wake you, but a merge on GitHub does not. On the first run of a session, suggest
`/loop 15m /orchestrate` if no loop is running.
