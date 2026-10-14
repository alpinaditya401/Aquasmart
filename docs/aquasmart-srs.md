# SRS.MD — AquaSmart
**Software Requirements Specification — Sistem Monitoring Kualitas Air Kolam/Akuakultur IoT**

- Tanggal pembuatan: 10 Oktober 2026
- Versi: **v1 — target state backend Flask**
- Acuan: PRD AquaSmart v1 (disusun paralel). Jika SRS tidak sepakat dengan PRD, **PRD yang menang**.
- Konvensi: setiap kebutuhan punya ID permanen (FR-006–FR-034, NFR-006–NFR-002; tidak berubah antar revisi; ID yang dipensiunkan tidak dipakai ulang), prioritas MoSCoW, dan kriteria penerimaan (acceptance criteria) yang teruji.
- Sumber kebenaran teknis: `endpoint-inventory.md` (42 endpoint, 14 domain, skema 19 tabel — disusun dari kode aktual 2026-10-10). Item bertanda 🔶 = operasi terbukti dari kode/test tetapi path direkonstruksi (router.php tidak ikut terunduh); ❓ = belum terverifikasi. Tidak ada endpoint yang dikarang.

---

## 1. Ruang Lingkup

SRS ini menspesifikasikan kebutuhan perangkat lunak AquaSmart pada **target state**: backend **Flask (Python)** hasil migrasi dari backend PHP 8.3 (keputusan pemilik, 10 Okt 2026), dengan kontrak API yang dipertahankan identik agar firmware ESP32 tidak perlu diubah.

Cakupan: 13 fitur (F1–F13) mencakup health & threshold, autentikasi, manajemen device, telemetri, commands/aktuasi, reports, alerts, feeding schedules, workspaces, product/units, observations, export CSV, dan audit; kebutuhan data (19 tabel SQLite); kebutuhan antarmuka (kontrak API + kontrak firmware); kebutuhan non-fungsional.

Di luar scope rilis ini: sensor pH air (DITUNDA ke tahun depan per keputusan pemilik — kolom `ph` tetap ada di skema untuk kompatibilitas tetapi tidak diisi/dipresentasikan sebagai pH air terkalibrasi); endpoint audit (FR-034, path belum terverifikasi); hardware fisik di luar firmware yang sudah dibedah (ESP32 + sensor turbidity, TDS, suhu DS18B20, level HC-SR04 — semua sudah dimiliki pemilik).

---

## 2. Kebutuhan Fungsional

Setiap kebutuhan memakai ID permanen yang sama dengan PRD AquaSmart v1. Jika SRS tidak sepakat dengan PRD, **PRD yang menang**.

### F1 — Autentikasi & Akun

**FR-001** *[Must]* Sistem menyediakan registrasi `POST /api/auth/register` (publik, rate limit 10/menit).
- AC1: Body `{name, contact (email/08xx), password, password_confirmation, serial_number?}`; validasi gagal → 422; kontak duplikat → 409.
- AC2: Respons 201 berisi data user AMAN (tanpa password hash) + session aktif; threshold default di-seed untuk user baru.
- AC3: Jika `serial_number` disertakan dan valid, device langsung diklaim ke user baru; serial tak dikenal/sudah dipakai → 409/422.


**FR-002** *[Must]* Sistem menyediakan login `POST /api/auth/login` (publik, rate limit 30/menit).
- AC1: `{username (email/08xx), password}` benar → 200 + cookie session + token CSRF; salah → 401.
- AC2: **Verifikasi hash bcrypt lama wajib**: password yang di-hash oleh PHP `password_hash()` harus tetap bisa login di backend Flask (paket `bcrypt`, bukan hash ulang buta).
- AC3: Upaya ke-31 dalam 1 menit → 429 `rate_limited` + header `Retry-After`.


**FR-003** *[Must]* 🔶 `POST /api/auth/logout` menghancurkan session.
- AC1: Setelah logout, `GET /api/auth/me` mengembalikan 401.


**FR-004** *[Must]* 🔶 `GET /api/auth/me` mengembalikan profil user aman `{id,name,contact,role,phone}` untuk session aktif; 401 bila tidak ada session.


**FR-005** *[Should]* 🔶 `PATCH /api/profile` (session + CSRF) memperbarui `{name (1–100), phone}`; body kosong → 422.


### F2 — Health & Rules

**FR-006** *[Must]* Sistem menyediakan endpoint health check publik `GET /api/health`.
- AC1: Respons 200 `{"status":"ok","service":"aquasmart-api"}` tanpa autentikasi.
- AC2: Endpoint tidak menulis ke database (read-only, aman dipoll monitoring).


**FR-007** *[Must]* Sistem menyediakan `GET /api/rules` (publik + CORS) yang mengembalikan aturan threshold aktif **v2** beserta checksum integritas SHA-256.
- AC1: Respons memuat `version:"threshold-rules-v2"`, nilai pH 6,5–8,5; suhu 25–30 °C; turbidity maks 50.
- AC2: `source_sha256` adalah hash deterministik dari nilai threshold (klien dapat memverifikasi perubahan tak sah).
- AC3: Header `Access-Control-Allow-Origin: *` terpasang (satu-satunya endpoint dengan CORS wildcard — sesuai perilaku terverifikasi).


### F3 — Perangkat

**FR-008** *[Must]* 🔶 `GET /api/devices` (session) mengembalikan daftar device milik user beserta status dan bacaan terakhir.
- AC1: Tiap item memuat `{id,name,location,online,aerator,feeder,auto,last_seen,latest_reading{ph,temperature,turbidity,simulation,created_at,provenance,source_session}}`.
- AC2: Flag `simulation` pada `latest_reading` wajib diteruskan apa adanya (dashboard wajib melabeli data simulasi vs nyata — lihat NFR-004).


**FR-009** *[Should]* 🔶 `POST /api/devices/claim` (session + CSRF) mengklaim device via `{serial}`; unit produk memerlukan kode aktivasi; serial sudah diklaim → 409; serial tak dikenal → 422.


**FR-010** *[Should]* 🔶 `PATCH /api/devices/{id}` (session + CSRF) mengubah `{name (1–100), location (1–150)}`; device bukan milik user → 404.


**FR-011** *[Should]* 🔶 `POST /api/devices/{id}/key/rotate` (session admin + CSRF) menerbitkan device key baru.
- AC1: Respons berisi key mentah baru SATU KALI; yang disimpan hanya hash SHA-256 di `device_credentials`.
- AC2: Key lama langsung tidak berlaku; tercatat di audit (`device.key_rotated`).


**FR-012** *[Could]* 🔶 `GET /api/devices/{id}/heartbeat` (session) mengembalikan `{device_id,last_seen,online,hardware_verified:false}` — nilai `hardware_verified` jujur `false` sampai ada bukti verifikasi fisik.


### F4 — Telemetri

**FR-013** *[Must]* `POST /api/devices/{id}/telemetry` (header `X-Device-Key`) menerima telemetri dari firmware ESP32 — **kontrak ini dipakai firmware dan tidak boleh berubah tanpa update firmware bersamaan**.
- AC1: Key salah → 401 `device_unauthenticated`; body >64 KiB → 413; JSON invalid → 400.
- AC2: Validasi ketat: `created_at` UTC ISO-8601 `...Z`; `simulation` bool; `provenance` (`simulation`|`device`) harus cocok dengan flag; `source_session` 8–64 alnum; **`calibrated` harus `false`**; **`ph_sensor` harus `soil_placeholder`** (kontrak saat ini HANYA menerima sensor belum terkalibrasi — sesuai kode terverifikasi).
- AC3: Timestamp duplikat dengan nilai berbeda → 409 (bukan overwrite diam-diam).
- AC4: Sukses → 201; `last_seen`/`online` device diperbarui. Firmware menganggap 201/409/422 sebagai terminal (tidak retry).
- AC5: Server menghitung `tds_ppm_estimate` (kurva DFRobot SEN0244) dan `water_level_percent` dari nilai mentah.


**FR-014** *[Could]* 🔶 `GET /api/devices/{id}/telemetry` (session, `?limit=1..100`) mengembalikan payload mentah (+`received_at`).


**FR-015** *[Must]* 🔶 `GET /api/devices/{id}/readings` (session, `?limit=1..100`) mengembalikan bacaan ternormalisasi `[{time,ph,temperature,turbidity,simulation,provenance,source_session}]` urut tertua→terbaru.
- AC1: Nilai dari sensor belum terkalibrasi TIDAK BOLEH disajikan sebagai hasil ukur terkalibrasi (lihat NFR-004).


### F5 — Perintah aktuator

**FR-016** *[Must]* `GET /api/device/devices/{id}/commands` (header `X-Device-Key`) — poll perintah untuk firmware. **Prefix `/api/device/devices/` adalah quirk nyata firmware; JANGAN disatukan dengan `/api/devices/`.**
- AC1: Respons 200 `{commands:[{id,actuator,value,duration,status,request_id,...}]}`; perintah `pending` berubah menjadi `delivered` saat diambil.
- AC2: Hanya perintah non-simulasi yang diberikan ke firmware.


**FR-017** *[Must]* `POST /api/device/devices/{id}/commands/{commandId}/ack` (header `X-Device-Key`) menerima `{status: succeeded|failed|timeout}`.
- AC1: Command tak ditemukan / belum `delivered` / sudah terminal → 409 (firmware menganggap 200/409 terminal dan tidak mengakutasi ulang).


**FR-018** *[Should]* 🔶 `POST /api/devices/{id}/control` (session admin + CSRF) meng-enqueue perintah aktuator `{actuator: aerator|feeder|auto, value: bool, duration? (feeder 1–10), request_id?}`.
- AC1: Tanpa CSRF → 403 `csrf_mismatch`; aktuator sibuk / `request_id` dipakai ulang dengan parameter berbeda → 409.
- AC2: Perintah `auto` tidak masuk antrian (mode, bukan aktuasi).
- AC3: Perintah bertanda `simulation=true` DITOLAK (konsisten dengan firmware yang menolaknya).


**FR-019** *[Could]* 🔶 `GET /api/devices/{id}/commands` (session) mengembalikan riwayat 100 perintah terakhir.


**FR-020** *[Could]* 🔶 `GET /api/devices/{id}/feeding-logs` (session) mengembalikan perintah feeder berstatus terminal (succeeded/failed/timeout); idempoten.


### F6 — Laporan

**FR-021** *[Must]* `GET /api/reports` (session, `?device_id&period=day|week|month&date=YYYY-MM-DD`) mengembalikan agregasi bucket harian UTC.
- AC1: Struktur `{device_id,period,date,timezone,start_at,end_at_exclusive,groups:[{day,cnt,ph_avg,temperature_avg,turbidity_avg,simulation_samples,non_simulation_samples,source_*}],total_samples,source_counts}`.
- AC2: Tanggal invalid → 422; periode tanpa data → `groups` kosong — **tidak difabrikasi** (sesuai perilaku terverifikasi).
- AC3: Sampel simulasi vs non-simulasi dihitung terpisah dan dilaporkan eksplisit.


### F7 — Alert

**FR-022** *[Should]* 🔶 `GET /api/alerts` (session, `?limit=1..100`) mengembalikan `[{id,device_id,severity,message,acknowledged,created_at,acknowledged_at,provenance,source_session}]`.


**FR-023** *[Should]* 🔶 `POST /api/alerts/{id}/acknowledge` (session + CSRF) menandai alert; tercatat di audit (`alert.acknowledged`).


### F8 — Jadwal pakan

**FR-024** *[Should]* 🔶 `GET /api/devices/{id}/schedules` (session) mengembalikan `[{id,time(HH:MM),duration,days,active,created_at}]`.




### F9 — Threshold milik user

**FR-025** *[Should]* 🔶 User terautentikasi dapat membaca threshold miliknya via `GET /api/thresholds`.
- AC1: Respons 200 memuat `{ph_min,ph_max,temperature_min,temperature_max,turbidity_max}`; tanpa session → 401 `unauthenticated`.

- AC1: Nilai overflow/divergen ditolak dengan 422 `validation_error`.
- AC2: Setiap perubahan tercatat di audit log (`thresholds.updated`) dan menghasilkan versi aturan baru yang idempoten (dapat dibaca via `GET /api/rule-versions`).


**FR-026** *[Could]* 🔶 `GET /api/rule-versions` (session) mengembalikan daftar versi threshold yang pernah diterapkan.
- AC1: Respons 200 berupa daftar `{id, version, rule, checksum_sha256, created_at}` urut terbaru→terlama.
- AC2: Idempoten — request tidak mengubah state server.
- AC3: Tanpa session valid → 401.

### F10 — Observasi pertumbuhan

**FR-027** *[Could]* 🔶 `GET /api/observations` (session, `?device_id=`) mengembalikan `[{id,device_id,observed_at,weight_g,length_cm,notes,...}]`.




### F11 — Export

**FR-028** *[Could]* 🔶 `GET /api/export` (session, `?device_id&kind=readings|alerts|commands|feeding_logs|reports|telemetry&period=day|week|month&date=YYYY-MM-DD`) mengembalikan CSV.
- AC1: Sel CSV di-guard dari formula injection (nilai diawali `=,+,-,@` dinetralkan).
- AC2: Filter invalid → 422.


### F12 — Workspace

**FR-029** *[Won't — rilis ini]* 🔶 `POST /api/workspaces/invitations` (session admin + CSRF) membuat undangan `{contact}`; token disimpan sebagai SHA-256, kedaluwarsa 24 jam.



**FR-030** *[Won't — rilis ini]* 🔶 `GET /api/workspaces/members` (session) daftar anggota.



### F13 — Produk/units

**FR-031** *[Won't — rilis ini]* 🔶 `POST /api/product/provision` (session seller + CSRF) membuat unit `{serial_number,name,location}` + kode aktivasi 16-char (TTL 30 hari).


**FR-032** *[Won't — rilis ini]* 🔶 `POST /api/product/claim` (session + CSRF) dengan `{serial,code}`; 5x gagal → lockout 15 menit; kode salah/kedaluwarsa → 409.


**FR-033** *[Won't — rilis ini]* 🔶 `GET /api/product/onboarding` (session, `?serial=`) status onboarding unit.



### F14 — Audit

**FR-034** *[Won't — rilis ini]* ❓ `GET /api/audit-logs` — operasi `AuditRepository::recent` terbukti ada di kode (aksi tercatat: auth.login/register, actuator.control, command.*, alert.acknowledged, schedule.*, thresholds.updated, device.*, telemetry.received), tetapi **path endpoint belum terverifikasi** (router.php tidak tersedia). Ditunda sampai path terkonfirmasi dari source.

---


## 3. Kebutuhan Data

Skema SQLite dipertahankan apa adanya (migrasi Flask memakai file DB yang sama — nol migrasi data). 19 tabel, kolom kunci:

| Tabel | Kolom kunci |
|---|---|
| `users` | id, username, contact, password_hash (bcrypt PHP — diverifikasi paket `bcrypt` di Flask), name, role (admin/viewer), phone, workspace_owner_id |
| `devices` | id (serial), user_id, name, location, online, aerator, feeder, auto_mode, sort_order, last_seen |
| `device_credentials` | device_id, key_hash (SHA-256), rotated_at |
| `device_inventory` | serial_number, default_name, default_location, claimed_user_id, claimed_at |
| `sensor_readings` | id, device_id, ph, temperature, turbidity, simulation, created_at, provenance, source_session |
| `device_telemetry` | id, device_id, created_at, received_at, provenance, simulation, source_session, payload (JSON mentah) |
| `actuator_commands` | id (hex 32-char), device_id, user_id, actuator, value, duration, request_id, status (pending/delivered/succeeded/failed/timeout), simulation, created_at, expires_at, delivered_at, completed_at, provenance, source_session |
| `alerts` | id, device_id, severity, message, acknowledged, created_at, acknowledged_at, provenance, source_session |
| `feeding_schedules` | id, device_id, time (HH:MM), duration, days, active |
| `threshold_settings` | user_id, ph_min, ph_max, temperature_min, temperature_max, turbidity_max |
| `rule_versions` | id, user_id, version, config_json, created_at |
| `reading_rule_versions` | reading_id, rule_id |
| `growth_observations` | id, user_id, device_id, observed_at, weight_g, length_cm, notes, provenance, source_session |
| `workspace_invitations` | id, owner_id, contact, token_hash, expires_at, accepted_at, revoked_at |
| `product_units` | serial, activation_hash, expires_at, used_at, key_hash, created_by, first_heartbeat, last_heartbeat |
| `activation_attempts` | user_id, serial, state_json (lockout) |
| `seller_operators` | user_id, granted_at |
| `audit_logs` | id, user_id, device_id, action, metadata, created_at, provenance, source_session |
| `api_rate_limits` | bucket, hits, expires_at |

Catatan data:
- Kolom `ph` tetap ada untuk kompatibilitas skema; dengan pH ditunda, sistem TIDAK mengisi/menampilkan `ph` sebagai pH air terkalibrasi (lihat NFR-025).
- `simulation` ditegakkan server-side pada ingest; data demo historis semuanya `simulation=1`.
- Semua timestamp UTC; zona Asia/Jakarta hanya di lapisan tampilan.

---

## 4. Kebutuhan Antarmuka

### 4.1 Skema autentikasi (tiga lapis)
- **Publik:** `/api/health`, `/api/rules`, `/api/auth/register`, `/api/auth/login` — tanpa auth.
- **Session user:** cookie `aquasmart_session` (HttpOnly, SameSite=Lax) + header `X-CSRF-Token` untuk SEMUA mutasi. Role `admin` vs `viewer`; viewer read-only → mutasi 403 `forbidden` ("Viewer hanya memiliki akses baca.").
- **Device-key:** header `X-Device-Key` (disimpan sebagai SHA-256); salah → 401 `device_unauthenticated`.

### 4.2 Envelope error & rate limit
- Format: `{"error":{"code":"...","message":"...","details"?:...}}`. Kode: `unauthenticated` 401, `device_unauthenticated` 401, `forbidden` 403, `csrf_mismatch` 403, `invalid_json` 400, `validation_error` 422, `payload_too_large` 413, `unsupported_media_type` 415, `rate_limited` 429 (+ header `Retry-After`); 409 untuk konflik (timestamp duplikat beda nilai, command terminal, `request_id` dipakai ulang).
- Rate limit: login 30/menit, register 10/menit, ingest device 240/menit per device (per IP).
- Kontrak umum: body JSON objek ≤ 64 KiB, nilai skalar; timestamp UTC ISO-8601 `...Z` ketat; CORS `*` + header `X-CSRF-Token, X-Device-Key`; security headers lengkap; `Cache-Control: no-store`.

### 4.3 Quirk kontrak yang WAJIB dipertahankan di Flask
- **Dual prefix:** `/api/devices/...` (telemetri) vs `/api/device/devices/...` (commands) — keduanya dipakai firmware; jangan disatukan.
- **Kontrak telemetri ketat** (FR-013 AC2): hanya menerima sensor belum terkalibrasi (`calibrated=false`, `ph_sensor=soil_placeholder`).
- **Threshold v2** sebagai default; dokumen API lama yang menyebut v1 tidak dijadikan acuan.

### 4.4 Kontrak firmware ESP32 (frozen — 3 endpoint)
1. `POST /api/devices/{id}/telemetry` — `X-Device-Key`; 201/409/422 = terminal.
2. `GET /api/device/devices/{id}/commands` — `X-Device-Key`; `{commands:[...]}`.
3. `POST /api/device/devices/{id}/commands/{id}/ack` — `X-Device-Key`, `{status: succeeded|failed|timeout}`; 200/409 = terminal, tidak ada aktuasi ulang.

---

## 5. Kebutuhan Non-Fungsional

**NFR-006** *[Must]* Kinerja ingest: sistem menangani laju ingest device sampai batas rate yang ditetapkan (240/menit/device) tanpa menolak request valid dan tanpa kehilangan data yang sudah dijawab 201.
- AC: Uji beban pada batas rate terdokumentasi → nol data hilang pada respons 201; 429 hanya untuk pelanggar batas (+ `Retry-After`).

**NFR-007** *[Must]* Keamanan:
- Password: hash bcrypt PHP lama harus terverifikasi di Flask (paket `bcrypt`); password baru memakai work factor setara.
- Device key: hanya hash SHA-256 yang disimpan; key mentah hanya ditampilkan sekali saat dibuat/rotasi.
- CSRF: semua mutasi session memerlukan header `X-CSRF-Token` yang valid (403 `csrf_mismatch` bila tidak).
- Cookie session HttpOnly + SameSite=Lax; security headers lengkap (Content-Type options, Frame DENY, Referrer, Permissions, CSP).
- AC operasional: file `railway-seed.local.txt` (kredensial admin nyata) sudah dihapus dari folder Drive publik dan password Railway sudah dirotasi SEBELUM deployment Flask; tidak ada kredensial di repo/code.

**NFR-025** *[Must]* Reliabilitas command: lifecycle `pending → delivered → succeeded|failed|timeout` dieksekusi benar; command kedaluwarsa otomatis via scheduler; idempotensi `request_id` (pakai ulang + parameter berbeda → 409); maksimal 1 perintah aktif per aktuator; ACK hanya untuk status `delivered`.
- AC: Uji skenario: poll → delivered; ack ganda → 409 kedua; command kedaluwarsa → timeout otomatis.

**NFR-025** *[Must]* Kejujuran data (integritas):
- Flag `simulation` ditegakkan server-side; firmware menolak command `simulation=true`.
- Report periode kosong → groups kosong, tidak difabrikasi.
- Nilai sensor belum terkalibrasi (turbidity non-NTU, TDS estimasi, soil pH placeholder) TIDAK BOLEH disajikan sebagai hasil ukur terkalibrasi; label "uncalibrated/estimasi" wajib tampil bila nilai ditampilkan.
- `GET /api/devices/{id}/heartbeat` melaporkan `hardware_verified:false` sampai ada bukti verifikasi fisik.
- AC: Audit tampilan dashboard — tidak ada angka yang mengklaim kalibrasi tanpa bukti kalibrasi.

**NFR-001** *[Must]* Kompatibilitas firmware: 3 endpoint kontrak (§4.4) path-nya frozen; perubahan kontrak hanya bersama update firmware. Dual-prefix quirk dipertahankan.

**NFR-002** *[Should]* Operasional: single-file SQLite (path terkonfigurasi, volume persistent di deployment); semua waktu internal UTC; log audit untuk aksi sensitif (login/register, control, command, threshold, key rotation, telemetry.received).

---

## 6. Prioritas MoSCoW (ringkas)

- **Must (12):** FR-001, FR-002, FR-003, FR-004, FR-006, FR-007, FR-008, FR-013, FR-015, FR-016, FR-017, FR-021; NFR-001–NFR-005.
- **Should (9):** FR-005, FR-009, FR-010, FR-011, FR-018, FR-022, FR-023, FR-024, FR-025; NFR-006.
- **Could (7):** FR-012, FR-014, FR-019, FR-020, FR-026, FR-027, FR-028.
- **Won't (rilis ini, 6):** FR-029, FR-030, FR-031, FR-032, FR-033, FR-034 (workspace, product/units, audit — path audit belum terverifikasi); dukungan sensor pH air (ditunda tahun depan).

## 7. Asumsi & Ketergantungan

- A-001: `router.php` tidak tersedia — 33 path endpoint bertanda 🔶 direkonstruksi dari method repository + nama test; verifikasi ulang saat source asli diperoleh. Tidak ada endpoint yang dikarang.
- A-002: Backend target adalah Flask (keputusan pemilik 10 Okt 2026); kontrak API dipertahankan identik dengan backend PHP.
- A-003: Sensor pH air ditunda ke tahun depan; kolom `ph` dipertahankan untuk kompatibilitas skema tetapi tidak dipresentasikan sebagai pH air.
- A-004: Seluruh hardware (turbidity, TDS, suhu, level, ESP32) sudah dimiliki pemilik; belum ada bukti ESP32 pernah di-flash/upload.
- A-005: Source frontend Next.js & BFF tidak ada di unduhan Drive (hanya di repo GitHub — di luar file yang dibedah); SRS ini mencakup sisi backend/API.
- Ketergantungan eksternal: firmware ESP32 (kontrak 3 endpoint frozen), file SQLite, layanan deployment (Railway — kredensial harus dirotasi dulu, lihat NFR-007).

---

## 8. Kriteria Penerimaan Rilis MVP (minggu ini)

1. Semua kebutuhan **Must** lolos acceptance criteria-nya (termasuk pytest yang di-port dari 104 test ID backend PHP).
2. Uji kontrak firmware hijau: telemetri → 201 dan tampil sebagai non-simulation; poll → delivered; ack → terminal; ack ganda → 409.
3. NFR-007 AC operasional terpenuhi (kredensial Drive dibersihkan + password dirotasi) sebelum deploy.
4. Dashboard melabeli data simulation vs nyata dengan benar (NFR-025).
5. Tidak ada data yang difabrikasi pada report periode kosong.

---

## 9. Traceability

| ID | Domain endpoint-inventory | Catatan |
|---|---|---|
| FR-001–FR-002 | §3 Auth ✅ | register & login — path terverifikasi |
| FR-003–FR-005 | §3 Auth 🔶 | logout, me, profile — path direkonstruksi |
| FR-006 | §1 Health ✅ | — |
| FR-007 | §2 Rules ✅ | threshold v2, bukan v1 |
| FR-008–FR-012 | §4 Devices 🔶 | path direkonstruksi |
| FR-013 | §5 Telemetry ✅ | kontrak firmware frozen |
| FR-014–FR-015 | §5 Telemetry 🔶 | path direkonstruksi |
| FR-016–FR-017 | §6 Commands ✅ | kontrak firmware frozen; quirk dual-prefix |
| FR-018–FR-020 | §6 Commands 🔶 | path direkonstruksi |
| FR-021 | §7 Reports ✅ | — |
| FR-022–FR-023 | §8 Alerts 🔶 | path direkonstruksi |
| FR-024 | §9 Schedules 🔶 | path direkonstruksi |
| FR-025–FR-026 | §2 Rules 🔶 | thresholds + rule-versions — path direkonstruksi |
| FR-027 | §12 Observations 🔶 | path direkonstruksi |
| FR-028 | §13 Export 🔶 | path direkonstruksi |
| FR-029–FR-030 | §10 Workspaces 🔶 | Won't rilis ini |
| FR-031–FR-033 | §11 Product 🔶 | Won't rilis ini |
| FR-034 | §14 Audit ❓ | path belum terverifikasi — Won't rilis ini |
| NFR-001–NFR-006 | lintas domain + temuan bedah firmware | — |

---

*Dokumen ini v1 — target state backend Flask, disusun 10 Okt 2026 dari kode aktual. Akan disempurnakan setelah verifikasi terhadap `router.php`/source asli bila diperoleh.*
