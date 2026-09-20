#!/usr/bin/env python3
"""Consistency check of the company repo. Reads only; changes nothing.

  doctor.py            all checks
  doctor.py budgets    only the size budgets of the instruction files
  doctor.py refs       only paths mentioned in instruction files that do not exist
  doctor.py markdown   only the Markdown lint check (scripts/mdfix.py --check --all)

Checks: skill and employee frontmatter, settings.json, skills-lock vs folders, size budgets,
references to missing paths, Markdown lint, job board vs job folders vs worktrees, unfilled placeholders in role files.
Exit code 1 if any problem is found.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

R = L.ROOT
BUDGETS_WORDS = [("CLAUDE.md", 1800), ("context/engineering.md", 700)]
# paths that are created on demand, or live in product repos, so a missing file is not an error
ON_DEMAND = ("CONTEXT.md", "docs/adr/", "work/", "routines/reviews/", ".claude/agent-memory/", "FINDINGS.md",
             "references/", "worktrees/_hq", ".maestro/", "handback.md", "progress.md", "brief.md", "review.md",
             "quality.md", "architecture.md", "qa.md", "handoff.md", "closed.md", "review-2.md", "qa-2.md",
             "quality-2.md", "resume-", "fix-", "qa/", ".claude/agents/senior-technical-adviser.md", "BOARD.md", "MEMORY.md")


def vendored():
    lock = R / "skills-lock.json"
    return set(json.loads(lock.read_text()).get("skills", {})) if lock.exists() else set()


def frontmatter(path):
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.S)
    if not m:
        return None
    return dict(re.findall(r"^([A-Za-z][\w-]*):\s*(.*)$", m.group(1), re.M))


def instruction_files():
    """HQ instruction files, never worktree copies, never vendored skills."""
    v = vendored()
    files = [R / "CLAUDE.md", R / "REVIEW.md", R / "README.md", R / "ROADMAP.md"]
    for pat in ("context/*.md", "context/journal/README.md", "routines/*.md", "jobs/README.md", "plans/README.md",
                "projects/README.md", "worktrees/README.md", "specs/*.md", "customers/*.md", "demos/README.md",
                "work/README.md", "scripts/README.md", ".claude/agents/*.md"):
        files += sorted(R.glob(pat))
    for d in sorted((R / ".claude" / "skills").glob("*")):
        if d.is_dir() and d.name not in v:
            files += sorted(d.glob("*.md"))
    return [f for f in files if f.exists()]


def yaml_string_problem(value):
    """Why an unquoted front matter value would not reach Claude Code as a plain string, or None if it is fine."""
    v = value.strip()
    if not v:
        return "is empty"
    if v[0] in "\"'":
        return None if len(v) > 1 and v[-1] == v[0] else "has an unclosed quote"
    if v[0] in "[{":
        return "starts with '[' or '{', which YAML reads as a list or a map: put it in double quotes"
    if v[0] in "*&!|>%@`" or v.startswith(("- ", "? ")):
        return f"starts with {v[0]!r}, which is YAML syntax: put it in double quotes"
    if ": " in v or v.endswith(":"):
        return "contains ': ', which YAML reads as a nested key: put it in double quotes"
    if " #" in v:
        return "contains ' #', which YAML reads as a comment: put it in double quotes"
    return None


STRING_KEYS = ("name", "description", "argument-hint", "when_to_use", "model", "effort", "memory")


def check_strings(label, fm, problems):
    for key in STRING_KEYS:
        if key in fm:
            why = yaml_string_problem(fm[key])
            if why:
                problems.append(f"{label}: front matter `{key}` {why}")


def check_frontmatter(problems):
    for d in sorted((R / ".claude" / "skills").glob("*")):
        if not d.is_dir():
            continue
        f = d / "SKILL.md"
        fm = frontmatter(f) if f.exists() else None
        if not fm:
            problems.append(f"skill {d.name}: SKILL.md missing or has no frontmatter")
        elif fm.get("name", "").strip("\"'") != d.name:
            problems.append(f"skill {d.name}: frontmatter name is {fm.get('name')!r}")
        elif not fm.get("description"):
            problems.append(f"skill {d.name}: no description")
        if fm:
            check_strings(f"skill {d.name}", fm, problems)
        for extra in sorted(d.glob("*.md")):                 # role templates shipped inside a skill
            efm = frontmatter(extra) if extra.name != "SKILL.md" else None
            if efm and "name" in efm:
                check_strings(L.rel(extra), efm, problems)
    for f in sorted((R / ".claude" / "agents").glob("*.md")):
        fm = frontmatter(f)
        if not fm or "name" not in fm:
            continue   # README and other notes are ignored by Claude Code too
        check_strings(f"employee {f.name}", fm, problems)
        if fm["name"].strip("\"'") != f.stem:
            problems.append(f"employee {f.name}: frontmatter name is {fm['name']!r}")
        if not fm.get("description") or "<FILL" in fm.get("description", ""):
            problems.append(f"employee {f.name}: description is empty or still a placeholder (it is the routing rule)")
        if "isolation" in fm:
            problems.append(f"employee {f.name}: remove `isolation`; the company manages worktrees itself")
        ph = re.findall(r"<FILL:[^<>\n]*>", f.read_text())
        if ph:
            problems.append(f"employee {f.name}: {len(ph)} unfilled placeholders, e.g. {ph[0]}")
        if len(f.read_text().splitlines()) > 75:
            problems.append(f"employee {f.name}: {len(f.read_text().splitlines())} lines (budget about 60)")


def check_settings(problems):
    p = R / ".claude" / "settings.json"
    try:
        s = json.loads(p.read_text())
        ask = s.get("permissions", {}).get("ask", [])
        if not any("push" in r for r in ask):
            problems.append("settings.json: no `ask` rule for git push; the CEO-approval gate is not enforced")
    except (OSError, ValueError) as e:
        problems.append(f".claude/settings.json: {e}")
    for name in vendored():
        if not (R / ".claude" / "skills" / name / "SKILL.md").exists():
            problems.append(f"third-party skill {name} is in skills-lock.json but not installed (python3 scripts/skills.py install)")


def check_budgets(problems, report):
    items = list(BUDGETS_WORDS) + [(L.rel(p), 800) for p in sorted((R / "projects").glob("*/CLAUDE.md"))]
    for relp, budget in items:
        p = R / relp
        if p.exists():
            n = len(p.read_text().split())
            report.append(f"{relp}: {n} words (budget {budget})")
            if n > budget:
                problems.append(f"{relp} is over budget: {n} > {budget} words. Move something to the file that owns it.")


def check_refs(problems):
    for f in instruction_files():
        text = f.read_text()
        for ref in set(re.findall(r"`([A-Za-z_.][\w./-]*\.(?:md|py|json)|[a-z.][\w./-]*/)`", text)):
            if any(x in ref for x in ("<", "NNN", "YYYY", "*")) or ref.startswith(ON_DEMAND) or ref.split("/")[-1].startswith(ON_DEMAND):
                continue
            if ref.startswith(("projects/", "worktrees/", "jobs/2", "~", "src/", "docs/")):
                continue
            if not ((R / ref).exists() or (f.parent / ref).exists() or (R / "scripts" / ref).exists()):
                problems.append(f"{L.rel(f)} mentions `{ref}`, which does not exist")


def check_markdown(problems):
    import mdfix
    for p in mdfix.all_files():
        for line, rule, msg in mdfix.check_text(p.read_text()):
            problems.append(f"{L.rel(p)}:{line} {rule} {msg}")


def check_jobs(problems):
    try:
        _, rows, _ = L.board_read()
    except SystemExit:
        problems.append("jobs/BOARD.md is missing or has no table"); return
    for r in rows:
        if r["State"] not in L.STATES:
            problems.append(f"board: {r['Job']} has unknown state {r['State']!r}")
        if not L.job_dir(r["Job"]).exists():
            problems.append(f"board: {r['Job']} has no job folder")
        if r["Worktree"] and not (R / r["Worktree"]).is_dir():
            problems.append(f"board: {r['Job']} points at {r['Worktree']}, which does not exist")
    on_board = {r["Job"] for r in rows}
    for d in sorted((R / "jobs").glob("20*")):
        if d.is_dir() and d.name not in on_board and not (d / "closed.md").exists():
            problems.append(f"jobs/{d.name}: not on the board and not closed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", nargs="?", default="all", choices=["all", "budgets", "refs", "markdown"])
    a = ap.parse_args()
    problems, report = [], []
    if a.what in ("all",):
        check_frontmatter(problems); check_settings(problems); check_jobs(problems)
    if a.what in ("all", "budgets"):
        check_budgets(problems, report)
    if a.what in ("all", "refs"):
        check_refs(problems)
    if a.what in ("all", "markdown"):
        check_markdown(problems)
    for r in report:
        print(r)
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("\nno problems found")


if __name__ == "__main__":
    main()
