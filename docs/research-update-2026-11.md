# XRlint research update — November 2026

**Researcher and maintainer:** Syed Omer Ali  
**Contact:** omer@exetech.dev  
**Project:** https://github.com/excel16061/XRlint

## Status

XRlint remains an ongoing, independently implemented research prototype for identifying security-sensitive UI properties in A-Frame/WebXR applications. Its detection taxonomy is motivated by *Shadowed Realities: An Investigation of UI Attacks in WebXR* (USENIX Security 2025). The paper's authors must continue to be credited for their original research; XRlint's implementation and evaluation are separate work.

## Implemented capabilities

- Static HTML/A-Frame scene modeling and approximate visibility, raycaster, overlap and occlusion checks.
- Pattern-based inspection of inline and local JavaScript for input synthesis, cursor manipulation, immersive-mode activity and scene capture.
- Command-line output, machine-readable JSON, rule/severity filters, and a localhost-only browser interface.
- Rule-level fixtures, attack-model fixtures, benign controls, evaluation scripts and reproducibility documentation.

## Evaluation and interpretation

The repository's existing evaluation reports detection of 12 of 14 **self-authored** attack-model pages. On these pages, reported page-level precision is 12/13 (about 92%) and recall is 12/14 (about 86%). These numbers do **not** establish accuracy on independent real-world attacks.

The project also documents scans of 104 official A-Frame scene examples (used for tuning) and a held-out collection of 132 HTML pages and 314 standalone JavaScript files. Findings on benign projects are not evidence of malicious intent. The original *Shadowed Realities* research artifact has **not** been evaluated by XRlint, and no result for that artifact is claimed.

## Verification

The supplied November 2026 archive's unit suite was executed locally using `python -m unittest discover -s tests -q`: **54 tests passed**. This verifies the tests in that archive, not the entire external evaluation or deployed GitHub version.

## Next research steps

1. Evaluate the original authors' attack/control artifact with independently checked labels.
2. Add JavaScript AST analysis and assess whether it improves precision and coverage.
3. Explore controlled runtime instrumentation for dynamically created XR entities.
4. Report rule-level results, denominators, false positives, withheld conclusions and versioned corpus provenance.
5. Avoid claims of detecting attacker intent from a property-only static finding.

This document records progress on the **existing XRlint research project**; it is not a new project or a peer-reviewed publication.
