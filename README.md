# Perfect Flowers, situs statis

Situs profil dan katalog untuk Perfect Flowers (Tangerang), dibuat statis supaya bisa di-host gratis di Cloudflare Pages.

Situs live: https://perfectflowersweb.pages.dev (Cloudflare Pages, build otomatis dari repo GitHub setiap push ke `main`).
Git remote: `git@github.com:alifvir/perfectFlowersweb.git`

## Isi

| Path | Fungsi |
|---|---|
| `build.py` | Generator. Memotong foto dari pricelist, lalu menulis seluruh halaman ke `dist/` |
| `data/site.json` | Identitas toko, nomor WhatsApp, rekening, alamat, domain |
| `assets/` | CSS dan JS sumber (disalin ke `dist/assets`) |
| `assets-src/` | Foto pricelist asli, QRIS, patokan lokasi. Tidak ikut terunggah |
| `catalog/` | 8 lembar katalog foto (kolase buket + harga) untuk halaman `/katalog/foto/` |
| `dist/` | Hasil build, inilah yang diunggah |
| `tools/audit.py` | Pemeriksa hasil build: tautan mati, alt, jumlah h1, em dash |
| `DESIGN.md` | Arah desain, palet, dial, dan alasannya |
| `DEPLOY.md` | Langkah isi nomor WA dan deploy ke Cloudflare Pages |

## Halaman yang dihasilkan

- `/` beranda
- `/katalog/` daftar harga dengan penyaring budget
- `/katalog/foto/` 8 lembar katalog foto, ditambah daftar harga yang belum masuk daftar utama
- `/katalog/buket-<harga>k/` halaman detail, satu per harga
- `/tentang/`
- `/kontak/`
- `/404.html`

## Potong foto produk

`build.py` memotong tiap sel pricelist jadi foto produk 4:5 dengan aturan seragam:

- Kotak label harga dideteksi per sel (`_deteksi_label`), lalu dipakai **nilai per baris grid** — label dalam satu baris letaknya sejajar, jadi satu sel yang deteksinya meleset tidak merusak seluruh baris.
- `BATAS_SEL` menampung pengecualian manual untuk label yang tidak terdeteksi otomatis.
- Ukuran potongan mengikuti kotak buket + ruang kosong 10% (`_bingkai`), jadi besar buket di dalam kartu relatif sama antar foto.
- `SEMBUNYI` berisi harga yang diturunkan dari situs; fotonya juga tidak ditulis ke `dist/`.

## Foto satuan (catalog/satuan/)

Foto buket asli per harga. Nama berkas = harganya: `175k.jpeg`, `175k (2).jpeg`, `260k (3).jpeg`.

- Tidak ada label harga di dalam foto, jadi dipotong apa adanya ke 4:5 (`_bingkai_foto`), dipusatkan ke kotak buket dengan ruang kosong 10%.
- Foto satuan jadi **foto utama** untuk harga itu (`utama: 0` → diurutkan paling depan); potongan pricelist tetap muncul di galeri "Foto lain di harga ini".
- Harga yang belum ada di pricelist otomatis dapat halaman sendiri (mis. 80K, 120K, 175K, 260K).
- Harga di `SEMBUNYI` hanya menyembunyikan potongan pricelist; foto satuan tetap tampil. Menambah foto `65k.*` berarti harga itu hidup lagi.

## Ketentuan pemesanan (poster)
`assets-src/tnc.jpeg` (poster asli dari owner) diubah jadi `assets/img/tnc.webp` (1000x1500, q88 — teks kecil butuh kualitas lebih tinggi) dan tampil di `/kontak/#ketentuan`: teks ringkas di kiri, poster di kanan, bisa diklik untuk lightbox ukuran penuh. Ditautkan dari footer ("Ketentuan pemesanan") dan dari catatan di halaman detail buket.

## Foto ukuran penuh

Semua foto produk bisa diklik untuk dibuka besar lewat lightbox `<dialog>` di `site.js` (tanpa library): tombol kaca pembesar di pojok kartu, foto utama dan galeri di halaman detail, tutup dengan Esc / tombol × / klik latar.

## Perintah

```bash
python build.py        # bangun ulang dist/
python tools/audit.py  # periksa hasil build
python tools/serve.py  # pratinjau lokal http://localhost:8098 (404 kustom, tanpa cache)
```

Butuh Python 3.10+ dan Pillow + numpy (`pip install pillow numpy`).

`tools/serve.py` dipakai untuk pratinjau, bukan `http.server` biasa: rute yang tidak ada dibalas `dist/404.html` (sama seperti di Cloudflare Pages), `.webp` dikirim dengan content-type benar, dan respons tidak di-cache sehingga hasil build terbaru langsung terlihat.

## Sumber data

- Harga dan foto: `D:\Alif\Project\pricelist` (6 grid pricelist, 51 foto buket, harga 35 ribu sampai 700 ribu)
- Ketentuan pemesanan: T&C toko (DP 50%, DP tidak dapat dikembalikan, kemiripan sekitar 90%)
- Rekening dan QRIS: BCA 8670697011 a.n. ELI NOFIYANTI, QRIS atas nama PERFECT FLOWERS, CIPONDOH
- Alamat pengambilan: Gg. Peluru No.23, Tangerang

Semua foto di situs adalah foto buket asli toko. Tidak ada foto stok, tidak ada statistik atau testimoni karangan.
