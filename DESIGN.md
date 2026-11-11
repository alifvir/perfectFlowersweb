# DESIGN.md — Perfect Flowers (situs statis)

Arahan desain untuk `perfect-flowers-web`. Dibaca bersama skill `antislop` sebagai filter.

## Dial

ENERGY 3 / RHYTHM 3 / MOTION 1

- ENERGY 3: romantis, bukan manis berlebihan. Warna masuk lewat latar section, busur emas, dan ornamen garis tipis, bukan lewat animasi.
- RHYTHM 3: komposisi antar section sengaja berbeda (split dengan foto melengkung, grid rapat, panel hijau gelap penuh, dua kolom teks dan poster, pita krem).
- MOTION 1: hanya hover dan transisi 120ms. Tidak ada animasi saat scroll.

## Palet dari logo

Logo (kartu nama bulat: monogram PF, mawar blush, eucalyptus sage, busur dan garis emas) adalah sumber seluruh warna. Tidak ada warna di luar daftar ini.

| Token | Nilai | Asal di logo | Dipakai untuk |
|---|---|---|---|
| paper | #FDF8F5 | kertas kartu | latar dasar |
| card | #FFFCFB | kertas kartu | kartu, rekening, bingkai foto |
| ink | #35272A | teks TikTok/IG | teks utama, garis |
| ink-2 | #33453A | daun eucalyptus tua | panel cara order dan footer |
| rose | #A8535A | mawar dusti | tombol utama, harga, kata ditekankan |
| rose-deep | #8E4249 | mawar tua | hover tombol |
| rose-soft | #E2B3AF | kelopak muda | garis kartu, bingkai poster, tombol saring aktif kelompok menengah |
| gold | #82642A | garis emas di logo | nomor urut section |
| gold-soft | #C9B08A | busur emas | busur belakang foto, garis kelompok harga besar, pembatas footer |
| sage | #5F7355 | daun eucalyptus | kelompok harga di bawah 100 ribu |
| sage-soft | #B6C4AA | daun muda | garis kartu, batas tombol saring |
| mauve | #8C6B66 | bayangan mawar | label kecil |
| muted | #7A6663 | teks keterangan di logo | teks penjelas |
| line | #EBDCD8 | garis tipis | garis rambut |

Latar section memakai versi muda dari warna logo: `--wash-blush` (hero), `--wash-sage` (pembayaran), `--wash-pink` (ketentuan), `--wash-butter` (lokasi).

Kontras terukur: teks utama 13.5:1 di atas paper, muted 5.1:1, rose 4.9:1, gold 4.8:1, sage 4.9:1. Di atas wash blush turun sedikit tetap di atas 4.5:1 (kecuali gold 4.4:1 yang hanya dipakai untuk angka 0.95rem, bukan paragraf). Teks terang di panel hijau 5.4:1 ke atas. Tombol rose dengan teks putih 4.9:1.

## Tipografi

- Judul: Cormorant Garamond 600, kenapa: serif kontras tinggi yang sama keluarganya dengan huruf "perfectflowers id" di logo, dan terasa seperti undangan, bukan template SaaS.
- Teks: Plus Jakarta Sans, kenapa: netral, x-height besar, nyaman di HP untuk pembeli yang membuka dari WhatsApp.
- Skala: judul hero clamp(2.4rem, 5.8vw, 4rem) dengan `text-wrap: balance`; judul section clamp(1.9rem, 3.6vw, 2.7rem).

## Ornamen bunga

Semua ornamen garis tipis, warna emas atau rose, tidak pernah mengulang sebagai pola latar:

- **Busur foto**: foto hero dan foto utama halaman detail memakai lengkung atas (radius 999px) seperti jendela toko bunga, dengan satu busur emas tipis 14px di belakangnya. Ini menggemakan lengkung emas di logo.
- **Tangkai eucalyptus** (`IKON_DAUN` di build.py): satu di sudut panel cara order (emas, opacity 0.16) dan satu di section ketentuan (rose, opacity 0.3). Disembunyikan di bawah 900px supaya tidak menabrak teks.
- **Pembatas kuntum**: satu kuntum lima kelopak di antara dua garis rambut, dipakai di atas footer (`pembatas()`).
- **Penanda ketentuan**: kuntum kecil 14px sebelum tiap poin ketentuan di beranda.
- **Logo**: monogram PF di header (kartu penuh tidak terbaca di 46px), kartu penuh di footer dan halaman tentang, monogram sebagai favicon.

Aturan: ornamen tidak boleh menutupi teks, tidak boleh jadi pola berulang, dan tidak menggantikan isi. Bila satu section sudah punya foto bunga (poster T&C), ornamen garis di section itu dibuat seminimal mungkin.

## Aturan yang dipegang

- Tidak ada statistik, testimoni, atau logo klien karangan. Angka yang tampil hanya harga dan ketentuan nyata dari T&C.
- Foto produk adalah foto asli dari pricelist toko, bukan stok foto.
- Ketentuan pemesanan tampil di beranda (`#ketentuan`), bukan disembunyikan di halaman kontak.
- Warna kelompok harga punya arti: sage = di bawah 100 ribu, rose = 100 sampai 200 ribu, gold = di atas 200 ribu. Warna yang sama dipakai di tombol saring dan garis bawah foto kartu.
- Tidak ada em dash di seluruh teks.
- Tidak ada emoji di teks situs.
- Setiap tautan punya tujuan nyata, tidak ada tombol mati.
- Tidak ada gradien dekoratif, orb blur, atau bayangan berlapis. Satu-satunya bayangan ada di tombol WhatsApp melayang.
- Tautan WhatsApp membuka tab baru (target blank, rel noopener).
- Nomor WhatsApp yang belum diisi tidak dirender sebagai tautan mati, melainkan tombol ke halaman Kontak.
