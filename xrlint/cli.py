"""Command-line entry point: `xrlint PATH [PATH ...]`."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .analyzer import analyze_paths
from .model import RULES, Severity
from .report import rules_table_markdown, to_json, to_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="xrlint",
        description="Static checker for risky UI properties in A-Frame/WebXR pages "
                    "(based on the 14 properties in 'Shadowed Realities', USENIX Security 2025).")
    p.add_argument("paths", nargs="*", help="HTML/JS files or folders to scan")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--min-severity", default="low", choices=[s.name.lower() for s in Severity],
                   help="hide findings below this severity (default: low)")
    p.add_argument("--rules", help="comma-separated rule ids to keep (default: all)")
    p.add_argument("--no-explain", action="store_true", help="omit the 'why risky' lines in text output")
    p.add_argument("--no-js", action="store_true", help="do not scan standalone .js files")
    p.add_argument("--fail-on", default="none", choices=["none"] + [s.name.lower() for s in Severity],
                   help="exit with status 1 if any finding is at or above this severity")
    p.add_argument("--list-rules", action="store_true", help="print the rule table and exit")
    p.add_argument("--version", action="version", version=f"xrlint {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_rules:
        print(rules_table_markdown())
        return 0
    if not args.paths:
        build_parser().print_usage(sys.stderr)
        return 2
    for p in args.paths:
        if not os.path.exists(p):
            print(f"xrlint: no such file or folder: {p}", file=sys.stderr)
            return 2
    rules = None
    if args.rules:
        rules = {r.strip() for r in args.rules.split(",") if r.strip()}
        unknown = rules - set(RULES)
        if unknown:
            print(f"xrlint: unknown rule(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
    result = analyze_paths(args.paths, include_js=not args.no_js)
    min_sev = Severity.parse(args.min_severity)
    base = os.getcwd()
    if args.format == "json":
        print(to_json(result, min_sev, base, rules))
    else:
        print(to_text(result, min_sev, base, explain=not args.no_explain, rules=rules))
    if args.fail_on != "none":
        thr = Severity.parse(args.fail_on)
        if any(f.severity >= thr and (rules is None or f.rule in rules) for f in result.findings):
            return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
