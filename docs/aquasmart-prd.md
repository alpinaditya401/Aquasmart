# PRD — AquaSmart
**Product Requirements Document — Sistem Monitoring Kualitas Air Kolam/Akuakultur IoT**

- Tanggal pembuatan: 10 Oktober 2026
- Versi: **v1**
- Status: Dokumen induk. Jika dokumen lain (DESIGN.MD, ARCHITECTURE.MD, SRS.MD) tidak sepakat dengan PRD ini, **PRD yang menang**.
- Metodologi: requirements berbasis bedah kode aktual (9–10 Okt 2026) + keputusan pemilik; ID permanen untuk setiap requirement (tidak boleh berubah antar revisi), prioritas MoSCoW, traceability antar dokumen.
- Sumber utama: `endpoint-inventory.md` (42 endpoint, 14 domain, skema 19 tabel — sumber kebenaran fitur), `bedah-techstack-2026-10-09.md`, `bedah-firmware-esp32-2026-10-10.md` (firmware 481 baris), `PROJECT_CONTEXT.md`, keputusan Alpin 10 Okt 2026 (migrasi backend PHP → Flask, hardware lengkap, pH ditunda 2027, deadline minggu ini).
- Target state dokumen ini: **backend Flask (Python)**. Setiap klaim fitur berdasar bukti di file grounding; yang belum terverifikasi ditandai eksplisit di §8.

---

## 1. Visi

**Setiap pemilik kolam ikan skala kecil bisa memantau kualitas air kolamnya secara real-time dan bertindak sebelum ikan bermasalah — dengan perangkat murah (ESP32) dan data yang jujur.**

Kejujuran data adalah prinsip yang tidak bisa dinegosiasi: data simulasi dan data nyata tidak boleh tercampur tanpa label; sensor yang belum dikalibrasi tidak boleh disajikan seolah akurat; klaim "production-ready" hanya boleh dipakai bila ada bukti uji. Dokumen proyek ini sendiri sudah mencabut klaim berlebihan di masa lalu — PRD ini melanjutkan tradisi itu.

---

## 2. Target User

**Primer: pemilik/pengelola kolam ikan skala kecil** — butuh tahu suhu, kekeruhan, dan TDS air kolam tanpa mengecek manual tiap jam; butuh kontrol aerator/feeder dari jauh; tidak punya budget sistem monitoring industrial.

**Sekunder: Alpin (pemilik & pengembang)** — membangun, mengoperasikan, dan memelihara sistem; butuh backend yang ia kuasai (Flask) agar bisa iterasi cepat.

**Tersier: dosen penilai (UNS)** — menilai kelengkapan proyek akhir praktikum dari kode, dokumen, dan bukti uji yang jujur.

**Bukan target:** tambak industrial multi-kolam (butuh arsitektur berbeda), pengguna yang butuh monitoring pH air presisi lab (sensor pH ditunda ke 2027 — lihat §8).

---

## 3. Masalah

1. **Kualitas air kolam berubah tanpa terpantau.** Suhu, kekeruhan, dan TDS yang di luar batas membuat ikan stres/mati; pengecekan manual jarang dilakukan dan tidak tercatat historinya.
2. **Kontrol aerator/feeder manual tidak terjadwal dan tidak tercatat.** Pemberian pakan dan aerasi bergantung ingatan; tidak ada log kapan aktuator menyala.
3. **Data sensor tanpa kalibrasi menyesatkan.** Tanpa kalibrasi 2-point, bacaan pH bisa meleset 0,5–1,0; mapping turbidity persen-bukan-NTU tidak bisa dipertanggungjawabkan. Sistem yang menyajikan angka mentah seolah akurat lebih berbahaya daripada tidak ada sistem.
4. **Solusi IoT existing terlalu mahal/kompleks untuk kolam kecil.** Butuh rakitan murah (ESP32 + sensor analog) dengan dashboard web sederhana.
5. **Status proyek saat ini: prototype/simulasi.** Backend PHP solid (104/104 test lolos) tapi pemilik memutuskan migrasi ke Flask; firmware nyata tapi belum pernah di-upload; semua data demo = simulasi; belum ada bukti ESP32 fisik berjalan.

---

## 4. Tujuan Produk

| # | Tujuan | Target terukur |
|---|---|---|
| G-001 | Backend Flask MVP live | 12 endpoint P0 (§5) merespons sesuai kontrak & lolos uji kontrak firmware akhir pekan ini |
| G-002 | Data nyata pertama | Telemetri dengan `simulation=0` dari ESP32 tampil di dashboard (bukan data seed) |
| G-003 | Kontrol end-to-end terbukti | 1 perintah aktuator (aerator) berhasil: dashboard → antrean → poll firmware → ACK `succeeded` |
| G-004 | Kredensial aman | `railway-seed.local.txt` dihapus dari folder Drive publik + password Railway dirotasi |
| G-005 | Test suite Flask hijau | pytest untuk 12 endpoint P0 lolos (di-port dari 104 test IDs backend PHP) |

Semua target di atas adalah target minggu ini (11–12 Okt 2026) — akan dievaluasi ulang sebelum v1.1.

---

## 5. Kebutuhan Fungsional

Setiap fitur punya ID permanen (format `FR-xxx`) yang dipakai identik di DESIGN.MD, ARCHITECTURE.MD, dan SRS.MD. **ID tidak boleh berubah** — jika requirement dihapus di revisi mendatang, ID-nya dipensiunkan, tidak dipakai ulang. Prioritas MoSCoW per FR.

### F1 — Autentikasi & Akun (session user)
- **FR-001** [Must] Registrasi pengguna: `POST /api/auth/register` — body `{name, contact (email/08xx), password, password_confirmation, serial_number?}`; respons 201 user aman (tanpa hash); seed thresholds default; 422 validasi; 409 kontak duplikat/serial dipakai; rate limit 10/menit.
- **FR-002** [Must] Login: `POST /api/auth/login` — `{username, password}`; respons 200 + cookie session HttpOnly SameSite=Lax + CSRF token; 401 kredensial salah; rate limit 30/menit.
- **FR-003** [Must] Logout: `POST /api/auth/logout` — session dihancurkan.
- **FR-004** [Must] Profil saat ini: `GET /api/auth/me` — `{id,name,contact,role,phone}` tanpa data sensitif.
- **FR-005** [Should] Update profil: `PATCH /api/profile` — `{name (1–100), phone}`; butuh CSRF.

### F2 — Health & Rules (publik)
- **FR-006** [Must] Health check: `GET /api/health` → `{"status":"ok","service":"aquasmart-api"}`.
- **FR-007** [Must] Threshold rules aktif: `GET /api/rules` → `{version:"threshold-rules-v2", rule:{...}, source_sha256}` + CORS. Threshold v2: pH 6,5–8,5; suhu 25–30 °C; turbidity maks 50.

### F3 — Perangkat (dashboard user)
- **FR-008** [Must] Daftar perangkat milik user: `GET /api/devices` — tiap item memuat status online, state aerator/feeder/auto, last_seen, dan latest_reading `{ph,temperature,turbidity,simulation,created_at,provenance,source_session}`.
- **FR-009** [Should] Klaim perangkat via serial: `POST /api/devices/claim` — `{serial}`; 409 bila sudah diklaim; 422 serial tak dikenal.
- **FR-010** [Should] Ubah nama/lokasi: `PATCH /api/devices/{id}` — `{name (1–100), location (1–150)}`; 404 bila bukan milik user.
- **FR-011** [Should] Rotasi device key: `POST /api/devices/{id}/key/rotate` — mengembalikan key mentah baru (yang disimpan hanya hash SHA-256).
- **FR-012** [Could] Heartbeat: `GET /api/devices/{id}/heartbeat` — `{device_id,last_seen,online}`.

### F4 — Telemetri (device → server)
- **FR-013** [Must] Ingest telemetri ESP32: `POST /api/devices/{id}/telemetry` — auth header `X-Device-Key`; kontrak kaya (ADC mentah + mV, `calibrated` harus `false`, `ph_sensor` harus `soil_placeholder` — kontrak saat ini hanya menerima sensor belum terkalibrasi); respons 201 ternormalisasi; 409 timestamp duplikat beda nilai; 422 validasi; update `last_seen`/`online`. **Dipakai firmware — kontrak tidak boleh berubah tanpa update firmware.**
- **FR-014** [Could] Lihat telemetri mentah: `GET /api/devices/{id}/telemetry?limit=1..100`.
- **FR-015** [Must] Bacaan ternormalisasi untuk grafik: `GET /api/devices/{id}/readings?limit=1..100` — `[{time,ph,temperature,turbidity,simulation,provenance,source_session}]` urut tertua→terbaru.

### F5 — Perintah aktuator (server → device)
- **FR-016** [Must] Poll commands oleh firmware: `GET /api/device/devices/{id}/commands` — auth `X-Device-Key`; respons `{"commands":[...]}`; pending→delivered. **Prefix `/api/device/devices/` adalah quirk nyata — jangan disatukan dengan `/api/devices/`.**
- **FR-017** [Must] ACK command: `POST /api/device/devices/{id}/commands/{commandId}/ack` — `{status: succeeded|failed|timeout}`; 409 bila belum delivered/sudah terminal.
- **FR-018** [Should] Kontrol aktuator dari dashboard: `POST /api/devices/{id}/control` — `{actuator: aerator|feeder|auto, value: bool, duration? (feeder 1–10), request_id?}`; butuh CSRF; 403 tanpa CSRF; 409 aktuator sibuk/request_id dipakai ulang. Command bertanda `simulation=true` DITOLAK (firmware menolak).
- **FR-019** [Could] Riwayat commands: `GET /api/devices/{id}/commands` — 100 terakhir.
- **FR-020** [Could] Feeding logs: `GET /api/devices/{id}/feeding-logs` — perintah feeder terminal.

### F6 — Laporan
- **FR-021** [Must] Agregasi laporan: `GET /api/reports?device_id&period=day|week|month&date=YYYY-MM-DD` — bucket harian UTC `{groups:[{day,cnt,ph_avg,temperature_avg,turbidity_avg,simulation_samples,non_simulation_samples}],total_samples}`; 422 tanggal invalid; periode kosong → groups kosong (tidak difabrikasi).

### F7 — Alert
- **FR-022** [Should] Daftar alerts: `GET /api/alerts?limit=1..100` — `{severity,message,acknowledged,...}`.
- **FR-023** [Should] Acknowledge alert: `POST /api/alerts/{id}/acknowledge` — butuh CSRF.

### F8 — Jadwal pakan
- **FR-024** [Should] CRUD feeding schedules: `GET/POST /api/devices/{id}/schedules`, `DELETE /api/schedules/{id}` — `{time (HH:MM), duration, days, active}`; mutasi butuh CSRF + role admin.

### F9 — Threshold milik user
- **FR-025** [Should] Lihat/ubah thresholds: `GET/PUT /api/thresholds` — 5 nilai (ph_min/max, temperature_min/max, turbidity_max); PUT butuh CSRF + admin; 422 bila overflow.
- **FR-026** [Could] Riwayat versi rules: `GET /api/rule-versions`.

### F10 — Observasi pertumbuhan
- **FR-027** [Could] CRUD observations: `GET/POST /api/observations`, `DELETE /api/observations/{id}` — `{device_id, observed_at ≤ hari ini, weight_g?, length_cm?, notes? ≤2000}`; minimal satu dari weight/length/notes.

### F11 — Export
- **FR-028** [Could] Export CSV: `GET /api/export?device_id&kind=readings|alerts|commands|feeding_logs|reports|telemetry&period&date` — CSV dengan proteksi formula-injection.

### F12 — Workspace (target v1.1)
- **FR-029** [Won't] Undangan workspace: `POST /api/workspaces/invitations` (token SHA-256, kedaluwarsa 24 jam) + `POST /api/workspaces/invitations/accept` (user menjadi viewer).
- **FR-030** [Won't] Kelola anggota: `GET/DELETE /api/workspaces/members/{id}`.

### F13 — Produk/units (target v1.1)
- **FR-031** [Won't] Provisioning unit: `POST /api/product/provision` — kode aktivasi 16-char TTL 30 hari.
- **FR-032** [Won't] Klaim unit: `POST /api/product/claim` — 5x gagal → lockout 15 menit.
- **FR-033** [Won't] Onboarding & dashboard unit: `GET /api/product/onboarding`, `GET /api/product/dashboard`.

### F14 — Audit (target v1.1)
- **FR-034** [Won't] Audit logs: `GET /api/audit-logs` — path belum terverifikasi (lihat §8 A-001); aksi tercatat: auth, actuator.control, command.*, alert.acknowledged, schedule.*, thresholds.updated, device.*, telemetry.received.

### Prioritas MoSCoW
- **Must (12):** FR-001, FR-002, FR-003, FR-004, FR-006, FR-007, FR-008, FR-013, FR-015, FR-016, FR-017, FR-021 — MVP minggu ini.
- **Should (9):** FR-005, FR-009, FR-010, FR-011, FR-018, FR-022, FR-023, FR-024, FR-025.
- **Could (7):** FR-012, FR-014, FR-019, FR-020, FR-026, FR-027, FR-028.
- **Won't v1.0 (6):** FR-029, FR-030, FR-031, FR-032, FR-033, FR-034 — target v1.1.

### ⚠️ Risiko scope (dicatat jujur)
Migrasi 12 endpoint Must + frontend + hardware dalam satu akhir pekan adalah risiko terbesar. Mitigasi yang disepakati dokumen ini: **urutan bangun bertahap** (auth → firmware contract → dashboard APIs → frontend → hardware), setiap endpoint P0 harus hijau di pytest sebelum lanjut; P1/P2 dipotong tanpa ragu bila waktu mepet.

## 6. Kebutuhan Non-Fungsional

- **NFR-001** Kontrak API identik dengan backend PHP: path, envelope error `{"error":{"code":"...","message":"..."}}`, dan kode status dipertahankan — firmware tidak boleh perlu diubah.
- **NFR-002** Autentikasi: session cookie HttpOnly + SameSite=Lax dan CSRF via header `X-CSRF-Token` untuk semua mutasi user; device via header `X-Device-Key` (disimpan sebagai SHA-256 di `device_credentials`).
- **NFR-003** Otorisasi role: `admin` vs `viewer`; viewer read-only — mutasi mengembalikan 403 `forbidden`.
- **NFR-004** Rate limiting: login 30/menit, register 10/menit, ingest device 240/menit per device (per IP); 429 + header `Retry-After`.
- **NFR-005** Simulation enforcement server-side: flag `simulation` + `provenance`/`source_session` harus konsisten; command bertanda simulation ditolak firmware.
- **NFR-006** Format data: timestamp UTC ISO-8601 `...Z` ketat; body JSON objek ≤ 64 KiB, nilai skalar saja.
- **NFR-007** Kompatibilitas password: hash bcrypt dari PHP (`password_hash()`) harus tetap terverifikasi di Flask — user existing tidak boleh dipaksa reset password.
- **NFR-008** Idempotensi: `request_id` yang dipakai ulang dengan parameter berbeda → 409.
- **NFR-009** Command lifecycle `pending → delivered → succeeded|failed|timeout` dengan expiry otomatis via scheduler; 1 perintah aktif per aktuator; ACK hanya untuk status `delivered`.
- **NFR-010** Threshold aktif adalah **v2** (pH 6,5–8,5; suhu 25–30 °C; turbidity ≤ 50) — dokumen API lama menyebut v1, yang berlaku v2 dari kode.
- **NFR-011** Kejujuran data di dashboard: data `simulation=1` dan `simulation=0` wajib dibedakan labelnya; tidak boleh tercampur tanpa penanda.
- **NFR-012** Quirk dual-prefix dipertahankan: `/api/devices/...` (telemetry) dan `/api/device/devices/...` (commands) tetap terpisah.
- **NFR-013** Security headers lengkap di semua respons; CORS `*` minimal untuk `/api/rules`; `Cache-Control: no-store` untuk API.
- **NFR-014** Channel pH **nonaktif** sampai 2027 (keputusan pemilik 10 Okt 2026 — sensor pH ditunda karena biaya); kolom pH tetap ada di skema tapi tidak diisi data nyata.

## 7. Scope

### 7.1 MVP minggu ini (11–12 Okt 2026) — "jadi" =
1. Backend Flask: 12 endpoint Must (§5) live, kontrak identik, pytest P0 hijau (G-001, G-005).
2. Frontend: 4 halaman — Login, Dashboard (daftar device + bacaan terakhir), Detail device (grafik), Reports — dengan label simulasi vs nyata (NFR-011).
3. Hardware: wiring lengkap (turbidity, TDS, suhu, level, ESP32), kalibrasi turbidity + TDS, firmware ter-upload pertama kali.
4. Bukti hidup: telemetri nyata pertama tampil (G-002) + 1 perintah aktuator end-to-end berhasil (G-003).
5. Keamanan: kredensial Railway diamankan (G-004).

### 7.2 v1.1 (minggu depan dan seterusnya)
- Endpoint Should/Could: thresholds user, alerts, schedules, control lanjutan, export CSV, observations, heartbeat, key rotation.
- FR-029–FR-034 (workspace, product/units, audit logs).
- Kalibrasi presisi lab-grade, UAT formal + SUS, dokumentasi akademik final.
- Sensor pH air: **2027** (keputusan pemilik; bukan bagian v1.x 2026).

## 8. Asumsi & Batasan

**Asumsi (ditandai jujur — diverifikasi vs belum):**
- A-001 *(sebagian belum terverifikasi)*: `router.php` tidak ikut terunduh — 8 endpoint path-nya ✅ terverifikasi (dari firmware/dokumen/nama test), 33 endpoint operasinya terbukti dari kode tapi path-nya direkonstruksi (🔶), 1 belum terverifikasi (❓ `GET /api/audit-logs`). Kontrak final menunggu `router.php` asli bila diperoleh.
- A-002 *(belum terverifikasi lokal)*: source frontend Next.js ada di repo GitHub `alpinaditya401/Testing-Project` (folder `frontend/`, terlihat di README) — belum diverifikasi isinya secara lokal.
- A-003 *(keputusan pemilik)*: backend dimigrasi PHP → Flask; threshold v2 yang berlaku (dokumen API lama menyebut v1 — diabaikan).
- A-004 *(snapshot)*: angka harga hardware adalah snapshot riset 10 Okt 2026, bukan cek harga live, belum termasuk ongkir.
- A-005 *(keputusan pemilik)*: sensor pH ditunda ke 2027; kolom pH tetap ada di skema database.

**Batasan:**
- B-001: Firmware ESP32 tidak diubah dalam scope ini — 3 endpoint kontraknya (telemetry, commands poll, ack) harus dipertahankan persis.
- B-002: Belum ada bukti ESP32 fisik pernah di-flash/upload — risiko hardware nyata (wiring salah bisa merusak board; ECHO HC-SR04 5V wajib divider).
- B-003: Semua data historis di demo.sqlite adalah simulasi (`simulation=1`, provenance `seed`) — tidak boleh dipakai sebagai bukti kinerja sistem.
- B-004: File `railway-seed.local.txt` berisi kredensial admin Railway nyata ada di folder Drive **publik** — penghapusan + rotasi password adalah prasyarat sebelum deployment apa pun.
- B-005: Dokumen ini tidak mencakup: multi-kolam industrial, monitoring pH presisi lab, dan aplikasi mobile native.

## 9. Traceability

Setiap FR-xxx di dokumen ini dipetakan ke: kebutuhan bernomor di SRS.MD (§2–3), modul di ARCHITECTURE.MD, dan layar di DESIGN.MD. ID bersifat permanen lintas revisi dokumen. FR Must (12) → modul Flask `blueprints/` + halaman dashboard W-001–W-004 (detail di DESIGN.MD).

---

*Dokumen ini v1 — dibuat 10 Oktober 2026 dari bedah kode aktual. Akan direvisi setelah MVP akhir pekan dievaluasi.*
