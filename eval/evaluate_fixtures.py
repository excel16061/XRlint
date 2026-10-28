"""Evaluate XRLint on the hand-written fixtures in tests/fixtures.

Three measurements (see README "Evaluation"):
  1. Rule-level precision/recall on the unit + control pages, against labels.json.
  2. Page-level detection of the 14 re-implemented attacks (a page is "flagged"
     if any MEDIUM or HIGH finding fires) and false alarms on the benign pages.
  3. Property coverage: for each attack, which of the paper's listed UI
     properties (Table 8 descriptions) produced at least one finding.

Usage:  python eval/evaluate_fixtures.py [--out eval/results]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from xrlint.analyzer import analyze_html  # noqa: E402
from xrlint.model import RULES, Severity  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
SCORED_RULES = sorted(r for r in RULES if r not in ("P1-third-party-script", "P9-mode-listener"))


def fired(path: str, min_sev=Severity.LOW) -> set:
    res = analyze_html(path)
    return {f.rule for f in res.findings if f.severity >= min_sev}, res


def pr(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else float("nan")
    r = tp / (tp + fn) if tp + fn else float("nan")
    return p, r


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args(argv)
    with open(os.path.join(FIX, "labels.json")) as fh:
        labels = json.load(fh)

    # ---------------------------------------------------------- 1. rule level
    counts = defaultdict(lambda: [0, 0, 0])  # rule -> tp, fp, fn
    per_file = {}
    for group in ("unit", "controls"):
        for name, expected in labels[group].items():
            got, _ = fired(os.path.join(FIX, group, name))
            got = {g for g in got if g in SCORED_RULES}
            exp = set(expected)
            for r in SCORED_RULES:
                if r in got and r in exp:
                    counts[r][0] += 1
                elif r in got:
                    counts[r][1] += 1
                elif r in exp:
                    counts[r][2] += 1
            per_file[f"{group}/{name}"] = {"expected": sorted(exp), "fired": sorted(got),
                                          "missed": sorted(exp - got), "unexpected": sorted(got - exp)}
    rule_rows = []
    tot = [0, 0, 0]
    for r in SCORED_RULES:
        tp, fp, fn = counts[r]
        tot = [tot[0] + tp, tot[1] + fp, tot[2] + fn]
        p, rc = pr(tp, fp, fn)
        rule_rows.append({"rule": r, "tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": rc})
    micro_p, micro_r = pr(*tot)

    # ---------------------------------------------------------- 2. page level
    attack_rows = []
    prop_hits = prop_total = 0
    for name, info in labels["attacks"].items():
        got_all, res = fired(os.path.join(FIX, "attacks", name), Severity.INFO)
        flagged = res.alarm(Severity.MEDIUM)
        scored_props = [p for p in info["paper_properties"] if labels["property_to_rules"][p]]
        covered = [p for p in scored_props if set(labels["property_to_rules"][p]) & got_all]
        mapped = {r for p in info["paper_properties"] for r in labels["property_to_rules"][p]}
        extra = sorted(r for r in got_all if r not in mapped and r != "P1-third-party-script")
        prop_hits += len(covered)
        prop_total += len(scored_props)
        attack_rows.append({
            "page": name, "attack": info["attack"], "flagged": flagged,
            "max_severity": res.max_severity().name.lower() if res.max_severity() is not None else None,
            "paper_properties": info["paper_properties"],
            "scored_properties": scored_props, "covered": covered,
            "missed": [p for p in scored_props if p not in covered], "extra_rules": extra,
        })

    benign = [("unit", n) for n, e in labels["unit"].items() if n.endswith("_safe.html")] + \
             [("controls", n) for n in labels["controls"]]
    benign_rows = []
    for group, n in benign:
        _, res = fired(os.path.join(FIX, group, n))
        benign_rows.append({"page": f"{group}/{n}", "alarm": res.alarm(Severity.MEDIUM),
                            "alarm_rules": sorted({f.rule for f in res.findings if f.severity >= Severity.MEDIUM})})

    detected = sum(a["flagged"] for a in attack_rows)
    false_alarms = sum(b["alarm"] for b in benign_rows)
    summary = {
        "rule_level": {"rows": rule_rows, "micro_precision": micro_p, "micro_recall": micro_r,
                       "tp": tot[0], "fp": tot[1], "fn": tot[2]},
        "attack_pages": {"rows": attack_rows, "detected": detected, "total": len(attack_rows)},
        "benign_pages": {"rows": benign_rows, "false_alarms": false_alarms, "total": len(benign_rows)},
        "property_coverage": {"covered": prop_hits, "total": prop_total},
        "per_file": per_file,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "fixtures.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=str)
    with open(os.path.join(args.out, "fixtures.md"), "w") as fh:
        fh.write(render_md(summary))
    print(render_md(summary))
    return summary


def _fmt(x):
    return "n/a" if x != x else f"{x:.2f}"  # NaN check


def render_md(s: dict) -> str:
    out = ["# Fixture evaluation", "",
           "All pages here were written by the author of XRLint (see README for why this inflates scores).", "",
           "## 1. Rule-level precision / recall (unit + control pages, findings >= low)", "",
           "| Rule | TP | FP | FN | Precision | Recall |", "|---|---|---|---|---|---|"]
    for r in s["rule_level"]["rows"]:
        out.append(f"| `{r['rule']}` | {r['tp']} | {r['fp']} | {r['fn']} | {_fmt(r['precision'])} | {_fmt(r['recall'])} |")
    rl = s["rule_level"]
    out += ["", f"Micro-averaged: precision {_fmt(rl['micro_precision'])}, recall {_fmt(rl['micro_recall'])} "
                f"(TP {rl['tp']}, FP {rl['fp']}, FN {rl['fn']}).", "",
            "## 2. Page-level detection (flag = any medium/high finding)", "",
            f"Attack pages flagged: **{s['attack_pages']['detected']}/{s['attack_pages']['total']}**. "
            f"Benign pages with a false alarm: **{s['benign_pages']['false_alarms']}/{s['benign_pages']['total']}**.", "",
            "| Attack page | Flagged | Max severity | Paper properties | Covered | Missed | Other rules fired |",
            "|---|---|---|---|---|---|---|"]
    for a in s["attack_pages"]["rows"]:
        out.append(f"| {a['attack']} | {'yes' if a['flagged'] else '**no**'} | {a['max_severity']} | "
                   f"{', '.join(a['paper_properties'])} | {', '.join(a['covered']) or '-'} | "
                   f"{', '.join(a['missed']) or '-'} | {', '.join(a['extra_rules']) or '-'} |")
    out += ["", "| Benign page | False alarm | Rules at medium/high |", "|---|---|---|"]
    for b in s["benign_pages"]["rows"]:
        out.append(f"| {b['page']} | {'**yes**' if b['alarm'] else 'no'} | {', '.join(b['alarm_rules']) or '-'} |")
    pc = s["property_coverage"]
    out += ["", "## 3. Property coverage on attack pages", "",
            f"{pc['covered']}/{pc['total']} (attack, property) pairs produced a finding of the matching rule. "
            "P1 (no iframe isolation) is a platform property and is not scored.", ""]
    misses = {k: v for k, v in s["per_file"].items() if v["missed"] or v["unexpected"]}
    if misses:
        out += ["## Disagreements with labels (unit + control pages)", ""]
        for k, v in misses.items():
            out.append(f"- `{k}`: missed {v['missed'] or '-'}, unexpected {v['unexpected'] or '-'}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
