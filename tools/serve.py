"""Pratinjau lokal hasil build, mirip perilaku Cloudflare Pages.

Bedanya dengan `python -m http.server --directory dist`:
- rute yang tidak ada mengembalikan dist/404.html (bukan halaman 404 bawaan Python),
- .webp dikirim dengan content-type yang benar,
- tidak ada cache, jadi hasil build terbaru selalu terlihat (cukup refresh biasa).

Pakai: python tools/serve.py [port]     -> http://localhost:8098
"""

import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8098


class Pratinjau(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        jalur = self.translate_path(self.path)
        if not os.path.exists(jalur):
            return self.halaman_404()
        return super().send_head()

    def halaman_404(self):
        berkas = os.path.join(ROOT, "404.html")
        if not os.path.exists(berkas):
            return super().send_head()
        with open(berkas, "rb") as f:
            isi = f.read()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(isi)))
        self.end_headers()
        return BytesIO(isi)


if __name__ == "__main__":
    if not os.path.isdir(ROOT):
        sys.exit("dist/ belum ada. Jalankan: python build.py")
    print("Pratinjau dist/ di http://localhost:%d" % PORT)
    ThreadingHTTPServer(("127.0.0.1", PORT), Pratinjau).serve_forever()
