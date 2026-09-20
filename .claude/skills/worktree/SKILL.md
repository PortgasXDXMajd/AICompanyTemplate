---
name: worktree
description: Create, hand over, merge and clean up the git worktree an employee works in. Every employee run gets its own worktree under worktrees/, for product repos and for the HQ repo alike, which is what makes parallel work safe. Use before delegating any work that changes files, when an employee launched with --agent starts work, when merging reviewed work, and when cleaning up.
argument-hint: <add|merge|remove|list> <project or _hq> <employee> <slug>
---

# Worktrees

One employee run, one worktree, one branch. Employees write only inside their worktree. The Chief of Staff is the only one who writes to a main checkout (the HQ root, `projects/<project>/`) and the only one who merges.

Request: $ARGUMENTS

Do not set `isolation: worktree` in an employee's role file. Claude Code's built-in isolation makes a worktree of the HQ repo in a location it manages, which contains no product code and is not under `worktrees/`. The company manages worktrees itself, with the commands below.

Run every command from the HQ root. `cd` does not persist between tool calls, so use `git -C <path>` and full paths.

## Naming

| Thing | Pattern | Example |
|---|---|---|
| Branch | `<employee>/<slug>` | `backend-engineer/003-email-signup` |
| Product worktree | `worktrees/<project>/<employee>--<slug>` | `worktrees/my-app/backend-engineer--003-email-signup` |
| HQ worktree | `worktrees/_hq/<employee>--<slug>` | `worktrees/_hq/growth-marketer--landing-copy` |

The slug comes from the plan or spec (`003-email-signup`) or is a short name for the task. When the Chief of Staff does the work itself, the employee name is `chief-of-staff`.

## Which repo

- The task changes product code → a worktree of `projects/<project>`.
- The task changes HQ files (`customers/`, `work/`, `plans/`, `specs/`, ...) → a worktree of HQ.
- The task changes nothing (a reviewer, a search, a read-only question) → no worktree. Point it at the path it should read.
- Both → two worktrees, named in the brief. This is rare; split the task if you can.

## Before the first worktree

HQ must be a git repo with at least one commit: `git rev-parse --verify HEAD`. If that fails, run `git init -b main` if needed, then commit the current files, before anything else. Find a repo's default branch with `git -C <repo> symbolic-ref --short HEAD` while its main checkout is on it. It is `main` for everything `new-project` creates.

## add

Product repo:

```bash
git -C projects/<project> status --short          # must print nothing: main checkout clean, on the default branch
git -C projects/<project> pull --ff-only          # only if it has a remote. If it fails, stop and tell the CEO: never reset or rebase a main checkout
git -C projects/<project> worktree add -b <employee>/<slug> ../../worktrees/<project>/<employee>--<slug> <default-branch>
git -C worktrees/<project>/<employee>--<slug> rev-parse --short HEAD    # this is the BASE
```

HQ:

```bash
git worktree add -b <employee>/<slug> worktrees/_hq/<employee>--<slug> <default-branch>
git -C worktrees/_hq/<employee>--<slug> rev-parse --short HEAD          # this is the BASE
```

The path after `-C projects/<project>` is relative to that repo, which is why it starts with `../../`. Put the worktree path, the branch, and the base into the delegation brief.

A plan that depends on other plans gets its worktree only after those are merged into the default branch, so it is cut from code that contains them.

A fix round (review findings, refinement check) goes back into the same worktree. Do not create a second one for the same branch.

## What the employee does there

- Reads, edits, runs and commits only under the worktree path: `git -C <worktree> add <paths>` and `git -C <worktree> commit`, or `cd <worktree> && <command>` within one call.
- Runs the project's install command first. A fresh worktree has no dependencies, no build output, and no untracked files. If the project needs a `.env`, copy it from the main checkout and never commit it.
- Does not touch the main checkouts, other worktrees, `context/log.md` or `context/decisions.md`. It returns its log line and any decision in the hand-back, and the Chief of Staff records them. The exceptions are its own job folder under `jobs/` and its own memory directory, `.claude/agent-memory/<name>/` at the HQ root: written in place, never committed by the employee, and never the stale copy inside an HQ worktree.
- Never merges, never pushes, never removes a worktree.

## Running employees in parallel

Two delegations can run at the same time when each has its own worktree, neither depends on the other's unmerged work, and the files they will change do not overlap. Plans list their in-scope files, so check those. If scopes overlap, run them one after the other. Merge in the order the plan index gives. A branch that is behind the default branch when its turn comes is updated first, in its own worktree, by its employee: `git -C <worktree> merge <default-branch> --no-edit`, resolve any conflict, rerun the tests, commit. Its new base is `git -C <worktree> merge-base HEAD <default-branch>`; put that in the fix brief, so the review judges only this employee's change. Then it is reviewed again.

## merge

Only after the work has passed `REVIEW.md` (and the refinement check for code). First, `git -C <worktree> status --short` must print nothing. If it lists files (an employee without shell access, or leftovers), look at them and commit them in the worktree yourself, by path.

```bash
# Product repo: needs the CEO's approval, asked for in the hand-off
git -C projects/<project> merge --no-ff <employee>/<slug> -m "Merge <employee>/<slug>: <title>"

# HQ: the Chief of Staff merges reviewed work itself
git merge --no-ff <employee>/<slug> -m "Merge <employee>/<slug>: <title>"
```

A merge that prints `Already up to date.` merged nothing: the work was never committed. Stop and check the worktree. On a conflict, run `git -C <repo> merge --abort` at once and send the branch back to be updated (see "Running employees in parallel"). Never resolve a conflict in a main checkout.

Pushing is a separate approval, as always.

## remove

After the merge:

```bash
git -C projects/<project> worktree remove ../../worktrees/<project>/<employee>--<slug>
git -C projects/<project> branch -d <employee>/<slug>
# HQ:
git worktree remove worktrees/_hq/<employee>--<slug>
git branch -d <employee>/<slug>
```

`branch -d` refuses to delete unmerged work, which is the safety net: never use `-D` or `worktree remove --force` without the CEO saying so.

Rejected or dropped work: run the same `worktree remove` and keep the branch until the CEO says to delete it. `worktree remove` deletes ignored files (`.env`, `node_modules`) and refuses if anything is modified or untracked; then commit the leftovers on the branch by path (`wip: rejected`) or delete the junk by hand, and retry. Never `rm -rf` a worktree folder; if that happened, run `git -C <repo> worktree prune`. To reopen a kept branch, add the worktree without `-b`: `git -C projects/<project> worktree add ../../worktrees/<project>/<employee>--<slug> <employee>/<slug>`.

## list

`git -C projects/<project> worktree list` and `git worktree list`. A worktree with no open roadmap item behind it is stale: report it in the weekly review, do not delete it silently.
