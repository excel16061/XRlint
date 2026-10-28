# Medium/high findings in aframe_examples

Source: github.com/aframevr/aframe @ 022bcc5f (2026-07-13), folder examples/

11/104 XR pages have at least one medium/high finding.

| File | Line | Severity | Rule | Message | Review note |
|---|---|---|---|---|---|
| performance/in-vr/components/controller.js | 16 | medium | `P6-dynamic-cursor` | script adds 'daydream-controls' at runtime; added controllers/cursors share the user's input events. | |
| performance/in-vr/components/controller.js | 18 | medium | `P6-dynamic-cursor` | script adds 'meta-touch-controls' at runtime; added controllers/cursors share the user's input events. | |
| performance/in-vr/components/controller.js | 19 | medium | `P6-dynamic-cursor` | script adds 'vive-controls' at runtime; added controllers/cursors share the user's input events. | |
| performance/in-vr/components/controller.js | 27 | medium | `P6-dynamic-cursor` | script adds 'raycaster' at runtime; added controllers/cursors share the user's input events. | |
| performance/in-vr/components/controller.js | 31 | medium | `P6-dynamic-cursor` | script adds 'cursor' at runtime; added controllers/cursors share the user's input events. | |
| showcase/hand-tracking/button.js | 60 | high | `P3-synthetic-input` | script fires a synthetic 'click' event; listeners that only check the event name cannot tell it from a real user action. | |
| showcase/link-traversal/js/components/link-controls.js | 23 | high | `P6-dynamic-cursor` | script adds 'laser-controls' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/link-traversal/js/components/link-controls.js | 24 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/link-traversal/js/components/link-controls.js | 32 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 12 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 13 | high | `P6-dynamic-cursor` | script adds 'cursor' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 162 | high | `P6-dynamic-cursor` | script adds 'laser-controls' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 163 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 167 | high | `P6-dynamic-cursor` | script adds 'laser-controls' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 168 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 224 | high | `P2-js-transparency` | script hides what looks like a cursor/controller; a fake cursor can then stand in for the real one. | |
| showcase/model-viewer/model-viewer.js | 310 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 320 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 342 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/model-viewer/model-viewer.js | 345 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/painter/components/brush.js | 37 | medium | `P6-dynamic-cursor` | script adds 'meta-touch-controls' at runtime; added controllers/cursors share the user's input events. | |
| showcase/post-processing/effect-controls.js | 21 | medium | `P6-dynamic-cursor` | script adds 'meta-touch-controls' at runtime; added controllers/cursors share the user's input events. | |
| showcase/post-processing/effect-controls.js | 24 | medium | `P6-dynamic-cursor` | script adds 'hand-tracking-controls' at runtime; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/index.html | 40 | medium | `P2-transparent-interactive` | <a-entity class='close-button'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| showcase/spatial-ui/ui-controller.js | 33 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/ui-controller.js | 36 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/ui-controller.js | 55 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/ui-controller.js | 58 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/ui-controller.js | 71 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/ui-controller.js | 74 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/ui-controller.js | 85 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/spatial-ui/ui-controller.js | 88 | high | `P6-dynamic-cursor` | script adds 'raycaster' at runtime in code that also hides elements; added controllers/cursors share the user's input events. | |
| showcase/ui/highlight.js | 44 | medium | `P3-synthetic-input` | script fires a synthetic 'mouseleave' event; listeners that only check the event name cannot tell it from a real user action. | |
| showcase/ui/index.html | 61 | medium | `P2-transparent-interactive` | <a-entity id='background'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| showcase/ui/index.html | 101 | medium | `P2-transparent-interactive` | <a-entity id='infoPanel'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| showcase/ui/index.html | 109 | medium | `P2-transparent-interactive` | <a-entity id='ponyoMovieImage'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| showcase/ui/index.html | 110 | high | `P4-same-space-overlap` | <a-entity id='kazetachinuMovieImage'> and <a-entity id='ponyoMovieImage'> (line 109) have the same position and size (one of them is invisible); the user cannot tell which one receives the click. | |
| showcase/ui/index.html | 110 | medium | `P2-transparent-interactive` | <a-entity id='kazetachinuMovieImage'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| showcase/ui/index.html | 111 | high | `P4-same-space-overlap` | <a-entity id='karigurashiMovieImage'> and <a-entity id='ponyoMovieImage'> (line 109) have the same position and size (one of them is invisible); the user cannot tell which one receives the click. | |
| showcase/ui/index.html | 111 | high | `P4-same-space-overlap` | <a-entity id='karigurashiMovieImage'> and <a-entity id='kazetachinuMovieImage'> (line 110) have the same position and size (one of them is invisible); the user cannot tell which one receives the click. | |
| showcase/ui/index.html | 111 | medium | `P2-transparent-interactive` | <a-entity id='karigurashiMovieImage'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| showcase/ui/index.html | 112 | medium | `P2-transparent-interactive` | <a-entity id='movieTitle'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
| showcase/ui/index.html | 115 | medium | `P2-transparent-interactive` | <a-entity id='movieDescription'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
