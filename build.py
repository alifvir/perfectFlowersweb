"""Build situs statis Perfect Flowers.

Sumber data:
  data/site.json   identitas toko, nomor WA, rekening, alamat
  assets-src/g*.jpeg  grid pricelist asli toko (foto buket + harga)
  assets-src/photos-35k.jpeg, assets-src/qris.jpeg, assets-src/patokan-maps.jpeg

Hasil: dist/ siap diunggah ke Cloudflare Pages.

Jalankan: python build.py
"""

import hashlib
import json
import os
import re
import shutil
from html import escape

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets-src")
DIST = os.path.join(ROOT, "dist")
IMG = os.path.join(DIST, "assets", "img")

# Harga per sel, urut baris demi baris. Dibaca ulang dari label di tiap foto.
GRIDS = {
    "g1": (3, 3, [65000, 350000, 160000, 235000, 235000, 35000, 235000, 50000, 130000]),
    "g2": (3, 3, [130000, 275000, 60000, 235000, 150000, 250000, 170000, 700000, 150000]),
    "g3": (3, 3, [110000, 250000, 160000, 150000, 225000, 130000, 65000, 235000, 215000]),
    "g4": (2, 3, [255000, 225000, 200000, 195000, 235000, 550000]),
    "g5": (3, 3, [70000, 250000, 35000, 35000, 70000, 35000, 35000, 50000, 60000]),
    "g6": (3, 3, [215000, 150000, 230000, 100000, 170000, 215000, 235000, 60000, 150000]),
}

# Bingkai potong seragam untuk semua foto produk: 4:5, ukuran buket disamakan,
# dasar potongan tepat di atas kotak label harga. Dulu tiap grid punya tinggi
# potong sendiri (POTONG), hasilnya posisi buket naik-turun tidak seragam.
RASIO_POTONG = 0.80    # lebar : tinggi

# Sel yang label harganya tidak terdeteksi otomatis (label hitam besar).
# Nilai = rasio tinggi sel tempat potongan harus berhenti.
BATAS_SEL = {"g4-5": 0.72, "g4-6": 0.72}

# Lembar katalog foto: semua kotak dibuat rasio sama (lebar:tinggi = 0.66)
# supaya grid 2 kolom tidak menyisakan ruang kosong di bawah lembar terpendek.
LEBAR_LEMBAR = 1080
RASIO_LEMBAR = 0.66

# Harga yang diturunkan dari situs (foto contohnya salah / belum layak tayang).
SEMBUNYI = {65000}

PILIHAN_BERANDA = [35000, 50000, 65000, 110000, 150000, 170000, 235000, 350000]

# Lembar katalog foto (catalog/). Tiap lembar adalah kolase buket dengan label
# harga yang sudah menempel di fotonya. Dipakai sebagai halaman tambahan
# /katalog/foto/, bukan untuk memotong ulang foto produk yang sudah ada.
LEMBAR = [
    {"berkas": "catalog.jpeg", "kolom": 2, "baris": 3,
     "harga": [255000, 225000, 200000, 195000, 235000, 550000]},
    {"berkas": "catalog (2).jpeg", "kolom": 3, "baris": 3,
     "harga": [65000, 350000, 160000, 235000, 235000, 35000, 235000, 50000, 130000]},
    {"berkas": "catalog (3).jpeg", "kolom": 3, "baris": 3,
     "harga": [130000, 275000, 60000, 235000, 150000, 250000, 170000, 700000, 150000]},
    {"berkas": "catalog (4).jpeg", "kolom": 3, "baris": 3,
     "harga": [110000, 250000, 160000, 150000, 215000, 130000, 65000, 235000, 215000]},
    {"berkas": "catalog (5).jpeg", "kolom": 3, "baris": 3,
     "harga": [215000, 150000, 250000, 100000, 170000, 215000, 235000, 60000, 150000]},
    {"berkas": "catalog (6).jpeg", "kolom": 2, "baris": 3,
     "harga": [350000, 300000, 200000, 215000, 300000, 175000]},
    {"berkas": "catalog (7).jpeg", "kolom": 2, "baris": 3,
     "harga": [315000, 320000, 875000, 400000, 255000, 215000]},
    {"berkas": "catalog (8).jpeg", "kolom": 3, "baris": 3,
     "harga": [70000, 250000, 35000, 40000, 70000, 35000, 35000, 50000, 60000]},
]
KATALOG = os.path.join(ROOT, "catalog")

# Foto satuan: foto buket per harga, nama berkasnya = harga ('175k (2).jpeg').
# Tidak ada label harga di dalam foto, jadi dipotong apa adanya ke 4:5.
SATUAN = os.path.join(KATALOG, "satuan")

SITE = json.load(open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8"))

_versi = {}


def versi_aset(relatif):
    """Potongan hash isi berkas, dipakai sebagai ?v= supaya CSS/JS tidak tersangkut cache lama."""
    if relatif not in _versi:
        with open(os.path.join(ROOT, relatif), "rb") as f:
            _versi[relatif] = hashlib.sha1(f.read()).hexdigest()[:8]
    return _versi[relatif]


def rupiah(n):
    return "Rp " + format(n, ",d").replace(",", ".")


def slug(n):
    return "buket-%dk" % (n // 1000)


def tulis(path, isi):
    tujuan = os.path.join(DIST, path)
    os.makedirs(os.path.dirname(tujuan) or DIST, exist_ok=True)
    with open(tujuan, "w", encoding="utf-8", newline="\n") as f:
        f.write(isi)


# ---------------------------------------------------------------- gambar

def _jumlah_kotak(a, r):
    """Jumlah nilai pada jendela (2r+1) persegi untuk tiap piksel, lewat integral image."""
    h, w = a.shape
    p = np.pad(a, r, mode="edge")
    ii = np.zeros((p.shape[0] + 1, p.shape[1] + 1), dtype=np.float64)
    ii[1:, 1:] = np.cumsum(np.cumsum(p, axis=0), axis=1)
    k = 2 * r + 1
    y0 = np.arange(h)[:, None]
    x0 = np.arange(w)[None, :]
    return ii[y0 + k, x0 + k] - ii[y0, x0 + k] - ii[y0 + k, x0] + ii[y0, x0]


def _kanal(cell):
    a = np.asarray(cell.convert("RGB")).astype(np.float32)
    gray = a[:, :, 0] * 0.299 + a[:, :, 1] * 0.587 + a[:, :, 2] * 0.114
    r = 4
    n = (2 * r + 1) ** 2
    rata = _jumlah_kotak(gray, r) / n
    std = np.sqrt(np.maximum(_jumlah_kotak(gray * gray, r) / n - rata * rata, 0))
    return a, gray, std


def _deteksi_label(cell, skala=5):
    """Cari kotak label harga di bagian bawah sel.

    Sel diperkecil dulu (rata-rata blok) supaya angka di dalam label tidak
    memotong-motong area putih/hitamnya. Kembalikan rasio y (0..1) atau None.
    """
    h, w = cell.height, cell.width
    mulai = int(h * 0.45)
    kecil = np.asarray(
        cell.crop((0, mulai, w, h)).resize((max(8, w // skala), max(8, (h - mulai) // skala)), Image.BOX)
    ).astype(np.int16)
    mn = kecil.min(axis=2)
    mx = kecil.max(axis=2)
    cw, ch = mn.shape[1], mn.shape[0]
    calon = []
    for mask, ambang in ((mn > 200, 0.12), (mx < 85, 0.10)):
        baris = []
        for y in range(ch):
            run = terbaik = 0
            for v in mask[y]:
                run = run + 1 if v else 0
                if run > terbaik:
                    terbaik = run
            if ambang * cw <= terbaik <= 0.55 * cw:
                baris.append(y)
        if not baris:
            continue
        kelompok, awal = [], baris[0]
        for a, b in zip(baris, baris[1:]):
            if b - a > 1:
                kelompok.append((awal, a))
                awal = b
        kelompok.append((awal, baris[-1]))
        for atas, bawah in kelompok:
            y0 = mulai + atas * skala
            y1 = mulai + (bawah + 1) * skala
            tinggi = (y1 - y0) / h
            if not (0.03 <= tinggi <= 0.17) or y1 / h < 0.84:
                continue
            blok = mask[atas:bawah + 1]
            kolom = np.where(blok.any(axis=0))[0]
            if len(kolom) == 0:
                continue
            lebar = kolom.max() - kolom.min() + 1
            if not (0.15 <= lebar / cw <= 0.50):
                continue
            if not (1.3 <= lebar / max(1, bawah - atas + 1) <= 6):
                continue
            calon.append(y0 / h)
    return min(calon) if calon else None


def _kotak_buket(gray, std, batas):
    """Perkiraan kotak buket: baris/kolom yang isinya penuh detail."""
    h, w = gray.shape
    x0, x1 = int(w * 0.08), int(w * 0.92)
    ramai = std > 11
    fraksi_baris = ramai[:, x0:x1].mean(axis=1)
    baris = [y for y in range(0, batas) if fraksi_baris[y] > 0.33]
    if baris:
        atas_b, bawah_b = min(baris), max(baris)
    else:
        atas_b, bawah_b = int(h * 0.12), batas - 1
    fraksi_kolom = ramai[atas_b:bawah_b + 1, :].mean(axis=0)
    kolom = [x for x in range(w) if fraksi_kolom[x] > 0.22]
    kiri_b, kanan_b = (min(kolom), max(kolom)) if kolom else (0, w - 1)
    kanan_b = max(kanan_b, kiri_b + 8)
    bawah_b = max(bawah_b, atas_b + 8)
    return atas_b, bawah_b, kiri_b, kanan_b


def _potong_sekitar(gray, kotak, batas, h, w):
    """Kotak 4:5 yang memuat buket + ruang kosong, dipusatkan ke buketnya."""
    atas_b, bawah_b, kiri_b, kanan_b = kotak
    tepi = 0.10  # ruang kosong di sekeliling buket, relatif ukuran buket
    tinggi_butuh = max((bawah_b - atas_b + 1) * (1 + 2 * tepi),
                       (kanan_b - kiri_b + 1) * (1 + 2 * tepi) / RASIO_POTONG)
    tinggi = int(round(min(max(tinggi_butuh, batas * 0.55), batas)))
    lebar = min(int(round(tinggi * RASIO_POTONG)), w)
    tinggi = int(round(lebar / RASIO_POTONG))

    pusat_y = (atas_b + bawah_b) / 2
    atas = int(round(pusat_y - tinggi / 2))
    atas = max(0, min(atas, batas - tinggi))
    pusat_x = (kiri_b + kanan_b) / 2
    kiri = int(round(pusat_x - lebar / 2))
    kiri = max(0, min(kiri, w - lebar))
    return kiri, atas, lebar, tinggi


def _bingkai(cell, batas_rasio):
    """Kotak potong 4:5 dari sel pricelist: dasar potongan di batas_rasio (atas label)."""
    a, gray, std = _kanal(cell)
    h, w = gray.shape
    batas = int(round(h * batas_rasio))
    batas = min(max(batas, int(h * 0.5)), h - 1)
    return _potong_sekitar(gray, _kotak_buket(gray, std, batas), batas, h, w)


def _bingkai_foto(im):
    """Kotak potong 4:5 untuk foto satuan (tanpa label harga di dalamnya)."""
    a, gray, std = _kanal(im)
    h, w = gray.shape
    return _potong_sekitar(gray, _kotak_buket(gray, std, h), h, h, w)


def harga_dari_nama(nama):
    """'175k (2).jpeg' -> 175000. Nama berkas di catalog/satuan/ memakai harga."""
    cocok = re.match(r"^\s*(\d+)\s*k", nama, re.IGNORECASE)
    return int(cocok.group(1)) * 1000 if cocok else None


def siapkan_gambar():
    """Potong tiap sel pricelist jadi foto produk, buang label harga di bawah."""
    if os.path.isdir(IMG):
        shutil.rmtree(IMG)
    os.makedirs(IMG, exist_ok=True)

    # tahap 1: ambil sel + deteksi posisi label tiap sel
    sel_grid = []
    for nama, (cols, rows, harga) in GRIDS.items():
        im = Image.open(os.path.join(SRC, nama + ".jpeg")).convert("RGB")
        W, H = im.size
        cw, ch = W / cols, H / rows
        for indeks, harga_sel in enumerate(harga):
            r, c = divmod(indeks, cols)
            cell = im.crop((int(c * cw), int(r * ch), int((c + 1) * cw), int(r * ch + ch)))
            sel_grid.append({"nama": nama, "kode": "%s-%d" % (nama, indeks + 1),
                             "baris": r, "indeks": indeks, "cell": cell,
                             "harga": harga_sel, "label": _deteksi_label(cell)})

    # tahap 2: satu nilai per baris grid, diambil dari deteksi paling atas.
    # Label harga dalam satu baris letaknya sejajar, jadi nilai baris lebih
    # tahan terhadap sel yang deteksinya meleset.
    batas_baris = {}
    for nama, (cols, rows, harga) in GRIDS.items():
        for r in range(rows):
            nilai = [s["label"] for s in sel_grid
                     if s["nama"] == nama and s["baris"] == r and s["label"]]
            if nilai:
                batas_baris[(nama, r)] = min(0.88, max(0.78, min(nilai)))
            else:
                batas_baris[(nama, r)] = 0.82
    for kode, nilai in BATAS_SEL.items():
        nama, nomor = kode.split("-")
        batas_baris[(nama, (int(nomor) - 1) // GRIDS[nama][0])] = nilai

    # tahap 3: potong dan simpan
    foto = []
    for s in sel_grid:
        # 0.03 = cadangan aman: deteksi kadang jatuh di bagian bawah kotak label
        batas = batas_baris[(s["nama"], s["baris"])] - 0.03
        kiri, atas, lebar, tinggi = _bingkai(s["cell"], batas)
        sel = s["cell"].crop((kiri, atas, kiri + lebar, atas + tinggi))
        lebar_out = min(640, round(sel.width * 2))
        sel = sel.resize((lebar_out, round(sel.height * lebar_out / sel.width)), Image.LANCZOS)
        if s["harga"] in SEMBUNYI:
            continue
        sel.save(os.path.join(IMG, s["kode"] + ".webp"), "WEBP", quality=82, method=6)
        foto.append({
            "berkas": "assets/img/%s.webp" % s["kode"],
            "harga": s["harga"],
            "alt": "Contoh buket %s buatan Perfect Flowers" % rupiah(s["harga"]),
            "w": sel.width,
            "h": sel.height,
            "utama": 1,
        })

    # foto satuan (catalog/satuan/): foto buket asli per harga, dipakai sebagai
    # foto utama untuk harga tsb. Harga yang belum ada di pricelist otomatis
    # dapat halaman sendiri. Harga di SEMBUNYI tetap boleh tampil di sini,
    # karena yang diturunkan cuma potongan pricelist-nya.
    if os.path.isdir(SATUAN):
        satuan = []
        for berkas in sorted(os.listdir(SATUAN)):
            harga_sel = harga_dari_nama(berkas)
            if not harga_sel or not berkas.lower().endswith((".jpeg", ".jpg", ".png", ".webp")):
                continue
            satuan.append((harga_sel, berkas))
        urut_harga = {}
        for harga_sel, berkas in satuan:
            urut_harga[harga_sel] = urut_harga.get(harga_sel, 0) + 1
            im = Image.open(os.path.join(SATUAN, berkas)).convert("RGB")
            kiri, atas, lebar, tinggi = _bingkai_foto(im)
            sel = im.crop((kiri, atas, kiri + lebar, atas + tinggi))
            lebar_out = min(640, round(sel.width * 2))
            sel = sel.resize((lebar_out, round(sel.height * lebar_out / sel.width)), Image.LANCZOS)
            kode = "s-%dk-%d" % (harga_sel // 1000, urut_harga[harga_sel])
            sel.save(os.path.join(IMG, kode + ".webp"), "WEBP", quality=84, method=6)
            foto.append({
                "berkas": "assets/img/%s.webp" % kode,
                "harga": harga_sel,
                "alt": "Contoh buket %s buatan Perfect Flowers" % rupiah(harga_sel),
                "w": sel.width,
                "h": sel.height,
                "utama": 0,
            })

    # hero: foto buket asli (portrait). Bidang potong dipilih agar bagian atas
    # (terpal hijau) dan struk di bawah tidak ikut, fokus ke buketnya.
    hero = Image.open(os.path.join(SRC, "photos-35k.jpeg")).convert("RGB")
    W, H = hero.size
    kiri, atas, lebar = int(W * 0.080), int(H * 0.300), int(W * 0.820)
    tinggi = round(lebar / 0.8)
    hero = hero.crop((kiri, atas, kiri + lebar, atas + tinggi))
    hero = hero.resize((800, 1000), Image.LANCZOS)
    hero.save(os.path.join(IMG, "hero.webp"), "WEBP", quality=84, method=6)

    # qris dan patokan lokasi
    for nama, keluar, ukuran in [
        ("qris.jpeg", "qris.webp", (720, 720)),
        ("patokan-maps.jpeg", "lokasi.webp", (900, 900)),
    ]:
        im2 = Image.open(os.path.join(SRC, nama)).convert("RGB")
        im2.thumbnail(ukuran, Image.LANCZOS)
        im2.save(os.path.join(IMG, keluar), "WEBP", quality=84, method=6)

    # poster ketentuan pemesanan (teks kecil, jadi kualitasnya lebih tinggi)
    tnc = Image.open(os.path.join(SRC, "tnc.jpeg")).convert("RGB")
    if tnc.width > 1000:
        tnc = tnc.resize((1000, round(tnc.height * 1000 / tnc.width)), Image.LANCZOS)
    tnc.save(os.path.join(IMG, "tnc.webp"), "WEBP", quality=88, method=6)

    # logo toko: kartu nama bulat dari owner. Di header dipakai potongan
    # monogram PF karena teks kecil di kartu tidak terbaca pada 46px; logo
    # penuh dipakai di footer dan halaman tentang.
    logo_penuh = Image.open(os.path.join(SRC, "logo.jpeg")).convert("RGB")

    def _bulat(im, ukuran=512):
        im = ImageOps.fit(im, (ukuran, ukuran), Image.LANCZOS)
        m = Image.new("L", (2048, 2048), 0)
        ImageDraw.Draw(m).ellipse((4, 4, 2043, 2043), fill=255)
        im.putalpha(m.resize((ukuran, ukuran), Image.LANCZOS))
        return im

    _bulat(logo_penuh).save(os.path.join(IMG, "logo.webp"), "WEBP", quality=90, method=6)
    W, H = logo_penuh.size
    monogram = logo_penuh.crop((int(W * 0.325), int(H * 0.105),
                                int(W * 0.665), int(H * 0.445)))
    tanda = _bulat(monogram)
    tanda.save(os.path.join(IMG, "logo-mark.webp"), "WEBP", quality=90, method=6)
    for ukuran in (64, 180):
        tanda.resize((ukuran, ukuran), Image.LANCZOS).save(
            os.path.join(IMG, "logo-%d.png" % ukuran), "PNG", optimize=True)

    # lembar katalog foto. Label harga sudah menempel di dalam foto, jadi lembar
    # tidak dipotong: tiap lembar diberi bingkai warna latarnya sendiri sampai
    # rasio seragam, supaya semua kotak di grid tingginya sama dan tidak ada
    # ruang kosong di bawah lembar yang lebih pendek.
    lembar = []
    for s in LEMBAR:
        im3 = Image.open(os.path.join(KATALOG, s["berkas"])).convert("RGB")
        if im3.width > 1080:
            im3 = im3.resize((1080, round(im3.height * 1080 / im3.width)), Image.LANCZOS)
        asal = im3.height / im3.width
        # bingkai warna kertas situs (sama dengan latar .lembar__tautan), bukan
        # warna sudut foto: hasilnya seragam dan tidak terlihat seperti sambungan
        im3 = ImageOps.pad(
            im3, (LEBAR_LEMBAR, round(LEBAR_LEMBAR / RASIO_LEMBAR)),
            color=(255, 250, 244), centering=(0.5, 0.5), method=Image.Resampling.LANCZOS,
        )
        lembar.append({"img": im3, "harga": s["harga"], "asal": asal})
    # urutan tetap seperti sebelumnya (rasio asli), supaya nomor lembar tidak berubah
    lembar.sort(key=lambda l: -l["asal"])

    hasil = []
    for indeks, l in enumerate(lembar, 1):
        im3 = l["img"]
        berkas = "katalog-%02d.webp" % indeks
        im3.save(os.path.join(IMG, berkas), "WEBP", quality=82, method=6)
        hasil.append({
            "berkas": "assets/img/" + berkas,
            "w": im3.width,
            "h": im3.height,
            "jumlah": len(l["harga"]),
            "min": min(l["harga"]),
            "max": max(l["harga"]),
        })

    return foto, hasil


# ---------------------------------------------------------------- komponen

def nav_aktif(aktif, kunci, href, teks):
    tanda = ' aria-current="page"' if aktif == kunci else ""
    return '<li><a href="%s"%s>%s</a></li>' % (href, tanda, teks)


def wa_tautan(pesan=None):
    nomor = (SITE.get("wa") or "").strip()
    if not nomor:
        return None
    nomor = nomor.replace("+", "").replace(" ", "").replace("-", "")
    if nomor.startswith("0"):
        nomor = "62" + nomor[1:]
    from urllib.parse import quote
    return "https://wa.me/%s?text=%s" % (nomor, quote(pesan or SITE.get("wa_pesan", "")))


def nomor_tampil():
    """0851-5722-6960 dari 6285157226960."""
    nomor = (SITE.get("wa") or "").strip()
    if not nomor:
        return ""
    nomor = nomor.replace("+", "").replace(" ", "").replace("-", "")
    lokal = "0" + nomor[2:] if nomor.startswith("62") else nomor
    if len(lokal) >= 11:
        return "%s-%s-%s" % (lokal[:4], lokal[4:8], lokal[8:])
    return lokal


def tombol_order(kelas="tombol", teks="Order via WhatsApp", pesan=None):
    tautan = wa_tautan(pesan)
    if tautan:
        return '<a class="%s" href="%s" target="_blank" rel="noopener">%s</a>' % (
            kelas, escape(tautan), teks)
    # nomor WA belum diisi: arahkan ke halaman kontak, jangan bikin tombol mati
    label = teks.replace("Order via WhatsApp", "Order sekarang").replace("Pesan lewat WhatsApp", "Cara pesan")
    return '<a class="%s" href="/kontak/">%s</a>' % (kelas, label)


IKON_DAUN = ('<svg viewBox="0 0 160 96" fill="none" stroke="currentColor" stroke-width="1.1" '
             'stroke-linecap="round" aria-hidden="true" focusable="false">'
             '<path d="M10 86C46 70 96 44 148 8"/>'
             '<ellipse cx="22" cy="56" rx="10" ry="6" transform="rotate(-56 22 56)"/>'
             '<ellipse cx="34" cy="84" rx="10" ry="6" transform="rotate(34 34 84)"/>'
             '<ellipse cx="54" cy="43" rx="10" ry="6" transform="rotate(-58 54 43)"/>'
             '<ellipse cx="66" cy="71" rx="10" ry="6" transform="rotate(30 66 71)"/>'
             '<ellipse cx="86" cy="30" rx="10" ry="6" transform="rotate(-56 86 30)"/>'
             '<ellipse cx="98" cy="58" rx="10" ry="6" transform="rotate(32 98 58)"/>'
             '<ellipse cx="116" cy="18" rx="10" ry="6" transform="rotate(-58 116 18)"/>'
             '<ellipse cx="128" cy="46" rx="10" ry="6" transform="rotate(28 128 46)"/>'
             '<ellipse cx="144" cy="9" rx="9" ry="5.4" transform="rotate(-44 144 9)"/>'
             '</svg>')

IKON_BUNGA = ('<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.15" '
              'aria-hidden="true" focusable="false">'
              '<ellipse cx="16" cy="8.6" rx="4.5" ry="6.3"/>'
              '<ellipse cx="16" cy="8.6" rx="4.5" ry="6.3" transform="rotate(72 16 16)"/>'
              '<ellipse cx="16" cy="8.6" rx="4.5" ry="6.3" transform="rotate(144 16 16)"/>'
              '<ellipse cx="16" cy="8.6" rx="4.5" ry="6.3" transform="rotate(216 16 16)"/>'
              '<ellipse cx="16" cy="8.6" rx="4.5" ry="6.3" transform="rotate(288 16 16)"/>'
              '<circle cx="16" cy="16" r="2.1" fill="currentColor" stroke="none"/>'
              '</svg>')

IKON_WA = ('<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false">'
           '<path fill="currentColor" d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38c1.45.79 3.08 1.21 4.79 1.21h.01c5.46 0 9.91-4.45 9.91-9.91C21.96 6.45 17.5 2 12.04 2Zm5.8 14.13c-.24.68-1.4 1.3-1.93 1.35-.53.05-1.02.24-3.44-.72-2.93-1.15-4.75-4.2-4.9-4.4-.14-.2-1.16-1.55-1.16-2.96 0-1.4.73-2.09 1-2.38.26-.29.58-.36.77-.36l.56.01c.18 0 .42-.07.65.5.24.58.82 2 .89 2.14.07.14.12.31.02.5-.1.2-.15.32-.29.49-.15.17-.31.38-.44.51-.15.14-.3.3-.13.59.17.29.75 1.24 1.62 2.01 1.11.99 2.05 1.3 2.34 1.44.29.15.46.12.63-.07.17-.2.73-.85.93-1.14.19-.29.39-.24.65-.14.26.09 1.66.78 1.94.93.29.14.48.22.55.34.07.13.07.73-.17 1.41Z"/></svg>')


def pembatas(kelas=""):
    """Garis rambut dengan satu kuntum kecil di tengahnya."""
    return ('<div class="pembatas %s" role="presentation">'
            '<span class="pembatas__garis"></span>%s<span class="pembatas__garis"></span></div>'
            % (kelas, IKON_BUNGA))


def tombol_wa_melayang():
    """Tombol WhatsApp tetap di pojok kanan bawah supaya selalu bisa dijangkau."""
    tautan = wa_tautan()
    if not tautan:
        return ""
    return ('<a class="wa-melayang" href="%s" target="_blank" rel="noopener" '
            'aria-label="Chat WhatsApp Perfect Flowers">%s</a>' % (escape(tautan), IKON_WA))


def kepala(judul, deskripsi, aktif, kanonikal=""):
    fav = '/assets/img/logo-64.png'
    kanon = ""
    if SITE.get("url") and kanonikal:
        kanon = '<link rel="canonical" href="%s%s">' % (SITE["url"], kanonikal)
    og_url = ""
    if SITE.get("url") and kanonikal:
        og_url = '<meta property="og:url" content="%s%s">' % (SITE["url"], kanonikal)
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(judul)}</title>
<meta name="description" content="{escape(deskripsi)}">
{kanon}
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(judul)}">
<meta property="og:description" content="{escape(deskripsi)}">
<meta property="og:image" content="/assets/img/hero.webp">
{og_url}
<link rel="icon" href="{fav}" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/logo-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="/assets/css/style.css?v={versi_aset('assets/css/style.css')}">
</head>
<body>
<a class="skip" href="#utama">Lewati ke isi utama</a>
<header class="site-head">
  <div class="wrap">
    <div class="site-head__row">
      <a class="merek" href="/">
        <img class="merek__logo" src="/assets/img/logo-mark.webp" alt="" width="46" height="46" decoding="async">
        <span class="merek__nama">Perfect Flowers</span>
      </a>
      <button class="nav-tombol" type="button" data-nav-tombol aria-expanded="false" aria-controls="nav-utama">
        <span class="nav-tombol__garis" aria-hidden="true"></span> Menu
      </button>
      <nav class="nav" id="nav-utama" data-nav data-terbuka="false" aria-label="Navigasi utama">
        <ul>
          {nav_aktif(aktif, "katalog", "/katalog/", "Katalog")}
          {nav_aktif(aktif, "cara", "/#cara-order", "Cara order")}
          {nav_aktif(aktif, "ketentuan", "/#ketentuan", "Ketentuan")}
          {nav_aktif(aktif, "tentang", "/tentang/", "Tentang")}
          {nav_aktif(aktif, "kontak", "/kontak/", "Kontak")}
        </ul>
      </nav>
      <div class="head-cta">{tombol_order("tombol", "Order via WhatsApp")}</div>
    </div>
  </div>
</header>
<main id="utama">
"""


def kaki():
    instagram = SITE.get("instagram", "")
    insta = ('<li><a href="%s">Instagram %s</a></li>' % (escape(instagram), escape(SITE["handle"]))
             if instagram else "")
    wa_kaki = ""
    tautan_wa = wa_tautan()
    if tautan_wa:
        wa_kaki = '<li><a href="%s" target="_blank" rel="noopener">WhatsApp %s</a></li>' % (
            escape(tautan_wa), nomor_tampil())
    return f"""</main>
<footer class="site-foot">
  <div class="wrap">
    {pembatas("pembatas--kaki")}
    <div class="site-foot__isi">
      <div>
        <img class="site-foot__logo" src="/assets/img/logo.webp" alt="Logo Perfect Flowers" width="72" height="72" loading="lazy" decoding="async">
        <h2>{escape(SITE["brand"])}</h2>
        <p>Buket bunga yang dirakit setelah order fix, diambil di Tangerang.</p>
        <p class="teks-kecil">{escape(SITE["tagline"])}</p>
      </div>
      <div>
        <h2>Halaman</h2>
        <ul>
          <li><a href="/katalog/">Katalog buket</a></li>
          <li><a href="/katalog/foto/">Katalog foto</a></li>
          <li><a href="/#cara-order">Cara order</a></li>
          <li><a href="/tentang/">Tentang</a></li>
          <li><a href="/kontak/">Kontak dan pembayaran</a></li>
          <li><a href="/#ketentuan">Ketentuan pemesanan</a></li>
        </ul>
      </div>
      <div>
        <h2>Ambil di</h2>
        <p>{escape(SITE["alamat"])}<br>{escape(SITE["petunjuk"])}</p>
        <ul>
          <li><a href="{escape(SITE["maps"])}">Buka di Google Maps</a></li>
          {insta}
          {wa_kaki}
        </ul>
      </div>
    </div>
    <div class="site-foot__bawah">
      <span>&copy; {escape(SITE["brand"])}. Semua foto buket adalah hasil rangkaian kami sendiri.</span>
      <span>DP 50%, sisanya dibayar saat ambil.</span>
    </div>
  </div>
</footer>
{tombol_wa_melayang()}
<script src="/assets/js/site.js?v={versi_aset('assets/js/site.js')}" defer></script>
</body>
</html>
"""


def band(harga):
    """Kelompok harga, dipakai untuk warna penanda di kartu dan tombol saring."""
    if harga < 100000:
        return "kecil"
    if harga < 200000:
        return "sedang"
    return "besar"


def kartu_produk(foto, harga, kelas_extra=""):
    return f"""<article class="kartu" data-harga="{harga}" data-band="{band(harga)}"{kelas_extra}>
  <a class="kartu__tautan" href="/katalog/{slug(harga)}/">
    <img src="/{foto['berkas']}" alt="{escape(foto['alt'])}" width="{foto['w']}" height="{foto['h']}" loading="lazy" decoding="async">
    <div class="kartu__meta">
      <h3 class="kartu__nama">Buket {harga // 1000}K</h3>
      <p class="kartu__harga">{rupiah(harga)}</p>
    </div>
  </a>
  <button class="tombol-zoom" type="button" data-zoom data-foto="/{foto['berkas']}" data-alt="{escape(foto['alt'])}" aria-label="Lihat foto Buket {harga // 1000}K ukuran penuh">
    <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="11" cy="11" r="7.2"/><path d="M20.2 20.2 16 16M11 8.4v5.2M8.4 11h5.2"/></svg>
  </button>
</article>"""


def ringkas(harga):
    if harga <= 50000:
        return "Pilihan paling ringan di daftar ini, cukup untuk ucapan singkat atau kejutan kecil."
    if harga <= 110000:
        return "Ukuran menengah, pas untuk hadiah ulang tahun atau hari jadi."
    if harga <= 175000:
        return "Rangkaian lebih penuh, untuk momen yang ingin terasa lebih besar."
    if harga <= 260000:
        return "Rangkaian besar dengan isian lebih banyak, untuk lamaran, wisuda, atau anniversary."
    return "Rangkaian terbesar di daftar ini, untuk momen yang ingin dibuat menonjol."


# ---------------------------------------------------------------- halaman

def halaman_beranda(tier):
    pilihan = "".join(kartu_produk(tier[h]["foto"][0], h) for h in PILIHAN_BERANDA if h in tier)
    termurah = min(tier)
    return kepala(
        "Perfect Flowers, buket bunga di Tangerang",
        "Buket bunga dirakit setelah order fix, mulai %s. Ambil di Gg. Peluru No.23, Tangerang." % rupiah(termurah),
        "beranda",
        "/",
    ) + f"""
<section class="hero">
  <div class="wrap hero__isi">
    <div>
      <h1>Buket bunga yang dirakit <em>hari itu</em>, bukan stok jadi.</h1>
      <p class="hero__teks">Pilih sesuai budget, dari {rupiah(termurah)} sampai rangkaian besar. Isi bunga mengikuti stok pagi, jadi tidak ada dua buket yang sama persis.</p>
      <div class="hero__aksi">
        <a class="tombol" href="/katalog/">Lihat katalog</a>
        {tombol_order("tombol tombol--outline", "Chat WhatsApp")}
      </div>
    </div>
    <figure class="hero__foto">
      <img src="/assets/img/hero.webp" alt="Buket bunga campur warna cerah dengan pita pink, hasil rangkaian Perfect Flowers" width="800" height="1000" fetchpriority="high" decoding="async">
      <figcaption class="hero__kartu">
        <strong>Mulai {rupiah(termurah)}</strong>
        <span>Harga jadi, bukan harga mulai.</span>
      </figcaption>
    </figure>
  </div>
</section>

<div class="wrap">
  <div class="fakta">
    <ul>
      <li><strong>Dirakit setelah order fix</strong><span>Buket baru dibuat setelah form order diisi, bukan diambil dari rak.</span></li>
      <li><strong>DP 50% mengunci order</strong><span>Sisanya dibayar saat ambil, bisa tunai.</span></li>
      <li><strong>Ambil di Gg. Peluru No.23</strong><span>Rumah warna hijau, belakang bengkel AC.</span></li>
    </ul>
  </div>
</div>

<section>
  <div class="wrap">
    <div class="judul-bagian">
      <h2>Buket pilihan, dari {rupiah(termurah)}</h2>
      <p>Semua foto di sini adalah buket yang sudah kami buat sendiri. Harga tertulis adalah harga jadi.</p>
    </div>
    <p class="label" data-nomor="01">Pilihan buket</p>
    <div class="produk-grid">{pilihan}</div>
    <p style="margin-top:1.6rem"><a class="tautan" href="/katalog/">Lihat semua harga</a></p>
  </div>
</section>

<section class="alur" id="cara-order">
  <span class="sprig sprig--alur" aria-hidden="true">{IKON_DAUN}</span>
  <div class="wrap">
    <p class="label" data-nomor="02">Cara order</p>
    <h2>Tiga langkah, tanpa aplikasi baru.</h2>
    <ol class="alur__daftar">
      <li>
        <span class="alur__nomor" aria-hidden="true">1</span>
        <div>
          <h3>Isi form fix order</h3>
          <p>Nama penerima, harga buket, isi kartu ucapan, dan jam ambil. Form dikirim lewat WhatsApp setelah kamu pilih buket.</p>
        </div>
      </li>
      <li>
        <span class="alur__nomor" aria-hidden="true">2</span>
        <div>
          <h3>Bayar DP 50%</h3>
          <p>Transfer BCA atau QRIS, lalu kirim bukti transfer. Order masuk daftar kerja setelah DP diterima.</p>
        </div>
      </li>
      <li>
        <span class="alur__nomor" aria-hidden="true">3</span>
        <div>
          <h3>Ambil sesuai jadwal</h3>
          <p>Datang ke {escape(SITE["alamat"])} pada jam yang disepakati, bayar sisanya di tempat.</p>
        </div>
      </li>
    </ol>
  </div>
</section>

<section class="bayar">
  <div class="wrap bayar__isi">
    <div>
      <p class="label" data-nomor="03">Pembayaran</p>
      <h2>DP lewat transfer BCA atau QRIS</h2>
      <p>DP minimal {SITE["dp_persen"]}% dari harga buket. Sisanya dibayar saat pengambilan, tunai atau transfer di tempat.</p>
      <div class="rekening">
        <dl>
          <dt>Bank</dt><dd>{escape(SITE["bank"]["nama"])}</dd>
          <dt>Nomor</dt><dd>{escape(SITE["bank"]["nomor"])}</dd>
          <dt>Atas nama</dt><dd>{escape(SITE["bank"]["atas_nama"])}</dd>
        </dl>
      </div>
      <p class="teks-kecil">Bukti transfer dikirim lewat WhatsApp supaya pesanan langsung masuk daftar kerja.</p>
    </div>
    <div class="qris">
      <img src="/assets/img/qris.webp" alt="Kode QRIS Perfect Flowers untuk pembayaran DP" width="720" height="720" loading="lazy" decoding="async">
      <p class="teks-kecil">Pindai dengan aplikasi bank atau e-wallet, lalu kirim bukti transfer lewat WhatsApp.</p>
    </div>
  </div>
</section>

<section class="ketentuan" id="ketentuan">
  <span class="sprig sprig--ketentuan" aria-hidden="true">{IKON_DAUN}</span>
  <div class="wrap">
    <p class="label" data-nomor="04">Ketentuan</p>
    <div class="tnc">
      <div>
        <h2>Ketentuan pemesanan, dibaca sebelum order.</h2>
        <p style="margin-top:1rem">Empat hal ini yang paling sering ditanyakan. Versi lengkapnya ada di poster sebelah, sama dengan poster yang kami kirim lewat WhatsApp.</p>
        <ul class="ketentuan__daftar">
          <li><b>DP {SITE["dp_persen"]}%</b><span>Dibayar setelah form fix order diisi, bukan saat tanya-tanya.</span></li>
          <li><b>DP tidak dikembalikan</b><span>Bila order dibatalkan sepihak, karena bunga dan material sudah disiapkan.</span></li>
          <li><b>Isi bunga ikut stok</b><span>Jenis dan warna menyesuaikan stok hari pengerjaan, hasil diusahakan mirip foto sekitar 90%.</span></li>
          <li><b>Bukti transfer</b><span>Dikirim lewat chat supaya pesanan langsung masuk daftar kerja.</span></li>
        </ul>
        <p style="margin-top:1.2rem">{tombol_order("tautan", "Tanya soal ketentuan lewat WhatsApp", "Halo Perfect Flowers, saya mau tanya ketentuan pemesanan buket.")}</p>
      </div>
      <figure class="tnc__gambar">
        <button class="bingkai-zoom" type="button" data-zoom data-foto="/assets/img/tnc.webp" data-alt="Poster ketentuan pemesanan Perfect Flowers: DP minimal 50 persen, pembayaran lewat QRIS atau transfer BCA, ketersediaan bunga mengikuti stok, dan DP tidak dapat dikembalikan">
          <img src="/assets/img/tnc.webp" alt="Poster ketentuan pemesanan Perfect Flowers: DP minimal 50 persen, pembayaran lewat QRIS atau transfer BCA 8670697011 a.n. Eli Nofiyanti, ketersediaan bunga mengikuti stok hari pengerjaan, dan DP tidak dapat dikembalikan" width="1000" height="1500" loading="lazy" decoding="async">
          <span class="petunjuk-zoom">Klik untuk ukuran penuh</span>
        </button>
        <figcaption>Ketentuan pemesanan Perfect Flowers</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="lokasi">
  <div class="wrap lokasi__isi">
    <img src="/assets/img/lokasi.webp" alt="Patokan lokasi pengambilan buket Perfect Flowers di Gg. Peluru No.23 Tangerang" width="900" height="900" loading="lazy" decoding="async">
    <div>
      <p class="label" data-nomor="05">Lokasi</p>
      <h2>Pengambilan di rumah, bukan dikirim.</h2>
      <address>{escape(SITE["alamat"])}<br>{escape(SITE["petunjuk"])}</address>
      <p class="teks-kecil">Pengambilan dilakukan sesuai jam yang disepakati saat order, supaya buket tidak menunggu terlalu lama di luar.</p>
      <div class="hero__aksi">
        <a class="tombol tombol--outline" href="{escape(SITE["maps"])}">Buka Google Maps</a>
        {tombol_order("tautan", "Tanya stok lewat WhatsApp")}
      </div>
    </div>
  </div>
</section>
""" + kaki()


def halaman_katalog(tier, lembar):
    daftar = "".join(kartu_produk(tier[h]["foto"][0], h) for h in sorted(tier))
    return kepala(
        "Katalog buket bunga, Perfect Flowers",
        "Daftar harga buket Perfect Flowers, dari %s sampai %s. Foto asli buket yang sudah dibuat."
        % (rupiah(min(tier)), rupiah(max(tier))),
        "katalog",
        "/katalog/",
    ) + f"""
<div class="page-head">
  <div class="wrap">
    <p class="label" data-nomor="01">Katalog</p>
    <h1>Harga buket, apa adanya.</h1>
    <p>{len(tier)} pilihan harga, dari {rupiah(min(tier))} sampai {rupiah(max(tier))}. Semua foto adalah buket yang sudah kami buat, jadi yang kamu lihat memang contoh nyata, bukan gambar ilustrasi.</p>
  </div>
</div>
<section style="padding-top:0">
  <div class="wrap">
    <div class="saring" data-saring role="group" aria-label="Saring buket berdasarkan harga">
      <button type="button" data-batas="semua" aria-pressed="true">Semua</button>
      <button type="button" data-batas="kecil" aria-pressed="false">Di bawah 100 ribu</button>
      <button type="button" data-batas="sedang" aria-pressed="false">100 sampai 200 ribu</button>
      <button type="button" data-batas="besar" aria-pressed="false">Di atas 200 ribu</button>
    </div>
    <p class="saring__hitung" data-hitung aria-live="polite"></p>
    <div class="produk-grid" data-daftar-produk>{daftar}</div>
    <p style="margin-top:1.8rem"><a class="tautan" href="/katalog/foto/">Lihat {len(lembar)} lembar katalog foto</a></p>
  </div>
</section>
""" + kaki()


def chip_harga(harga):
    """Tautan kecil untuk harga yang belum punya halaman sendiri."""
    pesan = "Halo Perfect Flowers, saya mau pesan buket %s. Boleh info ketersediaan bunga hari ini?" % rupiah(harga)
    tautan = wa_tautan(pesan)
    if tautan:
        return ('<li><a href="%s" target="_blank" rel="noopener"><b>%s</b><span>Tanya stok</span></a></li>'
                % (escape(tautan), rupiah(harga)))
    return '<li><a href="/kontak/"><b>%s</b><span>Cara pesan</span></a></li>' % rupiah(harga)


def lembar_foto(lembar):
    blok = []
    for nomor, l in enumerate(lembar, 1):
        alt = "Katalog foto lembar %d: %d buket dengan harga %s sampai %s" % (
            nomor, l["jumlah"], rupiah(l["min"]), rupiah(l["max"]))
        blok.append(f"""<figure class="lembar">
  <a class="lembar__tautan" href="/{l['berkas']}" target="_blank" rel="noopener">
    <img src="/{l['berkas']}" alt="{escape(alt)}" width="{l['w']}" height="{l['h']}" loading="lazy" decoding="async">
  </a>
  <figcaption><strong>Lembar {nomor}</strong><span>{l['jumlah']} buket</span><span>{rupiah(l['min'])} sampai {rupiah(l['max'])}</span></figcaption>
</figure>""")
    return "".join(blok)


def halaman_katalog_foto(lembar, tier):
    semua = sorted({h for s in LEMBAR for h in s["harga"]})
    baru = [h for h in semua if h not in tier and h not in SEMBUNYI]
    blok_baru = ""
    if baru:
        blok_baru = f"""
<section class="tambahan">
  <div class="wrap">
    <p class="label" data-nomor="02">Harga di lembar katalog</p>
    <h2 style="font-size:clamp(1.5rem,3vw,2rem);max-width:36ch">{len(baru)} harga ini ada di lembar katalog, belum masuk daftar utama.</h2>
    <p style="max-width:58ch;margin-top:0.9rem">Kalau tertarik pada salah satunya, tanya lewat WhatsApp. Kami cek stok bunga hari itu dulu, lalu kirim ukuran dan contoh foto buketnya.</p>
    <ul class="harga-baru">{''.join(chip_harga(h) for h in baru)}</ul>
  </div>
</section>"""
    termurah = min(s["min"] for s in lembar)
    termahal = max(s["max"] for s in lembar)
    return kepala(
        "Katalog foto buket, Perfect Flowers",
        "%d lembar katalog foto buket Perfect Flowers, dari %s sampai %s. Semua foto buket asli toko." % (
            len(lembar), rupiah(termurah), rupiah(termahal)),
        "katalog",
        "/katalog/foto/",
    ) + f"""
<div class="page-head">
  <div class="wrap">
    <p class="label" data-nomor="01">Katalog foto</p>
    <h1>Katalog foto, {len(lembar)} lembar, semua buket kami.</h1>
    <p>Ini lembar katalog yang biasa kami kirim lewat WhatsApp. Semua foto adalah buket yang sudah kami buat sendiri, dan harga tertulis di tiap foto adalah harga jadi, dari {rupiah(termurah)} sampai {rupiah(termahal)}. Lembar bisa dibuka sendiri untuk ukuran penuh.</p>
  </div>
</div>
{blok_baru}
<section style="padding-top:0">
  <div class="wrap">
    <p class="label" data-nomor="03">Lembar katalog</p>
    <div class="lembar-grid">{lembar_foto(lembar)}</div>
    <p style="margin-top:1.8rem"><a class="tautan" href="/katalog/">Lihat daftar harga per buket</a></p>
  </div>
</section>
""" + kaki()


def halaman_produk(tier, harga):
    data = tier[harga]
    lain = [h for h in sorted(tier) if h != harga]
    lain.sort(key=lambda h: abs(h - harga))
    terkait = "".join(kartu_produk(tier[h]["foto"][0], h) for h in lain[:4])
    galeri = "".join(
        '<button class="bingkai-zoom" type="button" data-zoom data-foto="/%s" data-alt="%s">'
        '<img src="/%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async"></button>'
        % (f["berkas"], escape(f["alt"]), f["berkas"], escape(f["alt"]), f["w"], f["h"])
        for f in data["foto"][1:]
    )
    blok_galeri = ""
    if galeri:
        blok_galeri = f"""
      <h2 style="font-size:1.2rem;margin-top:2rem">Foto lain di harga ini</h2>
      <p class="teks-kecil">{len(data["foto"]) - 1} buket lain yang pernah kami buat pada harga {rupiah(harga)}.</p>
      <div class="galeri">{galeri}</div>"""

    pesan = "Halo Perfect Flowers, saya mau pesan buket %s. Boleh info ketersediaan bunga hari ini?" % rupiah(harga)
    return kepala(
        "Buket %s, Perfect Flowers" % rupiah(harga),
        "%s Harga %s, dirakit setelah order fix, ambil di Tangerang." % (ringkas(harga), rupiah(harga)),
        "katalog",
        "/katalog/%s/" % slug(harga),
    ) + f"""
<section class="detail">
  <div class="wrap">
    <p class="label" data-nomor="01">Detail buket</p>
    <div class="detail__isi">
      <div class="detail__foto">
        <button class="bingkai-zoom" type="button" data-zoom data-foto="/{data['foto'][0]['berkas']}" data-alt="{escape(data['foto'][0]['alt'])}">
          <img src="/{data['foto'][0]['berkas']}" alt="{escape(data['foto'][0]['alt'])}" width="{data['foto'][0]['w']}" height="{data['foto'][0]['h']}" fetchpriority="high" decoding="async">
          <span class="petunjuk-zoom">Klik untuk ukuran penuh</span>
        </button>
      </div>
      <div class="detail__teks">
        <h1>Buket {harga // 1000}K</h1>
        <p class="detail__harga">{rupiah(harga)}</p>
        <p>{ringkas(harga)}</p>
        <div class="detail__aksi">
          {tombol_order("tombol tombol--penuh", "Pesan lewat WhatsApp", pesan)}
          <a class="tombol tombol--outline tombol--penuh" href="/katalog/">Lihat harga lain</a>
        </div>
        <ul class="catatan">
          <li><b>Isi bunga</b> mengikuti stok hari itu. Kalau ada bunga yang kosong, kami kabari dulu sebelum mulai merangkai.</li>
          <li><b>Kemiripan</b> sekitar 90% dari foto, karena bentuk dan warna bunga alami bisa sedikit berbeda.</li>
          <li><b>Pengerjaan</b> dimulai setelah form order dan DP {SITE["dp_persen"]}% masuk, jadwal ambil disepakati lewat WhatsApp.</li>
          <li><b>Pengambilan</b> di {escape(SITE["alamat"])}, {escape(SITE["petunjuk"]).lower()}</li>
        </ul>
        <p style="margin-top:1rem"><a class="tautan" href="/#ketentuan">Baca ketentuan pemesanan lengkap</a></p>
      </div>
    </div>
    {blok_galeri}
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <p class="label" data-nomor="02">Harga lain</p>
    <div class="produk-grid">{terkait}</div>
  </div>
</section>
""" + kaki()


def halaman_tentang(tier):
    return kepala(
        "Tentang Perfect Flowers",
        "Perfect Flowers merangkai buket dari rumah di Gg. Peluru No.23, Tangerang. Setiap order dirakit setelah form order masuk.",
        "tentang",
        "/tentang/",
    ) + f"""
<div class="page-head">
  <div class="wrap">
    <p class="label" data-nomor="01">Tentang</p>
    <h1>Merangkai dari rumah, satu pesanan sekali jalan.</h1>
    <p>Perfect Flowers melayani pesanan buket dari rumah di {escape(SITE["alamat"])}. Semua pesanan masuk lewat WhatsApp dengan form fix order, lalu dirakit satu per satu.</p>
    <figure class="tentang__logo">
      <img src="/assets/img/logo.webp" alt="Logo Perfect Flowers: monogram PF dengan mawar, pita satin, dan daun eucalyptus" width="512" height="512" loading="lazy" decoding="async">
      <figcaption>Kartu nama Perfect Flowers. TikTok @perfectflowers_id, Instagram {escape(SITE["handle"])}, WhatsApp {nomor_tampil()}.</figcaption>
    </figure>
  </div>
</div>
<section style="padding-top:0.4rem">
  <div class="wrap" style="display:grid;gap:clamp(1.4rem,3vw,2.4rem)">
    <div>
      <p class="label" data-nomor="02">Cara kami bekerja</p>
      <h2 style="font-size:clamp(1.5rem,3vw,2rem);max-width:30ch">Tidak ada buket yang menunggu di rak.</h2>
      <p style="max-width:60ch;margin-top:1rem">Bunga dibeli mendekati hari pengambilan, lalu dirangkai setelah form order dan DP masuk. Karena itu warna dan jenis bunga bisa berbeda sedikit dari foto contoh, biasanya masih sekitar 90% mirip. Kalau ada bunga yang sedang kosong, kami kabari lebih dulu sebelum mulai merangkai.</p>
    </div>
    <div>
      <p class="label" data-nomor="03">Harga</p>
      <h2 style="font-size:clamp(1.5rem,3vw,2rem);max-width:30ch">Harga jadi, dari {rupiah(min(tier))} sampai {rupiah(max(tier))}.</h2>
      <p style="max-width:60ch;margin-top:1rem">Setiap harga punya ukuran dan isian yang berbeda. Daftar lengkapnya ada di halaman katalog, lengkap dengan foto buket asli pada harga tersebut. Tidak ada biaya tersembunyi: yang tertulis adalah harga buketnya.</p>
      <p style="margin-top:1.2rem"><a class="tautan" href="/katalog/">Buka katalog</a></p>
    </div>
    <div>
      <p class="label" data-nomor="04">Pengambilan</p>
      <h2 style="font-size:clamp(1.5rem,3vw,2rem);max-width:30ch">Ambil di rumah, sesuai jam yang disepakati.</h2>
      <p style="max-width:60ch;margin-top:1rem">Lokasi pengambilan di {escape(SITE["alamat"])}, {escape(SITE["petunjuk"]).lower()} Jam pengambilan disepakati saat order supaya buket tidak menunggu terlalu lama di luar.</p>
      <p style="margin-top:1.2rem"><a class="tautan" href="{escape(SITE["maps"])}">Buka Google Maps</a></p>
    </div>
  </div>
</section>
""" + kaki()


def halaman_kontak(tier):
    tautan = wa_tautan()
    if tautan:
        kartu_wa = f"""
    <div class="kartu-info">
      <h2>WhatsApp</h2>
      <p>Nomor WhatsApp kami: <b>{escape(nomor_tampil())}</b>. Tanya stok, kirim form fix order, atau konsultasi isi buket.</p>
      <p class="teks-kecil">Balasan mengikuti jam kerja. Kalau sedang merangkai pesanan, balasan bisa agak lambat.</p>
      <p style="margin-top:1rem"><a class="tombol" href="{escape(tautan)}" target="_blank" rel="noopener">Chat lewat WhatsApp</a></p>
    </div>"""
    else:
        kartu_wa = """
    <div class="kartu-info kartu-info--catatan">
      <h2>WhatsApp</h2>
      <p>Nomor WhatsApp belum diisi di halaman ini.</p>
      <p class="teks-kecil">Placeholder: isi kolom <code>wa</code> pada <code>data/site.json</code>, lalu jalankan <code>python build.py</code>. Tombol order di seluruh halaman akan langsung mengarah ke nomor tersebut.</p>
    </div>"""

    return kepala(
        "Kontak dan pembayaran, Perfect Flowers",
        "Nomor WhatsApp, alamat pengambilan, rekening BCA, QRIS, dan ketentuan pemesanan Perfect Flowers.",
        "kontak",
        "/kontak/",
    ) + f"""
<div class="page-head">
  <div class="wrap">
    <p class="label" data-nomor="01">Kontak</p>
    <h1>Order, tanya stok, dan pembayaran.</h1>
    <p>Semua pesanan diproses lewat WhatsApp supaya isi kartu ucapan dan jam ambil bisa langsung dikonfirmasi.</p>
  </div>
</div>
<section style="padding-top:0.4rem">
  <div class="wrap kontak__isi">
    <div style="display:grid;gap:clamp(1rem,2.4vw,1.4rem)">
      {kartu_wa}
      <div class="kartu-info">
        <h2>Alamat pengambilan</h2>
        <address>{escape(SITE["alamat"])}<br>{escape(SITE["petunjuk"])}</address>
        <p style="margin-top:1rem"><a class="tautan" href="{escape(SITE["maps"])}">Buka Google Maps</a></p>
      </div>
      <div class="kartu-info">
        <h2>Pembayaran DP</h2>
        <p>DP minimal {SITE["dp_persen"]}%, sisanya dibayar saat ambil.</p>
        <div class="rekening">
          <dl>
            <dt>Bank</dt><dd>{escape(SITE["bank"]["nama"])}</dd>
            <dt>Nomor</dt><dd>{escape(SITE["bank"]["nomor"])}</dd>
            <dt>Atas nama</dt><dd>{escape(SITE["bank"]["atas_nama"])}</dd>
          </dl>
        </div>
        <p class="teks-kecil">QRIS tersedia, minta kode saat order.</p>
      </div>
    </div>
    <div style="display:grid;gap:clamp(1rem,2.4vw,1.4rem)">
      <div class="kartu-info" id="ketentuan">
        <h2>Ketentuan pemesanan</h2>
        <ul class="catatan" style="border-top:0;margin-top:0.4rem">
          <li><b>DP {SITE["dp_persen"]}%</b> dibayar setelah form fix order diisi, bukan saat tanya-tanya.</li>
          <li><b>DP tidak dapat dikembalikan</b> bila order dibatalkan sepihak, karena bunga dan material sudah disiapkan.</li>
          <li><b>Jenis bunga</b> menyesuaikan stok hari pengerjaan. Hasil diusahakan mirip foto, sekitar 90%.</li>
          <li><b>Bukti transfer</b> dikirim lewat chat supaya pesanan langsung masuk daftar kerja.</li>
        </ul>
        <p style="margin-top:1rem"><a class="tautan" href="/#ketentuan">Baca ketentuan lengkap dan posternya</a></p>
      </div>
      <div class="kartu-info">
        <h2>Sebelum order</h2>
        <p>Lihat dulu daftar harga dan foto buket pada tiap harga, supaya pilihan dan budget langsung cocok.</p>
        <p style="margin-top:1rem"><a class="tautan" href="/katalog/">Buka katalog</a></p>
      </div>
    </div>
  </div>
</section>
""" + kaki()


def halaman_404():
    return kepala("Halaman tidak ditemukan, Perfect Flowers",
                  "Halaman yang kamu cari tidak ada.", "beranda", "/404.html") + """
<section class="hero">
  <div class="wrap">
    <p class="label" data-nomor="404">Tidak ditemukan</p>
    <h1>Halaman ini tidak ada.</h1>
    <p class="hero__teks">Mungkin tautannya salah ketik, atau buketnya sudah diganti harga baru.</p>
    <div class="hero__aksi">
      <a class="tombol" href="/katalog/">Lihat katalog</a>
      <a class="tombol tombol--outline" href="/">Kembali ke beranda</a>
    </div>
  </div>
</section>
""" + kaki()


# ---------------------------------------------------------------- main

def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)

    foto, lembar = siapkan_gambar()

    tier = {}
    for f in foto:
        # potongan pricelist untuk harga di SEMBUNYI sudah dilewati di siapkan_gambar
        tier.setdefault(f["harga"], {"foto": []})
        tier[f["harga"]]["foto"].append(f)
    for h in tier:
        # foto satuan (utama=0) tampil lebih dulu, jadi dipakai sebagai foto utama
        tier[h]["foto"].sort(key=lambda f: (f.get("utama", 1), f["berkas"]))

    dist_aset = os.path.join(DIST, "assets")
    shutil.copytree(os.path.join(ROOT, "assets", "css"), os.path.join(dist_aset, "css"))
    shutil.copytree(os.path.join(ROOT, "assets", "js"), os.path.join(dist_aset, "js"))

    tulis("index.html", halaman_beranda(tier))
    tulis("katalog/index.html", halaman_katalog(tier, lembar))
    tulis("katalog/foto/index.html", halaman_katalog_foto(lembar, tier))
    for h in sorted(tier):
        tulis("katalog/%s/index.html" % slug(h), halaman_produk(tier, h))
    tulis("tentang/index.html", halaman_tentang(tier))
    tulis("kontak/index.html", halaman_kontak(tier))
    tulis("404.html", halaman_404())

    if SITE.get("url"):
        url = SITE["url"].rstrip("/")
        halaman = ["/", "/katalog/", "/katalog/foto/", "/tentang/", "/kontak/"] + [
            "/katalog/%s/" % slug(h) for h in sorted(tier)
        ]
        isi = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for p in halaman:
            isi.append("  <url><loc>%s%s</loc></url>" % (url, p))
        isi.append("</urlset>")
        tulis("sitemap.xml", "\n".join(isi) + "\n")
        tulis("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % url)
    else:
        tulis("robots.txt", "User-agent: *\nAllow: /\n")

    jumlah = sum(len(v["foto"]) for v in tier.values())
    print("Selesai. %d halaman, %d produk, %d foto, %d lembar katalog." % (
        6 + len(tier), len(tier), jumlah, len(lembar)))
    if not (SITE.get("wa") or "").strip():
        print("PERHATIAN: nomor WhatsApp masih kosong di data/site.json.")
        print("           Tombol order sementara mengarah ke /kontak/.")
    if not SITE.get("url"):
        print("Catatan: kolom url kosong, sitemap.xml tidak dibuat.")


if __name__ == "__main__":
    main()
