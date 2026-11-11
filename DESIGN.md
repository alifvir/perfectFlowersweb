# DESIGN.md — Perfect Flowers (situs statis)

Arahan desain untuk `perfect-flowers-web`. Dibaca bersama skill `antislop` sebagai filter.

## Dial

ENERGY 3 / RHYTHM 3 / MOTION 1

- ENERGY 3: berwarna, karena logo toko memang berwarna (lavender, koral, pink, ungu, sage, emas). Warna masuk lewat latar section dan penanda, bukan lewat animasi.
- RHYTHM 3: komposisi antar section sengaja berbeda (split, grid rapat, panel ungu gelap penuh, dua kolom teks dan poster, pita krem).
- MOTION 1: hanya hover dan transisi 120ms. Tidak ada animasi saat scroll.

## Palet dari logo

Logo toko (bulatan lavender dengan busur emas, mawar koral/pink/kuning/ungu, dan daun sage) adalah sumber seluruh warna. Tidak ada warna di luar daftar ini.

| Token | Nilai | Asal di logo | Dipakai untuk |
|---|---|---|---|
| paper | #FBF8F6 | kertas putih hangat | latar dasar |
| card | #FFFCF9 | kertas kartu | kartu, rekening, bingkai foto |
| ink | #241C2B | teks hitam logo | teks utama, garis |
| ink-2 | #463550 | bayangan mawar ungu | panel gelap dan footer |
| coral | #B5462F | mawar koral | tombol utama, harga, kata ditekankan |
| coral-deep | #8F3524 | koral tua | hover tombol |
| rose | #E3A3B7 | mawar pink | kelompok harga menengah, bilah kartu |
| rose-deep | #8D4258 | pink tua | teks di latar blush, tombol saring aktif |
| plum | #5B4673 | mawar ungu | tautan, hover, kelompok harga besar |
| lilac | #CCC4D3 | latar bulatan logo | kelompok harga kecil (netral), garis kartu |
| gold | #7C5E1B | busur emas | nomor urut section |
| sage | #456B57 | daun sage tua | kelompok harga di bawah 100 ribu |
| sage-soft | #9CBFAC | daun sage muda | garis kartu, batas tombol saring |
| muted | #6A5D70 | abu ungu | teks penjelas |
| line | #E6DCE7 | garis tipis | garis rambut |

Latar section memakai versi sangat muda dari warna logo: `--wash-lilac` (hero), `--wash-sage` (pembayaran), `--wash-blush` (ketentuan), `--wash-butter` (lokasi). Tujuannya memberi ritme warna antar section tanpa menambah warna baru.

Semua pasangan teks sudah dicek kontras minimum 4.5:1 di atas paper dan keempat wash (nilai terendah: koral 4.65, emas 4.34 untuk angka kecil 0.85rem), dan teks terang di panel ungu 5.5:1 ke atas.

## Aturan warna

- Satu aksen utama: koral. Dipakai di tombol, harga, dan satu kata yang ditekankan di judul. Bukan di garis, ikon, dan latar sekaligus.
- Warna kelompok harga punya arti, bukan hiasan: sage = di bawah 100 ribu, rose = 100 sampai 200 ribu, lilac/ungu = di atas 200 ribu. Warna yang sama dipakai di tombol saring dan garis bawah foto kartu, jadi pengunjung bisa menebak kelompok harga sebelum membaca angkanya.
- Ungu tua dipakai sebagai panel (cara order dan footer), menggantikan cokelat gelap lama, supaya satu keluarga dengan mawar ungu di logo.
- Nomor urut section memakai emas, menggemakan busur emas di logo.

## Tipografi

- Judul: Fraunces (serif variabel), kenapa: bunga dan momen personal lebih cocok dengan serif.
- Teks: Plus Jakarta Sans, kenapa: netral, x-height besar, nyaman di layar HP untuk pembeli yang membuka dari WhatsApp.
- Skala: judul hero clamp(2.5rem, 7vw, 4.3rem), line-height 1.06, letter-spacing -0.02em. Judul section clamp(1.7rem, 3.4vw, 2.5rem).

## Motif identitas

- Nomor section editorial: `01 / Pilihan buket`, `02 / Cara order`, dan seterusnya, dengan garis rambut di bawahnya, angka berwarna emas.
- Logo bulat dipakai apa adanya di header, footer, dan favicon. Wordmark teks di sebelahnya hanya untuk keterbacaan, bukan pengganti logo.

## Aturan yang dipegang

- Tidak ada statistik, testimoni, atau logo klien karangan. Angka yang tampil hanya harga dan ketentuan nyata dari T&C.
- Foto produk adalah foto asli dari pricelist toko, bukan stok foto.
- Ketentuan pemesanan tampil di beranda (`#ketentuan`), bukan disembunyikan di halaman kontak.
- Tidak ada em dash di seluruh teks.
- Tidak ada emoji di teks situs.
- Setiap tautan punya tujuan nyata, tidak ada tombol mati.
- Tidak ada gradien dekoratif, orb blur, atau bayangan berlapis. Satu-satunya bayangan ada di tombol WhatsApp melayang, karena ia harus terangkat di atas konten yang bergulir.
- Tautan WhatsApp membuka tab baru (target blank, rel noopener) supaya pengunjung tidak kehilangan halaman yang sedang dibaca.
- Nomor WhatsApp yang belum diisi tidak dirender sebagai tautan mati, melainkan tombol ke halaman Kontak.
