# DESIGN.MD — AquaSmart
**Desain UI/UX & Alur Layar — Sistem Monitoring Kualitas Air Kolam/Akuakultur IoT**

- Tanggal pembuatan: 10 Oktober 2026
- Versi: **v1 — untuk rebuild frontend (deadline minggu ini)**
- Acuan: `endpoint-inventory.md` (42 endpoint, 19 tabel — hasil bedah kode aktual 10 Okt 2026). Jika tidak sepakat, **endpoint-inventory menang**.
- Status endpoint di dokumen ini: ✅ = path terverifikasi dari sumber langsung; 🔶 = operasi terbukti, path direkonstruksi (belum terverifikasi penuh). Lihat endpoint-inventory.md untuk legenda lengkap.
- Prinsip: (1) **kejujuran data** — setiap angka berlabel provenance (nyata vs simulasi) + waktu, tanpa kecuali; (2) **mobile-first untuk cek kolam** — dibaca dari HP di lokasi, outdoor-readable; (3) **anti-slop** — keputusan konkret, tidak ada filler generik.
- ⚠️ **Catatan penting:** mockup HTML 5 halaman yang ada di repo adalah **STUB statis, BUKAN desain final** (tombol disabled, tertulis "MOCKUP STATIS"). Dokumen ini menggantikannya sebagai acuan desain yang berlaku.
- ⚠️ **Keputusan produk (10 Okt 2026):** sensor pH **DITUNDA ke tahun depan**. UI memperlakukan pH sebagai metrik "segera hadir" — tampil hanya jika data pH nyata & terkalibrasi tersedia; jika tidak, tampilkan state kosong yang jujur, bukan angka placeholder.

---

## 1. Prinsip Desain (kontrak yang mengikat implementasi)

### 1.1 Kejujuran data adalah fitur #1
- Setiap angka sensor WAJIB ditemani dua label: **provenance** (NYATA / SIMULASI) dan **waktu** (kapan diukur). Angka tanpa label provenance adalah bug.
- Data `simulation=1` tidak boleh disamarkan menjadi data nyata — tidak lewat warna, tidak lewat copywriting, tidak lewat posisi.
- Periode kosong (tidak ada bacaan) → tampilkan kosong. **Fabrikasi data dilarang** — backend sendiri tidak memfabrikasi (groups kosong = kosong), frontend wajib sama.

### 1.2 Mobile-first untuk cek kolam
- Alpin mengecek kolam dari HP di lokasi. Dashboard harus terbaca dalam 3 detik di layar 360px, di bawah sinar matahari (kontras tinggi, angka besar).
- Satu layar = satu tugas. Tidak ada dashboard yang memamerkan 12 widget sekaligus.

### 1.3 Kontrol fisik = konfirmasi eksplisit
- Setiap perintah aktuator (aerator/feeder) membuka dialog konfirmasi yang menyebut **durasi lease** (maks 30 detik) dan sifatnya (perintah terkirim ≠ motor berputar — sesuai komentar jujur di firmware).
- Tidak ada tombol "langsung jalan" untuk aktuator. Tidak ada double-submit (gunakan `request_id` idempoten).

### 1.4 Role terlihat di UI, bukan di error
- Viewer (read-only) **tidak pernah** melihat tombol aksi yang pasti 403 ("Viewer hanya memiliki akses baca."). Tombol admin disembunyikan untuk viewer sejak render pertama — bukan setelah diklik lalu error.
- Halaman admin (Workspaces, rotasi key) tidak ada di navigasi viewer.

### 1.5 Setiap halaman punya 4 state
Default, loading (skeleton, bukan spinner penuh), empty (1 aksi jelas), error (pesan jujur + tombol coba lagi — bedakan 401/403/422/429/500 dengan copy yang tepat, lihat §4).

---

## 2. Identitas Visual (ringkas, berpendapat)

AquaSmart bukan "startup dashboard biru generik". Identitasnya: **ruang kontrol kolam** — utilitarian, kontras tinggi, jujur.

- **Warna semantik (tetap, jangan dipakai untuk dekorasi):** hijau = OK/normal; kuning/amber = SIMULASI atau peringatan; merah = ALERT/offline/error; abu = tidak ada data. Arti warna tidak boleh berubah antar halaman.
- **Angka adalah hero:** bacaan sensor ditampilkan besar (≥28sp) dengan satuan jelas (°C, NTU, ppm, %). Label provenance selalu di bawah angka, bukan disembunyikan di tooltip.
- **Tipografi:** tanpa custom font di v1 — pakai system font stack Next.js. Alasan sadar: kecepatan dan konsistensi lebih penting daripada "kepribadian font" untuk alat operasional.
- **Mode gelap:** didukung (cek kolam malam hari), tapi bukan prioritas MVP — v1 fokus light mode kontras tinggi yang outdoor-readable.
- **Ikonografi:** ikon garis (outline) yang fungsional; satu-satunya ikon "emosional" yang diizinkan adalah indikator status device (● online / ○ offline).

---

## 3. Arsitektur Informasi & Peta Halaman

**Navigasi utama (setelah login) — sidebar desktop / bottom nav mobile, 5 item:**

| Posisi | Halaman | ID | Keterangan |
|---|---|---|---|
| 1 | Dashboard | A-003 | Daftar device + kartu bacaan terakhir — layar flagship |
| 2 | Reports | A-005 | Agregasi day/week/month |
| 3 | Alerts | A-006 | Daftar alert + acknowledge (badge jumlah belum dibaca) |
| 4 | Schedules | A-007 | Jadwal pakan per device |
| 5 | Settings | A-008 | Thresholds + profil + (admin) workspaces & device key |

**Halaman di luar nav utama:** A-001 Login, A-002 Register, A-004 Device Detail (dari kartu device), A-009 Workspaces (admin, via Settings), A-010 Accept Invitation.

**Aturan nav:** viewer tidak melihat menu admin di Settings; badge Alerts hanya menghitung `acknowledged=false`.

---

## 4. Spesifikasi Halaman

### A-001 Login — layar MVP
- **Tujuan:** masuk dalam <30 detik. **Endpoint:** ✅ `POST /api/auth/login` `{username, password}` → 200 + cookie `aquasmart_session` (HttpOnly) + CSRF token (simpan di memory/JS, kirim sebagai header `X-CSRF-Token` di semua mutasi).
- **Komponen:** form 2 field (username = email atau nomor 08xx, password) + tombol "Masuk" + link "Daftar".
- **States & error (copy jujur):**
  - 401 `unauthenticated` → "Username atau password salah." (jangan bocorkan mana yang salah)
  - 429 `rate_limited` → "Terlalu banyak percobaan. Coba lagi dalam X detik." (baca header `Retry-After`)
  - 422 `validation_error` → tampilkan pesan validasi per field dari respons
  - Network error → "Tidak bisa terhubung ke server. Periksa koneksi." + tombol coba lagi
- **Validasi client:** kedua field wajib diisi sebelum tombol aktif; password minimal sesuai aturan server (jangan hardcode angka yang tidak terverifikasi — tampilkan pesan server apa adanya).
- **Setelah sukses:** redirect ke A-003. Simpan juga info role untuk aturan §1.4.

### A-002 Register — layar MVP-pendamping
- **Tujuan:** pendaftaran + klaim device opsional. **Endpoint:** ✅ `POST /api/auth/register` `{name, contact, password, password_confirmation, serial_number?}` → 201 user aman (tanpa hash) + session langsung.
- **Komponen:** form 4 field + 1 opsional (nomor seri device untuk klaim langsung).
- **Error:** 422 validasi per field; 409 `kontak duplikat` → "Email/nomor ini sudah terdaftar. Masuk saja."; 409 `serial sudah dipakai` → "Nomor seri ini sudah diklaim device lain."
- **Catatan desain (asumsi):** field nomor seri diberi helper text "Opsional — ada di stiker perangkat" agar user tidak bingung.

### A-003 Dashboard — LAYAR FLAGSHIP (MVP)
- **Tujuan:** status semua kolam dalam 3 detik. **Endpoint:** 🔶 `GET /api/devices` → array `{id,name,location,online,aerator,feeder,auto,last_seen,latest_reading{ph,temperature,turbidity,simulation,created_at,provenance,source_session}}`.
- **Layout:**
```
┌─────────────────────────────┐
│ 🐟 AquaSmart      [🔔2] [👤] │  ← header: judul + badge alert + profil
├─────────────────────────────┤
│ ┌─ KOLAM 1 ───────────────┐ │
│ │ ● Online · 2 mnt lalu   │ │  ← status + last_seen relatif
│ │  28,4 °C   12 NTU       │ │  ← 2 metrik primer besar
│ │ [SIMULASI] 10:42:11     │ │  ← label provenance + waktu (WAJIB)
│ │ [Lihat detail →]        │ │
│ └─────────────────────────┘ │
│ ┌─ KOLAM 2 ───────────────┐ │
│ │ ○ Offline · 3 jam lalu  │ │  ← abu-abu, tidak disembunyikan
│ │ -- °C   -- NTU          │ │  ← strip, bukan 0 (0 = data palsu)
│ │ [Lihat detail →]        │ │
│ └─────────────────────────┘ │
│ [+ Tambah device]           │  ← klaim serial (A-002-style dialog)
└─────────────────────────────┘
```
- **Aturan kartu device:**
  - Metrik primer = suhu + turbidity (sensor yang dimiliki). TDS + level tampil sebagai baris sekunder kecil. pH **tidak** tampil sebagai kartu (ditunda — lihat catatan §1).
  - `latest_reading = null` atau device offline → tampilkan strip `--`, JANGAN angka 0.
  - Badge `[SIMULASI]` (amber) vs `[NYATA]` (hijau) selalu di bawah angka, beserta `created_at` ("10:42:11" + tanggal jika bukan hari ini).
  - `last_seen` relatif ("2 mnt lalu"); jika >120 dtk (HEARTBEAT_FRESH) → status offline otomatis di UI meski flag `online` true (asumsi desain — konsisten dengan `config/product.php`).
- **States:** loading = skeleton 2 kartu; empty ("Belum ada device — klaim device pertamamu" + tombol); error 401 → redirect login.
- **Aksi:** ketuk kartu → A-004. Tombol "+ Tambah device" → dialog klaim serial (🔶 `POST /api/devices/claim`).

### A-004 Device Detail — LAYAR MVP
- **Tujuan:** pantau + kendalikan satu kolam. **Endpoint:**
  - 🔶 `GET /api/devices/{id}/readings?limit=100` → `[{time,ph,temperature,turbidity,simulation,provenance,source_session}]` (urut tertua→terbaru — langsung bisa digrafik)
  - 🔶 `GET /api/devices/{id}/telemetry?limit=100` → payload mentah + `received_at` (tab "mentah", untuk debugging)
  - 🔶 `GET /api/devices/{id}/commands` → riwayat 100 perintah terakhir
  - 🔶 `GET /api/devices/{id}/heartbeat` → `{last_seen, online, hardware_verified:false}`
  - 🔶 `POST /api/devices/{id}/control` (admin + CSRF) → perintah aktuator
- **Layout:**
```
┌─────────────────────────────┐
│ ← KOLAM 1        [SIMULASI] │  ← badge provenance global halaman
│ ● Online · update 12 dtk lalu│
├─────────────────────────────┤
│ [Grafik: Suhu °C  24 jam ▾] │  ← tab metrik: Suhu|Turbidity|TDS|Level
│  ┌──────────────────────┐   │
│  │   /\      /\         │   │  ← garis putus-putus = titik simulasi
│  │__/  \____/  \________│   │     garis penuh = titik nyata
│  └──────────────────────┘   │
│ Rentang: [24j▾]             │  ← 24j / 7h? (asumsi: 24j, 7d)
├─────────────────────────────┤
│ KONTROL (admin saja)        │
│ Aerator   [● ON ] [Kirim]   │
│ Feeder    [○ OFF] [Kirim]   │
│ Auto mode [toggle]          │
├─────────────────────────────┤
│ RIWAYAT PERINTAH            │
│ 10:41 aerator ON → ✅       │
│ 10:38 feeder 5s → ⏱ timeout │
└─────────────────────────────┘
```
- **Aturan grafik (kontrak kejujuran):**
  - Titik `simulation=1` digambar **garis putus-putus + warna amber**; titik nyata garis penuh hijau. Legend selalu tampil. Grafik campuran tanpa legend = bug.
  - Sumbu-x = waktu UTC yang dikonversi ke Asia/Jakarta di label (catat zona di kaki grafik: "waktu WIB").
  - Rentang kosong → area grafik kosong + teks "Tidak ada data pada rentang ini" (jangan interpolasi).
- **Dialog konfirmasi aktuator (wajib):**
```
┌─────────────────────────────┐
│ Nyalakan Aerator?           │
│ Device: KOLAM 1             │
│ Durasi: 30 detik (maks)     │
│ ⚠️ Perintah terkirim ≠ motor │
│    berputar — status final  │
│    menunggu ACK perangkat.  │
│ [Batal]  [Ya, kirim]        │
└─────────────────────────────┘
```
  - Untuk feeder: tambah input durasi 1–10 detik (validasi: di luar itu → 422, tampilkan pesan server).
  - Setelah kirim: tampilkan status perintah live — `pending → delivered → succeeded|failed|timeout` (poll 🔶 `GET /api/devices/{id}/commands` atau refresh manual + auto-refresh 5 dtk sampai terminal).
  - Double-submit dicegah: tombol disable setelah diklik; `request_id` unik per klik (UUID client).
  - 403 (viewer/CSRF) → "Kamu tidak punya akses kontrol."; 409 (aktuator sibuk) → "Aerator sedang menjalankan perintah lain. Tunggu selesai."
- **Tab "Data mentah" (opsional, untuk debugging):** tampilkan `device_telemetry` payload apa adanya — berguna saat verifikasi sensor baru.

### A-005 Reports — LAYAR MVP
- **Tujuan:** agregat harian/mingguan/bulanan per device. **Endpoint:** ✅ `GET /api/reports?device_id&period=day|week|month&date=YYYY-MM-DD` → `{groups:[{day,cnt,ph_avg,temperature_avg,turbidity_avg,simulation_samples,non_simulation_samples}], total_samples, source_counts}`.
- **Layout:** pemilih device (dropdown) + pemilih periode (Day|Week|Month segmented) + date picker → tabel agregasi + ringkasan.
- **Aturan tabel:**
  - Kolom: Tanggal | n sampel | Suhu rata-rata | Turbidity rata-rata | label campuran ("3 nyata + 12 simulasi" bila keduanya ada).
  - Baris yang 100% simulasi → badge amber di baris itu.
  - Periode kosong → "Tidak ada data pada periode ini." (backend tidak memfabrikasi — frontend wajib sama).
  - 422 tanggal invalid → "Tanggal tidak valid." (jangan kirim tanggal invalid dari client — validasi format YYYY-MM-DD dulu).
- **Ringkasan atas:** total sampel + rentang tanggal aktual (dari `start_at`/`end_at_exclusive`, tampilkan sebagai WIB).

### A-006 Alerts
- **Endpoint:** 🔶 `GET /api/alerts?limit=100` → `[{id,device_id,severity,message,acknowledged,created_at,...}]`; 🔶 `POST /api/alerts/{id}/acknowledge` (CSRF).
- **Layout:** daftar alert, terbaru di atas; tiap item = severity (warna), pesan, device, waktu; swipe/ketuk "Tandai dibaca".
- **Aturan:** alert yang belum di-acknowledge tampil beda (bold + dot); acknowledge = aksi CSRF — viewer tidak melihat tombolnya (§1.4).
- **Empty:** "Tidak ada alert. Kolam aman 🎉" (hanya jika benar-benar kosong — jangan tampilkan saat error load).

### A-007 Schedules (jadwal pakan)
- **Endpoint:** 🔶 `GET/POST /api/devices/{id}/schedules` (POST: admin + CSRF `{time, duration, days}`), 🔶 `DELETE /api/schedules/{id}`.
- **Layout:** daftar jadwal per device: jam (HH:MM), durasi, hari aktif (chip S S R K J S M), toggle aktif, tombol hapus (konfirmasi).
- **Validasi:** format jam HH:MM 24-jam; durasi >0; minimal 1 hari dipilih — pesan error dari server (422) ditampilkan apa adanya.

### A-008 Settings & Thresholds
- **Endpoint:** 🔶 `GET /api/thresholds` → `{ph_min,ph_max,temperature_min,temperature_max,turbidity_max}`; 🔶 `PUT /api/thresholds` (admin + CSRF); ✅ `GET /api/rules` (publik, checksum SHA-256 — tampilkan versi rule aktif, mis. "threshold-rules-v2").
- **Layout:** form 5 angka threshold (admin bisa edit, viewer read-only — field disabled + helper "hanya admin").
- **Aturan:** 422 overflow → tampilkan pesan server; setelah PUT sukses, tampilkan versi rule baru + waktu (dari 🔶 `GET /api/rule-versions` — riwayat versi, bagus untuk audit).
- **Profil:** 🔶 `PATCH /api/profile` (nama, phone) — di tab terpisah dalam Settings.
- **Zona bahaya (admin):** rotasi device key (🔶 `POST /api/devices/{id}/key/rotate` → tampilkan key mentah SEKALI dengan peringatan "salin sekarang, tidak bisa dilihat lagi").

### A-009 Workspaces (admin saja)
- **Endpoint:** 🔶 `POST /api/workspaces/invitations` (admin + CSRF `{contact}`), 🔶 `GET /api/workspaces/members`, 🔶 `DELETE /api/workspaces/members/{id}`.
- **Layout:** daftar anggota (nama, role admin/viewer) + tombol "Undang" (dialog input kontak) + "Cabut akses" (konfirmasi).
- **Catatan:** undangan kedaluwarsa 24 jam (token SHA-256) — tampilkan status kedaluwarsa di daftar.

### A-010 Accept Invitation (asumsi desain — path menyusul backend)
- Halaman publik bertoken: tempel/buka link undangan → login/dftar dulu bila perlu → 🔶 `POST /api/workspaces/invitations/accept` → jadi viewer. Token salah/kedaluwarsa → pesan jelas, bukan 500.

---

## 5. Komponen UI Bersama

| Komponen | Spesifikasi |
|---|---|
| `DeviceCard` | Nama, lokasi, status online/offline, 2 metrik primer besar + 2 sekunder kecil, badge provenance + waktu. Offline → strip `--`, bukan 0. |
| `ProvenanceBadge` | `[NYATA]` hijau / `[SIMULASI]` amber. Selalu berdampingan dengan timestamp. Ukuran min 11sp, kontras AA. |
| `MetricHero` | Angka ≥28sp + satuan + label metrik + badge provenance di bawahnya. |
| `TimeSeriesChart` | Garis penuh (nyata) vs putus-putus (simulasi); legend wajib; label sumbu WIB; empty state jujur. |
| `AggTable` | Tabel agregasi reports dengan kolom campuran nyata/simulasi per baris. |
| `ActuatorDialog` | Konfirmasi + durasi lease + disclaimer ACK; cegah double-submit via `request_id`. |
| `StatusDot` | ● hijau online / ○ abu offline / ● amber peringatan. Jangan pakai warna saja — selalu ada teks. |
| `EmptyState` | Ilustrasi sederhana + 1 kalimat jujur + 1 aksi. Beda copy untuk "belum ada data" vs "gagal load". |
| `ErrorBanner` | Pesan per kode error (401/403/422/429/500) — lihat §4. Tombol "Coba lagi" hanya untuk error yang bisa dicoba lagi (bukan 401/403). |
| `SkeletonCard` | Placeholder loading berbentuk kartu (bukan spinner penuh). |

---

## 6. User Flows Kunci

### Flow A — Login → dashboard
1. Buka app → belum ada session → A-001.
2. Isi username + password → "Masuk" → ✅ `POST /api/auth/login`.
3. Sukses → simpan CSRF token → redirect A-003 → 🔶 `GET /api/devices` → render kartu.
4. 401 → pesan salah; tetap di A-001 (jangan redirect buta).

### Flow B — Detail device → perintah aerator → ACK
1. A-003 → ketuk kartu → A-004 → 🔶 readings + commands dimuat paralel.
2. (admin) Atur Aerator ON → "Kirim" → `ActuatorDialog` (durasi lease 30 dtk + disclaimer) → "Ya, kirim".
3. 🔶 `POST /api/devices/{id}/control` `{actuator:"aerator", value:true, request_id:<uuid>}` + header `X-CSRF-Token`.
4. Tampilkan status `pending` → poll `GET /api/devices/{id}/commands` tiap 5 dtk → `delivered` → `succeeded`/`failed`/`timeout` → berhenti poll, tampilkan hasil final.
5. 409 (sibuk) → "tunggu perintah sebelumnya selesai"; 403 → pesan akses.

### Flow C — Baca reports mingguan
1. A-005 → pilih device → periode "Week" → pilih tanggal (hari apapun dalam minggu itu).
2. ✅ `GET /api/reports?device_id=..&period=week&date=..` → tabel 7 baris + ringkasan.
3. Baris full-simulasi berlabel amber; minggu kosong → empty state jujur.

---

## 7. Aturan Label Data (kontrak kejujuran — checklist review)

1. Setiap angka sensor di UI ditemani badge `[NYATA]`/`[SIMULASI]` + timestamp. Tidak ada pengecualian.
2. Campuran nyata+simulasi dalam satu agregat → tulis komposisinya ("3 nyata + 12 simulasi").
3. Periode/rentang kosong → teks kosong yang jujur. Dilarang: interpolasi, angka 0 sebagai pengganti null, "estimasi" tanpa label.
4. Waktu tampil = WIB dengan label zona; waktu kirim ke API = UTC `...Z` ketat.
5. pH: tidak ditampilkan sebagai metrik aktif sampai sensor pH air terpasang & terkalibrasi (keputusan 10 Okt 2026). Jika API mengembalikan `ph`, tampilkan hanya dengan badge kalibrasi yang jelas; jika tidak ada, sembunyikan kartu pH (jangan tampilkan strip permanen yang membingungkan).
6. Copy dilarang: "real-time" untuk data simulasi; "terverifikasi" untuk klaim tanpa bukti.

---

## 8. Aksesibilitas & Responsif Dasar

- **Responsif:** breakpoint tunggal — ≤768px = layout mobile (bottom nav, kartu penuh); >768px = sidebar + grid 2–3 kolom. Grafik tetap terbaca di 360px (sumbu-x diringkas).
- **Sentuh:** target sentuh ≥48dp; tombol aktuator ≥56dp (aksi fisik, jangan sampai salah ketuk).
- **Kontras:** teks di atas badge berwarna memenuhi WCAG AA; angka hero tidak boleh tipis (min semibold).
- **Status tidak berwarna saja:** online/offline/simulasi selalu punya teks pendamping (§5 `StatusDot`).
- **Text scaling:** hormati pengaturan sistem sampai 200% tanpa teks terpotong di kartu device.
- **Basa:** Bahasa Indonesia; format angka Indonesia (koma desimal: "28,4 °C").

---

## 9. Pantangan Implementasi UI (checklist review)

1. Dilarang menampilkan angka sensor tanpa badge provenance + timestamp (§7).
2. Dilarang memfabrikasi data untuk periode kosong.
3. Dilarang menanam device key di frontend (hanya firmware yang memakai `X-Device-Key`).
4. Dilarang menampilkan tombol aksi admin ke viewer.
5. Dilarang hardcode base URL API per-file (satu env var).
6. Dilarang parsing pesan error untuk logika UI — pakai `error.code`.
7. Dilarang auto-retry tanpa batas untuk 429 (hormati `Retry-After`).
8. Dilarang mengirim tanggal invalid ke `/api/reports` (validasi `YYYY-MM-DD` di client).
9. Setiap halaman lolos 4 state (§1.5) + 401/403 handling yang benar.
10. Copy Bahasa Indonesia yang jujur — tidak ada klaim "real-time terverifikasi" tanpa bukti.

---

## 10. Traceability Halaman → Endpoint

| Halaman | Endpoint (status verifikasi) |
|---|---|
| A-001 Login | ✅ `POST /api/auth/login` |
| A-002 Register | ✅ `POST /api/auth/register` |
| A-003 Dashboard | 🔶 `GET /api/devices`, 🔶 `POST /api/devices/claim` |
| A-004 Device Detail | 🔶 `GET /api/devices/{id}/readings`, 🔶 `GET /api/devices/{id}/telemetry`, 🔶 `GET /api/devices/{id}/commands`, 🔶 `GET /api/devices/{id}/heartbeat`, 🔶 `POST /api/devices/{id}/control` |
| A-005 Reports | ✅ `GET /api/reports` |
| A-006 Alerts | 🔶 `GET /api/alerts`, 🔶 `POST /api/alerts/{id}/acknowledge` |
| A-007 Schedules | 🔶 `GET/POST /api/devices/{id}/schedules`, 🔶 `DELETE /api/schedules/{id}` |
| A-008 Settings | 🔶 `GET/PUT /api/thresholds`, ✅ `GET /api/rules`, 🔶 `GET /api/rule-versions`, 🔶 `PATCH /api/profile`, 🔶 `POST /api/devices/{id}/key/rotate` |
| A-009 Workspaces | 🔶 `POST /api/workspaces/invitations`, 🔶 `POST /api/workspaces/invitations/accept`, 🔶 `GET /api/workspaces/members`, 🔶 `DELETE /api/workspaces/members/{id}` |
| A-010 Accept Invitation | 🔶 `POST /api/workspaces/invitations/accept` |

**Ditandai asumsi desain (bukan dari endpoint):** struktur route Next.js (`/dashboard`, `/devices/[id]`, dsb.), nama halaman, pilihan visual (warna, ukuran font), copy Bahasa Indonesia, auto-refresh 5 detik pada status perintah, aturan offline-otomatis dari `HEARTBEAT_FRESH`, dan halaman A-010 (path backendnya belum terverifikasi).

---

*Dokumen ini v1 — dibuat 10 Okt 2026 untuk rebuild frontend dengan deadline minggu ini. Akan disempurnakan setelah review Alpin dan ketersediaan source frontend.*
