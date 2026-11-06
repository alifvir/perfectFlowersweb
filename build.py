"""Build situs statis Perfect Flowers.

Sumber data:
  data/site.json   identitas toko, nomor WA, rekening, alamat
  assets-src/g*.jpeg  grid pricelist asli toko (foto buket + harga)
  assets-src/photos-35k.jpeg, assets-src/qris.jpeg, assets-src/patokan-maps.jpeg

Hasil: dist/ siap diunggah ke Cloudflare Pages.

Jalankan: python build.py
"""

import json
import os
import shutil
from html import escape

from PIL import Image

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

# Tinggi potongan per grid. Label harga di pricelist letaknya beda-beda,
# jadi sel dengan label lebih tinggi dipotong lebih dalam agar label tidak ikut.
POTONG = {"g1": 0.76, "g2": 0.76, "g3": 0.76, "g4": 0.64, "g5": 0.76, "g6": 0.72}

PILIHAN_BERANDA = [35000, 50000, 65000, 110000, 150000, 170000, 235000, 350000]

SITE = json.load(open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8"))


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

def siapkan_gambar():
    """Potong tiap sel pricelist jadi foto produk, buang label harga di bawah."""
    if os.path.isdir(IMG):
        shutil.rmtree(IMG)
    os.makedirs(IMG, exist_ok=True)

    foto = []
    for nama, (cols, rows, harga) in GRIDS.items():
        sumber = os.path.join(SRC, nama + ".jpeg")
        im = Image.open(sumber).convert("RGB")
        W, H = im.size
        cw, ch = W / cols, H / rows
        for indeks, harga_sel in enumerate(harga):
            r, c = divmod(indeks, cols)
            potong = POTONG.get(nama, 0.76)
            kotak = (int(c * cw), int(r * ch), int((c + 1) * cw), int(r * ch + ch * potong))
            sel = im.crop(kotak)
            lebar = min(640, sel.width * 2)
            sel = sel.resize((lebar, round(sel.height * lebar / sel.width)), Image.LANCZOS)
            berkas = "%s-%d.webp" % (nama, indeks + 1)
            sel.save(os.path.join(IMG, berkas), "WEBP", quality=82, method=6)
            foto.append({
                "berkas": "assets/img/" + berkas,
                "harga": harga_sel,
                "alt": "Contoh buket %s buatan Perfect Flowers" % rupiah(harga_sel),
                "w": sel.width,
                "h": sel.height,
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

    return foto


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


IKON_WA = ('<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false">'
           '<path fill="currentColor" d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38c1.45.79 3.08 1.21 4.79 1.21h.01c5.46 0 9.91-4.45 9.91-9.91C21.96 6.45 17.5 2 12.04 2Zm5.8 14.13c-.24.68-1.4 1.3-1.93 1.35-.53.05-1.02.24-3.44-.72-2.93-1.15-4.75-4.2-4.9-4.4-.14-.2-1.16-1.55-1.16-2.96 0-1.4.73-2.09 1-2.38.26-.29.58-.36.77-.36l.56.01c.18 0 .42-.07.65.5.24.58.82 2 .89 2.14.07.14.12.31.02.5-.1.2-.15.32-.29.49-.15.17-.31.38-.44.51-.15.14-.3.3-.13.59.17.29.75 1.24 1.62 2.01 1.11.99 2.05 1.3 2.34 1.44.29.15.46.12.63-.07.17-.2.73-.85.93-1.14.19-.29.39-.24.65-.14.26.09 1.66.78 1.94.93.29.14.48.22.55.34.07.13.07.73-.17 1.41Z"/></svg>')


def tombol_wa_melayang():
    """Tombol WhatsApp tetap di pojok kanan bawah supaya selalu bisa dijangkau."""
    tautan = wa_tautan()
    if not tautan:
        return ""
    return ('<a class="wa-melayang" href="%s" target="_blank" rel="noopener" '
            'aria-label="Chat WhatsApp Perfect Flowers">%s</a>' % (escape(tautan), IKON_WA))


def kepala(judul, deskripsi, aktif, kanonikal=""):
    fav = '/assets/favicon.svg'
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
<link rel="icon" href="{fav}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<a class="skip" href="#utama">Lewati ke isi utama</a>
<header class="site-head">
  <div class="wrap">
    <div class="site-head__row">
      <a class="merek" href="/">Perfect Flowers<span>Tangerang</span></a>
      <button class="nav-tombol" type="button" data-nav-tombol aria-expanded="false" aria-controls="nav-utama">
        <span class="nav-tombol__garis" aria-hidden="true"></span> Menu
      </button>
      <nav class="nav" id="nav-utama" data-nav data-terbuka="false" aria-label="Navigasi utama">
        <ul>
          {nav_aktif(aktif, "katalog", "/katalog/", "Katalog")}
          {nav_aktif(aktif, "cara", "/#cara-order", "Cara order")}
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
    <div class="site-foot__isi">
      <div>
        <h2>{escape(SITE["brand"])}</h2>
        <p>Buket bunga yang dirakit setelah order fix, diambil di Tangerang.</p>
        <p class="teks-kecil">{escape(SITE["tagline"])}</p>
      </div>
      <div>
        <h2>Halaman</h2>
        <ul>
          <li><a href="/katalog/">Katalog buket</a></li>
          <li><a href="/#cara-order">Cara order</a></li>
          <li><a href="/tentang/">Tentang</a></li>
          <li><a href="/kontak/">Kontak dan pembayaran</a></li>
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
<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def kartu_produk(foto, harga, kelas_extra=""):
    return f"""<article class="kartu" data-harga="{harga}"{kelas_extra}>
  <a class="kartu__tautan" href="/katalog/{slug(harga)}/">
    <img src="/{foto['berkas']}" alt="{escape(foto['alt'])}" width="{foto['w']}" height="{foto['h']}" loading="lazy" decoding="async">
    <div class="kartu__meta">
      <h3 class="kartu__nama">Buket {harga // 1000}K</h3>
      <p class="kartu__harga">{rupiah(harga)}</p>
    </div>
  </a>
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
      <p class="teks-kecil">DP tidak dapat dikembalikan bila order dibatalkan sepihak, karena bunga dan material sudah disiapkan untuk pesanan tersebut.</p>
    </div>
    <div class="qris">
      <img src="/assets/img/qris.webp" alt="Kode QRIS Perfect Flowers untuk pembayaran DP" width="720" height="720" loading="lazy" decoding="async">
      <p class="teks-kecil">Pindai dengan aplikasi bank atau e-wallet, lalu kirim bukti transfer lewat WhatsApp.</p>
    </div>
  </div>
</section>

<section class="lokasi">
  <div class="wrap lokasi__isi">
    <img src="/assets/img/lokasi.webp" alt="Patokan lokasi pengambilan buket Perfect Flowers di Gg. Peluru No.23 Tangerang" width="900" height="900" loading="lazy" decoding="async">
    <div>
      <p class="label" data-nomor="04">Lokasi</p>
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


def halaman_katalog(tier):
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
  </div>
</section>
""" + kaki()


def halaman_produk(tier, harga):
    data = tier[harga]
    lain = [h for h in sorted(tier) if h != harga]
    lain.sort(key=lambda h: abs(h - harga))
    terkait = "".join(kartu_produk(tier[h]["foto"][0], h) for h in lain[:4])
    galeri = "".join(
        '<img src="/%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async">'
        % (f["berkas"], escape(f["alt"]), f["w"], f["h"])
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
        <img src="/{data['foto'][0]['berkas']}" alt="{escape(data['foto'][0]['alt'])}" width="{data['foto'][0]['w']}" height="{data['foto'][0]['h']}" fetchpriority="high" decoding="async">
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
      <div class="kartu-info">
        <h2>Ketentuan pemesanan</h2>
        <ul class="catatan" style="border-top:0;margin-top:0.4rem">
          <li><b>DP {SITE["dp_persen"]}%</b> dibayar setelah form fix order diisi, bukan saat tanya-tanya.</li>
          <li><b>DP tidak dapat dikembalikan</b> bila order dibatalkan sepihak, karena bunga dan material sudah disiapkan.</li>
          <li><b>Jenis bunga</b> menyesuaikan stok hari pengerjaan. Hasil diusahakan mirip foto, sekitar 90%.</li>
          <li><b>Bukti transfer</b> dikirim lewat chat supaya pesanan langsung masuk daftar kerja.</li>
        </ul>
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


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Perfect Flowers">
<rect width="64" height="64" rx="14" fill="#5c3120"/>
<text x="32" y="43" font-family="Georgia, serif" font-size="30" fill="#fbf7f1" text-anchor="middle">PF</text>
</svg>
"""


# ---------------------------------------------------------------- main

def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)

    foto = siapkan_gambar()

    tier = {}
    for f in foto:
        tier.setdefault(f["harga"], {"foto": []})
        tier[f["harga"]]["foto"].append(f)
    for h in tier:
        tier[h]["foto"].sort(key=lambda f: f["berkas"])

    dist_aset = os.path.join(DIST, "assets")
    shutil.copytree(os.path.join(ROOT, "assets", "css"), os.path.join(dist_aset, "css"))
    shutil.copytree(os.path.join(ROOT, "assets", "js"), os.path.join(dist_aset, "js"))
    tulis("assets/favicon.svg", FAVICON)

    tulis("index.html", halaman_beranda(tier))
    tulis("katalog/index.html", halaman_katalog(tier))
    for h in sorted(tier):
        tulis("katalog/%s/index.html" % slug(h), halaman_produk(tier, h))
    tulis("tentang/index.html", halaman_tentang(tier))
    tulis("kontak/index.html", halaman_kontak(tier))
    tulis("404.html", halaman_404())

    if SITE.get("url"):
        url = SITE["url"].rstrip("/")
        halaman = ["/", "/katalog/", "/tentang/", "/kontak/"] + [
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
    print("Selesai. %d halaman, %d produk, %d foto." % (5 + len(tier), len(tier), jumlah))
    if not (SITE.get("wa") or "").strip():
        print("PERHATIAN: nomor WhatsApp masih kosong di data/site.json.")
        print("           Tombol order sementara mengarah ke /kontak/.")
    if not SITE.get("url"):
        print("Catatan: kolom url kosong, sitemap.xml tidak dibuat.")


if __name__ == "__main__":
    main()
