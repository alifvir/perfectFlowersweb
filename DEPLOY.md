# Cara deploy dan mengisi data

Situs ini statis murni: tidak ada database, tidak ada server. Semua halaman dihasilkan `build.py` ke folder `dist/`, lalu `dist/` diunggah apa adanya.

## 1. Isi nomor WhatsApp (wajib sebelum online)

Buka `data/site.json`, isi kolom `wa`:

```json
"wa": "085157226960"
```

Boleh format `08xx` atau `628xx`, keduanya dirapikan otomatis. Setelah itu jalankan:

```bash
python build.py
```

Selama `wa` masih kosong, semua tombol order mengarah ke halaman Kontak dan halaman itu menampilkan placeholder. Setelah diisi, tombol berubah menjadi tautan WhatsApp dengan pesan pembuka yang sudah terisi.

## 2. Isi alamat domain (opsional, untuk sitemap)

Setelah punya domain, isi kolom `url` di `data/site.json`, contoh `"https://perfectflowers.id"`, lalu build ulang. `sitemap.xml` dan baris `Sitemap:` di `robots.txt` baru dibuat kalau kolom ini terisi. Tanpa domain, keduanya dilewati.

## 3. Deploy ke Cloudflare Pages

Cara yang dipakai sekarang: proyek Pages terhubung ke repo GitHub `alifvir/perfectFlowersweb`, jadi setiap `git push` ke `main` memicu build dan deploy otomatis.

- Alamat produksi: https://perfectflowersweb.pages.dev
- Project name Cloudflare: `perfectflowersweb`
- Build command: `pip install -r requirements.txt && python build.py`
- Build output directory: `dist`

Deploy manual (jarang perlu):

```bash
git add -A && git commit -m "..." && git push
```

### Cara lain, tanpa Git (kalau proyek Pages dibuat dengan Direct Upload)

Cara tercepat, tanpa CLI:

1. Buka Cloudflare Dashboard, menu Workers and Pages, lalu Create, tab Pages, pilih Upload assets.
2. Tarik seluruh isi folder `dist/` ke sana.
3. Selesai. Situs langsung dapat alamat `nama-proyek.pages.dev`.

Cara CLI, kalau ingin ulang deploy tiap ada perubahan:

```bash
npx wrangler pages deploy dist --project-name perfect-flowers
```

Domain sendiri: tab Custom domains di proyek Pages, tambahkan domain, lalu ikuti instruksi DNS dari Cloudflare.

## 4. Memperbarui isi

- Harga dan foto: `build.py` membaca harga langsung dari `GRIDS` (harga per sel di tiap foto pricelist) di bagian atas berkas. Kalau ada price list baru, simpan fotonya ke `assets-src/` dengan nama `gN.jpeg`, lalu perbarui daftar harga di `GRIDS` sesuai label harga pada tiap sel, urut baris demi baris kiri ke kanan.
- Teks halaman: ada di fungsi `halaman_beranda`, `halaman_katalog`, `halaman_produk`, `halaman_tentang`, `halaman_kontak` dalam `build.py`.
- Rekening, QRIS, alamat, petunjuk lokasi: `data/site.json` dan `assets-src/qris.jpeg`, `assets-src/patokan-maps.jpeg`.
- Setelah mengubah apa pun: `python build.py`, lalu periksa dengan `python tools/audit.py` (memeriksa tautan mati, alt, judul, dan em dash).

## 5. Yang perlu diketahui

- Harga di situs ini diambil dari pricelist foto toko. Kalau harga berubah, situs tidak ikut berubah sendiri. Ubah `GRIDS` lalu build ulang.
- Nomor rekening dan QRIS tampil publik karena memang dipakai untuk pembayaran DP.
- Foto produk dipotong otomatis dari grid pricelist, label harga aslinya ikut terbuang. Nilai potongan per grid ada di `POTONG`.
- Tidak ada form order di situs. Order tetap lewat WhatsApp dengan FORM FIX ORDER yang sudah dipakai.
