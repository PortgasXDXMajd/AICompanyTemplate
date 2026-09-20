#!/usr/bin/env python3
"""One employee run, one git worktree, one branch.

  worktree.py add --repo PROJECT|_hq --employee E --slug S [--job JOB] [--existing]
  worktree.py status PATH [--base SHA]      uncommitted files, commits since base, ahead/behind
  worktree.py update PATH                   bring a branch that is behind up to date (run by its employee)
  worktree.py merge PATH --title "..." [--approved-by-ceo]
  worktree.py remove PATH [--keep-branch]   never forces; refuses unmerged or dirty work
  worktree.py list                          every worktree, and whether a board row points at it

Layout:  worktrees/<project>/<employee>--<slug>   branch <employee>/<slug>   (product repos)
         worktrees/_hq/<employee>--<slug>        branch <employee>/<slug>   (this HQ repo)
"""
import argparse
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L


def git(repo_dir, *args, check=False):
    return L.run(["git", "-C", str(repo_dir), *args], check=check)


def repo_of(path):
    """('_hq' | project, main checkout path, branch) for a worktree path."""
    p = Path(path).resolve()
    try:
        parts = p.relative_to(L.ROOT / "worktrees").parts
    except ValueError:
        L.die(f"{path} is not under worktrees/")
    if len(parts) < 2 or not p.is_dir():
        L.die(f"{path} is not a worktree folder (worktrees/<repo>/<employee>--<slug>)")
    repo = parts[0]
    code, branch, _ = git(p, "symbolic-ref", "--short", "HEAD")
    if code != 0:
        L.die(f"{path}: cannot read its branch (is it a git worktree?)")
    return repo, L.repo_main(repo), branch, p


def ensure_hq_repo():
    code, _, _ = git(L.ROOT, "rev-parse", "--verify", "HEAD")
    if code != 0:
        L.die("HQ is not a git repo with a first commit yet. Run: git init -b main && git add -A && "
              "git commit -m 'Initial commit'  (in the HQ root), then retry.")


def cmd_add(a):
    L.valid_name(a.employee, "employee"); L.valid_slug(a.slug)
    ensure_hq_repo()
    main = L.repo_main(a.repo)
    base_branch = L.default_branch(a.repo)
    branch = f"{a.employee}/{a.slug}"
    path = L.worktree_path(a.repo, a.employee, a.slug)
    if path.exists():
        L.die(f"{L.rel(path)} already exists. A fix round or a resume goes back into it; do not create a second one.")
    if a.repo != L.HQ:
        code, dirty, _ = git(main, "status", "--short")
        if dirty:
            L.die(f"projects/{a.repo} main checkout is not clean:\n{dirty}\nOnly the Chief of Staff writes there; sort it out first.")
        code, remotes, _ = git(main, "remote")
        if remotes:
            code, _, err = git(main, "pull", "--ff-only")
            if code != 0:
                L.die(f"git pull --ff-only failed in projects/{a.repo}: {err}\nStop and tell the CEO. Never reset or rebase a main checkout.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if a.existing:
        git(main, "worktree", "add", str(path), branch, check=True)
    else:
        code, _, _ = git(main, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
        if code == 0:
            L.die(f"branch {branch} already exists. Reopen it with --existing, or pick another slug.")
        git(main, "worktree", "add", "-b", branch, str(path), base_branch, check=True)
    _, base, _ = git(path, "merge-base", "HEAD", base_branch)
    base = base[:9]
    data = {"worktree": L.rel(path), "branch": branch, "base": base, "cut_from": base_branch, "repo": a.repo}
    if a.job:
        head, rows, tail = L.board_read()
        r = L.board_find(rows, a.job)
        if r:
            r.update({"Worktree": data["worktree"], "Branch": branch, "Base": base, "Repo": a.repo, "Updated": L.stamp()})
            L.board_write(head, rows, tail)
        brief = L.job_dir(a.job) / "brief.md"
        if brief.exists():
            t = brief.read_text()
            marker = "_path, branch, base (filled in by worktree.py add --job)_"
            if marker in t:
                L.write_md(brief, t.replace(marker, f"`{L.ROOT / data['worktree']}`, branch `{branch}`, base `{base}` (cut from `{base_branch}`)"))
        L.journal_add(f"worktree created {data['worktree']} on {branch} at {base}", a.job)
    L.out(data, a.json)
    if not a.json:
        print("note: a fresh worktree has no installed dependencies, build output, or untracked files such as .env")


def cmd_status(a):
    repo, main, branch, path = repo_of(a.path)
    base_branch = L.default_branch(repo)
    _, dirty, _ = git(path, "status", "--short")
    base = a.base or git(path, "merge-base", "HEAD", base_branch)[1]
    _, commits, _ = git(path, "log", "--oneline", f"{base}..HEAD")
    _, counts, _ = git(path, "rev-list", "--left-right", "--count", f"{base_branch}...HEAD")
    behind, ahead = (counts.split() + ["0", "0"])[:2]
    _, stat, _ = git(path, "diff", "--stat", f"{base}...HEAD")
    _, merged, _ = git(main, "branch", "--merged", base_branch, "--format=%(refname:short)")
    data = {"worktree": L.rel(path), "repo": repo, "branch": branch, "base": base[:9],
            "uncommitted": dirty.splitlines(), "commits_since_base": commits.splitlines(),
            "ahead_of_default": int(ahead), "behind_default": int(behind),
            "merged_into_default": branch in merged.splitlines() and int(ahead) == 0 and bool(commits),  # needs --base from the board
            "diffstat": stat.splitlines()[-1] if stat else "no changes"}
    L.out(data, a.json)


def cmd_update(a):
    repo, _, branch, path = repo_of(a.path)
    base_branch = L.default_branch(repo)
    _, dirty, _ = git(path, "status", "--short")
    if dirty:
        L.die(f"commit or clean up first:\n{dirty}")
    code, _, _ = git(path, "merge", base_branch, "--no-edit")
    if code != 0:
        _, conflicts, _ = git(path, "diff", "--name-only", "--diff-filter=U")
        print(f"CONFLICT merging {base_branch} into {branch}. Resolve these files in the worktree, rerun the tests, "
              f"then: git -C {L.rel(path)} add <files> && git -C {L.rel(path)} commit --no-edit\n{conflicts}")
        sys.exit(2)
    _, base, _ = git(path, "merge-base", "HEAD", base_branch)
    L.out({"worktree": L.rel(path), "branch": branch, "new_base": base[:9],
           "note": "rerun the tests; the review now judges only the diff since new_base"}, a.json)


def cmd_merge(a):
    repo, main, branch, path = repo_of(a.path)
    base_branch = L.default_branch(repo)
    if repo != L.HQ and not a.approved_by_ceo:
        L.die("merging into a product repo's default branch needs the CEO's yes. Ask in the hand-off, then rerun with --approved-by-ceo.")
    _, dirty, _ = git(path, "status", "--short")
    if dirty:
        L.die(f"the worktree has uncommitted files. Look at them and commit them in the worktree, by path:\n{dirty}")
    if repo != L.HQ:
        _, mdirty, _ = git(main, "status", "--short")
        if mdirty:
            L.die(f"projects/{repo} main checkout is not clean:\n{mdirty}")
    _, counts, _ = git(path, "rev-list", "--left-right", "--count", f"{base_branch}...HEAD")
    behind, ahead = (counts.split() + ["0", "0"])[:2]
    if int(ahead) == 0:
        L.die(f"{branch} has no commits that {base_branch} lacks: the work was never committed, or it is already merged. Nothing to merge.")
    if repo != L.HQ and int(behind) > 0 and not a.allow_behind:   # HQ main moves all day (journal, jobs); git sorts it out
        L.die(f"{branch} is {behind} commit(s) behind {base_branch}. Its employee runs `worktree.py update {L.rel(path)}` and retests, "
              f"and the change is reviewed again. (--allow-behind skips this check when the files do not overlap.)")
    code, o, e = git(main, "merge", "--no-ff", branch, "-m", f"Merge {branch}: {a.title}")
    if code != 0:
        git(main, "merge", "--abort")
        L.die(f"merge conflict; aborted, the main checkout is untouched. Send the branch back to be updated "
              f"(worktree.py update) and reviewed again.\n{o}\n{e}")
    _, sha, _ = git(main, "rev-parse", "--short", "HEAD")
    L.journal_add(f"merged {branch} into {repo}:{base_branch} at {sha}: {a.title}")
    L.out({"merged": branch, "into": f"{repo}:{base_branch}", "commit": sha,
           "next": f"worktree.py remove {L.rel(path)}   (pushing is a separate CEO approval)"}, a.json)


def cmd_remove(a):
    _, main, branch, path = repo_of(a.path)
    code, _, e = git(main, "worktree", "remove", str(path))
    if code != 0:
        L.die(f"git refused to remove it (modified or untracked files?). Commit leftovers on the branch by path "
              f"('wip: rejected') or delete junk by hand, then retry. Never rm -rf a worktree, never --force without the CEO.\n{e}")
    res: Dict[str, Any] = {"removed": L.rel(path), "branch": branch}
    if a.keep_branch:
        res["branch_kept"] = True
    else:
        code, _, e = git(main, "branch", "-d", branch)
        res["branch_deleted"] = code == 0
        if code != 0:
            res["note"] = f"branch kept: it is not merged ({e.splitlines()[0] if e else 'unmerged'}). That is the safety net; delete it only when the CEO says so."
    L.journal_add(f"worktree removed {res['removed']}" + ("" if res.get("branch_deleted") else f", branch {branch} kept"))
    L.out(res, a.json)


def cmd_list(a):
    _, rows, _ = L.board_read()
    by_wt = {r["Worktree"]: r["Job"] for r in rows if r["Worktree"]}
    repos = [L.HQ] + sorted(p.name for p in (L.ROOT / "projects").glob("*") if (p / ".git").exists())
    found = []
    for repo in repos:
        main = L.repo_main(repo)
        _, o, _ = git(main, "worktree", "list", "--porcelain")
        cur = {}
        for ln in o.splitlines() + [""]:
            if ln.startswith("worktree "):
                cur = {"path": ln[9:]}
            elif ln.startswith("branch "):
                cur["branch"] = ln[7:].replace("refs/heads/", "")
            elif not ln and cur:
                if Path(cur["path"]).resolve() != main.resolve():
                    r = L.rel(cur["path"])
                    found.append({"repo": repo, "worktree": r, "branch": cur.get("branch", "?"),
                                  "job": by_wt.get(r, "NONE: stray worktree, no board row")})
                cur = {}
    missing = [f"{j}: board row points at {w}, which does not exist" for w, j in by_wt.items() if not (L.ROOT / w).exists()]
    if a.json:
        L.out({"worktrees": found, "problems": missing}, True); return
    for f in found:
        print(f"{f['worktree']}  [{f['branch']}]  job: {f['job']}")
    for m in missing:
        print("PROBLEM:", m)
    if not found and not missing:
        print("no worktrees")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ad = sub.add_parser("add"); ad.add_argument("--repo", required=True); ad.add_argument("--employee", required=True)
    ad.add_argument("--slug", required=True); ad.add_argument("--job"); ad.add_argument("--existing", action="store_true")
    st = sub.add_parser("status"); st.add_argument("path"); st.add_argument("--base")
    up = sub.add_parser("update"); up.add_argument("path")
    me = sub.add_parser("merge"); me.add_argument("path"); me.add_argument("--title", required=True)
    me.add_argument("--approved-by-ceo", action="store_true"); me.add_argument("--allow-behind", action="store_true")
    rm = sub.add_parser("remove"); rm.add_argument("path"); rm.add_argument("--keep-branch", action="store_true")
    sub.add_parser("list")
    a = ap.parse_args()
    {"add": cmd_add, "status": cmd_status, "update": cmd_update, "merge": cmd_merge,
     "remove": cmd_remove, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
