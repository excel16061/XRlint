"""Text, JSON and Markdown reports."""

from __future__ import annotations

import json
import os
import textwrap
from collections import Counter

from .analyzer import ScanResult
from .model import RULES, Severity

_TAG = {Severity.HIGH: "HIGH", Severity.MEDIUM: "MED ", Severity.LOW: "LOW ", Severity.INFO: "INFO"}


def _rel(path: str, base: str | None) -> str:
    if base:
        try:
            return os.path.relpath(path, base)
        except ValueError:
            return path
    return path


def filtered(result: ScanResult, min_sev: Severity, rules: set | None = None):
    return [f for f in result.findings if f.severity >= min_sev and (rules is None or f.rule in rules)]


def to_text(result: ScanResult, min_sev: Severity = Severity.LOW, base: str | None = None,
            explain: bool = True, rules: set | None = None) -> str:
    fs = filtered(result, min_sev, rules)
    lines = []
    by_file: dict = {}
    for f in fs:
        by_file.setdefault(f.file, []).append(f)
    for file in sorted(by_file):
        lines.append(f"{_rel(file, base)}")
        for f in sorted(by_file[file], key=lambda x: (x.line, -x.severity)):
            lines.append(f"  {f.line:>5}  {_TAG[f.severity]}  {f.rule}")
            for w in textwrap.wrap(f.message, 88):
                lines.append(f"               {w}")
            if explain:
                for w in textwrap.wrap("why risky: " + f.meta.why, 88):
                    lines.append(f"               {w}")
                for w in textwrap.wrap("legitimate use: " + f.meta.legit, 88):
                    lines.append(f"               {w}")
            if f.page:
                lines.append(f"               (loaded by {_rel(f.page, base)})")
        lines.append("")
    counts = Counter(f.severity for f in fs)
    pages = [p for p in result.pages if p.path.lower().endswith((".html", ".htm"))]
    alarmed = sum(1 for p in pages if p.alarm())
    lines.append(
        f"Scanned {len(pages)} HTML page(s) and {len(result.pages) - len(pages)} standalone script(s). "
        f"Findings shown (>= {min_sev.name.lower()}): "
        + ", ".join(f"{counts.get(s, 0)} {s.name.lower()}" for s in sorted(Severity, reverse=True) if s >= min_sev)
        + f". Pages with a medium/high finding: {alarmed}/{len(pages)}.")
    if result.errors:
        lines.append(f"{len(result.errors)} file(s) could not be analysed:")
        for p, e in result.errors:
            lines.append(f"  {_rel(p, base)}: {e}")
    lines.append("A finding means a risky UI property is used, not that the page is malicious.")
    return "\n".join(lines)


def to_json(result: ScanResult, min_sev: Severity = Severity.INFO, base: str | None = None,
            rules: set | None = None) -> str:
    out = {
        "findings": [dict(f.to_dict(), file=_rel(f.file, base), page=_rel(f.page, base) if f.page else "")
                     for f in filtered(result, min_sev, rules)],
        "pages": [{"path": _rel(p.path, base), "is_xr": p.is_xr, "alarm": p.alarm(),
                   "n_findings": len(p.findings)} for p in result.pages],
        "errors": [{"path": _rel(p, base), "error": e} for p, e in result.errors],
    }
    return json.dumps(out, indent=2)


def rules_table_markdown() -> str:
    rows = ["| Rule | Paper property | What it flags | Legitimate use |", "|---|---|---|---|"]
    for r in RULES.values():
        rows.append(f"| `{r.id}` | {r.prop} | {r.title} | {r.legit} |")
    return "\n".join(rows)
