# Medium/high findings in moonrider

Source: supermedium/moonrider @ f756aa6 2024-03-04

0/1 XR pages have at least one medium/high finding.

| File | Line | Severity | Rule | Message | Review note |
|---|---|---|---|---|---|
| src/components/active-item.js | 27 | medium | `P3-synthetic-input` | script fires a synthetic 'mouseleave' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/debug-controller.js | 26 | medium | `P3-synthetic-input` | script fires a synthetic 'triggerdown' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/debug-controller.js | 27 | medium | `P3-synthetic-input` | script fires a synthetic 'triggerup' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/debug-controller.js | 56 | medium | `P3-synthetic-input` | script fires a synthetic 'triggerup' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/debug-controller.js | 59 | medium | `P3-synthetic-input` | script fires a synthetic 'triggerdown' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/debug-controller.js | 68 | medium | `P3-synthetic-input` | script fires a synthetic 'triggerup' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/debug-controller.js | 71 | medium | `P3-synthetic-input` | script fires a synthetic 'triggerdown' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/debug-intro.js | 6 | high | `P3-synthetic-input` | script fires a synthetic 'click' event; listeners that only check the event name cannot tell it from a real user action. | |
| src/components/materials.js | 575 | medium | `P13-scene-capture` | script reads back the rendered scene; this exposes the user's 3D view to page scripts. | |
| src/components/super-keyboard.js | 353 | high | `P6-dynamic-cursor` | script adds 'raycaster' to 'this.hand' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/super-keyboard.js | 362 | high | `P6-dynamic-cursor` | script adds 'raycaster' to 'this.hand' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/super-keyboard.js | 461 | high | `P6-dynamic-cursor` | script adds 'raycaster' to 'this.hand' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/super-keyboard.js | 468 | high | `P6-dynamic-cursor` | script adds 'raycaster' to 'this.hand' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/super-keyboard.js | 481 | high | `P6-dynamic-cursor` | script adds 'raycaster' to 'this.hand' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/super-keyboard.js | 492 | high | `P6-dynamic-cursor` | script adds 'raycaster' to 'this.hand' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/super-keyboard.js | 537 | high | `P2-js-transparency` | script hides 'this.cursor', which is a cursor/controller; a fake cursor can then stand in for the real one. | |
