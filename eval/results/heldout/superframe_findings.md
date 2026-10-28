# Medium/high findings in superframe

Source: supermedium/superframe @ a46f0a4 2026-05-29

1/66 XR pages have at least one medium/high finding.

| File | Line | Severity | Rule | Message | Review note |
|---|---|---|---|---|---|
| components/camera-recorder/lib/CCapture.js | 63 | medium | `P13-scene-capture` | script reads back the rendered scene; this exposes the user's 3D view to page scripts. | |
| components/camera-recorder/lib/CCapture.js | 244 | medium | `P13-scene-capture` | script reads back the rendered scene; this exposes the user's 3D view to page scripts. | |
| components/camera-recorder/lib/CCapture.js | 264 | medium | `P13-scene-capture` | script reads back the rendered scene; this exposes the user's 3D view to page scripts. | |
| components/camera-recorder/lib/CCapture.js | 279 | medium | `P13-scene-capture` | script reads back the rendered scene; this exposes the user's 3D view to page scripts. | |
| components/camera-recorder/lib/CCapture.js | 425 | medium | `P13-scene-capture` | script reads back the rendered scene; this exposes the user's 3D view to page scripts. | |
| components/camera-recorder/lib/download.js | 87 | medium | `P3-synthetic-input` | script calls .click() programmatically. | |
| components/geometry-merger/examples/basic/index.html | 67 | medium | `P2-transparent-interactive` | <a-entity id='box'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| components/geometry-merger/examples/basic/index.html | 68 | medium | `P2-transparent-interactive` | <a-entity id='sphere'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| components/geometry-merger/examples/basic/index.html | 69 | medium | `P2-transparent-interactive` | <a-entity id='cylinder'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
