"""Build a simplified static model of an A-Frame page.

The model answers the questions the rules need:
  * which entities exist, where they are (approx. world position) and how big;
  * how transparent / visible they are;
  * whether a ray (cursor / controller) exists and which entities it can hit;
  * which entities have click handlers;
  * where the camera is and which way it faces (yaw only).

Approximations (documented in the README):
  * parent rotation and scale are ignored when computing world positions
    (entities under a rotated/scaled parent are marked `approx=True`);
  * only yaw (rotation about Y) of the camera is used;
  * glTF models and text have unknown size;
  * entities created by JavaScript at runtime are invisible to this model.
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from .jsutil import JsSource, make_source, listeners, registered_components

CLICK_EVENTS = {"click", "fusing", "mousedown", "mouseup", "triggerdown", "triggerup", "selectstart", "select"}
SURROUND_TAGS = {"a-sky", "a-videosphere"}
NON_ENTITY_TAGS = {"a-scene", "a-assets", "a-asset-item", "a-mixin"}
LIBRARY_RE = re.compile(r"(^|/)(aframe[\w.-]*|three[\w.-]*|[\w.-]+\.min)\.js$", re.I)
CONTROLLER_COMPONENTS = ("laser-controls", "oculus-touch-controls", "meta-touch-controls", "vive-controls",
                         "windows-motion-controls", "hand-controls", "generic-tracked-controller-controls",
                         "hand-tracking-controls", "tracked-controls", "oculus-go-controls", "daydream-controls")


def parse_props(value: str | None) -> dict[str, str]:
    """Parse an A-Frame multi-property string 'a: 1; b: two' into a dict."""
    out: dict[str, str] = {}
    if not value:
        return out
    for part in value.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def parse_vec3(value: str | None, default=(0.0, 0.0, 0.0)) -> tuple[float, float, float]:
    if not value:
        return default
    if ":" in value:  # object form 'x: 1; y: 2; z: 3'
        p = parse_props(value)
        try:
            return (float(p.get("x", 0)), float(p.get("y", 0)), float(p.get("z", 0)))
        except ValueError:
            return default
    nums = re.split(r"[\s,]+", value.strip())
    try:
        vals = [float(x) for x in nums if x]
    except ValueError:
        return default
    while len(vals) < 3:
        vals.append(0.0)
    return (vals[0], vals[1], vals[2])


def _float(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _is_false(v) -> bool:
    return v is not None and str(v).strip().lower() == "false"


@dataclass
class Entity:
    tag: Tag
    name: str
    line: int
    attrs: dict
    pos: tuple
    approx: bool
    size: tuple | None          # axis-aligned (w, h, d) in metres, None if unknown
    opacity: float
    visible: bool
    surround: bool
    parent: "Entity | None" = None
    hit: bool = False           # a ray can hit it
    explicit_target: bool = False  # matched by a raycaster `objects` selector
    handler: bool = False       # has a click-like handler
    handler_reason: str = ""
    hud: bool = False           # camera, cursor/controller, or attached to them (moves with the user)

    @property
    def interactive(self) -> bool:
        return self.hit and (self.explicit_target or self.handler)

    def label(self) -> str:
        ident = self.attrs.get("id")
        cls = self.attrs.get("class")
        if ident:
            return f"<{self.name} id='{ident}'>"
        if cls:
            return f"<{self.name} class='{cls}'>"
        return f"<{self.name}> (line {self.line})"

    def is_ancestor_of(self, other: "Entity") -> bool:
        p = other.parent
        while p is not None:
            if p is self:
                return True
            p = p.parent
        return False


@dataclass
class Camera:
    pos: tuple = (0.0, 1.6, 0.0)
    yaw_deg: float = 0.0
    line: int = 0
    explicit: bool = False

    def forward(self) -> tuple:
        y = math.radians(self.yaw_deg)
        return (-math.sin(y), 0.0, -math.cos(y))

    def right(self) -> tuple:
        y = math.radians(self.yaw_deg)
        return (math.cos(y), 0.0, -math.sin(y))


@dataclass
class Page:
    path: str
    soup: BeautifulSoup
    is_xr: bool
    entities: list = field(default_factory=list)
    camera: Camera = field(default_factory=Camera)
    ray_present: bool = False
    intersect_all: bool = False
    ray_selectors: list = field(default_factory=list)
    js: list = field(default_factory=list)            # list[JsSource]
    remote_scripts: list = field(default_factory=list)  # (line, url)
    gaze_fuse: list = field(default_factory=list)       # Tags with fuse cursor
    controller_rays: list = field(default_factory=list)  # Tags with controller rays


# ---------------------------------------------------------------- geometry

def _primitive_of(e_tag: str, attrs: dict) -> tuple[str | None, dict]:
    geo = parse_props(attrs.get("geometry"))
    prim = geo.get("primitive")
    if e_tag.startswith("a-") and e_tag not in ("a-entity", "a-camera", "a-cursor", "a-text", "a-gltf-model",
                                                  "a-obj-model", "a-sound", "a-light"):
        prim = prim or e_tag[2:]
        # primitive attribute form: <a-box width="2">
        for k in ("width", "height", "depth", "radius", "radius-outer", "radius-top", "radius-bottom"):
            if k in attrs:
                geo.setdefault(k.replace("radius-outer", "radiusouter"), attrs[k])
    return prim, geo


def _size(prim: str | None, geo: dict) -> tuple | None:
    if prim is None:
        return None
    g = lambda k, d: _float(geo.get(k), d)  # noqa: E731
    if prim == "box":
        return (g("width", 1), g("height", 1), g("depth", 1))
    if prim in ("plane", "image", "video"):
        return (g("width", 1), g("height", 1), 0.0)
    if prim == "circle":
        r = g("radius", 1)
        return (2 * r, 2 * r, 0.0)
    if prim == "ring":
        r = _float(geo.get("radiusouter", geo.get("radius-outer")), 1)
        return (2 * r, 2 * r, 0.0)
    if prim in ("sphere", "dodecahedron", "icosahedron", "octahedron", "tetrahedron"):
        r = g("radius", 1)
        return (2 * r, 2 * r, 2 * r)
    if prim in ("cylinder", "cone"):
        r = g("radius", g("radius-bottom", 1))
        return (2 * r, g("height", 1), 2 * r)
    if prim == "torus":
        r = g("radius", 1)
        return (2 * r, 2 * r, 0.4)
    return None


def _merged_attrs(tag: Tag, mixins: dict) -> dict:
    attrs: dict = {}
    for mid in (tag.get("mixin") or "").split():
        m = mixins.get(mid)
        if m is None:
            continue
        for k, v in m.items():
            if k in ("material", "geometry") and k in attrs:
                merged = parse_props(attrs[k])
                merged.update(parse_props(v))
                attrs[k] = "; ".join(f"{a}: {b}" for a, b in merged.items())
            else:
                attrs[k] = v
    for k, v in tag.attrs.items():
        v = " ".join(v) if isinstance(v, list) else v
        if k in ("material", "geometry") and k in attrs:
            merged = parse_props(attrs[k])
            merged.update(parse_props(v))
            attrs[k] = "; ".join(f"{a}: {b}" for a, b in merged.items())
        else:
            attrs[k] = v
    return attrs


def _opacity(attrs: dict) -> float:
    mat = parse_props(attrs.get("material"))
    if "opacity" in mat:
        return _float(mat["opacity"], 1.0)
    if "opacity" in attrs:
        return _float(attrs["opacity"], 1.0)
    return 1.0


def _visible(attrs: dict) -> bool:
    if _is_false(attrs.get("visible")):
        return False
    mat = parse_props(attrs.get("material"))
    return not _is_false(mat.get("visible"))


# ---------------------------------------------------------------- building

def is_library_script(src: str) -> bool:
    return bool(LIBRARY_RE.search(src)) or "/dist/" in src or "node_modules" in src


def _inside(path: str, root: str) -> bool:
    real_root = os.path.realpath(root)
    return os.path.commonpath([os.path.realpath(path), real_root]) == real_root


def load_page(path: str, text: str | None = None, max_js_bytes: int = 500_000,
              root: str | None = None) -> Page:
    """Parse a page. If `root` is given, local <script src> files outside it are not read."""
    if text is None:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    soup = BeautifulSoup(text, "html.parser")
    scene = soup.find("a-scene")
    page = Page(path=path, soup=soup, is_xr=scene is not None)

    # ---- scripts
    base = os.path.dirname(path)
    for s in soup.find_all("script"):
        src = s.get("src")
        stype = (s.get("type") or "").lower()
        if stype and "javascript" not in stype and stype != "module":
            continue
        if src:
            parsed = urlparse(src)
            if parsed.scheme in ("http", "https") or src.startswith("//"):
                page.remote_scripts.append((s.sourceline or 1, src))
                continue
            if is_library_script(src):
                continue
            local = os.path.normpath(os.path.join(base, parsed.path))
            if root is not None and not _inside(local, root):
                continue
            if os.path.isfile(local) and os.path.getsize(local) <= max_js_bytes:
                with open(local, encoding="utf-8", errors="replace") as fh:
                    page.js.append(make_source(local, fh.read(), 1))
        else:
            code = s.string or ""
            if code.strip():
                page.js.append(make_source(path, code, s.sourceline or 1, inline=True))

    if scene is None:
        return page

    # ---- mixins
    mixins = {}
    for m in soup.find_all("a-mixin"):
        if m.get("id"):
            mixins[m["id"]] = {k: (" ".join(v) if isinstance(v, list) else v) for k, v in m.attrs.items() if k != "id"}

    # ---- entities
    tag_to_entity: dict[int, Entity] = {}
    for tag in scene.find_all(True):
        name = tag.name.lower()
        if not name.startswith("a-") or name in NON_ENTITY_TAGS:
            continue
        if tag.find_parent("a-assets") is not None:
            continue
        attrs = _merged_attrs(tag, mixins)
        parent = None
        for anc in tag.parents:
            if id(anc) in tag_to_entity:
                parent = tag_to_entity[id(anc)]
                break
        local = parse_vec3(attrs.get("position"))
        approx = False
        if parent is not None:
            pp = parent.pos
            pos = (pp[0] + local[0], pp[1] + local[1], pp[2] + local[2])
            if parent.approx or ("rotation" in parent.attrs and parse_vec3(parent.attrs["rotation"]) != (0, 0, 0)) \
                    or ("scale" in parent.attrs and parse_vec3(parent.attrs["scale"], (1, 1, 1)) != (1, 1, 1)):
                approx = True
        else:
            pos = local
        prim, geo = _primitive_of(name, attrs)
        size = _size(prim, geo)
        scale = parse_vec3(attrs.get("scale"), (1.0, 1.0, 1.0))
        if size is not None:
            size = (size[0] * abs(scale[0]), size[1] * abs(scale[1]), size[2] * abs(scale[2]))
        e = Entity(tag=tag, name=name, line=tag.sourceline or 1, attrs=attrs, pos=pos, approx=approx,
                   size=size, opacity=_opacity(attrs), visible=_visible(attrs),
                   surround=name in SURROUND_TAGS or (prim == "sphere" and size is not None and size[0] >= 50),
                   parent=parent)
        if parent is not None and not parent.visible:
            e.visible = False
        tag_to_entity[id(tag)] = e
        page.entities.append(e)

    _mark_hud(page)
    _find_camera(page)
    _find_rays(page, scene)
    _find_handlers(page, scene)
    return page


def _mark_hud(page: Page) -> None:
    """Camera, cursors, controllers and everything attached to them move with the user."""
    for e in page.entities:
        own = e.name in ("a-camera", "a-cursor") or any(
            k in e.attrs for k in ("camera", "cursor", "raycaster") + CONTROLLER_COMPONENTS)
        e.hud = own or (e.parent is not None and e.parent.hud)


def _find_camera(page: Page) -> None:
    for e in page.entities:
        if e.name == "a-camera" or "camera" in e.attrs:
            explicit_pos = "position" in e.attrs
            pos = e.pos if explicit_pos else (e.pos[0], e.pos[1] + 1.6, e.pos[2])
            yaw = parse_vec3(e.attrs.get("rotation"))[1]
            p = e.parent
            while p is not None:
                yaw += parse_vec3(p.attrs.get("rotation"))[1]
                p = p.parent
            page.camera = Camera(pos=pos, yaw_deg=yaw, line=e.line, explicit=True)
            return


def _find_rays(page: Page, scene: Tag) -> None:
    holders = [scene] + [e.tag for e in page.entities]
    for tag in holders:
        attrs = {k: (" ".join(v) if isinstance(v, list) else v) for k, v in tag.attrs.items()}
        has_ray = any(k in attrs for k in ("raycaster", "cursor")) or tag.name == "a-cursor" \
            or "laser-controls" in attrs
        if not has_ray:
            continue
        page.ray_present = True
        objs = parse_props(attrs.get("raycaster")).get("objects")
        if objs:
            page.ray_selectors.append(objs)
        else:
            page.intersect_all = True
        cur = parse_props(attrs.get("cursor"))
        if (cur.get("fuse", "").lower() == "true") or (tag.name == "a-cursor" and cur.get("fuse", "").lower() == "true"):
            page.gaze_fuse.append(tag)
        if tag.name == "a-cursor" and str(tag.get("fuse", "")).lower() == "true":
            page.gaze_fuse.append(tag)
        if any(c in attrs for c in CONTROLLER_COMPONENTS):
            page.controller_rays.append(tag)

    # raycasters configured from JS: setAttribute('raycaster', 'objects: .x') / {objects: '.x'}
    for src in page.js:
        for m in re.finditer(r"""setAttribute\(\s*['"](raycaster|cursor)['"]\s*,\s*(['"][^'"]*['"]|\{[^}]*\})""",
                             src.text):
            page.ray_present = True
            sel = re.search(r"""objects['"]?\s*:\s*['"]?([^;'"}]+)""", m.group(2))
            if sel:
                page.ray_selectors.append(sel.group(1).strip())
            else:
                page.intersect_all = True

    for sel in page.ray_selectors:
        try:
            matched = {id(t) for t in scene.select(sel)}
        except Exception:  # unsupported selector: fall back to "everything"
            page.intersect_all = True
            continue
        for e in page.entities:
            if id(e.tag) in matched:
                e.explicit_target = True
    for e in page.entities:
        # A-Frame raycasts against meshes; an entity whose ancestor is a target is hit too.
        anc = e.parent
        while anc is not None and not e.explicit_target:
            if anc.explicit_target:
                e.explicit_target = True
            anc = anc.parent
        e.hit = page.ray_present and (page.intersect_all or e.explicit_target)
        if e.name in ("a-camera", "a-cursor", "a-light", "a-sound") or "camera" in e.attrs or "light" in e.attrs:
            e.hit = False


_SELECTOR_ASSIGN = r"""(?:querySelector(?:All)?\(\s*['"](?P<sel>[^'"]+)['"]\s*\)|getElementById\(\s*['"](?P<id>[^'"]+)['"]\s*\))"""


def _find_handlers(page: Page, scene: Tag) -> None:
    # 1) markup handlers
    for e in page.entities:
        for k in e.attrs:
            kl = k.lower()
            if kl in ("onclick", "link", "href") or (kl.startswith("event-set__") and "click" in kl) \
                    or (kl.startswith("on") and "click" in kl):
                e.handler, e.handler_reason = True, f"attribute '{k}'"
                break

    # 2) components registered in JS that listen for click-like events
    click_components = set()
    for src in page.js:
        for name, body, _ in registered_components(src):
            if re.search(r"""addEventListener\(\s*['"](%s)['"]""" % "|".join(CLICK_EVENTS), body) or \
                    re.search(r"""events\s*:\s*\{[^}]*\b(click|fusing)\b""", body, re.S):
                click_components.add(name.lower())
    if click_components:
        for e in page.entities:
            for k in e.attrs:
                if k.lower() in click_components:
                    e.handler, e.handler_reason = True, f"component '{k}' handles clicks"
                    break

    # 3) selectors used with addEventListener('click', ...) in page JS
    selectors: list[str] = []
    for src in page.js:
        for m, ev, _body, _b0 in listeners(src, CLICK_EVENTS):
            recv = m.group("recv")
            sm = re.search(_SELECTOR_ASSIGN, recv)
            if sm:
                selectors.append(sm.group("sel") or "#" + sm.group("id"))
                continue
            ident = recv.split(".")[-1].strip()
            if not re.fullmatch(r"[A-Za-z_$][\w$]*", ident or ""):
                continue
            # var btn = document.querySelector('#x')
            am = re.search(rf"\b{re.escape(ident)}\s*=\s*[^;\n]*?{_SELECTOR_ASSIGN}", src.text)
            if am:
                selectors.append(am.group("sel") or "#" + am.group("id"))
                continue
            # querySelectorAll('.x').forEach(function (el) { el.addEventListener('click'
            back = src.text[max(0, m.start() - 300):m.start()]
            fm = list(re.finditer(r"""querySelectorAll\(\s*['"]([^'"]+)['"]\s*\)\s*\.forEach""", back))
            if fm:
                selectors.append(fm[-1].group(1))
    for sel in selectors:
        try:
            matched = {id(t) for t in scene.select(sel)}
        except Exception:
            continue
        for e in page.entities:
            if id(e.tag) in matched:
                e.handler, e.handler_reason = True, f"script listens via '{sel}'"
