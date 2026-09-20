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
- Branches are named `<employee>/<short-name>`. Nothing is committed straight to the default branch.
- <Project-specific rules from the CEO, if any.>

## Company

This repo belongs to a company run from a separate HQ repo. Sessions normally start in HQ and work here under `projects/<name>/`. Company-wide engineering standards are in HQ at `context/engineering.md`, specs in `specs/`, the quality bar in `REVIEW.md`.
