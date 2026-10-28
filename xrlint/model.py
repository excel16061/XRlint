"""Core data types: severities, rule metadata, and findings.

Every rule is tied to one of the 14 security-sensitive UI properties
(P1-P14) listed in Table 1 of:

    C. Mukherjee, R. Mohamed, A. Arunasalam, H. Farrukh, Z. B. Celik.
    "Shadowed Realities: An Investigation of UI Attacks in WebXR".
    USENIX Security Symposium, 2025.

The property numbering below follows that table. A finding means
"this page uses a property that the paper shows can be abused";
it does NOT mean the page is malicious.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import IntEnum


class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def parse(cls, name: str) -> "Severity":
        return cls[name.strip().upper()]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name.lower()


@dataclass(frozen=True)
class Rule:
    id: str
    prop: str            # paper property, e.g. "P2"
    title: str
    why: str             # why it is risky (attack described in the paper)
    legit: str           # common legitimate use of the same property
    paper_attacks: tuple = ()


RULES: dict[str, Rule] = {}


def _r(*args, **kw) -> Rule:
    rule = Rule(*args, **kw)
    RULES[rule.id] = rule
    return rule


_r(
    "P1-third-party-script", "P1",
    "Third-party script loaded into a WebXR page",
    "WebXR has no iframe-like isolation for 3D content, so any script on the page "
    "(e.g. an ad SDK) can read the scene, add listeners and modify entities.",
    "Loading component libraries or analytics from a CDN.",
    ("GCJ", "CCJ", "BST", "AAD", "DoS-invisibility", "Object Erasure", "Intercepting Inputs", "GUI Switch"),
)
_r(
    "P2-transparent-interactive", "P2",
    "Invisible or near-transparent entity that the ray can hit",
    "A transparent mesh in front of real content silently receives the user's "
    "clicks (click hijacking, PIN interception, denial of interaction).",
    "Invisible 'hit boxes' that enlarge small targets.",
    ("Sequential Rendering", "Malvertising", "DoS-invisibility", "Object Erasure", "Intercepting Inputs"),
)
_r(
    "P2-js-transparency", "P2",
    "Script makes an element invisible or transparent at runtime",
    "Attacks in the paper inject transparent objects or hide the real cursor from JS, "
    "which a static scan of the HTML alone cannot see.",
    "Fading animations, hiding finished UI panels.",
    ("GCJ", "CCJ", "DoS-overriding"),
)
_r(
    "P3-synthetic-input", "P3",
    "Script emits synthetic input events (click, fusing, ...)",
    "Programmatic clicks look like real clicks to listeners that only check the event "
    "name, enabling ad-click fraud and forwarding of intercepted input.",
    "Forwarding events from a child to its parent, automated tests, keyboard accessibility.",
    ("Visual Overlapping", "Sequential Rendering", "Input Forgery", "Intercepting Inputs"),
)
_r(
    "P4-same-space-overlap", "P4",
    "Two entities occupy the same space and at least one is interactive",
    "When fully overlapping objects have the same size, the click goes to one of them "
    "(render/registration order) while the user sees the other (clickjacking, object erasure).",
    "Layered UI such as a button with a label or highlight on top.",
    ("Clickjacking", "Sequential Rendering", "DoS-invisibility", "Object Erasure", "Intercepting Inputs"),
)
_r(
    "P5-unvalidated-click", "P5",
    "Click/fusing handler does not check where the event came from",
    "Listeners registered by event name alone cannot tell a real cursor click from a fake "
    "cursor or a synthetic event. The paper's guideline is to check isTrusted, the cursor "
    "element and the intersection data.",
    "Almost every simple A-Frame app; it is only a problem when an attacker can inject events.",
    ("GCJ", "CCJ", "Input Forgery", "Intercepting Inputs"),
)
_r(
    "P6-dynamic-cursor", "P6",
    "Script adds a cursor / raycaster / controller at runtime",
    "Programmatically added controllers share the events of the physical controller; "
    "a hidden fake cursor can redirect or duplicate the user's clicks.",
    "Attaching controllers when a gamepad connects, switching input modes.",
    ("CCJ",),
)
_r(
    "P7-blind-spot", "P7",
    "Interactive or ad-like content placed or moved behind the user",
    "Objects behind the user collect impressions/clicks the user never sees.",
    "Content arranged all around the user in a 360-degree scene; HUDs that follow gaze.",
    ("CCJ", "BST", "Input Forgery"),
)
_r(
    "P8-aux-screen-activity", "P8",
    "Page opens windows, navigates or injects 2D media while in immersive mode",
    "The 2D page keeps running on the HMD's auxiliary screen; ads or redirects there are "
    "invisible to the immersed user.",
    "Link traversal between WebXR pages, opening an external store page on request.",
    ("AAD", "Malvertising"),
)
_r(
    "P9-mode-listener", "P9",
    "Page listens for entering/exiting immersive mode",
    "Scene entry/exit events let an attacker time hidden activity (start ads on enter, "
    "stop on exit, swap the page on exit).",
    "Adjusting UI for VR, pausing media.",
    ("AAD", "Malvertising", "GUI Switch"),
)
_r(
    "P10-render-order", "P10",
    "Script or markup manipulates render order / depth testing",
    "Control over which object is drawn last lets a later-rendered object visually hide "
    "an earlier one that still receives clicks.",
    "Drawing UI on top of the scene, transparency sorting fixes.",
    ("Clickjacking", "Sequential Rendering"),
)
_r(
    "P12-occluded-interactive", "P12",
    "Non-interactive object visually covers an interactive one",
    "The ray ignores non-interactive objects, so a click aimed at the visible 'bait' is "
    "received by the hidden interactive object behind it (e.g. an ad).",
    "Decorative frames or glass panels in front of buttons.",
    ("Visual Overlapping", "Sequential Rendering", "Malvertising", "DoS-invisibility", "Intercepting Inputs"),
)
_r(
    "P13-scene-capture", "P13",
    "Script captures the rendered scene (screenshot / canvas read-back)",
    "Programmatic screenshots let third-party code see the user's 3D environment "
    "without consent (GUI Switch).",
    "A 'take a photo' feature, sharing, automated testing.",
    ("GUI Switch",),
)
_r(
    "P14-gaze-override", "P14",
    "Gaze (fuse) cursor coexists with controller rays",
    "Controller raycasting takes priority over gaze fusing; a hidden controller ray can "
    "suppress gaze feedback such as warnings (DoS through overriding).",
    "Supporting both gaze and controller input.",
    ("DoS-overriding",),
)


@dataclass
class Finding:
    rule: str
    severity: Severity
    file: str
    line: int
    message: str
    evidence: str = ""
    page: str = ""  # HTML page that pulled this file in (if different)

    @property
    def meta(self) -> Rule:
        return RULES[self.rule]

    def key(self) -> tuple:
        return (self.rule, self.file, self.line, self.message)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.name.lower()
        d["property"] = self.meta.prop
        d["title"] = self.meta.title
        d["why"] = self.meta.why
        d["legitimate_uses"] = self.meta.legit
        return d
