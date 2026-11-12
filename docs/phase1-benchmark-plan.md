# Phase 1: reproducible baseline and independent benchmark protocol

**Status:** Local preparation; not committed or independently validated on the original research artifact.

## Existing evidence (reproduced locally)

- Unit suite: 54 tests, all passed.
- Self-authored attack fixtures: 12/14 flagged at medium/high severity.
- Self-authored benign fixtures: 1/15 flagged at medium/high severity.
- Attack-property coverage: 28/40 scored property pairs.
- Rule-level fixture micro-precision and recall: 20 TP, 0 FP, 0 FN; these labels and examples were authored alongside the rules and do not support a generalization claim.

## Reproduce without overwriting prior results

From the project root, with dependencies installed:

```sh
python eval/phase1_baseline.py --out eval/phase1-output
```

The output contains a JSON manifest with SHA-256 hashes of fixture inputs and analyzer Python files, environment information, command exit codes and captured test output. Results are local, not independent third-party validation. The command does not overwrite `eval/results/`.

## Independent benchmark protocol (not yet executed)

1. Acquire the original *Shadowed Realities* artifact from https://doi.org/10.6084/m9.figshare.28271207 and record archive URL, date, checksum, license and exact included applications. Do not assume the archive contains the claimed number of runnable WebXR pages.
2. Inventory entrypoints and dependencies. Record unavailable or non-runnable apps as execution failures rather than silently dropping them.
3. Define labels from the artifact's authors' descriptions and manual review, **before** examining XRlint findings. Never treat a guessed filename label as ground truth.
4. Freeze analyzer version, threshold (medium/high), parser configuration and exclusions before scoring. Run each distinct attack/control application once for primary case-level metrics. Report pages separately if an app has multiple pages.
5. Record TP, FP, TN, FN, withheld/unknown labels, execution failures, and denominators. Report precision and recall only when denominators are nonzero. Include per-rule coverage and a confusion matrix.
6. For benign held-out projects, separate property-presence correctness from attack-intent correctness; an accurately identified risky property can still be a false alarm for attack detection.
7. Keep self-authored, tuning, held-out and independently sourced artifact results in separate tables. Preserve raw output, reviewed labels, environment, hashes and a documented change log.
8. After baseline freeze, evaluate future versions on the same frozen test set. Do not tune on the final held-out set.

## Known risks and review gates

- `eval/evaluate_artifact.py` guesses labels from paths by default. These **must not** be reported as verified labels without review.
- The baseline test suite is not evidence that runtime-generated scene objects are detected.
- Reported 92% precision and 86% recall are only for self-authored attack/control fixtures.
- Original artifact evaluation is pending acquisition and manual labeling.
- No claim of novelty, general effectiveness, or real-world attack detection is established by Phase 1.
