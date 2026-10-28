# Limitations and weaknesses

This is the most important document for an honest pitch. Each section says what fails,
gives the evidence from this repo, and says what it would take to fix it.

## 1. Where the tool fails to detect (false negatives)

| Failure | Evidence | Fix |
|---|---|---|
| **Scenes built at runtime are invisible.** The geometry rules (P2, P4, P7, P12) read only the HTML markup. | 2 of the 14 attack pages are never flagged (DoS via invisibility, Object Erasure). 12 of 40 (attack, property) pairs are missed, mostly because the object was made with `createElement`. | Add a **dynamic mode**: load the page in headless Chromium with a WebXR emulator, wait for scripts to run, snapshot the live A-Frame scene (entities plus `object3D` world transforms, materials, raycaster targets), and run the same rules on the snapshot. |
| **Remote third-party code is not fetched.** | By design, `https://...` scripts are only listed (`P1`, info). | In a review pipeline, fetch the SDK/creative and scan it too; better still, use the dynamic mode above. |
| **Rendering-order attacks have no code to point at.** P10/P11 are A-Frame's default behaviour. | Clickjacking and Sequential Rendering: P10 is always missed. | Only the overlap (P4) can be flagged statically. Confirming who receives the click needs the dynamic mode or the paper's logging framework. |
| **Logic computed with vector maths.** | Input Forgery's "is the ad behind the user?" check uses a dot product and is missed (P7). | Data-flow analysis on a real JavaScript AST, tracking values from `getWorldDirection` and similar camera reads. |
| **Non-A-Frame scenes.** Raw three.js, Babylon.js and WebXR API pages have no markup scene. | Not evaluated. | Dynamic snapshotting of the three.js scene graph, which also covers A-Frame. |
| **Transparency not expressed as `opacity` or `visible`.** Shaders, alpha textures, `colorWrite: false`. | Not covered by any rule. | Extend the material checks; in dynamic mode, render-and-compare: an object that is hit by the ray but changes no pixels is effectively invisible. |

## 2. Where the tool gives false alarms (false positives)

There are two different kinds, and it is important to keep them apart.

**(a) The property is really there, but used legitimately.** This is by far the most common
kind. On the held-out projects (rules frozen), 21 of 29 medium/high findings were this kind;
in the A-Frame examples, 13 of 13 were. Examples:

- a controller hidden until the user enters VR (a-painter);
- debug code that simulates trigger presses (moonrider);
- hidden UI panels that are ray targets (A-Frame `showcase/ui`);
- a reading app that offers both gaze and controller input (our control `c3_reading.html`, P14);
- a screen-recording library reading the canvas back (superframe).

These are *correct* property detections and *wrong* if read as attack detections. This is a
built-in limit of property-level analysis, which is why XRLint reports risk, not intent.

**(b) The property is not really there.** 8 of 29 held-out findings:

| Case | Cause | Fix |
|---|---|---|
| `toDataURL` on an offscreen 2D canvas (moonrider `materials.js`) | The rule cannot tell which canvas is read. | Resolve the receiver: only flag canvases that come from `renderer.domElement`, `sceneEl.canvas` or the screenshot component. |
| `.click()` on a 2D download link (superframe `download.js`) | `.click()` is matched on any element. | Only flag `.click()`/`emit('click')` on A-Frame entities (receiver resolved to an `a-*` element). |
| 6 findings on a ray that is hidden only while also disabled (moonrider `super-keyboard.js`) | Hidden and disabled are not distinguished. | Treat `enabled: false` as "not an active ray". |

**Low-severity noise.** On the A-Frame examples there are 28 `P5`, 29 `P6` and 25 `P2-js`
low findings. They are useful for hardening and too noisy for triage, which is why page-level
"alarm" counts only medium and high.

## 3. How someone could evade it

A motivated attacker who knows the rules can get past XRLint easily. That is the main reason
not to market it as an attack detector.

| Evasion | Defeats |
|---|---|
| Create the trap entities at runtime, or load the code from a remote URL | P2, P4, P7, P12 (geometry rules); all script rules if remote |
| Minify or obfuscate (`el['em'+'it']('cl'+'ick')`) | P3, P5, P6, P8, P13 |
| Rename variables (`cursor` → `c`, `adBanner` → `x`) | Severity escalation in P2-js, P7 (names are used as hints) |
| Transparency via a custom shader or alpha texture | P2 |
| Slightly offset positions or sizes (beyond 1 cm / 5%) | P4 |
| Put the occluder under a rotated parent, or use three.js directly | P12, P7 (geometry is approximate) |
| Timing: only act after N minutes, or only for some users | everything static |

**What would fix it.** Static rules are a first filter. Robustness needs runtime enforcement.
The paper's guidelines (§8) describe it: validate input sources, monitor enter/exit of
immersive mode, and watch ads' position, size and opacity changes. That fits a runtime monitor
or the isolation approach of AdCube (Lee et al., USENIX Security 2021), which confines
third-party ad code. The Shadowed Realities authors' group at Purdue is building a runtime
system that detects UI manipulation in WebXR (see `related-work.md`). XRLint should be read as
complementary to that, not as competition.

## 4. Weaknesses in the evaluation itself

| Weakness | Why it matters | Fix |
|---|---|---|
| I wrote both the rules and the attack pages, from the same paper | Recall on them is an upper bound (12/14 says the rules do what they were designed to do). | Run on the authors' artifact (script ready, not yet run). Better: attacks written by someone else, or found in the wild. |
| Rules were changed after the first run on the fixtures and the A-Frame examples | The "after" numbers on those sets are optimistic. | Both versions are reported; the held-out projects were scanned once with frozen rules. Keep a held-out set for every future change. |
| One reviewer for the manual labels | No agreement measure | A second reviewer plus Cohen's kappa, as the paper did for its coding. |
| Small, A-Frame-only corpus (104 + 77 scene pages) | Prevalence numbers are not general. | Crawl many public A-Frame repos and pages; report per-rule rates with confidence intervals. |
| No browser testing | Two behaviour claims, (i) `isTrusted` is false for A-Frame entity clicks and (ii) invisible entities stay ray targets, come only from reading A-Frame's source and examples. | A few minutes in a browser with a test page would settle both. |
| Thresholds chosen by judgement | Opacity ≤ 0.05, occluder ≥ 0.5, 1 cm, 5%: results may be sensitive to them. | A sensitivity sweep over each constant in `rules.py`. |

## 5. Engineering weaknesses

- JavaScript is pattern-matched with regexes, plus brace counting that braces in strings can
  confuse. A real parser (e.g. esprima or tree-sitter) would fix most of the script-rule false
  positives listed above.
- Parent rotation and scale are ignored, and only the camera's yaw is used. Full transform
  matrices would be needed for correct geometry.
- Scripts that no scanned HTML references (bundled app code) are scanned standalone, without
  page context. That is why page-level counts undercount on real apps.
