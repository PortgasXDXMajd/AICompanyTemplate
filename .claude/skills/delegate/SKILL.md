---
name: delegate
description: How the Chief of Staff hands a task to an employee or a helper and gets the result back. Covers the job record, the employee's worktree, the delegation brief, and the two ways to run it - as its own visible Herdr tab when the session runs inside Herdr, or as an in-process subagent otherwise. Use for every delegation, every fix round, every resume, and every review, quality, architecture or QA helper.
argument-hint: <employee or "helper"> <task>
---

# Delegate

Task: $ARGUMENTS

Every delegation follows the same five steps: record, worktree, brief, run, collect. Only "run" differs between Herdr and a plain terminal. Write each step down before you do it (`jobs/README.md`): that is what lets a new session pick up after a crash.

## 1. Record

```bash
python3 scripts/job.py --json new --employee <employee> --slug <slug> --task "<one line>" --repo <project|_hq|none>
```

This creates `jobs/<job-id>/` (job id `<YYYYMMDD>-<employee>--<slug>`) with a brief skeleton and an empty `progress.md`, adds the board row in state `briefed`, and writes the journal line. Helpers (reviewer, quality, architecture, QA) are steps inside the job they check, not jobs of their own: their files live in that job's folder. Work the Chief of Staff does itself is a job too: `--employee chief-of-staff`, runner `self`.

Every later state change goes through `python3 scripts/job.py set <job-id> --state <state> [--runner ...] [--next "..."]`, which also stamps the row and the journal. Never edit `jobs/BOARD.md` by hand.

## 2. Worktree

If the task changes files:

```bash
python3 scripts/worktree.py --json add --repo <project|_hq> --employee <employee> --slug <slug> --job <job-id>
```

It creates the worktree and writes its path, branch and base into the board row and the brief (`worktree` skill for the rules). Fix rounds and resumes go back into the worktree the job already has. Read-only helpers get no worktree; they are pointed at the one they check.

## 3. Brief

Fill in `jobs/<job-id>/brief.md`, which `job.py new` started (helpers: write `<name>-brief.md`, fix rounds: `fix-N-brief.md`, resumes: `resume-N-brief.md`). In this order:

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

```bash
python3 scripts/agent.py where        # prints "herdr" or "plain"
```

### Inside Herdr: one tab per running agent

The CEO runs the company in Herdr to watch every employee work and to step into any tab. One tab per agent is the CEO's standing, explicit request, which is what the vendored `herdr` skill asks for before tabs are created. `scripts/agent.py` wraps the Herdr CLI; the vendored skill (`.claude/skills/herdr/SKILL.md`) remains the reference when something behaves unexpectedly. Do not use `herdr worktree`: the company manages worktrees itself.

```bash
# an employee (the role file sets its model, effort and tools)
python3 scripts/agent.py --json start --job <job-id> --employee <employee>
# a helper: rev (review), qual (quality), arch (architecture), qa; brief defaults to jobs/<job-id>/<kind>-brief.md
python3 scripts/agent.py --json start --job <job-id> --helper rev
python3 scripts/agent.py --json start --job <job-id> --helper qa --chrome      # QA that drives the browser
```

`start` opens a tab at the HQ root (so the session loads `CLAUDE.md`, the employees and the skills), picks a unique agent name (`backend-engineer`, `backend-engineer-2`, `rev-003`), starts Claude Code in it, prompts it with a pointer to its brief, checks that it actually started working, and updates the board and the journal: an employee becomes the row's Runner with state `running`; a helper sets state `in-review` and is named in Next step, never in Runner.

- Agents start with `--permission-mode acceptEdits`, so they can write files without asking. Shell commands the CEO has not allowed yet still ask, in that tab, and `.claude/settings.json` always asks before a push, a repo operation, or an edit to a product's main checkout. Its push rule matches on the word, so a commit message or `git stash push` can trigger it too: a harmless extra prompt, not a reason to rephrase. Pass `--ask-edits` if the CEO wants to approve every edit by hand.
- Exit code 4 means the agent needs the CEO (a dialog at startup, or `blocked`): tell the CEO which tab. Exit code 5 means the prompt may not have started a turn: look with `agent.py read`, and never prompt a second time blind.

Then wait, without blocking yourself: run it as a background shell command, or with your shell tool's longest timeout (600000 ms):

```bash
python3 scripts/agent.py --json wait <agent-name> --expect jobs/<job-id>/handback.md
```

- `working`: wait again, or work on something else meanwhile.
- `blocked` (exit code 4): the agent is showing an approval or a question. Never answer it. `python3 scripts/agent.py read <agent-name>` shows what it asks; set the job to `blocked`, tell the CEO which tab needs them and why, and do not wait on that agent again until the CEO says it is answered.
- `idle` or `done`: finished only if the result file exists (`result_file_exists`). No file: read the pane before you do anything, then prompt once for the file.

**Fix rounds and resumes** go to the same live agent, which still has its context: write `fix-N-brief.md` or `resume-N-brief.md`, name a new result file in it (`fix-N-handback.md`), set the job to `fixing`, and run `python3 scripts/agent.py prompt <agent-name> --brief jobs/<job-id>/fix-N-brief.md`. A stale hand-back from the earlier round must never be read as the new result.

**Close** a helper's tab as soon as you have read its output, and an employee's tab only after its work is merged and its worktree removed: `python3 scripts/agent.py close --tab <tab_id>`. Close only tabs you created, and leave a tab open when its work failed, is blocked, or the CEO is using it.

Several delegations can run at once: start them all, then wait on each. What may run in parallel is decided in the `worktree` skill.

### Plain terminal: in-process subagents

Set the row first: `python3 scripts/job.py set <job-id> --state running --runner subagent` (a helper: `--state in-review --next "rev running"`; a fix round: `--state fixing`). Then delegate with the Agent tool to the employee's subagent type (a general-purpose subagent for a helper), passing the brief's text as the prompt. Independent delegations go out in one message so they run in parallel. Subagents cannot ask the CEO anything: questions come back in the hand-back. They die with your session, so a crash leaves their jobs interrupted, with `progress.md` and the worktree showing how far they got.

## 5. Collect

Read the hand-back file. `python3 scripts/job.py set <job-id> --state handed-back`, record any decision the employee returned in `context/decisions.md`, add a journal line, and continue with `REVIEW.md`: independent review, refinement check and QA where they apply, hand-off, merge. The employee's line goes into `context/log.md` only when the job closes, so unfinished or failed work is never logged as done. When the job is closed, `python3 scripts/job.py close <job-id> --outcome merged --log "<the employee's log line>"` takes the row off the board, writes `closed.md`, and appends the line to `context/log.md` (`--outcome dropped` logs nothing). The job folder stays.
