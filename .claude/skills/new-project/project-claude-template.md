# <Project name>

<Purpose, one or two sentences.>

## Tech stack

Decided by the CEO on YYYY-MM-DD. Do not add a language, framework or major dependency that is not listed here without CEO approval. When one is approved, update this table in the same change.

| Layer | Choice | Why / notes |
|---|---|---|
| Product form | <web app, API, CLI, mobile app, browser extension, ...> | |
| Language / runtime | | |
| Framework | | |
| Data store | | |
| Auth | | |
| Hosting / deploy | | |
| Package manager | | |
| Testing | | |
| Lint / format | | |
| Hands-on QA | <Chrome via Claude Code, Playwright, Maestro + emulator, ...> | see the `qa-check` skill in HQ |
| CI | | |

<!-- Delete rows that do not apply. Add rows for anything else the CEO decided (payments, email, AI provider, ...). -->

## Commands

_Not set up yet. The first spec scaffolds the project and fills these in._

- Install:
- Run locally:
- Test:
- Lint / format:

## Structure

_Filled in once code exists: where things live and what goes where._

## Conventions

- Domain language lives in `CONTEXT.md` (a glossary, created when the first term is settled). Hard-to-reverse decisions live in `docs/adr/`.
- Each task is built in its own git worktree, on a branch named `<employee>/<short-name>`. Nothing is committed straight to the default branch.
- <Project-specific rules from the CEO, if any.>

## Company

This repo belongs to a company run from a separate HQ repo. Sessions start in HQ. Work happens in worktrees under HQ `worktrees/<name>/`; `projects/<name>/` is the main checkout and stays on the default branch. Company-wide engineering standards are in HQ at `context/engineering.md`, specs in `specs/`, the quality bar in `REVIEW.md`.
