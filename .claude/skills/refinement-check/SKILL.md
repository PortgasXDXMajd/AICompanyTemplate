---
name: refinement-check
description: Mandatory check after every code implementation and before any feature branch is pushed or merged. Runs the thermo-nuclear-code-quality-review and improve-codebase-architecture skills against the change, gets contained problems fixed on the branch, and raises wider ones with the CEO. Use when a developer hands back an implementation, or when the work log shows a pending review.
argument-hint: <project> <base> <branch>
---

# Refinement check

Working code is not the bar. After every implementation, two questions get asked while the change is fresh and cheap to fix: is this the cleanest way to build it, and did it leave the architecture better or worse?

Target: $ARGUMENTS

## The two skills behind it

Both are third-party, vendored in `.claude/skills/`, and marked user-invoked only, so you cannot call them through the Skill tool. Read their `SKILL.md` files and follow them as described here. Never edit them.

| Part | Skill file to read | Looks at |
|---|---|---|
| A. Code quality | `.claude/skills/thermo-nuclear-code-quality-review/SKILL.md` | The diff: abstraction quality, spaghetti growth, file sprawl, missed simplifications |
| B. Architecture | `.claude/skills/improve-codebase-architecture/SKILL.md` | The changed modules and their callers: shallow modules, leaky seams, poor locality |

The CEO can run either one directly at any time: `/thermo-nuclear-code-quality-review`, or `/improve-codebase-architecture projects/<name>` for a whole-codebase review. Always pass the project path, or it will review the HQ repo.

## Who runs it

The **Chief of Staff**, because the check needs helper subagents and may need the CEO. A developer never checks its own work:

- A delegated developer returns project, base, branch and changed files. The Chief of Staff runs the check.
- A developer in a `claude --agent` session finishes with self-review and ends its `context/log.md` line with `review pending: <project> <base> <branch>`. The next Chief of Staff session picks it up.

## Steps

1. **Scope.** `git -C projects/<name> diff --stat <base>...<branch>`. If base was not given, use `git -C projects/<name> merge-base <branch> <default branch>` and say so in the log line. Find the spec: a plan names it under "Why this matters". A plan that came from an audit has no spec, and the plan stands in for it everywhere below. Then:
   - No source code changed (docs, config, copy): log `refinement check: skipped, no code` and stop.
   - Under about 40 changed source lines and no new file: run part A only.
   - The spec says `Refinement: part A only`: run part A only.
2. **Review, in parallel.** Start two fresh general-purpose helper subagents. Neither may be the author, and both are read-only.
   - **Part A reviewer.** Tell it to read the skill file and follow it as its task. Give it: the skill file path from the table, the project path, base and branch, the spec, `context/engineering.md`, and the project's `CLAUDE.md`. It follows the skill against the diff and returns findings in the skill's priority order, each marked **blocker** or **note** against the skill's approval bar.
   - **Part B explorer.** Tell it to walk the code itself where the skill says to spawn a sub-agent, and to read the vocabulary file where the skill says to call the Skill tool. Give it: the skill file path from the table, `.claude/skills/codebase-design/SKILL.md` for the vocabulary, the project path, and the changed files plus their direct callers as the direction to explore. It follows step 1 of the skill only, applies the deletion test, and returns candidates rated `Strong`, `Worth exploring` or `Speculative`. The project's `CONTEXT.md` and `docs/adr/` are under `projects/<name>/`. Decisions recorded in ADRs are not re-litigated.

   This can run alongside the independent review in `REVIEW.md`. Merge the results and drop duplicates: both parts often flag the same pass-through wrapper.
3. **Sort every blocker and Strong candidate into one of two piles.** Notes, `Worth exploring` and `Speculative` items are never fixed now.
   - **Contained:** the fix touches only files in this change and alters no interface used outside them.
   - **Wider:** anything else, including the ambitious restructurings part A is told to look for.
4. **Fix the contained pile, once.** Re-delegate to the employee who wrote the change, with a brief that lists the findings and states: behaviour must not change, same branch, a separate commit, tests and lint must pass. If the Chief of Staff wrote the code, it makes the fix itself. Then run the project's test command yourself and start a fresh part A helper with the original blockers and the fix commit, to re-check only those. If tests fail or the fix left the scope, revert that commit and move the finding to the wider pile. One fix round per check. A second round means the spec or the design is the problem: take it to the CEO.
5. **Record the wider pile.** Append each item to `work/engineering/refinement-candidates.md`: project, date, files, one-line problem, proposed remedy, which part found it. Then:
   - One or two items: present them to the CEO in the hand-off under **Needs you**, with a recommendation.
   - Three or more, or the CEO wants to dig in: continue with step 2 of the architecture skill (the HTML report, scoped to these items). If the report cannot be opened where the CEO is, give the file path and the same content in chat.
   - For an item the CEO picks, grill it as the architecture skill's step 3 describes, then turn the outcome into a spec with the `feature` skill. Write `Refinement: part A only` in that spec so the refactor does not trigger another architecture pass, and the loop ends.
   - An item the CEO rejects with a reason that will still hold later gets an ADR, so it is not raised again. Any write into the product repo goes on a branch `chief-of-staff/<short-name>`, never the default branch.
6. **Log it.** One line in `context/log.md`: `refinement check: clean`, `fixed in place (N findings)`, `N candidates logged`, or `refactor spec NNN`, plus the project and branch. If this check answered a `review pending:` line, end yours with `review done: <project> <branch>`. The same line goes under **Checked** in the hand-off.

## The gate

A feature branch is not pushed, merged, or reported as done until its refinement check is logged. Pushing and merging still need the CEO's approval, and the hand-off asks for it.

Most checks end in `clean` or a small contained fix. That is the expected result, not a sign of looking too lightly. Do not manufacture findings, and do not soften real ones.
