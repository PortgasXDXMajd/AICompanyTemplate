---
name: worktree
description: Create, check, update, merge and clean up the git worktree an employee works in, with scripts/worktree.py. Every employee run gets its own worktree under worktrees/, for product repos and for the HQ repo alike, which is what makes parallel work safe. Use before delegating any work that changes files, when an employee in a direct session starts work, when merging reviewed work, and when cleaning up.
argument-hint: <add|status|update|merge|remove|list> ...
---

# Worktrees

One employee run, one worktree, one branch. Employees write only inside their worktree. The Chief of Staff is the only one who writes to a main checkout (the HQ root, `projects/<project>/`) and the only one who merges.

Request: $ARGUMENTS

All the git plumbing is in one script. Run it from the HQ root; add `--json` before the subcommand for machine-readable output:

```bash
python3 scripts/worktree.py add --repo <project|_hq> --employee <name> --slug <slug> [--job <job-id>] [--existing]
python3 scripts/worktree.py status <worktree> [--base <sha>]
python3 scripts/worktree.py update <worktree>
python3 scripts/worktree.py merge  <worktree> --title "<title>" [--approved-by-ceo]
python3 scripts/worktree.py remove <worktree> [--keep-branch]
python3 scripts/worktree.py list
```

Do not set `isolation: worktree` in an employee's role file. Claude Code's built-in isolation makes a worktree of the HQ repo in a location it manages, which contains no product code and is not under `worktrees/`.

## Naming (the script enforces it)

| Thing | Pattern | Example |
|---|---|---|
| Branch | `<employee>/<slug>` | `backend-engineer/003-email-signup` |
| Product worktree | `worktrees/<project>/<employee>--<slug>` | `worktrees/my-app/backend-engineer--003-email-signup` |
| HQ worktree | `worktrees/_hq/<employee>--<slug>` | `worktrees/_hq/growth-marketer--landing-copy` |

The slug comes from the plan or spec (`003-email-signup`) or is a short name for the task. When the Chief of Staff does the work itself, the employee name is `chief-of-staff`.

## Which repo

- The task changes product code → `--repo <project>`.
- The task changes HQ files (`customers/`, `work/`, `plans/`, `specs/`, ...) → `--repo _hq`.
- The task changes nothing (a reviewer, a search, a read-only question) → no worktree. Point it at the path it should read.
- Both → two worktrees, named in the brief. This is rare; split the task if you can.

## add

`add` refuses unless HQ is a git repo with a first commit and, for a product, its main checkout is clean and on the default branch. It pulls with `--ff-only` when there is a remote; if that fails, stop and tell the CEO, and never reset or rebase a main checkout. It prints the worktree path, the branch and the **base** commit. With `--job` it also writes all three into the job's board row and brief.

- A plan that depends on other plans gets its worktree only after those are merged, so it is cut from code that contains them.
- A fix round or a resume goes back into the worktree the job already has. `add` refuses to create a second one.
- `--existing` reopens a branch that was kept after its worktree was removed.

## What the employee does there

- Reads, edits, runs and commits only under the worktree path: `git -C <worktree> add <paths>` and `git -C <worktree> commit`, or `cd <worktree> && <command>` within one call (`cd` does not persist between calls).
- Runs the project's install command first. A fresh worktree has no dependencies, no build output, and no untracked files. If the project needs a `.env`, copy it from the main checkout and never commit it.
- Does not touch the main checkouts, other worktrees, `context/log.md` or `context/decisions.md`. It returns its log line and any decision in the hand-back, and the Chief of Staff records them. The exceptions are its own job folder under `jobs/` and its own memory directory, `.claude/agent-memory/<name>/` at the HQ root: written in place, never committed by the employee, and never the stale copy inside an HQ worktree.
- Never merges, never pushes, never removes a worktree.

## Running employees in parallel

Two delegations can run at the same time when each has its own worktree, neither depends on the other's unmerged work, and the files they will change do not overlap. Plans list their in-scope files, so check those. If scopes overlap, run them one after the other.

Merge in the order the plan index gives. `merge` refuses a product branch that is behind the default branch. Its employee then runs `update` in its own worktree, which merges the default branch in; on a conflict it lists the files to resolve. After resolving, the employee reruns the tests and commits. `update` prints the **new base**: put it in the fix brief, so the review judges only this employee's change. Then the change is reviewed again.

## merge

Only after the work has passed `REVIEW.md`. A product repo merge needs the CEO's yes, asked for in the hand-off: pass `--approved-by-ceo` only when they have said it. HQ branches the Chief of Staff merges itself.

`merge` checks that the worktree has nothing uncommitted (if it does, look at the files and commit them in the worktree yourself, by path), that the branch really has commits to merge (if not, the work was never committed: stop and look), and that the main checkout is clean. On a conflict it aborts and leaves the main checkout untouched: send the branch back for `update`. Never resolve a conflict in a main checkout.

Pushing is a separate approval, and is not in the script on purpose: run `git push` yourself so Claude Code asks the CEO.

## remove

After the merge. `remove` deletes the worktree and then the branch, and never forces either: git refuses to delete unmerged work or a worktree with modified or untracked files, and that refusal is the safety net. Never use `--force`, `branch -D` or `rm -rf` on a worktree without the CEO saying so; if a folder was deleted by hand, `git -C <repo> worktree prune` repairs the registration.

Rejected or dropped work: `remove --keep-branch`, and keep the branch until the CEO says to delete it. If git refuses because of leftovers, commit them on the branch by path (`wip: rejected`) or delete the junk by hand, then retry. Note that removing a worktree deletes its ignored files (`.env`, `node_modules`).

## list

Shows every worktree of HQ and of each project with the job that owns it. A worktree with no board row is a stray, and a board row whose worktree is gone is a problem: report both (the `job-status` skill does), do not delete silently.
