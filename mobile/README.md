# AquaSmart Mobile (Flutter)

Aplikasi Android pendamping dashboard web. Tidak semua fitur web dibuat versi
mobile. Yang ada di aplikasi:

| Layar | Isi | Endpoint backend |
| --- | --- | --- |
| Masuk | Login dengan email atau nomor HP | `POST /api/auth/login` |
| Kolam | Daftar perangkat, status online, bacaan terakhir dibanding batas aman | `GET /api/devices`, `GET /api/settings/thresholds` |
| Detail kolam | Bacaan terakhir, grafik pH, suhu, atau kekeruhan dari 50 bacaan terakhir | `GET /api/devices/{id}/readings` |
| Kontrol | Aerator nyala/mati, beri pakan 1-10 detik, mode otomatis, 5 perintah terakhir | `POST /api/devices/{id}/control`, `GET /api/devices/{id}/commands` |
| Peringatan | Daftar alert, tandai sudah dibaca, badge jumlah belum dibaca | `GET /api/alerts`, `PATCH /api/alerts/{id}/acknowledge` |

Daftar akun, klaim perangkat, jadwal pakan, threshold, laporan, ekspor, dan
observasi pertumbuhan tetap di dashboard web.

Kontrol mengikuti perilaku backend. Perintah masuk antrian, lalu status aerator
baru berubah setelah firmware mengirim ack. Layar kontrol memuat peringatan yang
sama dengan web: status Berhasil bukan bukti relay atau motor bergerak. Akun
non-admin hanya melihat status.

## Menjalankan

Butuh Flutter 3.47 dan Android SDK 36. Dari folder `mobile/`:

```bash
flutter pub get
flutter test
flutter run
```

Alamat server ditentukan saat build lewat `AQUASMART_API_URL`. Bawaannya
`http://10.0.2.2:8080`, yaitu komputer host dilihat dari emulator Android, tempat
backend berjalan dengan `docker compose up` (lihat `../Backend/README.md`).

Untuk HP di jaringan Wi-Fi yang sama dengan komputer backend, ganti dengan IP
komputer itu:

```bash
flutter build apk --release --dart-define=AQUASMART_API_URL=http://192.168.1.10:8080
```

HTTP tanpa TLS diizinkan (`usesCleartextTraffic`) karena AquaSmart dirancang
berjalan di komputer pembudidaya di jaringan lokal. Alamat HTTPS juga bisa dipakai.

APK release saat ini ditandatangani dengan debug key bawaan Flutter. Cukup untuk
dipasang langsung (sideload), belum untuk Play Store.

Sesi login hanya disimpan di memori. Setelah aplikasi ditutup, pengguna masuk lagi.

## Keputusan desain

Mengikuti `../FrontEnd/DESIGN_SYSTEM.md` supaya aplikasi terasa satu produk dengan
dashboard web. Pembacaan desain: aplikasi pemantauan untuk pembudidaya, bahasa
visual instrumen yang tenang, dial ENERGY 1 / RHYTHM 2 / MOTION 1.

- **Warna:** token web (`ink`, `deep-current`, `foam`, `clear-water-text`,
  `alarm-coral-text`) di `lib/theme.dart`. Hijau berarti aman, oranye berarti di
  luar batas, sama seperti web. Tema terang saja, mengikuti keputusan web.
- **Huruf:** font sistem Android. Segoe UI yang dipakai web tidak ada di Android,
  dan font sistem tidak perlu diunduh. Angka bacaan memakai tabular figures agar sejajar.
- **Fokus layar:** di detail kolam, yang paling besar adalah bacaan terakhir dan
  statusnya, karena keputusan pertama pembudidaya adalah apakah air perlu ditangani.
- **Kartu:** datar dengan garis `foam-line`, tanpa bayangan, seperti panel dashboard web.
- **Ikon:** ikon Material yang maknanya cocok dengan labelnya: tetes air untuk Kolam,
  lonceng untuk Peringatan, panah melingkar untuk Muat ulang. Setiap ikon punya label
  atau tooltip.
- **Grafik:** menjawab satu pertanyaan, yaitu apakah nilai keluar dari batas aman.
  Pita hijau muda adalah batas aman pemilik, dan titik oranye berada di luar batas.
  Sumbu X berisi urutan bacaan, bukan skala waktu, sehingga jarak waktu yang tidak
  sama tidak terlihat.
- **Logo dan ikon peluncur:** digambar ulang dari `../FrontEnd/public/logo.svg`.
  Ikon peluncur memakai latar `deep-current` karena tetes logo berwarna terang.

## Verifikasi (27 Oktober 2026)

- `flutter analyze`: tidak ada masalah. `flutter test`: 12 test lulus, termasuk klien
  API (cookie sesi, CSRF, error, 401, jaringan putus) dan widget (validasi login,
  kredensial salah, kartu kolam aman dan di luar batas, muat ulang, kontrol aerator,
  peringatan).
- Dicoba di emulator `AquaSmart_API36` (Android 36) terhadap backend `docker compose`
  dengan Postgres:
  - Login gagal dan berhasil; daftar kolam; detail kolam dan grafik.
  - Aerator nyala: perintah tercatat Antre. Perintah kedua ditolak dengan pesan
    aktuator sibuk. Beri pakan 6 detik. Mode otomatis.
  - Setelah ack firmware disimulasikan lewat API perangkat, status berubah menjadi
    Berhasil lewat pembaruan otomatis 10 detik.
  - Tandai peringatan sudah dibaca, badge berkurang; keluar.
  - APK release juga dicoba login di emulator.
- Belum diuji di HP fisik, dan belum diuji dengan ESP32 sungguhan.
- Sekali terlihat di emulator: kartu peringatan yang baru ditandai dibaca tampil
  terpotong sampai layar digambar ulang. Penyebabnya belum dipastikan.
