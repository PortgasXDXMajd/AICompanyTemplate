---
name: feature
description: Turn a feature idea or change request into an approved spec. Grills the CEO with the grilling skill until the design is settled, then writes specs/NNN-name.md and puts it on the roadmap. Use when the CEO wants to add, change or build something, before any implementation starts.
argument-hint: <feature idea>
---

# New feature

Nothing gets built from a one-line idea. This skill turns the idea into a spec the CEO has approved, so whoever builds it does not have to guess.

The idea: $ARGUMENTS

**Precondition.** If `context/company.md` says `STATUS: NOT ONBOARDED`, stop and run `onboard` first.

## 1. Find the facts yourself

Before asking the CEO anything, read what already answers it:

- Which project this belongs to: `projects/README.md`. If it needs a new project, run `new-project` first.
- That project's `CLAUDE.md` (tech stack, conventions), its `CONTEXT.md` and `docs/adr/` if they exist, and the code the feature will touch.
- Evidence for the problem in `customers/` and `customers/insights.md`.
- Related specs in `specs/` and past decisions in `context/decisions.md`.

## 2. Grill

Call the Skill tool with "grilling" and follow it. These are the roots of the design tree. Bring a recommended answer to each, based on what you read:

1. **Goal fit.** Does this serve the current goal in `ROADMAP.md`? If not, say so in the first round and recommend parking it in Later. The CEO can overrule; record that in `context/decisions.md`.
2. **Problem.** Who has it, and what is the evidence? No file in `customers/` backs it means it is an assumption, and the spec says so.
3. **Outcome.** What is true for the buyer when this ships?
4. **Scope.** The smallest version that delivers the outcome, and what is deliberately left out.
5. **Definition of done.** Checkable conditions, including the behaviours the tests must prove and, for anything a user sees or touches, the flows hands-on QA will walk through.
6. **Approach.** Only the decisions that are expensive to reverse: data model, interfaces other code depends on, third-party services. Stay inside the project's tech stack; a new language, framework or major dependency is its own question and needs a reason.
7. **Risks.** What could make this fail or take three times as long?

For a code project, when a term is fuzzy or new, call the Skill tool with "domain-modeling" to sharpen it, but do not write into the product repo from here. List the settled terms under "Domain terms" in the spec's Approach section. The developer adds them to `CONTEXT.md` on the feature branch.

Do not write the spec until the CEO confirms you have a shared understanding.

## 3. Write the spec

1. Copy `specs/_template.md` to `specs/NNN-short-name.md` with the next free number. Fill every section from the grilling. One page is the target; if it needs more, propose splitting it.
2. Show it to the CEO. The grilling was the spec's review, so no independent review is needed first. On approval, set `Status: approved`.
3. **Code projects: get the plans.** First make the project readable, because the adviser may not install or check out anything: main checkout on the default branch, clean, pulled, dependencies installed with the project's install command. Commit the approved spec to HQ first, so the adviser's worktree contains it. Then delegate to `senior-technical-adviser` with the `delegate` skill (it gets an HQ worktree) and this brief: spec to plans for `specs/NNN-short-name.md` in `projects/<name>`. It writes one plan per employee-sized task under `plans/<project>/` in that worktree, each with an owner. Look the plans over, merge the branch into HQ, and remove the worktree. On a project with no code yet it returns only the scaffold plan; delegate again after that is merged. If it returns questions, put them to the CEO and delegate again. If the adviser's role file is missing, run step 5 of `new-project` first. If it exists but cannot be delegated to, ask the CEO to restart `claude`; do not substitute a general-purpose subagent.
4. Add the item to `ROADMAP.md`: under **Now** if there is room (three items at most), otherwise **Next**, linking the spec and its plans. Owners come from the plans, or from `context/team.md` for non-code work. If nobody owns the work, the Chief of Staff does it, or propose a hire if it is clearly recurring.
5. Append a line to `context/log.md`, log any overruled recommendation in `context/decisions.md`, and commit with `Spec NNN: <title>`. The plans arrive through the merge of the adviser's branch.

Then route each plan to its owner with the `delegate` skill, in the order the plan index gives, each in its own worktree. Plans whose dependencies are merged and whose in-scope files do not overlap can run in parallel; the rest wait. A plan marked `unowned` follows the rule in `CLAUDE.md`: the Chief of Staff executes it in a `chief-of-staff` worktree, or proposes the hire if the role passes the four tests in `hire`. Every implementation goes through `REVIEW.md`: independent review, refinement check, and hands-on QA where a user sees or touches the result.
