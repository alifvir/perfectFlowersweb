// Perfect Flowers: menu mobile dan penyaring katalog. Tanpa library.

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
