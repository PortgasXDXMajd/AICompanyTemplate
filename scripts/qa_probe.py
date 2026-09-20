#!/usr/bin/env python3
"""What hands-on QA can run on this machine, and a bounded wait for a dev server.

  qa_probe.py                          probe web and mobile QA tooling
  qa_probe.py wait-url URL [--timeout 300]
                                       poll until the URL answers, give up after the timeout

Claude in Chrome cannot be probed from a script: look for mcp__claude-in-chrome__* in your own tool list.
"""
import argparse
import json
import platform
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L


def ver(cmd):
    if not shutil.which(cmd[0]):
        return None
    _, o, e = L.run(cmd)
    return (o or e).splitlines()[0][:80] if (o or e) else "present"


def probe(as_json):
    mcp = ver(["claude", "mcp", "list"]) and L.run(["claude", "mcp", "list"])[1] or ""
    r = {
        "os": platform.system(),
        "playwright_mcp": "playwright" in mcp.lower(),
        "maestro_mcp": "maestro" in mcp.lower(),
        "maestro": ver(["maestro", "--version"]),
        "java": ver(["java", "-version"]),
        "adb": ver(["adb", "version"]),
        "android_avds": (L.run(["emulator", "-list-avds"])[1].split() if shutil.which("emulator") else None),
        "android_devices": ([l.split()[0] for l in L.run(["adb", "devices"])[1].splitlines()[1:] if l.strip()] if shutil.which("adb") else None),
        "android_accel_ok": None,
        "ios_simulators": None,
    }
    if shutil.which("emulator"):
        code, _, _ = L.run(["emulator", "-accel-check"])
        r["android_accel_ok"] = code == 0
    if platform.system() == "Darwin" and shutil.which("xcrun"):
        code, o, _ = L.run(["xcrun", "simctl", "list", "devices", "available"])
        r["ios_simulators"] = sum(1 for l in o.splitlines() if "(" in l and "==" not in l and "--" not in l)
    web = "playwright MCP" if r["playwright_mcp"] else "only Claude in Chrome, if this session has its tools (claude --chrome)"
    if r["maestro"] and ((r["android_avds"] and r["android_accel_ok"]) or r["android_devices"] or r["ios_simulators"]):
        mobile = "possible (Maestro + a device/emulator/simulator)"
    elif r["android_devices"] or (r["android_avds"] and r["android_accel_ok"]):
        mobile = "Android only, raw adb (no Maestro)"
    elif r["android_avds"] and r["android_accel_ok"] is False:
        mobile = "NOT possible: no hardware acceleration. Never boot an unaccelerated emulator; offer a USB device or the CEO's Mac"
    else:
        mobile = "NOT possible here: no emulator, simulator or device. Verdict: not performed; write the Maestro flows anyway"
    r["web_qa"] = web; r["mobile_qa"] = mobile
    if as_json:
        print(json.dumps(r, indent=2))
    else:
        for k, v in r.items():
            print(f"{k}: {v}")
        print("\nAdd tools:  claude mcp add playwright -- npx -y @playwright/mcp@latest   |   claude mcp add maestro -- maestro mcp"
              "\n(an MCP server added now is available after the session restarts)")


def wait_url(url, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                print(f"up after {int(time.time() - t0)}s: HTTP {resp.status}"); return 0
        except urllib.error.HTTPError as e:
            print(f"up after {int(time.time() - t0)}s: HTTP {e.code}"); return 0
        except Exception:
            time.sleep(2)
    print(f"gave up after {timeout}s: {url} never answered"); return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    w = sub.add_parser("wait-url"); w.add_argument("url"); w.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()
    if a.cmd == "wait-url":
        sys.exit(wait_url(a.url, a.timeout))
    probe(a.json)


if __name__ == "__main__":
    main()
