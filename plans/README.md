# plans/

Executor-ready implementation plans, written by the Senior Technical Adviser with the `improve` skill. A spec (`specs/`) says what and why and is approved by the CEO. A plan says exactly how, for one employee, with verification commands and stop conditions.

- One folder per project: `plans/<project>/`, with `README.md` as the index (execution order, dependencies, owners, status) and `NNN-slug.md` per plan. `FINDINGS.md` holds the latest audit's vetted findings. `PROFILE.md` exists for a codebase that was imported (`import-project` skill): how it is built, the standards its code follows, the baseline on import and the CEO's answers (the Chief of Staff fills those in). Everyone who plans, writes or reviews code in that project reads the parts they touch.
- Source paths inside a plan are relative to the product repo root, which for the employee executing it is its worktree, never `projects/<project>/` itself.
- The adviser writes plans, in its own HQ worktree; the Chief of Staff merges them. Employees executing a plan report their status, and the Chief of Staff updates the index row. After a hire, the Chief of Staff may replace `unowned` with the employee's name in a plan's Owner line, branch name and index row, and edits nothing else in a plan. The Chief of Staff commits.
