# Design

## 1. Goal and non-goals

**Goal:** given A-Frame/WebXR source, point to every place a security-sensitive UI property
from Shadowed Realities (Table 1) is used. For each one, give the file, line, the property, and
the reason the paper considers it risky, so that a human reviewer can decide.

**Non-goals:** deciding intent, blocking pages, measuring user impact (the paper's logging
framework does that), multi-user XR, non-A-Frame engines.

## 2. Architecture

```
            paths (files / folders)
                     │
              analyzer.py ── walks folders, skips libraries (aframe*, three*, *.min.js, dist/, node_modules/)
             ┌───────┴────────────────────────┐
        HTML page                         standalone .js
             │                                 │
        scene.py  load_page()                   │
   ┌─────────┼────────────────────┐             │
 BeautifulSoup   scripts: inline + local src     │
   │              (jsutil.make_source:           │
   │               comment-stripped, line map)   │
   ▼                       │                     │
 Scene model               │                     │
  • entities: world pos, size, opacity,          │
    visibility, mixins, parent, HUD flag         │
  • camera (pos, yaw)                            │
  • rays: present? objects selector? all?        │
  • handlers: markup / components / selectors    │
   │                       │                     │
   ▼                       ▼                     ▼
 SCENE_RULES (rules.py)   SCRIPT_RULES (rules.py) ◄┘
  P2, P4, P7, P10, P12,    P2-js, P3, P5, P6, P7-js,
  P14, P1                  P8, P9, P10, P13
             └──────────┬──────────┘
                 Finding(rule, severity, file, line, message, evidence)
                        │  dedupe by (rule, file, line, message)
                   report.py → text / JSON      cli.py → exit codes (--fail-on)
```

| Module | Responsibility | Size |
|---|---|---|
| `model.py` | `Severity`, rule metadata (paper property, why risky, legitimate use, paper attacks), `Finding` | small |
| `jsutil.py` | comment stripping that keeps line numbers, brace matching, `addEventListener` and `registerComponent` extraction, named-handler lookup | small |
| `scene.py` | builds the scene model from HTML | largest |
| `rules.py` | one function per rule; thresholds are constants at the top | medium |
| `analyzer.py`, `report.py`, `cli.py` | orchestration and output | small |

Dependencies: `beautifulsoup4` (HTML with source line numbers) and `soupsieve` (CSS
selectors, so a raycaster's `objects: .clickable` is resolved exactly as the browser would).

## 3. Key modelling decisions

1. **"Can a ray hit it?" follows A-Frame's raycaster.** A-Frame's `raycaster.refreshObjects`
   intersects `querySelectorAll(objects)`, or *everything* when `objects` is empty, and
   intersects recursively. XRLint mirrors this: selector matches and their descendants are
   targets, or all entities if any ray has no selector. Camera, cursor and controller entities
   (and anything attached to them) are "HUD" and are excluded from the geometry rules.
2. **"Interactive" = hittable AND (selected by a raycaster OR has a click handler).** Handlers
   are found in markup (`onclick`, `event-set__click`), in components registered via
   `AFRAME.registerComponent` that listen for click-like events, and in
   `querySelector(...)`/`getElementById(...)` receivers of `addEventListener('click')`.
3. **Geometry is approximate on purpose.** World position = sum of parent positions; sizes come
   from A-Frame's default primitive sizes (box 1×1×1, plane 1×1, sphere radius 1, …) times
   scale; only the camera's yaw is used. Entities under rotated or scaled parents are marked
   approximate. This is enough for "same place", "in front of" and "behind the initial view",
   which is what the paper's attacks need.
4. **Severity encodes how closely a pattern matches a paper attack**, not how dangerous the
   page is. For example, a synthetic `click` is high and a synthetic `mouseenter` is medium; a
   runtime controller is low, but high if that same element is hidden.
5. **Each rule ships its own counter-argument.** `Rule.legit` is printed next to every finding
   so the reviewer sees the legitimate use straight away.

## 4. Why static analysis

| For static | Against static |
|---|---|
| Runs before deployment: in CI, in an ad network's creative review, or in a store review. | Cannot see anything built at runtime (`createElement`, remote SDKs, frameworks). |
| No headset, browser, users or emulator needed; all benign corpora in this repo (251 HTML + 317 JS files) scan in about 6 s on one CPU. | Cannot tell whether an attack *worked* (who actually received the click). |
| Points to an exact file and line, which a developer can fix. | Easy to evade for an attacker who knows the rules. |
| Deterministic and reproducible; results can be committed and diffed. | Geometry and JS semantics are approximated. |
| The paper's own guidance (§8) is phrased as code-level advice. | Many findings are legitimate uses (risk, not intent). |

The decision was static-first for a few-week, single-person project without a headset,
explicitly as the first half of a static + dynamic design. The dynamic half (a headless
browser with a WebXR emulator, snapshotting the live scene into the same `Page` model so all
geometry rules work unchanged) is the main next step. The rules only read the `Page`/`Entity`
model, so a snapshot could fill the same model. One change would be needed: `Entity` currently
keeps a reference to its BeautifulSoup tag, which would have to become optional.

## 5. Other trade-offs

| Decision | Alternative | Why this one, and the cost |
|---|---|---|
| Regexes over JS text | A real JS parser (esprima, tree-sitter) | No extra dependencies; fast. Cost: fooled by obfuscation and by braces in strings, and it cannot follow data flow. Biggest source of script false positives. |
| Rules | ML classifier | No labelled corpus of malicious WebXR pages exists. Rules are explainable and map 1:1 to the paper. |
| Property-level findings | Malicious/benign verdict | The paper says every property has legitimate uses, so a verdict from source would overclaim. |
| Severity filtering (page "alarm" = medium+) | Report everything equally | Low findings (unvalidated handlers, runtime controllers) are everywhere in benign code. |
| Skip `*.min.js`, `aframe*`, `three*`, `dist/` | Scan everything | Library internals legitimately use these properties and drown the report. Cost: minified malicious code is skipped too. |
| Dedupe shared JS findings across pages | Report per page | A component file used by 20 pages should appear once in the report. Page-level metrics still use per-page findings. |

## 6. Extension points

- New rule: write a function `(Page) -> Iterable[Finding]` or `(JsSource) -> Iterable[Finding]`,
  register its metadata with `_r(...)` in `model.py`, append it to `SCENE_RULES`/`SCRIPT_RULES`,
  and add a risky/safe fixture pair plus labels.
- New input source (e.g. a dynamic scene snapshot): produce a `scene.Page` and reuse every rule.
