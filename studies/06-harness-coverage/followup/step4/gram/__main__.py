"""Command line:
  python -m gram parse <document> [--lib lib] [--manual manual.jsonl] [--out out]
      writes out/parsed.jsonl (one row per content line, with its facts) and out/outliers.jsonl (unresolved
      clauses, with the reason), prints a summary
  python -m gram test [--lib lib]       runs every part's examples
"""
import argparse
import json
import os
import sys

from .pipeline import LibraryError, parse_text, run_tests, summary


def main():
    ap = argparse.ArgumentParser(prog="gram")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("document")
    p.add_argument("--lib", default="lib")
    p.add_argument("--manual", default="manual.jsonl")
    p.add_argument("--out", default="out")
    t = sub.add_parser("test")
    t.add_argument("--lib", default="lib")
    a = ap.parse_args()
    try:
        if a.cmd == "test":
            fails = run_tests(a.lib)
            print("\n".join(fails) if fails else "all examples pass")
            sys.exit(1 if fails else 0)
        recs = parse_text(open(a.document, encoding="utf-8").read(), a.lib, a.manual)
    except LibraryError as e:
        print("library error:", e)
        sys.exit(2)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "parsed.jsonl"), "w", encoding="utf-8") as f:
        for r in recs:
            facts = [dict(fa, clause=i) for i, c in enumerate(r["clauses"]) for fa in c.get("facts", [])]
            f.write(json.dumps({"line": r["line"], "status": r["status"], "facts": facts}) + "\n")
    with open(os.path.join(a.out, "outliers.jsonl"), "w", encoding="utf-8") as f:
        for r in recs:
            for c in r["clauses"]:
                if c["status"] not in ("parsed", "ignored", "manual"):
                    f.write(json.dumps({"line": r["line"], **c}) + "\n")
    print(json.dumps(summary(recs)))


if __name__ == "__main__":
    main()
