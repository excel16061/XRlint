"""Run XRLint on the public Shadowed Realities artifact (to be run on YOUR machine).

The artifact (apps, logging framework, metrics library) is on figshare:
    https://doi.org/10.6084/m9.figshare.28271207
It could not be downloaded from the environment where XRLint was written, so this
script has NOT been run on it yet and its folder layout is unknown to us.

Steps:
  1. Download the archive from the DOI above and unzip it into  data/shadowed_realities/
  2. python eval/evaluate_artifact.py data/shadowed_realities
     -> writes eval/results/artifact/pages.csv and summary.md
  3. Check the inferred labels in pages.csv. If any are wrong or "unknown", fix the
     'label' column (use an attack name from ATTACKS below, or 'control'), save it as
     labels.csv and re-run with:  --labels eval/results/artifact/labels.csv

A page is "flagged" if any MEDIUM or HIGH finding fires (same rule as the fixtures).
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from xrlint.analyzer import analyze_paths  # noqa: E402
from xrlint.model import Severity  # noqa: E402

# Keyword patterns used to GUESS the attack from a file path. Order matters.
ATTACKS = [
    ("GCJ", r"gcj|gaze.?cursor.?jack"),
    ("CCJ", r"ccj|controller.?cursor.?jack"),
    ("Visual Overlapping", r"visual.?overlap"),
    ("Sequential Rendering", r"sequential"),
    ("Clickjacking", r"clickjack"),
    ("BST", r"\bbst\b|blind.?spot"),
    ("AAD", r"\baad\b|auxiliary"),
    ("Input Forgery", r"forgery|synthetic"),
    ("Malvertising", r"malvert"),
    ("DoS through overriding", r"overrid"),
    ("DoS (invisibility)", r"dos|denial|invisib"),
    ("Object Erasure", r"erasure|erase"),
    ("Intercepting User Inputs", r"intercept|pin.?pad|keypad"),
    ("GUI Switch", r"gui.?switch|guiswitch"),
    ("control", r"control|baseline|no.?attack|original|benign"),
]


def guess_label(path: str) -> str:
    low = path.lower().replace("_", " ").replace("-", " ")
    for name, pat in ATTACKS:
        if re.search(pat, low):
            return name
    return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="folder where the artifact was unzipped")
    ap.add_argument("--labels", help="CSV with columns path,label (overrides guessed labels)")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "artifact"))
    args = ap.parse_args(argv)
    if not os.path.isdir(args.path):
        sys.exit(f"Not a folder: {args.path}\nDownload https://doi.org/10.6084/m9.figshare.28271207 and unzip it there.")

    overrides = {}
    if args.labels:
        with open(args.labels, newline="") as fh:
            overrides = {r["path"]: r["label"] for r in csv.DictReader(fh)}

    res = analyze_paths([args.path])
    rows = []
    for p in res.pages:
        if not p.path.lower().endswith((".html", ".htm")) or not p.is_xr:
            continue
        rel = os.path.relpath(p.path, args.path)
        label = overrides.get(rel, guess_label(rel))
        rules_mh = sorted({f.rule for f in p.findings if f.severity >= Severity.MEDIUM})
        rules_all = sorted({f.rule for f in p.findings if f.severity >= Severity.LOW})
        rows.append({"path": rel, "label": label, "flagged": p.alarm(Severity.MEDIUM),
                     "rules_medium_high": ";".join(rules_mh), "rules_low_plus": ";".join(rules_all)})

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "pages.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "label", "flagged", "rules_medium_high", "rules_low_plus"])
        w.writeheader()
        w.writerows(rows)

    by = defaultdict(lambda: [0, 0])
    for r in rows:
        by[r["label"]][0] += int(r["flagged"])
        by[r["label"]][1] += 1
    att = [v for k, v in by.items() if k not in ("control", "unknown")]
    att_flag, att_tot = sum(v[0] for v in att), sum(v[1] for v in att)
    ctl_flag, ctl_tot = by["control"] if "control" in by else (0, 0)
    tp, fn, fp, tn = att_flag, att_tot - att_flag, ctl_flag, ctl_tot - ctl_flag
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")

    lines = ["# XRLint on the Shadowed Realities artifact", "",
             f"Folder scanned: `{args.path}` ({len(rows)} XR pages, {len(res.errors)} errors).", "",
             "| Label | Flagged / pages |", "|---|---|"]
    for k in sorted(by):
        lines.append(f"| {k} | {by[k][0]}/{by[k][1]} |")
    lines += ["", f"Attack pages flagged (recall): {tp}/{tp + fn} = {rec:.2f}" if tp + fn else "No attack pages labelled.",
              f"Control pages flagged (false alarms): {fp}/{fp + tn}" if fp + tn else "No control pages labelled.",
              f"Page-level precision: {prec:.2f}" if tp + fp else "",
              "", "Labels marked 'unknown' were not counted; fix them in a labels.csv and re-run.",
              "Note: the artifact apps were built to contain the paper's 14 UI properties, and XRLint's rules",
              "were written from the same paper, so recall here is an optimistic upper bound."]
    with open(os.path.join(args.out, "summary.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
