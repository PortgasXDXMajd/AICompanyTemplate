---
name: doctor
description: Check that the company repo is consistent and the machine is ready - skill and employee frontmatter, settings, third-party skills, instruction-file size budgets, references to paths that no longer exist, job board vs job folders vs worktrees, unfilled placeholders in role files. Use when something behaves oddly, after editing skills, role files or CLAUDE.md, after pulling template updates, and inside the end-of-day and weekly routines.
---

# Doctor

Two read-only scripts. Neither changes anything.

```bash
python3 scripts/preflight.py      # the machine and the repo: git, first commit, claude, node, gh, Herdr, third-party skills, core files
python3 scripts/doctor.py         # the repo's own consistency (add `budgets` or `refs` to run one check)
```

Read the output and deal with each problem where it belongs:

- **Frontmatter or settings problems**: fix the file. A skill whose `name` differs from its folder is not loaded; an employee without a real `description` is never routed to.
- **Unfilled `<FILL: ...>` placeholders in a role file**: finish the hire (`hire` skill) or remove the half-made employee with the CEO's agreement.
- **Over budget**: move content to the file that owns it, under the rules of `routines/end-of-day.md`. Never cut a guardrailed section to make the number fit.
- **Markdown problems** (`file:line MDxxx ...`): run `python3 scripts/mdfix.py --all`, then fix by hand what it still reports (`markdown` skill).
- **A reference to a path that does not exist**: fix the reference or restore the file. If the path is created on demand, add it to `ON_DEMAND` in `scripts/doctor.py`.
- **Board, job folder or worktree mismatches**: run the `job-status` skill; it decides with the CEO what to resume, close or drop.
- **Missing third-party skills**: `python3 scripts/skills.py install`.

Report to the CEO only what needs a decision. Fix the rest and say what you fixed.
