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
| `dist/` | Hasil build, inilah yang diunggah |
| `tools/audit.py` | Pemeriksa hasil build: tautan mati, alt, jumlah h1, em dash |
| `DESIGN.md` | Arah desain, palet, dial, dan alasannya |
| `DEPLOY.md` | Langkah isi nomor WA dan deploy ke Cloudflare Pages |

## Halaman yang dihasilkan

- `/` beranda
- `/katalog/` daftar 23 harga dengan penyaring budget
- `/katalog/buket-<harga>k/` 23 halaman detail, satu per harga
- `/tentang/`
- `/kontak/`
- `/404.html`

## Perintah

```bash
python build.py        # bangun ulang dist/
python tools/audit.py  # periksa hasil build
python -m http.server 8099 -d dist   # pratinjau lokal di http://127.0.0.1:8099
```

Butuh Python 3.10+ dan Pillow (`pip install pillow`).

## Sumber data

- Harga dan foto: `D:\Alif\Project\pricelist` (6 grid pricelist, 51 foto buket, harga 35 ribu sampai 700 ribu)
- Ketentuan pemesanan: T&C toko (DP 50%, DP tidak dapat dikembalikan, kemiripan sekitar 90%)
- Rekening dan QRIS: BCA 8670697011 a.n. ELI NOFIYANTI, QRIS atas nama PERFECT FLOWERS, CIPONDOH
- Alamat pengambilan: Gg. Peluru No.23, Tangerang

Semua foto di situs adalah foto buket asli toko. Tidak ada foto stok, tidak ada statistik atau testimoni karangan.
