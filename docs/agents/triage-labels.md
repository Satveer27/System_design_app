# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the label strings used in this repo, and lists the extra labels the orchestrator uses.

| Label in mattpocock/skills | Label in our tracker | Meaning                                       |
| -------------------------- | -------------------- | --------------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue       |
| `needs-info`               | `needs-info`         | Waiting for more information                  |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, the orchestrator may take it |
| `ready-for-human`          | `ready-for-human`    | Needs the maintainer                          |
| `wontfix`                  | `wontfix`            | Will not be actioned                          |

When a skill mentions a role, use the corresponding label string from this table.

## Extra labels

| Label         | Kind  | Meaning                                            |
| ------------- | ----- | -------------------------------------------------- |
| `in-progress` | State | Claimed by an agent                                |
| `needs-review`| State | PR open, waiting for the review agent              |
| `review-fix1` | State | Review failed; waiting for the first fix           |
| `review-fix2` | State | Review failed again; waiting for the last fix      |
| `backend`     | Route | Goes to a backend agent                            |
| `frontend`    | Route | Goes to a frontend agent                           |
| `migrate`     | Lock  | Changes the database schema; only one at a time    |

## Rules

- Each issue meant for an agent has one state label and one of `backend` or `frontend`. Add `migrate` if it changes the database schema.
- Claiming an issue replaces `ready-for-agent`, `review-fix1` or `review-fix2` with `in-progress`.
- After opening or updating its PR, the builder replaces `in-progress` with `needs-review`. The
  orchestrator starts the matching reviewer for `needs-review` issues, one at a time, oldest first.
- No `migrate` issue is started while another one is unmerged. The lock is released on merge, not when the PR is opened.
- The agent that is blocked by something unclear comments on the issue and sets `needs-info`.

## Review loop

1. The review agent writes each problem as a comment on the issue.
2. First failed review: set `review-fix1`. The agent that built the feature fixes it.
3. Second failed review: set `review-fix2`. The same agent tries once more.
4. Third failed review: set `ready-for-human`.

Record the number of fixes already tried in an issue comment, so that it survives the label changing to `in-progress`.

A passed review also sets `ready-for-human`. Whenever `ready-for-human` is set, assign the issue or PR to the maintainer, because a label alone notifies nobody.
