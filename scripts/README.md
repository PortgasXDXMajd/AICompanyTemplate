# scripts/

The deterministic parts of running the company, as small Python scripts (standard library only, Python 3.8+). The skills decide **what** to do and judge the results; the scripts do the plumbing the same way every time: names, paths, git commands, the job board, the journal, Herdr calls.

Run them from the HQ root: `python3 scripts/<name>.py --help`. Scripts that print data take `--json` before the subcommand (`python3 scripts/job.py --json list`). They always resolve the real HQ root, even when run from a copy inside an HQ worktree. `.claude/settings.json` allows `python3 scripts/*` without a prompt.

| Script | What it does | Used by |
| --- | --- | --- |
| `preflight.py` | Checks the machine and the repo: git, first commit, claude, node, gh and its login, Herdr, third-party skills, core files | `onboard`, README quickstart |
| `job.py` | Job records: `new` (folder, brief skeleton, board row, journal line), `set` (state, runner, next step), `progress`, `show`, `list`, `close` (row off the board, `closed.md`, line in `context/log.md`) | `delegate`, `job-status`, `REVIEW.md`, every employee (`progress`) |
| `journal.py` | The Chief of Staff's journal: `add`, `tail`, `unclosed` (days never closed), `close` (day summary) | Chief of Staff, `end-of-day` |
| `worktree.py` | One worktree per employee run: `add` (checks, naming, base, fills the brief and the board), `status`, `update` (bring a branch up to date), `merge` (guards, aborts on conflict), `remove` (never forces), `list` (finds strays) | `worktree`, `delegate`, `refinement-check`, `job-status` |
| `agent.py` | Herdr: `start` an employee or a helper in its own tab and prompt it with its brief, `prompt` a fix round, `wait`, `read`, `list`, `close`; `where` says `herdr` or `plain` | `delegate`, `refinement-check`, `qa-check` |
| `status.py` | Collects the facts about every open job (files, verdict lines, progress, worktree, commits, merged or not, live Herdr agents, strays) and suggests a verdict | `job-status`, `daily-standup`, `end-of-day` |
| `project.py` | Product repos: `init`, `commit` (first commit; `--all` for an imported folder, refusing files that look like secrets), `clone`, `import-local` (a codebase from a folder on this machine; the folder is never touched), `survey` (read-only inventory of an existing codebase: git habits, manifests, tooling, tests, CI, containers, data, env variable names), `register` (registry row), `list` | `new-project`, `import-project` |
| `team.py` | Employees: `add-adviser`, `add` (role file from the template plus roster row), `list` | `new-project`, `import-project`, `hire` |
| `skills.py` | Third-party skills: `list`, `install`, `update` | README, `preflight.py` |
| `qa_probe.py` | Which hands-on QA tooling this machine has; `wait-url` polls a dev server with a time limit | `qa-check` |
| `mdfix.py` | Keeps Markdown free of markdownlint warnings: fixes tables, fence languages, blank lines, spacing, bare URLs and tag-like placeholders in place; reports what only an author can fix; `--hook` is the PostToolUse hook that runs after every write; `--check`, `--all`, `--verify` (real markdownlint through npx). The other scripts format their own Markdown output through it | the hook in `.claude/settings.json`, `markdown` skill, `doctor.py` |
| `doctor.py` | Read-only consistency check: frontmatter, settings, size budgets, references to missing paths, Markdown lint, board vs folders vs worktrees, unfilled role-file placeholders | `doctor` skill, `end-of-day`, `weekly-review` |

## What is deliberately not scripted

- **Anything that needs the CEO's approval through Claude Code's own prompt**: `git push`, `gh repo create`, `gh pr merge`, releases, and writing files into a product's main checkout (creating one with `init`, `clone` or `import-local` is the exception). A script would hide those commands from the permission rules in `.claude/settings.json`. `worktree.py merge` into a product repo insists on `--approved-by-ceo` for the same reason: say it only when the CEO said yes.
- **Judgment**: writing briefs, plans, specs and reviews, deciding what to resume or drop, deciding what goes into a `CLAUDE.md`. Scripts gather the facts for those decisions.
- **Project-specific commands**: install, test, run. They live in each project's `CLAUDE.md`.

## Changing a script

They are company procedure, owned by the Chief of Staff. Change one the way you would change a skill: with the CEO's agreement, tried out in a throwaway copy of the repo first (copy the folder somewhere else, `git init`, run the script there), and with this table kept true. `python3 scripts/doctor.py` checks that the repo is still consistent afterwards.

There is deliberately no test suite for these scripts in this repo. HQ holds company records, not code under test, and the only tests an employee should ever find and run are a product's own, inside `projects/<name>/` and its worktrees.
