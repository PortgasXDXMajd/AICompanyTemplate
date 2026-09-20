"""Shared helpers for the company scripts. Python 3 standard library only."""
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

STATES = ["briefed", "running", "blocked", "handed-back", "in-review",
          "fixing", "awaiting-merge", "interrupted", "failed"]
BOARD_COLS = ["Job", "Employee", "Task", "Repo", "Worktree", "Branch", "Base",
              "Runner", "State", "Updated", "Next step"]
HQ = "_hq"


def run(cmd, cwd=None, check=False):
    """Run a command, return (exit code, stdout, stderr), never raise on failure unless check."""
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        die(f"command failed: {' '.join(map(str, cmd))}\n{p.stderr.strip() or p.stdout.strip()}")
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def die(msg, code=1) -> NoReturn:
    """Print the error and exit. Typed NoReturn so checkers know the code after a guard is safe."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def out(data, as_json):
    """Print a dict as JSON, or as 'key: value' lines."""
    if as_json:
        print(json.dumps(data, indent=2))
    else:
        for k, v in data.items():
            print(f"{k}: {v}")


def hq_root():
    """The HQ main checkout, even when this file is a copy inside an HQ worktree."""
    here = Path(__file__).resolve().parent.parent
    code, common, _ = run(["git", "-C", str(here), "rev-parse", "--path-format=absolute", "--git-common-dir"])
    if code == 0 and common:
        root = Path(common).parent
        if (root / "CLAUDE.md").exists():
            return root
    return here


ROOT = hq_root()


def now():
    return _dt.datetime.now()


def today():
    return now().strftime("%Y-%m-%d")


def stamp():
    return now().strftime("%Y-%m-%d %H:%M")


def clean_cell(text):
    return re.sub(r"\s+", " ", str(text or "")).replace("|", "/").strip()


def table_row(cells):
    """One Markdown table row in markdownlint's 'compact' style: one space around every cell, `| |` for an empty one."""
    return "|" + "|".join(f" {c} " if c else " " for c in cells) + "|"


def write_md(path, text):
    """Write a Markdown file the way markdownlint wants it (mdfix.py does the formatting)."""
    import mdfix                      # imported here: mdfix itself imports this module
    Path(path).write_text(mdfix.fix_text(text))


def append_item(path, item, header=None):
    """Append one '- ...' list item to a Markdown file, keeping a blank line between prose or a heading and the list."""
    p = Path(path)
    text = p.read_text() if p.exists() else (header or "")
    body = text.rstrip("\n")
    last = body.splitlines()[-1] if body else ""
    sep = "\n" if last.startswith("- ") else "\n\n"
    p.write_text((body + sep if body else "") + item.rstrip("\n") + "\n")


def valid_slug(slug):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", slug or ""):
        die(f"slug must be lower-case letters, digits and '-', got: {slug!r}")
    return slug


def valid_name(name, what="name"):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,40}", name or ""):
        die(f"{what} must be kebab-case (a-z, 0-9, '-'), got: {name!r}")
    return name


# ---------------------------------------------------------------- journal

def journal_path(day=None):
    return ROOT / "context" / "journal" / f"{day or today()}.md"


def journal_add(text, job=None):
    p = journal_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    line = f"- {now().strftime('%H:%M')} {clean_cell(text)}"
    if job:
        line += f" ({job})"
    append_item(p, line, header=f"# Journal {today()}\n")
    return line


# ---------------------------------------------------------------- board

def board_path():
    return ROOT / "jobs" / "BOARD.md"


def board_read():
    """Return (head_lines, rows, tail_lines). rows are dicts keyed by BOARD_COLS."""
    p = board_path()
    if not p.exists():
        die(f"{p} not found")
    lines = p.read_text().splitlines()
    head, rows, tail = [], [], []
    seen_sep = False
    in_tail = False
    for ln in lines:
        s = ln.strip()
        if in_tail:
            tail.append(ln)
        elif not seen_sep:
            head.append(ln)
            if s.startswith("|") and set(s.replace("|", "").strip()) <= set("-: "):
                seen_sep = True
        elif s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            cells += [""] * (len(BOARD_COLS) - len(cells))
            rows.append(dict(zip(BOARD_COLS, cells)))
        else:
            in_tail = True
            tail.append(ln)
    if not seen_sep:
        die("jobs/BOARD.md has no table header")
    return head, rows, tail


def board_write(head, rows, tail):
    body = [table_row([clean_cell(r.get(c, "")) for c in BOARD_COLS]) for r in rows]
    write_md(board_path(), "\n".join(head + body + tail))


def board_find(rows, job):
    for r in rows:
        if r["Job"] == job:
            return r
    return None


def job_dir(job):
    return ROOT / "jobs" / job


# ---------------------------------------------------------------- repos

def repo_main(repo):
    """Main checkout path for '_hq' or a project name."""
    if repo == HQ:
        return ROOT
    p = ROOT / "projects" / repo
    if not (p / ".git").exists():
        die(f"no product repo at projects/{repo}")
    return p


def default_branch(repo):
    code, b, _ = run(["git", "-C", str(repo_main(repo)), "symbolic-ref", "--short", "HEAD"])
    if code != 0 or not b:
        die(f"cannot read the current branch of the {repo} main checkout")
    return b


def worktree_path(repo, employee, slug):
    return ROOT / "worktrees" / repo / f"{employee}--{slug}"


def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def verdict_of(path):
    """Last 'Verdict:' line of a helper output file, or None."""
    try:
        for ln in reversed(Path(path).read_text().splitlines()):
            m = re.match(r"\s*\**Verdict:?\**:?\s*(.+)", ln, re.I)
            if m:
                return m.group(1).strip()
    except OSError:
        pass
    return None
