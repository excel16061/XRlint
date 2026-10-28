"""Rule implementations.

Scene rules look at the markup model (scene.Page); script rules look at
JavaScript text (jsutil.JsSource). Each rule returns Finding objects.
Thresholds are module constants so they are easy to discuss and change.
"""

from __future__ import annotations

import re
from typing import Iterable

from .jsutil import JsSource, listeners
from .model import Finding, Severity as S
from .scene import CLICK_EVENTS, CONTROLLER_COMPONENTS, Entity, Page, parse_props

TRANSPARENT_MAX_OPACITY = 0.05   # at or below this, an entity is treated as invisible
OCCLUDER_MIN_OPACITY = 0.5       # an occluder must be at least this opaque to hide what is behind it
SAME_POS_EPS = 0.01              # metres
SAME_SIZE_REL = 0.05             # 5 % relative size difference
BEHIND_MARGIN = 0.25             # metres behind the camera plane before we call it a blind spot
MAX_PAIRWISE = 2000              # skip pairwise checks for very large scenes

AD_WORD_RE = re.compile(r"(^|[^a-z])(ad|ads|advert|advertisement|banner|sponsor|sponsored|promo)([^a-z]|$)", re.I)
XR_CONTEXT_EVENTS = {"enter-vr", "exit-vr", "enter-ar", "exit-ar", "sessionstart", "sessionend"}
IN_XR_CHECK_RE = re.compile(r"""is\(\s*['"](vr|ar)-mode['"]\s*\)|\.isPresenting\b|xr\.getSession\(\)|isImmersive""")


def _tag_head(e: Entity) -> str:
    return str(e.tag).split(">", 1)[0][:118] + ">"


def _f(rule, sev, file, line, msg, ev="") -> Finding:
    return Finding(rule=rule, severity=sev, file=file, line=line, message=msg, evidence=ev[:120])


# ======================================================================
# Scene (markup) rules
# ======================================================================

def rule_transparent_interactive(page: Page) -> Iterable[Finding]:
    for e in page.entities:
        if not e.hit or e.surround or e.hud:
            continue
        invisible = e.opacity <= TRANSPARENT_MAX_OPACITY
        hidden = not e.visible
        if not (invisible or hidden):
            continue
        if e.interactive:
            if invisible:
                yield _f("P2-transparent-interactive", S.HIGH, page.path, e.line,
                         f"{e.label()} has opacity {e.opacity:g} but the ray can hit it"
                         + (f" and it handles clicks ({e.handler_reason})" if e.handler else
                            " (matched by raycaster 'objects')")
                         + "; it can silently receive clicks meant for what is behind it.",
                         _tag_head(e))
            else:
                yield _f("P2-transparent-interactive", S.MEDIUM, page.path, e.line,
                         f"{e.label()} is visible=false but is a ray target; whether it still receives "
                         "clicks depends on the three.js/A-Frame version, so verify manually.",
                         "")
        elif invisible and e.size is not None:
            # everything is intersectable and this invisible mesh blocks the ray
            yield _f("P2-transparent-interactive", S.MEDIUM, page.path, e.line,
                     f"{e.label()} has opacity {e.opacity:g}; the raycaster has no 'objects' filter, so this "
                     "invisible mesh blocks clicks to anything behind it.", "")


def _same(a: float, b: float) -> bool:
    return abs(a - b) <= max(SAME_SIZE_REL * max(abs(a), abs(b)), 1e-6)


def rule_same_space_overlap(page: Page) -> Iterable[Finding]:
    ents = [e for e in page.entities if e.size is not None and not e.surround and not e.hud]
    if len(ents) > MAX_PAIRWISE:
        return
    for i, a in enumerate(ents):
        for b in ents[i + 1:]:
            if not (a.interactive or b.interactive):
                continue
            if any(abs(p - q) > SAME_POS_EPS for p, q in zip(a.pos, b.pos)):
                continue
            if not all(_same(p, q) for p, q in zip(a.size, b.size)):
                continue
            mixed = a.interactive != b.interactive
            transp = min(a.opacity, b.opacity) <= TRANSPARENT_MAX_OPACITY or not (a.visible and b.visible)
            sev = S.HIGH if (mixed or transp) else S.MEDIUM
            later, earlier = (b, a)  # document order = A-Frame registration order
            why = []
            if mixed:
                why.append("only one of them is interactive")
            if transp:
                why.append("one of them is invisible")
            yield _f("P4-same-space-overlap", sev, page.path, later.line,
                     f"{later.label()} and {earlier.label()} (line {earlier.line}) have the same position "
                     f"and size" + (f" ({', '.join(why)})" if why else "")
                     + "; the user cannot tell which one receives the click.",
                     "")


def rule_occluded_interactive(page: Page) -> Iterable[Finding]:
    cam = page.camera
    fwd, right = cam.forward(), cam.right()

    def rel(e: Entity):
        d = [e.pos[k] - cam.pos[k] for k in range(3)]
        depth = sum(d[k] * fwd[k] for k in range(3))
        lat = sum(d[k] * right[k] for k in range(3))
        return depth, lat, d[1]

    targets = [e for e in page.entities if e.interactive and not e.surround and not e.hud]
    occluders = [e for e in page.entities
                 if not e.hud and not e.hit and not e.interactive and e.visible and e.size is not None and not e.surround
                 and e.opacity >= OCCLUDER_MIN_OPACITY]
    if len(targets) * len(occluders) > MAX_PAIRWISE * 50:
        return
    for t in targets:
        td, tl, ty = rel(t)
        if td <= 0:
            continue
        for o in occluders:
            if o.is_ancestor_of(t) or t.is_ancestor_of(o):
                continue
            od, ol, oy = rel(o)
            if not (0 < od < td):
                continue
            half_w = max(o.size[0], o.size[2]) / 2
            half_h = o.size[1] / 2
            if abs(tl - ol) <= half_w and abs(ty - oy) <= half_h:
                yield _f("P12-occluded-interactive", S.MEDIUM, page.path, o.line,
                         f"{o.label()} is not a ray target but sits between the camera and the interactive "
                         f"{t.label()} (line {t.line}); a click aimed at it goes through to the hidden target.",
                         "")
                break


def rule_blind_spot(page: Page) -> Iterable[Finding]:
    cam = page.camera
    fwd = cam.forward()
    for e in page.entities:
        if e.surround or e.hud:
            continue
        d = [e.pos[k] - cam.pos[k] for k in range(3)]
        depth = sum(d[k] * fwd[k] for k in range(3))
        if depth >= -BEHIND_MARGIN:
            continue
        adlike = any(AD_WORD_RE.search(str(e.attrs.get(k, ""))) for k in ("id", "class", "src"))
        if e.interactive:
            yield _f("P7-blind-spot", S.MEDIUM if adlike else S.LOW, page.path, e.line,
                     f"interactive {e.label()} is {abs(depth):.1f} m behind the initial camera view"
                     + (" and looks like an ad" if adlike else "") + ".", "")
        elif adlike:
            yield _f("P7-blind-spot", S.LOW, page.path, e.line,
                     f"ad-like {e.label()} is placed behind the initial camera view.", "")


def rule_gaze_override(page: Page) -> Iterable[Finding]:
    if not page.gaze_fuse:
        return
    dynamic = any(re.search(r"setAttribute\(\s*['\"](%s)['\"]" % "|".join(CONTROLLER_COMPONENTS), s.text)
                  for s in page.js)
    if not (page.controller_rays or dynamic):
        return
    hidden = False
    for t in page.controller_rays:
        line = parse_props(t.get("line") if isinstance(t.get("line"), str) else None)
        ray = parse_props(t.get("raycaster") if isinstance(t.get("raycaster"), str) else None)
        if _hidden_attr(t) or ray.get("showline", "").lower() == "false" or line.get("visible", "") == "false" \
                or line.get("opacity", "1").strip() in ("0", "0.0"):
            hidden = True
    sev = S.HIGH if (hidden or dynamic) else S.MEDIUM
    g = page.gaze_fuse[0]
    yield _f("P14-gaze-override", sev, page.path, g.sourceline or 1,
             "gaze fuse cursor coexists with controller rays"
             + (" that are hidden or added at runtime" if (hidden or dynamic) else "")
             + "; controller events take priority and can suppress gaze feedback.", "")


def _hidden_attr(tag) -> bool:
    v = tag.get("visible")
    return isinstance(v, str) and v.strip().lower() == "false"


def rule_third_party_scripts(page: Page) -> Iterable[Finding]:
    if not page.is_xr:
        return
    for line, url in page.remote_scripts:
        yield _f("P1-third-party-script", S.INFO, page.path, line,
                 f"remote script {url} runs with full access to the WebXR scene (no iframe isolation).", url)


SCENE_RULES = [rule_transparent_interactive, rule_same_space_overlap, rule_occluded_interactive,
               rule_blind_spot, rule_gaze_override, rule_third_party_scripts]


# ======================================================================
# Script rules
# ======================================================================

SYNTH_EMIT_RE = re.compile(
    r"""\.emit\(\s*['"](?P<ev>click|fusing|mousedown|mouseup|mouseenter|mouseleave|triggerdown|triggerup|select|selectstart)['"]""")
SYNTH_DISPATCH_RE = re.compile(
    r"""dispatchEvent\(\s*new\s+(?:Mouse|Pointer|Custom|XRInputSource)?Event\(\s*['"](?P<ev>click|fusing|mousedown|mouseup|select|selectstart)['"]""")
SYNTH_CLICK_RE = re.compile(r"""\.click\(\s*\)""")


def rule_synthetic_input(src: JsSource) -> Iterable[Finding]:
    for rx in (SYNTH_EMIT_RE, SYNTH_DISPATCH_RE):
        for m in rx.finditer(src.text):
            ev = m.group("ev")
            sev = S.HIGH if ev in ("click", "fusing", "select") else S.MEDIUM
            yield _f("P3-synthetic-input", sev, src.path, src.line_of(m.start()),
                     f"script fires a synthetic '{ev}' event; listeners that only check the event name "
                     "cannot tell it from a real user action.", src.snippet(m.start()))
    for m in SYNTH_CLICK_RE.finditer(src.text):
        yield _f("P3-synthetic-input", S.MEDIUM, src.path, src.line_of(m.start()),
                 "script calls .click() programmatically.", src.snippet(m.start()))


VALIDATION_RE = re.compile(r"isTrusted|cursorEl|\.intersection\b|detail\s*\.\s*intersection|detail\s*\.\s*cursor")


def rule_unvalidated_click(src: JsSource) -> Iterable[Finding]:
    for m, ev, body, b0 in listeners(src, {"click", "fusing"}):
        if not body:
            continue  # handler not resolvable statically; do not guess
        if VALIDATION_RE.search(body):
            continue
        yield _f("P5-unvalidated-click", S.LOW, src.path, src.line_of(m.start()),
                 f"'{ev}' handler never checks isTrusted / detail.cursorEl / detail.intersection, so "
                 "fake-cursor or synthetic clicks are accepted.", src.snippet(m.start()))


HIDE_RE = re.compile(
    r"""setAttribute\(\s*['"]visible['"]\s*,\s*(?:false|['"]false['"])"""
    r"""|setAttribute\(\s*['"]material['"]\s*,\s*['"][^'"]*opacity\s*:\s*0(?:\.0+)?\s*(?:;|['"])"""
    r"""|setAttribute\(\s*['"]material['"]\s*,\s*['"]opacity['"]\s*,\s*['"]?0(?:\.0+)?['"]?\s*\)"""
    r"""|setAttribute\(\s*['"]material['"]\s*,\s*\{[^}]*opacity\s*:\s*0(?:\.0+)?\s*[,}]"""
    r"""|setAttribute\(\s*['"]opacity['"]\s*,\s*['"]?0(?:\.0+)?['"]?\s*\)"""
    r"""|object3D\s*\.\s*visible\s*=\s*false"""
    r"""|material\s*\.\s*opacity\s*=\s*0(?:\.0+)?\s*;""")


_RECV_RE = re.compile(r"([A-Za-z_$][\w$]*(?:\s*\.\s*[A-Za-z_$][\w$]*)*)\s*\.\s*$")


def _receiver(text: str, idx: int) -> str:
    line_start = text.rfind("\n", 0, idx) + 1
    m = _RECV_RE.search(text[line_start:idx])
    return re.sub(r"\s+", "", m.group(1)) if m else ""


def _cursor_receivers(src: JsSource) -> set:
    return {_receiver(src.text, m.start()) for m in DYN_CURSOR_RE.finditer(src.text)} - {""}


def _hidden_receivers(src: JsSource) -> set:
    hidden = {_receiver(src.text, m.start()) for m in HIDE_RE.finditer(src.text)}
    for m in DYN_CURSOR_RE.finditer(src.text):  # raycaster configured with showLine: false
        call = src.text[m.start():m.start() + 200].split(")", 1)[0]
        if re.search(r"showLine\s*:\s*false", call):
            hidden.add(_receiver(src.text, m.start()))
    return hidden - {""}


def rule_js_transparency(src: JsSource) -> Iterable[Finding]:
    cursors = _cursor_receivers(src)
    for m in HIDE_RE.finditer(src.text):
        recv = _receiver(src.text, m.start())
        cursorish = recv in cursors or "cursor" in recv.lower()
        sev = S.HIGH if cursorish else S.LOW
        msg = (f"script hides '{recv}', which is a cursor/controller; a fake cursor can then stand in for the real one."
               if cursorish else
               "script makes an element invisible/transparent at runtime (cannot tell statically whether "
               "it stays clickable).")
        yield _f("P2-js-transparency", sev, src.path, src.line_of(m.start()), msg, src.snippet(m.start()))


DYN_CURSOR_RE = re.compile(
    r"""setAttribute\(\s*['"](?P<c>raycaster|cursor|%s)['"]"""
    r"""|createElement\(\s*['"](?P<p>a-cursor)['"]""" % "|".join(CONTROLLER_COMPONENTS))


def rule_dynamic_cursor(src: JsSource) -> Iterable[Finding]:
    hidden = _hidden_receivers(src)
    for m in DYN_CURSOR_RE.finditer(src.text):
        comp = m.group("c") or m.group("p")
        recv = _receiver(src.text, m.start())
        is_hidden = recv != "" and recv in hidden
        sev = S.HIGH if is_hidden else S.LOW
        yield _f("P6-dynamic-cursor", sev, src.path, src.line_of(m.start()),
                 f"script adds '{comp}' to '{recv or '?'}' at runtime"
                 + (" and also hides that element" if is_hidden else "")
                 + "; added controllers/cursors share the user's input events.", src.snippet(m.start()))


NAV_RE = re.compile(
    r"""window\s*\.\s*open\s*\(|(?:window\s*\.\s*|document\s*\.\s*|\b)location\s*(?:\.\s*href\s*)?=(?!=)"""
    r"""|location\s*\.\s*(?:assign|replace)\s*\(|createElement\(\s*['"](?:iframe|video)['"]\s*\)""")


def rule_aux_screen(src: JsSource) -> Iterable[Finding]:
    xr_blocks = []
    for m, ev, body, b0 in listeners(src, XR_CONTEXT_EVENTS):
        if body:
            xr_blocks.append((b0, b0 + len(body), ev))
    for m in NAV_RE.finditer(src.text):
        ctx = next((ev for a, b, ev in xr_blocks if a <= m.start() < b), None)
        near = src.text[max(0, m.start() - 400):m.start()]
        if ctx or IN_XR_CHECK_RE.search(near):
            yield _f("P8-aux-screen-activity", S.HIGH, src.path, src.line_of(m.start()),
                     f"opens/navigates/injects 2D content while in immersive mode"
                     + (f" (inside a '{ctx}' handler)" if ctx else " (after an in-XR check)")
                     + "; the immersed user does not see the 2D page.", src.snippet(m.start()))
        else:
            yield _f("P8-aux-screen-activity", S.LOW, src.path, src.line_of(m.start()),
                     "opens a window / navigates / creates 2D media; not tied to immersive mode statically.",
                     src.snippet(m.start()))


def rule_mode_listener(src: JsSource) -> Iterable[Finding]:
    for m, ev, body, b0 in listeners(src, XR_CONTEXT_EVENTS):
        yield _f("P9-mode-listener", S.INFO, src.path, src.line_of(m.start()),
                 f"listens for '{ev}' (scene entry/exit detection).", src.snippet(m.start()))


RENDER_ORDER_RE = re.compile(r"""renderOrder\s*=|['"]render-?order['"]|depthTest\s*[:=]\s*false""")


def rule_render_order(src: JsSource) -> Iterable[Finding]:
    for m in RENDER_ORDER_RE.finditer(src.text):
        yield _f("P10-render-order", S.LOW, src.path, src.line_of(m.start()),
                 "script changes render order / depth testing, which decides which overlapping object is seen.",
                 src.snippet(m.start()))


CAPTURE_RE = re.compile(
    r"""components\s*\.\s*screenshot|\.getCanvas\(|\.toDataURL\(|\.toBlob\(|\.readPixels\(|\.captureStream\("""
    r"""|\.capture\(\s*['"](?:perspective|equirectangular)['"]""")
TIMER_RE = re.compile(r"setInterval\(|requestAnimationFrame\(|\btick\s*:\s*function|\btick\s*\(")
SEND_RE = re.compile(r"fetch\(|XMLHttpRequest|sendBeacon\(|WebSocket|\.send\(")


def rule_scene_capture(src: JsSource) -> Iterable[Finding]:
    for m in CAPTURE_RE.finditer(src.text):
        window = src.text[max(0, m.start() - 600):m.start() + 600]
        periodic = bool(TIMER_RE.search(window))
        sends = bool(SEND_RE.search(window))
        sev = S.HIGH if (periodic or sends) else S.MEDIUM
        extra = []
        if periodic:
            extra.append("runs on a timer/render loop")
        if sends:
            extra.append("near a network send")
        yield _f("P13-scene-capture", sev, src.path, src.line_of(m.start()),
                 "script reads back the rendered scene" + (f" ({', '.join(extra)})" if extra else "")
                 + "; this exposes the user's 3D view to page scripts.", src.snippet(m.start()))


SCRIPT_RULES = [rule_synthetic_input, rule_unvalidated_click, rule_js_transparency, rule_dynamic_cursor,
                rule_aux_screen, rule_mode_listener, rule_render_order, rule_scene_capture]


def scene_markup_render_order(page: Page) -> Iterable[Finding]:
    """Render-order / depth tricks declared in markup (material="depthTest: false", render-order)."""
    for e in page.entities:
        mat = parse_props(e.attrs.get("material"))
        if mat.get("depthtest", "").lower() == "false" or "render-order" in e.attrs:
            yield _f("P10-render-order", S.LOW, page.path, e.line,
                     f"{e.label()} disables depth testing / sets render order.", "")


SCENE_RULES.append(scene_markup_render_order)


CAM_READ_RE = re.compile(r"""getWorldDirection\(|\bcam(?:era)?(?:El)?\b[\w$.]*\.(?:object3D\.)?rotation|getAttribute\(\s*['"]rotation['"]\s*\)""")
POS_WRITE_RE = re.compile(r"""(?P<recv>[\w$.]+?)\s*\.\s*(?:object3D\s*\.\s*)?position\s*\.\s*(?:set|copy)\s*\(|(?P<recv2>[\w$.]+?)\s*\.\s*setAttribute\(\s*['"]position['"]""")


def rule_js_follow_view(src: JsSource) -> Iterable[Finding]:
    """BST-style: code reads the camera orientation and repositions another element nearby."""
    for m in POS_WRITE_RE.finditer(src.text):
        window = src.text[max(0, m.start() - 500):m.start()]
        if not CAM_READ_RE.search(window):
            continue
        recv = (m.group("recv") or m.group("recv2") or "")
        if "camera" in recv.lower() or "rig" in recv.lower():
            continue
        adlike = bool(AD_WORD_RE.search(re.sub(r"([a-z])([A-Z])", r"\1 \2", recv)))
        yield _f("P7-blind-spot", S.MEDIUM if adlike else S.LOW, src.path, src.line_of(m.start()),
                 f"script moves '{recv}' based on the camera orientation"
                 + (" and it looks like an ad" if adlike else "")
                 + "; content can be kept in (or out of) the user's blind spot.", src.snippet(m.start()))


SCRIPT_RULES.append(rule_js_follow_view)
