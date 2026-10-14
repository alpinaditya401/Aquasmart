# NFR_MEASUREMENT.md — Metode pengukuran NFR

> Dokumen ini berisi **metode ukur saja**. Jangan isi hasil sebelum ada
> data nyata dari environment yang ditentukan.

## V3-NFR01 — TTFB API lokal < 2 detik

```bash
curl -w "TTFB: %{time_starttransfer}s | total: %{time_total}s\n" \
  -o /dev/null -s http://127.0.0.1:8080/api/devices/<id>/readings?limit=50 \
  -b cookie.jar
```

- Ulangi 30x pada dataset representatif (≥1000 readings); catat
  konfigurasi mesin, lalu hitung p50/p95/p99.
- Lulus bila p95 < 2 detik.

## V3-NFR02 — Uptime lokal ≥ 90%

- Jendela observasi disepakati (mis. 7×24 jam); probe HTTP ke `/healthz`
  tiap 60 detik dari monitoring provider (UptimeRobot / Railway metrics).
- Health check tunggal tidak cukup — butuh deret waktu.
- Lulus bila rasio sukses ≥ 90% dalam jendela.

## V3-NFR06 — Latency notifikasi ≤ 60 detik setelah ingest valid

- Ambil `received_at` dari `device_telemetry` dan `created_at` dari `alerts`
  untuk breach yang sama:
  ```sql
  SELECT (julianday(a.created_at) - julianday(t.received_at)) * 86400 AS detik
  FROM alerts a JOIN device_telemetry t ON ...;
  ```
- Lulus bila p95 ≤ 60 detik.

## V3-NFR12 — Retensi lokal minimal 6 bulan

```sql
SELECT MIN(created_at), MAX(created_at),
       julianday(MAX(created_at)) - julianday(MIN(created_at)) AS hari
FROM sensor_readings;
```

- Lulus bila rentang ≥ 180 hari tanpa gap yang tidak dijelaskan.
- Uji restore: backup SQLite → restore ke DB kosong → hitung baris
  `device_telemetry` sama dengan sebelum backup.

## V3-NFR03 — Akurasi sensor (pH ±0,2; suhu ±0,5 °C)

- Bandingkan dengan alat referensi terkalibrasi pada 3 titik ukur;
  catat prosedur + foto setup. pH **menunggu sensor fisik**
  (PH_STATUS=DEFERRED_NEXT_YEAR).
- Evaluasi model ML **bukan** uji akurasi sensor.

## V3-NFR04 — Hash password aman

- Verifikasi: hash baru memakai bcrypt; hash lama PHP ($2y$) tetap
  terverifikasi (uji: login dengan akun lama → 200).
- Pastikan tidak ada password/token di log maupun respons API.
