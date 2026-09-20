#!/usr/bin/env python3
"""Third-party skills, vendored into .claude/skills/ and pinned in skills-lock.json.

  skills.py list       what the lock file pins, and whether each skill folder is present
  skills.py install    (re)install every third-party skill with `npx skills add`
  skills.py update     `npx skills update`; read the diff before committing

Never edit a vendored skill. Company behaviour lives in the wrapper skills.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

SOURCES = [
    ("https://github.com/mattpocock/skills", ["grilling", "tdd", "improve-codebase-architecture", "codebase-design", "domain-modeling"]),
    ("https://github.com/cursor/plugins", ["thermo-nuclear-code-quality-review"]),
    ("https://github.com/shadcn/improve", ["improve"]),
    ("herdrdev/herdr", ["herdr"]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["list", "install", "update"])
    a = ap.parse_args()
    if a.cmd == "list":
        lock = json.loads((L.ROOT / "skills-lock.json").read_text()).get("skills", {})
        for name, meta in sorted(lock.items()):
            ok = (L.ROOT / ".claude" / "skills" / name / "SKILL.md").exists()
            print(f"{name:40s} {meta.get('source', '?'):24s} {'present' if ok else 'MISSING'}")
        expected = {s for _, names in SOURCES for s in names}
        for s in sorted(expected - set(lock)):
            print(f"{s:40s} NOT IN skills-lock.json")
        return
    if a.cmd == "update":
        cmds = [["npx", "--yes", "skills", "update", "-p", "-y"]]
    else:
        cmds = [["npx", "--yes", "skills", "add", src, "--skill", *names, "-a", "claude-code", "--copy", "-y"] for src, names in SOURCES]
    for c in cmds:
        print("$", " ".join(c), flush=True)
        code, o, e = L.run(c, cwd=str(L.ROOT))
        print((o or e)[-600:])
        if code != 0:
            L.die("npx skills failed (network? node installed?)")
    print("done. Review what changed with `git diff -- .claude/skills skills-lock.json` before committing: skills are instructions your employees follow.")


if __name__ == "__main__":
    main()
