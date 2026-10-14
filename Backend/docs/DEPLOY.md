# DEPLOY.md — Cara deploy (belum dilakukan)

> Status: panduan ini **belum dieksekusi**. Jangan tulis bahwa deploy
> sudah berhasil sebelum ada bukti URL live + health check hijau.

## Backend Flask → Railway

1. Buat project baru di Railway, hubungkan repo ini
   (service dari direktori `aquasmart-backend/` bila monorepo).
2. Variables (wajib):
   - `SECRET_KEY` = string acak min. 32 karakter (wajib — app menolak
     boot tanpa ini saat `FLASK_CONFIG=production`).
   - `FLASK_CONFIG` = `production`
   - `CORS_ORIGINS` = `https://<domain-vercel>` (pisahkan koma bila banyak).
   - `DATABASE_URL` = (opsional) `postgresql://...` bila memakai
     Railway Postgres plugin. Default: SQLite `instance/aquasmart.sqlite`.
   - `SCHEDULER_ENABLED` = `true` hanya di **satu** service bila
     multi-worker, agar job expire tidak dobel.
   - `REDIS_URL` = (opsional) untuk rate limit terdistribusi.
3. `Procfile` sudah berisi `web: gunicorn wsgi:app --workers 2 --timeout 60`;
   `railway.json` memasang healthcheck ke `/healthz`.
4. Bila memakai SQLite: pasang **Volume** di-mount ke `/app/instance`
   agar database tidak hilang saat redeploy, lalu upload file
   `aquasmart.sqlite` awal.
5. Verifikasi: `GET https://<app>.up.railway.app/healthz` → 200
   `{"status":"ok"}` dan `GET /api/health` → 200.

## Frontend Next.js → Vercel

1. Import repo frontend ke Vercel (direktori `frontend/`).
2. Environment variable: `AQUASMART_API_URL=https://<app>.up.railway.app`
   (URL backend Flask dari langkah di atas — TANPA trailing slash).
3. Redeploy — pastikan bukan build lama yang tersaji.
4. Verifikasi: buka dashboard, login, pastikan request `/api/devices`
   lewat BFF mengembalikan data (bukan error).

## Catatan keamanan

- Rotasi password Railway (lihat `docs/HUMAN_ACTIONS.md`) SEBELUM deploy.
- Jangan pernah commit file `.env` / `*.local.txt`.
