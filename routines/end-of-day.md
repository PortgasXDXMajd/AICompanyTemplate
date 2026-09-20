# End of day

- **Trigger:** the CEO says "close the day", "wrap up", or stops for the day
- **Owner:** Chief of Staff
- **Inputs:** every file in `context/journal/` since the last one that ends in a day summary (a day nobody closed is closed now), `jobs/` (board and the folders of jobs touched in those days), `context/decisions.md`, `context/log.md`, every `CLAUDE.md` (HQ and `projects/*/CLAUDE.md`), role files in `.claude/agents/`, `context/engineering.md`
- **Output:** a true job board, a day summary in the journal, approved edits to the instruction files, one commit

The point is that tomorrow's sessions start faster and make fewer mistakes than today's: nothing in flight is forgotten, and what the company learned today is in the files every session reads.

## Steps

1. **Settle the board.** Run the `job-status` skill (`python3 scripts/status.py` underneath). `python3 scripts/journal.py unclosed` lists the days that were never closed. Every open job gets a true state and a next step. Nothing is left `running` that is not running.
2. **Collect the day's lessons.** Read the journal files from the inputs and, for each job touched in them, `progress.md`, the hand-back, `review.md`, `quality.md`, `architecture.md`, `qa.md` and the fix briefs. Look for what cost time or quality:
   - the same review, quality or QA finding showing up in more than one job
   - something an employee had to discover that a file could have told it: a command, a path, a convention, a gotcha, a test account
   - a question an employee returned, or a STOP condition it hit, because a brief, plan or spec left something out
   - work the CEO rejected or redirected, and why (`context/decisions.md`)
   - an instruction that was ignored, misread, or contradicted by another file

   Each lesson needs evidence: a job id, a file, a journal line. No evidence, no lesson. At most three changes a day: pick the ones that would have saved the most. Removing instructions that nobody seems to need is a weekly-review question, because one quiet day proves nothing.
3. **Put each lesson in the narrowest place that every session which needs it will read:**
   - facts about one product (commands, structure, gotchas, test accounts, QA notes) → that project's `CLAUDE.md`
   - how one role should work → its role file in `.claude/agents/`
   - how code is written everywhere → `context/engineering.md`
   - how a procedure runs → the wrapper skill or routine (never a third-party skill)
   - only what every session in the company must know → HQ `CLAUDE.md`
4. **Clean the instruction files today's lessons touched**: HQ `CLAUDE.md` and `projects/<name>/CLAUDE.md`, never the copies under `worktrees/` and never a third-party skill. (The weekly review does a full pass over all of them.) Remove:
   - **duplicates**: keep the rule in the file that owns it, and point to it from elsewhere only if needed
   - **contradictions**: the latest CEO decision in `context/decisions.md` wins; if that does not settle it, ask
   - **stale facts**: a path, command or name that no longer exists (check by looking, not by running installs or builds in a main checkout); fix or delete
   - **noise**: anything a capable agent would do right without being told, and anything that was only true for one finished task

   `python3 scripts/doctor.py budgets` measures them and `python3 scripts/doctor.py refs` finds mentions of paths that no longer exist. Budgets: HQ `CLAUDE.md` under about 1,800 words, a project's `CLAUDE.md` under about 800 (1,200 for an imported codebase), a role file under about 60 lines, `context/engineering.md` under about 700 words. If a file is over, something moves out to where it belongs. HQ `CLAUDE.md` is loaded by every session and every subagent: it is the most expensive place to put a sentence.
5. **Guardrails.** These change only when the CEO says so in plain words, never as "cleanup": in HQ `CLAUDE.md` the sections "Who you are", "Start of session", "Rules for everyone", "CEO approval required" and the journal and job-board rules; the review, refinement, test-first and QA gates in `REVIEW.md` and `context/engineering.md`; and any tech stack table. A proposed change to one of these never rides along in the list of step 6: put it to the CEO as its own question, quoting the current text and the new text. Do not water a rule down to make a finding go away.
6. **Show the CEO the changes** as a short list: file, the change, the reason, the evidence. Apply what they approve. HQ files are edited in the main checkout. A project's `CLAUDE.md` is a product repo file: edit it in a `chief-of-staff` worktree and ask for the merge; the CEO approving the diff is its review. To keep that cheap, collect a project's lessons in `work/engineering/claude-md-lessons.md` during the week and apply them in one worktree at the weekly review, unless a lesson would stop tomorrow's work from going wrong. If the CEO is not there, apply nothing: write the proposals to `routines/reviews/YYYY-MM-DD-end-of-day.md` and put "review end-of-day proposals" on tomorrow's list.
7. **Close the journal.** `python3 scripts/journal.py close "<done, open, blocked, first thing tomorrow>"` appends the `## Day summary` block that marks the day as closed.
8. Run `python3 scripts/doctor.py` and fix what it finds. **Commit** HQ by path: `context/`, `jobs/`, `ROADMAP.md`, the instruction files you changed, `.claude/agent-memory/`. Message: `End of day YYYY-MM-DD`.
9. Tell the CEO in five lines or fewer what is open for tomorrow and what, if anything, is waiting on them.

Be strict about step 4 and honest about step 2. A day with no lessons is fine. An instruction file that grows every day is a failure of this routine.
