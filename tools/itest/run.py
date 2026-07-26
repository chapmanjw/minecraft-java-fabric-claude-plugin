"""CLI entry for the live MCP integration suite.

  cd tools && python -m itest.run [--only PREFIX] [--destructive] [--baseline FILE]
"""
from __future__ import annotations

import argparse

from .harness import run, report, load_server_skip_log


def main(argv=None):
    ap = argparse.ArgumentParser(description="Live MCP integration suite for minecraft-java.")
    ap.add_argument("--only", default=None, help="run only tools with this name prefix (e.g. block, level)")
    ap.add_argument("--destructive", action="store_true", help="also run destructive cases")
    ap.add_argument("--baseline", default=None, help="write a tab-separated baseline report to this path")
    ap.add_argument(
        "--server-log",
        default=None,
        help=(
            "path to the Minecraft server log. When given, a tool that is not live is explained "
            "using the server's OWN reason rather than inferred from the category tables — the "
            "only way to tell an unmet requiredFabricModules/version constraint apart from a "
            "category opt-out"
        ),
    )
    a = ap.parse_args(argv)
    if a.server_log:
        n = load_server_skip_log(a.server_log)
        print(f"server log: {n} skip reason(s) loaded from {a.server_log}")
        if n == 0:
            print("  (no 'Skipping tool' lines found — falling back to inferred reasons)")
    results, uncovered, live = run(only=a.only, include_destructive=a.destructive)
    ok = report(results, uncovered, live, baseline_path=a.baseline)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
