#!/usr/bin/env python3
"""Employees: role files in .claude/agents/ and the roster in context/team.md.

  team.py add-adviser                      install the Senior Technical Adviser if missing
  team.py add NAME --owns "paths" [--developer]
                                           copy the employee template to .claude/agents/NAME.md and add the roster row
  team.py list

`add` only lays down the file. Filling in the description, mission, owned files and definition of done
is the hire skill's job, and hiring needs the CEO's approval first.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

AGENTS = L.ROOT / ".claude" / "agents"
TEAM = L.ROOT / "context" / "team.md"
TEMPLATE = L.ROOT / ".claude" / "skills" / "hire" / "employee-template.md"
ADVISER = L.ROOT / ".claude" / "skills" / "new-project" / "senior-technical-adviser.md"
DEV_BLOCK = re.compile(r"<!-- DEVELOPER ROLES ONLY\..*?-->\n## Engineering rules\n.*?(?=\n## )", re.S)


def roster_add(name, owns, reach):
    t = TEAM.read_text()
    live = t.split("<!--")[0]   # the commented example rows do not count
    if re.search(rf"^\|\s*{re.escape(name)}\s*\|", live, re.M):
        return False
    row = f"| {name} | Employee | {L.clean_cell(owns)} | {reach} |"
    lines = t.splitlines()
    # keep the commented example block below the real table
    table_end = next((i for i, l in enumerate(lines) if l.strip().startswith("<!--")), len(lines))
    last = max(i for i, l in enumerate(lines[:table_end]) if l.strip().startswith("|"))
    lines.insert(last + 1, row)
    TEAM.write_text("\n".join(lines) + "\n")
    return True


def cmd_add_adviser(a):
    dest = AGENTS / "senior-technical-adviser.md"
    if dest.exists():
        print("senior-technical-adviser already on the team; nothing to do"); return
    AGENTS.mkdir(parents=True, exist_ok=True)
    dest.write_text(ADVISER.read_text())
    roster_add("senior-technical-adviser", "`plans/`",
               "delegated automatically, or `claude --agent senior-technical-adviser`")
    L.journal_add("hired senior-technical-adviser (model fable, effort max)")
    print(f"installed {L.rel(dest)} and added the roster row. Claude Code picks it up within a few seconds.")


def cmd_add(a):
    name = L.valid_name(a.name, "employee name")
    dest = AGENTS / f"{name}.md"
    if dest.exists():
        L.die(f"{L.rel(dest)} already exists; edit it instead")
    t = TEMPLATE.read_text().replace("name: <FILL: role-name>", f"name: {name}", 1)
    if not a.developer:
        t = DEV_BLOCK.sub("", t)
    else:
        t = t.replace("<!-- DEVELOPER ROLES ONLY. Delete this section for non-coding roles. -->\n", "")
    AGENTS.mkdir(parents=True, exist_ok=True)
    dest.write_text(t)
    roster_add(name, a.owns, f"delegated automatically, or `claude --agent {name}`")
    L.journal_add(f"hired {name} (owns {a.owns})")
    left = sorted(set(re.findall(r"<FILL:[^<>\n]*>", t)))
    print(f"created {L.rel(dest)} and the roster row. Placeholders still to fill in: {len(left)}")
    for p in left:
        print("  ", p)


def cmd_list(a):
    for p in sorted(AGENTS.glob("*.md")):
        t = p.read_text()
        m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
        if not m or "name:" not in m.group(1):
            continue
        fm = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", m.group(1), re.M))
        ph = len(re.findall(r"<FILL:[^<>\n]*>", t))
        print(f"{fm.get('name')}  model={fm.get('model', 'inherit')} effort={fm.get('effort', '-')}"
              + (f"  ({ph} unfilled placeholders)" if ph else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("add-adviser")
    ad = sub.add_parser("add"); ad.add_argument("name"); ad.add_argument("--owns", required=True)
    ad.add_argument("--developer", action="store_true")
    sub.add_parser("list")
    a = ap.parse_args()
    {"add-adviser": cmd_add_adviser, "add": cmd_add, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
