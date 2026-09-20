# Review Standard

Nothing reaches the CEO, a customer, or a product repo's default branch until it passes this file. The point is to catch problems while they are cheap. Review happens in the employee's worktree, before anything is merged. Every helper below is started with the `delegate` skill, and its output stays in the job's folder under `jobs/`.

## 1. Self-review (always, by whoever did the work)

Before you hand anything back, check:

- [ ] It meets every condition in the definition of done from the brief, spec or plan. If one is not met, say which and why.
- [ ] It serves the current goal in `ROADMAP.md`, or the CEO explicitly asked for it anyway.
- [ ] Claims about customers or the market cite a file in `customers/`, or are labeled as assumptions.
- [ ] You ran it. Code was executed and tested, links were opened, numbers were recomputed. "Should work" is not done.
- [ ] Code was built test-first (`tdd` skill) and follows `context/engineering.md` and the tech stack in the project's `CLAUDE.md`. The failing run and the passing run are in `progress.md`; the final test and lint output is in the hand-back.
- [ ] Nothing secret is in the repo: no API keys, passwords, or customer personal data beyond what the work needs.
- [ ] It is the smallest version that does the job. Extra scope was cut or moved to `ROADMAP.md` under Next or Later.
- [ ] Files are in the right folder (see the table in `CLAUDE.md`), everything you changed is in your worktree and committed, and you only changed files you own.

## 2. Independent review (for anything that matters)

Required when the work will be seen outside the company, changes a product repo, or sets direction (positioning, pricing). Three exceptions: an edit to a project's `CLAUDE.md` from the end-of-day routine is reviewed by the CEO approving the diff; and specs and plans: the grilling that produced a spec is its review, and a plan is held to the quality bar in the `improve` skill's plan template.

The Chief of Staff hands the output to a **fresh helper (not an employee, and not whoever did the work)**, giving it only: this file, the spec or brief, the plan if the work executed one, the job's `progress.md` and hand-back, and the output. When there is a plan, its done criteria are the definition of done for question 1; the spec is context, and spec conditions assigned to other plans are not failures. For code it also gets `context/engineering.md`, the project's `CLAUDE.md`, the `tdd` skill's path, and the worktree path, base and branch. The reviewer did not see the reasoning, so it judges the result the way a customer or the CEO would. It changes nothing and writes `review.md`, ending in a `Verdict:` line. Set the board row to `in-review` first.

The reviewer answers:

1. Does the output meet the definition of done? Go through the conditions one by one.
2. What is wrong, missing, or unverified? Rank by severity.
3. What would the buyer described in `context/company.md` think of this?
4. Code only: which rule in `context/engineering.md` or the project's tech stack does the diff break? Name the rule and the line.
5. Code only: were the tests written first, and are they worth keeping? Check the red and green runs recorded in `progress.md`, that tests sit at the seams the plan names (no plan: the seam the developer recorded in `progress.md` before the first test), and the `tdd` skill's anti-patterns: coupled to the implementation, tautological, or written in bulk after the fact. Would each new test fail if the change were reverted?
6. Verdict: **pass**, **pass with fixes** (list them), or **fail** (say what to redo).

The author fixes what the reviewer found, in the same worktree. Two failed rounds means the brief or spec is the problem: go back to the CEO with the question instead of a third attempt.

## 3. Refinement check (code only)

Every code implementation then goes through the `refinement-check` skill: a strict code quality review and an architecture pass on what changed. It can run alongside the independent review. Contained problems are fixed on the branch; wider ones go to the CEO. A spec marked `Refinement: part A only` skips the architecture part. This is where refactoring happens: the test-first loop deliberately leaves it out.

## 4. Hands-on QA (anything a user sees or touches)

Passing tests do not show that a screen makes sense. After the fixes from sections 2 and 3 are in, the `qa-check` skill runs the real thing from the worktree and uses it the way a customer would: a web app in a real browser, a mobile app in an emulator or simulator, an API or CLI through its real entry point. Set the board row to `in-review` and name the QA helper in Next step.

- QA always leaves `qa.md` with a verdict. No user-facing surface changed (a refactor, a migration, docs): `Verdict: skipped: no user-facing surface`. Tools not available: `Verdict: not performed: <what is missing>`, and the hand-off says so. It never implies QA happened.
- Blockers go back for a fix round: at most two, then the CEO decides. After a QA fix round the independent reviewer re-checks that commit only (`review-2.md`), and the refinement check is re-run only if the fix adds a file or changes more than about 40 lines.

A feature branch is not pushed, merged, or reported as done until sections 2 to 4 each have their file with a verdict in the job folder.

## 5. Handing work to the CEO

Write the hand-off to `jobs/<job-id>/handoff.md` and set the board row to `awaiting-merge` before you present it, so a new session knows what the CEO was asked. Lead with the result, then what the CEO needs to decide. Format:

- **Done:** what now exists, with file paths or a demo link.
- **Checked:** how it was verified: the reviewer's verdict, the refinement check line, and the QA result with its evidence.
- **Not done / risks:** anything cut, unverified, or uncertain. Be specific.
- **Needs you:** decisions or approvals required, each as a question with a recommendation. For code this always includes whether to merge `<branch>` into the default branch. After the CEO's yes, the Chief of Staff merges and removes the worktree (`worktree` skill).

Keep it short. The CEO can open the files. For specced work the Chief of Staff also adds the entry in `demos/`, from the QA evidence and the hand-back.

## 6. When the CEO rejects work

Record why in `context/decisions.md`. If the same kind of rejection happens twice, change the process: tighten the employee's role file, this checklist, `context/engineering.md`, or the spec template. The end-of-day routine looks for exactly these patterns. Fix the system, not only the instance.
