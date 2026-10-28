"""Run all rules over files and folders."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .jsutil import make_source
from .model import Finding, Severity
from .rules import SCENE_RULES, SCRIPT_RULES
from .scene import is_library_script, load_page

HTML_EXT = (".html", ".htm")
JS_EXT = (".js", ".mjs")
SKIP_DIRS = {"node_modules", ".git", "dist", "vendor", "__pycache__"}


@dataclass
class PageResult:
    path: str
    is_xr: bool
    findings: list = field(default_factory=list)

    def max_severity(self) -> Severity | None:
        return max((f.severity for f in self.findings), default=None)

    def alarm(self, threshold: Severity = Severity.MEDIUM) -> bool:
        return any(f.severity >= threshold for f in self.findings)


@dataclass
class ScanResult:
    pages: list = field(default_factory=list)       # list[PageResult] (HTML pages and standalone JS)
    errors: list = field(default_factory=list)      # (path, message)

    @property
    def findings(self) -> list:
        """All findings, each reported once even if a shared JS file is used by many pages."""
        seen, out = set(), []
        for p in self.pages:
            for f in p.findings:
                if f.key() not in seen:
                    seen.add(f.key())
                    out.append(f)
        return out


def analyze_html(path: str, text: str | None = None, seen_js: set | None = None,
                 root: str | None = None) -> PageResult:
    page = load_page(path, text, root=root)
    res = PageResult(path=path, is_xr=page.is_xr)
    out: dict = {}
    for rule in SCENE_RULES:
        for f in rule(page):
            out.setdefault(f.key(), f)
    for src in page.js:
        if seen_js is not None and not src.inline:
            seen_js.add(os.path.abspath(src.path))
        for rule in SCRIPT_RULES:
            for f in rule(src):
                if f.file != path:
                    f.page = path
                out.setdefault(f.key(), f)
    res.findings = sorted(out.values(), key=lambda f: (f.file, f.line, -f.severity, f.rule))
    return res


def analyze_js(path: str) -> PageResult:
    with open(path, encoding="utf-8", errors="replace") as fh:
        src = make_source(path, fh.read(), 1)
    res = PageResult(path=path, is_xr=False)
    out: dict = {}
    for rule in SCRIPT_RULES:
        for f in rule(src):
            out.setdefault(f.key(), f)
    res.findings = sorted(out.values(), key=lambda f: (f.line, -f.severity, f.rule))
    return res


def _walk(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            yield os.path.join(dirpath, name)


def analyze_paths(paths: list[str], include_js: bool = True, max_js_bytes: int = 500_000,
                  root: str | None = None) -> ScanResult:
    """Analyse HTML pages (with their local scripts) and, optionally, standalone JS files.

    A JS file referenced by any scanned page is analysed in that page's context;
    findings in shared JS are reported once (deduplicated by rule/file/line).
    If `root` is given, pages may only pull in local scripts that live inside it.
    """
    result = ScanResult()
    html_files, js_files = [], []
    for p in paths:
        files = [p] if os.path.isfile(p) else list(_walk(p))
        for f in files:
            low = f.lower()
            if low.endswith(HTML_EXT):
                html_files.append(f)
            elif low.endswith(JS_EXT) and include_js and not is_library_script(f.replace(os.sep, "/")):
                js_files.append(f)
    seen_js: set = set()
    for f in html_files:
        try:
            pr = analyze_html(f, seen_js=seen_js, root=root)
        except Exception as exc:  # keep scanning other files
            result.errors.append((f, repr(exc)))
            continue
        result.pages.append(pr)
    for f in js_files:
        if os.path.abspath(f) in seen_js:
            continue
        try:
            if os.path.getsize(f) > max_js_bytes:
                continue
            pr = analyze_js(f)
        except Exception as exc:
            result.errors.append((f, repr(exc)))
            continue
        result.pages.append(pr)
    return result
