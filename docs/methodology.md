# Methodology and evaluation

All numbers are produced by the scripts in `eval/` and stored in `eval/results/`.
`bash scripts/fetch_corpora.sh && bash scripts/run_all.sh` regenerates every one of them.
I re-ran this from a fresh download and got identical results.

## 1. Research questions

- **RQ1 (implementation):** Does each rule fire on pages that use its property, and stay
  quiet on pages that don't?
- **RQ2 (attack coverage):** Which of the paper's 14 attacks, and which of their listed
  properties, can a static view of the code see?
- **RQ3 (benign noise):** How often do the rules fire on real, benign A-Frame code, and are
  those findings correct about the property?
- **RQ4 (authors' apps):** How does XRLint do on the paper's own attack and control apps?
  *Not answered yet.*

## 2. Test data and how it was chosen

| Set | Size | Selection | Ground truth |
|---|---|---|---|
| **Unit pages** `tests/fixtures/unit/` | 22 (11 risky + 11 safe) | One minimal risky page and one minimal safe page for each rule that is not info-level. Each safe page changes only what makes the property absent (e.g. same button but visible, or the bait also clickable). | Rule ids whose property is present (`labels.json`). |
| **Control apps** `tests/fixtures/controls/` | 4 | Benign apps modelled on the paper's four app types (gaming, shopping, reading, travel, §6.3), using common A-Frame idioms such as unvalidated click handlers and hiding targets when hit. | Rule ids whose property is genuinely present; e.g. the reading app has both gaze and controllers, so P14 is present. |
| **Attack pages** `tests/fixtures/attacks/` | 14 | One page per attack in the paper's taxonomy (Table 2 / Table 8), written by me from the paper's text descriptions. The attack code sits in a separate local "SDK" file, as if vendored third-party code. **Not the authors' code.** | The properties the paper lists for that attack (Table 8). This comes from the paper, not from what XRLint can detect. |
| **A-Frame official examples** | 119 HTML pages (104 with a scene) | Everything in `examples/` of `aframevr/aframe` at commit `022bcc5` (2026-07-13). Chosen because the paper's own study apps were built from A-Frame examples, and the set is benign by construction. | All benign. Medium/high findings manually reviewed. |
| **Held-out projects** | 132 HTML (77 with a scene), 314 JS files | Four well-known open-source A-Frame projects: a-painter (`0deba1f`), moonrider (`f756aa6`), superframe (`a46f0a4`), aframe-extras (`676f362`). The paper itself cites A-Painter and Moonrider as examples of WebXR apps. Chosen before scanning. **Scanned once, with rules frozen.** | All benign. Medium/high findings manually reviewed. |
| **Authors' artifact** | 56 attack + 4 control apps (per the paper) | — | Not run: figshare was blocked from my environment. `eval/evaluate_artifact.py` is ready. |

**Order of work (visible in the git history):** rules and analyzer → fixtures and labels
committed → first evaluation run (saved in `eval/results/first_run/`) → three fixes → final
run → held-out scan, once.

## 3. How precision and recall were measured

**Rule level (RQ1)** on unit and control pages. For each (page, rule) pair with an info-level
rule excluded (P1, P9), a **true positive** means the rule fired at low severity or above and
the label says the property is present. A **false positive** means it fired but the label
says absent. A **false negative** means the label says present but the rule did not fire.
Precision = TP / (TP + FP) and recall = TP / (TP + FN), micro-averaged over all pairs.

**Page level (RQ2)** uses a page "flag": any medium or high finding. Recall = attack pages
flagged / 14. False alarms = benign fixture pages (11 safe unit pages + 4 controls) flagged.
Page-level precision = flagged attack pages / all flagged pages.

**Property coverage (RQ2):** for each attack, take the properties the paper lists for it
(P1 excluded, being a platform fact). A property is "covered" if a rule mapped to that property
fired (low or above; mapping in `labels.json → property_to_rules`, with P11 mapped to the P4
rule).

**Benign corpora (RQ3).** Every medium/high finding is a false alarm with respect to intent. I
manually labelled each one as *property present* or *property not present* to measure how
accurate the property detection is. I also report counts per rule at each severity. Most
application code in the held-out projects is bundled JS that no HTML page references, so I
report findings and files rather than "flagged pages".

## 4. Results

| | First run | After fixes |
|---|---|---|
| RQ1: micro precision / recall (unit + controls) | 0.95 / 1.00 (20 TP, 1 FP, 0 FN) | 1.00 / 1.00 (20 TP, 0 FP, 0 FN) |
| RQ2: attack pages flagged | 11/14 | 12/14 |
| RQ2: benign fixture pages flagged | 2/15 | 1/15 |
| RQ2: page-level precision | 11/13 = 0.85 | 12/13 = 0.92 |
| RQ2: property coverage | 27/40 | 28/40 |
| RQ3: A-Frame examples, scene pages flagged | 11/104 (43 findings, 10 files) | 3/104 (13 findings, 4 files) |
| RQ3: A-Frame examples, property present (manual) | — | 13/13 |
| RQ3: held-out, medium/high findings (files) | — | 29 (9), scanned once |
| RQ3: held-out, property present (manual) | — | 21/29 |

The three changes made between runs, and what triggered each, are listed in the README
("What changed after the first run").

## 5. What the numbers prove, and what they don't

**They do show that:**
- The rules implement what they claim on clear, minimal examples (RQ1).
- Static analysis of A-Frame source can see most of the property *combinations* behind the
  paper's attacks when the attack code is available and declarative. It sees 12 of 14 attacks
  on our re-implementations.
- It has a specific, explainable blind spot: anything created at runtime. Two attacks and most
  missed properties fall there (RQ2).
- In benign real-world code, the paper's risky properties are used legitimately and fairly
  often. A property-level tool will therefore produce findings that are mostly "correct but
  harmless" (RQ3: 34/42 correct about the property, 0/42 attacks).

**They do not show that:**
- XRLint detects real attacks in the wild. No real malicious WebXR page was tested.
- The 0.92 page-level precision or the 0.86 recall generalise. Both come from pages I wrote,
  in a style I chose, from the same descriptions the rules came from.
- The A-Frame example numbers are unbiased. The rules were changed after seeing them.
- The manual labels are reliable. There was a single reviewer and no agreement measure.
- Anything about the authors' 56 apps. Not run yet.
- Anything about other frameworks, minified code, or remote SDKs.

**Statistical note.** With 14 attack pages, one more or one fewer detection moves recall by
7 percentage points. These are counts to read individually, not rates to compare between
tools.

## 6. How to strengthen the evaluation (in order of value)

1. Run `eval/evaluate_artifact.py` on the authors' 56 + 4 apps (instructions in the README).
2. Get attack pages written by someone else, or from the wild.
3. A second reviewer for the manual labels, and Cohen's kappa.
4. A larger benign crawl with per-rule rates and confidence intervals.
5. A sensitivity analysis over the thresholds in `rules.py`.
6. Two quick browser checks: whether `isTrusted` is false on A-Frame entity clicks, and whether
   invisible entities stay ray targets.
