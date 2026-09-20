---
name: new-project
description: Create a new product project for the company - grills the CEO on the tech stack, then creates a GitHub repo with a README and a CLAUDE.md recording that stack, cloned into projects/<name> and added to the registry in projects/README.md. Also use to register and clone a product repo that already exists. Use during onboarding and whenever the CEO wants to start a new product or codebase.
argument-hint: <project-name or existing repo URL>
---

# New project

Product code lives in its own GitHub repo, never in this HQ repo. `projects/` holds local clones and is gitignored apart from `projects/README.md`, which is the registry. Every project has its own `CLAUDE.md` stating the tech stack the CEO chose. The first software project also brings the company's first employee: the Senior Technical Adviser.

Input from the CEO: $ARGUMENTS

**Precondition.** If `context/company.md` says `STATUS: NOT ONBOARDED`, stop and run `onboard` first. Onboarding calls this skill at the right moment.

Run every command from the HQ repo root. Use `git -C projects/<name> ...` instead of `cd`, so later HQ commits do not land in the product repo.

## 1. Settle the details

Check the tools first: `gh --version` and `gh auth status`. Then get these, asking only for what is missing:

- **Name:** kebab-case, short, no spaces. Check it is not already in the registry or present under `projects/`.
- **Purpose:** one line. Take it from `context/company.md` when this is the main product.
- **New or existing:** if the CEO gave a URL or says the repo exists, go to step 4.
- **Owner:** the GitHub user or org. Default to the account from `gh api user --jq .login`. If `gh` is unavailable, ask the CEO.
- **Visibility:** `private` unless the CEO says `public`.

## 2. Settle the tech stack (new repo only)

The CEO chooses the stack. Your job is to make it a considered choice and to write it down where every future session will read it.

Call the Skill tool with "grilling" and follow it. The roots of the design tree are the rows of `project-claude-template.md` (next to this file): product form, language and runtime, framework, data store, auth, hosting, package manager, testing, lint and format, CI. Ask only about rows that apply, and let earlier answers decide which later questions exist (no data store question for a static site).

- Bring a recommended answer to every question, based on `context/company.md` (stage, hours per week, budget), what the CEO already knows well, and what the buyer needs. For a company before its first customer, recommend the boring, familiar option the CEO can debug themselves over the fashionable one, and say so.
- If the CEO names a stack up front, do not re-ask it. Grill only the gaps and any choice that conflicts with the constraints.
- The reason for each choice goes in the table's "Why / notes" column. That is the record.
- **House style.** If `context/engineering.md` says `STATUS: DEFAULTS`, add one last branch once language and framework are settled: show the CEO the defaults in that file and grill what they always and never want in code. Test: a reviewer could say whether a diff follows each rule. "Clean code" fails. "No function longer than one screen; no comments that restate the code" passes. Write the rules into its "House style" section and set `STATUS: SET YYYY-MM-DD`.
- Not a software project (content, a service, research)? Replace the Tech stack table with a `## Tools and formats` list, and delete the Commands and Structure sections and the `CONTEXT.md` / ADR line from the template.

Close with one playback: name, owner, visibility, the filled stack table, and, if `.claude/agents/senior-technical-adviser.md` does not exist yet, that this adds the Senior Technical Adviser as the first employee (newest Fable model, maximum effort: the most capable and most expensive setting, used for understanding code and writing plans, never for implementing). Creating a repo and hiring need CEO approval, and one yes to this playback is the shared-understanding confirmation and both approvals. It covers the initial push.

## 3. Create the repo (new repo only)

```bash
mkdir -p projects/<name>
git -C projects/<name> init -b main
# write projects/<name>/README.md and projects/<name>/CLAUDE.md (content below)
git -C projects/<name> add README.md CLAUDE.md
git -C projects/<name> commit -m "Initial commit: README and CLAUDE.md with tech stack"
gh repo create <owner>/<name> --<visibility> --source projects/<name> --remote origin --push
```

Two files only. `CLAUDE.md` is `project-claude-template.md` filled in with the stack from step 2. The README stays honest about the stage:

```markdown
# <Project name>

<Purpose, one or two sentences.>

## Who it is for
<The buyer, from context/company.md.>

## What it promises
<The promise, from context/company.md.>

## Status
Just started. Nothing to run yet.
```

Do not scaffold code, add a licence, or set up CI here. Record the decisions in `CLAUDE.md`; building them is the first spec (use the `feature` skill).

**If `gh` is missing or not authenticated:** still create the local repo and the first commit. Register the project with repo `not created yet` and status `local only`. Give the CEO these commands to finish:

```bash
# install gh from https://cli.github.com, then:
gh auth login
gh repo create <owner>/<name> --<visibility> --source projects/<name> --remote origin --push
```

When the CEO says it is done, verify with `git -C projects/<name> remote -v`, then set the registry row to `active` with the URL.

Then go to step 5.

## 4. Register an existing repo (existing repo only)

```bash
gh repo clone <owner>/<name> projects/<name>
# without gh: git clone <url> projects/<name>
```

Read its README and its `CLAUDE.md` if present, so the purpose line in the registry is accurate.

If it has no `CLAUDE.md`, or the one it has does not state the tech stack: work the stack out from the code yourself (manifests, lockfiles, config) and fill in `project-claude-template.md`, including Commands and Structure from what is actually there. Replace "Decided by the CEO on" with "Recorded from the existing code on YYYY-MM-DD, confirmed by the CEO". Ask the CEO only about what the code cannot tell you. Commit the file on a branch `chief-of-staff/add-claude-md`, show it to the CEO, and ask for the merge in the same message, recommending yes. Until it is merged, leave that branch checked out and write `CLAUDE.md pending merge` in the registry row. Change nothing else in the repo.

Before step 5, two things the new-repo path covers in step 2: if `.claude/agents/senior-technical-adviser.md` does not exist, tell the CEO this project adds the Senior Technical Adviser as the first employee (newest Fable model, maximum effort: the most expensive setting; it plans, it never implements) and get an explicit yes. And if `context/engineering.md` says `STATUS: DEFAULTS`, run the House style branch of step 2 now.

## 5. Make sure the Senior Technical Adviser exists (software projects only)

If `.claude/agents/senior-technical-adviser.md` is missing, then with the CEO's yes from step 2 or step 4, copy `senior-technical-adviser.md` (next to this file) there unchanged. Do not lower its `model: fable` or `effort: max`: the CEO's standing rule is that the adviser always runs on the newest Fable model at maximum effort. Add its row to `context/team.md` (owns `plans/`; reach it by delegation or `claude --agent senior-technical-adviser`) and note the hire in `context/decisions.md`. Claude Code picks up the new file within a few seconds. One adviser serves every project, so skip this step if the file is already there.

## 6. Record it

1. Add a row to the registry in `projects/README.md`: name, `owner/name` linked to the GitHub URL, purpose, status, today's date. Status values are listed in that file.
2. If this is the main product, mention it under Product in `context/company.md`.
3. Append a line to `context/log.md`.
4. Commit the HQ files you changed, by path, with the message `Add project <name>`: `projects/README.md`, `context/log.md`, and `context/company.md`, `context/engineering.md`, `context/team.md`, `context/decisions.md` or `.claude/agents/senior-technical-adviser.md` if touched. During onboarding, skip this commit: onboarding commits everything at the end.

## 7. Put the adviser to work

- **Existing repo with code:** recommend an audit to the CEO and say what it costs: the adviser is the expensive model. On a yes, first make the project readable, because the adviser may not install anything: default branch (or `chief-of-staff/add-claude-md`) checked out, clean, pulled, dependencies installed with the project's install command. Then delegate to `senior-technical-adviser` with a brief: audit `projects/<name>` at `standard` depth. It returns a findings table; bring that to the CEO, get their selection, and delegate again for the plans. The CEO can instead run it interactively with `claude --agent senior-technical-adviser`.
- **New, empty repo:** there is nothing to audit. The adviser's first job comes when the first spec is approved (`feature` skill): it turns the spec into plans.

If `senior-technical-adviser` cannot be delegated to yet, do not substitute a general-purpose subagent: ask the CEO to restart `claude`.

Report the repo URL and the local path to the CEO. When called from `onboard`, continue with onboard's next step.
