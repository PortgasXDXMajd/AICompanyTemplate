#!/usr/bin/env python3
"""Collect the ground truth about every open job, for the job-status skill.

  status.py            a readable report
  status.py --json     the same facts as JSON

It gathers facts and suggests a verdict per job. Judging the work, and what to do, is for the Chief of Staff.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

REVIEW_FILES = ("review", "quality", "architecture", "qa")


def herdr_agents():
    if os.environ.get("HERDR_ENV") != "1":
        return None
    code, o, _ = L.run(["herdr", "agent", "list"])
    if code != 0:
        return {}
    try:
        data = json.loads(o)
    except ValueError:
        return {}
    res = data.get("result") if isinstance(data, dict) else None
    agents = res.get("agents") if isinstance(res, dict) else res
    return {a.get("name"): a.get("agent_status") for a in (agents or []) if isinstance(a, dict) and a.get("name")}


def inspect(row, agents):
    job = row["Job"]; d = L.job_dir(job)
    f = {"job": job, "employee": row["Employee"], "task": row["Task"], "board_state": row["State"],
         "runner": row["Runner"], "next_step": row["Next step"], "updated": row["Updated"]}
    f["folder_exists"] = d.exists()
    names = sorted(p.name for p in d.iterdir()) if d.exists() else []
    f["files"] = names
    f["handback"] = "handback.md" in names
    f["handoff_written"] = "handoff.md" in names
    prog = d / "progress.md"
    if prog.exists():
        lines = [l for l in prog.read_text().splitlines() if l.startswith("- ")]
        f["progress_lines"] = len(lines)
        f["progress_tail"] = lines[-5:]
        f["minutes_since_progress"] = int((time.time() - prog.stat().st_mtime) / 60)
    else:
        f["progress_lines"] = 0; f["progress_tail"] = []; f["minutes_since_progress"] = None
    verdicts = {}
    for p in sorted(d.glob("*.md")) if d.exists() else []:
        if p.stem.split("-")[0] in REVIEW_FILES and not p.stem.endswith("brief"):
            verdicts[p.name] = L.verdict_of(p) or "NO VERDICT LINE (cut off?)"
    f["verdicts"] = verdicts
    fixes = sorted(p.name for p in d.glob("fix-*-brief.md")) if d.exists() else []
    f["open_fix_round"] = next((b for b in fixes if not (d / b.replace("-brief", "-handback")).exists()), None)

    wt = row["Worktree"]
    f["worktree"] = wt
    f["worktree_exists"] = bool(wt) and (L.ROOT / wt).is_dir()
    if f["worktree_exists"]:
        _, o, _ = L.run([sys.executable, str(Path(__file__).parent / "worktree.py"), "--json", "status", str(L.ROOT / wt)]
                           + (["--base", row["Base"]] if row["Base"] else []))
        try:
            g = json.loads(o)
            f.update({"uncommitted": g["uncommitted"], "commits": g["commits_since_base"],
                      "behind_default": g["behind_default"], "merged_into_default": g["merged_into_default"]})
        except (ValueError, KeyError):
            f["git_error"] = o
    runner = row["Runner"]
    f["runner_alive"] = None
    if runner.startswith("herdr:") and agents is not None:
        name = runner[6:].split()[0]
        f["runner_status"] = agents.get(name, "gone")
        f["runner_alive"] = name in agents
    elif runner in ("subagent", "self"):
        f["runner_alive"] = False   # these die with the session that started them
    if agents:
        slug = job.split("--", 1)[-1]
        m = re.match(r"(\d+)", slug)
        tag = m.group(1) if m else slug[:12]          # the same tag agent.py puts into helper names
        pat = re.compile(rf"(rev|qual|arch|qa)-{re.escape(tag)}(-\d+)?")
        f["live_helpers"] = {n: s for n, s in agents.items() if pat.fullmatch(n)}
    f["suggested"] = suggest(f)
    return f


def suggest(f):
    if f.get("merged_into_default"):
        return "MERGED, NOT CLOSED: finish the close-out yourself (remove worktree, job.py close). Do not ask the CEO again."
    if f.get("runner_status") == "blocked" or f["board_state"] == "blocked":
        return "NEEDS THE CEO: say exactly what is being asked and in which tab."
    if f["board_state"] == "awaiting-merge":
        return "NEEDS THE CEO: waiting for the merge decision (see handoff.md)."
    if f.get("runner_alive") and f.get("runner_status") == "working":
        return "RUNNING FINE: leave it."
    if f.get("live_helpers"):
        return "REVIEW RUNNING: a helper is still alive; wait for it, do not start another."
    if f["open_fix_round"]:
        return f"FIX ROUND CUT OFF ({f['open_fix_round']}): resume it in the same worktree."
    if f["handback"]:
        if not f["verdicts"]:
            return "FINISHED, NOT REVIEWED: start the review now."
        bad = [k for k, v in f["verdicts"].items() if v.startswith("NO VERDICT")]
        if bad:
            return f"REVIEW UNFINISHED: {', '.join(bad)} has no verdict line; redo that step."
        return "REVIEW IN PROGRESS OR DONE: read the verdicts; continue from the first step REVIEW.md still requires, or hand off."
    if f["progress_lines"] or f.get("commits") or f.get("uncommitted"):
        recent = f["minutes_since_progress"] is not None and f["minutes_since_progress"] < 15
        if recent or f["runner"] == "direct session":
            return "POSSIBLY STILL RUNNING: recent progress or a direct session. Ask the CEO whether that session is still open before resuming."
        return "INTERRUPTED: work exists, nobody is running it. Judge the work, then resume in the same worktree."
    return "NEVER STARTED: start it."


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    _, rows, _ = L.board_read()
    agents = herdr_agents()
    jobs = [inspect(r, agents) for r in rows]

    _, o, _ = L.run([sys.executable, str(Path(__file__).parent / "worktree.py"), "--json", "list"])
    try:
        wl = json.loads(o)
    except ValueError:
        wl = {"worktrees": [], "problems": [o]}
    strays = [w for w in wl["worktrees"] if w["job"].startswith("NONE")]
    on_board = {r["Job"] for r in rows}
    orphan_jobs = [p.name for p in sorted((L.ROOT / "jobs").glob("20*")) if p.is_dir()
                   and p.name not in on_board and not (p / "closed.md").exists()]
    jf = sorted((L.ROOT / "context" / "journal").glob("20*.md"))
    journal_tail = jf[-1].read_text().splitlines()[-12:] if jf else []

    report = {"where": "herdr" if agents is not None else "plain terminal (subagents die with their session)",
              "open_jobs": jobs, "stray_worktrees": strays, "board_problems": wl["problems"],
              "job_folders_without_row_or_close": orphan_jobs,
              "last_journal_file": L.rel(jf[-1]) if jf else None, "journal_tail": journal_tail}
    if a.json:
        print(json.dumps(report, indent=2)); return

    print(f"Running in: {report['where']}")
    print(f"Open jobs: {len(jobs)}\n")
    for f in jobs:
        print(f"== {f['job']}  ({f['employee']}: {f['task']})")
        print(f"   board: {f['board_state']} | runner: {f['runner'] or '-'}"
              + (f" -> {f['runner_status']}" if f.get("runner_status") else "") + f" | next: {f['next_step']}")
        print(f"   files: {', '.join(f['files']) or 'NO JOB FOLDER'}")
        for k, v in f["verdicts"].items():
            print(f"   {k}: {v}")
        if f["worktree"]:
            if f["worktree_exists"]:
                print(f"   worktree: {f['worktree']} | commits since base: {len(f.get('commits', []))} | "
                      f"uncommitted: {len(f.get('uncommitted', []))} | behind default: {f.get('behind_default')}")
            else:
                print(f"   worktree: {f['worktree']} DOES NOT EXIST")
        for l in f["progress_tail"]:
            print(f"   {l}")
        if f["minutes_since_progress"] is not None:
            print(f"   last progress {f['minutes_since_progress']} min ago")
        print(f"   SUGGESTED: {f['suggested']}\n")
    for s in strays:
        print(f"STRAY WORKTREE (no board row): {s['worktree']} [{s['branch']}]")
    for p in report["board_problems"]:
        print(f"BOARD PROBLEM: {p}")
    for j in orphan_jobs:
        print(f"JOB FOLDER WITH NO ROW AND NO closed.md: jobs/{j}")
    if journal_tail:
        print(f"\nEnd of {report['last_journal_file']}:")
        print("\n".join(journal_tail))


if __name__ == "__main__":
    main()
