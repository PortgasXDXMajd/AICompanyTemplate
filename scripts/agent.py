#!/usr/bin/env python3
"""Run an employee or a helper as its own Claude Code session in its own Herdr tab.

  agent.py where                                   'herdr' or 'plain'
  agent.py start --job JOB --employee NAME [--brief FILE] [--chrome] [--ask-edits]
  agent.py start --job JOB --helper rev|qual|arch|qa [--brief FILE] [--chrome] [--ask-edits]
  agent.py prompt AGENT --brief FILE               a fix round or a resume, to the same live agent
  agent.py wait AGENT [--expect FILE] [--timeout-ms 540000]
  agent.py read AGENT [--lines 60]
  agent.py list
  agent.py close --tab TAB_ID

Only works inside Herdr (HERDR_ENV=1). In a plain terminal, delegate with the Agent tool instead.
Exit codes: 0 ok, 3 not inside Herdr, 4 the agent needs the CEO (blocked / not ready), 5 stalled.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

HELPERS = {"rev": "review", "qual": "quality", "arch": "architecture", "qa": "qa"}


def in_herdr():
    return os.environ.get("HERDR_ENV") == "1"


def need_herdr():
    if not in_herdr():
        print("plain: not inside Herdr (HERDR_ENV is not 1). Delegate with the Agent tool instead.", file=sys.stderr)
        sys.exit(3)


def herdr(*args):
    """Run herdr; return (ok, parsed-json-or-text, error-code)."""
    code, o, e = L.run(["herdr", *args])
    blob = o if code == 0 else (e or o)
    try:
        data = json.loads(blob)
    except (ValueError, TypeError):
        data = blob
    err = None
    if code != 0:
        if isinstance(data, dict):
            err = (data.get("error") or {}).get("code") or data.get("code")
        if not err:
            m = re.search(r"\b(agent_not_ready|agent_blocked|agent_prompt_stalled|timeout|agent_not_running|agent_not_idle)\b", str(blob))
            err = m.group(1) if m else "error"
    return code == 0, data, err


def dig(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def live_names():
    _, data, _ = herdr("agent", "list")
    agents = dig(data, "result", "agents") or dig(data, "result") or []
    return {a.get("name") for a in agents if isinstance(a, dict) and a.get("name")}


def unique(name):
    name = re.sub(r"[^a-z0-9_-]", "-", name.lower())[:28]
    taken, cand, i = live_names(), name, 2
    while cand in taken:
        cand = f"{name}-{i}"; i += 1
    return cand


def tag_of(job):
    slug = job.split("--", 1)[-1]
    m = re.match(r"(\d+)", slug)
    return m.group(1) if m else slug[:12]


def cmd_start(a):
    need_herdr()
    d = L.job_dir(a.job)
    if not d.exists():
        L.die(f"no job folder for {a.job}. Create it first: job.py new ...")
    if a.helper:
        kind = HELPERS[a.helper]
        brief = Path(a.brief) if a.brief else d / f"{kind}-brief.md"
        name = unique(f"{a.helper}-{tag_of(a.job)}")
        label = f"{kind} {tag_of(a.job)}"
        extra = []
    else:
        role = L.ROOT / ".claude" / "agents" / f"{a.employee}.md"
        if not role.exists():
            L.die(f"no employee {a.employee} in .claude/agents/")
        brief = Path(a.brief) if a.brief else d / "brief.md"
        name = unique(a.employee)
        label = f"{a.employee} {a.job.split('--', 1)[-1]}"
        extra = ["--agent", a.employee]
    if not brief.exists():
        L.die(f"brief not found: {brief}")
    if a.chrome:
        extra.append("--chrome")
    if not a.ask_edits:
        extra += ["--permission-mode", "acceptEdits"]

    tab_args = ["tab", "create", "--cwd", str(L.ROOT), "--label", label, "--no-focus"]
    if os.environ.get("HERDR_WORKSPACE_ID"):
        tab_args += ["--workspace", os.environ["HERDR_WORKSPACE_ID"]]
    ok, data, err = herdr(*tab_args)
    if not ok:
        L.die(f"herdr tab create failed ({err}): {data}")
    tab = dig(data, "result", "tab", "tab_id"); pane = dig(data, "result", "root_pane", "pane_id")
    if not tab or not pane:
        L.die(f"could not read tab/pane ids from herdr's answer: {data}")

    ok, data, err = herdr("agent", "start", name, "--kind", "claude", "--pane", pane, "--", *extra)
    res: Dict[str, Any] = {"agent": name, "tab": tab, "pane": pane, "brief": L.rel(brief), "job": a.job}
    if not ok:
        res["status"] = err
        L.journal_add(f"agent {name} in tab {tab} did not become ready ({err}); the CEO must look at that tab", a.job)
        L.out(res, a.json)
        sys.exit(4 if err == "agent_not_ready" else 1)

    who = "You are a helper subagent, not the Chief of Staff (CLAUDE.md, Who you are, 2). " if a.helper else ""
    text = (f"{who}Delegation from the Chief of Staff. Your brief is in {L.rel(brief)}. Read it and carry it out. "
            f"When you are finished, write your result to the file the brief names and stop.")
    ok, data, err = herdr("agent", "prompt", name, text, "--wait", "--timeout", "20000")
    res["status"] = "working" if (not ok and err == "timeout") else str(dig(data, "result", "agent", "agent_status") or err)

    head, rows, tail = L.board_read()
    r = L.board_find(rows, a.job)
    if r:
        if a.helper:
            r["State"] = "in-review"
            r["Next step"] = L.clean_cell((r["Next step"] + "; " if "running" in r["Next step"] else "") + f"{name} running (tab {tab})")
        else:
            r["Runner"] = f"herdr:{name} (tab {tab})"; r["State"] = "running"
            r["Next step"] = "wait for the hand-back, then review"
        r["Updated"] = L.stamp()
        L.board_write(head, rows, tail)
    L.journal_add(f"started {name} in Herdr tab {tab} with {L.rel(brief)}: {res['status']}", a.job)
    L.out(res, a.json)
    if err == "agent_prompt_stalled":
        print("the prompt may not have started a turn. Look with `agent.py read` before doing anything; never re-prompt blind.", file=sys.stderr)
        sys.exit(5)
    if res["status"] == "blocked":
        sys.exit(4)


def cmd_prompt(a):
    need_herdr()
    brief = Path(a.brief)
    if not brief.exists():
        L.die(f"brief not found: {brief}")
    text = (f"Follow-up from the Chief of Staff. Your new brief is in {L.rel(brief)}. Read it and carry it out. "
            f"Write your result to the new file that brief names, not the earlier one, and stop.")
    ok, data, err = herdr("agent", "prompt", a.agent, text, "--wait", "--timeout", "20000")
    status = "working" if (not ok and err == "timeout") else str(dig(data, "result", "agent", "agent_status") or err)
    L.journal_add(f"prompted {a.agent} with {L.rel(brief)}: {status}")
    L.out({"agent": a.agent, "status": status}, a.json)
    if err in ("agent_blocked",) or status == "blocked":
        sys.exit(4)
    if err == "agent_prompt_stalled":
        sys.exit(5)


def cmd_wait(a):
    need_herdr()
    ok, data, err = herdr("agent", "wait", a.agent, "--timeout", str(a.timeout_ms))
    status = "working" if (not ok and err == "timeout") else str(dig(data, "result", "agent", "agent_status") or err)
    res: Dict[str, Any] = {"agent": a.agent, "status": status}
    if a.expect:
        p = Path(a.expect)
        res["result_file_exists"] = p.exists()
        if p.exists():
            res["verdict"] = L.verdict_of(p)
    advice = {
        "working": "still working: wait again, or do something else meanwhile",
        "blocked": "it is showing an approval or a question. Never answer it. Read what it asks, set the job to blocked, tell the CEO which tab, and do not wait again until they say it is answered",
        "idle": "stopped", "done": "stopped",
    }.get(status, "unexpected: look with `agent.py read`")
    if status in ("idle", "done") and a.expect:
        advice = "finished: collect the result" if res["result_file_exists"] else "stopped WITHOUT its result file: read the pane before doing anything, then prompt once for the file"
    res["advice"] = advice
    L.out(res, a.json)
    if status == "blocked":
        sys.exit(4)


def cmd_read(a):
    need_herdr()
    code, o, e = L.run(["herdr", "agent", "read", a.agent, "--source", "recent-unwrapped", "--lines", str(a.lines)])
    print(o if code == 0 else e)
    sys.exit(0 if code == 0 else 1)


def cmd_list(a):
    need_herdr()
    _, data, _ = herdr("agent", "list")
    agents = dig(data, "result", "agents") or dig(data, "result") or []
    rows = [{"name": x.get("name"), "status": x.get("agent_status"), "tab": x.get("tab_id"), "pane": x.get("pane_id")}
            for x in agents if isinstance(x, dict)]
    if a.json:
        L.out({"agents": rows}, True)
    else:
        for r in rows:
            print(f"{r['name'] or '(unnamed)'}  [{r['status']}]  tab {r['tab']}")
        if not rows:
            print("no live agents")


def cmd_close(a):
    need_herdr()
    ok, data, err = herdr("tab", "close", a.tab)
    if not ok:
        L.die(f"herdr tab close failed ({err}): {data}")
    L.journal_add(f"closed Herdr tab {a.tab}")
    print(f"closed {a.tab}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where")
    s = sub.add_parser("start"); s.add_argument("--job", required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--employee"); g.add_argument("--helper", choices=sorted(HELPERS))
    s.add_argument("--brief"); s.add_argument("--chrome", action="store_true"); s.add_argument("--ask-edits", action="store_true")
    p = sub.add_parser("prompt"); p.add_argument("agent"); p.add_argument("--brief", required=True)
    w = sub.add_parser("wait"); w.add_argument("agent"); w.add_argument("--expect"); w.add_argument("--timeout-ms", type=int, default=540000)
    r = sub.add_parser("read"); r.add_argument("agent"); r.add_argument("--lines", type=int, default=60)
    sub.add_parser("list")
    c = sub.add_parser("close"); c.add_argument("--tab", required=True)
    a = ap.parse_args()
    if a.cmd == "where":
        print("herdr" if in_herdr() else "plain"); return
    {"start": cmd_start, "prompt": cmd_prompt, "wait": cmd_wait, "read": cmd_read,
     "list": cmd_list, "close": cmd_close}[a.cmd](a)


if __name__ == "__main__":
    main()
