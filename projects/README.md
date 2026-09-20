# projects/

The company's products. Each project is its own GitHub repo, cloned into `projects/<name>/`. Those clones are gitignored here: product code is versioned in the product repo, and this HQ repo only keeps the registry below.

- Create a project with `/new-project <name>`. It grills the tech stack, creates the GitHub repo with a README and a `CLAUDE.md`, clones it here, and adds the row.
- On a fresh clone of HQ, restore the working copies with `gh repo clone <repo> projects/<name>` for each row.
- The checkout at `projects/<name>/` is the main checkout: it stays on the default branch, clean, and only the Chief of Staff writes to it. All work on a project happens in worktrees under `worktrees/<name>/`, which is how several employees work on one project at the same time.
- Every project has its own `CLAUDE.md` with the tech stack the CEO chose. Work inside a project follows it, plus `context/engineering.md` and `REVIEW.md` from HQ. Specs stay in HQ under `specs/`.

- Search tools skip gitignored folders. Pass your worktree path as the search path (`projects/<name>` only for reading the main checkout).
- Status values: `active`, `local only` (not on GitHub yet), `paused`, `archived`.

## Registry

| Name | GitHub repo | Purpose | Status | Created |
| --- | --- | --- | --- | --- |
