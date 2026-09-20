# jobs/

The company's flight recorder for work in progress. Every delegation is a **job** with its own folder, and `BOARD.md` lists every job that is not finished. If a session dies, a new one reads this folder and knows exactly what was running, how far it got, and what to do next. The `job-status` skill does that reading.

```
jobs/
  BOARD.md                         every open job, one row each
  <YYYYMMDD>-<employee>--<slug>/   one folder per job
    brief.md                       the assignment (Chief of Staff)
    progress.md                    the employee's running journal, appended as it works
    handback.md                    the employee's result
    review.md, quality.md, architecture.md, qa.md     helper outputs, each ending in a Verdict line
                                   (briefs: <name>-brief.md, re-checks: <name>-2.md)
    qa/                            screenshots, recordings, logs and flow files from hands-on QA
    handoff.md                     what the CEO was shown and asked, written before it is presented
    fix-1-brief.md, fix-1-handback.md, ...            fix rounds
    resume-1-brief.md, ...                            restarts after an interruption
```

Rules:

- **Use the scripts, not a text editor**, for the board and for progress lines: `python3 scripts/job.py new | set | progress | show | list | close`. They keep the table well-formed, stamp the time, and write the journal line. `python3 scripts/status.py` reads everything back.

- **Write before you act.** The Chief of Staff adds the board row and the brief before starting the employee. The employee appends to `progress.md` when it starts and finishes each step, with the command it ran and what came back. A line written after the fact is lost in a crash.
- `BOARD.md` is written by the Chief of Staff. The one exception: an employee the CEO launched directly adds and updates its own row.
- An employee writes only in its own job folder here, at the HQ root, never in the copy of `jobs/` inside an HQ worktree. Everything else it changes is in its worktree. Helpers write only their output file, not `progress.md`.
- An employee in a direct session adds its own row with state `running`.
- The Chief of Staff's own work is a job too: employee `chief-of-staff`, runner `self`.
- When a job closes, its row leaves the board, one line goes into `context/log.md`, and the folder stays as the record. Job folders are committed with the rest of HQ.

## States

| State | Meaning | Who moves it on |
|---|---|---|
| `briefed` | Row, brief and worktree exist; the employee has not started | Chief of Staff |
| `running` | The employee is working | employee finishes, or a session notices it stopped |
| `blocked` | Waiting on the CEO (an approval, a question, a merge conflict) | CEO |
| `handed-back` | `handback.md` exists; not reviewed yet | Chief of Staff |
| `in-review` | Independent review, refinement check or QA is running; Next step names the helpers | Chief of Staff |
| `fixing` | A fix round is running in the same worktree | employee |
| `awaiting-merge` | Passed everything; `handoff.md` is written and the CEO has been asked | CEO |
| `interrupted` | The runner is gone and there is no hand-back | `job-status` skill proposes resume, restart or drop |
| `failed` | The employee gave up or hit a STOP condition | Chief of Staff, with the CEO |

Closed jobs (`merged`, `dropped`) are removed from the board.
