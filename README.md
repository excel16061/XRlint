# XRLint

A static checker for A-Frame / WebXR pages that flags the **security-sensitive UI properties**
described in *Shadowed Realities: An Investigation of UI Attacks in WebXR*
(Mukherjee, Mohamed, Arunasalam, Farrukh, Celik — USENIX Security 2025).

That paper lists 14 UI properties of WebXR (Table 1, P1–P14) that malicious publishers,
advertisers or ad networks can combine into attacks such as clickjacking, invisible
click-interception and hidden ads. The paper's discussion names automated detection tools for
XR dark patterns as future work. XRLint is a small first attempt at the static part of that:
it reads a page's HTML and JavaScript and reports **where** a risky property is used, **which**
property it is, and **why** the paper considers it risky.

> **Related, in-progress work.** The paper authors' group at Purdue is building a *runtime*
> system that detects UI manipulation in WebXR (user-study announcement, April 2026; see
> `docs/related-work.md`). XRLint is static and should be read as a complement to that, not
> a competitor.

> **XRLint flags risk, not intent.** Every property it detects also has legitimate uses
> (the paper says so too), and most findings on real code are legitimate. Treat a finding
> as "a human should look here", not "this page is an attack".

---

## Run locally

Requires Python 3.9+ and two small dependencies (`beautifulsoup4`, `soupsieve`).

```bash
# 1. Get the code
git clone https://github.com/haniyakonain/xrlint.git && cd xrlint

# 2. Create an isolated environment and install XRLint into it
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .               # installs the `xrlint` command and its dependencies

# 3. Run the test suite (expect: Ran 54 tests ... OK)
python3 -m unittest discover -s tests

# 4. Check a page
xrlint tests/fixtures/unit/p12_occluded_risky.html
```

Run `source .venv/bin/activate` again in each new terminal before using `xrlint`.

### Web UI

Prefer a browser over the terminal? Start the built-in web UI (standard library only, no extra installs):

```bash
xrlint-web                     # or: python3 -m xrlint.web
```

Open <http://127.0.0.1:8000>, paste a page's HTML (or upload a page with its local `.js` files, or a
whole folder), and click **Check**. Findings appear as cards with severity, rule, line number, the
surrounding source and an explanation. **Load example** runs the occluded-ad page from the tests.
Use `--port 9000` to change the port. By default it only listens on your own machine; uploaded
files are scanned in a temporary folder that is deleted afterwards, and pages can only pull in
scripts from that upload.
Without installing, `python3 -m xrlint ...` works from the repo root (once the two
dependencies are installed).

## Usage

```bash
xrlint page.html                      # one page (its local <script src> files are scanned too)
xrlint site/                          # a whole folder (HTML + standalone .js)
xrlint site/ --min-severity medium    # hide low/info findings
xrlint site/ --format json > out.json
xrlint site/ --rules P3-synthetic-input,P8-aux-screen-activity
xrlint site/ --fail-on high           # exit code 1 if anything high is found (for CI)
xrlint --list-rules
```

Example output (`xrlint tests/fixtures/unit/p12_occluded_risky.html`):

```
tests/fixtures/unit/p12_occluded_risky.html
     13  MED   P12-occluded-interactive
               <a-plane id='door'> is not a ray target but sits between the camera and the interactive
               <a-box id='promo'> (line 14); a click aimed at it goes through to the hidden target.
               why risky: The ray ignores non-interactive objects, so a click aimed at the visible
               'bait' is received by the hidden interactive object behind it (e.g. an ad).
               legitimate use: Decorative frames or glass panels in front of buttons.
```

Severities: **high** (the pattern closely matches a paper attack, e.g. a synthetic `click`, a
redirect inside an `enter-vr` handler, a hidden cursor), **medium** (risky property clearly
present), **low** (property present, very common in normal code), **info** (context only).

## How it works

1. **Scene model** (`xrlint/scene.py`). The HTML is parsed with BeautifulSoup. For every
   A-Frame entity XRLint estimates its world position (sum of parent positions), size (from the
   primitive and its attributes, with A-Frame's default sizes), opacity and visibility (including
   mixins). It finds the camera (A-Frame's default is at height 1.6 m looking down −Z), every
   raycaster/cursor, and their `objects` selector. As in A-Frame's own raycaster, no selector
   means "intersect everything". An entity is **interactive** if a ray can hit it and it is
   either selected by a raycaster or has a click handler. Handlers are found in markup
   (`onclick`, `event-set__click`), in components registered with `AFRAME.registerComponent`
   that listen for click-like events, and in `querySelector(...).addEventListener('click', ...)`.
2. **Script scanning** (`xrlint/jsutil.py`). Inline scripts and local script files are
   comment-stripped and searched with regular expressions. Brace matching approximates
   handler bodies, for example "is this `window.open` inside an `enter-vr` handler?".
   This is not a JavaScript parser.
3. **Rules** (`xrlint/rules.py`). Each rule maps to one paper property:

| Rule | Paper property | What it flags | Legitimate use |
|---|---|---|---|
| `P1-third-party-script` | P1 | Third-party script loaded into a WebXR page (info) | Loading component libraries or analytics from a CDN. |
| `P2-transparent-interactive` | P2 | Invisible or near-transparent entity that the ray can hit | Invisible 'hit boxes' that enlarge small targets. |
| `P2-js-transparency` | P2 | Script makes an element invisible or transparent at runtime | Fading animations, hiding finished UI panels. |
| `P3-synthetic-input` | P3 | Script emits synthetic input events (click, fusing, ...) | Forwarding events, automated tests, accessibility. |
| `P4-same-space-overlap` | P4, P11 | Two entities with the same position and size, at least one interactive | Layered UI such as a button with a label on top. |
| `P5-unvalidated-click` | P5 | Click/fusing handler never checks where the event came from | Almost every simple A-Frame app. |
| `P6-dynamic-cursor` | P6 | Script adds a cursor / raycaster / controller at runtime (high if that element is hidden) | Attaching controllers when a gamepad connects. |
| `P7-blind-spot` | P7 | Interactive or ad-like content behind the initial view, or moved relative to the camera | 360° scenes; HUDs that follow gaze. |
| `P8-aux-screen-activity` | P8 | `window.open` / navigation / injected iframe or video while in immersive mode | Link traversal between WebXR pages. |
| `P9-mode-listener` | P9 | Listens for `enter-vr` / `exit-vr` (info) | Adjusting UI for VR. |
| `P10-render-order` | P10 | Render order / depth test manipulated | Drawing UI on top of the scene. |
| `P12-occluded-interactive` | P12 | Opaque non-interactive object between the camera and an interactive one | Decorative frames in front of buttons. |
| `P13-scene-capture` | P13 | Screenshot / canvas read-back (high if on a timer or near a network send) | A "take a photo" feature. |
| `P14-gaze-override` | P14 | Gaze fuse cursor plus controller rays (high if the rays are hidden or added at runtime) | Supporting both input types. |

**Not checked as separate rules:** P1 (no iframe isolation) is a property of the WebXR
platform, not of a page, so XRLint only lists remote scripts as `info`. P11 (fully overlapping
objects: the first rendered one receives the click) is engine behaviour, so it is covered by the
same-space rule `P4`.

A note on the paper's validation advice for P5: it recommends checking `isTrusted`, the cursor
id and the intersection data. From reading A-Frame's source, entity `click` events are
`CustomEvent`s dispatched by the cursor component, and the DOM gives `isTrusted: false` to any
event dispatched by script. So for A-Frame entity clicks, `detail.cursorEl` and
`detail.intersection` look like the useful checks. XRLint accepts any of the three. I have not
tested this in a browser.

---

## Evaluation

All numbers below are produced by scripts in `eval/` and stored in `eval/results/`
(`bash scripts/fetch_corpora.sh && bash scripts/run_all.sh` regenerates them). **What was
tested on which data:**

| Data | What it is | Who wrote it | Used for |
|---|---|---|---|
| `tests/fixtures/unit/` | 22 tiny pages: one risky and one safe page per rule | me (tool author) | rule-level precision/recall, unit tests |
| `tests/fixtures/controls/` | 4 benign apps modelled on the paper's app types (gaming, shopping, reading, travel) | me | false alarms, rule-level precision/recall |
| `tests/fixtures/attacks/` | 14 attack pages, one per attack in the paper's taxonomy, written from the paper's descriptions | me (**not** the paper's code) | page-level detection, property coverage |
| A-Frame official examples | `aframevr/aframe` @ `022bcc5`, folder `examples/`: 119 HTML pages, 104 with a scene | A-Frame project | false alarms on real benign code (**rules were adjusted after looking at it**) |
| Held-out projects | `aframevr/a-painter` @ `0deba1f`, `supermedium/moonrider` @ `f756aa6`, `supermedium/superframe` @ `a46f0a4`, `c-frame/aframe-extras` @ `676f362`: 132 HTML pages (77 with a scene) and 314 standalone JS files | their authors | false alarms on code the rules were **never tuned on** |
| Shadowed Realities artifact | the authors' 56 attack apps + 4 control apps | paper authors | **not run yet**: it could not be downloaded from my environment. See below. |

### 1. Fixtures (self-written)

Labels were written in `tests/fixtures/labels.json` and committed **before** the first run.
For the attack pages, the label is the set of properties the paper itself lists for each
attack (its Table 8), not what XRLint detects.

| | First run | After the fixes below |
|---|---|---|
| Rule-level, unit + control pages (≥ low): precision / recall | 0.95 / 1.00 (20 TP, 1 FP, 0 FN) | 1.00 / 1.00 (20 TP, 0 FP, 0 FN) |
| Attack pages flagged (any medium/high) | 11/14 | 12/14 |
| Benign fixture pages with a medium/high false alarm | 2/15 | 1/15 |
| (attack, property) pairs covered, P1 excluded | 27/40 | 28/40 |

Page-level, after fixes: 12 of 14 attack pages flagged and 1 of 15 benign pages flagged, i.e.
precision 12/13 ≈ 0.92 and recall 12/14 ≈ 0.86 **on pages I wrote myself**.

The two attacks never flagged are **DoS via invisibility** and **Object Erasure**. In both, the
attacker's script creates the transparent covering object at runtime with `createElement`, so
it never appears in the markup. Only a low-severity "script makes something transparent" hint
fires for the first, and nothing fires for the second. This is the runtime-scene limitation in
practice. Several other properties are also missed for the same reason (overlap and occlusion
created by JS). P10 is never detected for the clickjacking and sequential-rendering attacks,
because those rely on A-Frame's normal rendering order rather than any code that changes it.

The remaining benign false alarm is the reading app (`c3_reading.html`), which legitimately
offers both a gaze cursor and a laser controller. That is exactly property P14, so the rule
is "right" about the property and wrong about intent.

Full per-page table: `eval/results/fixtures.md`. First run: `eval/results/first_run/`.

### 2. A-Frame official examples (benign, used for tuning)

| | First run | After fixes |
|---|---|---|
| Scene pages with ≥1 medium/high finding | 11/104 | 3/104 |
| Medium/high findings (files) | 43 (10 files) | 13 (4 files) |

I manually reviewed the 13 remaining findings (`eval/results/manual_review.md`). In all 13
the property really is present, used legitimately: hidden UI panels that are ray targets,
stacked images shown one at a time, and a hand-tracking button that turns a press into a
synthetic `click`. Because the rules were changed after seeing this corpus, **3/104 is an
optimistic number.**

There is also a lot of noise at low severity: 28 `P5` (unvalidated click handlers), 29 `P6`
(controllers added at runtime) and 25 `P2-js` (elements hidden at runtime). That is why
those cases are low and not medium.

### 3. Held-out projects (scanned once, rules frozen)

| Project | HTML (scene) pages | JS files | Medium/high findings (files) |
|---|---|---|---|
| a-painter | 1 (1) | 27 | 4 (1) |
| moonrider | 18 (1) | 108 | 16 (5) |
| superframe | 103 (66) | 141 | 9 (3) |
| aframe-extras | 10 (9) | 38 | 0 (0) |
| **Total** | **132 (77)** | **314** | **29 (9)** |

Most application code in these projects lives in bundled JS that no HTML file references
directly, so it is scanned as standalone scripts. Counting "flagged pages" would therefore
undercount, and the table counts findings and files instead. Manual review of the 29
findings, by one reviewer (me): in **21** the property is really present, used legitimately
(a controller hidden until VR starts, debug code that simulates trigger presses, a screen
recorder that reads the canvas back). In **8** the property is not really there:

- `toDataURL` on an offscreen 2D canvas that is not the rendered scene;
- `.click()` on a 2D download link;
- 6 findings in one file where a ray's line is hidden only when the ray is also disabled (a judgement call).

**No finding on benign code is an attack**, so every medium/high finding on these projects
is a false alarm with respect to intent.

### 4. The paper's artifact (please run this on your machine)

The artifact (apps, logging framework, interaction-metrics library) is at
**https://doi.org/10.6084/m9.figshare.28271207**. My environment could not reach figshare
(the proxy returned 403), so I have not run XRLint on it and I do not know its folder layout.
To run it:

1. Download the archive from that DOI in your browser.
2. Unzip it into `data/shadowed_realities/` inside this repo (`data/` is git-ignored).
3. Run `python3 eval/evaluate_artifact.py data/shadowed_realities`.
4. Open `eval/results/artifact/pages.csv`. The script **guesses** each page's attack from its
   path. Correct the `label` column wherever it says `unknown` or is wrong (use the attack
   names in the script, or `control`), save the file as `eval/results/artifact/labels.csv`, and
   re-run with `--labels eval/results/artifact/labels.csv`.

It reports how many of the attack apps and how many of the control apps are flagged. Even
then, the result is an **upper bound**: the authors built those apps to exhibit the paper's
properties, and XRLint's rules were written from the same paper.

### What changed after the first run

These three changes were made after looking at the first-run results on the fixtures and the
A-Frame examples. They are the reason the "after" columns above are optimistic.

1. **Bug:** the cursor ring attached to the camera was treated as an object blocking the view
   (false P12 in the shopping control and the GCJ page). Camera, cursor and controller entities
   and their children are now excluded from the geometry rules.
2. **Precision:** adding a raycaster or controller at runtime is extremely common in benign code
   (6 example files, 9 example pages). `P6` is now low by default and high only if the **same element** is also
   hidden. Previously it was high if anything in the file was hidden. `P2-js` is escalated only
   when the hidden element is a cursor or controller.
3. **Recall:** the camera-orientation pattern used to detect content kept in the blind spot only
   matched variables named `camera`. It now also matches `cam`. This was found by the missed BST
   page, so BST being detected afterwards is partly a result of tuning.

---

## Limitations (please read)

- **Static analysis misses scenes built at runtime.** Anything created by `createElement`,
  loaded from a remote script, built by a framework (React/Vue), generated from templates, or
  obfuscated or minified is invisible to the scene model. Two of the 14 attack pages are missed
  for exactly this reason, and real third-party ad code would normally be remote and minified.
  Minified files (`*.min.js`) and A-Frame/three.js themselves are skipped on purpose.
- **Every flagged property has legitimate uses, so the tool flags risk, not intent.** On
  benign code, 34 of the 42 medium/high findings I reviewed were correct about the property
  (13/13 in the A-Frame examples, 21/29 in the held-out projects), and none were attacks.
  Deciding intent needs context: who wrote the code, where the click goes, whether money or
  data flows.
- **Recall on attack pages written to match the paper looks better than it would in the
  wild.** I wrote the attack pages and the rules from the same descriptions, so 12/14 measures
  "does the tool find what it was designed to find", not real-world recall. The same applies,
  more weakly, to the paper's own artifact. Real attackers could hide transparency inside a
  shader, compute positions, or rename events.
- **Geometry is approximate.** Parent rotation and scale are ignored (such entities are marked
  approximate internally), only camera yaw is used, glTF models and text have unknown size, and
  the camera may move. Occlusion and blind-spot checks therefore only describe the initial view.
- **JavaScript is pattern-matched, not parsed.** Brace counting can be fooled by braces in
  strings, handlers passed indirectly are skipped, and a variable's meaning is guessed from its
  name (e.g. "cursor", "ad").
- **Uncertain A-Frame behaviour.** Whether a `visible: false` entity still receives ray clicks
  is not documented clearly (the cursor docs say "closest visible intersected entity", while
  A-Frame's own model-viewer example uses an invisible plane as a ray target). Those findings
  are therefore medium and say "verify manually".
- **One reviewer.** The manual review was done by one person without a second rater.
- **A-Frame only.** Three.js, Babylon.js and raw WebXR pages are not modelled. Only the
  JS-pattern rules apply to them.

## References

- C. Mukherjee, R. Mohamed, A. Arunasalam, H. Farrukh, Z. B. Celik. *Shadowed Realities: An
  Investigation of UI Attacks in WebXR.* USENIX Security Symposium, 2025.
  PDF: https://habiba-farrukh.github.io/files/ShadowedRealities.pdf
- Shadowed Realities research artifacts: https://doi.org/10.6084/m9.figshare.28271207
- Attacks the taxonomy builds on, as cited by that paper: K. Cheng et al., *When the User Is
  Inside the User Interface: An Empirical Study of UI Security Properties in Augmented Reality*,
  USENIX Security 2024; H. Lee et al., *AdCube: WebVR Ad Fraud and Practical Confinement of
  Third-Party Ads*, USENIX Security 2021.
- A-Frame: https://github.com/aframevr/aframe (raycaster and cursor source read for the
  behaviour notes above).

