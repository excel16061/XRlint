# Medium/high findings in a-painter

Source: aframevr/a-painter @ 0deba1f 2022-10-26

0/1 XR pages have at least one medium/high finding.

| File | Line | Severity | Rule | Message | Review note |
|---|---|---|---|---|---|
| src/components/paint-controls.js | 23 | high | `P2-js-transparency` | script hides 'el', which is a cursor/controller; a fake cursor can then stand in for the real one. | |
| src/components/paint-controls.js | 182 | high | `P6-dynamic-cursor` | script adds 'vive-controls' to 'el' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/paint-controls.js | 183 | high | `P6-dynamic-cursor` | script adds 'oculus-touch-controls' to 'el' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
| src/components/paint-controls.js | 184 | high | `P6-dynamic-cursor` | script adds 'windows-motion-controls' to 'el' at runtime and also hides that element; added controllers/cursors share the user's input events. | |
