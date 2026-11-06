# Tutorial deploy ke Cloudflare Pages

Pilih satu route. Route A paling cepat dan tanpa terminal. Route B dipakai kalau mau deploy ulang lewat satu perintah.

Situs ini statis murni: yang diunggah hanya isi folder `dist/`. Tidak ada build step di Cloudflare, tidak ada environment variable, tidak ada database.

Yang akan didapat: alamat `https://<nama-proyek>.pages.dev` yang bisa dibuka dari mana saja, gratis. Untuk proyek ini hasilnya https://perfectflowersweb.pages.dev

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

## Route C: GitHub + deploy otomatis

Urutannya wajib begini: **repo GitHub dulu, proyek Pages belakangan.** Proyek Pages yang dibuat lewat upload atau `wrangler pages deploy` adalah proyek Direct Upload, dan Direct Upload tidak bisa dihubungkan ke GitHub selamanya. Kalau telanjur, harus buat proyek Pages baru.

1. Repo lokal disiapkan di `D:\Alif\Project\perfect-flowers-web` (sudah di-`git init`, commit pertama sudah ada, `dist/` diabaikan karena Cloudflare yang membangun).
2. Buat repo kosong di https://github.com/new. Nama `perfectFlowersweb`, pilih **Private**, dan **jangan** centang "Add a README file" supaya tidak perlu merge.
3. Hubungkan dan dorong:

```bash
cd /d/Alif/Project/perfect-flowers-web
git remote add origin https://github.com/<username>/perfect-flowers-web.git
git push -u origin main
```

4. Cloudflare: **Workers & Pages** > **Create** > tab **Pages** > **Connect to Git** > pilih GitHub > izinkan akses > pilih repo > **Begin setup**.
5. Isi setelan build persis seperti ini:

| Kolom | Nilai |
|---|---|
| Project name | `perfectflowersweb` |
| Production branch | `main` |
| Framework preset | None |
| Build command | `pip install -r requirements.txt && python build.py` |
| Build output directory | `dist` |
| Root directory | (kosongkan) |
| Environment variables | tidak perlu |

Build image Cloudflare versi 3 sudah menyediakan Python 3.13 dan pip, jadi Pillow terpasang saat build.

6. **Save and Deploy**. Tunggu log build selesai (biasanya di bawah satu menit), lalu buka `https://perfectflowersweb.pages.dev`.
7. Update seterusnya cukup `git push`. Cloudflare membangun ulang sendiri, dan tiap push ke branch lain menghasilkan preview deployment dengan alamat sendiri.
8. Untuk proyek yang sudah terhubung Git, deploy manual masih bisa dengan `npx wrangler@latest pages deploy dist --project-name perfect-flowers`, tapi jalur normalnya adalah push.

### Kalau build di Cloudflare gagal

Paling sering karena Pillow tidak bisa dipasang dari PyPI saat build. Jalan keluar darurat: hapus baris `dist/` dari `.gitignore`, commit folder `dist` yang sudah jadi, lalu ubah build command menjadi `exit 0` (build directory tetap `dist`). Dengan begitu Cloudflare hanya menyajikan berkas yang sudah dibangun di laptop.

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
