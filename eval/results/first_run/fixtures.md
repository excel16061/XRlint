# Fixture evaluation

All pages here were written by the author of XRLint (see README for why this inflates scores).

## 1. Rule-level precision / recall (unit + control pages, findings >= low)

| Rule | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|
| `P10-render-order` | 1 | 0 | 0 | 1.00 | 1.00 |
| `P12-occluded-interactive` | 1 | 1 | 0 | 0.50 | 1.00 |
| `P13-scene-capture` | 1 | 0 | 0 | 1.00 | 1.00 |
| `P14-gaze-override` | 2 | 0 | 0 | 1.00 | 1.00 |
| `P2-js-transparency` | 2 | 0 | 0 | 1.00 | 1.00 |
| `P2-transparent-interactive` | 1 | 0 | 0 | 1.00 | 1.00 |
| `P3-synthetic-input` | 1 | 0 | 0 | 1.00 | 1.00 |
| `P4-same-space-overlap` | 1 | 0 | 0 | 1.00 | 1.00 |
| `P5-unvalidated-click` | 5 | 0 | 0 | 1.00 | 1.00 |
| `P6-dynamic-cursor` | 1 | 0 | 0 | 1.00 | 1.00 |
| `P7-blind-spot` | 3 | 0 | 0 | 1.00 | 1.00 |
| `P8-aux-screen-activity` | 1 | 0 | 0 | 1.00 | 1.00 |

Micro-averaged: precision 0.95, recall 1.00 (TP 20, FP 1, FN 0).

## 2. Page-level detection (flag = any medium/high finding)

Attack pages flagged: **11/14**. Benign pages with a false alarm: **2/15**.

| Attack page | Flagged | Max severity | Paper properties | Covered | Missed | Other rules fired |
|---|---|---|---|---|---|---|
| GCJ | yes | high | P1, P2, P5 | P2, P5 | - | P12-occluded-interactive |
| CCJ | yes | high | P1, P2, P5, P6, P7 | P2, P5, P6, P7 | - | - |
| Clickjacking (rendering vs interaction order) | yes | medium | P4, P10, P11 | P4, P11 | P10 | P5-unvalidated-click |
| Visual Overlapping | yes | high | P3, P12 | P3, P12 | - | P5-unvalidated-click |
| Sequential Rendering | yes | high | P2, P3, P4, P10, P12 | P3, P4 | P2, P10, P12 | P5-unvalidated-click |
| BST | **no** | low | P1, P7 | - | P7 | P5-unvalidated-click |
| AAD | yes | high | P1, P8, P9 | P8, P9 | - | P5-unvalidated-click |
| Input Forgery | yes | high | P3, P5, P7 | P3, P5 | P7 | - |
| Malvertising | yes | high | P1, P2, P8, P9, P12 | P2, P8, P9 | P12 | P5-unvalidated-click |
| DoS (invisibility) | **no** | low | P1, P2, P4, P12 | P2 | P4, P12 | P5-unvalidated-click |
| DoS through overriding | yes | high | P1, P2, P14 | P2, P14 | - | P5-unvalidated-click, P6-dynamic-cursor |
| Object Erasure | **no** | low | P1, P2, P4 | - | P2, P4 | P5-unvalidated-click |
| Intercepting User Inputs | yes | high | P1, P2, P3, P4, P5, P12 | P2, P3, P5 | P4, P12 | - |
| GUI Switch | yes | high | P1, P9, P13 | P9, P13 | - | P5-unvalidated-click, P8-aux-screen-activity |

| Benign page | False alarm | Rules at medium/high |
|---|---|---|
| unit/p2_transparent_hitbox_safe.html | no | - |
| unit/p3_synthetic_click_safe.html | no | - |
| unit/p4_same_space_safe.html | no | - |
| unit/p5_unvalidated_click_safe.html | no | - |
| unit/p6_dynamic_cursor_safe.html | no | - |
| unit/p7_blind_spot_safe.html | no | - |
| unit/p8_aux_screen_safe.html | no | - |
| unit/p10_render_order_safe.html | no | - |
| unit/p12_occluded_safe.html | no | - |
| unit/p13_capture_safe.html | no | - |
| unit/p14_gaze_override_safe.html | no | - |
| controls/c1_gaming.html | no | - |
| controls/c2_shopping.html | **yes** | P12-occluded-interactive |
| controls/c3_reading.html | **yes** | P14-gaze-override |
| controls/c4_travel.html | no | - |

## 3. Property coverage on attack pages

27/40 (attack, property) pairs produced a finding of the matching rule. P1 (no iframe isolation) is a platform property and is not scored.

## Disagreements with labels (unit + control pages)

- `controls/c2_shopping.html`: missed -, unexpected ['P12-occluded-interactive']
