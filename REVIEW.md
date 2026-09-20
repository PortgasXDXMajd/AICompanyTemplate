# Review Standard

Nothing reaches the CEO, a customer, or a product repo's default branch until it passes this file. The point is to catch problems while they are cheap.

## 1. Self-review (always, by whoever did the work)

Before you hand anything back, check:

- [ ] It meets every condition in the definition of done from the brief, spec or plan. If one is not met, say which and why.
- [ ] It serves the current goal in `ROADMAP.md`, or the CEO explicitly asked for it anyway.
- [ ] Claims about customers or the market cite a file in `customers/`, or are labeled as assumptions.
- [ ] You ran it. Code was executed and tested, links were opened, numbers were recomputed. "Should work" is not done.
- [ ] Code follows `context/engineering.md` and stays inside the tech stack in the project's `CLAUDE.md`. Test and lint output is included.
- [ ] Nothing secret is in the repo: no API keys, passwords, or customer personal data beyond what the work needs.
- [ ] It is the smallest version that does the job. Extra scope was cut or moved to `ROADMAP.md` under Next or Later.
- [ ] Files are in the right folder (see the table in `CLAUDE.md`) and you only changed files you own.

## 2. Independent review (for anything that matters)

Required when the work will be seen outside the company, changes a product repo, or sets direction (positioning, pricing). Specs and plans are the exception: the grilling that produced a spec is its review, and a plan is held to the quality bar in the `improve` skill's plan template.

The Chief of Staff hands the output to a **fresh general-purpose subagent (not an employee, and not whoever did the work)**, giving it only: this file, the spec or brief, the plan if the work executed one, and the output. When there is a plan, its done criteria are the definition of done for question 1; the spec is context, and spec conditions assigned to other plans are not failures. For code it also gets `context/engineering.md`, the project's `CLAUDE.md`, and the project path, base and branch. The reviewer did not see the reasoning, so it judges the result the way a customer or the CEO would.

The reviewer answers:

1. Does the output meet the definition of done? Go through the conditions one by one.
2. What is wrong, missing, or unverified? Rank by severity.
3. What would the buyer described in `context/company.md` think of this?
4. Code only: which rule in `context/engineering.md` or the project's tech stack does the diff break? Name the rule and the line.
5. Verdict: **pass**, **pass with fixes** (list them), or **fail** (say what to redo).

The author fixes what the reviewer found. Two failed rounds means the brief or spec is the problem: go back to the CEO with the question instead of a third attempt.

## 3. Refinement check (code only)

Every code implementation then goes through the `refinement-check` skill: a strict code quality review and an architecture pass on what changed. It can run alongside the independent review. Contained problems are fixed on the branch; wider ones go to the CEO. A feature branch is not pushed, merged, or reported as done until the check is logged in `context/log.md`. A spec marked `Refinement: part A only` skips the architecture part.

A log line containing `review pending: <project> <base> <branch>` comes from a developer who worked directly with the CEO. Unless a later line says `review done:` for the same branch, section 2, and for code section 3, are still owed on that work. The Chief of Staff runs them before any other work and logs `review done: <project> <branch>`.

## 4. Handing work to the CEO

Lead with the result, then what the CEO needs to decide. Format:

- **Done:** what now exists, with file paths or a demo link.
- **Checked:** how it was verified, what the reviewer said, and the refinement check line.
- **Not done / risks:** anything cut, unverified, or uncertain. Be specific.
- **Needs you:** decisions or approvals required, each as a question with a recommendation. For code this always includes whether to merge `<branch>` into the default branch.

Keep it short. The CEO can open the files.

## 5. When the CEO rejects work

Record why in `context/decisions.md`. If the same kind of rejection happens twice, change the process: tighten the employee's role file, this checklist, `context/engineering.md`, or the spec template. Fix the system, not only the instance.
