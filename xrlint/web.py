"""Small local web UI for XRLint.

Run `xrlint-web` (or `python3 -m xrlint.web`) and open http://127.0.0.1:8000.
Uses only the standard library. Uploaded files are written to a fresh temporary
folder, scanned there, and deleted; pages may only pull in scripts from that folder.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

from . import __version__
from .analyzer import analyze_paths
from .model import RULES

MAX_BODY_BYTES = 5_000_000
MAX_FILES = 200
SCAN_EXT = (".html", ".htm", ".js", ".mjs")


class ScanError(ValueError):
    """Bad input from the client (reported as HTTP 400)."""


def safe_relpath(name: str) -> str:
    """Turn a client-supplied file name into a safe relative path, or raise ScanError."""
    parts = [p for p in name.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or any(p == ".." or ":" in p for p in parts):
        raise ScanError(f"invalid file name: {name!r}")
    return os.path.join(*parts)


def scan_files(files: list[dict]) -> dict:
    """Scan uploaded files ({"name": ..., "content": ...}) and return a JSON-ready report."""
    if not isinstance(files, list) or not files:
        raise ScanError("no files to scan")
    if len(files) > MAX_FILES:
        raise ScanError(f"too many files (limit {MAX_FILES})")
    tmp = tempfile.mkdtemp(prefix="xrlint-web-")
    try:
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str) \
                    or not isinstance(item.get("content"), str):
                raise ScanError("each file needs a string 'name' and 'content'")
            rel = safe_relpath(item["name"])
            dest = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(item["content"])
        if not any(f["name"].lower().endswith(SCAN_EXT) for f in files):
            raise ScanError("upload at least one .html/.htm or .js file")
        result = analyze_paths([tmp], root=tmp)

        def rel(path: str) -> str:
            return os.path.relpath(path, tmp).replace(os.sep, "/") if path else ""

        return {
            "findings": [dict(f.to_dict(), file=rel(f.file), page=rel(f.page)) for f in result.findings],
            "pages": [{"path": rel(p.path), "is_xr": p.is_xr, "alarm": p.alarm(),
                       "n_findings": len(p.findings)} for p in result.pages],
            "errors": [{"path": rel(p), "error": e} for p, e in result.errors],
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def rules_list() -> list[dict]:
    return [{"id": r.id, "property": r.prop, "title": r.title, "why": r.why, "legit": r.legit}
            for r in RULES.values()]


def _index_html() -> bytes:
    return resources.files("xrlint").joinpath("static/index.html").read_bytes()


class Handler(BaseHTTPRequestHandler):
    server_version = f"xrlint-web/{__version__}"

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                         "script-src 'self' 'unsafe-inline'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, obj) -> None:
        self._send(status, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 - http.server naming
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(HTTPStatus.OK, _index_html(), "text/html; charset=utf-8")
        elif path == "/api/rules":
            self._json(HTTPStatus.OK, {"version": __version__, "rules": rules_list()})
        else:
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/scan":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY_BYTES:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE if length > 0 else HTTPStatus.BAD_REQUEST,
                       {"error": f"request body must be 1 byte to {MAX_BODY_BYTES // 1_000_000} MB"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._json(HTTPStatus.OK, scan_files(payload.get("files") if isinstance(payload, dict) else None))
        except (ScanError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:  # keep the server alive; report the failure
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"scan failed: {exc!r}"})

    def log_message(self, fmt: str, *args) -> None:
        pass  # keep the terminal quiet


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="xrlint-web", description="Run the XRLint web UI.")
    p.add_argument("--host", default="127.0.0.1", help="address to listen on (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)),
                   help="port to listen on (default: $PORT or 8000)")
    args = p.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"XRLint web UI running at http://{args.host}:{args.port}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
