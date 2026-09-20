#!/usr/bin/env python3
"""Product repos under projects/ and the registry in projects/README.md.

  project.py init NAME                  validate the name, mkdir, git init -b main
  project.py commit NAME [-m MSG]       first commit of README.md and CLAUDE.md
  project.py clone OWNER/NAME|URL [NAME]
  project.py register NAME --repo OWNER/NAME --purpose "..." [--status active] [--url URL]
  project.py list

Creating the GitHub repo and pushing are NOT in here on purpose: run `gh repo create ...` yourself,
so Claude Code asks the CEO (see .claude/settings.json).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

REG = L.ROOT / "projects" / "README.md"
COLS = ["Name", "GitHub repo", "Purpose", "Status", "Created"]
STATUSES = ["active", "local only", "paused", "archived"]


def check_name(name):
    L.valid_name(name, "project name")
    if name.startswith("_"):
        L.die("project names must not start with '_' (worktrees/_hq is reserved)")
    return name


def reg_rows():
    lines = REG.read_text().splitlines()
    try:
        i = next(k for k, l in enumerate(lines) if l.strip().startswith("| Name |"))
    except StopIteration:
        L.die("projects/README.md has no registry table")
    rows = []
    for l in lines[i + 2:]:
        if not l.strip().startswith("|"):
            break
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        rows.append(dict(zip(COLS, c + [""] * 5)))
    return lines[:i + 2], rows, lines[i + 2 + len(rows):]


def cmd_init(a):
    name = check_name(a.name); p = L.ROOT / "projects" / name
    _, rows, _ = reg_rows()
    if p.exists() or any(r["Name"] == name for r in rows):
        L.die(f"project {name} already exists")
    p.mkdir(parents=True)
    L.run(["git", "-C", str(p), "init", "-b", "main"], check=True)
    L.journal_add(f"project {name}: local repo created at projects/{name}")
    print(f"created projects/{name} (empty repo on main). Now write README.md and CLAUDE.md there, then: project.py commit {name}")


def cmd_commit(a):
    p = L.repo_main(a.name)
    missing = [f for f in ("README.md", "CLAUDE.md") if not (p / f).exists()]
    if missing:
        L.die(f"write these first: {', '.join(missing)}")
    L.run(["git", "-C", str(p), "add", "README.md", "CLAUDE.md"], check=True)
    L.run(["git", "-C", str(p), "commit", "-m", a.message], check=True)
    _, sha, _ = L.run(["git", "-C", str(p), "rev-parse", "--short", "HEAD"])
    print(f"committed {sha} in projects/{a.name}.\nNext (asks the CEO): gh repo create <owner>/{a.name} --private|--public "
          f"--source projects/{a.name} --remote origin --push")


def cmd_clone(a):
    src = a.source
    name = check_name(a.name or re.sub(r"\.git$", "", src.rstrip("/").split("/")[-1]).lower())
    p = L.ROOT / "projects" / name
    if p.exists():
        L.die(f"projects/{name} already exists")
    if "://" in src or src.startswith("git@"):
        code, _, e = L.run(["git", "clone", src, str(p)])
    else:
        code, _, e = L.run(["gh", "repo", "clone", src, str(p)])
        if code != 0:
            code, _, e = L.run(["git", "clone", f"https://github.com/{src}.git", str(p)])
    if code != 0:
        L.die(f"clone failed: {e}")
    has = (p / "CLAUDE.md").exists()
    L.journal_add(f"project {name}: cloned {src}")
    print(f"cloned into projects/{name}. CLAUDE.md present: {has}")


def cmd_register(a):
    if a.status not in STATUSES:
        L.die(f"status must be one of: {', '.join(STATUSES)}")
    head, rows, tail = reg_rows()
    url = a.url or (f"https://github.com/{a.repo}" if "/" in a.repo else "")
    cell = f"[{a.repo}]({url})" if url else a.repo
    row = next((r for r in rows if r["Name"] == a.name), None)
    if row:
        row.update({"GitHub repo": cell, "Purpose": a.purpose or row["Purpose"], "Status": a.status})
    else:
        rows.append({"Name": a.name, "GitHub repo": cell, "Purpose": a.purpose or "", "Status": a.status, "Created": L.today()})
    body = [L.table_row([L.clean_cell(r[c]) if c != "GitHub repo" else r[c] for c in COLS]) for r in rows]
    L.write_md(REG, "\n".join(head + body + tail))
    L.journal_add(f"project {a.name}: registry row set ({a.status})")
    print(f"registered {a.name} [{a.status}]")


def cmd_list(a):
    _, rows, _ = reg_rows()
    for r in rows:
        here = (L.ROOT / "projects" / r["Name"] / ".git").exists()
        print(f"{r['Name']}  [{r['Status']}]  {r['GitHub repo']}  local clone: {'yes' if here else 'NO'}")
    if not rows:
        print("no projects registered")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("name")
    c = sub.add_parser("commit"); c.add_argument("name"); c.add_argument("-m", "--message", default="Initial commit: README and CLAUDE.md with tech stack")
    cl = sub.add_parser("clone"); cl.add_argument("source"); cl.add_argument("name", nargs="?")
    r = sub.add_parser("register"); r.add_argument("name"); r.add_argument("--repo", required=True)
    r.add_argument("--purpose"); r.add_argument("--status", default="active"); r.add_argument("--url")
    sub.add_parser("list")
    a = ap.parse_args()
    {"init": cmd_init, "commit": cmd_commit, "clone": cmd_clone, "register": cmd_register, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
