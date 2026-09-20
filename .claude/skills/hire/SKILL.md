---
name: hire
description: Add a new AI employee to the company. Checks that the role is justified, defines its mission, owned files and definition of done with the CEO, then creates the subagent in .claude/agents/ and updates context/team.md. Also covers changing or removing an employee. Use when the CEO asks to hire, add, change or remove an employee, or when recurring work has no owner.
argument-hint: <role, e.g. "growth marketer">
---

# Hire an employee

An employee is a Claude Code subagent: one file in `.claude/agents/`. The Chief of Staff delegates to it based on its `description`, and the CEO can work with it directly via `claude --agent <name>`.

Role requested: $ARGUMENTS

**Precondition.** If `context/company.md` says `STATUS: NOT ONBOARDED`, stop. Tell the CEO a hire needs a company first, run `onboard`, and at its hiring step evaluate the role the CEO asked for before recommending a different one.

## 1. Check the role is real

A role is justified only if all four hold. If one fails, say so plainly and offer the alternative.

| Test | If it fails |
|---|---|
| **Recurring work.** This kind of task will come up again and again, and it serves the current goal or a Now/Next roadmap item. | One-off work: the Chief of Staff just does it. |
| **Owned output.** There are files or folders this employee will be responsible for. | It is a persona with no job. Do not create it. |
| **Checkable done.** You can state what finished, good work looks like for this role. | Define that first, or the role cannot be reviewed. |
| **No overlap.** Nobody in `context/team.md` already owns this. | Widen the existing employee's role file instead. |

Be wary of hiring a whole org chart early. Each employee adds routing decisions and another file to keep accurate. Two sharp roles beat six vague ones.

## 2. Define the job with the CEO

Draft these yourself from `context/company.md` and `ROADMAP.md`, then show the CEO and adjust. Ask questions only where your draft is a guess.

- **Name:** kebab-case role name (`growth-marketer`, `backend-engineer`, `customer-researcher`). Role names route better than human names.
- **Description:** the routing rule the Chief of Staff uses. Start with "Use for" and list the concrete task types. Add what it is *not* for if a neighbour role exists.
- **Mission:** one sentence tying the role to the buyer and the current goal.
- **Owns:** the files and folders it may edit. Everything else is read-only for it.
- **Delivers:** the recurring outputs, and where each one goes.
- **Definition of done:** role-specific checks, on top of `REVIEW.md`.
- **Boundaries:** what it must not do. Actions needing CEO approval are already in `CLAUDE.md`; add role-specific ones.
- **Tools:** leave `tools` out to inherit everything, which suits builders. Restrict it for roles that should not run commands or change code, for example `tools: Read, Grep, Glob, Write, Edit, WebSearch, WebFetch` for a researcher or writer. Do not grant the `Agent` tool: employees do not delegate, handoffs go through the Chief of Staff.
- **Developer roles** (backend, frontend, mobile, anything that writes code): the role file must tell the employee to read `context/engineering.md` and the project's `CLAUDE.md` before starting, and to hand back the project, base, branch and changed files so the `refinement-check` skill can run. Which developer roles to hire is a question for the Senior Technical Adviser: its plans name the owner each task needs. The template has a block for this; keep it for developers and delete it for everyone else.
- **Isolation:** leave the `isolation` field out. Every employee works in a worktree the company creates under `worktrees/` (`worktree` skill); Claude Code's built-in `isolation: worktree` would put it in an HQ-only worktree somewhere else, without the product code.
- **Model:** `opus`. The CEO's standing rule is that every hire runs on the newest Opus model; the `opus` alias always points at it, so never pin a dated model ID. The only exception is the Senior Technical Adviser, which runs on `fable` at `effort: max` and is created by the `new-project` skill, not here. Change a hire's model only if the CEO asks.

## 3. Get approval

Show the CEO the complete role file. Hiring needs an explicit yes.

## 4. Create the employee

1. Run `python3 scripts/team.py add <name> --owns "<files and folders>"` (add `--developer` for a role that writes code; without it the engineering block is removed). It copies `employee-template.md` to `.claude/agents/<name>.md` with the name set and adds the roster row. Then fill every `<FILL: ...>` placeholder; `python3 scripts/team.py list` shows how many are left, and `python3 scripts/doctor.py` fails while any remain. Delete guidance comments. Keep the file under about 60 lines: a role file is a job description, and the company context already arrives through `CLAUDE.md`.
2. Check the row the script added to `context/team.md`: what the employee owns is what the Chief of Staff routes by.
3. Append the hire and its reason to `context/decisions.md`, add a line to `context/log.md`, and commit with `Hire <name>`.
4. Claude Code picks up a new file in `.claude/agents/` within a few seconds, no restart needed. If delegating to `<name>` still fails after that, ask the CEO to restart `claude`.

## 5. First assignment

Pick one small, real task from the roadmap. For a developer that is normally the next plan in `plans/<project>/` that the adviser marked `unowned` for this role: set the owner in the plan and the index first. Set `owner: <name>` on its roadmap item (add the item to **Now** if it is not on the roadmap yet), and delegate it with the `delegate` skill. If the employee is not available, do not substitute a general-purpose subagent: ask the CEO to restart `claude` and say "give `<name>` its first assignment". When the task returns, put it through `REVIEW.md`. Whatever the review catches that better instructions would have prevented, fix in the role file now. A role file is tuned by its first few tasks, not by the draft.

## Changing or removing an employee

- **Change:** edit `.claude/agents/<name>.md` and the row in `context/team.md`. Log why in `context/decisions.md`. Do this whenever the same review problem shows up twice.
- **Remove:** needs CEO approval. Delete the role file, remove the row from `context/team.md`, and reassign what it owned. Keep `.claude/agent-memory/<name>/` unless the CEO wants it gone: a rehire can use those notes. Log the decision.
