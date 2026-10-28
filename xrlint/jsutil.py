"""Small, dependency-free helpers for scanning JavaScript text.

This is deliberately NOT a JavaScript parser. It strips comments, finds
patterns with regular expressions and matches braces to approximate
function bodies. That keeps the tool simple and fast, at the cost of
missing obfuscated or dynamically built code (see README limitations).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class JsSource:
    path: str          # file the code lives in (HTML page for inline scripts)
    text: str          # comment-stripped code, same length/newlines as original
    line_offset: int   # line number of the first character of `text`
    inline: bool = False

    def line_of(self, index: int) -> int:
        return self.line_offset + self.text.count("\n", 0, index)

    def snippet(self, index: int, width: int = 90) -> str:
        start = self.text.rfind("\n", 0, index) + 1
        end = self.text.find("\n", index)
        if end == -1:
            end = len(self.text)
        line = self.text[start:end].strip()
        return line[:width]


def strip_comments(code: str) -> str:
    """Replace // and /* */ comments with spaces, keeping newlines.

    String literals ('', "", ``) are respected so that "http://x" is not
    treated as a comment. Regex literals are not recognised (rarely matters).
    """
    out = []
    i, n = 0, len(code)
    quote = None
    while i < n:
        c = code[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(code[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and code[i + 1] == "/":
            j = code.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
            continue
        if c == "/" and i + 1 < n and code[i + 1] == "*":
            j = code.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in code[i:j]))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def make_source(path: str, raw: str, line_offset: int = 1, inline: bool = False) -> JsSource:
    return JsSource(path=path, text=strip_comments(raw), line_offset=line_offset, inline=inline)


def block_after(text: str, start: int, limit: int = 20000) -> tuple[int, int]:
    """Return (begin, end) of the first {...} block at or after `start`.

    Naive brace counting; braces inside strings can confuse it.
    Returns (start, start) if no block is found within `limit` characters.
    """
    i = text.find("{", start, start + limit)
    if i == -1:
        return start, start
    depth = 0
    for j in range(i, min(len(text), i + limit)):
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i, j + 1
    return i, min(len(text), i + limit)


EVENT_LISTENER_RE = re.compile(
    r"""(?P<recv>[\w$.\[\]'"()#-]*?)\s*\.\s*addEventListener\s*\(\s*['"](?P<event>[\w:-]+)['"]""")

COMPONENT_RE = re.compile(r"""AFRAME\s*\.\s*registerComponent\s*\(\s*['"](?P<name>[\w-]+)['"]""")


def listeners(src: JsSource, events: set[str] | None = None):
    """Yield (match, event_name, body_text, body_start) for addEventListener calls."""
    for m in EVENT_LISTENER_RE.finditer(src.text):
        ev = m.group("event")
        if events is not None and ev not in events:
            continue
        body, b0 = handler_body(src.text, m.end())
        yield m, ev, body, b0


_NAMED_HANDLER_RE = re.compile(r"\s*,\s*(?:this\s*\.\s*)?([A-Za-z_$][\w$]*)\s*(?:\.bind\([^)]*\))?\s*[,)]")


def handler_body(text: str, pos: int) -> tuple[str, int]:
    """Best-effort body of the handler passed as 2nd argument at `pos`.

    Handles inline `function (...) {}` / arrow functions, and named
    references (`onClick`, `this.onClick.bind(this)`) defined in the same
    source as `function onClick(` or `onClick: function (` / `onClick (...) {`.
    """
    brace = text.find("{", pos, pos + 400)
    paren = text.find(")", pos, pos + 400)
    head = text[pos:brace] if brace != -1 else ""
    if brace != -1 and (paren == -1 or brace < paren or "=>" in head or "function" in head):
        if "function" in head or "=>" in head:
            b0, b1 = block_after(text, pos, limit=4000)
            return text[b0:b1], b0
    m = _NAMED_HANDLER_RE.match(text, pos)
    if m:
        name = re.escape(m.group(1))
        d = re.search(rf"(?:function\s+{name}\s*\(|\b{name}\s*:\s*function\b|\b{name}\s*=\s*function\b"
                      rf"|\b{name}\s*=\s*\([^)]*\)\s*=>|^\s*{name}\s*\([^)]*\)\s*\{{)", text, re.M)
        if d:
            b0, b1 = block_after(text, d.end() - 1 if text[d.end() - 1] == "{" else d.end(), limit=4000)
            return text[b0:b1], b0
    return "", pos


def registered_components(src: JsSource):
    """Yield (name, body, start_index) for AFRAME.registerComponent calls."""
    for m in COMPONENT_RE.finditer(src.text):
        b0, b1 = block_after(src.text, m.end(), limit=60000)
        yield m.group("name"), src.text[b0:b1], m.start()
