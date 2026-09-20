#!/usr/bin/env python3
"""The Chief of Staff's journal: context/journal/YYYY-MM-DD.md.

  journal.py add "text" [--job JOB]     append a timestamped line to today's file
  journal.py tail [-n 40]               show the end of the newest journal file
  journal.py unclosed                   list journal files since the last day summary
  journal.py close "summary text"       append the '## Day summary' block to today's file
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

SUMMARY = "## Day summary"


def files():
    d = L.ROOT / "context" / "journal"
    return sorted(p for p in d.glob("20*.md"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("text"); a.add_argument("--job")
    t = sub.add_parser("tail"); t.add_argument("-n", type=int, default=40)
    sub.add_parser("unclosed")
    c = sub.add_parser("close"); c.add_argument("text")
    args = ap.parse_args()

    if args.cmd == "add":
        print(L.journal_add(args.text, args.job))
    elif args.cmd == "tail":
        fs = files()
        if not fs:
            print("no journal yet"); return
        print(f"# {L.rel(fs[-1])}")
        print("\n".join(fs[-1].read_text().splitlines()[-args.n:]))
    elif args.cmd == "unclosed":
        fs = files()
        last_closed = max((i for i, p in enumerate(fs) if SUMMARY in p.read_text()), default=-1)
        todo = fs[last_closed + 1:]
        if not todo:
            print("every journal file ends in a day summary")
        for p in todo:
            print(L.rel(p))
    elif args.cmd == "close":
        p = L.journal_path()
        L.journal_add("end of day")
        with p.open("a") as f:
            f.write(f"\n{SUMMARY}\n\n{args.text.strip()}\n")
        print(f"closed {L.rel(p)}")


if __name__ == "__main__":
    main()
