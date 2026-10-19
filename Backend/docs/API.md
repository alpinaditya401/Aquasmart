# Dokumentasi API Backend AquaSmart (Flask)

Dokumen ini ditulis dari kode di `app/routes/*.py` pada cabang `evaluasi-backend`
(19 Oktober 2026). Kalau dokumen dan kode berbeda, kode yang benar. Perilaku
yang belum sesuai harapan dicatat di bagian [Kondisi yang perlu diketahui](#kondisi-yang-perlu-diketahui),
bukan disembunyikan.

## Dasar

| Hal | Nilai |
| --- | --- |
| Base URL lokal | `http://127.0.0.1:8080` (`python wsgi.py`) atau `http://localhost:8080` (`docker compose up`) |
| Format | JSON (`Content-Type: application/json`), kecuali ekspor CSV |
| Waktu | String UTC ISO-8601 berakhiran `Z`, kecuali kolom command yang berupa epoch detik |
| Health check | `GET /healthz` (orkestrator) dan `GET /api/health` |

### Format error

Semua error memakai satu bentuk (`app/errors.py`):

```json
{"error": {"code": "unprocessable", "message": "Password minimal 8 karakter."}}
```

| Status | `code` | Kapan |
| --- | --- | --- |
| 401 | `unauthorized` | Belum login, sesi habis, atau `X-Device-Key` salah |
| 403 | `forbidden` | Bukan pemilik data atau bukan admin |
| 403 | `csrf_mismatch` | Header `X-CSRF-Token` tidak ada atau salah |
| 404 | `not_found` | Data atau endpoint tidak ada |
| 405 | `method_not_allowed` | Method HTTP salah |
| 409 | `conflict` | Bentrok data (duplikat, status tidak sesuai) |
| 422 | `unprocessable` | Validasi input gagal |
| 429 | `rate_limited` | Melewati batas permintaan |
| 500 | `internal_error` | Kesalahan server |

## Autentikasi

Ada dua jenis klien, masing-masing dengan cara autentikasi sendiri (`app/auth.py`).

**Pengguna dashboard (sesi).** Login atau register mengembalikan cookie
`aquasmart_session` (HttpOnly, SameSite=Lax) dan `csrf_token` 48 karakter hex di
body. Setiap request yang mengubah data (ditandai **CSRF** di tabel) wajib
mengirim header `X-CSRF-Token` berisi token itu.

**Perangkat ESP32 (device key).** Header `X-Device-Key` berisi key mentah. Server
hanya menyimpan SHA-256 dari key dan membandingkannya dengan `hmac.compare_digest`.
Key didapat dari endpoint rotasi key dan hanya ditampilkan sekali.

Kolom **Akses** di tabel memakai singkatan berikut:
- Publik: tanpa autentikasi
- Sesi: cookie login
- Sesi + CSRF: cookie login dan header `X-CSRF-Token`
- Admin: sesi dengan `role = admin`
- Device: header `X-Device-Key`

### Rate limit

| Endpoint | Batas |
| --- | --- |
| `POST /api/auth/register` | 10 per menit per IP |
| `POST /api/auth/login` | 30 per menit per IP |
| Semua endpoint lain | 240 per menit per IP |

Penyimpanannya Redis bila `REDIS_URL` di-set (docker-compose melakukannya). Tanpa
itu limiter memakai memori proses, sehingga tiap worker gunicorn menghitung sendiri.

### CORS

`GET /api/rules` memasang `Access-Control-Allow-Origin: *`. Endpoint `/api/*` lain
hanya menjawab origin yang tercantum di `CORS_ORIGINS` (dipisah koma), dengan
`Access-Control-Allow-Credentials: true`.

## Ringkasan endpoint

| Method | Path | Akses | Fungsi |
| --- | --- | --- | --- |
| GET | `/healthz` | Publik | Health check orkestrator |
| GET | `/api/health` | Publik | Health check API |
| GET | `/api/rules` | Publik | Threshold bawaan dan checksum |
| POST | `/api/auth/register` | Publik | Daftar akun |
| POST | `/api/auth/login` | Publik | Masuk |
| POST | `/api/auth/logout` | Sesi | Keluar |
| GET | `/api/auth/me` | Sesi | Data pengguna yang login |
| PATCH | `/api/profile` | Sesi + CSRF | Ubah nama atau nomor HP |
| GET | `/api/devices` | Sesi | Daftar perangkat milik pengguna |
| POST | `/api/devices/claim` | Sesi + CSRF | Klaim perangkat dari serial |
| PATCH | `/api/devices/{id}` | Sesi + CSRF | Ubah nama dan lokasi perangkat |
| POST | `/api/devices/{id}/key/rotate` | Admin + CSRF | Buat device key baru |
| POST | `/api/devices/{id}/control` | Admin + CSRF | Kirim perintah aerator, feeder, atau mode auto |
| GET | `/api/devices/{id}/readings` | Sesi | Bacaan sensor ternormalisasi |
| GET | `/api/reports` | Sesi | Agregasi harian per periode |
| GET | `/api/devices/{id}/export.csv` | Sesi | Ekspor bacaan ke CSV |
| GET | `/api/alerts` | Sesi | Daftar alert |
| POST | `/api/alerts/{id}/acknowledge` | Sesi + CSRF | Tandai alert sudah dibaca |
| GET | `/api/settings/thresholds` | Sesi | Threshold milik pengguna |
| PUT | `/api/settings/thresholds` | Admin + CSRF | Ubah threshold (membuat versi baru) |
| GET | `/api/rule-versions` | Sesi | Riwayat versi threshold |
| GET | `/api/devices/{id}/schedules` | Sesi | Daftar jadwal pakan |
| POST | `/api/devices/{id}/schedules` | Sesi + CSRF | Tambah jadwal pakan |
| PUT | `/api/schedules/{sid}` | Sesi + CSRF | Ubah jadwal pakan |
| DELETE | `/api/schedules/{sid}` | Sesi + CSRF | Hapus jadwal pakan |
| GET | `/api/devices/{id}/feeding-logs` | Sesi | Riwayat pemberian pakan |
| POST | `/api/devices/{id}/feeding-logs` | Admin + CSRF | Perintah beri pakan sekarang |
| GET | `/api/devices/{id}/observations` | Sesi | Daftar observasi pertumbuhan |
| POST | `/api/devices/{id}/observations` | Sesi + CSRF | Catat observasi pertumbuhan |
| GET | `/api/workspace` | Sesi | Workspace (model satu pengguna) |
| GET | `/api/audit-logs` | Sesi | Audit log (belum diimplementasikan, selalu kosong) |
| POST | `/api/devices/{id}/telemetry` | Device | Kirim telemetri dari ESP32 |
| POST | `/api/devices/{id}/heartbeat` | Device | Tanda perangkat hidup |
| GET | `/api/devices/{id}/telemetry/raw` | Device | Telemetri mentah berhalaman |
| GET | `/api/device/devices/{id}/commands` | Device | ESP32 mengambil perintah |
| POST | `/api/device/devices/{id}/commands/{cid}/ack` | Device | ESP32 melapor hasil perintah |

Prefix `/api/device/devices/` (dengan `device` tunggal) memang berbeda dari
`/api/devices/`. Firmware ESP32 memakai path ini, jadi jangan disatukan.

---

## Publik

### `GET /api/health`
`200` `{"status": "ok", "service": "aquasmart-api"}`

### `GET /healthz`
`200` `{"status": "ok"}`. Dipakai `HEALTHCHECK` Docker dan Railway.

### `GET /api/rules`
Threshold bawaan dan checksum yang bisa dipakai firmware untuk mendeteksi perubahan.

```json
{
  "version": "threshold-rules-v2",
  "rule": {"ph_min": 6.5, "ph_max": 8.5, "temperature_min": 25.0,
           "temperature_max": 30.0, "turbidity_max": 50.0},
  "checksum": "sha256:<hex>"
}
```

`checksum` adalah SHA-256 dari JSON `rule` dengan kunci terurut dan tanpa spasi.

## Akun

### `POST /api/auth/register`
Body:

| Field | Aturan |
| --- | --- |
| `name` | 1-100 karakter |
| `contact` | Email atau nomor HP, wajib, juga dipakai sebagai username |
| `password` | Minimal 8 karakter |
| `password_confirmation` | Sama dengan `password` |

`201` langsung login:
```json
{"user": {"id": 1, "username": "budi@contoh.id", "contact": "budi@contoh.id",
          "name": "Budi", "role": "admin", "phone": null, "workspace_owner_id": null},
 "csrf_token": "<48 hex>"}
```
Error: `422` validasi, `409` kontak sudah terdaftar, `429`.

### `POST /api/auth/login`
Body `{"username": "<contact>", "password": "..."}`. `200` bentuknya sama dengan
register. `401` bila kredensial salah. Password lama dari backend PHP (`$2y$`)
tetap diterima.

### `POST /api/auth/logout`
`200` `{"ok": true}`. Menghapus isi sesi.

### `GET /api/auth/me`
`200` `{"user": {...}, "csrf_token": "<48 hex>"}`. `401` bila belum login.

### `PATCH /api/profile` (CSRF)
Body opsional `{"name": "1-100 karakter", "phone": "maks 20 karakter"}`.
`200` `{"user": {...}}`.

## Perangkat

### `GET /api/devices`
`200`:
```json
{"devices": [{
  "id": "AQS-001", "name": "Kolam A", "location": "Belakang rumah",
  "online": true, "aerator": false, "feeder": false, "auto": false,
  "last_seen": "2026-10-19T03:00:00Z",
  "latest_reading": {"ph": 7.1, "temperature": 27.4, "turbidity": 12.0,
                     "simulation": false, "provenance": "device",
                     "source_session": "...", "created_at": "..."}
}]}
```
`latest_reading` bernilai `null` bila belum ada bacaan.

### `POST /api/devices/claim` (CSRF)
Body `{"serial_number": "AQS-001"}` (alias `serial` diterima). Serial diubah ke huruf
besar dan harus cocok `^[A-Z0-9_-]{1,128}$`.
`201` `{"device": {"id": "AQS-001", "name": "...", "location": "..."}}`.
`422` serial tidak valid atau belum terdaftar di inventaris. `409` sudah diklaim.

### `PATCH /api/devices/{id}` (CSRF)
Body `{"name": "1-100 karakter", "location": "1-150 karakter"}`, keduanya wajib.
`200` `{"updated": true}`. `404` tidak ada, `403` bukan milik pengguna.

### `POST /api/devices/{id}/key/rotate` (Admin, CSRF)
`200`:
```json
{"device_id": "AQS-001", "device_key": "<key mentah>",
 "notice": "Simpan key ini sekarang. Key tidak akan ditampilkan lagi."}
```
Key lama langsung tidak berlaku.

### `POST /api/devices/{id}/control` (Admin, CSRF)
Body:

| Field | Aturan |
| --- | --- |
| `actuator` | `aerator`, `feeder`, atau `auto` |
| `value` | boolean |
| `duration` | Hanya untuk `feeder`: bilangan bulat 1-10, bawaan 1 |
| `request_id` | Opsional, untuk idempotensi |
| `simulation` | Bila `true`, ditolak `422` |

- `auto` hanya mengubah mode perangkat: `200` `{"ok": true, "device_id": "...", "auto": true}`.
- `aerator` atau `feeder` masuk antrian: `201` `{"command": {...}}`. Bentuk command:
  `{id, device_id, actuator, value, duration, request_id, status: "pending", created_at, expires_at}`
  (waktu dalam epoch detik, kedaluwarsa 300 detik).
- `request_id` yang sama dengan parameter sama mengembalikan command lama (`200`).
  Parameter berbeda: `409`.
- `409` bila aktuator yang sama masih punya perintah `pending` atau `delivered`.

Respons sukses berarti perintah **tersimpan di antrian**, bukan bukti aktuator
fisik bergerak. Bukti aktuasi hanya dari ack perangkat.

## Data sensor dan laporan

### `GET /api/devices/{id}/readings?limit=50`
`limit` 1-100. Urut dari yang paling lama.
`200` `{"readings": [{time, ph, temperature, turbidity, simulation, provenance, source_session}]}`.

### `GET /api/reports?device_id=&period=day|week|month&date=YYYY-MM-DD`
Agregasi harian UTC. Minggu dimulai Senin. Periode tanpa data mengembalikan
`groups` kosong (tidak diisi angka karangan).
```json
{"device_id": "AQS-001", "period": "week", "date": "2026-10-19", "timezone": "UTC",
 "start_at": "2026-10-19T00:00:00Z", "end_at_exclusive": "2026-10-26T00:00:00Z",
 "groups": [{"day": "2026-10-19", "cnt": 12, "ph_avg": 7.05,
             "temperature_avg": 27.3, "turbidity_avg": 10.4,
             "simulation_samples": 0, "non_simulation_samples": 12}],
 "total_samples": 12}
```

### `GET /api/devices/{id}/export.csv?from=YYYY-MM-DD&to=YYYY-MM-DD`
`200` `text/csv` sebagai lampiran `aquasmart-{id}-{from}-{to}.csv`. Kolom:
`time, ph, temperature, turbidity, simulation, provenance, source_session`. Sel teks
yang diawali `= + - @` diberi awalan `'` untuk mencegah formula injection.
`422` format tanggal salah atau `from > to`. `403` bukan milik pengguna.

## Alert

### `GET /api/alerts?limit=20`
`limit` 1-100. Urut terbaru dulu.
`200` `{"alerts": [{id, device_id, severity, message, acknowledged, created_at, acknowledged_at, provenance, source_session}], "unacknowledged_count": 3}`.

### `POST /api/alerts/{id}/acknowledge` (CSRF)
`200` `{"alert": {...}}`. `404` tidak ada, `403` bukan perangkat pengguna,
`409` sudah di-acknowledge.

## Threshold

### `GET /api/settings/thresholds`
`200` `{"thresholds": {ph_min, ph_max, temperature_min, temperature_max, turbidity_max}}`.
Bila pengguna belum pernah menyimpan, nilai bawaan `/api/rules` yang dikembalikan.

### `PUT /api/settings/thresholds` (Admin, CSRF)
Body berisi kelima field di atas, semuanya angka. Aturan: pH 0-14, `ph_min <= ph_max`,
`temperature_min <= temperature_max`, `turbidity_max >= 0`.
`200` `{"thresholds": {...}, "rule_version": "2"}`. Setiap simpan membuat versi baru.

### `GET /api/rule-versions`
50 versi terakhir milik pengguna:
`200` `{"versions": [{id, version, created_at, config}], "note": "..."}`.

## Jadwal pakan

### `GET /api/devices/{id}/schedules`
`200` `{"schedules": [{id, device_id, time, duration, days, active, created_at, end_time}]}`.

### `POST /api/devices/{id}/schedules` (CSRF)
Body:

| Field | Aturan | Bawaan |
| --- | --- | --- |
| `time` | `HH:MM` 24 jam | wajib |
| `duration` | bilangan bulat 1-30 | 10 |
| `days` | `Setiap hari`, `Senin - Jumat`, atau `Akhir pekan` | `Setiap hari` |
| `active` | boolean | `true` |

`201` `{"schedule": {...}}`. `end_time` dihitung sebagai `time + duration` menit.

### `PUT /api/schedules/{sid}` (CSRF)
Body sama dengan POST. `200` `{"schedule": {...}}`.

### `DELETE /api/schedules/{sid}` (CSRF)
`200` `{"deleted": true}`.

## Pemberian pakan

### `GET /api/devices/{id}/feeding-logs`
100 command feeder terakhir yang sudah selesai (`succeeded`, `failed`, `timeout`):
`200` `{"feeding_logs": [{id, device_id, actuator, value, duration, status, request_id, created_at, completed_at}]}`.

### `POST /api/devices/{id}/feeding-logs` (Admin, CSRF)
Body `{"duration": 1-10, "request_id": "opsional"}`, `duration` bawaan 5.
Aturannya sama dengan `control` untuk feeder. `201` `{"feeding_log": {...}}`,
`200` bila `request_id` sudah pernah dipakai dengan parameter sama.

## Observasi pertumbuhan

### `GET /api/devices/{id}/observations`
`200` `{"observations": [{id, user_id, device_id, observed_at, weight_g, length_cm, notes, created_at, provenance, source_session}]}`.

### `POST /api/devices/{id}/observations` (CSRF)
Body: `observed_at` (`YYYY-MM-DD`, tidak boleh tanggal masa depan) dan minimal satu dari
`weight_g` (angka >= 0), `length_cm` (angka >= 0), `notes` (maks 2000 karakter).
`201` `{"observation": {...}}`.

## Workspace

### `GET /api/workspace`
Model satu pengguna: `200` `{"owner_id": 1, "members": [{"id": 1, "name": "...", "role": "admin"}]}`.

### `GET /api/audit-logs`
Belum diimplementasikan. Selalu `200` `{"audit_logs": []}`.

## Endpoint perangkat (ESP32)

Semua butuh header `X-Device-Key`. Key salah: `401`.

### `POST /api/devices/{id}/telemetry`
Contoh body:
```json
{
  "created_at": "2026-10-19T03:00:00Z",
  "simulation": false,
  "provenance": "device",
  "source": "hardware",
  "source_session": "esp32boot0001",
  "calibrated": false,
  "ph_sensor": "soil_placeholder",
  "temperature": 27.4,
  "temperature_status": "ok",
  "turbidity_adc": 1830, "turbidity_mv": 1475, "turbidity_mapping_percent": 12.5,
  "soil_ph_adc": 2010, "soil_ph_mv": 1620,
  "tds_adc": 410, "tds_mv": 330,
  "water_distance_cm": 18.2, "tank_height_cm": 60
}
```

| Field | Aturan |
| --- | --- |
| `created_at` | ISO-8601 dengan zona waktu (`Z` atau offset) |
| `simulation` | boolean, harus cocok dengan `provenance` |
| `provenance` | `device` atau `simulation` |
| `source` | `hardware` atau `simulated`, bawaan `simulated` |
| `source_session` | 8-64 karakter alfanumerik |
| `calibrated` | boolean, wajib |
| `ph_sensor` | harus `soil_placeholder` (sensor pH yang ada adalah sensor tanah) |
| `temperature_status` | `ok`, `disconnected`, atau `unverified` |
| `temperature` | wajib angka bila status `ok` |
| `turbidity_mapping_percent` | opsional, 0-100 |
| `water_distance_cm`, `tank_height_cm` | opsional tetapi harus berpasangan, 0-500 |

Body maksimal 64 KiB. Seluruh body disimpan mentah untuk audit.
`201` `{"ok": true, "device_id", "created_at", "received_at", "simulation", "provenance", "source"}`.
Kiriman ulang dengan `created_at` dan isi identik: `201` dengan `"duplicate": true`.
`created_at` sama tetapi isi berbeda: `409`. `422` validasi, `404` perangkat tidak dikenal.

### `POST /api/devices/{id}/heartbeat`
`204` tanpa body. Memperbarui `last_seen` dan menandai perangkat online.

### `GET /api/devices/{id}/telemetry/raw?cursor=&limit=100`
`limit` 1-1000. `cursor` adalah `created_at` terakhir dari halaman sebelumnya.
`200` `{"telemetry": [{created_at, received_at, provenance, simulation, source, source_session, payload}], "next_cursor": "..." | null}`.

### `GET /api/device/devices/{id}/commands`
Mengambil command `pending` yang belum kedaluwarsa dan mengubahnya jadi `delivered`.
`200` `{"commands": [{...}]}`. Poll berikutnya tidak mengembalikan command yang sama.

### `POST /api/device/devices/{id}/commands/{cid}/ack`
Body `{"status": "succeeded" | "failed" | "timeout"}`.
`200` `{"ok": true, "id": "...", "status": "succeeded"}`.
`409` bila command tidak ditemukan, belum di-poll, atau sudah selesai. Firmware
menganggap `409` sebagai final dan tidak mengaktuasi ulang.

Siklus command: `pending` -> `delivered` -> `succeeded` / `failed` / `timeout`.
Command `pending` yang lewat batas diubah jadi `expired` oleh
`flask expire-commands` atau scheduler (`SCHEDULER_ENABLED=true`).

---

## Kondisi yang perlu diketahui

Temuan pemeriksaan kode 19 Oktober 2026. Belum diperbaiki di cabang ini.

1. **Telemetri belum diolah jadi bacaan dan alert.** `POST .../telemetry` hanya mengisi
   tabel `device_telemetry`. Tidak ada kode yang menulis `sensor_readings` atau
   `alerts`, sehingga `readings`, `reports`, `export.csv`, `alerts`, dan
   `latest_reading` hanya menampilkan data lama hasil impor, bukan data perangkat baru.
2. **Tiga endpoint belum membatasi data per pemilik.** `GET /api/alerts` mengembalikan
   alert semua pengguna. `GET /api/devices/{id}/readings` dan `GET /api/reports`
   tidak memeriksa apakah perangkat milik pengguna yang login.
3. **Semua akun baru ber-role `admin`.** Belum ada role viewer.
4. **Audit log** belum diimplementasikan (lihat di atas).
5. **Ekspor CSV** memakai batas `< {to}T23:59:59Z`, jadi detik terakhir hari `to`
   tidak ikut.
6. **Kontrol aktuator belum terbukti di perangkat fisik.** API hanya mencatat
   antrian dan ack.
