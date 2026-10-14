# AquaSmart — Flask Backend

> **Status dokumen: menunggu approval pengajar.** Implementasi dan klaim
> pada dokumen ini belum disetujui; jangan dikutip sebagai hasil final
> yang sudah disahkan.

Rewrite backend PHP → Flask (Python), kontrak API dipertahankan identik
agar firmware ESP32 dan frontend Next.js tidak perlu diubah.

## 1. Instalasi tech stack (Urgensi)

| Paket | Urgensi | Alasan |
|---|---|---|
| Python 3.12 | 🔴 KRITIS | runtime utama |
| Flask 3.1 + Flask-SQLAlchemy 3.1 | 🔴 KRITIS | framework + ORM (skema SQLite dipakai ulang, nol migrasi) |
| bcrypt 5.0 | 🔴 KRITIS | verifikasi hash password PHP lama ($2y$) |
| Flask-Limiter 4.1 | 🟠 TINGGI | rate limit auth (10/30 per menit, sesuai kontrak) |
| gunicorn 26 | 🟠 TINGGI | server production di Railway |
| APScheduler 3.11 | 🟡 SEDANG | expiry command (pengganti `tick()` PHP) — belum dipakai |
| pytest 9.1 | 🟡 SEDANG | test kontrak API |

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Struktur repo

```
aquasmart-backend/
├── app/
│   ├── __init__.py        # factory, registrasi blueprint, error handler
│   ├── models.py          # 1:1 dengan skema SQLite PHP (19 tabel inti)
│   ├── auth.py            # X-Device-Key (SHA-256) + session + CSRF
│   ├── errors.py          # envelope {"error":{"code","message"}}
│   └── routes/
│       ├── public.py      # GET /api/health, GET /api/rules
│       ├── auth.py        # POST /api/auth/{register,login,logout}, GET /me
│       ├── telemetry.py   # POST /api/devices/<id>/telemetry
│       ├── readings.py    # GET /api/devices/<id>/readings
│       ├── devices.py     # GET /api/devices
│       ├── commands.py    # GET+POST /api/device/devices/<id>/commands[/ack]
│       ├── reports.py     # GET /api/reports
│       ├── settings.py    # GET /api/settings/thresholds
│       └── alerts.py      # GET /api/alerts
│       └── control.py     # POST /api/devices/<id>/control (FR-018)
├── tests/test_api.py      # 15 test kontrak (pytest)
├── instance/aquasmart.sqlite  # salinan demo.sqlite (dev)
├── config.py, wsgi.py, requirements.txt
└── FR-PRIORITY-TIMELINE.md
```

## 3. Menjalankan

```bash
export SECRET_KEY="ganti-dengan-yang-kuat"
python wsgi.py            # dev → http://127.0.0.1:8080
gunicorn wsgi:app         # production (Railway)
pytest tests/ -q          # 15 test
```

## 4. Koneksi backend → frontend

Frontend Next.js memakai BFF proxy (`app/api/[...path]/route.ts`):
browser → Next.js `/api/...` → `${AQUASMART_API_URL}/api/...`.
**Tidak perlu ubah kode frontend** — cukup arahkan env var:

```bash
# di Vercel / .env frontend
AQUASMART_API_URL=http://127.0.0.1:8080   # dev
AQUASMART_API_URL=https://<flask>.up.railway.app  # production
```

Bentuk respons Flask sudah disamakan dengan skema zod frontend
(`{devices:[...]}`, `{readings:[...]}`, `{thresholds:{...}}`,
`{alerts:[...], unacknowledged_count}`).

## 5. Kontrak yang dipertahankan dari PHP

- 3 endpoint firmware frozen (telemetry, poll, ack) + quirk dual-prefix
  `/api/devices` vs `/api/device/devices`
- Telemetri ketat: `calibrated=false`, `ph_sensor=soil_placeholder`,
  provenance cocok dengan simulation
- Error envelope + rate limit + threshold-rules-v2 + checksum SHA-256
