"""Scan a folder of (assumed benign) A-Frame pages and summarise what fires.

Used for the A-Frame official examples (https://github.com/aframevr/aframe,
folder examples/). Every page there is benign, so every MEDIUM/HIGH finding
is a false alarm *with respect to malicious intent* -- although the risky
property may genuinely be present. The script also writes all medium/high
findings to a Markdown file for manual review.

Usage:
    python eval/scan_corpus.py PATH_TO/aframe/examples --name aframe_examples --out eval/results
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from xrlint.analyzer import analyze_paths  # noqa: E402
from xrlint.model import Severity  # noqa: E402


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--name", default="corpus")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--source-note", default="", help="e.g. repo URL and commit, recorded in the output")
    args = ap.parse_args(argv)

    res = analyze_paths([args.path])
    html = [p for p in res.pages if p.path.lower().endswith((".html", ".htm"))]
    xr = [p for p in html if p.is_xr]
    alarmed = [p for p in xr if p.alarm(Severity.MEDIUM)]
    by_rule_sev = Counter((f.rule, f.severity.name.lower()) for f in res.findings)
    pages_by_rule = Counter()
    for p in xr:
        for r in {f.rule for f in p.findings if f.severity >= Severity.MEDIUM}:
            pages_by_rule[r] += 1

    summary = {
        "source": args.source_note,
        "html_pages": len(html), "xr_pages": len(xr), "standalone_js": len(res.pages) - len(html),
        "xr_pages_with_medium_or_high": len(alarmed),
        "medium_or_high_findings": sum(1 for f in res.findings if f.severity >= Severity.MEDIUM),
        "files_with_medium_or_high": len({f.file for f in res.findings if f.severity >= Severity.MEDIUM}),
        "note": "Scripts not referenced by any scanned HTML page (e.g. bundled app sources) are scanned "
                "standalone, so their findings count in files_with_medium_or_high but not in xr_pages_*.",
        "findings_by_rule_and_severity": {f"{r}|{s}": n for (r, s), n in sorted(by_rule_sev.items())},
        "xr_pages_alarmed_by_rule": dict(pages_by_rule.most_common()),
        "errors": res.errors,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, f"{args.name}.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    rel = lambda p: os.path.relpath(p, args.path)  # noqa: E731
    lines = [f"# Medium/high findings in {args.name}", "", f"Source: {args.source_note}", "",
             f"{len(alarmed)}/{len(xr)} XR pages have at least one medium/high finding.", "",
             "| File | Line | Severity | Rule | Message | Review note |", "|---|---|---|---|---|---|"]
    for f in sorted(res.findings, key=lambda f: (f.file, f.line)):
        if f.severity >= Severity.MEDIUM:
            msg = f.message.replace("|", "\\|")
            lines.append(f"| {rel(f.file)} | {f.line} | {f.severity.name.lower()} | `{f.rule}` | {msg} | |")
    with open(os.path.join(args.out, f"{args.name}_findings.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

    print(json.dumps({k: v for k, v in summary.items() if k != "errors"}, indent=2))
    print(f"errors: {len(res.errors)}")
    return summary


if __name__ == "__main__":
    main()
