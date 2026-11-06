# DESIGN.md — Perfect Flowers (situs statis)

Arahan desain untuk `perfect-flowers-web`. Dibaca bersama skill `antislop` sebagai filter.

## Dial

ENERGY 2 / RHYTHM 3 / MOTION 1

- ENERGY 2: hangat dan tenang, bukan halaman kampanye. Buket adalah fokus, bukan animasi.
- RHYTHM 3: komposisi antar section sengaja berbeda (split, grid rapat, panel gelap penuh, dua kolom foto dan teks).
- MOTION 1: hanya hover dan transisi 120ms. Tidak ada animasi saat scroll.

## Kenapa arah ini

Referensi Dribbble (Gift and Flower Shop Landing Page) memakai abu terang, radius besar, dan sans-serif geometris. Itu dipakai sebagai pelajaran ritme (foto besar, panel gelap sebagai pemisah), bukan untuk ditiru. Website ini butuh karakter sendiri: kertas hangat dan tipografi serif, karena produknya bunga dan pembelinya memesan lewat WhatsApp untuk momen pribadi.

## Palet

| Token | Nilai | Alasan |
|---|---|---|
| paper | #FBF7F1 | dasar krem hangat, terasa seperti kertas kado |
| paper-2 | #F3E9DE | pemisah section tanpa garis |
| ink | #1F1613 | teks utama, hitam hangat bukan hitam murni |
| ink-2 | #5C3120 | judul sekunder dan panel gelap (diambil dari palet referensi) |
| clay | #9C5748 | satu-satunya aksen: harga, tautan, tombol |
| muted | #6E5F58 | teks penjelas |
| line | #E3D6C8 | garis rambut |

Dua warna inti (ink, ink-2) plus netral krem, satu aksen (clay). Aksen hanya muncul di harga, CTA, dan penanda section, tidak disebar.

## Tipografi

- Judul: Fraunces (serif variabel), kenapa: bunga dan momen personal lebih cocok dengan serif, dan sans-serif geometris akan membuat situs ini mirip mockup Dribbble yang jadi referensi.
- Teks: Plus Jakarta Sans, kenapa: netral, x-height besar, nyaman di layar HP untuk pembeli yang membuka dari WhatsApp.
- Skala: judul hero clamp(2.6rem, 6vw, 4.3rem), line-height 1.03, letter-spacing -0.02em. Judul section clamp(1.7rem, 3.2vw, 2.4rem).

## Motif identitas

Nomor section editorial: setiap section diberi label `01 / Pilihan buket`, `02 / Cara order`, dan seterusnya, dengan garis rambut di bawahnya. Dipakai konsisten di semua halaman. Ini yang membuat halaman terasa satu keluarga tanpa perlu ornamen.

## Aturan yang dipegang

- Tidak ada statistik, testimoni, atau logo klien karangan. Angka yang tampil hanya harga dan ketentuan nyata dari T&C.
- Foto produk adalah foto asli dari pricelist toko, bukan stok foto.
- Logo memakai wordmark teks, bukan logo karangan.
- Tidak ada em dash di seluruh teks.
- Tidak ada emoji.
- Setiap tautan punya tujuan nyata, tidak ada tombol mati.
- Tombol WhatsApp melayang di pojok kanan bawah: satu-satunya elemen dengan bayangan, karena ia harus terangkat di atas konten yang bergulir. Warnanya memakai aksen clay, bukan hijau WhatsApp, supaya palet tetap satu keluarga.
- Tautan WhatsApp membuka tab baru (target blank, rel noopener) supaya pengunjung tidak kehilangan halaman yang sedang dibaca.
- Nomor WhatsApp yang belum diisi tidak dirender sebagai tautan mati, melainkan tombol ke halaman Kontak.
