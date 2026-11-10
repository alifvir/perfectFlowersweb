// Perfect Flowers: menu mobile, penyaring katalog, dan pembesar foto. Tanpa library.

(function () {
  var tombol = document.querySelector("[data-nav-tombol]");
  var nav = document.querySelector("[data-nav]");
  if (tombol && nav) {
    tombol.addEventListener("click", function () {
      var buka = nav.getAttribute("data-terbuka") === "true";
      nav.setAttribute("data-terbuka", buka ? "false" : "true");
      tombol.setAttribute("aria-expanded", buka ? "false" : "true");
    });
  }

  // --- foto ukuran penuh -------------------------------------------------
  var dialog = null;
  var gambar = null;
  var keterangan = null;

  function siapkanLightbox() {
    if (dialog) return;
    dialog = document.createElement("dialog");
    dialog.className = "lightbox";
    dialog.setAttribute("aria-label", "Foto ukuran penuh");

    var tutup = document.createElement("button");
    tutup.type = "button";
    tutup.className = "lightbox__tutup";
    tutup.setAttribute("aria-label", "Tutup foto");
    tutup.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" ' +
      'stroke="currentColor" stroke-width="1.9" stroke-linecap="round">' +
      '<path d="M6 6l12 12M18 6L6 18"/></svg>';
    tutup.addEventListener("click", function () { dialog.close(); });

    gambar = document.createElement("img");
    gambar.decoding = "async";

    keterangan = document.createElement("p");
    keterangan.className = "lightbox__ket";

    dialog.appendChild(tutup);
    dialog.appendChild(gambar);
    dialog.appendChild(keterangan);
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog) dialog.close();
    });
    document.body.appendChild(dialog);
  }

  document.addEventListener("click", function (e) {
    var pemicu = e.target.closest("[data-zoom]");
    if (!pemicu) return;
    e.preventDefault();
    siapkanLightbox();
    var src = pemicu.getAttribute("data-foto");
    if (!src) {
      var img = pemicu.querySelector("img");
      if (!img) return;
      src = img.getAttribute("src");
    }
    gambar.src = src;
    gambar.alt = pemicu.getAttribute("data-alt") || "";
    keterangan.textContent = gambar.alt;
    dialog.showModal();
  });

  var saring = document.querySelector("[data-saring]");
  var daftar = document.querySelector("[data-daftar-produk]");
  var hitung = document.querySelector("[data-hitung]");
  if (!saring || !daftar) return;

  var kartu = Array.prototype.slice.call(daftar.querySelectorAll("[data-harga]"));
  var tombolSaring = Array.prototype.slice.call(saring.querySelectorAll("button"));

  function terapkan(batas, label) {
    var tampil = 0;
    kartu.forEach(function (el) {
      var harga = parseInt(el.getAttribute("data-harga"), 10);
      var cocok = batas === "semua" || (batas === "kecil" && harga < 100000) ||
        (batas === "sedang" && harga >= 100000 && harga < 200000) ||
        (batas === "besar" && harga >= 200000);
      el.hidden = !cocok;
      if (cocok) tampil += 1;
    });
    tombolSaring.forEach(function (b) {
      b.setAttribute("aria-pressed", b === label ? "true" : "false");
    });
    if (hitung) hitung.textContent = tampil + " buket ditampilkan";
  }

  tombolSaring.forEach(function (b) {
    b.addEventListener("click", function () {
      terapkan(b.getAttribute("data-batas"), b);
    });
  });

  terapkan("semua", tombolSaring[0]);
})();
