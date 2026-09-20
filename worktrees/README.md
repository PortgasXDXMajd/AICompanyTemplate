# worktrees/

Where employees work. Every employee run gets its own git worktree here, so several employees can work at the same time without touching each other's files, and nothing reaches a main checkout before it is reviewed.

```text
worktrees/
  <project>/<employee>--<slug>/   worktree of projects/<project>, on branch <employee>/<slug>
  _hq/<employee>--<slug>/         worktree of this HQ repo, on branch <employee>/<slug>
```

- Everything in this folder except this file is gitignored. The work itself is safe: it lives on branches in the repo each worktree belongs to.
- The Chief of Staff creates a worktree before delegating, and removes it after the branch is merged. The exact commands are in the `worktree` skill.
- The main checkouts (the HQ root and `projects/<project>/`) stay on their default branch. Only the Chief of Staff writes there, with two exceptions for employees: their own job folder under `jobs/` and their own memory directory, both at the HQ root.
- A fresh worktree has no installed dependencies, build output, or untracked files such as `.env`. Install first.
- Search tools skip gitignored folders. Pass the worktree path as the search path.
