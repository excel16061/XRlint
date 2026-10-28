# Manual review of medium/high findings on benign code

Reviewer: the author of the tool (single reviewer, no second rater, so treat these
verdicts as one person's judgement). Every page reviewed here is benign, so none of
the findings is a "true attack". The question asked for each finding is narrower:
**is the flagged UI property really present in the code?**

Verdicts: **present** = the risky property is really used (a legitimate use);
**not present** = the rule matched code that does not actually use the property.

## A-Frame official examples (aframevr/aframe @ 022bcc5, `examples/`)

Note: rules were adjusted after the first run on this corpus (see README, "What changed
after the first run"), so these numbers are not an unbiased estimate.

| File | Line(s) | Rule | Verdict | Note |
|---|---|---|---|---|
| showcase/hand-tracking/button.js | 60 | P3 | present | a pressable button converts a hand "press" into a synthetic `click` |
| showcase/ui/highlight.js | 44 | P3 | present | synthetic `mouseleave` to reset hover state |
| showcase/ui/index.html | 61, 101, 109-112, 115 | P2 (visible=false target) | present | hidden panels inside a `.raycastable` parent, shown later at runtime |
| showcase/ui/index.html | 110, 111 (x2) | P4 | present | three movie images stacked in the same place, only one shown at a time |
| showcase/spatial-ui/index.html | 40 | P2 (visible=false target) | present | close button hidden until a panel opens |

13/13 findings: property present. 0/13 malicious.

## Held-out projects (scanned once, after rules were frozen; not tuned on)

| Project @ commit | File | Line(s) | Rule | Verdict | Note |
|---|---|---|---|---|---|
| a-painter @ 0deba1f | src/components/paint-controls.js | 23, 182-184 | P2-js (high), P6 (high) | present | controller entity is hidden until the user enters VR |
| moonrider @ f756aa6 | src/components/active-item.js | 27 | P3 | present | synthetic `mouseleave` |
| moonrider | src/components/debug-controller.js | 26, 27, 56, 59, 68, 71 | P3 | present | debug tool that simulates trigger presses |
| moonrider | src/components/debug-intro.js | 6 | P3 (high) | present | debug flag skips the intro by emitting `click` on the start button |
| moonrider | src/components/materials.js | 575 | P13 | **not present** | `toDataURL` on an offscreen 2D canvas used to build an environment-map texture, not a read-back of the rendered scene |
| moonrider | src/components/super-keyboard.js | 353, 362, 461, 468, 481, 492 | P6 (high) | **not present** (judgement call) | the line is hidden only when the raycaster is also disabled (`enabled: false`), so there is no hidden *active* ray |
| moonrider | src/components/super-keyboard.js | 537 | P2-js (high) | present | cursor hidden while a font loads |
| superframe @ a46f0a4 | components/camera-recorder/lib/CCapture.js | 63, 244, 264, 279, 425 | P13 | present | recording library that reads back the canvas |
| superframe | components/camera-recorder/lib/download.js | 87 | P3 | **not present** (for XR) | `.click()` on a 2D download link, not on an XR entity |
| superframe | components/geometry-merger/examples/basic/index.html | 67-69 | P2 (visible=false target) | present | invisible originals kept as ray targets so hovering the merged mesh works |

21/29 findings: property present; 8/29 not present (6 of them are one judgement call on
`super-keyboard.js`). 0/29 malicious.

Two things this review taught:

1. "Is the property present?" and "is this an attack?" are different questions. On
   benign code the tool is mostly right about the first and, by construction, always
   wrong about the second whenever it raises a medium/high finding.
2. The `superframe` geometry-merger example and the `model-viewer` showcase
   (an invisible 30 x 20 m plane with class `raycastable`, used as a laser hit surface)
   both rely on invisible entities being ray targets. That suggests A-Frame's raycaster
   does hit invisible entities, but I only read the code; I did not test it in a browser.
