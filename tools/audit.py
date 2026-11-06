"""Pemeriksaan cepat hasil build: tautan, judul, alt, em dash, dan ukuran.

Jalankan setelah build: python tools/audit.py
"""

import os
import re
import sys
from collections import Counter

DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")

masalah = []
halaman = []
for akar, _dirs, berkas in os.walk(DIST):
    for b in berkas:
        if b.endswith(".html"):
            halaman.append(os.path.join(akar, b))

def rel(p):
    return os.path.relpath(p, DIST).replace("\\", "/")

for p in sorted(halaman):
    html = open(p, encoding="utf-8").read()
    nama = rel(p)
    h1 = len(re.findall(r"<h1[ >]", html))
    if h1 != 1:
        masalah.append("%s: jumlah h1 = %d" % (nama, h1))
    if "lang=\"id\"" not in html:
        masalah.append("%s: tidak ada lang=id" % nama)
    if "<title>" not in html or re.search(r"<title>\s*</title>", html):
        masalah.append("%s: title kosong" % nama)
    if 'name="description"' not in html:
        masalah.append("%s: meta description kosong" % nama)
    if "\u2014" in html:
        masalah.append("%s: ada em dash" % nama)
    # tautan internal harus ada berkasnya
    for href in re.findall(r'href="(/[^"#?]*)"', html):
        target = os.path.join(DIST, href.lstrip("/"))
        if href.endswith("/"):
            target = os.path.join(target, "index.html")
        if not os.path.exists(target):
            masalah.append("%s: tautan mati %s" % (nama, href))
    # gambar tanpa alt atau tanpa ukuran
    for tag in re.findall(r"<img [^>]*>", html):
        if 'alt="' not in tag:
            masalah.append("%s: img tanpa alt" % nama)
        if "width=" not in tag or "height=" not in tag:
            masalah.append("%s: img tanpa width/height" % nama)
        src = re.search(r'src="(/[^"]+)"', tag)
        if src:
            f = os.path.join(DIST, src.group(1).lstrip("/"))
            if not os.path.exists(f):
                masalah.append("%s: gambar hilang %s" % (nama, src.group(1)))
    # aset css/js
    for aset in re.findall(r'(?:href|src)="(/assets/[^"]+)"', html):
        if not os.path.exists(os.path.join(DIST, aset.lstrip("/"))):
            masalah.append("%s: aset hilang %s" % (nama, aset))

ukuran = Counter()
for akar, _dirs, berkas in os.walk(DIST):
    for b in berkas:
        ext = os.path.splitext(b)[1].lower()
        ukuran[ext] += os.path.getsize(os.path.join(akar, b))

print("halaman diperiksa:", len(halaman))
for ext, total in ukuran.most_common():
    print("  %-6s %7.1f KB" % (ext, total / 1024))
print("masalah:", len(masalah))
for m in masalah:
    print("  -", m)
sys.exit(1 if masalah else 0)
