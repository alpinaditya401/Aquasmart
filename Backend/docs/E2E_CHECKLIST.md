# E2E_CHECKLIST.md — Uji end-to-end

> Status: **belum dites** (Playwright tersedia di skill webapp-testing,
> tetapi backend & frontend belum di-deploy ke URL publik).

## Prasyarat

- Backend Flask live di `<API>` (Railway).
- Frontend Next.js live di `<WEB>` (Vercel) dengan
  `AQUASMART_API_URL=<API>`.
- Akun admin + 1 device terdaftar dengan device key.

## Checklist

| # | Skenario | Langkah | Hasil |
|---|---|---|---|
| 1 | Login | Buka `<WEB>/login`, isi kredensial admin → dashboard tampil | belum dites |
| 2 | Lihat device | Dashboard menampilkan daftar device + bacaan terakhir | belum dites |
| 3 | Telemetri | (simulasi firmware) POST `/api/devices/<id>/telemetry` dengan X-Device-Key → 201; refresh dashboard → data muncul | belum dites |
| 4 | Ack alert | Buat kondisi alert (atau seed), buka halaman alerts → acknowledge → 200, ack ulang → 409 | belum dites |
| 5 | Edit threshold | Pengaturan → ubah turbidity_max → tersimpan; cek rule version bertambah | belum dites |
| 6 | Export CSV | Device → export.csv?from=&to= → file terunduh, header benar | belum dites |
| 7 | Kontrol aktuator | Control → nyalakan aerator → command pending; (butuh firmware/ESP32 untuk poll+ack penuh) | belum dites |

## Catatan

- Langkah 3 & 7 butuh perangkat ESP32 fisik atau simulator yang
  memanggil endpoint device-key; tanpa itu hanya terverifikasi via pytest.
- Setelah deploy, jalankan checklist ini dan ganti "belum dites"
  dengan tanggal + hasil.
