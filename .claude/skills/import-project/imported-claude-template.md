# `<Project name>`

`<What it does and for whom. Two sentences, confirmed by the CEO.>`

Imported codebase: recorded from the code at commit `<short sha>` on YYYY-MM-DD, confirmed by the CEO. Evidence and detail are in HQ at `plans/<name>/PROFILE.md`: read the sections your task touches before you change anything.

## The rule for working here

New code looks like the code around it. Before you write anything, find the closest existing example of the same kind of thing (an endpoint, a screen, a migration, a test) and follow its shape: where the files go, how things are named, how errors are handled, how it is tested. Where this file and the profile are silent, the surrounding code decides. Where this codebase differs from HQ `context/engineering.md` on how code is written, this file wins. Company process still applies: your own worktree, test first, reviews, no merge, no push. Do not reformat, rename, upgrade or tidy code you were not asked to change.

## Tech stack

Do not add a language, framework or major dependency that is not listed here without CEO approval. When one is approved, update this table in the same change.

| Layer | Choice | Version | Notes |
| --- | --- | --- | --- |
| Product form | | | |
| Language / runtime | | | |
| Framework | | | |
| Data store | | | |
| Auth | | | |
| Hosting / deploy | | | |
| Package manager | | | |
| Testing | | | |
| Lint / format / types | | | |
| Hands-on QA | `<Chrome via Claude Code, Playwright, Maestro + emulator, ...>` | | see the `qa-check` skill in HQ |
| CI | | | |

<!-- Delete rows that do not apply. Add rows for anything else that matters (payments, email, queues, AI provider, ...). -->

## Commands

Verified on import unless marked otherwise. Baseline on import: `<tests: N passed, N failed (names in the profile); lint: N warnings>`. You are measured against that baseline, not against zero, and you do not fix old failures unless your task says so.

- Install:
- Run locally:
- Test (all):
- Test (one file or case):
- Lint / format / type-check:
- Build:
- Database (migrate, seed, reset):

## Structure

| Path | What lives there |
| --- | --- |
| | |

`<Where the files of a new endpoint, screen, model or migration go. Which folders are generated or vendored and must not be edited by hand.>`

## Services and data

- `<Each data store and external service: what it is for, which env variable names configure it, what to use locally.>`
- **Never from a dev machine:** `<production database, live payments, real email, ...>`

## How this codebase does things

Each rule is checkable in a diff and names a file to copy from.

1. `<Rule.>` Example: `<path>`

## Decided with the CEO on import

- **Tests:** `<test-first with the project's own test tools; what to do where the code has no tests yet>`
- **Differences from company standards:** `<each one, and which way was chosen>`
- **Must not change:** `<public APIs, URLs, schemas, contracts with other systems>`
- **Off limits:** `<folders and files nobody touches without asking>`

## Delivery

- Default branch: `<name>`. Changes ship by `<local merge by the Chief of Staff | pull request>`. Required checks: `<...>`
- `<Does a merge to the default branch deploy to production? If yes: a merge approval is a deploy approval.>`
- Commit messages: `<the format this repo uses, with an example>`
- Each task is built in its own git worktree, on a branch named `<employee>/<short-name>`. Nothing is committed straight to the default branch.

## Company

Run from a separate HQ repo, where sessions start. Work happens in worktrees under HQ `worktrees/<name>/`; `projects/<name>/` is the main checkout and stays on the default branch. Specs: HQ `specs/`. Plans and profile: `plans/<name>/`. Quality bar: `REVIEW.md`.
