# ARCHITECTURE.MD — AquaSmart
**Arsitektur Teknis — Sistem Monitoring Kualitas Air Kolam/Akuakultur IoT**

- Tanggal pembuatan: 10 Oktober 2026
- Versi: **v1 (target state: backend Flask)** — akan disempurnakan
- Acuan: hasil bedah kode aktual 9–10 Okt 2026 (`endpoint-inventory.md`: 42 endpoint / 19 tabel; `bedah-firmware-esp32-2026-10-10.md`: firmware 481 baris; `bedah-techstack-2026-10-09.md`). Jika bertentangan dengan dokumen lama (mis. API doc Sept yang masih menyebut threshold v1), **dokumen ini menang untuk target state**.
- Keputusan stack (final, dari pemilik Alpin Aditya): **Flask (Python) + SQLite (file DB dipakai ulang) + Next.js 16 + BFF**, firmware Arduino ESP32.

> **Legenda bukti:** ✅ = terverifikasi dari kode/sumber aktual · 🔶 = operasi terbukti, detail path direkonstruksi (butuh konfirmasi `router.php` asli) · ❓ = belum terverifikasi · 💡 = asumsi/usulan arsitektur (bukan fakta existing).

---

## 1. Ringkasan Keputusan & Justifikasi

| Keputusan | Pilihan | Justifikasi |
|---|---|---|
| Backend | **Flask 3.x (Python)** — rewrite dari PHP 8.3 | Keputusan pemilik (10 Okt 2026). Kontrak API dipertahankan 1:1 agar firmware tidak perlu diubah |
| Database | **SQLite, file yang SAMA dipakai ulang** | Nol migrasi data; 19 tabel sudah ada dan terbukti (demo.sqlite). SQLAlchemy memetakan skema existing |
| ORM | Flask-SQLAlchemy | Model eksplisit per 19 tabel; tanpa auto-migrate yang merusak data existing |
| Auth user | Session cookie + CSRF via header `X-CSRF-Token` | ✅ Pola existing dipertahankan (cookie `aquasmart_session` HttpOnly SameSite=Lax); Flask-Login atau session manual |
| Hash password | Paket `bcrypt` (PyPI) | ✅ Hash existing = bcrypt PHP — Werkzeug standar tidak bisa verifikasi; bcrypt agar user lama tetap bisa login |
| Auth device | Header `X-Device-Key`, disimpan SHA-256 | ✅ Kontrak firmware; tidak berubah |
| Rate limit | Flask-Limiter | ✅ Batas existing: login 30/mnt, register 10/mnt, ingest 240/mnt/device |
| Scheduler | APScheduler | Pengganti `tick()` PHP: expiry command otomatis |
| Server prod | Gunicorn | Railway mendukung Python via Nixpacks (auto-detect `requirements.txt`) |
| Frontend | Next.js 16 App Router (10 rute, source di GitHub) | ✅ Ada di repo `alpinaditya401/Testing-Project` folder `frontend/` |
| BFF | Lapisan BFF Next.js → Flask API | 💡 Struktur BFF belum diverifikasi dari source (belum terunduh); peran: agregasi + API key server-side |
| Firmware | Arduino core ESP32 3.0.7, board DOIT DEVKIT V1 | ✅ Kode nyata 481 baris; kontrak 3 endpoint tidak berubah |
| Sensor pH | **DITUNDA ke tahun depan** | Keputusan pemilik (10 Okt 2026, alasan biaya). Channel pH nonaktif via `*_CONFIRMED=false` |

---

## 2. Arsitektur Keseluruhan

```
┌──────────────────────────────────────────────────────────────────┐
│  LAPISAN PERANGKAT (kolam)                                        │
│  ESP32 (Arduino) — sensor: turbidity GPIO34 · TDS GPIO35 ·        │
│  suhu DS18B20 GPIO4 · level HC-SR04 (TRIG27/ECHO25) ·             │
│  aktuator: feeder servo GPIO18 · aerator relay GPIO23 ·           │
│  pompa trigger GPIO14                                             │
│  (pH: DITUNDA — channel nonaktif)                                 │
└───────────────┬────────────────────────────────┬─────────────────┘
                │ POST /api/devices/{id}/telemetry   │ GET /api/device/devices/{id}/commands
                │ header X-Device-Key                │ POST .../commands/{cid}/ack
                │ TLS + CA pinning, NTP wajib        │
┌───────────────▼────────────────────────────────▼─────────────────┐
│  BACKEND — Flask 3.x + Gunicorn (Railway)                         │
│  Blueprints per domain: health · rules · auth · devices ·          │
│  telemetry · commands · reports · alerts · schedules ·             │
│  workspaces · product · observations · export · audit              │
│  Services: command_lifecycle · simulation_guard · rate_limit ·     │
│  audit_log                                                        │
│  APScheduler: expiry command otomatis (pengganti tick())           │
└───────────────┬────────────────────────────────┬─────────────────┘
                │ SQLAlchemy                     │ session cookie +
                │                                │ header X-CSRF-Token
┌───────────────▼────────────────────────────────▼─────────────────┐
│  SQLite (file DB existing, 19 tabel) — volume persistent Railway   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  LAPISAN PRESENTASI                                               │
│  Browser user ──▶ Next.js 16 (Vercel) ──▶ BFF ──▶ Flask API        │
│  (admin & viewer; viewer = read-only)                             │
└──────────────────────────────────────────────────────────────────┘
```

**Aturan emas:**
1. **Firmware tidak pernah diubah kontraknya** — 3 endpoint + format error + dual-prefix quirk dipertahankan (§7).
2. **File SQLite yang sama dipakai ulang** — tidak ada migrasi data; model hanya memetakan.
3. **Flag `simulation` ditegakkan server-side** — data simulasi tidak boleh tercampur tanpa label; firmware MENOLAK command bertanda simulation.
4. Semua timestamp UTC ISO-8601 `...Z` ketat; konversi ke Asia/Jakarta hanya di tampilan.

---

## 3. Komponen & Tanggung Jawab

### 3.1 Firmware ESP32 (✅ terverifikasi dari kode)
- **Struktur modular:** `aquasmart_esp32.ino` (112 baris) + 5 header (`aqs_common`, `aqs_sensors`, `aqs_actuators`, `aqs_network`, `aqs_display`) — 481 baris total.
- **Sensor:** kirim raw ADC + mV (median 9 sampel); server yang menurunkan ppm/level/persen. Semua ADC di **ADC1** (ADC2 mati saat WiFi jalan).
- **Aktuator:** digerakkan flag `ENABLE_*` + `*_CONFIRMED` (default FALSE = "keluaran aman" sampai wiring dikonfirmasi per-item). Lease: feeder ≤10 dtk (maks 30 dtk), aerator 30 dtk, pompa 30 dtk.
- **Jaringan:** retry exponential 1–60 dtk + jitter; offline 5 menit → auto-restart; TLS CA pinning (`ROOT_CA`); **NTP wajib** sebelum command diterima; replay protection 8 slot NVS; command ID hex 32-char + expiry check.
- **Kejujuran kode:** komentar "A terminal ACK means the output pin was ordered, not that the motor turned." Status README: PARTIAL (compile ✅, upload/WiFi/telemetri fisik ❌).

### 3.2 Backend Flask (💡 target state — struktur usulan)
```
aquasmart-flask/
├── app.py                 # application factory
├── config.py              # env-based config
├── models/                # 19 model SQLAlchemy (map 1:1 ke tabel existing)
│   └── __init__.py        # users, devices, device_credentials, sensor_readings, ...
├── blueprints/            # 1 blueprint per domain (§4)
│   ├── health.py  rules.py  auth.py  devices.py  telemetry.py
│   ├── commands.py  reports.py  alerts.py  schedules.py
│   ├── workspaces.py  product.py  observations.py  export.py
│   ├── audit.py
├── services/
│   ├── command_lifecycle.py  # pending→delivered→succeeded|failed|timeout + expiry
│   ├── simulation_guard.py   # penegakan flag simulation + provenance
│   ├── idempotency.py        # request_id 409 handling
│   └── audit_log.py
├── scheduler.py           # APScheduler: expiry command, (opsional) agregasi
├── tests/                 # pytest — port dari 104 test IDs PHP
└── requirements.txt
```

### 3.3 Scheduler (APScheduler)
- **Tugas wajib:** expiry command otomatis — command `pending`/`delivered` yang melewati `expires_at` → `timeout` (pengganti `tick()` PHP).
- **Tugas opsional (P1):** pre-agregasi laporan harian; cleanup `api_rate_limits` kedaluwarsa.
- Berjalan in-process bersama Gunicorn (single worker untuk scheduler) atau sebagai proses terpisah — 💡 keputusan implementasi.

### 3.4 SQLite (✅ skema terverifikasi dari demo.sqlite)
- 19 tabel (detail §5). File DB existing dipakai ulang **tanpa migrasi**.
- ⚠️ **Batasan sadar:** SQLite = single-writer; cukup untuk v1 (satu kolam / sedikit device). Migrasi ke Postgres/MySQL adalah keputusan masa depan, bukan sekarang (CR-001 menunggu keputusan sponsor — ✅ fakta dari README repo).

### 3.5 Frontend Next.js 16 (✅ keberadaan terverifikasi; detail 🔶)
- ✅ Ada di repo GitHub `alpinaditya401/Testing-Project`, folder `frontend/`: 10 rute App Router, design system, BFF ke backend. Deploy aktif di Vercel (catatan: yang tayang masih build lama per 21 Sep 2026).
- 🔶 Detail implementasi per halaman belum diverifikasi (source belum dibedah) — rencana perbaikan ada di dokumen rencana penyelesaian.

### 3.6 BFF — Backend for Frontend (❓/💡)
- ❓ Source BFF (`frontend-bff/`: `route.ts` + `api-schemas.ts` per penamaan folder) belum terunduh/belum diverifikasi.
- 💡 Peran arsitektur yang diusulkan: BFF memegang API key / menyederhanakan respons untuk frontend, meneruskan session user ke Flask API. **Tidak boleh** menyimpan kredensial device (`X-Device-Key` hanya untuk firmware).

---

## 4. Alur Data Utama

### 4.1 Alur telemetri (ESP32 → dashboard)
```
[ESP32] sampling sensor (median 9x, ADC1)
   │  payload: created_at*, simulation, provenance, source_session,
   │  temperature(+status), turbidity_adc/mv(+meta), soil_ph_adc/mv,
   │  tds_adc/mv, water_distance_cm+tank_height_cm, calibrated=false,
   │  ph_sensor="soil_placeholder"   (*kontrak KETAT — §7)
   ▼
POST /api/devices/{id}/telemetry   (header X-Device-Key)
   │  validasi: key ✅ → kontrak ✅ → 201
   │  401 key salah · 409 timestamp duplikat beda nilai · 422 validasi
   ▼
[Flask] TelemetryRepository.ingest:
   1. simpan payload mentah → device_telemetry
   2. hitung tds_ppm_estimate (kurva DFRobot SEN0244), water_level_percent
   3. tulis sensor_readings (flag simulation sesuai kiriman)
   4. update devices.last_seen / online
   5. evaluasi threshold v2 → buat alerts bila breach
   6. audit telemetry.received
   ▼
[SQLite] → dashboard baca via GET /api/devices/{id}/readings, GET /api/reports
```
**Catatan:** `calibrated` harus `false` dan `ph_sensor` harus `soil_placeholder` — kontrak saat ini HANYA menerima sensor belum terkalibrasi (✅ dari kode). Setelah kalibrasi turbidity/TDS, kontrak ini harus dilonggarkan **bersama** (firmware + backend).

### 4.2 Alur command (dashboard → ESP32)
```
[Dashboard] POST /api/devices/{id}/control
   {actuator: aerator|feeder|auto, value, duration?, request_id?}
   │  session admin + CSRF ✅ → 403 tanpa CSRF
   │  idempotensi: request_id dipakai ulang + param beda → 409
   │  1 perintah aktif per aktuator → 409 bila sibuk
   ▼
[Flask] enqueue → actuator_commands (status=pending, simulation=0)
   │  (command simulation=true DITOLAK di antrian hardware)
   ▼
[ESP32] GET /api/device/devices/{id}/commands  (poll, X-Device-Key)
   │  respons {"commands":[...]} → status pending→delivered
   │  cek: ID hex 32-char, expiry, replay (NVS 8 slot), NTP sync
   ▼
[ESP32] aktuasi GPIO (lease ≤30 dtk)
   ▼
[ESP32] POST /api/device/devices/{id}/commands/{cid}/ack
   {status: succeeded|failed|timeout}
   │  409 bila belum delivered / sudah terminal
   ▼
[Flask] status → succeeded|failed|timeout (+completed_at)
   │  scheduler: pending/delivered lewat expires_at → timeout
   ▼
[Dashboard] GET /api/devices/{id}/commands (riwayat 100 terakhir)
```

**Lifecycle status:** `pending → delivered → succeeded | failed | timeout`
- `pending`: di antrian, belum di-poll firmware
- `delivered`: sudah di-poll, menunggu ACK
- `succeeded` / `failed` / `timeout`: terminal (ACK = "GPIO diperintahkan", bukan bukti motor berputar — ✅ komentar jujur di kode)

---

## 5. Skema Database — Ringkasan 19 Tabel (✅ dari demo.sqlite)

| # | Tabel | Peran | Kolom kunci |
|---|---|---|---|
| 1 | `users` | Akun | id, username, contact, password_hash (bcrypt), role admin/viewer, workspace_owner_id |
| 2 | `devices` | Perangkat milik user | id (serial), user_id, name, location, online, aerator, feeder, auto_mode, last_seen |
| 3 | `device_credentials` | Kunci perangkat | device_id, key_hash (SHA-256), rotated_at |
| 4 | `device_inventory` | Stok serial | serial_number, claimed_user_id, claimed_at |
| 5 | `sensor_readings` | Bacaan ternormalisasi | device_id, ph, temperature, turbidity, **simulation**, provenance, source_session, created_at |
| 6 | `device_telemetry` | Payload mentah | device_id, payload (JSON), provenance, simulation, received_at |
| 7 | `actuator_commands` | Antrian perintah | id (hex 32), device_id, actuator, value, duration, request_id, status, simulation, expires_at |
| 8 | `alerts` | Peringatan threshold | device_id, severity, message, acknowledged |
| 9 | `feeding_schedules` | Jadwal pakan | device_id, time (HH:MM), duration, days, active |
| 10 | `threshold_settings` | Ambang per user | user_id, ph_min/max, temperature_min/max, turbidity_max |
| 11 | `rule_versions` | Riwayat versi rule | user_id, version, config_json |
| 12 | `reading_rule_versions` | Bacaan↔rule | reading_id, rule_id |
| 13 | `growth_observations` | Observasi ikan | device_id, observed_at, weight_g, length_cm, notes |
| 14 | `workspace_invitations` | Undangan | owner_id, contact, token_hash, expires_at |
| 15 | `product_units` | Unit produk | serial, activation_hash, expires_at, key_hash |
| 16 | `activation_attempts` | Lockout aktivasi | user_id, serial, state_json |
| 17 | `seller_operators` | Hak seller | user_id, granted_at |
| 18 | `audit_logs` | Jejak audit | user_id, device_id, action, metadata |
| 19 | `api_rate_limits` | Rate limit | bucket, hits, expires_at |

**Relasi kunci:**
```
users 1───* devices 1───1 device_credentials
              │         └───* sensor_readings / device_telemetry / actuator_commands / alerts
users 1───1 threshold_settings 1───* rule_versions
devices *───* feeding_schedules · growth_observations
users *───* workspace_invitations (owner → contact)
```
- **Aturan data:** setiap baris sensor/command membawa `provenance` + `source_session` + flag `simulation` — tidak boleh ada baris tanpa ketiganya (✅ pola existing).
- **Threshold aktif = v2:** pH 6,5–8,5; suhu 25–30 °C; turbidity ≤ 50. `GET /api/rules` mengembalikan `source_sha256` untuk verifikasi integritas (✅ dari kode).

---

## 6. Keamanan

| Lapisan | Mekanisme | Status |
|---|---|---|
| Auth user | Session cookie `aquasmart_session` (HttpOnly, SameSite=Lax) + header `X-CSRF-Token` untuk semua mutasi | ✅ existing → pertahankan |
| Auth device | Header `X-Device-Key`, hash SHA-256 di `device_credentials` | ✅ existing → pertahankan |
| Otorisasi | Role admin vs viewer; viewer read-only (mutasi → 403 `forbidden`) | ✅ existing → pertahankan |
| Password | bcrypt (verifikasi hash lama PHP via paket `bcrypt`) | ✅ existing → pertahankan |
| Rate limit | Flask-Limiter: login 30/mnt, register 10/mnt, ingest 240/mnt/device (+ header `Retry-After`) | ✅ existing → pertahankan |
| Transport firmware | TLS + CA pinning (`ROOT_CA`); flag `DEVELOPMENT_INSECURE_TLS` mencetak peringatan keras | ✅ dari kode firmware |
| Waktu | NTP wajib sebelum command diterima firmware | ✅ dari kode firmware |
| Replay | Proteksi replay 8 slot NVS + ID command hex 32-char + expiry check | ✅ dari kode firmware |
| Simulation | Flag ditegakkan server-side; firmware menolak command `simulation=true` | ✅ existing → pertahankan |
| Input | Body JSON ≤ 64 KiB, nilai skalar saja; timestamp UTC ketat; validasi 422 | ✅ existing → pertahankan |
| Header | Security headers lengkap; `Cache-Control: no-store`; CORS `*` + header `X-CSRF-Token, X-Device-Key` | ✅ existing → pertahankan |
| Error | Envelope `{"error":{"code":...,"message":...}}` — tanpa stack trace ke client | ✅ existing → pertahankan |

**⚠️ Insiden terbuka (KRITIS):** file `railway-seed.local.txt` berisi kredensial admin Railway ditemukan di folder Drive **publik** (temuan 9 Okt 2026). Tindakan: hapus dari Drive + rotasi password — sebelum deployment Flask apa pun.

---

## 7. Kontrak Antar-Komponen yang TIDAK BOLEH Berubah

> Alasan: firmware ESP32 sudah dikompilasi dari kontrak ini. Mengubah kontrak = wajib update firmware + upload ulang fisik.

1. **3 endpoint firmware (✅ terverifikasi dari `aquasmart_esp32.ino` + `aqs_network.h`):**
   - `POST /api/devices/{id}/telemetry` — header `X-Device-Key`; 201/409/422 = terminal
   - `GET /api/device/devices/{id}/commands` — header `X-Device-Key`; respons `{"commands":[...]}`
   - `POST /api/device/devices/{id}/commands/{id}/ack` — header `X-Device-Key`, body `{"status":"succeeded"|"failed"|"timeout"}`; 200/409 = terminal
2. **Dual-prefix quirk:** `/api/devices/...` (telemetri) dan `/api/device/devices/...` (commands) adalah DUA prefix berbeda — **jangan disatukan** saat rewrite Flask.
3. **Kontrak body telemetri kaya:** `created_at` UTC ketat, `simulation` + `provenance` harus cocok, `source_session` 8–64 alnum, `calibrated=false`, `ph_sensor="soil_placeholder"`, pasangan `water_distance_cm`+`tank_height_cm`.
4. **Error envelope** `{"error":{"code":"...","message":"..."}}` dengan kode yang sama.
5. **Threshold rules v2** + SHA-256 di `GET /api/rules` (dokumen API lama yang menyebut v1 sudah kedaluwarsa).

---

## 8. Keputusan Arsitektur (ADR Singkat)

### ADR-001: Flask, bukan PHP
- **Keputusan:** rewrite backend ke Flask 3.x (Python).
- **Konteks:** backend PHP 8.3 sebenarnya solid (104/104 test). Pemilik memutuskan pindah ke Flask (10 Okt 2026).
- **Konsekuensi:** rewrite penuh; risiko ditanggung dengan scope MVP ketat + kontrak API identik. File DB dipakai ulang sehingga data tidak hilang.

### ADR-002: SQLite dipakai ulang, nol migrasi data
- **Keputusan:** model SQLAlchemy memetakan 19 tabel existing 1:1; tidak ada skrip migrasi destruktif.
- **Konsekuensi:** single-writer cukup untuk v1; migrasi ke Postgres/MySQL ditunda (CR-001 menunggu sponsor).

### ADR-003: bcrypt untuk hash lama
- **Keputusan:** verifikasi password memakai paket `bcrypt`, bukan Werkzeug default.
- **Alasan:** hash existing dibuat oleh `password_hash()` PHP (bcrypt); user lama harus tetap bisa login tanpa reset.

### ADR-004: Threshold rules v2 sebagai acuan
- **Keputusan:** v2 (pH 6,5–8,5; suhu 25–30 °C; turbidity ≤ 50) adalah versi aktif; dokumen lama (v1) diabaikan.

### ADR-005: pH ditunda ke tahun depan
- **Keputusan:** channel pH nonaktif (`*_CONFIRMED=false`); tidak ada belanja probe pH tahun ini (alasan biaya).
- **Konsekuensi:** kolom `ph` di `sensor_readings` tetap ada (skema tidak diubah); dashboard tidak menampilkan kartu pH sampai probe air tersedia.

### ADR-006: Command simulation ditolak di antrian hardware
- **Keputusan:** pola existing dipertahankan — antrian hardware hanya untuk perintah nyata.
- **Alasan:** mencegah aktuator fisik bergerak dari perintah uji.

---

## 9. Deployment

```
[GitHub] alpinaditya401/Testing-Project (public)
   │  push (backend Flask di folder terpisah / repo terpisah — 💡 putuskan)
   ▼
[Railway] Service: aquasmart-flask (Python via Nixpacks)
   │  - requirements.txt → auto-detect Python
   │  - Start: gunicorn app:app
   │  - Env: SECRET_KEY (BARU), DATABASE_PATH, TIMEZONE=Asia/Jakarta
   │  - Volume: mount ke path SQLite (persistent!)
   │  ⚠️  SETELAH rotasi kredensial (insiden §6)
   ▼
[Vercel] frontend/ (Next.js 16)
   │  - NEXT_PUBLIC_API_URL → URL Railway Flask
   │  - Deploy ulang (yang tayang masih build lama per 21 Sep 2026)
```

**Urutan cutover (💡 usulan):**
1. Amankan kredensial (hapus file Drive + rotasi password Railway).
2. Deploy Flask ke Railway sebagai service BARU (jangan timpa service PHP dulu).
3. Uji 3 endpoint firmware + 12 endpoint P0 via curl/pytest terhadap URL Railway.
4. Flash ESP32 menunjuk ke URL Flask baru; verifikasi telemetri nyata end-to-end.
5. Alihkan `NEXT_PUBLIC_API_URL` frontend ke Flask; deploy ulang Vercel.
6. Nonaktifkan service PHP lama setelah 24 jam stabil.

**Catatan monorepo:** repo berisi banyak proyek — set **Root Directory** Railway ke folder aplikasi Flask.

---

## 10. Batasan & Risiko Arsitektur yang Diketahui

| # | Batasan / Risiko | Status | Mitigasi |
|---|---|---|---|
| 1 | Kredensial Railway terpapar di Drive publik | 🔴 terbuka | §6 — hapus + rotasi SEBELUM deploy |
| 2 | Rewrite PHP→Flask dalam akhir pekan | 🟡 risiko jadwal | Scope MVP 12 endpoint P0; P1/P2 dipotong |
| 3 | Path endpoint 🔶/❓ (33+1) direkonstruksi tanpa `router.php` | 🟡 akurasi | Samakan dengan firmware (3 endpoint ✅); sisanya konfirmasi dari test IDs / source PHP bila diperoleh |
| 4 | SQLite single-writer | 🟢 diterima v1 | Cukup untuk sedikit device; migrasi DB = keputusan masa depan |
| 5 | BFF belum diverifikasi (❓) | 🟡 | Verifikasi source `frontend-bff/` sebelum mengandalkannya |
| 6 | Endpoint pompa (`pump`) belum diterima server | 🟡 gap kontrak | Tambahkan sebagai P1; sampai saat itu pompa hanya via trigger lokal |
| 7 | Semua sensor uncalibrated; kontrak telemetri ketat | 🟡 | Kalibrasi turbidity/TDS; longgarkan kontrak bersama firmware+backend |
| 8 | Firmware belum pernah upload fisik | 🟡 | Ikuti checklist upload + verifikasi E2E di dokumen rencana |
| 9 | Frontend Vercel masih build lama | 🟢 | Deploy ulang setelah cutover backend |

---

*Dokumen ini v1 (10 Okt 2026) — disusun dari kode aktual, bukan asumsi. Asumsi ditandai 💡/🔶/❓ dan harus dikonfirmasi sebelum dijadikan acuan implementasi.*
