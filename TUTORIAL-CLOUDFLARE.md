# Tutorial deploy ke Cloudflare Pages

Pilih satu route. Route A paling cepat dan tanpa terminal. Route B dipakai kalau mau deploy ulang lewat satu perintah.

Situs ini statis murni: yang diunggah hanya isi folder `dist/`. Tidak ada build step di Cloudflare, tidak ada environment variable, tidak ada database.

Yang akan didapat: alamat `https://<nama-proyek>.pages.dev` yang bisa dibuka dari mana saja, gratis.

---

## Route A: Upload lewat dashboard (tanpa terminal)

1. Buka https://dash.cloudflare.com lalu login (daftar dulu kalau belum punya akun, gratis).
2. Di sidebar kiri pilih **Workers & Pages**.
3. Klik tombol **Create** (di kanan atas), lalu pilih tab **Pages**.
4. Klik **Upload assets**.
5. Isi **Project name**: `perfect-flowers`. Nama ini menjadi bagian alamat, jadi hasilnya `perfect-flowers.pages.dev`. Kalau nama sudah dipakai akun lain, tambahkan sesuatu, misalnya `perfect-flowers-tangerang`.
6. Di kotak upload, **tarik seluruh isi folder `dist`** (bukan foldernya, tapi isinya): `index.html`, `404.html`, `robots.txt`, folder `katalog`, `tentang`, `kontak`, `assets`. Cara paling aman di Windows: buka `D:\Alif\Project\perfect-flowers-web\dist` di File Explorer, tekan Ctrl+A, lalu drag ke kotak upload.
7. Klik **Deploy site**. Tunggu beberapa detik sampai muncul alamat `https://perfect-flowers.pages.dev`.

Buka alamatnya. Kalau halaman tampil tanpa CSS, berarti yang terunggah adalah folder `dist` utuh (bukan isinya). Hapus deployment itu, ulangi langkah 6.

### Kenapa tombolnya ada dua pilihan

- **Upload assets** (Route A): proyek langsung jadi, file diunggah manual tiap kali berubah. Cepat, tapi tidak terhubung ke Git selamanya. Proyek yang dibuat dengan cara ini **tidak bisa** diubah menjadi proyek Git di kemudian hari.
- **Connect to Git**: Cloudflare membangun sendiri dari repo setiap ada push. Cocok kalau nanti situs ini mau dirawat lewat GitHub. Butuh repo dulu, dan build command harus dikosongkan (karena `dist/` sudah jadi), output directory `dist`.

Kalau ragu dan hanya ingin situsnya cepat online, pakai Upload assets.

---

## Route B: Lewat terminal (wrangler)

Sudah dicek di mesin ini: Node v24.18.0, npm 11.16.0, wrangler 4.158.0 bisa dipanggil lewat `npx`, dan belum login.

1. Login sekali saja:

```bash
cd /d/Alif/Project/perfect-flowers-web
npx wrangler@latest login
```

Browser akan terbuka dan meminta izin. Klik **Allow**. Terminal akan menampilkan pesan berhasil.

2. Deploy:

```bash
npx wrangler@latest pages deploy dist --project-name perfect-flowers
```

Pertama kali dijalankan, wrangler menanyakan konfirmasi pembuatan proyek. Jawab `y`. Setelah selesai, terminal menampilkan alamat produksi dan alamat preview per deployment.

3. Deploy berikutnya cukup perintah yang sama. Untuk memasang domain sendiri:

```bash
npx wrangler@latest pages project list
```

lalu tambahkan domain lewat dashboard: **Workers & Pages** > pilih proyek > **Custom domains** > **Set up a custom domain**.

---

## Memperbarui situs setelah ada perubahan

1. Ubah isi situs (misalnya harga, nomor WA, foto), lalu:

```bash
python build.py
python tools/audit.py
```

2. Unggah ulang:
   - Route A: buka proyek Pages, tab **Deployments**, klik **Create new deployment** (atau **Upload assets** lagi), unggah isi `dist` yang baru.
   - Route B: `npx wrangler@latest pages deploy dist --project-name perfect-flowers`

Deployment lama tetap tersimpan dan bisa dikembalikan dari tab Deployments.

---

## Domain sendiri (opsional)

1. Beli domain di registrar mana pun (misalnya .id atau .com).
2. Di dashboard Cloudflare, **Workers & Pages** > proyek > **Custom domains** > **Set up a custom domain**.
3. Kalau domainnya sudah memakai nameserver Cloudflare, cukup tunggu 1 sampai 5 menit. Kalau belum, Cloudflare memberi instruksi CNAME (`perfect-flowers.pages.dev`) untuk dipasang di DNS registrar.
4. Setelah domain aktif, isi kolom `url` di `data/site.json`, jalankan `python build.py`, lalu deploy ulang. Sitemap dan tag canonical baru dibuat setelah kolom itu terisi.

---

## Yang sering bikin gagal

| Gejala | Penyebab | Perbaikan |
|---|---|---|
| Halaman tampil tanpa CSS dan gambar | yang diunggah folder `dist` utuh, jadi `index.html` ada di dalam subfolder | unggah **isi** `dist`, bukan foldernya |
| `/katalog/` jadi 404 | folder `katalog` tidak ikut terunggah | pastikan seluruh isi `dist` terunggah |
| Halaman 404 polos bawaan Cloudflare | `404.html` tidak ada di root | file `404.html` sudah dibuat `build.py`, pastikan ikut terunggah |
| CSS lama masih dipakai setelah update | cache browser, nama berkas CSS tidak memakai hash | hard refresh Ctrl+F5 |
| `wrangler` minta login terus | login tersimpan per pengguna Windows | jalankan `npx wrangler@latest login` sekali lagi |
| Nama proyek ditolak | nama sudah dipakai akun lain | ganti, misalnya `perfect-flowers-tangerang` |

---

## Batas gratis yang relevan

Cloudflare Pages gratis untuk proyek statis dengan jumlah deployment besar per bulan dan bandwidth tidak dibatasi. Untuk situs sekecil ini tidak ada biaya. Yang berbayar adalah fitur lanjutan (misalnya Functions dengan pemakaian berat), dan situs ini tidak memakai Functions sama sekali.
