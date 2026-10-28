import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from xrlint.web import Handler, ScanError, safe_relpath, scan_files

FIX = os.path.join(os.path.dirname(__file__), "fixtures")

PAGE_WITH_SCRIPT = """<!DOCTYPE html>
<html><body>
  <a-scene>
    <a-entity camera look-controls position="0 1.6 0"></a-entity>
    <a-box id="sponsor" position="2 1 -4"></a-box>
  </a-scene>
  <script src="{src}"></script>
</body></html>
"""
SYNTHETIC_CLICK_JS = "setInterval(function () { document.querySelector('#sponsor').emit('click'); }, 10000);\n"


def read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


class ScanFilesTest(unittest.TestCase):
    def test_pasted_page_is_scanned_with_relative_paths(self):
        report = scan_files([{"name": "page.html", "content": read("unit/p12_occluded_risky.html")}])
        rules = {(f["rule"], f["file"], f["line"]) for f in report["findings"]}
        self.assertIn(("P12-occluded-interactive", "page.html", 13), rules)
        self.assertEqual(report["pages"][0]["path"], "page.html")
        self.assertTrue(report["pages"][0]["alarm"])

    def test_uploaded_local_script_is_followed(self):
        report = scan_files([
            {"name": "site/index.html", "content": PAGE_WITH_SCRIPT.format(src="js/app.js")},
            {"name": "site/js/app.js", "content": SYNTHETIC_CLICK_JS},
        ])
        hits = [f for f in report["findings"] if f["rule"] == "P3-synthetic-input"]
        self.assertEqual([f["file"] for f in hits], ["site/js/app.js"])
        self.assertEqual(hits[0]["page"], "site/index.html")

    def test_scripts_outside_the_upload_are_not_read(self):
        with tempfile.TemporaryDirectory() as outside:
            secret = os.path.join(outside, "outside.js")
            with open(secret, "w", encoding="utf-8") as fh:
                fh.write(SYNTHETIC_CLICK_JS)
            for src in (secret, "../" * 12 + secret.lstrip("/")):
                report = scan_files([{"name": "page.html", "content": PAGE_WITH_SCRIPT.format(src=src)}])
                self.assertFalse([f for f in report["findings"] if f["rule"] == "P3-synthetic-input"], src)

    def test_bad_input_is_rejected(self):
        for name in ("../x.html", "a/../../x.html", "", "/", "C:x.html"):
            with self.assertRaises(ScanError, msg=name):
                safe_relpath(name)
        self.assertEqual(safe_relpath("/site\\js/./app.js"), os.path.join("site", "js", "app.js"))
        for files in ([], None, [{"name": "a.html"}], [{"name": "notes.txt", "content": "hi"}]):
            with self.assertRaises(ScanError, msg=repr(files)):
                scan_files(files)


class WebServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, path, body=None):
        req = urllib.request.Request(self.base + path, data=body, method="POST" if body is not None else "GET",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                return res.status, res.headers.get("Content-Type"), res.read()
        except urllib.error.HTTPError as err:
            return err.code, err.headers.get("Content-Type"), err.read()

    def test_index_and_rules(self):
        status, ctype, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertTrue(ctype.startswith("text/html"))
        self.assertIn(b"XRLint", body)
        status, _, body = self.request("/api/rules")
        self.assertEqual(status, 200)
        self.assertIn("P12-occluded-interactive", {r["id"] for r in json.loads(body)["rules"]})

    def test_scan_endpoint(self):
        payload = {"files": [{"name": "p.html", "content": read("unit/p12_occluded_risky.html")}]}
        status, _, body = self.request("/api/scan", json.dumps(payload).encode())
        self.assertEqual(status, 200)
        self.assertIn("P12-occluded-interactive", {f["rule"] for f in json.loads(body)["findings"]})

    def test_scan_endpoint_errors(self):
        status, _, body = self.request("/api/scan", b"not json")
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(body))
        status, _, _ = self.request("/api/scan", json.dumps({"files": [{"name": "../a.html", "content": ""}]}).encode())
        self.assertEqual(status, 400)
        status, _, _ = self.request("/nope")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
