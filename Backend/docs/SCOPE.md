# SCOPE.md — Batas iterasi backend Flask ini

## Out-of-scope (sengaja tidak dikerjakan pada iterasi ini)

| Area | Status | Alasan |
|---|---|---|
| Workspace (FR-029, FR-030) | out-of-scope | Prioritas Won't di SRS; multi-user sharing ditunda v1.1 |
| Product/units (FR-031–FR-033) | out-of-scope | Alur provisioning/aktivasi komersial ditunda v1.1 |
| Audit logs endpoint | out-of-scope | **Path `GET /api/audit-logs` belum terverifikasi** — `router.php` tidak tersedia sehingga path tidak bisa direkonstruksi dengan pasti; operasi `AuditRepository::recent` terbukti ada di kode PHP lama. Ditunda sampai path terkonfirmasi dari source asli. |
| Flutter client | out-of-scope | Backlog — lihat SKPL V4.0 V3-FR12 |
| Inferensi ML produk (V3-FR10) | out-of-scope | Menunggu sensor terkalibrasi + model terpilih. Adapter `ml/inference_adapter.py` tersedia (return None bila model belum ada) |

## Catatan

- Audit *semantik* (pencatatan aksi) tetap berjalan di beberapa endpoint
  (mis. perubahan threshold), tetapi endpoint baca audit-logs belum dibuka.
- Bila path audit-logs terverifikasi di kemudian hari, buka endpoint
  `GET /api/audit-logs` (session admin) mengikuti envelope error baku.
