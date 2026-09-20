# AI Company Blueprint

A repo template for running a company staffed by Claude. You are the CEO. Every Claude Code session opened in this repo is an employee that knows the company, knows its job, and writes its work back into the repo so the next session picks up where the last one stopped.

It is plain markdown plus native Claude Code features (`CLAUDE.md`, subagents, skills). No framework, no server, nothing to install beyond Claude Code.

## Quickstart

1. Click **Use this template** on GitHub and create your own (private) company repo, then clone it.
2. `cd` into it and run `claude`.
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

```
/hire growth marketer
```

The hire skill makes you justify the role, drafts the job description, and creates the employee once you approve.

**The repo is the memory.** Sessions are stateless, so everything that matters is written down: decisions in `context/decisions.md`, finished work in `context/log.md`, evidence in `customers/`, specs in `specs/`, implementation plans in `plans/`, deliverables in `work/`, proof in `demos/`.

## Layout

```
CLAUDE.md          Operating manual every session loads
ROADMAP.md         One goal, then Now / Next / Later
REVIEW.md          Quality bar and review process
context/           Company facts, team roster, decision log, work log
customers/         Evidence about real buyers
specs/             What will be built or done, written before doing it
plans/             Executor-ready implementation plans, per project, written by the adviser
work/              Non-code deliverables: copy, outreach drafts, research
demos/             Proof of finished work, viewable in two minutes
routines/          Recurring procedures: daily standup, weekly review
projects/          Product repos, cloned here, tracked in their own GitHub repos
.claude/agents/    Employees
.claude/skills/    Company procedures (onboard, hire, new-project, feature, refinement-check)
                   plus third-party skills installed with `npx skills`
skills-lock.json   Versions of the third-party skills
```

## Commands

| Command | What it does |
|---|---|
| `/onboard` | Interview about product, buyer, pain, promise, goal. Sets up the company. |
| `/hire <role>` | Justify, define, and create a new employee. |
| `/new-project <name>` | Grill the tech stack, create a product repo on GitHub with a README and a `CLAUDE.md` recording that stack, clone it into `projects/`. |
| `/feature <idea>` | Grill a feature idea into an approved spec in `specs/`, have the adviser turn it into plans, and put it on the roadmap. |
| `claude --agent senior-technical-adviser` | Work with the adviser directly, for example "audit projects/my-app". |
| `/improve-codebase-architecture projects/<name>` | Full, interactive architecture review of one project. Always pass the project path. |
| `/thermo-nuclear-code-quality-review` | Strict maintainability review of the current branch's changes. |
| "run the daily standup" | Executes `routines/daily-standup.md`. |
| "run the weekly review" | Executes `routines/weekly-review.md`. |

Routines are interactive in v1: they end with decisions that need you. Unattended runs are not set up.

## Design choices

- **One coordinator.** Employees do not delegate to each other. Handoffs go through the Chief of Staff so priorities are decided in one place.
- **Expensive model plans, cheaper models build.** The adviser (Fable, maximum effort) does the understanding and specifying. Developers (Opus) execute plans that leave nothing to guess. Expect adviser runs to be the costly ones.
- **Roles are earned.** An employee without owned files and a definition of done is only a persona. The hire skill refuses to create those.
- **You approve anything irreversible or external.** Spending, sending, publishing, creating or deleting repos, hiring. The list is in `CLAUDE.md`.
- **Product code stays out of HQ.** Each product is its own GitHub repo. `projects/` holds local clones and is gitignored apart from its registry.

## Third-party skills

Six third-party skills (all MIT) are vendored into `.claude/skills/` and pinned in `skills-lock.json`. Four come from [mattpocock/skills](https://github.com/mattpocock/skills), one from [cursor/plugins](https://github.com/cursor/plugins), one from [shadcn/improve](https://github.com/shadcn/improve):

| Skill | Used for |
|---|---|
| `grilling` | The interview method behind `/onboard`, `/new-project` and `/feature` |
| `improve` | The Senior Technical Adviser's method: codebase audits and executor-ready plans |
| `thermo-nuclear-code-quality-review` | Part A of `refinement-check`: strict code quality review of every change |
| `improve-codebase-architecture` | Part B of `refinement-check`: architecture pass on every change |
| `codebase-design`, `domain-modeling` | Vocabulary and glossary discipline the architecture skill depends on |

They were installed with:

```bash
npx skills add https://github.com/mattpocock/skills \
  --skill grilling improve-codebase-architecture codebase-design domain-modeling \
  -a claude-code --copy -y
npx skills add https://github.com/cursor/plugins \
  --skill thermo-nuclear-code-quality-review -a claude-code --copy -y
npx skills add https://github.com/shadcn/improve --skill improve -a claude-code --copy -y
```

Update them with `npx skills update`, and read the diff before committing: skills are instructions your employees will follow. Do not edit them in place. Company-specific behaviour goes in the wrapper skills (`onboard`, `new-project`, `feature`, `refinement-check`), so updates never clobber it.

**The refinement check.** After every code implementation, and before any feature branch is pushed or merged, the Chief of Staff runs `refinement-check`: two fresh subagents review the change with the code quality and architecture skills. Problems contained in the change are fixed on the branch. Wider ones are logged in `work/engineering/refinement-candidates.md` and brought to you.

## Customizing

Everything is a markdown file. Change the rules in `CLAUDE.md`, the coding standards in `context/engineering.md`, the quality bar in `REVIEW.md`, the interview in `.claude/skills/onboard/SKILL.md`, the employee template in `.claude/skills/hire/employee-template.md`. Keep `CLAUDE.md` short: every session and every employee loads it.
