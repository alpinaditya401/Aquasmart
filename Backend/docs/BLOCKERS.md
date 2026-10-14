# BLOCKERS.md — Hal yang tidak bisa diverifikasi agent / butuh manusia

## Teknis (tidak bisa diverifikasi di environment ini)

1. **Kompilasi firmware** — perubahan `config.example.h`
   (`TURBIDITY_CALIBRATED`, `PH_STATUS`, komentar TDS) dan stub
   `setPump`/`setAerator` di `aqs_actuators.h` **belum diverifikasi
   compile** (arduino-cli tidak tersedia di VM ini). Perubahan bersifat
   aditif (`constexpr` + fungsi `inline`), risiko rendah, tetapi wajib
   Verify di Arduino IDE sebelum upload.

2. **Validasi diagram Mermaid** — instalasi `@mermaid-js/mermaid-cli`
   via npx gagal (npm error saat install). Diagram di `docs/uml/*.mmd`
   belum divalidasi mesin; render manual di https://mermaid.live
   sebelum dilampirkan ke laporan akademik.

3. **E2E checklist** — belum dijalankan karena backend & frontend belum
   di-deploy ke URL publik (lihat `docs/E2E_CHECKLIST.md`).

## Deviasi dari task yang didokumentasikan

4. **Schedules: `time`+`duration`, bukan `start_time`/`end_time`.**
   Task meminta validasi `start_time`/`end_time`, tetapi skema baku
   `feeding_schedules` (DB) dan kontrak frontend (zod `Schedule`)
   memakai `time` (HH:MM) + `duration` (1–30). API mengikuti kontrak
   yang ada agar kompatibel; respons menyertakan `end_time` terhitung.

5. **Validasi TDS pada thresholds** — task meminta "TDS tidak boleh
   negatif", tetapi tabel `threshold_settings` tidak memiliki kolom TDS
   (hanya ph_min/max, temperature_min/max, turbidity_max). Tidak ada
   kolom untuk divalidasi; bila TDS masuk threshold, butuh perubahan
   skema + keputusan pemilik.

## Butuh keputusan/tindakan manusia

6. Lihat `docs/HUMAN_ACTIONS.md` (hapus file sensitif dari Drive publik,
   rotasi kredensial, SECRET_KEY production, pilihan SQLite vs Postgres).
7. `docs/SCOPE.md`: workspace/product-units/audit-logs out-of-scope;
   path audit-logs belum terverifikasi.
