# AI Company Blueprint

A repo template for running a company staffed by Claude. You are the CEO. Every Claude Code session opened in this repo is an employee that knows the company, knows its job, and writes its work back into the repo so the next session picks up where the last one stopped.

It is plain markdown plus native Claude Code features (`CLAUDE.md`, subagents, skills). No framework, no server, nothing to install beyond Claude Code.

## Quickstart

1. Click **Use this template** on GitHub and create your own (private) company repo, then clone it.
2. `cd` into it, run `python3 scripts/preflight.py` to see what your machine is missing, then run `claude`.
3. Say hello. The session sees the company is not onboarded and starts the onboarding interview (`/onboard`). It grills you in rounds, each question with a recommended answer, and pushes back on vague ones. That is the point.
4. When onboarding ends you have a filled `context/company.md`, a `ROADMAP.md` with one measurable goal, and a recommendation for your next hire. If you build software you also have your first employee (the Senior Technical Adviser), your first product repo under `projects/`, with a `CLAUDE.md` recording the tech stack you chose, and your coding rules in `context/engineering.md`.

Optional but recommended: install and authenticate the GitHub CLI (`gh auth login`) so `/new-project` can create product repos for you.

## How it works

**You talk to the Chief of Staff.** A normal `claude` session in this repo acts as Chief of Staff: it clarifies what you want, checks it against the roadmap, routes it to the employee who owns that work (or does it itself), gets it reviewed against `REVIEW.md`, and records the result.

**Employees are Claude Code subagents.** Each one is a single file in `.claude/agents/` with a mission, the files it owns, a definition of done, and its own persistent memory. The Chief of Staff delegates to them automatically. You can also work with one directly:

```bash
claude --agent growth-marketer
```

**Your first employee comes with your first software project.** The Senior Technical Adviser runs on the newest Fable model at maximum effort and works by shadcn's `improve` skill: it reads the codebase, audits it, and turns approved specs into executor-ready plans in `plans/<project>/`, one per task and employee. It never writes code. Everyone else is hired when recurring work needs an owner, and runs on the newest Opus model:

```text
/hire growth marketer
```

The hire skill makes you justify the role, drafts the job description, and creates the employee once you approve.

**Nothing is lost when a session dies.** Every delegation is a job with its own folder under `jobs/` (brief, the employee's running progress log, hand-back, reviews), `jobs/BOARD.md` lists every open job, and the Chief of Staff keeps a journal in `context/journal/`. Start a fresh session, ask "what is happening?", and the `job-status` skill reads all of it, checks it against the worktrees and any agents still running, and tells you what is fine, what failed or was cut off, and what it recommends restarting, with a yes or no for each. You can also reopen the old conversation itself with `claude --continue`.

**The repo is the memory.** Sessions are stateless, so everything that matters is written down: decisions in `context/decisions.md`, finished work in `context/log.md`, evidence in `customers/`, specs in `specs/`, implementation plans in `plans/`, deliverables in `work/`, proof in `demos/`.

## Layout

```text
CLAUDE.md          Operating manual every session loads
ROADMAP.md         One goal, then Now / Next / Later
REVIEW.md          Quality bar and review process
context/           Company facts, team roster, decision log, work log, daily journal
jobs/              Job board and one folder per delegation: the flight recorder
customers/         Evidence about real buyers
specs/             What will be built or done, written before doing it
plans/             Executor-ready implementation plans, per project, written by the adviser
work/              Non-code deliverables: copy, outreach drafts, research
demos/             Proof of finished work, viewable in two minutes
routines/          Recurring procedures: daily standup, end of day, weekly review
projects/          Product repos, cloned here, tracked in their own GitHub repos
worktrees/         One git worktree per running employee (gitignored)
.claude/agents/    Employees
.claude/skills/    Company procedures (onboard, hire, new-project, feature, delegate, worktree,
                   job-status, refinement-check, qa-check, doctor, markdown), plus third-party skills
                   installed with `npx skills`
scripts/           The deterministic plumbing the skills call (Python, standard library only)
.markdownlint-cli2.jsonc  Markdown lint rules for VS Code, markdownlint-cli2 and scripts/mdfix.py
.claude/settings.json  Runs the Markdown fixer after every write; makes Claude Code ask you before a push, a GitHub repo operation,
                   or an edit to a product's main checkout; allows the scripts, git inside
                   worktrees, and the Herdr commands delegation uses
skills-lock.json   Versions of the third-party skills
```

## How code gets built

1. `/feature` grills the idea into a spec you approve.
2. The Senior Technical Adviser turns the spec into plans, one per task and employee, each ordered test-first and with a QA section.
3. Developers build each plan in their own worktree, **test-first** (Matt Pocock's `tdd` skill): a failing test, then just enough code to pass it, one slice at a time.
4. Before anything is merged: an independent review (which checks the tests really came first), the refinement check (code quality and architecture), and **hands-on QA**, where the product is run and used like a customer would, in a real browser through Claude in Chrome or Playwright, or in an Android emulator or iOS simulator through Maestro. Screenshots and findings are saved with the job.
5. You get a short hand-off with the evidence and one question: merge?

Hands-on QA needs tools on your machine: the Claude in Chrome extension and `claude --chrome` for web, Maestro plus an Android emulator or (macOS only) an iOS simulator for mobile. When they are missing, the hand-off says QA was not performed. It never pretends.

## Parallel work: one worktree per employee

Every employee run gets its own git worktree under `worktrees/` (gitignored), on its own branch: `worktrees/<project>/<employee>--<slug>` for product code, `worktrees/_hq/<employee>--<slug>` for HQ files. Employees write only there. The main checkouts stay on their default branch and only the Chief of Staff touches them, to merge reviewed work. That is what lets a backend and a frontend engineer build on the same project at the same time, and it means nothing unreviewed ever sits in a main checkout. The `worktree` skill holds the exact commands.

## Watching your employees: Herdr

[Herdr](https://herdr.dev) is a terminal workspace manager for coding agents. Run the company inside it and every employee gets its own tab, with live status in the sidebar, and you can step into any tab and talk to that employee.

```bash
curl -fsSL https://herdr.dev/install.sh | sh    # or: brew install herdr
herdr integration install claude                # lets Herdr see Claude Code's state
cd /path/to/company && herdr                    # then run `claude` in the first pane: that is your Chief of Staff
```

Inside Herdr the Chief of Staff delegates by opening a tab per employee (and per review helper), starting `claude --agent <employee>` in it, and waiting for the hand-back. When an employee needs an approval, its tab shows as blocked and the Chief of Staff tells you which one; it never answers approvals for you. Outside Herdr the same delegations run as in-process subagents. The `delegate` skill covers both.

## Scripts

Skills decide and judge; scripts do the repeatable plumbing the same way every time, so it does not depend on a model retyping git or Herdr commands correctly. They are plain Python 3 with no dependencies, in `scripts/` (`scripts/README.md` has the full table):

| Script | In one line |
| --- | --- |
| `preflight.py` | Is this machine and repo ready? |
| `job.py`, `journal.py`, `status.py` | The flight recorder: job folders, the board, the journal, and the report a new session starts from |
| `worktree.py` | Create, check, update, merge and remove employee worktrees, with every guard built in |
| `agent.py` | Start an employee or a helper in its own Herdr tab, prompt it, wait for it, read it, close it |
| `project.py`, `team.py` | Product repos and their registry; role files and the roster |
| `mdfix.py` | Keeps every Markdown file free of markdownlint warnings; runs by itself after each write |
| `skills.py`, `qa_probe.py`, `doctor.py` | Third-party skills; what hands-on QA can run here; a consistency check of the whole repo |

Pushes, GitHub repo creation and PR merges are deliberately **not** in any script: those commands run in the open so Claude Code's permission prompt reaches you.

## Markdown without warnings

Everything here is Markdown, so it is kept clean under [markdownlint](https://github.com/DavidAnson/markdownlint), the linter behind the warnings in VS Code. `.markdownlint-cli2.jsonc` holds the rules (defaults, line length off, compact tables; third-party skills are ignored because they are never edited). A `PostToolUse` hook in `.claude/settings.json` runs `scripts/mdfix.py` on every `.md` file Claude writes: it fixes table spacing, code fences without a language, blank lines and the rest in place, and hands anything it cannot decide back to Claude to fix in the same turn. The scripts that write Markdown (job board, journal, registry, roster, role files) format their output the same way. `python3 scripts/mdfix.py --all` fixes the whole repo by hand, and `python3 scripts/doctor.py` fails if any file is not clean.

## Commands

| Command | What it does |
| --- | --- |
| `/onboard` | Interview about product, buyer, pain, promise, goal. Sets up the company. |
| `/hire <role>` | Justify, define, and create a new employee. |
| `/new-project <name>` | Grill the tech stack, create a product repo on GitHub with a README and a `CLAUDE.md` recording that stack, clone it into `projects/`. |
| `/feature <idea>` | Grill a feature idea into an approved spec in `specs/`, have the adviser turn it into plans, and put it on the roadmap. |
| `claude --agent senior-technical-adviser` | Work with the adviser directly, for example "audit projects/my-app". |
| `/improve-codebase-architecture projects/<name>` | Full, interactive architecture review of one project. Always pass the project path. |
| `/thermo-nuclear-code-quality-review` | Strict maintainability review of the current branch's changes. |
| `/job-status`, or "what is happening?" | Rebuilds the state of every job from disk and recommends what to resume, restart, review or drop. |
| `/qa-check <job>` | Runs the product and uses it like a customer: real browser, emulator or simulator. |
| `/doctor` | Checks the machine and the repo for inconsistencies (`preflight.py`, `doctor.py`). |
| "run the daily standup" | Executes `routines/daily-standup.md`. |
| "close the day" | Executes `routines/end-of-day.md`: settles the job board, distils the day's lessons, prunes and updates every `CLAUDE.md` (you approve the edits). |
| "run the weekly review" | Executes `routines/weekly-review.md`. |

Routines are interactive in v1: they end with decisions that need you. Unattended runs are not set up.

## Design choices

- **Crash-proof by default.** Briefs, progress and results are files, written before and while the work happens. A new session needs no explanation from you.
- **Test first, then use it for real.** Tests come before code, and nothing with a screen is called done until someone has clicked through it.
- **Isolation by default.** One employee run, one worktree, one branch. Only the Chief of Staff merges.
- **One coordinator.** Employees do not delegate to each other. Handoffs go through the Chief of Staff so priorities are decided in one place.
- **Expensive model plans, cheaper models build.** The adviser (Fable, maximum effort) does the understanding and specifying. Developers (Opus) execute plans that leave nothing to guess. Expect adviser runs to be the costly ones.
- **Roles are earned.** An employee without owned files and a definition of done is only a persona. The hire skill refuses to create those.
- **You approve anything irreversible or external.** Spending, sending, publishing, creating or deleting repos, hiring. The list is in `CLAUDE.md`.
- **Product code stays out of HQ.** Each product is its own GitHub repo. `projects/` holds local clones and is gitignored apart from its registry.

## Third-party skills

Eight third-party skills are vendored into `.claude/skills/` and pinned in `skills-lock.json`. Five come from [mattpocock/skills](https://github.com/mattpocock/skills), one each from [cursor/plugins](https://github.com/cursor/plugins), [shadcn/improve](https://github.com/shadcn/improve) and [herdrdev/herdr](https://github.com/herdrdev/herdr) (Apache-2.0; the others are MIT):

| Skill | Used for |
| --- | --- |
| `grilling` | The interview method behind `/onboard`, `/new-project` and `/feature` |
| `tdd` | How every developer builds: test-first, in vertical slices |
| `herdr` | The Herdr CLI reference behind `delegate`'s one-tab-per-employee mode |
| `improve` | The Senior Technical Adviser's method: codebase audits and executor-ready plans |
| `thermo-nuclear-code-quality-review` | Part A of `refinement-check`: strict code quality review of every change |
| `improve-codebase-architecture` | Part B of `refinement-check`: architecture pass on every change |
| `codebase-design`, `domain-modeling` | Vocabulary and glossary discipline the architecture skill depends on |

They were installed with:

```bash
python3 scripts/skills.py install     # runs these:
npx skills add https://github.com/mattpocock/skills \
  --skill grilling tdd improve-codebase-architecture codebase-design domain-modeling \
  -a claude-code --copy -y
npx skills add https://github.com/cursor/plugins \
  --skill thermo-nuclear-code-quality-review -a claude-code --copy -y
npx skills add https://github.com/shadcn/improve --skill improve -a claude-code --copy -y
npx skills add herdrdev/herdr --skill herdr -a claude-code --copy -y
```

Update them with `python3 scripts/skills.py update` (`npx skills update`), and read the diff before committing: skills are instructions your employees will follow. Do not edit them in place. Company-specific behaviour goes in the wrapper skills (`onboard`, `new-project`, `feature`, `delegate`, `refinement-check`), so updates never clobber it.

**The refinement check.** After every code implementation, and before any feature branch is pushed or merged, the Chief of Staff runs `refinement-check`: two fresh subagents review the change with the code quality and architecture skills. Inside Herdr those helpers are tabs too. Problems contained in the change are fixed on the branch. Wider ones are logged in `work/engineering/refinement-candidates.md` and brought to you.

## Customizing

Everything is a markdown file. Change the rules in `CLAUDE.md`, the coding standards in `context/engineering.md`, the quality bar in `REVIEW.md`, the interview in `.claude/skills/onboard/SKILL.md`, the employee template in `.claude/skills/hire/employee-template.md`. Keep `CLAUDE.md` short: every session and every employee loads it.
