#!/usr/bin/env python3
"""Keep Markdown free of markdownlint warnings.

  mdfix.py FILE [FILE ...]      fix the files in place, then report what is left
  mdfix.py --all                every Markdown file the company owns (not vendored skills, not product repos)
  mdfix.py --check [...]        report only, change nothing (exit 1 if anything is wrong)
  mdfix.py --hook               Claude Code PostToolUse hook: reads the tool call on stdin, fixes the .md file it wrote
  mdfix.py --verify             run the real markdownlint-cli2 through npx, with .markdownlint-cli2.jsonc (needs Node)

Fixed automatically: table spacing (MD060 compact style, MD055), code fences without a language (MD040, guessed,
`text` when unsure), blank lines around headings, fences, lists and tables (MD022, MD031, MD032, MD058), trailing
spaces and tabs (MD009, MD010), repeated blank lines (MD012), heading spacing, indentation and trailing punctuation
(MD018, MD019, MD023, MD026), list markers and their spacing (MD004, MD030), bare URLs (MD034), placeholders that
look like HTML tags such as <name> (MD033, wrapped in backticks), and the final newline (MD047).

Reported, because only the author can fix them: first line is not a heading (MD041), more than one H1 (MD025),
skipped heading level (MD001), duplicate headings (MD024), emphasis used as a heading (MD036), a table row with
the wrong number of cells (MD056), real inline HTML (MD033), spaces just inside a code span (MD038).
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

FENCE = re.compile(r"^(\s{0,3})(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^(\s{0,3})(#{1,6})(\s*)(.*?)\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d{1,9}[.)])(\s+)(.*)$")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
DELIM_CELL = re.compile(r"^:?-{1,}:?$")
HTML_TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9-]*)((?:\s+[^<>]*)?)(/?)>")
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)")     # a span opened by N backticks closes with N
BARE_URL = re.compile(r"(?<![<(\[`\"'=\w/])(https?://[^\s<>()\[\]`\"']+[^\s<>()\[\]`\"'.,;:!?])")
REAL_HTML = {"a", "abbr", "b", "br", "code", "dd", "del", "details", "div", "dl", "dt", "em", "h1", "h2", "h3", "h4",
             "hr", "i", "img", "ins", "kbd", "li", "ol", "p", "picture", "pre", "s", "small", "source", "span",
             "strong", "sub", "summary", "sup", "table", "tbody", "td", "th", "thead", "tr", "u", "ul", "video"}
SHELL_WORDS = ("python3 ", "python ", "git ", "npx ", "npm ", "pnpm ", "yarn ", "herdr ", "claude ", "gh ", "curl ",
               "cd ", "brew ", "uv ", "pip ", "ls ", "cat ", "mkdir ", "cp ", "mv ", "export ", "test ", "maestro ",
               "adb ", "emulator ", "xcrun ", "docker ", "make ", "./", "$ ", "sudo ")


# ---------------------------------------------------------------- structure

def regions(lines: List[str]) -> List[str]:
    """Per line: 'front' (YAML front matter), 'fence-open', 'fence', 'fence-close', 'comment', or 'text'."""
    kinds = ["text"] * len(lines)
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                for k in range(0, j + 1):
                    kinds[k] = "front"
                i = j + 1
                break
    fence: Optional[Tuple[str, int]] = None
    in_comment = False
    while i < len(lines):
        ln = lines[i]
        if fence:
            m = FENCE.match(ln)
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= fence[1] and not m.group(3).strip():
                kinds[i] = "fence-close"; fence = None
            else:
                kinds[i] = "fence"
        elif in_comment:
            kinds[i] = "comment"
            if "-->" in ln:
                in_comment = False
        else:
            m = FENCE.match(ln)
            if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
                kinds[i] = "fence-open"; fence = (m.group(2)[0], len(m.group(2)))
            elif ln.lstrip().startswith("<!--"):
                kinds[i] = "comment"
                if "-->" not in ln:
                    in_comment = True
        i += 1
    return kinds


def guess_language(body: List[str]) -> str:
    text = "\n".join(body).strip()
    rows = [l.strip() for l in body if l.strip()]
    if not rows:
        return "text"
    if text[0] in "{[":
        try:
            json.loads(text); return "json"
        except ValueError:
            pass
    code_rows = [r for r in rows if not r.startswith("#")]
    if code_rows and sum(r.startswith(SHELL_WORDS) for r in code_rows) >= max(1, len(code_rows) // 2):
        return "bash"
    if rows[0] == "---" or (len(rows) > 1 and all(re.match(r"^[\w.-]+:(\s|$)|^- ", r) for r in rows)):
        return "yaml"
    if any(re.match(r"^(def |class |import |from \w+ import )", r) for r in rows):
        return "python"
    if any(re.match(r"^#{1,6} ", r) for r in rows) and any(re.match(r"^(- |\d+\. |## |\| )", r) for r in rows):
        return "markdown"
    return "text"


def split_cells(row: str) -> List[str]:
    """Cells of a table row. GFM splits on every unescaped pipe, code spans included."""
    s = row.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    cells, cur, i = [], "", 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "\\|"; i += 2; continue
        if s[i] == "|":
            cells.append(cur.strip()); cur = ""
        else:
            cur += s[i]
        i += 1
    cells.append(cur.strip())
    return cells


def is_delim(row: str) -> bool:
    cells = split_cells(row)
    return bool(cells) and all(DELIM_CELL.match(c.replace(" ", "")) for c in cells)


# --------------------------------------------------------------------- fix

def fix_text(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    kinds = regions(lines)

    # pass 1: line-level fixes outside code, comments and front matter
    for i, ln in enumerate(lines):
        k = kinds[i]
        if k == "fence-open":
            m = FENCE.match(ln)
            if m and not m.group(3).strip():
                j = i + 1
                while j < len(lines) and kinds[j] == "fence":
                    j += 1
                lines[i] = f"{m.group(1)}{m.group(2)}{guess_language(lines[i + 1:j])}"
            continue
        if k != "text":
            continue
        ln = ln.rstrip().replace("\t", "    ")
        h = HEADING.match(ln)
        if h and h.group(3) and h.group(4):              # a real ATX heading: "## Title"
            title = re.sub(r"\s+#+$", "", h.group(4))     # closing hashes
            if not title.endswith("..."):
                title = re.sub(r"[.,;:!]+$", "", title)   # MD026
            ln = f"{h.group(2)} {title}"                  # MD019, MD023
        li = LIST_ITEM.match(ln)
        if li and not re.fullmatch(r"\s*([-*_]\s*){3,}", ln):        # not a thematic break
            marker = "-" if li.group(2) in "*+" else li.group(2)   # MD004
            ln = f"{li.group(1)}{marker} {li.group(4)}"            # MD030
        lines[i] = ln

    # pass 2: inline fixes (placeholders that look like HTML, bare URLs), never inside code spans
    for i, ln in enumerate(lines):
        if kinds[i] == "text" and ("<" in ln or "http" in ln):
            lines[i] = fix_inline(ln)

    # pass 3: tables
    i = 0
    while i < len(lines) - 1:
        if kinds[i] == "text" and kinds[i + 1] == "text" and "|" in lines[i] and is_delim(lines[i + 1]) \
                and len(split_cells(lines[i])) == len(split_cells(lines[i + 1])):
            indent = re.match(r"^\s*", lines[i]).group(0)  # type: ignore[union-attr]
            j = i
            while j < len(lines) and kinds[j] == "text" and lines[j].strip() and "|" in lines[j]:
                cells = split_cells(lines[j])
                if j == i + 1:
                    cells = [re.sub(r"-+", "---", c.replace(" ", "")) for c in cells]
                lines[j] = indent + L.table_row(cells)
                kinds[j] = "table"
                j += 1
            i = j
        else:
            i += 1

    # pass 4: blank lines around headings, fences, tables and top-level lists; collapse repeated blanks
    out: List[str] = []
    okind: List[str] = []

    def blank_before():
        if out and out[-1].strip() and okind[-1] != "front":
            out.append(""); okind.append("text")

    for i, ln in enumerate(lines):
        k = kinds[i]
        prev_k = kinds[i - 1] if i else ""
        is_heading = k == "text" and bool(HEADING.match(ln)) and bool(re.match(r"^\s{0,3}#{1,6}\s", ln))
        if is_heading or k == "fence-open" or (k == "table" and prev_k != "table"):
            blank_before()
        elif k == "text" and LIST_ITEM.match(ln) and out and out[-1].strip():
            prev = out[-1]
            prev_is_listish = bool(LIST_ITEM.match(prev)) or prev.startswith((" ", "\t")) or okind[-1] in ("fence-close", "comment")
            if not prev_is_listish and not ln.startswith((" ", "\t")):
                blank_before()
        elif k == "text" and ln.strip() and out and out[-1].strip():
            if okind[-1] in ("fence-close",) or (okind[-1] == "table") or \
                    (okind[-1] == "text" and HEADING.match(out[-1]) and re.match(r"^\s{0,3}#{1,6}\s", out[-1])):
                blank_before()
        if k == "text" and not ln.strip() and out and not out[-1].strip() and okind[-1] == "text":
            continue                                    # MD012
        out.append(ln); okind.append(k)
    while out and not out[-1].strip():
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    return "\n".join(out) + "\n"


def outside_code(ln: str, fn) -> str:
    """Apply fn to the parts of a line that are not inside a code span."""
    out, pos = [], 0
    for m in CODE_SPAN.finditer(ln):
        out.append(fn(ln[pos:m.start()])); out.append(m.group(0)); pos = m.end()
    out.append(fn(ln[pos:]))
    return "".join(out)


def prose_only(ln: str) -> str:
    """The line with its code spans blanked out."""
    return CODE_SPAN.sub(lambda m: " " * len(m.group(0)), ln)


def fix_inline(ln: str) -> str:
    def wrap(m):
        return m.group(0) if m.group(2).lower() in REAL_HTML else f"`{m.group(0)}`"

    def fix(seg: str) -> str:
        seg = HTML_TAG.sub(wrap, seg)
        return BARE_URL.sub(lambda m: f"<{m.group(1)}>", seg)
    return outside_code(ln, fix)


# ------------------------------------------------------------------- check

def check_text(text: str) -> List[Tuple[int, str, str]]:
    lines = text.split("\n")
    kinds = regions(lines)
    probs: List[Tuple[int, str, str]] = []
    if fix_text(text) != text:
        probs.append((0, "FORMAT", "spacing, tables, fence languages or blank lines are off; run mdfix.py on this file"))
    body = [(i, l) for i, l in enumerate(lines) if kinds[i] == "text"]
    first = next(((i, l) for i, l in body if l.strip()), None)
    if first and not re.match(r"^# \S", first[1]):
        probs.append((first[0] + 1, "MD041", "the first line of content must be a top-level heading (# Title)"))
    seen, last_level, h1 = {}, 0, 0
    for i, l in body:
        m = re.match(r"^\s{0,3}(#{1,6})\s+(.*?)\s*$", l)
        if not m:
            continue
        level, title = len(m.group(1)), m.group(2)
        if level == 1:
            h1 += 1
            if h1 > 1:
                probs.append((i + 1, "MD025", "only one top-level heading per file"))
        if last_level and level > last_level + 1:
            probs.append((i + 1, "MD001", f"heading jumps from level {last_level} to {level}"))
        last_level = level
        if title in seen:
            probs.append((i + 1, "MD024", f"duplicate heading {title!r} (first on line {seen[title]})"))
        seen.setdefault(title, i + 1)
    for i, l in body:
        s = l.strip()
        prev_blank = i == 0 or not lines[i - 1].strip()
        next_blank = i + 1 >= len(lines) or not lines[i + 1].strip()
        m = re.fullmatch(r"(\*\*|__|\*|_)(.+?)\1", s)
        if m and prev_blank and next_blank and not re.search(r"[.,;:!?]$", m.group(2)) and "\\" not in s:
            probs.append((i + 1, "MD036", f"emphasis used instead of a heading: {s!r}. Make it a heading, or a sentence ending in a full stop"))
        for c in CODE_SPAN.finditer(l):
            inner = c.group(0)[len(c.group(1)):-len(c.group(1))]
            padded = inner.startswith(" ") and inner.endswith(" ") and ("`" in inner)
            if inner.strip() and inner != inner.strip() and not padded:
                probs.append((i + 1, "MD038", f"spaces inside the code span {c.group(0)!r}; remove them, or reword if the space is the point"))
        for t in HTML_TAG.finditer(prose_only(l)):
            if t.group(2).lower() in REAL_HTML:
                probs.append((i + 1, "MD033", f"inline HTML {t.group(0)}; use Markdown instead"))
    i = 0
    while i < len(lines) - 1:
        if kinds[i] == "text" and "|" in lines[i] and kinds[i + 1] == "text" and is_delim(lines[i + 1]):
            want = len(split_cells(lines[i])); j = i
            while j < len(lines) and kinds[j] == "text" and lines[j].strip() and "|" in lines[j]:
                got = len(split_cells(lines[j]))
                if got != want:
                    probs.append((j + 1, "MD056", f"table row has {got} cells, the header has {want} (escape a literal pipe as \\|)"))
                j += 1
            i = j
        else:
            i += 1
    return probs


# ------------------------------------------------------------------- files

def vendored() -> set:
    lock = L.ROOT / "skills-lock.json"
    try:
        return set(json.loads(lock.read_text()).get("skills", {}))
    except (OSError, ValueError):
        return set()


def ours(path: Path) -> bool:
    """True for Markdown the company owns: inside HQ (or an HQ worktree), not vendored, not a product repo."""
    try:
        rel = path.resolve().relative_to(L.ROOT).parts
    except ValueError:
        return False
    if rel in (("worktrees", "README.md"), ("projects", "README.md")):
        return True
    if rel[:1] == ("worktrees",):
        if len(rel) < 3 or rel[1] != L.HQ:
            return False
        rel = rel[3:]                      # a file inside an HQ worktree: judge it by its path inside HQ
    if not rel or rel[0] in ("projects", "worktrees", "node_modules", ".git"):
        return rel in (("worktrees", "README.md"), ("projects", "README.md"))
    return not (rel[:2] == (".claude", "skills") and len(rel) > 2 and rel[2] in vendored())


def all_files() -> List[Path]:
    files = []
    for p in sorted(L.ROOT.rglob("*.md")):
        parts = p.relative_to(L.ROOT).parts
        if parts[0] in ("worktrees", "projects", "node_modules", ".git") and len(parts) > 2:
            continue                       # product repos, worktrees and their copies are not swept by --all
        if ours(p):
            files.append(p)
    return files


def process(path: Path, write: bool) -> List[Tuple[int, str, str]]:
    text = path.read_text()
    if write:
        fixed = fix_text(text)
        if fixed != text:
            path.write_text(fixed)
        text = fixed
    return check_text(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--all", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--hook", action="store_true"); ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    if a.verify:
        if not shutil.which("npx"):
            L.die("npx not found: install Node.js to run the real markdownlint (mdfix.py --check works without it)")
        code, o, e = L.run(["npx", "--yes", "markdownlint-cli2", "**/*.md"], cwd=str(L.ROOT))
        print((o + "\n" + e).strip()); sys.exit(code)

    if a.hook:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            sys.exit(0)
        fp = (event.get("tool_input") or {}).get("file_path") or ""
        p = Path(fp)
        if not fp.endswith(".md") or not p.is_file() or not ours(p):
            sys.exit(0)
        probs = process(p, write=True)
        if probs:
            print(f"{fp}: Markdown problems that need you (mdfix.py fixed the rest):", file=sys.stderr)
            for line, rule, msg in probs:
                print(f"  line {line}: {rule} {msg}", file=sys.stderr)
            sys.exit(2)            # exit 2 hands the message back to Claude, which then fixes the file
        sys.exit(0)

    paths = all_files() if a.all or not a.files else [Path(f) for f in a.files]
    bad = 0
    for p in paths:
        if not p.is_file():
            print(f"{p}: not a file"); bad += 1; continue
        before = p.read_text()
        probs = process(p, write=not a.check)
        changed = (not a.check) and p.read_text() != before
        if changed:
            print(f"fixed  {L.rel(p)}")
        for line, rule, msg in probs:
            print(f"{L.rel(p)}:{line} {rule} {msg}"); bad += 1
    print(f"\n{len(paths)} file(s) checked, {bad} problem(s) left" + ("" if a.check else " after fixing"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
