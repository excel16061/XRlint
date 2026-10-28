# Medium/high findings in aframe_examples

Source: aframevr/aframe @ 022bcc5 2026-07-13, examples/

3/104 XR pages have at least one medium/high finding.

| File | Line | Severity | Rule | Message | Review note |
|---|---|---|---|---|---|
| showcase/hand-tracking/button.js | 60 | high | `P3-synthetic-input` | script fires a synthetic 'click' event; listeners that only check the event name cannot tell it from a real user action. | |
| showcase/spatial-ui/index.html | 40 | medium | `P2-transparent-interactive` | <a-entity class='close-button'> is visible=false but is a ray target; whether it still receives clicks depends on the three.js/A-Frame version, so verify manually. | |
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
