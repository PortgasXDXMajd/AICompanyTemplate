# plans/

Executor-ready implementation plans, written by the Senior Technical Adviser with the `improve` skill. A spec (`specs/`) says what and why and is approved by the CEO. A plan says exactly how, for one employee, with verification commands and stop conditions.

- One folder per project: `plans/<project>/`, with `README.md` as the index (execution order, dependencies, owners, status) and `NNN-slug.md` per plan. `FINDINGS.md` holds the latest audit's vetted findings.
- Source paths inside a plan are relative to `projects/<project>/`.
- The adviser writes plans. The employee executing a plan updates only its status row in the index. After a hire, the Chief of Staff may replace `unowned` with the employee's name in a plan's Owner line, branch name and index row, and edits nothing else in a plan. The Chief of Staff commits.
