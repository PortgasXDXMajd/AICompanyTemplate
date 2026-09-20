---
name: markdown
description: Write Markdown that produces no markdownlint warnings, and fix files that do. Use whenever you create or edit any .md file in this repo (skills, role files, specs, plans, briefs, hand-backs, reviews, README files, CLAUDE.md), when the CEO mentions Markdown warnings, lint, MD0xx rules, table spacing or code fences without a language, and after pulling template updates.
argument-hint: "[files to fix, or --all]"
---

# Markdown without warnings

Every Markdown file the company owns must be clean under markdownlint, the linter behind the warnings in VS Code. The rules are in `.markdownlint-cli2.jsonc`: all defaults, except that line length is off (prose is not hard-wrapped here) and tables use the `compact` style.

Files: $ARGUMENTS

## It fixes itself

A hook in `.claude/settings.json` runs `scripts/mdfix.py` on every `.md` file right after you write or edit it. It silently repairs what a machine can repair. If something is left that only the author can decide, the hook hands you the list: fix those lines in the same turn. After the hook has touched a file, read it again before your next edit, because it may have changed on disk.

By hand, from the HQ root:

```bash
python3 scripts/mdfix.py <file> [<file> ...]   # fix in place, then list what is left
python3 scripts/mdfix.py --all                 # every Markdown file the company owns
python3 scripts/mdfix.py --check --all         # report only; doctor.py runs this too
python3 scripts/mdfix.py --verify              # the real markdownlint-cli2 through npx (needs Node), for a second opinion
```

Third-party skills (listed in `skills-lock.json`) are never edited and never linted. Product repos under `projects/` and their worktrees follow their own rules.

## Write it right the first time

The fixer is a safety net. These habits mean it has nothing to do:

1. **Every code fence names its language.** `bash` for commands, `json`, `yaml`, `python`, `markdown` for Markdown samples, `text` for anything else (directory trees, templates, sample output, prompts). Never a bare fence. The fixer guesses, and when it cannot tell it writes `text`, which is rarely what you meant.
2. **Tables in compact style.** One space on each side of every cell, a delimiter row of `| --- | --- |` (colons for alignment go inside: `| :-- | --: |`), leading and trailing pipes on every row, the same number of cells in every row, an empty cell written as `| |`. Do not pad columns to line them up. A literal pipe inside a cell is `\|`, also inside backticks.
3. **Blank lines around structure.** One blank line before and after every heading, fenced block, list and table. Never two blank lines in a row. The file ends with exactly one newline.
4. **Headings.** The first line of content (after front matter) is the only `# H1`. Levels go down one step at a time (`##` then `###`, never `#` then `###`). No two headings with the same text in one file. No trailing `.`, `,`, `:`, `;` or `!`. One space after the hashes, no indentation.
5. **Do not fake a heading with emphasis.** A line that is only `**Bold text**` or `_italic text_` is flagged. Make it a real heading, or make it a sentence that ends with a full stop (`_Nothing here yet._`).
6. **Angle-bracket placeholders go in backticks.** A placeholder such as `<job-id>` is read as an HTML tag unless it sits inside a code span, so always put it between backticks. Template placeholders of the form `<FILL: ...>` are safe as they are. No raw HTML; comments (`<!-- ... -->`) are fine.
7. **Lists.** `-` for bullets, one space after the marker, ordered lists numbered `1.` `2.` `3.`, nested items indented to line up with the text of their parent.
8. **Links.** No bare URLs in prose: write `[text](https://...)` or `<https://...>`.
9. **No trailing spaces, no tabs, no spaces just inside a code span.** Write `x`, never a span padded with spaces. If the space is what you want to show, say it in words ("a colon followed by a space").

## What the fixer does, and what it leaves to you

| Fixed automatically | Reported to you |
| --- | --- |
| Table spacing and pipes (MD055, MD060) | First line is not a `# H1` (MD041) |
| Fence without a language (MD040, guessed) | More than one `# H1` (MD025) |
| Blank lines around headings, fences, lists, tables (MD022, MD031, MD032, MD058) | Heading level skipped (MD001) |
| Repeated blank lines, final newline (MD012, MD047) | Duplicate heading text (MD024) |
| Trailing spaces, tabs (MD009, MD010) | Emphasis used as a heading (MD036) |
| Heading spacing, indentation, trailing punctuation (MD019, MD023, MD026) | Table row with the wrong number of cells (MD056) |
| `*` or `+` bullets, extra spaces after a marker (MD004, MD030) | Real inline HTML (MD033) |
| Bare URLs, placeholders like `<name>` (MD034, MD033) | Spaces just inside a code span (MD038) |

## Files that scripts write

The job board, job folders, the journal, the work log, the project registry, the team roster and new role files are written by `scripts/`, and those scripts format their own output through the same fixer. Do not hand-edit the board or append to the log yourself: use the scripts, and the Markdown stays clean.
