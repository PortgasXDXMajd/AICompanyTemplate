#!/usr/bin/env python3
"""Job records: jobs/<job-id>/ and the rows of jobs/BOARD.md.

  job.py new --employee E --slug S --task "..." [--repo PROJECT|_hq|none] [--runner R]
  job.py set JOB [--state S] [--runner R] [--next "..."] [--worktree P --branch B --base SHA]
  job.py progress JOB "text"            append a timestamped line to the job's progress.md
  job.py show JOB                       files, verdicts, last progress lines
  job.py list                           the open jobs on the board
  job.py close JOB --outcome merged|dropped --log "what was finished" [--path P]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

NEXT = {"briefed": "write the brief, create the worktree, start",
        "running": "wait for the hand-back, then review",
        "blocked": "waiting on the CEO",
        "handed-back": "start the independent review",
        "in-review": "collect the helper verdicts",
        "fixing": "wait for the fix hand-back, then re-check",
        "awaiting-merge": "waiting for the CEO's merge decision (handoff.md)",
        "interrupted": "decide with the CEO: resume, restart or drop",
        "failed": "decide with the CEO: fix the brief or plan, or drop"}

BRIEF = """# Brief: {job}

- **From**: Delegation brief from the Chief of Staff. Job `{job}`. Your job folder is `{folder}`, never a copy of it inside a worktree.
- **Goal**: {task}
- **Worktree**: _path, branch, base (filled in by worktree.py add --job)_
- **Read first**:
- **Definition of done**:
- **Constraints**:
- **Progress**: append to `{folder}/progress.md` when you start and when you finish each step (`python3 scripts/job.py progress {job} "..."`).
- **Return**: write `{folder}/handback.md` in the hand-off format from `REVIEW.md`, then stop.
"""


def cmd_new(a):
    L.valid_name(a.employee, "employee"); L.valid_slug(a.slug)
    job = f"{L.now().strftime('%Y%m%d')}-{a.employee}--{a.slug}"
    d = L.job_dir(job)
    head, rows, tail = L.board_read()
    if L.board_find(rows, job) or d.exists():
        L.die(f"job {job} already exists; pick another slug")
    d.mkdir(parents=True)
    L.write_md(d / "brief.md", BRIEF.format(job=job, folder=d, task=a.task))
    L.write_md(d / "progress.md", f"# Progress: {job}\n")
    rows.append({"Job": job, "Employee": a.employee, "Task": a.task, "Repo": a.repo,
                 "Worktree": "", "Branch": "", "Base": "", "Runner": a.runner or "",
                 "State": "briefed", "Updated": L.stamp(), "Next step": "write the brief, create the worktree, start"})
    L.board_write(head, rows, tail)
    L.journal_add(f"job created: {a.task}", job)
    L.out({"job": job, "folder": str(d), "brief": str(d / "brief.md"), "state": "briefed"}, a.json)


def cmd_set(a):
    head, rows, tail = L.board_read()
    r = L.board_find(rows, a.job) or L.die(f"no open job {a.job} on the board")
    changed = []
    if a.state:
        if a.state not in L.STATES:
            L.die(f"state must be one of: {', '.join(L.STATES)}")
        r["State"] = a.state; changed.append(f"state={a.state}")
        if a.next is None:
            r["Next step"] = NEXT.get(a.state, r["Next step"])
    for col, val in (("Runner", a.runner), ("Next step", a.next), ("Worktree", a.worktree),
                     ("Branch", a.branch), ("Base", a.base)):
        if val is not None:
            r[col] = val; changed.append(f"{col.lower()}={val}")
    if not changed:
        L.die("nothing to set")
    r["Updated"] = L.stamp()
    L.board_write(head, rows, tail)
    L.journal_add("board: " + ", ".join(changed), a.job)
    L.out({k: r[k] for k in L.BOARD_COLS}, a.json)


def cmd_progress(a):
    d = L.job_dir(a.job)
    if not d.exists():
        L.die(f"no job folder {d}")
    line = f"- {L.stamp()} {L.clean_cell(a.text)}"
    L.append_item(d / "progress.md", line, header=f"# Progress: {a.job}\n")
    print(line)


def cmd_show(a):
    d = L.job_dir(a.job)
    if not d.exists():
        L.die(f"no job folder {d}")
    _, rows, _ = L.board_read()
    r = L.board_find(rows, a.job)
    files = sorted(p.name + ("/" if p.is_dir() else "") for p in d.iterdir())
    verdicts = {p.name: L.verdict_of(p) for p in d.glob("*.md")
                if p.stem.split("-")[0] in ("review", "quality", "architecture", "qa") and not p.stem.endswith("brief")}
    prog = (d / "progress.md").read_text().splitlines()[-a.lines:] if (d / "progress.md").exists() else []
    data = {"job": a.job, "board": r or "not on the board (closed or never recorded)",
            "files": files, "verdicts": verdicts, "progress_tail": prog}
    if a.json:
        L.out(data, True)
    else:
        print(f"job: {a.job}\nboard: {r or 'not on the board'}\nfiles: {', '.join(files)}")
        for k, v in verdicts.items():
            print(f"verdict {k}: {v or 'NO VERDICT LINE (unfinished)'}")
        print("progress (tail):"); print("\n".join(prog) or "  (empty)")


def cmd_list(a):
    _, rows, _ = L.board_read()
    if a.json:
        L.out({"open_jobs": rows}, True); return
    if not rows:
        print("no open jobs"); return
    for r in rows:
        print(f"{r['Job']}  [{r['State']}]  {r['Employee']}  {r['Task']}  -> {r['Next step']}")


def cmd_close(a):
    head, rows, tail = L.board_read()
    r = L.board_find(rows, a.job) or L.die(f"no open job {a.job} on the board")
    rows.remove(r)
    L.board_write(head, rows, tail)
    d = L.job_dir(a.job); d.mkdir(parents=True, exist_ok=True)
    L.write_md(d / "closed.md", f"# Closed\n\n- outcome: {a.outcome}\n- when: {L.stamp()}\n- note: {L.clean_cell(a.log)}\n")
    if a.outcome == "merged":
        where = a.path or L.rel(d)
        L.append_item(L.ROOT / "context" / "log.md", f"- {L.today()} | {r['Employee']} | {L.clean_cell(a.log)} | {where}")
    L.journal_add(f"job closed ({a.outcome}): {a.log}", a.job)
    L.out({"job": a.job, "outcome": a.outcome, "logged": a.outcome == "merged"}, a.json)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("--employee", required=True); n.add_argument("--slug", required=True)
    n.add_argument("--task", required=True); n.add_argument("--repo", default="none"); n.add_argument("--runner")
    s = sub.add_parser("set"); s.add_argument("job")
    for f in ("state", "runner", "next", "worktree", "branch", "base"):
        s.add_argument(f"--{f}")
    p = sub.add_parser("progress"); p.add_argument("job"); p.add_argument("text")
    sh = sub.add_parser("show"); sh.add_argument("job"); sh.add_argument("--lines", type=int, default=15)
    sub.add_parser("list")
    c = sub.add_parser("close"); c.add_argument("job")
    c.add_argument("--outcome", required=True, choices=["merged", "dropped"])
    c.add_argument("--log", required=True); c.add_argument("--path")
    a = ap.parse_args()
    {"new": cmd_new, "set": cmd_set, "progress": cmd_progress, "show": cmd_show,
     "list": cmd_list, "close": cmd_close}[a.cmd](a)


if __name__ == "__main__":
    main()
