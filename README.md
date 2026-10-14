# AquaSmart AIoT — Paket Submission

**Versi:** 11 Oktober 2026
**Anggota:** Alpin Aditya Pratama (V3925004), Dimas Aryo Sejati (V3925022)

## Isi paket

| Folder | Isi |
|---|---|
| `backend/` | Backend Flask (Python) — pengganti PHP per SKPL V4.0. 68/68 test hijau. Lihat `backend/README.md` untuk cara menjalankan. |
| `frontend/` | Frontend Next.js 16 + BFF proxy. Set `AQUASMART_API_URL` ke URL backend Flask. |
| `firmware/` | Firmware ESP32 (Arduino). Status: dites 10 Okt 2026, semua berhasil. |
| `docs/` | SKPL V4.0, PRD, SRS, Arsitektur, Desain, Dokumen Rencana Penyelesaian. |

## Fitur yang dibuat (FR-01 s.d. FR-28)

Auth (register/login/logout/me), health, rules, devices, telemetry ingest,
readings, command poll/ACK, kontrol aktuator, reports, alerts, schedules,
thresholds, heartbeat, raw telemetry, feeding logs, rule versions,
observations, export CSV.

## Cara menjalankan backend (ringkas)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="isi-dengan-kunci-kuat"
python wsgi.py   # → http://127.0.0.1:8080
pytest -q        # → 68 passed
```

## Catatan

- Dokumen menunggu approval pengajar.
- Sensor pH ditunda ke tahun depan (keputusan pemilik).
- Kalibrasi formal sensor turbidity/TDS masih pending.
