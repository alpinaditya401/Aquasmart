# HUMAN_ACTIONS.md — Tindakan yang HARUS dilakukan manusia

Dokumen ini berisi tindakan keamanan dan operasional yang **tidak boleh**
dikerjakan agent. Status: **menunggu approval/tindakan manusia**.

> Aturan: agent tidak menghapus file di luar repo, tidak merotasi kredensial,
> dan tidak membersihkan riwayat git tanpa konfirmasi eksplisit.

## 1. Kredensial Railway yang terpapar (KRITIS)

- [ ] Hapus file `railway-seed.local.txt` dari folder Google Drive publik
      (`backend/deploy/railway-seed.local.txt`).
- [ ] Rotasi password akun Railway yang nilainya ada di file tersebut.
- [ ] Pastikan kredensial baru TIDAK disimpan di file `.local.txt` di Drive.

## 2. File sensitif lain di Drive publik

- [ ] Hapus dari Drive publik: `03_RajaDewa-Unity/vuforia-keys.local.txt`
      (2 license key Vuforia).
- [ ] Hapus dari Drive publik: `04_LittleLemon/.env` dan `.env.bak`
      (DJANGO_SECRET_KEY — dua versi terpapar).
- [ ] Hapus dari Drive publik: `credentials.local.txt`
      (4 password akun test).
- [ ] Rotasi semua nilai di atas setelah dihapus dari Drive.

## 3. Jika file sensitif pernah ter-commit ke git

- [ ] Cek riwayat: `git log -p -- <nama-file>` untuk tiap file sensitif.
- [ ] Pembersihan riwayat (mis. `git-filter-repo`) HANYA setelah konfirmasi
      eksplisit dari pemilik repo — karena me-rewrite history dan
      mempengaruhi semua clone.

## 4. Sebelum deploy production

- [ ] Set `SECRET_KEY` production (min. 32 karakter acak) di Railway Variables.
- [ ] Putuskan storage database: SQLite+Volume (default, sesuai SKPL V4.0)
      atau Railway Postgres plugin (rekomendasi bila telemetri concurrent).
- [ ] Upload/pasang file SQLite production bila memakai SQLite+Volume.
