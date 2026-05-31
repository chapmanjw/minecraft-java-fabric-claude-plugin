"""CLI entry for the live MCP integration suite.

  cd tools && python -m itest.run [--only PREFIX] [--destructive] [--baseline FILE]
"""
from __future__ import annotations

import argparse

from .harness import run, report


def main(argv=None):
    ap = argparse.ArgumentParser(description="Live MCP integration suite for minecraft-java.")
    ap.add_argument("--only", default=None, help="run only tools with this name prefix (e.g. block, level)")
    ap.add_argument("--destructive", action="store_true", help="also run destructive cases")
    ap.add_argument("--baseline", default=None, help="write a tab-separated baseline report to this path")
    a = ap.parse_args(argv)
    results, uncovered, live = run(only=a.only, include_destructive=a.destructive)
    ok = report(results, uncovered, live, baseline_path=a.baseline)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
