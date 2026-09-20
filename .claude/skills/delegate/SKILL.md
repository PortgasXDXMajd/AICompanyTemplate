---
name: delegate
description: How the Chief of Staff hands a task to an employee or a helper and gets the result back. Covers the job record, the employee's worktree, the delegation brief, and the two ways to run it - as its own visible Herdr tab when the session runs inside Herdr, or as an in-process subagent otherwise. Use for every delegation, every fix round, every resume, and every review, quality, architecture or QA helper.
argument-hint: <employee or "helper"> <task>
---

# Delegate

Task: $ARGUMENTS

Every delegation follows the same five steps: record, worktree, brief, run, collect. Only "run" differs between Herdr and a plain terminal. Write each step down before you do it (`jobs/README.md`): that is what lets a new session pick up after a crash.

## 1. Record

Job id: `<YYYYMMDD>-<employee>--<slug>`. Create `jobs/<job-id>/`, add the row to `jobs/BOARD.md` (state `briefed`), and add a journal line. Helpers (reviewer, quality, architecture, QA) are steps inside the job they check, not jobs of their own: their files live in that job's folder. Work the Chief of Staff does itself is a job too: employee `chief-of-staff`, runner `self`, with its own `progress.md`.

## 2. Worktree

If the task changes files, create the employee's worktree with the `worktree` skill and put its path, branch and base on the board row. Fix rounds and resumes go back into the worktree the job already has. Read-only helpers get no worktree; they are pointed at the one they check.

## 3. Brief

Write `jobs/<job-id>/brief.md` (helpers: `<name>-brief.md`, fix rounds: `fix-N-brief.md`, resumes: `resume-N-brief.md`). In this order:

- **From**: "Delegation brief from the Chief of Staff. Job `<job-id>`. Your job folder is `<absolute HQ root>/jobs/<job-id>/`, never a copy of it inside a worktree." For a helper add: "You are a helper subagent (`CLAUDE.md`, Who you are, 2), not the Chief of Staff and not an employee. Do exactly this task and stop. Change no tracked file; write only your output file (a QA helper also its `qa/` folder). A QA helper may install, build and run the product in the worktree and must leave `git status` there as it found it."
- **Goal**: the outcome, in one or two sentences, and which roadmap item it serves.
- **Worktree**: the path to work in, its branch, and the base commit. For a helper: the path to read.
- **Read first**: exact file paths (plan, spec, customer notes, prior work, skill files a helper must follow).
- **Definition of done**: checkable conditions. For a plan, its done criteria.
- **Constraints**: scope limits, things not to touch, deadline.
- **Progress** (employees only; helpers do not write `progress.md`): "Append to `jobs/<job-id>/progress.md` when you start and when you finish each step: what you did, the command, what came back."
- **Return**: what to hand back (files changed, summary, open questions, the line for the work log), written to `jobs/<job-id>/handback.md` in the hand-off format from `REVIEW.md`. Helpers write `review.md`, `quality.md`, `architecture.md` or `qa.md` (`review-2.md` and so on for a re-check), and every helper file ends with a line `Verdict: pass | pass with fixes | fail | skipped: <reason> | not performed: <reason>`. That line is how a later session knows the step finished.

Never override the model or effort set in an employee's role file.

## 4. Run

Update the board row first. An employee job: state `running`, and the runner. A fix round: state `fixing`. A helper: state `in-review`, and the helper's name in Next step (`rev-003, qual-003 running`); never overwrite the Runner column with a helper. Then check where you are:

```bash
test "${HERDR_ENV:-}" = 1 && echo herdr || echo plain
```

### Inside Herdr: one tab per running agent

The CEO runs the company in Herdr to watch every employee work and to step into any tab. One tab per agent is the CEO's standing, explicit request, which is what the vendored `herdr` skill asks for before tabs are created. That skill (`.claude/skills/herdr/SKILL.md`) is the authority on the CLI: read it before the first command of a session, and check the syntax your installed version accepts with `herdr tab` and `herdr agent`. Parse IDs from the JSON responses; never guess them. Do not use `herdr worktree`: the company manages worktrees itself.

1. **Tab.** Keep the working directory at the HQ root, so the new session loads `CLAUDE.md`, the employees and the skills:

   ```bash
   herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD" --label "<employee> <slug>" --no-focus
   ```

   Read the new tab's ID and its root pane's ID from `.result.tab` and `.result.root_pane`, and put the tab on the board row.
2. **Start the agent** in that pane. Herdr agent names must be unique among live agents and match `[a-z][a-z0-9_-]{0,31}`. Employees use their own name, with `-2`, `-3` when the same employee runs twice. Helpers use a short kind and the job's number or a short tag: `rev-003`, `qual-003`, `arch-003`, `qa-003`, with `-2` for a re-check.

   ```bash
   # an employee: the role file sets its model, effort and tools
   herdr agent start <agent-name> --kind claude --pane <pane_id> -- --agent <employee> --permission-mode acceptEdits
   # a read-only helper: a plain session
   herdr agent start <agent-name> --kind claude --pane <pane_id> -- --permission-mode acceptEdits
   # a QA helper that drives the browser
   herdr agent start <agent-name> --kind claude --pane <pane_id> -- --chrome --permission-mode acceptEdits
   ```

   `acceptEdits` lets the agent write files without asking. Shell commands the CEO has not allowed yet still ask, in that tab, and `.claude/settings.json` always asks before a push, a repo operation, or an edit to a product's main checkout. Its push rule matches on the word, so a commit message or a `git stash push` can trigger it too: that is a harmless extra prompt, not a reason to rephrase around it. If the CEO wants to approve every edit by hand, drop the flag. If `agent start` returns `agent_not_ready`, the session is waiting on a dialog: tell the CEO which tab needs them.
3. **Prompt it** with a pointer to the brief, and make sure it started:

   ```bash
   herdr agent prompt <agent-name> "Delegation from the Chief of Staff. Your brief is in jobs/<job-id>/brief.md. Read it and carry it out. When you are finished, write your hand-back to the file the brief names and stop." --wait --timeout 20000
   ```

   For a helper, begin the prompt with "You are a helper subagent, not the Chief of Staff (CLAUDE.md, Who you are, 2)." A `timeout` result is the good case: the agent started working and is still at it. `agent_prompt_stalled` means it may not have started: look with `herdr agent get` and `herdr agent read`, and never send the prompt a second time blind. The hand-back is a work product, not a workaround for reading the screen, so asking for it in the first prompt is right here.
4. **Wait** without blocking yourself. Run the wait as a background shell command, or call your shell tool with its longest timeout (600000 ms) and keep Herdr's timeout below it:

   ```bash
   herdr agent wait <agent-name> --timeout 540000
   ```

   - `timeout`: still working. Wait again, or work on something else meanwhile.
   - `blocked`: the agent is showing an approval or a question. Never answer it. Read what it asks (`herdr agent read <agent-name> --source recent-unwrapped --lines 60`), set the board row to `blocked`, tell the CEO which tab needs them and why, and do not wait on that agent again until the CEO says it is answered. `blocked` is a settled state, so waiting again returns at once.
   - `idle` or `done`: the job is finished only if the hand-back file also exists. No file: look with `agent get` and `agent read` before you do anything, then prompt once for the file.
5. **Fix rounds and resumes** go to the same agent in the same tab when it is still alive, because it still has its context: write `fix-N-brief.md` or `resume-N-brief.md`, name a new hand-back file in it (`fix-N-handback.md`), and prompt again. A stale hand-back from the earlier round must never be read as the new result.
6. **Close** a helper's tab as soon as you have read its output. Close an employee's tab only after its work is merged and its worktree removed. Close only tabs you created (`herdr tab close <tab_id>`), and leave a tab open when its work failed, is blocked, or the CEO is using it.

Several delegations can run at once: create the tabs, prompt them all, then wait on each. What may run in parallel is decided in the `worktree` skill.

### Plain terminal: in-process subagents

Delegate with the Agent tool to the employee's subagent type (a general-purpose subagent for a helper), passing the brief's text as the prompt. Independent delegations go out in one message so they run in parallel. Subagents cannot ask the CEO anything: questions come back in the hand-back. They die with your session, so a crash leaves their jobs `interrupted`, with `progress.md` and the worktree showing how far they got.

## 5. Collect

Read the hand-back file. Set the board row to `handed-back`, record any decision the employee returned in `context/decisions.md`, add a journal line, and continue with `REVIEW.md`: independent review, refinement check and QA where they apply, hand-off, merge. The employee's line goes into `context/log.md` only when the job closes, so unfinished or failed work is never logged as done. When the job is closed, take its row off the board. The job folder stays.
