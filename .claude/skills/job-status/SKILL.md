---
name: job-status
description: Reconstruct what is going on in the company from the files alone - open jobs, what each employee was doing, what finished, what was interrupted or failed - and recommend what to continue, restart, review or drop. Use at the start of every Chief of Staff session that finds open jobs, when the CEO asks "what is happening", "where were we", "status", after a crash or a cleared context, and at the start of the end-of-day routine.
---

# Status and resume

The CEO must never have to re-explain anything. Everything needed is on disk: read it, check it against reality, report, and ask for a yes or no.

## 1. Read the record

- `jobs/BOARD.md`: every open job and its last known state.
- The newest file in `context/journal/` (and the one before it if today's is short): the last things the Chief of Staff did and was about to do. The last entries tell you what was in flight when the previous session ended.
- `ROADMAP.md` (already in context) and the last 20 lines of `context/log.md`.

## 2. Check each open job against reality

The board says what was believed. Find out what is true:

```bash
ls jobs/<job-id>/                                  # brief, progress, handback, review files?
tail -n 30 jobs/<job-id>/progress.md               # how far did it get, what was it doing last?
git worktree list; git -C projects/<project> worktree list
git -C <worktree> status --short                   # uncommitted work?
git -C <worktree> log --oneline <base>..HEAD       # what was committed?
git -C <repo> branch --merged <default-branch>     # was this job's branch already merged?
```

A review step counts as done only when its file ends in a `Verdict:` line (`review.md`, `quality.md`, `architecture.md`, `qa.md`, and `-2` files for re-checks). Read the verdict: "pass with fixes" with no fix brief after it means the fixes were never started. A file without a verdict line was cut off mid-write. `handoff.md` holds what the CEO was last asked about this job.

Is anyone still working on it?

- Inside Herdr (`test "${HERDR_ENV:-}" = 1`): `herdr agent list`, then `herdr agent get <agent-name>` for the runner named on the board, and for any helper named in its Next step (`rev-`, `qual-`, `arch-`, `qa-`). A live helper means wait for it; do not start another. Employee tabs are separate processes and often outlive a dead Chief of Staff session. `working` means it is still running, `blocked` means it is waiting for the CEO in its tab, `idle` or `done` means it stopped.
- Runner `subagent` or `self`: these die with the session that started them. No hand-back for the current round means the job was interrupted, unless that session is in fact still open in another terminal.
- Runner `direct session`: the CEO ran that employee themselves. It is finished when `handback.md` exists.
- Before you call anything interrupted: if its last progress line is less than about 15 minutes old, or its runner is `direct session`, ask the CEO whether that session is still open. Two writers in one worktree is worse than waiting.

Also look for strays: worktrees with no board row, job folders with no row and no hand-back, board rows whose worktree is gone.

Last resort, when the journal and the job folders do not explain something: the previous session's transcript is under `~/.claude/projects/` in the folder named after this directory's path, newest `.jsonl` first. Read only its tail. Its format is internal and changes between versions, so treat it as a hint.

## 3. Classify

| Verdict | Evidence | Recommendation |
|---|---|---|
| **Running fine** | live runner, recent progress lines | leave it, say when you will look again |
| **Needs the CEO** | runner `blocked`, or state `blocked` / `awaiting-merge` | say exactly what is being asked and where |
| **Finished, not reviewed** | `handback.md` exists, no review files | start the review now |
| **Review unfinished** | a step `REVIEW.md` requires for this kind of work has no file with a verdict line, or a verdict asks for fixes that were not started | continue from the first unfinished step |
| **Fix round cut off** | `fix-N-brief.md` without `fix-N-handback.md`, no live runner | resume the fix round in the same worktree |
| **Merged, not closed** | the branch shows in `branch --merged`, the row is still open | finish the close-out yourself: remove the worktree, log, take the row off. Do not ask the CEO again |
| **Interrupted** | no runner, no hand-back, progress or commits exist | resume in the same worktree |
| **Never started** | `briefed`, or `running` with no progress, no commits and no runner | start it |
| **Failed** | progress ends in an error or a STOP condition, or the hand-back says so | say why; fix the brief or plan before retrying, or drop |
| **Stale** | nothing has moved and no roadmap item needs it | drop, with the CEO's yes |

Judge the work too, not only the state: read the last progress lines and the diff. "Interrupted but 90% done and tests green" and "interrupted after going down the wrong path" need different recommendations. Say which it is.

## 4. Report

Lead with one line: how many jobs are open and how many need the CEO. Then one block per job, worst first:

```
<job id>: <employee>, <task>
State: <verdict>, <one line of evidence>
Good / not good: <your judgment of the work so far, and why>
Recommend: <continue | resume | restart from scratch | review now | drop> (yes/no?)
```

End with anything the last session was about to do for the CEO that is not a job (from the journal), and the top item in **Now**. No open jobs and a clean journal: say so in two lines.

## 5. Act on the answers

- **Resume**: write `jobs/<job-id>/resume-N-brief.md`: what was done (from `progress.md` and the commits), what is left, and "continue from here, do not redo finished steps, verify the state of the worktree before you change anything". Run it with the `delegate` skill in the same worktree. If the employee's Herdr tab is still alive and idle, prompt that agent; it still has its context.
- **Restart from scratch**: keep the old branch until the CEO says to drop it (`worktree` skill, rejected work), then delegate again under a new slug.
- **Review now**: continue with `REVIEW.md` from the first missing step.
- **Drop**: remove the worktree, keep or delete the branch as the CEO says, take the row off the board, log it.

Update `jobs/BOARD.md` and the journal as you go, before each action.
