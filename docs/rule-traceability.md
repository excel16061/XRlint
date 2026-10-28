# Rule-by-rule traceability to the paper

Source: Mukherjee, Mohamed, Arunasalam, Farrukh, Celik. *Shadowed Realities: An Investigation
of UI Attacks in WebXR.* USENIX Security 2025. Section and table numbers refer to that paper:

- §3: motivation and threat model
- §5.2 / Table 1: the 14 UI properties
- §5.3 / Table 2: taxonomy and existing attacks
- §5.4.1–5.4.5: the five new attacks
- §6.2: interaction metrics
- §8: discussion and developer guidelines
- Table 8 (appendix): per-attack property descriptions

| Rule ID | Severity range | Property (Table 1) | Paper attacks using it (§ / Table) | Paper guidance it implements (§8) | What XRLint checks | Fixture pair |
|---|---|---|---|---|---|---|
| `P1-third-party-script` | info | P1 Absence of iframe | GCJ, CCJ, BST, AAD, Malvertising, DoS (both), Object Erasure, Intercepting Inputs, GUI Switch (§3, §5.3, §5.4.1–5.4.3, Table 8) | — (platform property) | Remote `<script src>` on a page with `<a-scene>` | — |
| `P2-transparent-interactive` | medium–high | P2 Transparency | Intercepting Inputs, DoS-invisibility, Object Erasure (§5.3); Malvertising (§5.4.1); Sequential Rendering (§5.4.5) | Monitor ads' opacity changes; avoid clickable objects behind transparent ones | Ray-hittable entity with opacity ≤ 0.05 (high) or `visible: false` (medium); invisible mesh when the ray hits everything (medium) | `unit/p2_transparent_hitbox_*` |
| `P2-js-transparency` | low–high | P2 Transparency | GCJ hides the real cursor; CCJ hides the fake controller (§5.3, Table 8); DoS through overriding uses invisible controllers (§5.4.3) | Monitor opacity changes | Script sets `visible` false / opacity 0; high if the element is a cursor or controller | `unit/p6_dynamic_cursor_risky` |
| `P3-synthetic-input` | medium–high | P3 Synthetic input | Input Forgery, Intercepting Inputs (§5.3); Visual Overlapping (§5.4.4); Sequential Rendering (§5.4.5) | Validate input source; reject synthetic events (`isTrusted`, intersection data) | `emit('click'|'fusing'|...)`, `dispatchEvent(new …Event('click'))`, `.click()` | `unit/p3_synthetic_click_*` |
| `P4-same-space-overlap` | medium–high | P4 Same space overlapping objects; **also covers P11** (first rendered of fully overlapping objects gets the click) | Clickjacking via rendering vs interaction order (§5.3); Object Erasure, DoS-invisibility, Intercepting Inputs (§5.3); Sequential Rendering (§5.4.5) | Design: avoid layering clickable third-party objects | Two entities with the same position (±1 cm) and size (±5%), at least one interactive; high if only one is interactive or one is invisible | `unit/p4_same_space_*` |
| `P5-unvalidated-click` | low | P5 Event registration with only the event name | GCJ, CCJ, Input Forgery, Intercepting Inputs (§5.3, Table 8) | Input validation: check cursor id, intersection attributes, `isTrusted` | `click`/`fusing` handler body never reads `isTrusted`, `detail.cursorEl` or `detail.intersection` | `unit/p5_unvalidated_click_*` |
| `P6-dynamic-cursor` | low–high | P6 Cursor event sharing | CCJ (§5.3, Table 8). (DoS through overriding also injects controllers, but the paper attributes it to P14, not P6.) | Input validation (cursor id) | `setAttribute('cursor'|'raycaster'|'laser-controls'|…)` or `createElement('a-cursor')` in script; high if the same element is hidden | `unit/p6_dynamic_cursor_*` |
| `P7-blind-spot` | low–medium | P7 Blind spot | BST, CCJ, Input Forgery (§5.3, Table 8); measured by BSRf (§6.2) | Monitor ads' position changes | Interactive or ad-like entity behind the initial camera view (markup); script moving an element based on camera orientation | `unit/p7_blind_spot_*` |
| `P8-aux-screen-activity` | low–high | P8 Auxiliary screens (with P9) | AAD (§5.3, Table 8); Malvertising (§5.4.1). (GUI Switch's page swap on exit also triggers this rule, but the paper lists P1, P9, P13 for it.) | Block invalid auxiliary-screen redirection by overriding `window.open` | `window.open`, `location` changes, `createElement('iframe'|'video')`; high inside `enter-vr`/`exit-vr`/session handlers or after an in-VR check | `unit/p8_aux_screen_*` |
| `P9-mode-listener` | info | P9 Scene entry/exit detection | AAD (§5.3); Malvertising (§5.4.1); GUI Switch (§5.4.2) | Run-time monitoring of enter/exit events | `addEventListener('enter-vr'|'exit-vr'|'sessionstart'|…)` | (context only) |
| `P10-render-order` | low | P10 Sequential rendering | Clickjacking (§5.3); Sequential Rendering (§5.4.5) | Design: avoid loading clickable entities after transparent foreground elements | Explicit `renderOrder`, `render-order`, `depthTest: false` (markup or script). Default rendering order is **not** detectable | `unit/p10_render_order_*` |
| *(no separate rule)* | — | P11 Click to first rendered of fully overlapping objects | Clickjacking (§5.3) | — | Covered by `P4-same-space-overlap`; engine behaviour itself is not checkable | — |
| `P12-occluded-interactive` | medium | P12 Click received by first clickable intersected entity | Visual Overlapping (§5.4.4); Sequential Rendering (§5.4.5); Malvertising (§5.4.1); DoS-invisibility, Intercepting Inputs (§5.3) | Design: avoid rendering clickable third-party objects behind unclickable ones | Opaque (≥ 0.5), visible, non-ray-target entity between the camera and an interactive entity, overlapping it in view | `unit/p12_occluded_*` |
| `P13-scene-capture` | medium–high | P13 3D capture (new in the paper) | GUI Switch (§5.4.2) | (none specific) | `components.screenshot`, `getCanvas`, `toDataURL`, `toBlob`, `readPixels`, `captureStream`; high on a timer or near a network send | `unit/p13_capture_*` |
| `P14-gaze-override` | medium–high | P14 Gaze-fusing override (new in the paper) | DoS through overriding (§5.4.3) | (none specific) | Fuse cursor plus controller rays in the same page; high if the rays are hidden or added by script | `unit/p14_gaze_override_*` |

## Paper attack → XRLint rules (quick reverse lookup)

| Attack (category, §) | Properties (Table 8) | Rules that can fire |
|---|---|---|
| GCJ (Click Manipulation, §5.3) | P1, P2, P5 | P2-js, P5 |
| CCJ (Click Manipulation, §5.3) | P1, P2, P5, P6, P7 | P2-js, P5, P6, P7 |
| Clickjacking (Click Manipulation, §5.3) | P4, P10, P11 | P4 |
| Visual Overlapping (Click Manipulation, §5.4.4) | P3, P12 | P3, P12 |
| Sequential Rendering (Click Manipulation, §5.4.5) | P2, P3, P4, P10, P12 | P2, P3, P4, P10, P12 |
| BST (Peripheral Exploitation, §5.3) | P1, P7 | P7 |
| AAD (Peripheral Exploitation, §5.3) | P1, P8, P9 | P8, P9 |
| Input Forgery (Peripheral Exploitation, §5.3) | P3, P5, P7 | P3, P5, P7 |
| Malvertising (Peripheral Exploitation, §5.4.1) | P1, P2, P8, P9, P12 | P2, P8, P9, P12 |
| DoS via invisibility (Functionality Disruption, §5.3) | P1, P2, P4, P12 | P2, P4, P12 |
| DoS through overriding (Functionality Disruption, §5.4.3) | P1, P2, P14 | P2-js, P14 (P6 also fires, outside the paper's list) |
| Object Erasure (Functionality Disruption, §5.3) | P1, P2, P4 | P2, P4 |
| Intercepting User Inputs (UI-based Privacy Leakage, §5.3) | P1, P2, P3, P4, P5, P12 | P2, P3, P4, P5, P12 |
| GUI Switch (UI-based Privacy Leakage, §5.4.2) | P1, P9, P13 | P9, P13 (P8 also fires, outside the paper's list) |

"Rules that can fire" lists the rules mapped to the paper's properties for that attack. P1 has no scored rule. Whether it fires depends on the
attack being visible in the source. See `threat-model.md` §3 for what actually fired on our
re-implementations.
