# Weekly review

- **Trigger:** end of the week, or "run the weekly review"
- **Owner:** Chief of Staff
- **Inputs:** `ROADMAP.md`, this week's files in `context/journal/`, `jobs/BOARD.md`, last week's weekly review in `routines/reviews/` if there is one (files ending in `-end-of-day.md` are pending end-of-day proposals), this week's entries in `context/log.md` and `context/decisions.md`, new files in `customers/`, `work/` and `demos/`
- **Output:** `routines/reviews/YYYY-MM-DD.md`, updated `ROADMAP.md`, and a short summary to the CEO

## Steps

1. **Progress on the goal.** State the metric in the current goal and its value now against last week. If it cannot be measured, say that first: it is the top problem.
2. **What shipped.** List finished items with demo links. Move them to Done in `ROADMAP.md`.
3. **What did not ship, and why.** Be specific: wrong scope, blocked on the CEO, poor spec, bad estimate.
4. **What we learned about customers.** New evidence this week. Update `customers/insights.md`. Mark assumptions in `context/company.md` as confirmed or disproved.
5. **Team check.** For each employee: did their work pass review first time? Is the role still needed? Is there recurring work nobody owns that justifies a hire?
6. **Worktrees and repo health.** Run `python3 scripts/worktree.py list` and `python3 scripts/doctor.py`. Report any worktree with no open roadmap item behind it; do not delete it silently.
7. **Codebase health.** Read `work/engineering/refinement-candidates.md` if it exists. If the same area keeps showing up, recommend that the CEO run `/improve-codebase-architecture projects/<name>` on that project.
8. **Process fixes and instruction files.** Any rejection or rework that happened twice gets a change to a role file, `REVIEW.md`, or a template. Do the full pass the end-of-day routine skips: every `CLAUDE.md` (HQ and each project, never the copies under `worktrees/`) and every role file, for duplicates, contradictions, stale facts, and instructions that a whole week of journals shows nobody needed. Apply the batched lessons in `work/engineering/claude-md-lessons.md`. The guardrails and the approval step of `routines/end-of-day.md` apply here too: show the CEO each change and its evidence, and apply what they approve.
9. **Next week.** Propose the Now list, three items at most, each tied to the goal. Get the CEO's agreement, then update `ROADMAP.md`.
10. Append a line to `context/log.md` and commit.

Be blunt in the write-up. A review that reports only good news is not doing its job.
