#!/usr/bin/env python3
"""Check that this machine and this repo are ready to run the company.

  preflight.py          a checklist: what is there, what is missing, and what each thing is needed for
  preflight.py --json

Exit code 1 if something REQUIRED is missing.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L


def first_line(cmd):
    if not shutil.which(cmd[0]):
        return None
    _, o, e = L.run(cmd)
    txt = o or e
    return txt.splitlines()[0][:70] if txt else "present"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    checks = []

    def add(name, ok, level, need, fix=""):
        checks.append({"check": name, "ok": bool(ok), "level": level, "needed_for": need, "fix": "" if ok else fix})

    add("git", first_line(["git", "--version"]), "required", "everything", "install git")
    code, _, _ = L.run(["git", "-C", str(L.ROOT), "rev-parse", "--verify", "HEAD"])
    add("HQ is a git repo with a first commit", code == 0, "required", "worktrees, merges, history",
        "git init -b main && git add -A && git commit -m 'Initial commit'")
    add("claude CLI", first_line(["claude", "--version"]), "required", "running employees", "install Claude Code")
    add("python3", True, "required", "these scripts")
    add("node / npx", first_line(["npx", "--version"]), "recommended", "installing and updating third-party skills (skills.py)", "install Node.js")
    gh = first_line(["gh", "--version"])
    add("gh CLI", gh, "recommended", "creating and cloning product repos", "install gh from https://cli.github.com")
    if gh:
        code, _, _ = L.run(["gh", "auth", "status"])
        add("gh authenticated", code == 0, "recommended", "creating product repos", "gh auth login")
    add("herdr", first_line(["herdr", "--version"]), "optional", "one visible tab per employee", "curl -fsSL https://herdr.dev/install.sh | sh, then: herdr integration install claude")
    add("running inside Herdr", os.environ.get("HERDR_ENV") == "1", "optional", "one visible tab per employee", "start `herdr` in the HQ folder, then `claude` in its first pane")
    lock = L.ROOT / "skills-lock.json"
    missing = []
    if lock.exists():
        for name in json.loads(lock.read_text()).get("skills", {}):
            if not (L.ROOT / ".claude" / "skills" / name / "SKILL.md").exists():
                missing.append(name)
    add("third-party skills present", lock.exists() and not missing, "required", "grilling, tdd, improve, reviews, herdr",
        f"python3 scripts/skills.py install   (missing: {', '.join(missing) or 'skills-lock.json'})")
    for d in ("jobs/BOARD.md", "context/company.md", "context/team.md", "ROADMAP.md", "REVIEW.md", "CLAUDE.md", ".claude/settings.json"):
        add(d, (L.ROOT / d).exists(), "required", "the operating manual and records", "restore it from the template")
    onboarded = "NOT ONBOARDED" not in (L.ROOT / "context" / "company.md").read_text() if (L.ROOT / "context" / "company.md").exists() else False
    add("company onboarded", onboarded, "info", "doing real work", "run /onboard")

    if a.json:
        print(json.dumps(checks, indent=2))
    else:
        for c in checks:
            mark = "ok  " if c["ok"] else {"required": "MISS", "recommended": "warn", "optional": "  - ", "info": "  - "}[c["level"]]
            print(f"[{mark}] {c['check']}  ({c['level']}: {c['needed_for']})" + (f"\n        fix: {c['fix']}" if c["fix"] else ""))
        print("\nHands-on QA tooling is checked separately: python3 scripts/qa_probe.py")
    sys.exit(1 if any(c["level"] == "required" and not c["ok"] for c in checks) else 0)


if __name__ == "__main__":
    main()
